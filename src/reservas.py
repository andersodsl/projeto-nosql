import aerospike
from aerospike import exception as ex

import salas
from db import (client, chave_reserva, chave_contador, consultar_por_campo, listar_set,
                SET_RESERVAS, SET_SALAS, TTL_PROVISORIA, SEM_EXPIRACAO, MANTER_TTL)


def _mostrar(dados):
    print(f"{dados['sala']} | {dados['data']} | {dados['horario']} | "
          f"{dados['responsavel']} | {dados['status']}")


def _erro_banco(e):
    if getattr(e, 'code', None) == 22:
        print('O servidor recusou gravar com TTL (erro 22). O TTL está desativado '
              'no banco: veja a seção "Tuning" do README (nsup-period).')
    else:
        print('Erro no banco:', e)


def reservar(sala, data, horario, responsavel, provisoria=False):
    if not salas.existe(sala):
        print('Sala não cadastrada. Cadastre a sala primeiro.')
        return
    status = 'provisoria' if provisoria else 'confirmada'
    meta = {'ttl': TTL_PROVISORIA} if provisoria else SEM_EXPIRACAO
    try:
        client.put(
            chave_reserva(sala, data, horario),
            {'sala': sala, 'data': data, 'horario': horario,
             'responsavel': responsavel, 'status': status},
            meta=meta,
            policy={'exists': aerospike.POLICY_EXISTS_CREATE},
        )
    except ex.RecordExistsError:
        print('Essa sala já está reservada nesse horário.')
        return
    except ex.AerospikeError as e:
        _erro_banco(e)
        return
    if provisoria:
        print(f'Reserva provisória criada! Expira em {TTL_PROVISORIA} segundos se não for confirmada.')
    else:
        client.increment(chave_contador(sala), 'confirmadas', 1, meta=SEM_EXPIRACAO)
        print('Reserva confirmada!')


def consultar(sala, data, horario):
    try:
        _, meta, dados = client.get(chave_reserva(sala, data, horario))
    except ex.RecordNotFound:
        print('Sala livre nesse horário.')
        return
    _mostrar(dados)
    if dados['status'] == 'provisoria':
        print(f"Atenção: reserva provisória, expira em {meta['ttl']} segundos.")


def trocar_responsavel(sala, data, horario, novo_responsavel):
    try:
        client.put(
            chave_reserva(sala, data, horario),
            {'responsavel': novo_responsavel},
            meta=MANTER_TTL,
            policy={'exists': aerospike.POLICY_EXISTS_UPDATE},
        )
        print('Responsável atualizado!')
    except ex.RecordNotFound:
        print('Não existe reserva nesse horário.')


def confirmar(sala, data, horario):
    try:
        _, _, dados = client.get(chave_reserva(sala, data, horario))
    except ex.RecordNotFound:
        print('Não existe reserva nesse horário (ela pode ter expirado).')
        return
    if dados['status'] == 'confirmada':
        print('Essa reserva já está confirmada.')
        return
    client.put(
        chave_reserva(sala, data, horario),
        {'status': 'confirmada'},
        meta=SEM_EXPIRACAO, 
        policy={'exists': aerospike.POLICY_EXISTS_UPDATE},
    )
    client.increment(chave_contador(sala), 'confirmadas', 1, meta=SEM_EXPIRACAO)
    print('Reserva confirmada! Ela não expira mais.')


def cancelar(sala, data, horario):
    try:
        _, _, dados = client.get(chave_reserva(sala, data, horario))
        client.remove(chave_reserva(sala, data, horario))
    except ex.RecordNotFound:
        print('Não existe reserva nesse horário.')
        return
    if dados['status'] == 'confirmada':
        client.increment(chave_contador(sala), 'confirmadas', -1, meta=SEM_EXPIRACAO)
    print('Reserva cancelada!')


def listar_todas():
    registros = listar_set(SET_RESERVAS)
    if not registros:
        print('Nenhuma reserva.')
    for dados in sorted(registros, key=lambda d: (d['sala'], d['data'], d['horario'])):
        _mostrar(dados)


def da_sala(sala):
    registros, metodo = consultar_por_campo(SET_RESERVAS, 'sala', sala)
    print(f'(busca feita por: {metodo})')
    if not registros:
        print('Nenhuma reserva para essa sala.')
    for dados in sorted(registros, key=lambda d: (d['data'], d['horario'])):
        _mostrar(dados)


def do_responsavel(nome):
    registros, metodo = consultar_por_campo(SET_RESERVAS, 'responsavel', nome)
    print(f'(busca feita por: {metodo})')
    if not registros:
        print('Nenhuma reserva para esse responsável.')
    for dados in sorted(registros, key=lambda d: (d['data'], d['horario'])):
        _mostrar(dados)


def ocupacao():
    lista = listar_set(SET_SALAS)
    if not lista:
        print('Nenhuma sala cadastrada.')
    for sala in sorted(lista, key=lambda d: d['sala']):
        try:
            _, _, contador = client.get(chave_contador(sala['sala']))
            total = contador.get('confirmadas', 0)
        except ex.RecordNotFound:
            total = 0
        print(f"{sala['sala']}: {total} reserva(s) confirmada(s)")
