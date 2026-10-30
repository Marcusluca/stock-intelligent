import pandas as pd
import pytest

from stock_intelligence import config
from stock_intelligence.calculations import calcular_divergencias, calcular_indicadores
from stock_intelligence.demo_data import AVISO_DEMO, carregar_dados_demo
from stock_intelligence.prioritization import priorizar
from stock_intelligence.validation import validar


def test_demo_tem_o_formato_que_o_loader_entrega():
    bruto = carregar_dados_demo()
    for coluna in config.COLUNAS_OBRIGATORIAS + ["linha_planilha"]:
        assert coluna in bruto.columns
    assert len(bruto) == 29


def test_demo_e_claramente_ficticia():
    bruto = carregar_dados_demo()
    codigos = bruto["codigo_material"].dropna()
    assert codigos.str.startswith("DEMO").all()
    assert "fictícios" in AVISO_DEMO


def test_demo_e_reproduzivel():
    pd.testing.assert_frame_equal(carregar_dados_demo(), carregar_dados_demo())


def test_demo_mostra_a_validacao_funcionando():
    resultado = validar(carregar_dados_demo())
    assert resultado.colunas_ausentes == []
    assert len(resultado.dados_validos) == 26
    assert resultado.quantidade_invalidos == 3

    problemas = resultado.problemas
    assert (problemas["gravidade"] == "erro").sum() == 3
    assert (problemas["gravidade"] == "aviso").sum() == 2
    assert sorted(problemas["linha"]) == [7, 27, 28, 29, 30]


def test_demo_indicadores():
    resultado = validar(carregar_dados_demo())
    calculado = calcular_divergencias(resultado.dados_validos)
    ind = calcular_indicadores(calculado, resultado.quantidade_invalidos)
    assert ind["total_analisados"] == 26
    assert ind["total_divergentes"] == 14
    assert ind["total_sem_divergencia"] == 12
    assert ind["itens_com_falta"] == 11
    assert ind["itens_com_sobra"] == 3
    assert ind["exposicao_financeira"] == pytest.approx(9480.30)
    assert ind["percentual_divergentes"] == pytest.approx(14 / 26 * 100)
    assert ind["registros_invalidos"] == 3


def test_demo_priorizacao():
    resultado = validar(carregar_dados_demo())
    prioridades = priorizar(calcular_divergencias(resultado.dados_validos))
    assert list(prioridades["codigo_material"][:4]) == ["DEMO022", "DEMO012", "DEMO003", "DEMO005"]
    assert prioridades["prioridade"].value_counts().to_dict() == {"Média": 8, "Alta": 4, "Baixa": 2}