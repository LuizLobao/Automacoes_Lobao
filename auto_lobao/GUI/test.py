import PySimpleGUI as sg


menu_def = [
    ['Arquivo',['Abrir','Salvar','Sair']],
    ['Editar',['Copiar','Cortar','Colar','Desfazer']],
    ['Sobre','Ajuda'],
]



layout = [
    [sg.Menu(menu_def, key='-MENU-')],
    [sg.CalendarButton('Data')],
    [sg.vtop([
        sg.Text('Rotinas'), 
        sg.Combo(values=['Verificar Duplicidade BOV', 
                           'Calcular Tendências', 
                           'Enviar Tendência Operações',
                           'Salvar Tendência Histórica',
                           'Liberar Tendência Processo Legado',
                           'Procedures Receita Contratada',
                           'Gerar tabelas Ofertas vs De-Para Ticket',
                           '------'], size=(40,6), key='-ROTINAS-')
        ])],
    [sg.Button('Botão', key='-BOTAO1-')],
    [sg.Input(key = '-INPUT-')],
    
]


window = sg.Window("Automações Lobão", layout)

while True:
    event, values = window.read()

    if event == sg.WIN_CLOSED:
        break
    # --------- MENU -------------
    if event == 'Abrir':
        sg.popup('Abrir', '','')
    if event == 'Salvar':
        sg.popup('Salvar', 'texto Salvar', 'texto 2 Salvar...')
    if event == 'Sair':
        sg.popup('Sair', 'texto Sair', 'texto 2 Sair...')
    if event == 'Ajuda':
        sg.popup('Ajuda', 'texto Ajuda', 'texto 2 Ajuda...')
    # --------- DEMAIS ------------
    if event == '-BOTAO1-':
        print(values)
window.close()    