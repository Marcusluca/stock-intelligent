"""Leitura segura de arquivos Excel (.xlsx) e CSV.

Os dados são lidos como texto. O openpyxl lê apenas os valores das células:
fórmulas e macros nunca são executadas.
"""
import io
from pathlib import Path

import pandas as pd


class ArquivoInvalidoError(Exception):
    """Erro de leitura com mensagem em linguagem simples para o usuário."""


def carregar_arquivo(arquivo, nome=None) -> pd.DataFrame:
    """Lê um .xlsx ou .csv e devolve um DataFrame com todos os valores como texto.

    `arquivo` pode ser um caminho (str/Path) ou o arquivo enviado pelo Streamlit.
    Adiciona a coluna `linha_planilha` com o número da linha original
    (a linha 1 é o cabeçalho), para apontar erros com precisão.
    """
    if hasattr(arquivo, "seek"):
        arquivo.seek(0)  # volta ao início, caso o arquivo já tenha sido lido

    nome = (nome or getattr(arquivo, "name", None) or str(arquivo)).lower()

    try:
        if nome.endswith(".csv"):
            df = _ler_csv(arquivo)
        elif nome.endswith(".xlsx"):
            df = pd.read_excel(arquivo, dtype=str, engine="openpyxl")
        else:
            raise ArquivoInvalidoError(
                "Formato não suportado. Envie um arquivo .xlsx ou .csv."
            )
    except ArquivoInvalidoError:
        raise
    except Exception as erro:
        raise ArquivoInvalidoError(
            "Não foi possível ler o arquivo. Verifique se ele não está "
            f"corrompido e se tem um cabeçalho na primeira linha. ({erro})"
        ) from erro

    df["linha_planilha"] = df.index + 2

    # Remove apenas linhas totalmente em branco (comuns no fim de planilhas)
    colunas_dados = [c for c in df.columns if c != "linha_planilha"]
    df = df.dropna(how="all", subset=colunas_dados)
    return df.reset_index(drop=True)


def _ler_csv(arquivo) -> pd.DataFrame:
    """Lê CSV tentando detectar o separador (, ou ;) e a codificação."""
    if isinstance(arquivo, (str, Path)):
        conteudo = Path(arquivo).read_bytes()
    else:
        conteudo = arquivo.read()

    try:
        texto = conteudo.decode("utf-8-sig")
    except UnicodeDecodeError:
        texto = conteudo.decode("latin-1")  # comum em CSVs gerados no Excel/Windows

    return pd.read_csv(io.StringIO(texto), sep=None, engine="python", dtype=str)