import logging
import os
import pandas as pd
import pyodbc
import shutil
import zipfile
import win32com.client as win32

import segredos

user_id = os.getlogin()
FORMAT = f'%(asctime)s | %(levelname)s | %(filename)s | User: {user_id} | %(message)s'
logging.basicConfig(level=logging.INFO, filename="logs/auto_lobao.log", format=FORMAT)



def criar_conexao():
    dados_conexao = (
        "Driver={SQL Server};"
        f"Server={segredos.db_server};"
        f"Database={segredos.db_name};"
        "Trusted_Connection=yes;"
        # f"UID={segredos.db_user};"
        # f"PWD={segredos.db_pass}"
    )
    return pyodbc.connect(dados_conexao)

def executa_procedure_sql(nome_procedure, param=None):
    conexao = criar_conexao()

    try:
        cursor = conexao.cursor()
        if param:
            cursor.execute(f'SET NOCOUNT ON; EXEC {nome_procedure} {param}')
        else:
            cursor.execute(f'SET NOCOUNT ON; EXEC {nome_procedure}')
        conexao.commit()
        logging.info(f'Procedure {nome_procedure} executada.')
    
    except Exception as e:
        logging.error(f"Erro ao executar a procedure: {e}") #TODO trocar por log
    
    finally:
        conexao.close()

def enviaEmailComAnexo(EmailTo, Subject, Body, EmailCC=None, File=None):
    try:
        # Criar a integração com o Outlook
        outlook = win32.Dispatch('outlook.application')

        # Criar um email
        email = outlook.CreateItem(0)

        # Configurar as informações do seu email
        email.To = EmailTo

        if EmailCC:
            email.CC = EmailCC

        email.Subject = Subject
        email.HTMLBody = Body

        if File:
            email.Attachments.Add(File)

        email.Send()
        logging.info("Email enviado com sucesso!")
    except Exception as e:
        logging.error(f"Ocorreu um erro ao enviar o email: {str(e)}")

def executa_arquivo_sql(arquivo_sql):
    conexao = criar_conexao()
    try:
        caminho_arquivo_sql = arquivo_sql

        with open(caminho_arquivo_sql, 'r', encoding='utf-8') as arquivo:
            conteudo_sql = arquivo.read()
            cursor = conexao.cursor()
            cursor.execute(conteudo_sql)
            conexao.commit()

    except Exception as e:
        logging.error(f"Erro ao executar o arquivo SQL: {e}")
    
    finally:
        conexao.close()

def executar_sql(comando_sql):
    try:
        conexao = criar_conexao()
        logging.info("Conectado ao banco para executar SQL")
        cursor = conexao.cursor()
        cursor.execute(comando_sql)
        conexao.commit()
        conexao.close()
    except Exception as e:
        logging.error(f"Ocorreu um erro ao executar o SQL: {str(e)}")

def copia_e_renomeia_arquivo(origem, destino):
    try:
        shutil.copy(origem, destino)
        logging.info(f'Arquivo copiado de {origem} para {destino}') 
    except FileNotFoundError:
        logging.error(f'Erro: Arquivo de origem não encontrado em {origem}')
    except Exception as e:
        logging.error(f'Ocorreu um erro ao copiar o arquivo: {str(e)}')

def verifica_duplicidade_bov(arquivo_zip, arquivo, campo_check):
    try:
        arquivo_sem_caminho = arquivo_zip.split('\\')[-1].split('.')[0]

        with zipfile.ZipFile(arquivo_zip, 'r') as zip_file:
            with zip_file.open(arquivo) as txt_file:
                df = pd.read_csv(txt_file, sep=';', encoding='ANSI', quotechar='"', low_memory=False) 
        
        contagem_codigos = df.groupby(campo_check).size().reset_index(name='Contagem')
        contagem_codigos = contagem_codigos.sort_values(by='Contagem', ascending=False)

        check = contagem_codigos.groupby('Contagem').size().reset_index(name='check')
        
        filtro_igual_1 = check['Contagem'] == 1
        filtro_maior_1 = check['Contagem'] > 1

        soma_igual_1 = check.loc[filtro_igual_1, 'check'].sum()
        soma_maior_1 = check.loc[filtro_maior_1, 'check'].sum()
        total_registros = soma_igual_1 + soma_maior_1

        percentual_duplicados = (soma_maior_1 / total_registros) * 100
        if percentual_duplicados > 1: #maior que 1pct
            logging.warning(f'ATENÇAO: Arquivo {arquivo_sem_caminho} com percentual de {percentual_duplicados:.2f}% duplicados')

        resultado = f'Arquivo: {arquivo_sem_caminho} : temos {soma_maior_1} duplicados e {soma_igual_1} sem duplicadas: {percentual_duplicados:.2f}%'

        logging.info(resultado)

        return(percentual_duplicados)

    except Exception as e:
        logging.error(f"Ocorreu um erro no arquivo {arquivo_sem_caminho}: {str(e)}")


caminho = 'C:\\JETL\\BASE\\old\\'
arquivos_colunas = [
	('BOV_1059_20231025.TXT.zip','BOV_1059.TXT', 'NUMERO_PEDIDO'),
	('BOV_1065_20231025.TXT.zip','BOV_1065.TXT', 'NUMERO_PEDIDO'),
	('BOV_6163_20231025.TXT.zip','BOV_6163.TXT', 'cd_item_ordem'),
	('BOV_6162_20231025.TXT.zip', 'BOV_6162.TXT', 'cd_item_ordem')
]

for arquivo_zip, arquivo, coluna in arquivos_colunas:
	verifica_duplicidade_bov(f'{caminho}{arquivo_zip}', arquivo, coluna)