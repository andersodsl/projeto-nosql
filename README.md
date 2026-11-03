# Agendamento de salas e laboratórios com Aerospike

Projeto de NoSQL (chave-valor) da disciplina Banco de Dados II.
Equipe: Anderson e Naira

Sistema em Python que controla salas, laboratórios e reservas no campus, usando o
**Aerospike** (banco chave-valor) rodando em Docker.

## Estrutura

```
projeto-nosql/
  docker-compose.yml      sobe o banco e as ferramentas (backup, administração)
  requirements.txt        dependência Python (cliente do Aerospike)
  src/
    db.py                 conexão, chaves e buscas
    salas.py              CRUD das salas
    reservas.py           CRUD das reservas + TTL, contador atômico, índice
    app.py                menu do sistema
    popular.py            dados de exemplo
    testes.py             testes automáticos
    benchmark.py          medição de desempenho (tuning)
  scripts/
    backup_automatico.py  backup em rodadas, com rodízio
    restaurar.py          restaura o backup mais recente
  docs/
    estudo_aerospike.md   material de estudo (características, nichos, prós e contras)
    roteiro_apresentacao.md
  backup/                 arquivos de backup (gerados)
```

## Modelo de dados

| Set | Chave | Conteúdo (bins) |
|---|---|---|
| `salas` | `lab1` | sala, tipo, capacidade, bloco |
| `reservas` | `lab1:2026-11-03:14h` | sala, data, horario, responsavel, status |
| `contadores` | `lab1` | confirmadas |

A chave da reserva é composta (`sala:data:horário`), o que impede duas reservas
iguais. O Aerospike não tem chave estrangeira: a aplicação confere se a sala existe
e não deixa remover sala que tenha reservas.

## Como rodar (tudo a partir da pasta do projeto)

Pré-requisitos: Docker Desktop aberto ("Engine running") e Python.

```
py -m pip install -r requirements.txt
docker compose up -d
docker ps
py src/popular.py
py src/app.py
```

Parar o banco: `docker compose down`.

Os avisos `DeprecationWarning` que aparecem ao rodar são do cliente do Aerospike (ele
mudou o nome de algumas funções) e não afetam o funcionamento. Para escondê-los, rode
antes `$env:PYTHONWARNINGS = "ignore"`.

## Testes automáticos

```
py src/testes.py
```

Mostra `[OK]` ou `[FALHOU]` para cada teste. Com `--ttl`, também espera 65 segundos
para provar que a reserva provisória expira sozinha.

## CRUD

| Onde | Operação | Chamada no código |
|---|---|---|
| Salas > Cadastrar | Create | `client.put` com `POLICY_EXISTS_CREATE` |
| Salas > Consultar / Listar | Read | `client.get` / `client.query(...).foreach` |
| Salas > Alterar capacidade | Update | `client.put` com `POLICY_EXISTS_UPDATE` |
| Salas > Remover | Delete | `client.remove` |
| Reservas | CRUD completo | em `src/reservas.py` |

## Recursos do Aerospike usados

- **TTL:** reserva provisória que expira em 60 s; confirmada, não expira mais.
- **Contador atômico:** `client.increment` conta as reservas confirmadas por sala.
- **Índice secundário:** busca por sala e por responsável (a tela mostra se usou o
  índice ou uma varredura).

## Capacidades: redundância e backup

Ver a configuração do namespace (procure `replication-factor` e `nsup-period`):

```
docker compose run --rm tools asadm -h aerospike -e "show config namespace"
```

No nosso container, o `replication-factor` aparece como **1** (uma cópia só) e o banco
roda em **um nó só**, então não há replicação de verdade. Num cluster, costuma-se usar 2
ou mais cópias. A mesma saída mostra `index-type mem` e `storage-engine device`: o
índice fica na memória e os dados em arquivo, que é a arquitetura híbrida. A explicação
completa está em `docs/estudo_aerospike.md`.

**Backup automático (versão de demonstração):**

```
py scripts/backup_automatico.py --intervalo 15 --rodadas 3 --manter 2
```

Faz 3 backups, um a cada 15 segundos, em `backup/auto_AAAAMMDD_HHMMSS`, guardando só
os 2 mais recentes. Cada backup mostra um relatório do `absctl` (no nosso teste: 11
registros e 2 índices lidos). Se uma pasta antiga não puder ser removida (por exemplo,
projeto dentro do OneDrive), o script avisa em vez de dizer que removeu. Em produção o Aerospike oferece o Aerospike Backup Service, que
agenda backups por cron.

## Dump (backup manual e restauração)

1. Criar dados (`py src/popular.py`) e fazer o backup:

```
docker compose run --rm absctl absctl backup -h aerospike:3000 -n test -d /data/backup/dump1
```

2. No `py src/app.py`, cancelar uma reserva e listar (ela sumiu).
3. Restaurar:

```
docker compose run --rm absctl absctl restore -h aerospike:3000 -n test -d /data/backup/dump1
```

4. Listar de novo (a reserva voltou).

A restauração só grava registros que não existem no banco ou que são mais antigos que
os do backup. Por isso, **apague a reserva antes de restaurar**: se nada foi apagado, o
relatório mostra `Inserted Records: 0` (os 11 registros aparecem como `Fresher Records`,
porque o banco já tem as versões mais novas). O contador de ocupação também é um
registro: se ele mudou depois do backup, a restauração pode mantê-lo como está.

Para repetir o backup, use outro nome de pasta (`dump2`).

## Tuning e configuração

**a) Servidor: NSUP e TTL.** Segundo a documentação, o servidor recusa gravações com
TTL quando o processo que apaga os expirados (NSUP) está desligado, ou seja, quando
`nsup-period` é 0 (e `allow-ttl-without-nsup` é false). Na imagem que usamos, o
`show config namespace` mostra `nsup-period` = **120** segundos e
`allow-ttl-without-nsup` = false: o NSUP já está ligado, e o TTL funciona sem erro.
Em instalações em que o valor é 0, o app mostra "erro 22" ao criar uma reserva
provisória, e a solução é definir o período (aqui, 10 segundos):

```
docker compose run --rm tools asadm -h aerospike --enable -e "manage config namespace test param nsup-period to 10"
```

(se pedir confirmação, responda `y`). Depois confira com o comando `show config
namespace` da seção anterior.

**b) Aplicação.**

```
py src/benchmark.py
```

Grava e lê 2000 registros de três jeitos: sequencial, paralelo (8 threads) e em lote
(uma chamada só, para leitura). Resultado da nossa máquina (2000 registros):

| | Sequencial | Paralelo | Em lote |
|---|---|---|---|
| Gravar | 1,08 s | 0,30 s | - |
| Ler | 1,07 s | 0,32 s | indisponível* |

O paralelo ficou cerca de 3 a 4 vezes mais rápido que o sequencial.
\*A função de leitura em lote usada não existe na versão do cliente instalada, e o
script avisa isso em vez de falhar.

## Fontes

Ver o final de `docs/estudo_aerospike.md`.