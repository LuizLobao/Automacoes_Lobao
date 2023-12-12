
import flet as ft

def tendencias(router):
    
    content = ft.Column(
               
            [
                ft.Row(
                [
                    ft.Text("Tendência", size=30), 
                    ft.IconButton(icon=ft.icons.INSERT_CHART_OUTLINED, icon_size=30),
                    ], 
                alignment=ft.MainAxisAlignment.CENTER
            ),
             ft.Tabs(
                selected_index=0,
                animation_duration=300,
            tabs=[
                ft.Tab(
                        text="Calcular Tendência",
                        icon=ft.icons.BAR_CHART_OUTLINED,
                        content= ft.Container(
                                        ft.Text('TESTE1')
                                )
                    ),
                ft.Tab(
                    text="Enviar p/ Operações",
                    icon=ft.icons.ATTACH_EMAIL_OUTLINED,
                    content=ft.Text("This is Tab 2"),
                ),
                ft.Tab(
                    text="Copiar para Histórico",
                    icon=ft.icons.FILE_COPY,
                    content=ft.Text("This is Tab 3"),
                ),
                ft.Tab(
                    text="Liberar Legado",
                    icon=ft.icons.BOOKMARKS,
                    content=ft.Text("This is Tab 4"),
                ),
        ],
        expand=1,
    )   

            ]
        )
    
    
    

    
    
   
    return content