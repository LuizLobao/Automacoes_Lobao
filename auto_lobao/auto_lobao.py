import logging

from funcoes import *

FORMAT = '%(asctime)s | %(levelname)s | %(filename)s | %(message)s'
logging.basicConfig(level=logging.INFO, filename="logs/auto_lobao.log", format=FORMAT)


def main():
    logging.info('Inicio da Execucao')
    # Seu código principal começa aqui
   
    caminho = fr'C:\\JETL\\BASE\\'
    #arquivo = f'{caminho}BOV_1059_202310.TXT'
    #duplicados = verifica_duplicidade_bov(arquivo,'NUMERO_PEDIDO')

    #arquivo = f'{caminho}BOV_1065_202310.TXT'
    #verifica_duplicidade_bov(arquivo,'NUMERO_PEDIDO')
#
    #arquivo = f'{caminho}BOV_6163_202310.TXT'
    #verifica_duplicidade_bov(arquivo,'cd_item_ordem')
#
    arquivo = f'{caminho}BOV_6162_202310.TXT'
    duplicados = verifica_duplicidade_bov(arquivo,'cd_item_ordem')
    print(duplicados)




# Verifique se o script está sendo executado diretamente (não importado)
if __name__ == "__main__":
    main()