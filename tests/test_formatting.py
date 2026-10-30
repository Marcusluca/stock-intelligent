from stock_intelligence.formatting import (
    formatar_inteiro,
    formatar_moeda,
    formatar_percentual,
    formatar_quantidade,
)


def test_moeda():
    assert formatar_moeda(1925) == "R$ 1.925,00"
    assert formatar_moeda(0.5) == "R$ 0,50"


def test_percentual():
    assert formatar_percentual(75.0) == "75,0%"


def test_inteiro():
    assert formatar_inteiro(1234567) == "1.234.567"


def test_quantidade():
    assert formatar_quantidade(100.0) == "100"
    assert formatar_quantidade(-10.0) == "-10"
    assert formatar_quantidade(2.5) == "2,5"
    assert formatar_quantidade(1234.5) == "1.234,5"