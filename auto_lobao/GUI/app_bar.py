import flet as ft


def NavBar(page):



    NavBar = ft.AppBar(
            leading=ft.Icon(ft.icons.CONVEYOR_BELT),
            leading_width=40,
            title=ft.Text("Automações Lobão"),
            center_title=False,
            bgcolor=ft.colors.SURFACE_VARIANT,
            actions=[
                ft.IconButton(ft.icons.HOME, tooltip='Inicial', on_click=lambda _: page.go('/')),
                ft.IconButton(ft.icons.INSERT_CHART_OUTLINED, tooltip='Tendência', on_click=lambda _: page.go('/tendencias')),
                ft.IconButton(ft.icons.ATTACH_MONEY_OUTLINED, tooltip='Receita Contratada', on_click=lambda _: page.go('/receitacontratada')),
                ft.IconButton(ft.icons.PERSON_PIN_OUTLINED, tooltip='De-Para Canais', on_click=lambda _: page.go('/deparacanais')),
                ft.IconButton(ft.icons.CRISIS_ALERT_SHARP, tooltip='Metas', on_click=lambda _: page.go('/')),
                ft.IconButton(ft.icons.PERSON_ROUNDED, on_click=lambda _: page.go('/profile')),
                ft.IconButton(ft.icons.SETTINGS_ROUNDED, on_click=lambda _: page.go('/settings'))
                
                
            ]
        )

    return NavBar