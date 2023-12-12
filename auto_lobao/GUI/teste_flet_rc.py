import flet as ft

def main(page: ft.Page):
    page.title = "Automações Lobão"
    page.vertical_alignment = ft.MainAxisAlignment.START

    txt_number = ft.TextField(value="0", text_align=ft.TextAlign.RIGHT, width=100)

    def minus_click(e):
        txt_number.value = str(int(txt_number.value) - 1)
        page.update()

    def plus_click(e):
        txt_number.value = str(int(txt_number.value) + 1)
        page.update()

    rail = ft.NavigationRail(
        selected_index=0,
        label_type=ft.NavigationRailLabelType.ALL,
        # extended=True,
        min_width=100,
        min_extended_width=300,
        #leading=ft.FloatingActionButton(icon=ft.icons.CREATE, text="Add"),
        group_alignment=-0.9,
        destinations=[
            ft.NavigationRailDestination(
                icon=ft.icons.HOME_OUTLINED, 
                selected_icon=ft.icons.HOME_ROUNDED, 
                label="Inicial", 
            ),
            ft.NavigationRailDestination(
                icon=ft.icons.INSERT_CHART_OUTLINED, 
                selected_icon=ft.icons.INSERT_CHART_ROUNDED, 
                label="Tendência", 
            ),
            ft.NavigationRailDestination(
                icon=ft.icons.ATTACH_MONEY_OUTLINED,
                selected_icon_content=ft.Icon(ft.icons.ATTACH_MONEY),
                label="Receita Contratada",
            ),
            ft.NavigationRailDestination(
                icon=ft.icons.PERSON_PIN_OUTLINED,
                selected_icon_content=ft.Icon(ft.icons.PERSON_PIN_ROUNDED),
                label_content=ft.Text("De-Para Canais"),
            ),
            ft.NavigationRailDestination(
                icon=ft.icons.SETTINGS_OUTLINED,
                selected_icon_content=ft.Icon(ft.icons.SETTINGS),
                label_content=ft.Text("Settings"),
            ),
        ],
        on_change=lambda e: print("Selected destination:", e.control.selected_index),
    )

    page.add(
        ft.Row(
            [
                rail,
                ft.VerticalDivider(width=1),
                ft.Column([ft.Row(
                    [
                        ft.Icon(name=ft.icons.HOME_OUTLINED, color=ft.colors.GREEN, size=30),
                        ft.Text('RECEITA CONTRATADA', size=30),
                        
                     ],
            ),], alignment=ft.MainAxisAlignment.START, expand=True),
            ],
            expand=True,
        ),

    )

ft.app(target=main)

        