"""Testes automáticos da aplicação, rodando contra o Aerospike de verdade.

Uso:
  py src/testes.py          testes rápidos
  py src/testes.py --ttl    inclui o teste de expiração (espera cerca de 65 s)

Cada linha mostra [OK] ou [FALHOU]. No final, um resumo.
"""
import io
import sys
import time
from contextlib import redirect_stdout

from aerospike import exception as ex

import db
import reservas
import salas
from db import (client, chave_contador, chave_reserva, chave_sala,
                consultar_por_campo, SET_RESERVAS, TTL_PROVISORIA)

SALA = 'teste-sala'
DATA = '2099-01-01'
resultados = []


def silencioso(funcao, *args, **kwargs):
    """Roda uma função e devolve o que ela imprimiu (sem mostrar na tela)."""
    saida = io.StringIO()
    with redirect_stdout(saida):
        funcao(*args, **kwargs)
    return saida.getvalue()


def checar(nome, condicao):
    print(f"[{'OK' if condicao else 'FALHOU'}] {nome}")
    resultados.append(bool(condicao))


def registro(chave):
    """Devolve (metadados, bins) ou None se o registro não existe."""
    try:
        _, meta, bins = client.get(chave)
        return meta, bins
    except ex.RecordNotFound:
        return None


def total_confirmadas():
    dados = registro(chave_contador(SALA))
    return dados[1].get('confirmadas', 0) if dados else 0


def limpar():
    for chave in (chave_reserva(SALA, DATA, '08h'), chave_reserva(SALA, DATA, '10h'),
                  chave_reserva(SALA, DATA, '12h'), chave_sala(SALA), chave_contador(SALA)):
        try:
            client.remove(chave)
        except ex.RecordNotFound:
            pass


def testar(com_ttl):
    print('--- Salas ---')
    silencioso(salas.cadastrar, SALA, 'laboratorio', 30, 'Bloco T')
    checar('cadastrar sala', registro(chave_sala(SALA)) is not None)
    saida = silencioso(salas.cadastrar, SALA, 'laboratorio', 30, 'Bloco T')
    checar('recusar sala duplicada', 'Já existe' in saida)
    silencioso(salas.alterar_capacidade, SALA, 45)
    checar('alterar capacidade', registro(chave_sala(SALA))[1]['capacidade'] == 45)

    print('--- Reservas ---')
    saida = silencioso(reservas.reservar, 'sala-que-nao-existe', DATA, '08h', 'Ana')
    checar('recusar reserva em sala inexistente',
           'não cadastrada' in saida and registro(chave_reserva('sala-que-nao-existe', DATA, '08h')) is None)
    silencioso(reservas.reservar, SALA, DATA, '08h', 'Ana')
    checar('reservar (create)', registro(chave_reserva(SALA, DATA, '08h')) is not None)
    checar('contador atômico = 1 após reservar', total_confirmadas() == 1)
    saida = silencioso(reservas.reservar, SALA, DATA, '08h', 'Bruno')
    checar('recusar reserva duplicada',
           'já está reservada' in saida and registro(chave_reserva(SALA, DATA, '08h'))[1]['responsavel'] == 'Ana')
    silencioso(reservas.trocar_responsavel, SALA, DATA, '08h', 'Carla')
    checar('trocar responsável (update)', registro(chave_reserva(SALA, DATA, '08h'))[1]['responsavel'] == 'Carla')

    print('--- Índice secundário ---')
    encontrados, metodo = consultar_por_campo(SET_RESERVAS, 'responsavel', 'Carla')
    checar(f'buscar por responsável (método: {metodo})', len(encontrados) >= 1)
    encontrados, metodo = consultar_por_campo(SET_RESERVAS, 'sala', SALA)
    checar(f'buscar por sala (método: {metodo})', len(encontrados) >= 1)

    print('--- TTL (reserva provisória) ---')
    saida = silencioso(reservas.reservar, SALA, DATA, '10h', 'Duda', provisoria=True)
    if 'erro 22' in saida:
        checar('criar provisória (TTL desativado no banco: veja a seção Tuning do README)', False)
    else:
        dados = registro(chave_reserva(SALA, DATA, '10h'))
        checar('criar provisória', dados is not None and dados[1]['status'] == 'provisoria')
        checar('provisória tem prazo para expirar', dados is not None and 0 < dados[0]['ttl'] <= TTL_PROVISORIA)
        checar('provisória não entra no contador', total_confirmadas() == 1)
        silencioso(reservas.confirmar, SALA, DATA, '10h')
        dados = registro(chave_reserva(SALA, DATA, '10h'))
        checar('confirmar provisória', dados is not None and dados[1]['status'] == 'confirmada')
        checar('confirmada não expira mais', dados is not None and (dados[0]['ttl'] in (-1, 4294967295) or dados[0]['ttl'] > 86400))
        checar('contador = 2 após confirmar', total_confirmadas() == 2)

    print('--- Cancelar e remover ---')
    silencioso(reservas.cancelar, SALA, DATA, '08h')
    checar('cancelar reserva (delete)', registro(chave_reserva(SALA, DATA, '08h')) is None)
    saida = silencioso(salas.remover, SALA)
    checar('não remover sala que ainda tem reserva', 'Não é possível remover' in saida or registro(chave_reserva(SALA, DATA, '10h')) is None)

    if com_ttl:
        print(f'--- Expiração real (aguardando {TTL_PROVISORIA + 5} s) ---')
        silencioso(reservas.reservar, SALA, DATA, '12h', 'Eva', provisoria=True)
        time.sleep(TTL_PROVISORIA + 5)
        checar('provisória expirou sozinha', registro(chave_reserva(SALA, DATA, '12h')) is None)


def main():
    com_ttl = '--ttl' in sys.argv
    db.criar_indices()
    limpar()
    try:
        testar(com_ttl)
    finally:
        limpar()
        db.client.close()
    ok = sum(resultados)
    print(f'\nResultado: {ok}/{len(resultados)} testes passaram.')
    sys.exit(0 if ok == len(resultados) else 1)


main()
