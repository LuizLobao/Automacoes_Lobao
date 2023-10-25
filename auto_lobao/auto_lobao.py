import logging
import os
import warnings

from funcoes import *
import segredos
from menu import *
from modelo_tendencia import *

warnings.filterwarnings('ignore', message="pandas only supports SQLAlchemy connectable .*")

user_id = os.getlogin()
FORMAT = f'%(asctime)s | %(levelname)s | %(filename)s | User: {user_id} | %(message)s'
logging.basicConfig(level=logging.INFO, filename="logs/auto_lobao.log", format=FORMAT)


data_referencia = (datetime.today()- timedelta(days=1))
AAAAMMDD_referencia = (datetime.today()- timedelta(days=0)).strftime('%Y%m%d') 
AAAAMM = (datetime.today()).strftime('%Y%m')
ultimo_dia_do_mes = (data_referencia.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
dias_faltando = (ultimo_dia_do_mes - data_referencia).days
hoje = (datetime.today()- timedelta(days=0)).strftime('%d/%m/%Y') 


def roda_modelo_tendencia():
	puxa_deflac_ref()
	df_real = puxa_dados_real()
	executa_procedure_sql('SP_CDO_PREPARA_BASE_TEND_VL')

	df = puxa_dados_para_simular()
	produtos = ['FIBRA', 'NOVA FIBRA']
	segmentos = ['VAREJO', 'EMPRESARIAL']
	gestao = ['RSE', 'RCS', 'RNN', 'TLV', 'WEB', 'OUTROS NACIONAIS']

	for produto in produtos:
		for segmento in segmentos:
			for gest in gestao:
				filtraDF_e_CalculaTendencia(df, 'VL', produto, segmento, gest)

	executa_procedure_sql('SP_CDO_PREPARA_BASE_TEND_VL_VLL')
	montaExcelTendVlVll()
	executa_procedure_sql('SP_CDO_TEND_VL_VLL_LEGADA_IGUAL_CDO')

def roda_verifica_duplicidade_bov():
	caminho = 'C:\\JETL\\BASE\\old\\'
	arquivos_colunas = [
		('BOV_1059_20231025.TXT.zip','BOV_1059.TXT', 'NUMERO_PEDIDO'),
		('BOV_1065_20231025.TXT.zip','BOV_1065.TXT', 'NUMERO_PEDIDO'),
		('BOV_6163_20231025.TXT.zip','BOV_6163.TXT', 'cd_item_ordem'),
		('BOV_6162_20231025.TXT.zip', 'BOV_6162.TXT', 'cd_item_ordem')
	]
	
	for arquivo_zip, arquivo, coluna in arquivos_colunas:
		verifica_duplicidade_bov(f'{caminho}{arquivo_zip}', arquivo, coluna)

def enviar_email_tend_vl_vll_para_operacoes ():
	
	para = segredos.lista_email_vll_nf_to
	cc = segredos.lista_email_vll_nf_cc
	assunto = f"Projeção VL e VLL - FIBRA e NOVA FIBRA - {hoje}"
	anexo = (f'S:\\Resultados\\01_Relatorio Diario\\1 - Base Eventos\\02 - TENDÊNCIA\\Insumos_Tendência\\Tend_VL_VLL_Fibra_NovaFibra_{AAAAMMDD}.xlsx')
	corpo = f"""
    <p>Caros,</p>

    <p>Segue o arquivo atualizado com a projeção de VL e de VLL para Fibra Legado e Nova Fibra calculada hoje: {hoje}</p>
    <p></p>
    <p></p>

    <p>Att,</p>
    <p>Lobão, Luiz</p>
    """
	enviaEmailComAnexo(para, assunto, corpo, cc, anexo)

def libera_tendencias_processo_legado ():
	comando_sql = 'update TB_VALIDA_CARGA_TENDENCIA set DATA_CARGA = convert(varchar, getdate(), 120 )'
	executar_sql(comando_sql)

def tendencias_para_tabela_historico ():
	nome_procedure = 'dbo.SP_CDO_0003_TENDENCIA_PARA_HISTORICO'
	param = AAAAMM
	executa_procedure_sql(nome_procedure, param=None)

def enviar_lista_pdv_outros ():
	comando_sql = 'select * from [VW_COD_SAP_OUTROS] order by qtd desc'

	conexao = criar_conexao()
	cursor = conexao.cursor()
	df=pd.read_sql(comando_sql, conexao)
	os.makedirs('temp', exist_ok=True)
	df.to_csv('temp/pdv_outros.csv', sep=';', decimal=',') 

	anexo = r'C:\Users\oi066724\Documents\Python\Automacoes_Lobao\auto_lobao\temp\pdv_outros.csv'

	corpo = """
		<div>
			Caros, Segue a lista de PDVs que estão aparecendo como OUTROS na BOV.
			Favor verificar e atualizar a classificação dos mesmos.
		</div>
		<br>
		<br>
	"""
	para = segredos.lista_email_pdv_outros
	assunto = f'PDVs Outros: {hoje}!'

	enviaEmailComAnexo(para, assunto, corpo, cc=None, File = anexo)

def main():
	logging.info('Inicio da Execucao')
	# Seu código principal começa aqui

	opcaoSelecionada = 0
	while opcaoSelecionada != 13:
		opcaoSelecionada = menu()
		if opcaoSelecionada == '1':
			print('opção 1 selecionada...(Verificando duplicidades na BOV - consultar log)')
			roda_verifica_duplicidade_bov()
			a = input('Tecle qualquer tecla para continuar...')
	
		elif opcaoSelecionada == '2':
			print('opção 2 selecionada...(Calcular tendência HoltWinters)')
			roda_modelo_tendencia()
			a = input('Tecle qualquer tecla para continuar...')
	
		elif opcaoSelecionada == '3':
			print('opção 3 selecionada...(Enviar tendência para Operações)')
			enviar_email_tend_vl_vll_para_operacoes()
			a = input('Tecle qualquer tecla para continuar...')
	
		elif opcaoSelecionada == '4':
			print('opção 4 selecionada...')
			a = input('Tecle qualquer tecla para continuar...')
	
		elif opcaoSelecionada == '5':
			print('opção 5 selecionada...(Enviar tendências para tabela de histórico)')
			tendencias_para_tabela_historico ()
			a = input('Tecle qualquer tecla para continuar...')
	
		elif opcaoSelecionada == '6':
			print('opção 6 selecionada...(Libera tendências processo legado)')
			libera_tendencias_processo_legado ()
			a = input('Tecle qualquer tecla para continuar...')
	
		elif opcaoSelecionada == '7':
			print('opção 7 selecionada...')
			a = input('Tecle qualquer tecla para continuar...')
	
		elif opcaoSelecionada == '8':
			print('opção 8 selecionada...')
			a = input('Tecle qualquer tecla para continuar...')
	
		elif opcaoSelecionada == '9':
			print('opção 9 selecionada...')
			a = input('Tecle qualquer tecla para continuar...')
	
		elif opcaoSelecionada == '10':
			print('opção 10 selecionada...')
			a = input('Tecle qualquer tecla para continuar...')
	
		elif opcaoSelecionada == '11':
			print('opção 11 selecionada...')
			a = input('Tecle qualquer tecla para continuar...')
	
		elif opcaoSelecionada == '12':
			print('opção 13 selecionada...(Envia Lista de PDV Outros)')
			enviar_lista_pdv_outros ()
			a = input('Tecle qualquer tecla para continuar...')
	
		elif opcaoSelecionada == '13':
			print('Opção 13...SAIR')
			break
		
		else:
			print('Opção Inválida')


# Verifique se o script está sendo executado diretamente (não importado)
if __name__ == "__main__":
	main()