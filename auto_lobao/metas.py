import configparser
import logging
import os
import urllib
from datetime import datetime

import numpy as np
import pandas as pd
import pypyodbc as odbc
from funcoes import criar_arquivo_zip, executar_sql
from sqlalchemy import create_engine
from sqlalchemy.engine import URL

from funcoes import *

pd.options.mode.chained_assignment = None  # default='warn'

AAAAMMDD = (datetime.today()).strftime('%Y%m%d')
AAAAMM = (datetime.today()).strftime('%Y%m')
AAAAMMv = int((datetime.today()).strftime('%Y%m'))
MM_AAAA = (datetime.today()).strftime('%m/%Y')


user_id = os.getlogin()
FORMAT = f'%(asctime)s | %(levelname)s | %(filename)s | User: {user_id} | %(message)s'
logging.basicConfig(
    level=logging.INFO, filename='logs/auto_lobao.log', format=FORMAT
)


def prepara_meta_pove(config):
    '''
    Abrir o arquivo da META POVE original, realizar os ajustes nas nomenclaturas das colunas e registros.
    Duplicar as informações de BANDA LARGA (Fibra e Nova Fibra) e chamar de FIBRA / NOVA FIBRA (GPON)
    Incluir outras colunas que serão necessárias para a carga no banco de dados
    '''
    
    logging.info('Inicio prepara_meta_pove')

    try:
        diretorio = config['DEFAULT']['dir_rede_metas']
        arquivopove = config['DEFAULT']['arquivo_meta_pove']
        caminho = diretorio + arquivopove
        logging.info(f'Prepara_Meta_Pove: Abrindo Arquivo: {caminho}')
        meta_pove_df = pd.read_excel(caminho, sheet_name=1, header=1)
        meta_pove_df = meta_pove_df.drop(columns='Unnamed: 0')
    
        logging.info('Prepara_Meta_Pove: Ajustando Colunas')
        meta_pove_df['INDICADOR'] = meta_pove_df['INDICADOR'].replace('Meta', 'META')
        meta_pove_df['SEGMENTO'] = meta_pove_df['SEGMENTO'].replace('VA', 'VAREJO')
        meta_pove_df['SEGMENTO'] = meta_pove_df['SEGMENTO'].replace('EM', 'EMPRESARIAL')
        meta_pove_df['Tipo'] = meta_pove_df['Tipo'].replace('Aquisição', 'NOVOS CLIENTES')
        meta_pove_df['Tipo'] = meta_pove_df['Tipo'].replace('Migração', 'MIG BASE')
        meta_pove_df['Gestão'] = meta_pove_df['Gestão'].replace('TELEAGENTES TLV NACIONAL', 'TLV PP')
        meta_pove_df['Canal'] = meta_pove_df['Canal'].replace('Canais de Base', 'OUTROS')

        #Filtrar apenas as UGRs que usamos para nossos relatórios
        logging.info('Prepara_Meta_Pove: Aplicando Filtros')
        lista_produto = ['BANDA LARGA','FIXO FIBRA','OI TV FIBRA']
        meta_pove_df = meta_pove_df[meta_pove_df['Produto'].isin(lista_produto)]

        menordata = meta_pove_df['Anomes'].min()
        menordatatxt = str(menordata)

        ano = menordatatxt[:4]
        mes = menordatatxt[4:]

        #print(menordata)

        meta_pove_df = meta_pove_df.loc[meta_pove_df['Anomes'] == menordata]                                 
        #meta_pove_df = meta_pove_df.loc[meta_pove_df['Anomes'] == AAAAMMv]

        #cria df só com banda larga para depois transformar na GPON
        logging.info('Prepara_Meta_Pove: cria df só com banda larga para depois transformar na GPON')
        meta_pove_gpon = meta_pove_df.loc[meta_pove_df['Produto'] == 'BANDA LARGA']
        meta_pove_gpon['Produto'] = np.where((meta_pove_gpon['GRUPO_PLANO'] == 'FIBRA') & 
                                           (meta_pove_gpon['Produto'] == 'BANDA LARGA'), 
                                           'FIBRA', meta_pove_gpon['Produto'])
        meta_pove_gpon['Produto'] = np.where((meta_pove_gpon['GRUPO_PLANO'] == 'NOVA FIBRA') & 
                                           (meta_pove_gpon['Produto'] == 'BANDA LARGA'), 
                                           'NOVA FIBRA', meta_pove_gpon['Produto'])


        #renomeando os produtos com base no Grupo Plano e no Produto
        logging.info('Prepara_Meta_Pove: renomeando os produtos com base no Grupo Plano e no Produto')
        meta_pove_df['Produto'] = np.where((meta_pove_df['GRUPO_PLANO'] == 'FIBRA') & 
                                           (meta_pove_df['Produto'] == 'FIXO FIBRA'), 
                                           'FIXO FIBRA', meta_pove_df['Produto'])
        meta_pove_df['Produto'] = np.where((meta_pove_df['GRUPO_PLANO'] == 'NOVA FIBRA') & 
                                           (meta_pove_df['Produto'] == 'FIXO FIBRA'), 
                                           'FIXO NOVA FIBRA', meta_pove_df['Produto'])
        meta_pove_df['Produto'] = np.where((meta_pove_df['GRUPO_PLANO'] == 'FIBRA') & 
                                           (meta_pove_df['Produto'] == 'BANDA LARGA'), 
                                           'BANDA LARGA FIBRA', meta_pove_df['Produto'])
        meta_pove_df['Produto'] = np.where((meta_pove_df['GRUPO_PLANO'] == 'NOVA FIBRA') & 
                                           (meta_pove_df['Produto'] == 'BANDA LARGA'), 
                                           'BANDA LARGA NOVA FIBRA', meta_pove_df['Produto'])
        meta_pove_df['Produto'] = np.where((meta_pove_df['GRUPO_PLANO'] == 'FIBRA') & 
                                           (meta_pove_df['Produto'] == 'OI TV FIBRA'), 
                                           'OI TV FIBRA', meta_pove_df['Produto'])
        meta_pove_df['Produto'] = np.where((meta_pove_df['GRUPO_PLANO'] == 'NOVA FIBRA') & 
                                           (meta_pove_df['Produto'] == 'OI TV FIBRA'), 
                                           'OI TV NOVA FIBRA', meta_pove_df['Produto'])

        #juntar o DF do meta_pove com a gpon criada acima
        meta_pove_df = pd.concat([meta_pove_df, meta_pove_gpon], ignore_index=True)

        #incluir as demais colunas necessárias para subir no banco de dados
        logging.info('Prepara_Meta_Pove: Cria colunas extras')
        meta_pove_df['DT_REFERENCIA'] = f'01/{mes}/{ano}'
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
        meta_pove_df['DS_SEGMENTACAO'] = np.nan
        meta_pove_df['DS_CLASS_CELULA'] = np.nan

        #renomear o nome das colunas
        logging.info('Prepara_Meta_Pove: Renomear colunas')
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

        #colocar as colunas na ordem necessária
        logging.info('Prepara_Meta_Pove: Colocar colunas na ordem correta')
        meta_pove_df = meta_pove_df[['DS_TIPO','DS_PRODUTO','Produto','DS_UGR','DS_GRUPO_INDICADOR'
                                    ,'DS_INDICADOR','DS_DET_INDICADOR','DT_REFERENCIA','CD_ACESSO_GPON'
                                    ,'CD_CONTA_FATURA','CD_IDENT_PESSOA','DS_UNIDADE_NEGOCIO','DS_TP_POSSE'
                                    ,'NO_CURTO_TERRITORIO','NO_MUNICIPIO','nu_localidade','DS_CAMPANHA'
                                    ,'DS_OFERTA','DS_CANAL_BOV','CD_CANAL_SAP_ORI','CD_CANAL_SAP','CD_SURVEY'
                                    ,'CD_CELULA','DS_VELOCIDADE','DS_NUMERO_PEDIDO','DS_NUMERO_PEDIDO_ORIG','VL_OFERTA'
                                    ,'DT_ANOMES','QTD','DS_SEGMENTACAO','DS_CLASS_CELULA']]
        return meta_pove_df
    
    except Exception as e:
        logging.error(
            f'Ocorreu um erro em prepara_meta_pove: {str(e)}'
        )
        return None


