import aerospike
from aerospike import exception as ex

from db import (client, chave_sala, chave_contador, consultar_por_campo, listar_set,
                SET_RESERVAS, SET_SALAS, SEM_EXPIRACAO)


def cadastrar(sala, tipo, capacidade, bloco):
    try:
        client.put(
            chave_sala(sala),
            {'sala': sala, 'tipo': tipo, 'capacidade': capacidade, 'bloco': bloco},
            meta=SEM_EXPIRACAO,
            policy={'exists': aerospike.POLICY_EXISTS_CREATE},
        )
        print('Sala cadastrada!')
    except ex.RecordExistsError:
        print('Já existe uma sala com esse código.')


def existe(sala):
    try:
        client.get(chave_sala(sala))
        return True
    except ex.RecordNotFound:
        return False


def consultar(sala):
    try:
        _, _, dados = client.get(chave_sala(sala))
        print('Sala:', dados)
    except ex.RecordNotFound:
        print('Sala não encontrada.')


def alterar_capacidade(sala, capacidade):
    try:
        client.put(
            chave_sala(sala),
            {'capacidade': capacidade},
            meta=SEM_EXPIRACAO,
            policy={'exists': aerospike.POLICY_EXISTS_UPDATE},
        )
        print('Capacidade atualizada!')
    except ex.RecordNotFound:
        print('Sala não encontrada.')


def remover(sala):
    reservas, _ = consultar_por_campo(SET_RESERVAS, 'sala', sala)
    if reservas:
        print(f'Não é possível remover: a sala tem {len(reservas)} reserva(s).')
        return
    try:
        client.remove(chave_sala(sala))
        print('Sala removida!')
    except ex.RecordNotFound:
        print('Sala não encontrada.')
        return
    try:
        client.remove(chave_contador(sala))
    except ex.RecordNotFound:
        pass


def listar():
    registros = listar_set(SET_SALAS)
    if not registros:
        print('Nenhuma sala cadastrada.')
    for dados in sorted(registros, key=lambda d: d['sala']):
        print(f"{dados['sala']} | {dados['tipo']} | {dados['capacidade']} lugares | {dados['bloco']}")
