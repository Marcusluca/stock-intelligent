"""Validação dos dados importados.

Regras:
- ERRO: a linha não pode ser calculada com segurança (fica separada, não é apagada).
- AVISO: a linha é calculada, mas há algo suspeito para o analista conferir.
"""
import math
from dataclasses import dataclass

import pandas as pd

from stock_intelligence import config


@dataclass
class ResultadoValidacao:
    """Pacote com tudo o que a validação encontrou."""

    colunas_ausentes: list
    problemas: pd.DataFrame      # uma linha por problema encontrado
    dados_validos: pd.DataFrame  # linhas prontas para o cálculo (números já convertidos)
    dados_invalidos: pd.DataFrame  # linhas com erro, exatamente como vieram

    @property
    def quantidade_invalidos(self) -> int:
        return len(self.dados_invalidos)


def _converter_numero(valor) -> float:
    """Converte texto em número. Devolve NaN se não for possível.

    Aceita "10", "2.5" e "2,50". Se houver vírgula, assume formato brasileiro
    ("1.234,56": o ponto separa milhares e a vírgula, os decimais).
    """
    if valor is None or pd.isna(valor):
        return float("nan")
    texto = str(valor).strip().replace("R$", "").replace(" ", "")
    if texto == "":
        return float("nan")
    if "," in texto:
        texto = texto.replace(".", "").replace(",", ".")
    try:
        numero = float(texto)
    except ValueError:
        return float("nan")
    return numero if math.isfinite(numero) else float("nan")


def _esta_vazio(serie: pd.Series) -> pd.Series:
    """True onde a célula está em branco ou só tem espaços."""
    return serie.isna() | (serie.astype(str).str.strip() == "")


def _tabela_problemas(lista: list) -> pd.DataFrame:
    tabela = pd.DataFrame(lista, columns=config.COLUNAS_PROBLEMAS)
    return tabela.sort_values(["linha", "coluna"]).reset_index(drop=True)


def validar(df_bruto: pd.DataFrame) -> ResultadoValidacao:
    """Valida o DataFrame lido por `carregar_arquivo`."""
    df = df_bruto.copy()
    df.columns = [str(c).strip().lower() for c in df.columns]
    if "linha_planilha" not in df.columns:
        df["linha_planilha"] = df.index + 2

    # 1) Colunas obrigatórias: sem elas, nada mais pode ser validado
    ausentes = [c for c in config.COLUNAS_OBRIGATORIAS if c not in df.columns]
    if ausentes:
        vazio = df.iloc[0:0]
        return ResultadoValidacao(ausentes, _tabela_problemas([]), vazio, vazio)

    problemas = []
    invalida = pd.Series(False, index=df.index)  # True = linha com algum ERRO

    def registrar(mascara, coluna, mensagem, gravidade):
        """Anota um problema para cada linha onde `mascara` é True."""
        for _, linha in df[mascara].iterrows():
            original = linha[coluna]
            problemas.append({
                "linha": int(linha["linha_planilha"]),
                "coluna": coluna,
                "gravidade": gravidade,
                "problema": mensagem,
                "valor_original": "" if pd.isna(original) else str(original),
            })
        if gravidade == config.GRAVIDADE_ERRO:
            invalida[mascara] = True

    vazio = {c: _esta_vazio(df[c]) for c in config.COLUNAS_OBRIGATORIAS}

    # 2) Colunas numéricas: vazio, texto no lugar de número, negativo
    numeros = {}
    for coluna in config.COLUNAS_NUMERICAS:
        numero = df[coluna].map(_converter_numero)
        numeros[coluna] = numero
        registrar(vazio[coluna], coluna, "Campo vazio.", config.GRAVIDADE_ERRO)
        registrar(
            ~vazio[coluna] & numero.isna(), coluna,
            "Valor não numérico. Use apenas números (ex.: 10 ou 2,50).",
            config.GRAVIDADE_ERRO,
        )
        registrar(numero < 0, coluna, "Valor negativo não é permitido.", config.GRAVIDADE_ERRO)

    # 3) Campos de identificação
    registrar(vazio["codigo_material"], "codigo_material",
              "Código do material vazio.", config.GRAVIDADE_ERRO)
    registrar(vazio["deposito"], "deposito",
              "Depósito vazio.", config.GRAVIDADE_ERRO)
    registrar(vazio["descricao"], "descricao",
              "Descrição vazia.", config.GRAVIDADE_AVISO)

    # 4) Duplicidade: só quando código E depósito se repetem juntos
    chave = df[config.COLUNAS_CHAVE].astype(str).apply(
        lambda coluna: coluna.str.strip().str.upper()
    )
    duplicado = (
        chave.duplicated(keep=False)
        & ~vazio["codigo_material"]
        & ~vazio["deposito"]
    )
    registrar(
        duplicado, "codigo_material",
        "A combinação código + depósito aparece em mais de uma linha. "
        "Confira se é lançamento repetido ou erro de digitação.",
        config.GRAVIDADE_AVISO,
    )

    # 5) Separa linhas válidas e inválidas (nada é apagado)
    colunas = config.COLUNAS_OBRIGATORIAS + ["linha_planilha"]

    validos = df[~invalida].copy()
    for coluna in config.COLUNAS_NUMERICAS:
        validos[coluna] = numeros[coluna][~invalida]
    for coluna in ["codigo_material", "descricao", "deposito"]:
        validos[coluna] = validos[coluna].fillna("").astype(str).str.strip()
    validos["descricao"] = validos["descricao"].replace("", "(sem descrição)")

    return ResultadoValidacao(
        colunas_ausentes=[],
        problemas=_tabela_problemas(problemas),
        dados_validos=validos[colunas].reset_index(drop=True),
        dados_invalidos=df[invalida][colunas].reset_index(drop=True),
    )