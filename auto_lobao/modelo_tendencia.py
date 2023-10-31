import os
import configparser
from datetime import datetime, timedelta

import pandas as pd
import statsmodels.api as sm
import win32com.client as win32
from dateutil.relativedelta import relativedelta
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.tsa.seasonal import seasonal_decompose

from funcoes import *


config = configparser.ConfigParser()
config.read('auto_lobao/config.ini', encoding='utf-8')


data_referencia = datetime.today() - timedelta(days=1)
AAAAMMDD_referencia = (datetime.today() - timedelta(days=0)).strftime('%Y%m%d')
AAAAMM = (datetime.today()).strftime('%Y%m')
AAAAMMDD = (datetime.today()).strftime('%Y%m%d')
ultimo_dia_do_mes = (
    data_referencia.replace(day=1) + timedelta(days=32)
).replace(day=1) - timedelta(days=1)
dias_faltando = (ultimo_dia_do_mes - data_referencia).days


def puxa_deflac_ref():

    caminho_arquivo_csv = f'temp\\deflac_ref_{AAAAMMDD_referencia}.csv'
    comando_sql = f"""
					SELECT 
						-- a.[dt_anomes]
						a.[DS_PRODUTO]
						,a.[DS_UNIDADE_NEGOCIO]
						,CASE when b.DS_GESTAO = 'GESTAO NACIONAL' and DS_CANAL_FINAL in ('TLV RECEPTIVO','TLV ATIVO','TLV PP') then 'TLV'
							when b.DS_GESTAO = 'GESTAO NACIONAL' and DS_CANAL_FINAL in ('WEB') then 'WEB'
							when b.DS_GESTAO = 'GESTAO REGIONAL' then c.COD_REGIONAL
							else b.DS_GESTAO
							END  AS GESTAO
						,CASE WHEN RIGHT(CONVERT(DATE,a.[DT_REFERENCIA],103),2) IN ('01','02','03','04','05','06','07') THEN 'S1'
							WHEN RIGHT(CONVERT(DATE,a.[DT_REFERENCIA],103),2) IN ('08','09','10','11','12','13','14') THEN 'S2'
							WHEN RIGHT(CONVERT(DATE,a.[DT_REFERENCIA],103),2) IN ('15','16','17','18','19','20','21') THEN 'S3'
							WHEN RIGHT(CONVERT(DATE,a.[DT_REFERENCIA],103),2) IN ('22','23','24','25','26','27','28') THEN 'S4'
							ELSE 'S5' 
							END AS SEMANA
						,sum(CASE WHEN DS_INDICADOR = 'VL' THEN CAST([QTD] AS FLOAT) ELSE 0 END) as QTD_VL
						,sum(CASE WHEN DS_INDICADOR = 'VLL' THEN CAST([QTD] AS FLOAT) ELSE 0 END) as QTD_VLL
						,(sum(CASE WHEN DS_INDICADOR = 'VLL' THEN CAST([QTD] AS FLOAT) ELSE 0 END)) / (sum(CASE WHEN DS_INDICADOR = 'VL' THEN CAST([QTD] AS FLOAT) ELSE 0 END)) -1 as pct
					FROM [BDintelicanais].[dbo].[TBL_CDO_FISICOS_REAL] as A
						left join [dbo].[TBL_CDO_DE_PARA_CANAL] as B on A.DS_CANAL_BOV = b.[DS_DESCRICAO_CANAL_BOV]
						LEFT JOIN [dbo].[TBL_CDO_DE_PARA_REGIONAL] AS c ON A.NO_CURTO_TERRITORIO = C.NO_CURTO_TERRITORIO
					where [DS_DET_INDICADOR] in ('NOVOS CLIENTES','MIG AQUISICAO')
						and [dt_anomes] in ( '202308' )
						and DS_INDICADOR IN ('VL','VLL')
					group by  
						--a.[dt_anomes]
						[DS_PRODUTO]
						,[DS_UNIDADE_NEGOCIO]
						,CASE when b.DS_GESTAO = 'GESTAO NACIONAL' and DS_CANAL_FINAL in ('TLV RECEPTIVO','TLV ATIVO','TLV PP') then 'TLV'
							when b.DS_GESTAO = 'GESTAO NACIONAL' and DS_CANAL_FINAL in ('WEB') then 'WEB'
							when b.DS_GESTAO = 'GESTAO REGIONAL' then c.COD_REGIONAL
							else b.DS_GESTAO
							END 
						,CASE WHEN RIGHT(CONVERT(DATE,a.[DT_REFERENCIA],103),2) IN ('01','02','03','04','05','06','07') THEN 'S1'
							WHEN RIGHT(CONVERT(DATE,a.[DT_REFERENCIA],103),2) IN ('08','09','10','11','12','13','14') THEN 'S2'
							WHEN RIGHT(CONVERT(DATE,a.[DT_REFERENCIA],103),2) IN ('15','16','17','18','19','20','21') THEN 'S3'
							WHEN RIGHT(CONVERT(DATE,a.[DT_REFERENCIA],103),2) IN ('22','23','24','25','26','27','28') THEN 'S4'
							ELSE 'S5' 
							END
					order by 1,2,3,4 
				"""

    try:
        conexao = criar_conexao()
        df = pd.read_sql(comando_sql, conexao)
        df.to_csv(
            caminho_arquivo_csv, sep=';', header=True, index=False, mode='w'
        )

        # deletar a tabela de deflação antes de gravar os novos dados
        conexao.execute('delete from dbo.TBL_CDO_APOIO_DEFLAC_REF_TEND')
        conexao.commit()

        # insere no banco os dados de deflação
        for index, linha in df.iterrows():
            conexao.execute(
                'Insert into dbo.TBL_CDO_APOIO_DEFLAC_REF_TEND (DS_PRODUTO, DS_UNIDADE_NEGOCIO, GESTAO, SEMANA, QTD_VL, QTD_VLL, pct) values(?,?,?,?,?,?,?)',
                linha.DS_PRODUTO,
                linha.DS_UNIDADE_NEGOCIO,
                linha.GESTAO,
                linha.SEMANA,
                linha.QTD_VL,
                linha.QTD_VLL,
                linha.pct,
            )
        conexao.commit()

    except Exception as e:
        logging.critical(f'Ocorreu um erro na funcao puxa_deflac_ref: {e}')

    finally:
        conexao.close()


