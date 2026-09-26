import pandas as pd
from src.ingestion.read_data import ler_vendas_lojas, ler_vendas_ecommerce


def limpar_preco(valor):
    """Converte um preço em texto (ex: 'R$ 699,90', '349,90', '4599.90')
    para um número float, tratando os formatos inconsistentes do CSV."""
    if isinstance(valor, (int, float)):
        return valor
    if pd.isna(valor):
        return valor
    texto = str(valor)
    texto = texto.replace("R$", "")
    texto = texto.strip()
    texto = texto.replace(",", ".")
    return float(texto)


df_lojas = ler_vendas_lojas()
df_lojas["preco_unitario"] = df_lojas["preco_unitario"].apply(limpar_preco)

# --- tratamento de duplicatas de id_venda ---
mascara_duplicados = df_lojas.duplicated(subset="id_venda", keep=False)
df_lojas_revisao = df_lojas[mascara_duplicados]
df_lojas = df_lojas[~mascara_duplicados]
# ---------------------------------------------

# --- tratamento de vendas com id diferente mas dados idênticos ---
colunas_para_comparar = ["data_venda", "produto", "categoria", "quantidade", "preco_unitario", "cidade", "loja_id"]
mascara_mesma_venda = df_lojas.duplicated(subset=colunas_para_comparar, keep=False)
df_lojas_revisao_similares = df_lojas[mascara_mesma_venda]
df_lojas = df_lojas[~mascara_mesma_venda]
# ------------------------------------------------------------------------

df_lojas["cidade"] = df_lojas["cidade"].fillna("Não informado")

print("\nValores nulos por coluna, após tratar cidade:")
print(df_lojas.isnull().sum())

print("Linhas para revisão (possível mesma venda, IDs diferentes):")
print(df_lojas_revisao_similares)
print("\nTotal de linhas após separar possíveis vendas duplicadas:", len(df_lojas))

mascara_preco_nulo = df_lojas["preco_unitario"].isna()
df_lojas_revisao_preco = df_lojas[mascara_preco_nulo]
df_lojas = df_lojas[~mascara_preco_nulo]

print("\nLinha removida por preço nulo:")
print(df_lojas_revisao_preco)
print("\nTotal de linhas após remover preço nulo:", len(df_lojas))

df_ecommerce = ler_vendas_ecommerce()

print("=== VENDAS LOJAS (CSV) ===")
print(df_lojas.head())
print(df_lojas.info())

print("Linhas para revisão (mesmo id_venda, quantidade diferente):")
print(df_lojas_revisao)
print("\nTotal de linhas após separar duplicatas de id_venda:", len(df_lojas))

print("\n=== VENDAS ECOMMERCE (JSON) ===")
print(df_ecommerce.head())
print(df_ecommerce.info())