def meta_pove_para_csv(config, dataframe):
    '''
    Recebe o dataframe e salva no formato CSV no diretório de rede, incluindo no nome 
    do arquivo o ANOMES localizado na primeira linha do DF
    '''

    try:
        diretorio = config['DEFAULT']['dir_rede_metas']
        arquivopove = config['DEFAULT']['arquivo_meta_pove']
        caminho = diretorio + arquivopove

        #identifica o ANO-MES da primeira linha do DF
        anomes_df = dataframe['DT_ANOMES'].iloc[0]

        dataframe.to_csv(
            diretorio + f'meta_pove_{anomes_df}.csv',
            sep=';',
            header=True,
            index=False,
            decimal=',',
            mode='w',
        )
        logging.info(f'Arquivo de meta POVE criado em CSV: meta_pove_{anomes_df}.csv')
    
    except Exception as e:
        logging.error(f"Erro durante meta_pove_para_csv: {e}")


def prepara_meta_diaria(config):
    '''
    Abrir o arquivo de metas por dia (CargaMeta_Municipio)
    Apagar a coluna de TOTAL
    Fazer a transposição da tabela, transformando os dias em coluna
    Ajustar o nome de alguns registros nas colunas
    '''
    logging.info('Inicio prepara_meta_diaria')
    try:
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
        meta_diaria_df['GESTAO'] = meta_diaria_df['GESTAO'].replace('TELEAGENTES TLV NACIONAL', 'TLV PP')
        meta_diaria_df['DIA'] = meta_diaria_df['DIA'].str.replace('D0', '')
        meta_diaria_df['DIA'] = meta_diaria_df['DIA'].str.replace('D', '')
    
        return meta_diaria_df

    except Exception as e:
        logging.error(
            f'Ocorreu um erro em prepara_meta_diaria: {str(e)}'
        )
        return None