def CalculaTendencia(
    df, dias_ate_fim_mes, indicador, PRODUTO, UNIDADE_NEGOCIO, GESTAO
):
    print(
        f'CalculaTendencia - {indicador}-{PRODUTO}-{UNIDADE_NEGOCIO}-{GESTAO}'
    )
    # seasonal_decompose(df_b, model='additve', period=7).plot();
    # localiza o INDICE de uma data especifica para criar a base de TREINO e de TESTE
    # indice = df_b.index.get_loc('2023-08-01')
    # train = df_b[:indice]
    # test = df_b[indice:]

    final_model = ExponentialSmoothing(
        df.qtd, trend='additive', seasonal='add', seasonal_periods=7
    ).fit()
    pred = final_model.forecast(dias_ate_fim_mes)

    dff = pred.to_frame()
    dff = dff.rename(columns={0: 'VALOR'})
    dff['INDICADOR'] = indicador
    dff['PRODUTO'] = PRODUTO
    dff['UNIDADE'] = UNIDADE_NEGOCIO
    dff['GESTAO'] = GESTAO

    dff.to_csv(
        f'C:\\Users\\oi066724\\Documents\\Python\\Tendencia\\TEND_DEFLAC\\tendencia_{AAAAMMDD_referencia}.csv',
        sep=';',
        header=False,
        index=True,
        mode='a',
    )

    # Create a new column with index values
    dff['DATA'] = dff.index
    # Using reset_index() to set index into column
    dff = dff.reset_index()

    dff['DATA_Ajustada'] = dff['DATA'].dt.strftime('%Y-%m-%d')
    # print(dff)

    conexao = criar_conexao()
    # insere no banco os dados de deflação
    for index, linha in dff.iterrows():
        conexao.execute(
            'Insert into dbo.TBL_CDO_APOIO_TENDENCIA (DATA, qtd, DS_INDICADOR, DS_PRODUTO, DS_UNIDADE_NEGOCIO, GESTAO) values(?,?,?,?,?,?)',
            linha.DATA_Ajustada,
            linha.VALOR,
            linha.INDICADOR,
            linha.PRODUTO,
            linha.UNIDADE,
            linha.GESTAO,
        )
    conexao.commit()


def excluir_tabela_tendencia(conexao):
    conexao.execute('delete from dbo.TBL_CDO_APOIO_TENDENCIA')
    conexao.commit()
    logging.debug('Excluindo tendencia da tabela TBL_CDO_APOIO_TENDENCIA')


