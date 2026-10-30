from stock_intelligence import config
from stock_intelligence.ajuda import texto_como_interpretar
from stock_intelligence.formatting import formatar_percentual
from stock_intelligence.prioritization import CRITERIOS_PADRAO


def test_texto_explica_que_a_exposicao_e_uma_estimativa():
    texto = texto_como_interpretar()
    assert "estimativa" in texto
    assert "prejuízo contábil" in texto


def test_texto_usa_pesos_e_faixas_do_config():
    texto = texto_como_interpretar()
    for criterio in CRITERIOS_PADRAO:
        assert criterio.rotulo in texto
        assert formatar_percentual(criterio.peso * 100) in texto
    assert f"{config.LIMITE_PRIORIDADE_ALTA} pontos" in texto
    assert f"{config.LIMITE_PRIORIDADE_MEDIA} pontos" in texto


def test_texto_diz_que_a_priorizacao_e_uma_recomendacao():
    assert "recomendação" in texto_como_interpretar()