import pandas as pd

from stock_intelligence.validation import validar

COLUNAS = ["codigo_material", "descricao", "deposito",
           "estoque_sistema", "estoque_fisico", "valor_unitario"]


def _bruto(*linhas):
    """Cada linha é uma tupla na ordem de COLUNAS, tudo como texto (como no loader)."""
    return pd.DataFrame(list(linhas), columns=COLUNAS, dtype=str)


def test_coluna_ausente():
    df = pd.DataFrame({"codigo_material": ["A"], "descricao": ["x"]})
    resultado = validar(df)
    assert "deposito" in resultado.colunas_ausentes
    assert resultado.dados_validos.empty


def test_linha_correta_nao_gera_problemas():
    resultado = validar(_bruto(("M1", "Item", "A", "10", "9", "2.5")))
    assert resultado.problemas.empty
    assert len(resultado.dados_validos) == 1


def test_mesmo_codigo_em_depositos_diferentes_nao_e_duplicidade():
    resultado = validar(_bruto(
        ("M1", "Item", "A", "10", "10", "1"),
        ("M1", "Item", "B", "5", "5", "1"),
    ))
    assert resultado.problemas.empty


def test_mesmo_codigo_e_deposito_gera_aviso_mas_continua_nos_calculos():
    resultado = validar(_bruto(
        ("M1", "Item", "A", "10", "10", "1"),
        ("m1 ", "Item", "a", "10", "10", "1"),  # difere só em caixa e espaços
    ))
    avisos = resultado.problemas[resultado.problemas["gravidade"] == "aviso"]
    assert len(avisos) == 2
    assert len(resultado.dados_validos) == 2


def test_texto_em_coluna_numerica_vai_para_invalidos():
    resultado = validar(_bruto(
        ("M1", "Item", "A", "abc", "10", "1"),
        ("M2", "Item", "A", "10", "10", "1"),
    ))
    assert len(resultado.dados_validos) == 1
    assert len(resultado.dados_invalidos) == 1
    problema = resultado.problemas.iloc[0]
    assert problema["linha"] == 2          # primeira linha de dados = linha 2
    assert problema["coluna"] == "estoque_sistema"


def test_valor_negativo_e_erro():
    resultado = validar(_bruto(("M1", "Item", "A", "-5", "10", "1")))
    assert resultado.quantidade_invalidos == 1


def test_valor_unitario_negativo_e_erro():
    resultado = validar(_bruto(("M1", "Item", "A", "5", "10", "-1")))
    assert resultado.quantidade_invalidos == 1


def test_codigo_vazio_e_erro():
    resultado = validar(_bruto(("  ", "Item", "A", "5", "5", "1")))
    assert resultado.quantidade_invalidos == 1


def test_virgula_decimal_e_aceita():
    resultado = validar(_bruto(("M1", "Item", "A", "10", "9", "2,50")))
    assert resultado.dados_validos.iloc[0]["valor_unitario"] == 2.5