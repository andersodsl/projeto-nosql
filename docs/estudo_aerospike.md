## 1. O que é o Aerospike 

Banco de dados NoSQL do tipo **chave-valor**, distribuído (funciona em vários
servidores ligados em cluster), criado para ser muito rápido com muitos dados.
Também aceita outras formas de modelar dados, mas o uso principal é chave-valor
**[doc]**.

Como os nomes se comparam ao banco relacional:

| Relacional | Aerospike | No nosso projeto |
|---|---|---|
| Banco de dados | namespace | `test` |
| Tabela | set | `salas`, `reservas`, `contadores` |
| Linha | registro | uma reserva |
| Coluna | bin | `responsavel`, `status`... |
| Chave primária | chave | `lab1:2026-11-03:14h` |

---

## 2. Principais características

1. **Chave-valor.** Cada registro é encontrado pela chave, direto, sem JOIN.
2. **Arquitetura híbrida de memória (HMA).** O padrão é guardar o **índice
   primário na memória** e os **dados em SSD**. Dá velocidade próxima da memória,
   com custo menor do que guardar tudo em RAM **[doc]**. Os dados também podem ficar
   só na memória. A opção "tudo em flash" é só da edição Enterprise **[doc]**.
3. **Cliente inteligente (Smart Client).** O cliente sabe em qual servidor do
   cluster cada dado está e vai direto nele ("um salto"), distribuindo o tráfego
   **[vendor]**.
4. **Distribuído e replicado.** Os dados são replicados entre os nós do cluster, o
   que dá resistência a falhas **[doc]**. A arquitetura é "shared-nothing" (nós
   independentes) com clusters que se autogerenciam **[terceiros]**.
5. **Latência baixa e previsível.** Comparativos de terceiros citam respostas
   abaixo de 1 ms e milhões de operações por segundo **[terceiros, não medimos]**.
6. **TTL (expiração automática).** Cada registro pode ter um prazo de vida e é
   apagado sozinho depois dele **[doc]**. Usamos isso nas reservas provisórias.
7. **Operações atômicas por registro** (como somar um contador direto no banco).
   Usamos isso no contador de reservas.
8. **Índices secundários** para buscar por outros campos além da chave. Há um
   limite de 256 por namespace **[doc]**. Usamos isso nas buscas por sala e por
   responsável.
9. **Consistência.** No modo padrão (AP, "alta disponibilidade"), numa falha de
   rede as leituras podem vir desatualizadas **[fórum oficial]**. O modo de
   **consistência forte** só existe na edição Enterprise **[vendor]**.
10. **Licença.** Servidor Community em AGPLv3 e clientes em Apache v2 **[vendor]**.

### Community vs Enterprise (nós usamos a Community)

| Item | Community (grátis) | Enterprise (paga) |
|---|---|---|
| Nós por cluster | até 8 **[doc]** | até 256 **[doc]** |
| Namespaces | até 2 **[doc]** | até 32 **[doc]** |
| Limite de dados do cluster | alguns TB (2,5 TB na tabela atual de produtos; uma página mais antiga diz 5 TB) **[conferir]** | sem limite |
| Consistência forte, rack awareness, multi-site (XDR) | não | sim **[vendor]** |
| Suporte | comunidade | suporte da empresa |

---

## 3. Nichos de aplicação

Onde o Aerospike costuma ser usado, segundo a própria empresa e outros sites
**[vendor / terceiros]**:

- **Publicidade online (ad tech):** leilão de anúncios em tempo real (decidir em
  milissegundos qual anúncio mostrar). É o mercado onde ele é mais conhecido.
- **Detecção de fraude:** analisar uma transação enquanto ela acontece. A empresa
  cita o PayPal como exemplo **[vendor]**.
- **Recomendação e personalização:** guardar o perfil do usuário e consultar rápido.
- **Sessões e perfis de usuário** em sistemas grandes.
- **IoT e telecom:** muitos dados chegando o tempo todo.
- **Pagamentos, fintech e jogos online.**

**Regra geral:** vale a pena quando há **muitos acessos por segundo**, **resposta
rápida e previsível** e o acesso é principalmente **por chave**.

Ligando ao nosso projeto: reservas de salas funcionam bem em chave-valor porque o
acesso é por uma chave natural (sala + data + horário). Mas admitimos que, no nosso
tamanho, um banco relacional também resolveria; o Aerospike é "grande" para o
problema, e usamos o projeto para demonstrar os recursos.

---

## 4. Prós e contras