def inserir_dados_tendencia(conexao):
    comando_sql = f"""
		INSERT into dbo.TBL_CDO_APOIO_TENDENCIA
		SELECT CONVERT(DATE,a.[DT_REFERENCIA],103) AS DATA
			,sum(CAST([QTD] AS FLOAT)) as qtd
			,a.[DS_INDICADOR]
			,a.[DS_PRODUTO]
			,a.[DS_UNIDADE_NEGOCIO]
			,CASE when b.DS_GESTAO = 'GESTAO NACIONAL' and DS_CANAL_FINAL in ('TLV RECEPTIVO','TLV ATIVO','TLV PP') then 'TLV'
				  when b.DS_GESTAO = 'GESTAO NACIONAL' and DS_CANAL_FINAL in ('WEB') then 'WEB'
				  when b.DS_GESTAO = 'GESTAO REGIONAL' then c.COD_REGIONAL
				  else b.DS_GESTAO
				  END  AS GESTAO
		FROM [BDintelicanais].[dbo].[TBL_CDO_FISICOS_REAL] as A
			left join [dbo].[TBL_CDO_DE_PARA_CANAL] as B on A.DS_CANAL_BOV = b.[DS_DESCRICAO_CANal_BOV]
			LEFT JOIN [dbo].[TBL_CDO_DE_PARA_REGIONAL] AS c ON A.NO_CURTO_TERRITORIO = C.NO_CURTO_TERRITORIO
		where [DS_DET_INDICADOR] in ('NOVOS CLIENTES','MIG AQUISICAO')
			and [dt_anomes] = '{AAAAMM}'
			and DS_INDICADOR = 'VL'
		group by [DS_PRODUTO]
			,[DS_INDICADOR]
			,CONVERT(DATE,[DT_REFERENCIA],103)
			,[DS_UNIDADE_NEGOCIO]
			,CASE when b.DS_GESTAO = 'GESTAO NACIONAL' and DS_CANAL_FINAL in ('TLV RECEPTIVO','TLV ATIVO','TLV PP') then 'TLV'
				  when b.DS_GESTAO = 'GESTAO NACIONAL' and DS_CANAL_FINAL in ('WEB') then 'WEB'
				  when b.DS_GESTAO = 'GESTAO REGIONAL' then c.COD_REGIONAL
				  else b.DS_GESTAO
				  END
	"""
    try:
        conexao.execute(comando_sql)
        conexao.commit()
        logging.info(f'Insert na tabela TBL_CDO_APOIO_TENDENCIA realizado.')
    except Exception as e:
        logging.error(
            'Erro ao inserir dados em TBL_CDO_APOIO_TENDENCIA - funcao: inserir_dados_tendencia'
        )


def exportar_dados_tendencia_para_csv(conexao):
    try:
        comando_sql = (
            """select * from dbo.TBL_CDO_APOIO_TENDENCIA order by DATA"""
        )
        df = pd.read_sql(comando_sql, conexao, parse_dates=['DATA'])

        # Verifica se o diretório 'temp' existe e cria, se necessário.
        diretorio_temp = 'temp'
        if not os.path.exists(diretorio_temp):
            os.makedirs(diretorio_temp)

        caminho_arquivo_csv = os.path.join(
            diretorio_temp, f'tendencia_{AAAAMMDD_referencia}.csv'
        )
        df.to_csv(
            caminho_arquivo_csv, sep=';', header=True, index=False, mode='w'
        )

        logging.info(
            f'Arquivo de tendência CSV criado em {caminho_arquivo_csv}'
        )
    except Exception as e:
        logging.error(
            f'Erro ao exportar dados de tendência para CSV: {str(e)}'
        )


def puxa_dados_real():
    try:
        conexao = criar_conexao()
        excluir_tabela_tendencia(conexao)
        inserir_dados_tendencia(conexao)
        exportar_dados_tendencia_para_csv(conexao)
    except Exception as e:
        logging.error(f'Ocorreu um erro no puxa_dados_real: {e}')
    finally:
        conexao.close()


def puxa_dados_para_simular():

    data_inicio = '2023-06-01'
    comando_sql = f"""
					select 
						CONVERT(DATE,[DATA],103) AS DATA
						,sum(QTD) as qtd
						,DS_INDICADOR
						,DS_PRODUTO
						,DS_UNIDADE_NEGOCIO
						,GESTAO
					from [BDintelicanais].[dbo].[TBL_CDO_FISICOS_REAL_PROFORMA_PARA_TEND_VL]
					where CONVERT(DATE,[DATA],103) >= '{data_inicio}'
					group by 
						CONVERT(DATE,[DATA],103)
						,DS_INDICADOR
						,DS_PRODUTO
						,DS_UNIDADE_NEGOCIO
						,GESTAO
					order by 1
	"""
    try:
        conexao = criar_conexao()
        df = pd.read_sql(comando_sql, conexao, parse_dates=['DATA'])
        df['qtd'] = df['qtd'].astype(float)
        logging.info('Funcao puxa_dados_para_simular executada')
        return df

    except Exception as e:
        logging.error(f'Ocorreu um erro no puxa_dados_para_simular: {e}')
        return None
    finally:
        conexao.close()


