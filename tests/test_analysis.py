import pandas as pd

from stock_intelligence.analysis import (
    divergencias_por_deposito,
    filtrar,
    ordenar,
    ranking_depositos,
    ranking_materiais,
)
from stock_intelligence.calculations import calcular_divergencias

COLUNAS = ["codigo_material", "descricao", "deposito",
           "estoque_sistema", "estoque_fisico", "valor_unitario"]


def _calculado(linhas=None):
    if linhas is None:
        linhas = [
            ("M1", "Parafuso industrial", "A", 100, 90, 2.5),    # falta, R$ 25
            ("M2", "Rolamento industrial", "A", 50, 48, 150),    # falta, R$ 300
            ("M3", "Motor elétrico", "B", 10, 12, 800),         # sobra, R$ 1.600
            ("M4", "Cabo elétrico", "B", 200, 200, 15),         # sem divergência
            ("M1", "Parafuso industrial", "B", 30, 30, 2.5),    # sem divergência
        ]
    return calcular_divergencias(pd.DataFrame(linhas, columns=COLUNAS))


def test_filtrar_por_deposito():
    assert len(filtrar(_calculado(), depositos=["B"])) == 3


def test_filtrar_por_tipo():
    assert len(filtrar(_calculado(), tipos=["Falta"])) == 2


def test_lista_vazia_de_filtro_devolve_nada():
    assert filtrar(_calculado(), depositos=[]).empty


def test_busca_por_codigo_ignora_maiusculas():
    resultado = filtrar(_calculado(), busca="m3")
    assert list(resultado["codigo_material"]) == ["M3"]


def test_busca_por_descricao():
    resultado = filtrar(_calculado(), busca="rolamento")
    assert list(resultado["codigo_material"]) == ["M2"]


def test_busca_com_caractere_especial_nao_quebra():
    assert filtrar(_calculado(), busca="(").empty


def test_busca_vazia_nao_filtra():
    assert len(filtrar(_calculado(), busca="  ")) == 5


def test_ordenar_por_impacto_decrescente():
    resultado = ordenar(_calculado(), "impacto_financeiro", crescente=False)
    assert resultado.iloc[0]["codigo_material"] == "M3"


def test_ordenar_por_codigo_desempata_por_deposito():
    resultado = ordenar(_calculado(), "codigo_material", crescente=True)
    pares = list(zip(resultado["codigo_material"], resultado["deposito"]))
    assert pares[:2] == [("M1", "A"), ("M1", "B")]


def test_ranking_materiais_ignora_itens_sem_divergencia():
    ranking = ranking_materiais(_calculado())
    assert list(ranking["codigo_material"]) == ["M3", "M2", "M1"]


def test_ranking_materiais_respeita_limite():
    assert len(ranking_materiais(_calculado(), n=2)) == 2


def test_ranking_depositos():
    ranking = ranking_depositos(_calculado()).set_index("deposito")
    assert list(ranking.index) == ["B", "A"]  # B tem R$ 1.600; A tem R$ 325
    assert ranking.loc["A", "impacto_financeiro"] == 325
    assert ranking.loc["A", "itens_divergentes"] == 2
    assert ranking.loc["A", "itens_analisados"] == 2
    assert ranking.loc["B", "itens_divergentes"] == 1
    assert ranking.loc["B", "itens_analisados"] == 3


def test_divergencias_por_deposito():
    tabela = divergencias_por_deposito(_calculado()).set_index("deposito")
    assert tabela.loc["A", "Falta"] == 2
    assert tabela.loc["A", "Sobra"] == 0
    assert tabela.loc["B", "Falta"] == 0
    assert tabela.loc["B", "Sobra"] == 1


def test_divergencias_por_deposito_sem_divergencias():
    sem = _calculado([("M4", "Cabo", "B", 200, 200, 15)])
    tabela = divergencias_por_deposito(sem)
    assert tabela.empty
    assert list(tabela.columns) == ["deposito", "Falta", "Sobra"]