**Prós**
- Muito rápido e com resposta previsível em grande escala **[terceiros]**.
- Custo menor que guardar tudo em RAM, por causa da arquitetura híbrida **[doc]**.
- Escala adicionando nós; replicação entre nós **[doc]**.
- TTL, contadores atômicos e índices secundários prontos.
- Edição Community gratuita, boa para estudar e para projetos pequenos.

**Contras**
- **Consultas flexíveis são limitadas.** Não tem JOIN nem chave estrangeira.
  Buscar por outro campo exige criar índice antes **[terceiros]**. No projeto
  vimos isso: a integridade (a sala existe?) é responsabilidade da aplicação.
- **A edição Community tem limites** (8 nós, 2 namespaces, sem consistência forte)
  **[doc]**.
- **Cuidado com o TTL.** Por padrão, o servidor pode recusar gravar com TTL, a menos
  que o processo que limpa registros expirados (NSUP) esteja ligado **[doc]**.
  Foi o que configuramos na parte de tuning.
- **Montar cluster em Docker é trabalhoso.** Por isso nossa demonstração roda em um
  único nó (sem réplica de verdade).
- **Ferramentas mudaram.** O backup antigo (`asbackup`) virou "legado" e hoje a
  ferramenta oficial é o `absctl` **[doc]**. Material antigo na internet pode estar
  desatualizado.
- Comunidade e material de estudo menores que os de bancos mais populares
  **[conferir, opinião]**.

---

## 5. Capacidades: redundância e backup

**Redundância (replicação).** O banco guarda cópias dos dados em nós diferentes. O
número de cópias é o `replication-factor` (o padrão costuma ser 2). Se um nó cair,
outro tem os dados **[doc]**. Na nossa demonstração há **um nó só**, então mostramos
a configuração (`replication-factor`), mas não há onde guardar a segunda cópia. Isso
precisa ser dito com honestidade na apresentação.

**Backup.**
- Ferramenta oficial: **absctl** (faz backup e restauração em arquivos `.asb`)
  **[doc]**.
- **Backup automático** de verdade: o **Aerospike Backup Service (ABS)** agenda
  backups por cron (por exemplo, completo por dia e incremental por hora) **[doc]**.
- No projeto, o `scripts/backup_automatico.py` faz uma versão simples da ideia:
  roda o backup em rodadas e guarda só os mais recentes. É para demonstrar o
  conceito, não substitui o ABS.

**Dump (exportar e restaurar os dados).** É o mesmo processo: o `absctl backup`
gera os arquivos e o `absctl restore` devolve os dados ao banco.

---

## 6. Glossário

- **Chave-valor:** guarda dados associados a uma chave, e a consulta principal é por ela.
- **Registro:** um conjunto de dados com uma chave. **Bin:** um campo do registro.
- **Cluster / nó:** conjunto de servidores / um servidor desse conjunto.
- **Replicação:** manter cópias dos dados em mais de um nó.
- **TTL:** tempo de vida de um registro. **NSUP:** processo que apaga os expirados.
- **Índice secundário:** índice para buscar por um campo que não é a chave.
- **Atômico:** acontece por inteiro ou não acontece, sem ficar pela metade.
- **Dump:** exportar os dados do banco para arquivos.
- **AP / consistência forte:** prioridade para disponibilidade / para dados sempre corretos.

---

## 7. Fontes (abra e confira)

- Armazenamento híbrido: https://aerospike.com/docs/architecture/storage
- Limites do servidor: https://aerospike.com/docs/guide/limitations
- Edições (Community x Enterprise): https://aerospike.com/products/product-matrix/
- Retenção de dados e TTL: https://aerospike.com/docs/database/manage/namespace/retention
- Ferramentas de backup (visão geral): https://aerospike.com/docs/database/tools/backup-and-restore/overview/
- absctl (guia rápido): https://aerospike.com/docs/database/tools/backup-and-restore/absctl/quickstart/
- Migração do asbackup para o absctl: https://aerospike.com/docs/database/tools/backup-and-restore/legacy-migration/
- Fórum oficial sobre consistência na Community: https://discuss.aerospike.com/t/regarding-community-edition/5427
- Visão geral e casos de uso (empresa): https://aerospike.com/docs
- Comparativos de terceiros: https://www.dremio.com/wiki/aerospike/ e https://www.index.dev/skill-vs-skill/database-voltdb-vs-redis-vs-aerospike
- Site indicado pelo professor: https://dbdb.io/browse
