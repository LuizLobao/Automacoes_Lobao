from auto_lobao import *


import pytest
import pyodbc

def teste_basico_inicial ():
    assert 1==1

@pytest.mark.parametrize('server, db_name, expected_result', [
    ('SQLPW90DB03\DBINST3, 1443', 'BDintelicanais', True),  # Defina os valores de teste e o resultado esperado
    ('SQLPW90DB03\DBINST3, 1443', 'BDQualivendas', True),
    ('invalid_server', 'invalid_db', False),
])
def test_criar_conexao(server, db_name, expected_result):
    assert bool(criar_conexao(server, db_name)) == expected_result


