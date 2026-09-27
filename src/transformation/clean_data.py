import re
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


def padronizar_data(texto):
    """Reescreve qualquer formato de data conhecido para o padrão YYYY-MM-DD,
    sem ambiguidade, antes de converter para datetime de verdade."""
    texto = str(texto).strip()

    # Ano primeiro (YYYY-MM-DD ou YYYY/MM/DD) — sem ambiguidade
    m = re.match(r"^(\d{4})[-/](\d{2})[-/](\d{2})$", texto)
    if m:
        ano, mes, dia = m.groups()
        return f"{ano}-{mes}-{dia}"

    # Dia primeiro (DD/MM/YYYY) — padrão brasileiro confirmado
    m = re.match(r"^(\d{2})/(\d{2})/(\d{4})$", texto)
    if m:
        dia, mes, ano = m.groups()
        return f"{ano}-{mes}-{dia}"

    return texto  # formato não reconhecido — mantém como está para investigar depois


# ============================================================
# LIMPEZA: VENDAS DAS LOJAS FÍSICAS (CSV)
# ============================================================

df_lojas = ler_vendas_lojas()

# Preço vinha como texto bagunçado ("R$ 699,90", "349,90") -> converte para float
df_lojas["preco_unitario"] = df_lojas["preco_unitario"].apply(limpar_preco)

# Duplicata de id_venda com dados conflitantes (ex.: mesma venda com quantidade
# diferente em cada linha) -> não dá pra saber qual é a correta, vai para revisão
mascara_duplicados = df_lojas.duplicated(subset="id_venda", keep=False)
df_lojas_revisao = df_lojas[mascara_duplicados]
df_lojas = df_lojas[~mascara_duplicados]

# Mesma venda registrada com IDs diferentes (todas as outras colunas idênticas)
# -> ambiguidade de identidade do evento, também vai para revisão
colunas_para_comparar = ["data_venda", "produto", "categoria", "quantidade", "preco_unitario", "cidade", "loja_id"]
mascara_mesma_venda = df_lojas.duplicated(subset=colunas_para_comparar, keep=False)
df_lojas_revisao_similares = df_lojas[mascara_mesma_venda]
df_lojas = df_lojas[~mascara_mesma_venda]

# cidade nula -> não afeta faturamento/ticket médio, só "vendas por região",
# então mantemos a linha com um marcador explícito em vez de descartar
df_lojas["cidade"] = df_lojas["cidade"].fillna("Não informado")

# preço nulo -> não dá pra calcular faturamento sem preço, vai para revisão
mascara_preco_nulo = df_lojas["preco_unitario"].isna()
df_lojas_revisao_preco = df_lojas[mascara_preco_nulo]
df_lojas = df_lojas[~mascara_preco_nulo]

# quantidade <= 0 ou preço negativo -> registros inválidos, sem interpretação
# de negócio clara (não temos coluna de "devolução"), vão para revisão
mascara_invalidos = (df_lojas["quantidade"] <= 0) | (df_lojas["preco_unitario"] < 0)
df_lojas_revisao_invalidos = df_lojas[mascara_invalidos]
df_lojas = df_lojas[~mascara_invalidos]

# categoria nula -> recuperável: outros registros do mesmo produto já têm
# a categoria preenchida, então usamos isso como referência em vez de descartar
mapa_categoria = df_lojas.dropna(subset=["categoria"]).groupby("produto")["categoria"].first()
df_lojas["categoria"] = df_lojas["categoria"].fillna(df_lojas["produto"].map(mapa_categoria))

# Padronização de texto: remove espaços extras e corrige capitalização
df_lojas["cidade"] = df_lojas["cidade"].str.strip().str.title()
df_lojas["categoria"] = df_lojas["categoria"].str.strip().str.title()

# Correção manual de uma inconsistência de acentuação que o .title() não resolve
# ("Eletronicos" sem acento vs "Eletrônicos" com acento são o mesmo valor)
df_lojas["categoria"] = df_lojas["categoria"].replace({"Eletronicos": "Eletrônicos"})

