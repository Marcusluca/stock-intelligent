"""Dados demonstrativos FICTÍCIOS (etapa 5).

Servem apenas para mostrar o funcionamento do sistema. Não representam nenhum
estoque real. Todos os códigos começam com "DEMO" para deixar isso evidente.
Algumas linhas têm problemas de propósito, para exibir a validação.
"""
import pandas as pd

from stock_intelligence import config

NOME_ARQUIVO_DEMO = "dados_demonstrativos_ficticios.csv"

AVISO_DEMO = (
    "🧪 **Modo demonstração:** os dados abaixo são **fictícios**, criados apenas para "
    "mostrar como o sistema funciona. Eles não representam nenhum estoque real. "
    "Algumas linhas contêm erros de propósito, para exibir a validação."
)

# (codigo_material, descricao, deposito, estoque_sistema, estoque_fisico, valor_unitario)
# Tudo como texto, exatamente como o loader entregaria uma planilha real.
_LINHAS = [
    ("DEMO001", "Parafuso sextavado M10", "A", "500", "500", "0.45"),
    ("DEMO002", "Rolamento 6205", "A", "40", "38", "32.90"),
    ("DEMO003", "Motor elétrico 5 cv", "A", "6", "5", "2850.00"),
    ("DEMO004", "Cabo flexível 2,5 mm (metro)", "A", "1200", "1200", "3.80"),
    ("DEMO005", "Retentor 35x52x7", "A", "20", "12", "18.50"),
    ("DEMO006", "Filtro de óleo hidráulico", "A", "15", "15", "96.00"),
    ("DEMO007", "Anel o-ring 50 mm", "A", "300", "310", "1.20"),
    ("DEMO008", "Correia em V B-62", "A", "25", "24", "41.00"),
    ("DEMO009", "Graxa multiuso (kg)", "A", "80", "80", "27.50"),
    ("DEMO010", "Luva de borracha (par)", "A", "60", "55", "14.90"),
    ("DEMO011", "Rolamento 6205", "B", "30", "30", "32.90"),
    ("DEMO012", "Bomba d'água industrial", "B", "4", "3", "1750.00"),
    ("DEMO013", "Filtro de ar para compressor", "B", "22", "22", "74.00"),
    ("DEMO014", "Retentor 35x52x7", "B", "18", "18", "18.50"),
    ("DEMO015", 'Válvula solenoide 1/2"', "B", "10", "9", "385.00"),
    ("DEMO016", "Disjuntor 32 A", "B", "35", "38", "22.00"),
    ("DEMO017", "Fita isolante (rolo)", "B", "150", "150", "6.90"),
    ("DEMO018", "Mangueira hidráulica (metro)", "B", "90", "82", "58.00"),
    ("DEMO019", "Rolamento 6205", "C", "12", "12", "32.90"),
    ("DEMO020", "Motor elétrico 5 cv", "C", "2", "2", "2850.00"),
    ("DEMO021", "Parafuso sextavado M10", "C", "800", "760", "0.45"),
    ("DEMO022", "Sensor indutivo M18", "C", "14", "0", "210.00"),
    ("DEMO023", "Filtro de óleo hidráulico", "C", "8", "8", "96.00"),
    ("DEMO024", "Lubrificante sintético (litro)", "C", "200", "215", "38.00"),
    ("DEMO025", "Anel o-ring 50 mm", "C", "120", "120", "1.20"),
    # --- Linhas com problema de propósito (para demonstrar a validação) ---
    ("DEMO026", "Termostato analógico", "C", "n/d", "4", "120.00"),   # texto no lugar de número
    ("DEMO027", "Contator tripolar", "B", "-3", "2", "95.00"),        # quantidade negativa
    (None, "Item sem código", "A", "10", "9", "5.00"),                # código vazio
    ("DEMO006", "Filtro de óleo hidráulico", "A", "15", "14", "96.00"),  # mesmo código + depósito
]


def carregar_dados_demo() -> pd.DataFrame:
    """Devolve os dados fictícios no mesmo formato que `carregar_arquivo` entrega."""
    df = pd.DataFrame(_LINHAS, columns=config.COLUNAS_OBRIGATORIAS)
    df["linha_planilha"] = range(2, len(df) + 2)
    return df