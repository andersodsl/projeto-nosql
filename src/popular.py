"""Cadastra salas e reservas de exemplo, para as demonstrações."""
import db
import reservas
import salas

db.criar_indices()

salas.cadastrar('lab1', 'laboratorio', 30, 'Bloco A')
salas.cadastrar('lab2', 'laboratorio', 25, 'Bloco A')
salas.cadastrar('sala101', 'sala', 40, 'Bloco B')
salas.cadastrar('auditorio', 'auditorio', 120, 'Bloco C')

reservas.reservar('lab1', '2026-11-03', '14h', 'Ana')
reservas.reservar('lab1', '2026-11-03', '16h', 'Bruno')
reservas.reservar('sala101', '2026-11-03', '08h', 'Carla')
reservas.reservar('auditorio', '2026-11-04', '19h', 'Ana')

db.client.close()
print('\nPronto: dados de exemplo processados.')