def meta_diaria_para_csv(config, dataframe):
    '''
    Receber o dataframe depois de ser preparado e salvar como CSV no diretório de rede.
    '''
    try:
        diretorio = config['DEFAULT']['dir_rede_metas']

        anomes_df = dataframe['ANOMES'].iloc[0]

        dataframe.to_csv(
            diretorio + f'meta_diaria_{anomes_df}.csv',
            sep=';',
            header=True,
            index=False,
            decimal=',',
            mode='w',
        )
        logging.info(f'Arquivo de meta criado em CSV: meta_diaria_{anomes_df}.csv')
    except Exception as e:
        logging.error(
            f'Ocorreu um erro em meta_diaria_para_csv: {str(e)}'
        )
    

def carregar_metapove_na_tabela_cdo_metas(config, meta_pove_df):
    '''
    Filtrar apenas os produtos de BANDA LARGA (GPON)
    Apagar a coluna Produto que não será necessária
    Apagar qualquer META que exista na tabela para o mês do dataframe 
    Carregar no banco de dados
    '''

    try:
        anomes_df = meta_pove_df['DT_ANOMES'].iloc[0]

        lista_produto = ['BANDA LARGA FIBRA', 'BANDA LARGA NOVA FIBRA']
        meta_pove_df = meta_pove_df[meta_pove_df['Produto'].isin(lista_produto)]

        meta_pove_df.drop('Produto', inplace=True, axis=1)

        diretorio = config['DEFAULT']['dir_rede_metas']
        meta_pove_df.to_csv(
            diretorio + f'meta_pove_CDO_{anomes_df}.csv',
            sep=';',
            header=True,
            index=False,
            decimal=',',
            mode='w',
        )

        comando_sql = (
            f"delete from dbo.TBL_CDO_FISICOS_METAS where DT_ANOMES = {anomes_df} and DS_TIPO = 'META' "
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
        connection_url = URL.create('mssql+pyodbc', query={'odbc_connect': connection_string})
        engine = create_engine(connection_url, module=odbc)

        logging.info(f'Iniciando carga de Meta em : TBL_CDO_FISICOS_METAS')
        meta_pove_df.to_sql(
            'TBL_CDO_FISICOS_METAS',
            engine,
            if_exists='append',
            index=False,
            schema='dbo',
        )
        logging.info(f'Fim da carga de Meta em : TBL_CDO_FISICOS_METAS ({anomes_df})')

    except Exception as e:
        logging.error(f"Erro durante a carga de Meta Pove: {e}")


def carregar_metadiaria_para_banco_de_dados(meta_diaria_df):
    '''
    Receber o dataframe depois de se tratado.
    Apagar da tabela de Metas os dados do Ano-Mês do DF antes de inserir os dados novos.
    Carregar dataframe na tabela de metas.
    '''

    try:
        anomes_df = meta_diaria_df['ANOMES'].iloc[0]

        logging.info(f'Deletando META para anomes = {anomes_df} em TBL_PC_META_DIARIA_VL_VLL')
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
        connection_url = URL.create('mssql+pyodbc', query={'odbc_connect': connection_string})
        engine = create_engine(connection_url, module=odbc)

        logging.info(f'Iniciando carga de Meta em : TBL_PC_META_DIARIA_VL_VLL')
        meta_diaria_df.to_sql(
            'TBL_PC_META_DIARIA_VL_VLL',
            engine,
            if_exists='append',
            index=False,
            schema='dbo',
        )
        logging.info(f'Fim da carga de Meta em : TBL_PC_META_DIARIA_VL_VLL {anomes_df}')

    except Exception as e:
        logging.error(f"Erro durante a carga de Meta Diária: {e}")


def prepara_meta_tblResultados(config, arquivo_csv):
    '''
    ATENÇÃO: na tblResultados carregamos a VLL como VL
    '''
    diretorio = config['DEFAULT']['dir_rede_metas']
    caminho = diretorio + arquivo_csv
    logging.info(f'Arquivo MetaPOVE para tblResultados:{caminho}')

    df = pd.read_csv(caminho, sep=';',encoding='utf8')
    anomes_df = df['DT_ANOMES'].iloc[0]
    logging.info(f'Anomes DataFrame MetaPOVE para carga em tblResultados:({anomes_df})')
    

    df = df.drop(columns=['DS_PRODUTO','DS_UGR','DS_GRUPO_INDICADOR','DS_NUMERO_PEDIDO','DS_NUMERO_PEDIDO_ORIG',
                          'VL_OFERTA','CD_ACESSO_GPON','CD_CANAL_SAP','CD_SURVEY','CD_CELULA','DS_VELOCIDADE',
                          'CD_CONTA_FATURA','DS_CAMPANHA','DS_OFERTA','CD_CANAL_SAP_ORI','NO_MUNICIPIO','nu_localidade',
                          'CD_IDENT_PESSOA','DS_TP_POSSE','DT_REFERENCIA'])
    
    df = df.rename(columns={'DS_INDICADOR':'INDBD', 
                                 'DS_TIPO':'TIPO_INDICADOR',
                                 'DT_ANOMES':'DATA',
                                 'Produto':'GRUPO_PLANO',
                                 'DS_UNIDADE_NEGOCIO':'SEGMENTO',
                                 'NO_CURTO_TERRITORIO':'FILIAL',
                                 'DS_CANAL_BOV':'CANAL_FINAL',
                                 'QTD':'VALOR'
                                 })
    #incluir as demais colunas necessárias para subir no banco de dados
    df['CANAL_BOV'] = df.loc[:,'CANAL_FINAL']
    df['CANAL_PARA'] = np.nan
    df['COD_SAP'] = np.nan
    df['DDD'] = np.nan
    df['PLANO'] = np.nan
    df['PACOTE'] = np.nan
    df['CAMPANHA'] = np.nan
    df['HL'] = np.nan
    df['VENDEDOR'] = np.nan
    df['ARPU'] = np.nan
    df['PLANO_GERENCIAL'] = np.nan
    df['ZONA_COMPETICAO'] = np.nan
    df['PLANO_OFERTA'] = np.nan
    df['PORTABILIDADE'] = np.nan
    df['MULTIPRODUTO'] = np.nan
    df['IND_COMBO'] = np.nan
    df['PEDIDO_UNICO'] = np.nan


     #Filtrar
    lista = ['NOVOS CLIENTES']
    df = df[df['DS_DET_INDICADOR'].isin(lista)]

    seg = ['VAREJO']
    df = df[df['SEGMENTO'].isin(seg)]

    df['INDBD'] = df['INDBD'].str.upper()
    #df['INDBD'] = df['INDBD'].replace('Gross', 'GROSS')
    #df['INDBD'] = df['INDBD'].replace('gross', 'GROSS')
    #df['INDBD'] = df['INDBD'].replace('Vll', 'VLL')
    #df['INDBD'] = df['INDBD'].replace('vll', 'VLL')

    seg = ['VLL','GROSS']
    df = df[df['INDBD'].isin(seg)]

    df = df[['INDBD','TIPO_INDICADOR','DATA','CANAL_BOV','CANAL_PARA',
             'COD_SAP','FILIAL','DDD','GRUPO_PLANO','PLANO','SEGMENTO',
             'PACOTE','VALOR','CANAL_FINAL','CAMPANHA','HL','VENDEDOR',
             'ARPU','PLANO_GERENCIAL','ZONA_COMPETICAO','PLANO_OFERTA',
             'PORTABILIDADE','MULTIPRODUTO','IND_COMBO','PEDIDO_UNICO']]
    
    df['SEGMENTO'] = df['SEGMENTO'].replace('VAREJO', 'VA')
    df['INDBD'] = df['INDBD'].replace('VLL', 'VL')
    
    df.loc[df['CANAL_FINAL'].str.contains('PAP P', case=False), 'CANAL_FINAL'] = 'PAP Próprio'

    df['CANAL_FINAL'] = df['CANAL_FINAL'].replace('TELEAGENTES TLV NACIONAL', 'TLV PP')
    df.loc[df['CANAL_BOV'].str.contains('PAP P', case=False), 'CANAL_BOV'] = 'PAP Próprio'
    df['CANAL_BOV'] = df['CANAL_BOV'].replace('TELEAGENTES TLV NACIONAL', 'TLV PP')

    logging.info(f'Iniciando criação de CSV do arquivo para tbl_resultados:({anomes_df})')
    df.to_csv(diretorio+f'tbl_resultado_{anomes_df}.csv',sep=';',
        header=True,
        index=False,
        decimal=',',
        mode='w', 
        encoding='utf8')
    
    return(df)


def carregar_meta_tblResultados(meta_tblResultados_df):
    '''
    Receber o dataframe depois de se tratado.
    Apagar da tabela de Metas os dados do Ano-Mês do DF antes de inserir os dados novos.
    Carregar dataframe na tabela de metas.
    '''

    try:
        # Convertendo a coluna 'VALOR' para float
        meta_tblResultados_df['VALOR'] = meta_tblResultados_df['VALOR'].str.replace(',', '.').astype(float)

        anomes_df = meta_tblResultados_df['DATA'].iloc[0]
        logging.info(f'Anomes do meta_tblResultados_df:({anomes_df})')

        logging.info(f'Deletando META para data = {anomes_df} em tbl_re_baseresultados')
        comando_sql = (
            f"delete from dbo.tbl_re_baseresultados where data = {anomes_df} and TIPO_INDICADOR = 'meta' "
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
        connection_url = URL.create('mssql+pyodbc', query={'odbc_connect': connection_string})
        engine = create_engine(connection_url, module=odbc)

        logging.info(f'Iniciando carga de Meta em : tbl_re_baseresultados')
        meta_tblResultados_df.to_sql(
            'tbl_re_baseresultados',
            engine,
            if_exists='append',
            index=False,
            schema='dbo'
        )
        logging.info(f'Fim da carga de Meta em : tbl_re_baseresultados')

    except Exception as e:
        logging.error(f"Erro durante a carga de Meta: {e}")


def prepara_meta_tblResultadosEmpresarial(config, arquivo_csv):
    '''
    ATENÇÃO: na tblResultadosEmpresarial carregamos a VLL como VL
    '''
    diretorio = config['DEFAULT']['dir_rede_metas']
    #arquivo_csv = 'meta_pove_202311.csv'
    caminho = diretorio + arquivo_csv
    logging.info(f'Arquivo MetaPOVE para tblResultadosEmp:{caminho}')

    df = pd.read_csv(caminho, sep=';',encoding='utf8')
    anomes_df = df['DT_ANOMES'].iloc[0]
    logging.info(f'Anomes DataFrame MetaPOVE para carga em tblResultadosEmp:{anomes_df}')

    df = df.drop(columns=['DS_PRODUTO','DS_UGR','DS_GRUPO_INDICADOR','DS_NUMERO_PEDIDO','DS_NUMERO_PEDIDO_ORIG',
                          'VL_OFERTA','CD_ACESSO_GPON','CD_CANAL_SAP','CD_SURVEY','CD_CELULA','DS_VELOCIDADE',
                          'CD_CONTA_FATURA','DS_CAMPANHA','DS_OFERTA','CD_CANAL_SAP_ORI','NO_MUNICIPIO','nu_localidade',
                          'CD_IDENT_PESSOA','DS_TP_POSSE','DT_REFERENCIA'])
    
    df = df.rename(columns={'DS_INDICADOR':'INDBD', 
                                 'DS_TIPO':'TIPO_INDICADOR',
                                 'DT_ANOMES':'DATA',
                                 'Produto':'GRUPO_PLANO',
                                 'DS_UNIDADE_NEGOCIO':'SEGMENTO',
                                 'NO_CURTO_TERRITORIO':'UF_CLIENTE',
                                 'DS_CANAL_BOV':'CANAL_FINAL',
                                 'QTD':'VALOR'
                                 })
    #incluir as demais colunas necessárias para subir no banco de dados
    df['CANAL_BOV'] = df.loc[:,'CANAL_FINAL']
    df['UF_CARTEIRA'] = df.loc[:,'UF_CLIENTE']
    df['CANAL_PARA'] = np.nan
    df['COD_SAP'] = np.nan
    df['DDD'] = np.nan
    df['PLANO'] = np.nan
    df['PACOTE'] = np.nan
    df['CAMPANHA'] = ''
    df['HL'] = ''
    df['VENDEDOR'] = np.nan
    df['ARPU'] = np.nan
    df['PLANO_GERENCIAL'] = ''
    df['ZONA_COMPETICAO'] = np.nan
    df['PLANO_OFERTA'] = ''
    df['PORTABILIDADE'] = ''
    df['MULTIPRODUTO'] = np.nan
    df['IND_COMBO'] = np.nan
    df['PEDIDO_UNICO'] = np.nan
    df['GER_VENDAS'] = np.nan
    df['CANAL_VAREJO'] = np.nan


     #Filtrar
    lista = ['NOVOS CLIENTES']
    df = df[df['DS_DET_INDICADOR'].isin(lista)]

    seg = ['EMPRESARIAL']
    df = df[df['SEGMENTO'].isin(seg)]


    df['INDBD'] = df['INDBD'].str.upper()
    #df['INDBD'] = df['INDBD'].replace('gross', 'GROSS')
    #df['INDBD'] = df['INDBD'].replace('Vll', 'VLL')
    #df['INDBD'] = df['INDBD'].replace('vll', 'VLL')
    
    seg = ['VLL','GROSS']
    df = df[df['INDBD'].isin(seg)]

    df = df[['INDBD','TIPO_INDICADOR','DATA','CANAL_BOV','CANAL_PARA',
             'COD_SAP','UF_CLIENTE','UF_CARTEIRA','DDD','GRUPO_PLANO',
             'PLANO','SEGMENTO','PACOTE','VALOR','CANAL_FINAL','CAMPANHA',
             'HL','VENDEDOR','GER_VENDAS','ARPU','PLANO_GERENCIAL',
             'ZONA_COMPETICAO','PLANO_OFERTA','PORTABILIDADE','IND_COMBO','PEDIDO_UNICO','CANAL_VAREJO']]
    
    df['SEGMENTO'] = df['SEGMENTO'].replace('EMPRESARIAL', 'EM')
    df['INDBD'] = df['INDBD'].replace('VLL', 'VL')
    
    df.loc[df['CANAL_FINAL'].str.contains('PAP P', case=False), 'CANAL_FINAL'] = 'PAP Próprio'

    df['CANAL_FINAL'] = df['CANAL_FINAL'].replace('TELEAGENTES TLV NACIONAL', 'TLV PP')
    df.loc[df['CANAL_BOV'].str.contains('PAP P', case=False), 'CANAL_BOV'] = 'PAP Próprio'
    df['CANAL_BOV'] = df['CANAL_BOV'].replace('TELEAGENTES TLV NACIONAL', 'TLV PP')

    logging.info(f'Iniciando criação de CSV do arquivo para tbl_resultadosEMP:({anomes_df})')
    df.to_csv(diretorio+f'tbl_resultadoemp_{anomes_df}.csv',sep=';',
        header=True,
        index=False,
        decimal=',',
        mode='w', 
        encoding='utf8')
    
    return(df)


def carregar_meta_tblResultadosEmpresarial(meta_tblResultadosEmp_df):
    '''
    Receber o dataframe depois de se tratado.
    Apagar da tabela de Metas os dados do Ano-Mês do DF antes de inserir os dados novos.
    Carregar dataframe na tabela de metas.
    '''
    try:
        # Convertendo a coluna 'VALOR' para float
        meta_tblResultadosEmp_df['VALOR'] = meta_tblResultadosEmp_df['VALOR'].str.replace(',', '.').astype(float)
    
        anomes_df = meta_tblResultadosEmp_df['DATA'].iloc[0]

        logging.info(f'Apagando META de tbl_re_baseresultados_empresarial para data:{anomes_df}')
        comando_sql = (
            f"delete from dbo.tbl_re_baseresultados_empresarial where data = {anomes_df} and TIPO_INDICADOR = 'meta'"
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
    

        logging.info(f'Iniciando carga de Meta em : tbl_re_baseresultados_empresarial')
        meta_tblResultadosEmp_df.to_sql(
            'tbl_re_baseresultados_empresarial',
            engine,
            if_exists='append',
            index=False,
            schema='dbo'
        )
        logging.info(f'Fim da carga de Meta em : tbl_re_baseresultados_empresarial')
    
    except Exception as e:
        logging.error(f"Erro durante a carga de Meta: {e}")

config = configparser.ConfigParser()
config.read('auto_lobao/config.ini', encoding='utf-8')
#arquivo_csv = 'meta_pove_202311.csv'

#meta_tblResultados_df = prepara_meta_tblResultados(config, arquivo_csv)
#carregar_meta_tblResultados(meta_tblResultados_df)

#meta_tblResultadosEmp_df = prepara_meta_tblResultadosEmpresarial(config, arquivo_csv)
#carregar_meta_tblResultadosEmpresarial(meta_tblResultadosEmp_df)