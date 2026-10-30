"""Cálculos de inventário. Funções puras: mesma entrada, mesma saída."""
import numpy as np
import pandas as pd

from stock_intelligence import config


def calcular_divergencias(df: pd.DataFrame) -> pd.DataFrame:
    """Acrescenta as colunas de divergência, tipo, quantidade e impacto."""
    resultado = df.copy()

    resultado["divergencia"] = (
        resultado["estoque_fisico"] - resultado["estoque_sistema"]
    ).round(config.CASAS_DECIMAIS_QUANTIDADE)

    resultado["tipo_divergencia"] = np.select(
        [resultado["divergencia"] < 0, resultado["divergencia"] > 0],
        [config.TIPO_FALTA, config.TIPO_SOBRA],
        default=config.TIPO_SEM_DIVERGENCIA,
    )

    resultado["quantidade_divergente"] = resultado["divergencia"].abs()
    resultado["impacto_financeiro"] = (
        resultado["quantidade_divergente"] * resultado["valor_unitario"]
    )
    return resultado


def calcular_indicadores(df_calculado: pd.DataFrame, registros_invalidos: int = 0) -> dict:
    """Indicadores gerais. Recebe o resultado de `calcular_divergencias`.

    Faltas e sobras são contadas em NÚMERO DE ITENS, e não em quantidade somada,
    porque materiais diferentes podem usar unidades de medida diferentes.
    """
    total = len(df_calculado)
    itens_com_falta = int((df_calculado["tipo_divergencia"] == config.TIPO_FALTA).sum())
    itens_com_sobra = int((df_calculado["tipo_divergencia"] == config.TIPO_SOBRA).sum())
    divergentes = itens_com_falta + itens_com_sobra

    return {
        "total_analisados": total,
        "total_divergentes": divergentes,
        "total_sem_divergencia": total - divergentes,
        "itens_com_falta": itens_com_falta,
        "itens_com_sobra": itens_com_sobra,
        "exposicao_financeira": float(df_calculado["impacto_financeiro"].sum()),
        "percentual_divergentes": (divergentes / total * 100) if total else 0.0,
        "registros_invalidos": registros_invalidos,
    }