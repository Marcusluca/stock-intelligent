import pandas as pd
import pytest

from stock_intelligence.calculations import calcular_divergencias, calcular_indicadores


def _montar(linhas):
    """Cria um DataFrame de teste. Cada linha: (sistema, fisico, valor_unitario)."""
    df = pd.DataFrame(
        linhas, columns=["estoque_sistema", "estoque_fisico", "valor_unitario"]
    )
    return df.astype(float)


def test_falta():
    r = calcular_divergencias(_montar([(100, 90, 2.5)])).iloc[0]
    assert r["divergencia"] == -10
    assert r["tipo_divergencia"] == "Falta"
    assert r["quantidade_divergente"] == 10
    assert r["impacto_financeiro"] == pytest.approx(25.0)


def test_sobra():
    r = calcular_divergencias(_montar([(10, 12, 800)])).iloc[0]
    assert r["divergencia"] == 2
    assert r["tipo_divergencia"] == "Sobra"
    assert r["impacto_financeiro"] == pytest.approx(1600.0)


def test_sem_divergencia():
    r = calcular_divergencias(_montar([(200, 200, 15)])).iloc[0]
    assert r["divergencia"] == 0
    assert r["tipo_divergencia"] == "Sem divergência"
    assert r["impacto_financeiro"] == 0


def test_erro_de_arredondamento_nao_cria_divergencia():
    # 0.1 + 0.2 != 0.3 em ponto flutuante; o sistema não pode tratar isso como sobra
    r = calcular_divergencias(_montar([(0.3, 0.1 + 0.2, 10)])).iloc[0]
    assert r["tipo_divergencia"] == "Sem divergência"


def test_indicadores_com_exemplo_do_enunciado():
    df = _montar([(100, 90, 2.5), (50, 48, 150), (10, 12, 800), (200, 200, 15)])
    ind = calcular_indicadores(calcular_divergencias(df), registros_invalidos=2)
    assert ind["total_analisados"] == 4
    assert ind["total_divergentes"] == 3
    assert ind["total_sem_divergencia"] == 1
    assert ind["itens_com_falta"] == 2
    assert ind["itens_com_sobra"] == 1
    assert ind["exposicao_financeira"] == pytest.approx(1925.0)
    assert ind["percentual_divergentes"] == pytest.approx(75.0)
    assert ind["registros_invalidos"] == 2


def test_indicadores_com_tabela_vazia_nao_quebra():
    ind = calcular_indicadores(calcular_divergencias(_montar([])))
    assert ind["total_analisados"] == 0
    assert ind["percentual_divergentes"] == 0.0