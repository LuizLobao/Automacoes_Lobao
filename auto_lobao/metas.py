import configparser
import pandas as pd

config = configparser.ConfigParser()
config.read('auto_lobao/config.ini', encoding='utf-8')


def prepara_meta_diaria():
    diretorio = config['DEFAULT']['dir_rede_metas']
    arquivo = config['DEFAULT']['arquivo_meta_diaria']
    caminho = diretorio+arquivo
    
    df = pd.read_excel(caminho, sheet_name=0, header=0)
    df = df.drop(columns='TOTAL')
    
    # Usando a função melt para transpor as colunas D01, D02, D03, D04 em uma coluna "DIA"
    df = pd.melt(df, id_vars=['ORIGEM', 'TIPO', 'SEGMENTO', 'GESTAO', 'FILIAL','MUNICIPIO', 'INDICADOR','ANOMES'], var_name='DIA', value_name='VALOR')
    # Usando o replace para arrumar as informações de cada coluna
    df['SEGMENTO'] = df['SEGMENTO'].replace('VA', 'VAREJO')
    df['SEGMENTO'] = df['SEGMENTO'].replace('EM', 'EMPRESARIAL')
    df['GESTAO'] = df['GESTAO'].replace('Canais de Base','OUTROS')
    df['GESTAO'] = df['GESTAO'].replace('TELEAGENTES TLV NACIONAL','TLV PP')
    df['DIA'] = df['DIA'].str.replace('D0', '')
    df['DIA'] = df['DIA'].str.replace('D', '')
    print(df)

    df.to_csv(diretorio+'meta_diaria.csv', sep=';',header=True, index=False, decimal=','  , mode='w')
    

prepara_meta_diaria()