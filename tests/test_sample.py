from . auto_lobao import *


import pytest
import pyodbc


@pytest.mark.parametrize('server, db_name, expected_result', [
    ('SQLPW90DB03\DBINST3, 1443', 'BDintelicanais', True),  # Defina os valores de teste e o resultado esperado
    ('SQLPW90DB03\DBINST3, 1443', 'BDQualivendas', True),
    ('invalid_server', 'invalid_db', False),
])
def test_criar_conexao(server, db_name, expected_result):
    # Substitua 'seu_modulo' pelo nome do módulo onde a função criar_conexao está definida
    # Certifique-se de configurar 'segredos.db_server' e 'segredos.db_name' adequadamente para seus testes
    assert bool(criar_conexao(server, db_name)) == expected_result
