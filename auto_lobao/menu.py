import subprocess


def menu():
    subprocess.run('cls', shell=True)
    print(
        '----------------- Menu de Automações de Atividades -----------------'
    )
    print('')
    print(f'Data de Hoje: ')
    print(
        '--------------- Atividades Relacionadas a Tendência -----------------'
    )
    print('1) Verifica duplicidades na BOV')
    print('2) Calcular tendência HoltWinters')
    print('3) Enviar tendência para Operações')
    print('4) Atualizar tendência Gross (enviado pelo Amado)')
    print('5) Enviar tendências para tabela de histórico')
    print('6) Libera tendências processo legado')
    print(
        '--------------- Atividades Receita Contratada -----------------------'
    )
    print('9) Procedures Receita Contratada')
    print('10) Gerar tabelas Ofertas vs De-Para Ticket')
    print('')
    print(
        '--------------- Atividades Cargas de Metas/Orçamento ----------------'
    )
    print('11) Carga Meta Diaria (CDO) ')
    print('12) Carga Meta POVE (CDO)')
    print('')
    print(
        '--------------- Atividades Relacionadas a PDVs/Carteira -------------'
    )
    print('15) Envia Lista de PDV Outros')
    print('')
    print('')
    print('')
    print(
        '---------------------------------------------------------------------'
    )
    print('20) Sair')
    print(
        '-------------------------------------------------------------------'
    )

    selecionada = input('Selecione uma das opções acima: #')

    return selecionada
