import pandas as pd
import pytest

from stock_intelligence import config
from stock_intelligence.calculations import calcular_divergencias
from stock_intelligence.prioritization import CRITERIOS_PADRAO, Criterio, priorizar

COLUNAS = ["codigo_material", "descricao", "deposito",
           "estoque_sistema", "estoque_fisico", "valor_unitario"]

EXEMPLO = [
    ("P001", "Motor elétrico grande", "A", 10, 9, 5000.00),
    ("P002", "Retentor", "A", 4, 0, 20.00),
    ("P003", "Filtro de óleo", "B", 100, 98, 35.00),
    ("P004", "Anel de vedação", "B", 50, 55, 10.00),
    ("P005", "Cabo elétrico", "B", 200, 190, 15.00),
    ("P006", "Rolamento", "A", 30, 30, 150.00),
    ("P007", "Parafuso", "A", 500, 500, 0.50),
]


def _calculado(linhas=EXEMPLO):
    df = pd.DataFrame(linhas, columns=COLUNAS)
    df["linha_planilha"] = range(2, len(df) + 2)
    return calcular_divergencias(df)


def test_itens_sem_divergencia_nao_entram():
    resultado = priorizar(_calculado())
    assert len(resultado) == 5
    assert "P006" not in list(resultado["codigo_material"])
    assert "P007" not in list(resultado["codigo_material"])


def test_ordem_e_pontuacao():
    resultado = priorizar(_calculado())
    assert list(resultado["codigo_material"]) == ["P002", "P001", "P005", "P003", "P004"]
    assert list(resultado["pontuacao"]) == pytest.approx([78.5, 74.5, 69.0, 51.4, 46.0])
    assert list(resultado["posicao"]) == [1, 2, 3, 4, 5]


def test_faixas_de_prioridade():
    resultado = priorizar(_calculado())
    assert list(resultado["prioridade"]) == ["Alta", "Alta", "Alta", "Média", "Média"]


def test_valor_financeiro_sozinho_nao_decide():
    resultado = priorizar(_calculado()).set_index("codigo_material")
    primeiro = priorizar(_calculado()).iloc[0]
    assert primeiro["codigo_material"] == "P002"  # retentor: 100% do estoque, só R$ 80
    assert primeiro["impacto_financeiro"] < resultado.loc["P001", "impacto_financeiro"]


def test_pontos_por_criterio():
    resultado = priorizar(_calculado()).set_index("codigo_material")
    p002 = resultado.loc["P002"]
    assert p002["pontos_impacto"] == pytest.approx(60.0)      # 3ª posição de 5
    assert p002["pontos_percentual"] == pytest.approx(100.0)  # 4 de 4 = 100% (limite: 25%)
    assert p002["pontos_tipo"] == pytest.approx(100.0)        # falta
    assert p002["pontos_deposito"] == pytest.approx(50.0)     # depósito A: 2 de 4 itens
    assert resultado.loc["P004", "pontos_tipo"] == pytest.approx(60.0)  # sobra
    assert resultado.loc["P003", "pontos_deposito"] == pytest.approx(100.0)  # B: 3 de 3


def test_pontuacao_e_a_media_ponderada_dos_criterios():
    resultado = priorizar(_calculado())
    for _, linha in resultado.iterrows():
        esperado = sum(
            config.PESOS_CRITERIOS[nome] * linha[f"pontos_{nome}"]
            for nome in config.PESOS_CRITERIOS
        )
        assert linha["pontuacao"] == pytest.approx(esperado, abs=0.1)


def test_motivos_explicam_a_priorizacao():
    resultado = priorizar(_calculado()).set_index("codigo_material")
    motivos = resultado.loc["P002", "motivos"]
    assert "R$ 80,00" in motivos
    assert "100,0%" in motivos
    assert "falta física" in motivos
    assert "depósito A" in motivos


def test_estoque_zero_no_sistema():
    resultado = priorizar(_calculado([("X1", "Item", "A", 0, 5, 10.0)]))
    linha = resultado.iloc[0]
    assert linha["pontos_percentual"] == pytest.approx(100.0)
    assert "estoque zero" in linha["motivos"]


def test_sem_divergencias_devolve_tabela_vazia():
    resultado = priorizar(_calculado([("M4", "Cabo", "B", 200, 200, 15.0)]))
    assert resultado.empty
    assert "motivos" in resultado.columns


def _criterio_criticidade():
    return Criterio(
        nome="criticidade",
        rotulo="Criticidade",
        descricao="Criticidade informada na planilha (0 a 100).",
        peso=1.0,
        pontuar=lambda d: d["criticidade"],
        explicar=lambda linha: f"criticidade {int(linha['criticidade'])}",
        colunas_necessarias=("criticidade",),
    )


def test_criterio_extra_e_ignorado_se_a_coluna_nao_existe():
    resultado = priorizar(_calculado(), CRITERIOS_PADRAO + [_criterio_criticidade()])
    assert "pontos_criticidade" not in resultado.columns
    assert list(resultado["pontuacao"]) == pytest.approx([78.5, 74.5, 69.0, 51.4, 46.0])


def test_criterio_extra_entra_quando_a_coluna_existe():
    calculado = _calculado()
    calculado["criticidade"] = [10, 90, 20, 30, 40, 50, 60]
    resultado = priorizar(calculado, [_criterio_criticidade()])
    assert list(resultado["codigo_material"]) == ["P002", "P005", "P004", "P003", "P001"]
    assert resultado.iloc[0]["pontuacao"] == pytest.approx(90.0)


def test_sem_nenhum_criterio_disponivel_da_erro():
    with pytest.raises(ValueError):
        priorizar(_calculado(), [_criterio_criticidade()])