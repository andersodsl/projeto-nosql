"""Restaura um backup no Aerospike usando o absctl (dentro do Docker).

Uso (na pasta do projeto):
  py scripts/restaurar.py                    restaura o backup mais recente
  py scripts/restaurar.py auto_20261101_...  restaura uma pasta específica de backup/
"""
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PASTA_BACKUP = RAIZ / 'backup'

pastas = sorted(p.name for p in PASTA_BACKUP.iterdir() if p.is_dir()) if PASTA_BACKUP.exists() else []
if not pastas:
    sys.exit('Nenhum backup encontrado na pasta backup/. Rode antes o backup.')

escolhida = sys.argv[1] if len(sys.argv) > 1 else pastas[-1]
if escolhida not in pastas:
    sys.exit(f'Backup "{escolhida}" não encontrado. Disponíveis: {", ".join(pastas)}')

print(f'Restaurando o backup: {escolhida}')
comando = [
    'docker', 'compose', 'run', '--rm', 'absctl',
    'absctl', 'restore', '-h', 'aerospike:3000', '-n', 'test',
    '-d', f'/data/backup/{escolhida}',
]
sys.exit(subprocess.run(comando, cwd=RAIZ).returncode)
