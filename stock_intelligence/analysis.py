"""Filtros, ordenação e agregações usadas no dashboard (sem Streamlit)."""
import pandas as pd

from stock_intelligence import config

# Texto mostrado ao usuário -> coluna real do DataFrame
OPCOES_ORDENACAO = {
    "Impacto financeiro": "impacto_financeiro",
    "Quantidade divergente": "quantidade_divergente",
    "Código do material": "codigo_material",
}


def filtrar(df: pd.DataFrame, depositos=None, tipos=None, busca: str = "") -> pd.DataFrame:
    """Aplica os filtros do painel.

    - depositos / tipos: listas de valores aceitos. None = não filtra.
      Lista vazia = nada selecionado = resultado vazio.
    - busca: texto procurado no código OU na descrição (sem diferenciar maiúsculas).
    """
    resultado = df
    if depositos is not None:
        resultado = resultado[resultado["deposito"].isin(depositos)]
    if tipos is not None:
        resultado = resultado[resultado["tipo_divergencia"].isin(tipos)]

    busca = busca.strip()
    if busca:
        # regex=False: o texto digitado é tratado como texto comum, então
        # caracteres como "(" ou "*" não quebram a busca
        no_codigo = resultado["codigo_material"].str.contains(busca, case=False, regex=False)
        na_descricao = resultado["descricao"].str.contains(busca, case=False, regex=False)
        resultado = resultado[no_codigo | na_descricao]
    return resultado


def ordenar(df: pd.DataFrame, coluna: str, crescente: bool = False) -> pd.DataFrame:
    """Ordena por `coluna`. Empates são desfeitos por código e depósito,
    para que o resultado seja sempre o mesmo (reproduzível)."""
    desempate = [c for c in ["codigo_material", "deposito"] if c != coluna]
    return df.sort_values(
        [coluna] + desempate,
        ascending=[crescente] + [True] * len(desempate),
    )


def ranking_materiais(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """Os n registros com maior impacto financeiro (só os que têm divergência)."""
    divergentes = df[df["quantidade_divergente"] > 0]
    ordenado = divergentes.sort_values(
        ["impacto_financeiro", "codigo_material", "deposito"],
        ascending=[False, True, True],
    )
    colunas = ["codigo_material", "descricao", "deposito", "tipo_divergencia",
               "quantidade_divergente", "impacto_financeiro"]
    return ordenado.head(n)[colunas].reset_index(drop=True)


def ranking_depositos(df: pd.DataFrame) -> pd.DataFrame:
    """Depósitos ordenados pelo impacto financeiro estimado."""
    base = df.assign(divergente=df["quantidade_divergente"] > 0)
    agrupado = base.groupby("deposito").agg(
        itens_analisados=("divergente", "size"),
        itens_divergentes=("divergente", "sum"),
        impacto_financeiro=("impacto_financeiro", "sum"),
    ).reset_index()
    return agrupado.sort_values(
        ["impacto_financeiro", "deposito"], ascending=[False, True]
    ).reset_index(drop=True)


def divergencias_por_deposito(df: pd.DataFrame) -> pd.DataFrame:
    """Quantos itens com falta e com sobra existem em cada depósito."""
    colunas = ["deposito", config.TIPO_FALTA, config.TIPO_SOBRA]
    divergentes = df[df["tipo_divergencia"] != config.TIPO_SEM_DIVERGENCIA]
    if divergentes.empty:
        return pd.DataFrame(columns=colunas)

    tabela = divergentes.groupby(["deposito", "tipo_divergencia"]).size().unstack(fill_value=0)
    for tipo in (config.TIPO_FALTA, config.TIPO_SOBRA):
        if tipo not in tabela.columns:  # ex.: só existem faltas, nenhuma sobra
            tabela[tipo] = 0
    tabela.columns.name = None
    return tabela[[config.TIPO_FALTA, config.TIPO_SOBRA]].reset_index()