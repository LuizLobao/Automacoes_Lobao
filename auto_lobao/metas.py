import configparser
import logging
import pandas as pd
import pypyodbc as odbc
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
import urllib
import os
from datetime import datetime, timedelta


AAAAMMDD = (datetime.today()).strftime('%Y%m%d')


user_id = os.getlogin()
FORMAT = f'%(asctime)s | %(levelname)s | %(filename)s | User: {user_id} | %(message)s'
logging.basicConfig(
    level=logging.INFO, filename='logs/auto_lobao.log', format=FORMAT
)


from funcoes import executar_sql, criar_arquivo_zip


def carregar_dados_excel_para_csv(config):
    diretorio = config['DEFAULT']['dir_rede_metas']
    arquivo = config['DEFAULT']['arquivo_meta_diaria']
    caminho = diretorio + arquivo

    meta_diaria_df = pd.read_excel(caminho, sheet_name=0, header=0)
    meta_diaria_df = meta_diaria_df.drop(columns='TOTAL')

    # Realize as transformações nos dados, como a transposição e substituições
    meta_diaria_df = pd.melt(
        meta_diaria_df,
        id_vars=[
            'ORIGEM',
            'TIPO',
            'SEGMENTO',
            'GESTAO',
            'FILIAL',
            'MUNICIPIO',
            'INDICADOR',
            'ANOMES',
        ],
        var_name='DIA',
        value_name='VALOR',
    )
    # Usando o replace para arrumar as informações de cada coluna
    meta_diaria_df['SEGMENTO'] = meta_diaria_df['SEGMENTO'].replace('VA', 'VAREJO')
    meta_diaria_df['SEGMENTO'] = meta_diaria_df['SEGMENTO'].replace('EM', 'EMPRESARIAL')
    meta_diaria_df['GESTAO'] = meta_diaria_df['GESTAO'].replace('Canais de Base', 'OUTROS')
    meta_diaria_df['GESTAO'] = meta_diaria_df['GESTAO'].replace('TELEAGENTES TLV NACIONAL', 'TLV PP')
    meta_diaria_df['DIA'] = meta_diaria_df['DIA'].str.replace('D0', '')
    meta_diaria_df['DIA'] = meta_diaria_df['DIA'].str.replace('D', '')
    anomes_df = meta_diaria_df['ANOMES'].iloc[0]

    meta_diaria_df.to_csv(
        diretorio + f'meta_diaria_{anomes_df}.csv',
        sep=';',
        header=True,
        index=False,
        decimal=',',
        mode='w',
    )
    logging.info(f'Arquivo de meta criado em CSV: meta_diaria_{anomes_df}.csv')
    return meta_diaria_df


def carregar_dados_para_banco_de_dados(meta_diaria_df, config):
    anomes_df = meta_diaria_df['ANOMES'].iloc[0]

    comando_sql = (
        f'delete from dbo.TBL_PC_META_DIARIA_VL_VLL where anomes = {anomes_df}'
    )
    executar_sql(comando_sql)

    SERVER_NAME = r'SQLPW90DB03\DBINST3,1443'
    DATABASE_NAME = 'BDintelicanais'
    connection_string = f"""
    Driver={{ODBC Driver 13 for SQl Server}};
    Server={SERVER_NAME};
    Database={DATABASE_NAME};
    Trusted_Connection=yes;
    """
    connection_url = URL.create(
        'mssql+pyodbc', query={'odbc_connect': connection_string}
    )
    engine = create_engine(connection_url, module=odbc)

    logging.info(f'Iniciando carga de Meta em : TBL_PC_META_DIARIA_VL_VLL')
    meta_diaria_df.to_sql(
        'TBL_PC_META_DIARIA_VL_VLL',
        engine,
        if_exists='append',
        index=False,
        schema='dbo',
    )
    logging.info(f'Fim da carga de Meta em : TBL_PC_META_DIARIA_VL_VLL')


def main():
    config = configparser.ConfigParser()
    config.read('auto_lobao/config.ini', encoding='utf-8')

    diretorio = config['DEFAULT']['dir_rede_metas']
    arquivo = config['DEFAULT']['arquivo_meta_diaria']
    caminho = diretorio + arquivo
    base, ext = os.path.splitext(arquivo)
    caminhozip = diretorio+f'{base}-{AAAAMMDD}.zip'

    meta_diaria_df = carregar_dados_excel_para_csv(config)
    
    criar_arquivo_zip(caminho, caminhozip)
    # Excluir o arquivo de origem após criar o ZIP
    os.remove(caminho)

    carregar_dados_para_banco_de_dados(meta_diaria_df, config)


if __name__ == '__main__':
    main()
