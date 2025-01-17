import re
import pandas as pd
from PyPDF2 import PdfReader

nome_arquivo_ficha = 'ficha-financeira.pdf'
reader = PdfReader(nome_arquivo_ficha)
paginas = reader.pages

def extrair_nome_pessoa_ficha(texto: str) -> str | None:
    nome_regex = r'Nome:\s([A-Z\s]+)\s'
    nome = re.search(nome_regex, texto)
    if nome is None: return None
    return nome.groups()[0]


def extrair_cpf_da_ficha(texto: str) -> str | None:
    cpf_regex = r'CPF:\s([\d]{3}\.[\d]{3}\.[\d]{3}-[\d]{2})'
    cpf = re.search(cpf_regex, texto)
    if cpf is None: return None
    return cpf.groups()[0]


def extrair_cpf_do_nome_arquivo_ficha(nome_arquivo_ficha: str) -> str | None:
    cpf_regex = r'Ficha_Financeira_([\d]{11})'
    cpf = re.search(cpf_regex, nome_arquivo_ficha)
    if cpf is None: return None
    return cpf.groups()[0]


def remover_pontos_do_cpf(cpf: str) -> str:
    return cpf.replace('.', '').replace('-', '')


dados = []
for pagina in paginas:
    texto_pagina = pagina.extract_text()
    resultados = re.findall(r'Referência:\s([01][\d]\/[\d]{4})|(\d{3})\s([A-Z-/.\s()+0-9]+)\s(\d+,\d+)', texto_pagina)
    dados.append(resultados)

lista_dados = []
for itens_pagina in dados:
    for item in itens_pagina:
        lista_dados.append(item)

linhas = []
referencia_atual = None
for registro in lista_dados:
    if registro[0]:
        referencia_atual = registro[0]
        continue
    linhas.append((referencia_atual, *registro[1:]))

colunas = ['referencia', 'codigo', 'nome', 'valor']
df_ficha = pd.DataFrame(linhas, columns=colunas)

# converte coluna 'valor' para numeros
df_ficha['valor'] = df_ficha['valor'].str.replace('.', '')
df_ficha['valor'] = pd.to_numeric(df_ficha['valor'].str.replace(',', '.'))

codigos_vantagens = ('109', '113', '115', '127', '131', '182', '203', '119')
soma_por_mes = df_ficha[df_ficha['codigo'].isin(codigos_vantagens)].groupby(['referencia'], sort=False, as_index=False).sum()[['referencia', 'valor']]

texto_ficha_primeira_pagina = paginas[0].extract_text()
nome_arquivo = ''
cpf_pessoa = extrair_cpf_do_nome_arquivo_ficha(nome_arquivo_ficha)
if cpf_pessoa is not None:
    nome_arquivo = cpf_pessoa + '.csv'
else:
    cpf_pessoa = extrair_cpf_da_ficha(texto_ficha_primeira_pagina)
    cpf_sem_pontos = remover_pontos_do_cpf(cpf_pessoa)
    nome_arquivo = cpf_sem_pontos + '.csv'

nome_pessoa = extrair_nome_pessoa_ficha(texto_ficha_primeira_pagina)
soma_por_mes.columns = pd.MultiIndex.from_tuples(zip([nome_pessoa, ''], soma_por_mes.columns))

soma_por_mes.to_csv(nome_arquivo, sep=';', index=False)