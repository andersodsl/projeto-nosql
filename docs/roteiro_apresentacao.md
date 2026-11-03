# Roteiro da apresentação (cerca de 25 minutos)

O professor pede de 20 a 25 minutos. Este roteiro soma uns 24 e meio. Para ficar mais
perto de 22, resuma "Nichos de aplicação" e pule "Testes automáticos".

Antes de começar: Docker Desktop aberto e terminal aberto na pasta do projeto. Para
mostrar o spin-up, comece com o banco desligado (`docker compose down`). Depois do
`docker compose up -d`, rode `py src/popular.py` (dados de exemplo). Para esconder os
avisos do cliente, rode `$env:PYTHONWARNINGS = "ignore"`. Limpe a tela (`cls`) para a
senha de qualquer comando não aparecer.

Podem dividir as partes entre vocês como preferirem. Todos devem entender o projeto
inteiro, porque a turma pode perguntar qualquer coisa.

| Tempo | Parte | O que falar / mostrar |
|---|---|---|
| 0:00-1:00 | Abertura | Equipe, banco (Aerospike, chave-valor) e tema (agendamento de salas) |
| 1:00-5:00 | Características | Seção 2 do `docs/estudo_aerospike.md` |
| 5:00-7:30 | Nichos de aplicação | Seção 3 do estudo |
| 7:30-10:00 | Prós e contras | Seção 4 do estudo, incluindo Community x Enterprise |
| 10:00-12:00 | Spin-up | Mostrar `docker-compose.yml`, rodar `docker compose up -d` e `docker ps` |
| 12:00-13:30 | Modelo de dados | Tabela de sets e chaves do README; mostrar `src/db.py` (função `chave_reserva`) |
| 13:30-18:00 | CRUD ao vivo | `py src/app.py`: cadastrar sala, reservar, consultar, reserva duplicada (recusada), trocar responsável, cancelar. **Aqui, criar uma reserva provisória** |
| 18:00-19:30 | Recursos do banco | Voltar na provisória (mostra o tempo que falta e depois "Sala livre"); contador (Relatórios > Ocupação); índice (a tela diz o método da busca) |
| 19:30-21:00 | Redundância | `docker compose run --rm tools asadm -h aerospike -e "show config namespace"`: mostrar `replication-factor` (aparece **1**), `index-type` (mem) e `storage-engine` (device); explicar que há um nó só |
| 21:00-22:30 | Backup automático e dump | `py scripts/backup_automatico.py --intervalo 15 --rodadas 3 --manter 2`; depois **cancelar uma reserva** e só então `py scripts/restaurar.py` (se nada foi apagado, o relatório mostra `Inserted Records: 0`); listar e mostrar que voltou. Não mostre a Ocupação depois da restauração |
| 22:30-23:30 | Tuning | NSUP (`nsup-period` já vem em 120, o TTL funciona sem erro) e `py src/benchmark.py` (nosso resultado: gravar 1,08 s sequencial x 0,30 s paralelo; ler 1,07 x 0,32) |
| 23:30-24:30 | Testes automáticos | `py src/testes.py` (todos [OK]) e conclusão |

## Plano B (se algo falhar ao vivo)

- Tenha **prints ou um vídeo curto** de cada demonstração, feitos nos ensaios.
- Se o Docker não subir: mostre o `docker-compose.yml`, explique o comando e passe
  para os prints.
- Se um comando de backup falhar: mostre a pasta `backup/` do ensaio e explique
  o processo (backup, apagar, restaurar).

## Ensaio

Faça pelo menos **dois ensaios completos cronometrados**, com o banco recém-subido
e os dados recriados (`docker compose down` e `docker compose up -d` entre eles).