# Datas em formatos mistos (YYYY-MM-DD, YYYY/MM/DD, DD/MM/YYYY) -> padroniza
# manualmente para YYYY-MM-DD antes de converter, evitando um bug conhecido do
# pandas ao combinar format="mixed" com dayfirst=True
df_lojas["data_venda"] = df_lojas["data_venda"].apply(padronizar_data)
df_lojas["data_venda"] = pd.to_datetime(df_lojas["data_venda"], format="%Y-%m-%d")

print("=== VENDAS LOJAS (CSV) — resultado final ===")
print(df_lojas.head())
print(df_lojas.info())
print("\nTotal de linhas válidas:", len(df_lojas))
print("Linhas em revisão (id duplicado, qtd. diferente):", len(df_lojas_revisao))
print("Linhas em revisão (mesma venda, IDs diferentes):", len(df_lojas_revisao_similares))
print("Linhas em revisão (preço nulo):", len(df_lojas_revisao_preco))
print("Linhas em revisão (quantidade/preço inválidos):", len(df_lojas_revisao_invalidos))


# ============================================================
# LIMPEZA: VENDAS DO E-COMMERCE (JSON)
# ============================================================

df_ecommerce = ler_vendas_ecommerce()

# Registro duplicado, idêntico em todas as colunas -> remoção direta, sem ambiguidade
df_ecommerce = df_ecommerce.drop_duplicates()

# e-mail do cliente nulo -> não afeta nenhuma métrica de negócio, mantém a linha
df_ecommerce["cliente_email"] = df_ecommerce["cliente_email"].fillna("Não informado")

# preço nulo -> mesmo critério do CSV, vai para revisão
mascara_preco_nulo = df_ecommerce["preco_unitario"].isna()
df_ecommerce_revisao_preco = df_ecommerce[mascara_preco_nulo]
df_ecommerce = df_ecommerce[~mascara_preco_nulo]

# produto nulo -> sem chave segura para recuperar (preço sozinho não é confiável,
# pode haver mais de um produto com o mesmo preço), vai para revisão
mascara_produto_nulo = df_ecommerce["produto"].isna()
df_ecommerce_revisao_produto = df_ecommerce[mascara_produto_nulo]
df_ecommerce = df_ecommerce[~mascara_produto_nulo]

# Padronização de texto na região (mesmo padrão de cidade/categoria do CSV)
df_ecommerce["regiao"] = df_ecommerce["regiao"].str.strip().str.title()

# status fora do domínio válido (ex.: "desconhecido") -> validação de domínio,
# não é nulo, mas também não é um valor que o negócio reconhece, vai para revisão
status_validos = ["concluida", "cancelada", "pendente"]
mascara_status_invalido = ~df_ecommerce["status"].isin(status_validos)
df_ecommerce_revisao_status = df_ecommerce[mascara_status_invalido]
df_ecommerce = df_ecommerce[~mascara_status_invalido]

# quantidade <= 0 -> mesmo critério do CSV, vai para revisão
mascara_invalidos = (df_ecommerce["quantidade"] <= 0)
df_ecommerce_revisao_invalidos = df_ecommerce[mascara_invalidos]
df_ecommerce = df_ecommerce[~mascara_invalidos]

# Datas com e sem horário misturadas (ex.: "2026-01-05T14:32:00" e "2026-01-06").
# Sem ambiguidade de dia/mês aqui (ano sempre vem primeiro), então format="mixed"
# é seguro. Horário não importa para as métricas, por isso descartamos com .dt.date
df_ecommerce["data"] = pd.to_datetime(df_ecommerce["data"], format="mixed").dt.date

print("\n=== VENDAS ECOMMERCE (JSON) — resultado final ===")
print(df_ecommerce.head())
print(df_ecommerce.info())
print("\nTotal de linhas válidas:", len(df_ecommerce))
print("Linhas em revisão (preço nulo):", len(df_ecommerce_revisao_preco))
print("Linhas em revisão (produto nulo):", len(df_ecommerce_revisao_produto))
print("Linhas em revisão (status inválido):", len(df_ecommerce_revisao_status))
print("Linhas em revisão (quantidade inválida):", len(df_ecommerce_revisao_invalidos))