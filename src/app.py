"""Sistema de agendamento de salas e laboratórios (menu no terminal)."""
import db
import reservas
import salas


def pedir_inteiro(texto):
    while True:
        try:
            return int(input(texto))
        except ValueError:
            print('Digite um número inteiro.')


def pedir_reserva():
    sala = input('Sala (ex: lab1): ')
    data = input('Data (ex: 2026-11-03): ')
    horario = input('Horário (ex: 14h): ')
    return sala, data, horario


def menu_salas():
    while True:
        print('\n--- SALAS ---')
        print('1 Cadastrar | 2 Consultar | 3 Alterar capacidade | 4 Remover | 5 Listar | 0 Voltar')
        opcao = input('Escolha: ')
        if opcao == '1':
            salas.cadastrar(input('Código (ex: lab1): '),
                            input('Tipo (sala, laboratorio ou auditorio): '),
                            pedir_inteiro('Capacidade: '),
                            input('Bloco: '))
        elif opcao == '2':
            salas.consultar(input('Código da sala: '))
        elif opcao == '3':
            salas.alterar_capacidade(input('Código da sala: '), pedir_inteiro('Nova capacidade: '))
        elif opcao == '4':
            salas.remover(input('Código da sala: '))
        elif opcao == '5':
            salas.listar()
        elif opcao == '0':
            return


def menu_reservas():
    while True:
        print('\n--- RESERVAS ---')
        print('1 Reservar | 2 Reservar provisória | 3 Confirmar provisória | 4 Consultar')
        print('5 Trocar responsável | 6 Cancelar | 7 Listar todas | 0 Voltar')
        opcao = input('Escolha: ')
        if opcao == '1':
            sala, data, horario = pedir_reserva()
            reservas.reservar(sala, data, horario, input('Responsável: '))
        elif opcao == '2':
            sala, data, horario = pedir_reserva()
            reservas.reservar(sala, data, horario, input('Responsável: '), provisoria=True)
        elif opcao == '3':
            reservas.confirmar(*pedir_reserva())
        elif opcao == '4':
            reservas.consultar(*pedir_reserva())
        elif opcao == '5':
            sala, data, horario = pedir_reserva()
            reservas.trocar_responsavel(sala, data, horario, input('Novo responsável: '))
        elif opcao == '6':
            reservas.cancelar(*pedir_reserva())
        elif opcao == '7':
            reservas.listar_todas()
        elif opcao == '0':
            return


def menu_relatorios():
    while True:
        print('\n--- RELATÓRIOS ---')
        print('1 Ocupação por sala | 2 Reservas de uma sala | 3 Reservas de um responsável | 0 Voltar')
        opcao = input('Escolha: ')
        if opcao == '1':
            reservas.ocupacao()
        elif opcao == '2':
            reservas.da_sala(input('Código da sala: '))
        elif opcao == '3':
            reservas.do_responsavel(input('Nome do responsável: '))
        elif opcao == '0':
            return


def main():
    db.criar_indices()
    while True:
        print('\n=== AGENDAMENTO DE SALAS E LABORATÓRIOS ===')
        print('1 Salas | 2 Reservas | 3 Relatórios | 0 Sair')
        opcao = input('Escolha: ')
        if opcao == '1':
            menu_salas()
        elif opcao == '2':
            menu_reservas()
        elif opcao == '3':
            menu_relatorios()
        elif opcao == '0':
            break
    db.client.close()


main()
