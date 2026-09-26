# src/ingestion/read_data.py

import pandas as pd


def ler_vendas_lojas(caminho: str = "data/raw/vendas_lojas.csv") -> pd.DataFrame:
    """Lê o arquivo CSV de vendas das lojas físicas."""
    df = pd.read_csv(caminho)
    return df


def ler_vendas_ecommerce(caminho: str = "data/raw/vendas_ecommerce.json") -> pd.DataFrame:
    """Lê o arquivo JSON de vendas do e-commerce."""
    df = pd.read_json(caminho)
    return df


if __name__ == "__main__":
    df_lojas = ler_vendas_lojas()
    df_ecommerce = ler_vendas_ecommerce()

    print("=== VENDAS LOJAS (CSV) ===")
    print(df_lojas.head())
    print(df_lojas.info())

    print("\n=== VENDAS ECOMMERCE (JSON) ===")
    print(df_ecommerce.head())
    print(df_ecommerce.info())

    def limpar_preco(valor):
        """Converte um preço em texto (ex: 'R$ 699,90', '349,90', '4599.90')
        para um número float, tratando os formatos inconsistentes do CSV."""

        # Se já for um número (não veio como texto), não precisa fazer nada
        if isinstance(valor, (int, float)):
            return valor

        # Se for nulo/vazio, mantém como nulo
        if pd.isna(valor):
            return valor

        texto = str(valor)
        texto = texto.replace("R$", "")  # remove o símbolo de moeda
        texto = texto.strip()  # remove espaços nas pontas
        texto = texto.replace(",", ".")  # troca vírgula decimal por ponto

        return float(texto)