def montaExcelTendVlVll():
    comando_sql = f'''select DS_PRODUTO,
                            DS_INDICADOR,
                            DS_UNIDADE_NEGOCIO,
                            NO_CURTO_TERRITORIO as FILIAL,
                            sum(qtd) as QTD,
                            TS_ATUALIZACAO
                    FROM TBL_CDO_fisicos_tendencia
                    where DT_ANOMES = '{AAAAMM}' and DS_DET_INDICADOR <> 'MIG BASE' and DS_INDICADOR <> 'gross'
                    group by DS_PRODUTO,
                        DS_INDICADOR,
                        DS_UNIDADE_NEGOCIO,
                        NO_CURTO_TERRITORIO,
                        TS_ATUALIZACAO'''

    comando_sql_2 = """select * from TBL_CDO_APOIO_TENDENCIA_VL_VLL"""
    try:
        conexao = criar_conexao()
        cursor = conexao.cursor()
        df = pd.read_sql(comando_sql, conexao)
        df2 = pd.read_sql(comando_sql_2, conexao)

        pt_tabdin = df.pivot_table(
            values='QTD',
            index=['FILIAL'],
            columns=['DS_INDICADOR', 'DS_PRODUTO'],
            aggfunc='sum',
            fill_value=0,
            margins=True,
            margins_name='TOTAL',
        )

        pt_tabdin2 = df2.pivot_table(
            values='QTD_FINAL',
            index=['DS_INDICADOR', 'DS_PRODUTO', 'GESTAO'],
            columns=['DATA'],
            aggfunc='sum',
            fill_value=0,
            margins=True,
            margins_name='TOTAL',
        )
        
        dir_insumo_tend = config['DEFAULT']['dir_rede_insumo_tend']
        dest_filename = f'Tend_VL_VLL_Fibra_NovaFibra_{AAAAMMDD}.xlsx'
        full_dest_path = os.path.join(dir_insumo_tend, dest_filename)
        
        if os.path.exists(full_dest_path):
            # Se o arquivo já existe, determine o próximo número sequencial
            base, ext = os.path.splitext(full_dest_path)
            version = 1
            while os.path.exists(f"{base}-v{version}{ext}"):
                version += 1
            new_dest_path = f"{base}-v{version}{ext}"
            os.rename(full_dest_path, new_dest_path)
        
        with pd.ExcelWriter(full_dest_path) as writer:
            df.to_excel(
                writer, sheet_name='DADOS', startcol=0, startrow=0, index=0
            )
            pt_tabdin.to_excel(
                writer, sheet_name='TEND', startcol=0, startrow=0, index=1
            )
            df2.to_excel(
                writer,
                sheet_name='DADOS_DIARIO',
                startcol=0,
                startrow=0,
                index=0,
            )
            pt_tabdin2.to_excel(
                writer,
                sheet_name='TEND_DIARIA',
                startcol=0,
                startrow=0,
                index=1,
            )

        logging.info('Arquivo de Tend VL e VLL criado na pasta de rede')

    except Exception as e:
        logging.error(f'Ocorreu um erro no montaExcelTendVlVll: {e}')
    finally:
        conexao.close()


def filtra_df(
    base, indicador, PRODUTO=None, UNIDADE_NEGOCIO=None, GESTAO=None
):

    df_filtrada = base.query(f'DS_INDICADOR == "{indicador}"')

    if PRODUTO != None:
        df_filtrada = df_filtrada.query(f'DS_PRODUTO == "{PRODUTO}"')

    if UNIDADE_NEGOCIO != None:
        df_filtrada = df_filtrada.query(
            f'DS_UNIDADE_NEGOCIO == "{UNIDADE_NEGOCIO}"'
        )

    if GESTAO != None:
        df_filtrada = df_filtrada.query(f'GESTAO == "{GESTAO}"')

    # base apenas com DATA e valor
    df_filtrada = df_filtrada[['DATA', 'qtd']]

    # Soma por DATA
    df_a = df_filtrada.groupby('DATA').sum()

    # diario 'D' > mensal 'MS'
    df_b = df_a.resample(rule='D').sum()
    return df_b


def filtraDF_e_CalculaTendencia(
    base, indicador, PRODUTO, UNIDADE_NEGOCIO, GESTAO
):
    df_b = filtra_df(base, indicador, PRODUTO, UNIDADE_NEGOCIO, GESTAO)

    dias_ate_fim_mes = dias_faltando
    CalculaTendencia(
        df_b, dias_ate_fim_mes, indicador, PRODUTO, UNIDADE_NEGOCIO, GESTAO
    )
