import subprocess

from datetime import datetime, timedelta

hoje = (datetime.today() - timedelta(days=0)).strftime('%d/%m/%Y')

def menu():
    subprocess.run('cls', shell=True)
    print(
        '----------------- Menu de Automações de Atividades -----------------'
    )
    print('')
    print(f'Data de Hoje: {hoje}')
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
    print('10) Procedures Receita Contratada')
    print('11) Gerar tabelas Ofertas vs De-Para Ticket')
    print('')
    print(
        '--------------- Atividades Cargas de Metas/Orçamento ----------------'
    )
    print('20) Carga Meta Diaria (CDO) ')
    print('21) Carga Meta POVE (CDO)')
    print('22) Carga Meta na tbl_re_baseresultados(_Empresarial) ')
    print(
        '--------------- Atividades Relacionadas a PDVs/Carteira -------------'
    )
    print('30) Envia Lista de PDV Outros')
    print('')
    print('')
    print('')
    print(
        '---------------------------------------------------------------------'
    )
    print('99) Sair')
    print(
        '-------------------------------------------------------------------'
    )

    selecionada = input('Selecione uma das opções acima: #')

    return selecionada
