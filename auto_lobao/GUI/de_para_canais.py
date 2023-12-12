import sys
sys.path.insert(0, r'C:\Users\oi066724\Documents\Python\Automacoes_Lobao\auto_lobao')
import flet as ft
import funcoes
from auto_lobao import enviar_lista_pdv_outros


def de_para_canais(router):
    
    def click_pdvoutros(e,page):
        print('botão clicado')
        pb = ft.ProgressBar(width=400, color="amber", bgcolor="#eeeeee")
        page.add(pb)
        page.update()
        #enviar_lista_pdv_outros()

    content = ft.Column(
               
            [
                ft.Row(
                [
                    ft.Text("De-Para Canais"), 
                    ft.IconButton(icon=ft.icons.PERSON_PIN_OUTLINED, icon_size=30),
                    ], 
                alignment=ft.MainAxisAlignment.CENTER
            ),
            ft.Row(
                [
                    ft.Text("De-Para Canais", size=10), 
                    ft.IconButton(icon=ft.icons.PERSON_PIN_OUTLINED, icon_size=20, on_click=lambda e: click_pdvoutros(e, page),),
                    ], 
                alignment=ft.MainAxisAlignment.START
            ),   

            ]
        )
    
   
    return content