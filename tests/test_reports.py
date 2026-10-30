import io
from datetime import datetime

import pandas as pd
import pytest
from openpyxl import load_workbook

from stock_intelligence import config
from stock_intelligence.calculations import calcular_divergencias, calcular_indicadores
from stock_intelligence.prioritization import CRITERIOS_PADRAO, priorizar
from stock_intelligence.reports import gerar_relatorio_excel, nome_sugerido_relatorio

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

PROBLEMAS = pd.DataFrame([{
    "linha": 4, "coluna": "estoque_sistema", "gravidade": "erro",
    "problema": "Valor não numérico.", "valor_original": "abc",
}])


def _entradas(linhas=EXEMPLO, problemas=None):
    """Monta tudo o que o relatório recebe, como o app faz."""
    df = pd.DataFrame(linhas, columns=COLUNAS)
    df["linha_planilha"] = range(2, len(df) + 2)
    originais = df.astype(str)  # o loader entrega tudo como texto
    calculado = calcular_divergencias(df)
    indicadores = calcular_indicadores(calculado, registros_invalidos=2)
    prioridades = priorizar(calculado)
    if problemas is None:
        problemas = pd.DataFrame(columns=config.COLUNAS_PROBLEMAS)
    return originais, calculado, indicadores, prioridades, problemas


def _abrir(entradas):
    originais, calculado, indicadores, prioridades, problemas = entradas
    conteudo = gerar_relatorio_excel(
        originais, calculado, indicadores, prioridades, problemas,
        CRITERIOS_PADRAO, "inventario.csv", datetime(2026, 10, 29, 19, 30),
    )
    return load_workbook(io.BytesIO(conteudo))


def _resumo(pasta):
    return {
        linha[0].value: linha[1].value
        for linha in pasta["Resumo"].iter_rows() if linha[0].value
    }


def test_abas_sem_problemas():
    pasta = _abrir(_entradas())
    assert pasta.sheetnames == ["Resumo", "Divergências", "Priorização", "Dados originais"]


def test_abas_com_problemas():
    pasta = _abrir(_entradas(problemas=PROBLEMAS))
    assert pasta.sheetnames == [
        "Resumo", "Divergências", "Priorização", "Problemas", "Dados originais"
    ]


def test_resumo_traz_os_indicadores():
    resumo = _resumo(_abrir(_entradas()))
    assert resumo["Registros analisados"] == 7
    assert resumo["Registros com divergência"] == 5
    assert resumo["Registros sem divergência"] == 2
    assert resumo["Itens com falta"] == 4
    assert resumo["Itens com sobra"] == 1
    assert resumo["% de registros com divergência"] == pytest.approx(5 / 7)
    assert resumo["Exposição financeira estimada (R$)"] == pytest.approx(5350.0)
    assert resumo["Registros com dados inválidos (fora dos cálculos)"] == 2
    assert resumo["Prioridade alta"] == 3
    assert resumo["Prioridade média"] == 2
    assert resumo["Prioridade baixa"] == 0


def test_resumo_traz_as_ressalvas():
    pasta = _abrir(_entradas())
    textos = [str(c.value) for c in pasta["Resumo"]["A"] if c.value]
    assert any("não um prejuízo contábil confirmado" in t for t in textos)
    assert any("recomendação" in t for t in textos)


def test_divergencias_com_classificacao_e_formato_de_moeda():
    ws = _abrir(_entradas())["Divergências"]
    cabecalho = [c.value for c in ws[1]]
    linhas = {linha[0].value: linha for linha in ws.iter_rows(min_row=2)}
    assert ws.max_row == 8  # cabeçalho + 7 registros

    impacto = linhas["P001"][cabecalho.index("Exposição financeira estimada (R$)")]
    assert impacto.value == pytest.approx(5000.0)  # número, não texto
    assert "R$" in impacto.number_format

    classificacao = cabecalho.index("Classificação")
    assert linhas["P002"][classificacao].value == "Falta"
    assert linhas["P004"][classificacao].value == "Sobra"
    assert linhas["P006"][classificacao].value == "Sem divergência"


def test_priorizacao_na_ordem_do_ranking():
    ws = _abrir(_entradas())["Priorização"]
    cabecalho = [c.value for c in ws[1]]
    linhas = list(ws.iter_rows(min_row=2, values_only=True))
    assert "Motivos" in cabecalho
    assert len(linhas) == 5
    assert linhas[0][0] == 1 and linhas[0][3] == "P002"


def test_dados_originais_ficam_como_foram_importados():
    ws = _abrir(_entradas())["Dados originais"]
    assert ws["A2"].value == "P001"
    assert ws["D2"].value == "10"  # texto, como veio da planilha


def test_textos_com_igual_nao_viram_formula():
    pasta = _abrir(_entradas([("F1", "=1+1", "A", 10, 9, 2.0)]))
    for nome in ("Divergências", "Priorização", "Dados originais"):
        encontradas = [
            c for linha in pasta[nome].iter_rows(min_row=2)
            for c in linha if c.value == "=1+1"
        ]
        assert encontradas, f"'=1+1' não encontrado em {nome}"
        assert all(c.data_type == "s" for c in encontradas)  # s = texto, f = fórmula


def test_nao_altera_os_dados_recebidos():
    entradas = _entradas(problemas=PROBLEMAS)
    quadros = [entradas[i] for i in (0, 1, 3, 4)]
    copias = [q.copy() for q in quadros]
    _abrir(entradas)
    for original, copia in zip(quadros, copias):
        pd.testing.assert_frame_equal(original, copia)


def test_sem_divergencias_gera_relatorio_valido():
    pasta = _abrir(_entradas([("M4", "Cabo", "B", 200, 200, 15.0)]))
    assert pasta["Priorização"].max_row == 1  # só o cabeçalho
    assert _resumo(pasta)["Prioridade alta"] == 0


def test_nome_sugerido():
    assert nome_sugerido_relatorio("exemplo_mvp.csv") == "stock_intelligence_exemplo_mvp.xlsx"
    assert nome_sugerido_relatorio("meu arquivo (1).xlsx") == "stock_intelligence_meu_arquivo_1.xlsx"
    assert nome_sugerido_relatorio(".csv") == "stock_intelligence_inventario.xlsx"