import flet as ft

def main(page: ft.Page):
    page.title = "Automações Lobão"
    page.theme_mode = "dark"
    

    def route_change(route):
        page.views.clear()
        page.views.append(
            ft.View(
                "/",
                [
                    
                    ft.AppBar(title=ft.Text("Home"), bgcolor=ft.colors.SURFACE_VARIANT),
                    ft.Row([
                        ft.ElevatedButton("Tendências", on_click=lambda _: page.go("/tendencia")),
                        ft.ElevatedButton("Receita Contratada", on_click=lambda _: page.go("/receita")),
                        ft.ElevatedButton("Metas", on_click=lambda _: page.go("/metas")),
                        ft.ElevatedButton("PDVs", on_click=lambda _: page.go("/pdv")),
                        ft.IconButton(icon = ft.icons.BUILD_CIRCLE, tooltip='CONFIGURAÇÕES', disabled=True)
                        ],wrap=True, alignment=ft.MainAxisAlignment.CENTER
                        ),
                ],
            )
        )
        if page.route == "/tendencia":
            
            conteudo = (ft.Container(
                                content=(
                                    ft.Row(
                                            [
                                            ft.Text('Texto depois da divisória 1'),
                                            ft.Text('Texto depois da divisória 2'),
                                            ],
                                        )                                    
                                        )
                                    )
                                
                            )
                       
            
            
            page.views.append(
                ft.View(
                    "/tendencia",
                    [
                        ft.AppBar(title=ft.Text("Tendências"), bgcolor=ft.colors.SURFACE_VARIANT),
                        ft.Row(
                                [
                                    ft.ElevatedButton("Verificar Duplicidade", disabled=True, tooltip='EM DESENVOLVIMENTO'),
                                    ft.ElevatedButton("Calcular Tendência de VL e VLL", ),
                                    ft.ElevatedButton("Enviar para Operações", tooltip='Envia arquivo Excel com a tendência para Amado'),
                                    ft.ElevatedButton("Tendência Gross", disabled = True, tooltip='EM DESENVOLVIMENTO - Rodar no Excel'),
                                    ft.ElevatedButton("Gravar Histórico", tooltip='Grava tendência de hoje em tabela histórica para acompanhamento'),
                                    ft.ElevatedButton("Libera Legado", tooltip='Libera tendencia modelo antigo para demais processos'),
                                ]
                            ,wrap=True, alignment=ft.MainAxisAlignment.CENTER),
                        ft.Divider(),
                        #----------incluir aqui o conteudo --------------
                        conteudo,

                        #----------fim do conteudo --------------
                    ],
                )
            )
        if page.route == "/receita":
            page.views.append(
                ft.View(
                    "/receita",
                    [
                        ft.AppBar(title=ft.Text("Receita Contratada"), bgcolor=ft.colors.SURFACE_VARIANT),
                    ],
                )
            )
        if page.route == "/metas":
            page.views.append(
                ft.View(
                    "/metas",
                    [
                        ft.AppBar(title=ft.Text("Carga de Metas"), bgcolor=ft.colors.SURFACE_VARIANT),
                    ],
                )
            )
        if page.route == "/pdv":
            page.views.append(
                ft.View(
                    "/pdv",
                    [
                        ft.AppBar(title=ft.Text("De-Para de PDVs"), bgcolor=ft.colors.SURFACE_VARIANT),
                    ],
                )
            )
        page.update()

    def view_pop(view):
        page.views.pop()
        top_view = page.views[-1]
        page.go(top_view.route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop
    page.go(page.route)


ft.app(target=main)