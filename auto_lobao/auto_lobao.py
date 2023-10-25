import logging
import os

from funcoes import *
from menu import *

warnings.filterwarnings('ignore', message="pandas only supports SQLAlchemy connectable .*")

user_id = os.getlogin()
FORMAT = f'%(asctime)s | %(levelname)s | %(filename)s | User: {user_id} | %(message)s'
logging.basicConfig(level=logging.INFO, filename="logs/auto_lobao.log", format=FORMAT)



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
			print('opção 2 selecionada...')
			a = input('Tecle qualquer tecla para continuar...')
	
		elif opcaoSelecionada == '3':
			print('opção 3 selecionada...')
			a = input('Tecle qualquer tecla para continuar...')
	
		elif opcaoSelecionada == '4':
			print('opção 4 selecionada...')
			a = input('Tecle qualquer tecla para continuar...')
	
		elif opcaoSelecionada == '5':
			print('opção 5 selecionada...')
			a = input('Tecle qualquer tecla para continuar...')
	
		elif opcaoSelecionada == '6':
			print('opção 6 selecionada...')
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
			print('opção 13 selecionada...')
			a = input('Tecle qualquer tecla para continuar...')
	
		elif opcaoSelecionada == '13':
			print('Opção 13...SAIR')
			break
		
		else:
			print('Opção Inválida')


# Verifique se o script está sendo executado diretamente (não importado)
if __name__ == "__main__":
	main()