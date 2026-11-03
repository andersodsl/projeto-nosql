import aerospike
from aerospike import exception as ex
from aerospike import predicates

NAMESPACE = 'test'
SET_SALAS = 'salas'
SET_RESERVAS = 'reservas'
SET_CONTADORES = 'contadores'

TTL_PROVISORIA = 60 

SEM_EXPIRACAO = {'ttl': aerospike.TTL_NEVER_EXPIRE}
MANTER_TTL = {'ttl': getattr(aerospike, 'TTL_DONT_UPDATE', -2)}

client = aerospike.client({'hosts': [('127.0.0.1', 3000)]}).connect()


def chave_sala(sala):
    return (NAMESPACE, SET_SALAS, sala)


def chave_reserva(sala, data, horario):
    return (NAMESPACE, SET_RESERVAS, f'{sala}:{data}:{horario}')


def chave_contador(sala):
    return (NAMESPACE, SET_CONTADORES, sala)


def criar_indices():
    for campo in ('sala', 'responsavel'):
        try:
            client.index_string_create(NAMESPACE, SET_RESERVAS, campo, f'idx_reservas_{campo}')
        except ex.AerospikeError as e:
            if getattr(e, 'code', None) != 200:  
                print(f'Aviso: não foi possível criar o índice de "{campo}": {e}')


def consultar_por_campo(set_name, campo, valor):
   
    encontrados = []
    try:
        consulta = client.query(NAMESPACE, set_name)
        consulta.where(predicates.equals(campo, valor))
        consulta.foreach(lambda registro: encontrados.append(registro[2]))
        return encontrados, 'índice secundário'
    except ex.AerospikeError:
        encontrados = []

        def filtrar(registro):
            if registro[2].get(campo) == valor:
                encontrados.append(registro[2])

        client.query(NAMESPACE, set_name).foreach(filtrar)
        return encontrados, 'varredura (scan)'


def listar_set(set_name):
    registros = []
    client.query(NAMESPACE, set_name).foreach(lambda registro: registros.append(registro[2]))
    return registros
