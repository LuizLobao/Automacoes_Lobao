import configparser
import logging
import numpy as np
import pandas as pd
import pypyodbc as odbc
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
import urllib
import os
from datetime import datetime, timedelta


AAAAMMDD = (datetime.today()).strftime('%Y%m%d')
AAAAMM = (datetime.today()).strftime('%Y%m')
AAAAMMv = int((datetime.today()).strftime('%Y%m'))
MM_AAAA = (datetime.today()).strftime('%m/%Y')


user_id = os.getlogin()
FORMAT = f'%(asctime)s | %(levelname)s | %(filename)s | User: {user_id} | %(message)s'
logging.basicConfig(
    level=logging.INFO, filename='logs/auto_lobao.log', format=FORMAT
)


from funcoes import executar_sql, criar_arquivo_zip


def meta_pove_para_csv(config):
    diretorio = config['DEFAULT']['dir_rede_metas']
    arquivopove = config['DEFAULT']['arquivo_meta_pove']
    caminho = diretorio + arquivopove

    meta_pove_df = pd.read_excel(caminho, sheet_name=1, header=1)
    meta_pove_df = meta_pove_df.drop(columns='Unnamed: 0')
 
    meta_pove_df['INDICADOR'] = meta_pove_df['INDICADOR'].replace('Meta', 'META')
    meta_pove_df['SEGMENTO'] = meta_pove_df['SEGMENTO'].replace('VA', 'VAREJO')
    meta_pove_df['SEGMENTO'] = meta_pove_df['SEGMENTO'].replace('EM', 'EMPRESARIAL')
    meta_pove_df['Tipo'] = meta_pove_df['Tipo'].replace('Aquisição', 'NOVOS CLIENTES')
    meta_pove_df['Tipo'] = meta_pove_df['Tipo'].replace('Migração', 'MIG BASE')
    meta_pove_df['Gestão'] = meta_pove_df['Gestão'].replace('TELEAGENTES TLV NACIONAL', 'TLV PP')
    meta_pove_df['Canal'] = meta_pove_df['Canal'].replace('Canais de Base', 'OUTROS')
    
    meta_pove_df = meta_pove_df.loc[meta_pove_df['Produto'] == 'BANDA LARGA']
    meta_pove_df = meta_pove_df.loc[meta_pove_df['Anomes'] == AAAAMMv]

    meta_pove_df['DT_REFERENCIA'] = f'01/{MM_AAAA}'
    meta_pove_df['DS_UGR'] = 'HC'
    meta_pove_df['DS_GRUPO_INDICADOR'] = 'FISICOS'
    meta_pove_df['CD_ACESSO_GPON'] = np.nan
    meta_pove_df['CD_CONTA_FATURA'] = np.nan
    meta_pove_df['CD_IDENT_PESSOA'] = np.nan
    meta_pove_df['DS_TP_POSSE'] = np.nan
    meta_pove_df['nu_localidade'] = np.nan
    meta_pove_df['DS_CAMPANHA'] = np.nan
    meta_pove_df['DS_OFERTA'] = np.nan
    meta_pove_df['CD_CANAL_SAP_ORI'] = np.nan
    meta_pove_df['CD_CANAL_SAP'] = np.nan
    meta_pove_df['CD_SURVEY'] = np.nan
    meta_pove_df['CD_CELULA'] = np.nan
    meta_pove_df['DS_VELOCIDADE'] = np.nan
    meta_pove_df['DS_NUMERO_PEDIDO'] = np.nan
    meta_pove_df['DS_NUMERO_PEDIDO_ORIG'] = np.nan
    meta_pove_df['VL_OFERTA'] = np.nan


    meta_pove_df = meta_pove_df.rename(columns={'INDICADOR':'DS_TIPO', 
                                 'Tipo':'DS_DET_INDICADOR',
                                 'GRUPO_PLANO':'DS_PRODUTO',
                                 'SEGMENTO':'DS_UNIDADE_NEGOCIO',
                                 'UF':'NO_CURTO_TERRITORIO',
                                 'MUNICIPIO':'NO_MUNICIPIO',
                                 'Canal':'DS_CANAL_BOV',
                                 'INDB':'DS_INDICADOR',
                                 'Meta':'QTD',
                                 'Anomes':'DT_ANOMES'})
    
    meta_pove_df = meta_pove_df[['DS_TIPO','DS_PRODUTO','DS_UGR','DS_GRUPO_INDICADOR'
                                ,'DS_INDICADOR','DS_DET_INDICADOR','DT_REFERENCIA','CD_ACESSO_GPON'
                                ,'CD_CONTA_FATURA','CD_IDENT_PESSOA','DS_UNIDADE_NEGOCIO','DS_TP_POSSE'
                                ,'NO_CURTO_TERRITORIO','NO_MUNICIPIO','nu_localidade','DS_CAMPANHA'
                                ,'DS_OFERTA','DS_CANAL_BOV','CD_CANAL_SAP_ORI','CD_CANAL_SAP','CD_SURVEY'
                                ,'CD_CELULA','DS_VELOCIDADE','DS_NUMERO_PEDIDO','DS_NUMERO_PEDIDO_ORIG','VL_OFERTA'
                                ,'DT_ANOMES','QTD']]
    
    anomes_df = meta_pove_df['DT_ANOMES'].iloc[0]

    meta_pove_df.to_csv(
        diretorio + f'meta_pove_{anomes_df}.csv',
        sep=';',
        header=True,
        index=False,
        decimal=',',
        mode='w',
    )
    #print(meta_pove_df)
    logging.info(f'Arquivo de meta POVE criado em CSV: meta_pove_{anomes_df}.csv')
    return meta_pove_df


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


