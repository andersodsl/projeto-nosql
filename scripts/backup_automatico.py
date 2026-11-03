"""Backup automático do Aerospike, feito em rodadas, com rodízio de pastas.

A cada intervalo, roda o absctl (ferramenta oficial de backup) dentro do Docker e
grava em backup/auto_AAAAMMDD_HHMMSS. Guarda só os últimos N backups.

Uso (na pasta do projeto):
  py scripts/backup_automatico.py                    3 backups, 1 a cada 30 s
  py scripts/backup_automatico.py --intervalo 20 --rodadas 5 --manter 3

Observação: é uma versão simples, para demonstrar a ideia. Em produção, o
Aerospike oferece o Aerospike Backup Service, que agenda backups por cron.
"""
import argparse
import shutil
import subprocess
import time
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PASTA_BACKUP = RAIZ / 'backup'


def fazer_backup():
    nome = datetime.now().strftime('auto_%Y%m%d_%H%M%S')
    comando = [
        'docker', 'compose', 'run', '--rm', 'absctl',
        'absctl', 'backup', '-h', 'aerospike:3000', '-n', 'test',
        '-d', f'/data/backup/{nome}',
    ]
    resultado = subprocess.run(comando, cwd=RAIZ)
    return nome, resultado.returncode == 0


def aplicar_rodizio(manter):
    pastas = sorted(p for p in PASTA_BACKUP.glob('auto_*') if p.is_dir())
    for antiga in pastas[:-manter] if manter > 0 else []:
        shutil.rmtree(antiga, ignore_errors=True)
        print(f'  Backup antigo removido: {antiga.name}')


def main():
    parser = argparse.ArgumentParser(description='Backup automático do Aerospike')
    parser.add_argument('--intervalo', type=int, default=30, help='segundos entre backups')
    parser.add_argument('--rodadas', type=int, default=3, help='quantos backups fazer')
    parser.add_argument('--manter', type=int, default=3, help='quantos backups guardar')
    args = parser.parse_args()

    PASTA_BACKUP.mkdir(exist_ok=True)
    print(f'Backup automático: {args.rodadas} rodada(s), a cada {args.intervalo} s, '
          f'guardando os {args.manter} mais recentes.')
    for rodada in range(1, args.rodadas + 1):
        print(f'\n[{datetime.now():%H:%M:%S}] Rodada {rodada}/{args.rodadas}')
        nome, ok = fazer_backup()
        print(f'  {"Backup concluído" if ok else "FALHOU"}: {nome}')
        aplicar_rodizio(args.manter)
        if rodada < args.rodadas:
            time.sleep(args.intervalo)
    print('\nFim. Pastas em backup/:', ', '.join(sorted(p.name for p in PASTA_BACKUP.glob('auto_*'))))


main()
