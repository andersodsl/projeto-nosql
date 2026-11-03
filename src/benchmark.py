import time
from concurrent.futures import ThreadPoolExecutor

import aerospike
from aerospike import exception as ex

NAMESPACE = 'test'
SET = 'benchmark'
TOTAL = 2000
THREADS = 8

client = aerospike.client({'hosts': [('127.0.0.1', 3000)]}).connect()


def chave(i):
    return (NAMESPACE, SET, f'sala{i}:2026-11-03:14h')


def gravar(i):
    client.put(chave(i), {'sala': f'sala{i}', 'responsavel': f'aluno{i}'},
               meta={'ttl': aerospike.TTL_NEVER_EXPIRE})


def ler(i):
    client.get(chave(i))


def limpar():
    for i in range(TOTAL):
        try:
            client.remove(chave(i))
        except ex.RecordNotFound:
            pass


def sequencial(funcao):
    inicio = time.perf_counter()
    for i in range(TOTAL):
        funcao(i)
    return time.perf_counter() - inicio


def paralelo(funcao):
    inicio = time.perf_counter()
    with ThreadPoolExecutor(max_workers=THREADS) as pool:
        list(pool.map(funcao, range(TOTAL)))
    return time.perf_counter() - inicio


def em_lote():
    chaves = [chave(i) for i in range(TOTAL)]
    inicio = time.perf_counter()
    try:
        if hasattr(client, 'batch_read'):      
            client.batch_read(chaves)
        else:                                  
            client.get_many(chaves)
    except (AttributeError, TypeError, ex.AerospikeError):
        return None
    return time.perf_counter() - inicio


limpar()
t_grav_seq = sequencial(gravar)
t_ler_seq = sequencial(ler)
t_ler_lote = em_lote()

limpar()
t_grav_par = paralelo(gravar)
t_ler_par = paralelo(ler)

limpar()
client.close()

print(f'\nRegistros: {TOTAL} | Threads no modo paralelo: {THREADS}')
print(f'Gravar  sequencial: {t_grav_seq:.2f}s | paralelo: {t_grav_par:.2f}s')
print(f'Ler     sequencial: {t_ler_seq:.2f}s | paralelo: {t_ler_par:.2f}s')
if t_ler_lote is None:
    print('Ler     em lote: indisponível nesta versão do cliente')
else:
    print(f'Ler     em lote (1 chamada): {t_ler_lote:.2f}s')