def carregar_metapove_para_banco_de_dados(meta_pove_df, config):
    anomes_df = meta_pove_df['DT_ANOMES'].iloc[0]

    comando_sql = (
        f"delete from dbo.TBL_CDO_FISICOS_METAS where DT_ANOMES = {AAAAMM} and DS_TIPO = 'META' "
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

    logging.info(f'Iniciando carga de Meta em : TBL_CDO_FISICOS_METAS')
    meta_pove_df.to_sql(
        'TBL_CDO_FISICOS_METAS',
        engine,
        if_exists='append',
        index=False,
        schema='dbo',
    )
    logging.info(f'Fim da carga de Meta em : TBL_CDO_FISICOS_METAS')

def carregar_dados_para_banco_de_dados(meta_diaria_df, config):
    anomes_df = meta_diaria_df['ANOMES'].iloc[0]

    comando_sql = (f'delete from dbo.TBL_PC_META_DIARIA_VL_VLL where anomes = {anomes_df}')
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


#def main():
    #config = configparser.ConfigParser()
    #config.read('auto_lobao/config.ini', encoding='utf-8')
#
    #diretorio = config['DEFAULT']['dir_rede_metas']
    #arquivo = config['DEFAULT']['arquivo_meta_diaria']
    #arquivopove = config['DEFAULT']['arquivo_meta_pove']
#
    #caminho = diretorio + arquivo
    #base, ext = os.path.splitext(arquivo)
    #caminhozip = diretorio+f'{base}-{AAAAMMDD}.zip'
    #meta_diaria_df = carregar_dados_excel_para_csv(config)
    #criar_arquivo_zip(caminho, caminhozip)
    #os.remove(caminho)
    #carregar_dados_para_banco_de_dados(meta_diaria_df, config)
#
#
    #caminho_pove = diretorio + arquivopove
    #basepove, ext = os.path.splitext(arquivopove)
    #caminhopovezip = diretorio+f'{basepove}-{AAAAMMDD}.zip'
    #meta_pove_df = meta_pove_para_csv(config)
    #criar_arquivo_zip(caminho_pove, caminhopovezip)
    #os.remove(caminho_pove)
    #carregar_metapove_para_banco_de_dados(meta_pove_df, config)

#if __name__ == '__main__':
#    main()
