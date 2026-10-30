"""Formatação de números no padrão brasileiro."""


def formatar_moeda(valor: float) -> str:
    """1925.5 -> 'R$ 1.925,50'"""
    texto = f"{valor:,.2f}"  # formato americano: 1,925.50
    texto = texto.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {texto}"


def formatar_percentual(valor: float) -> str:
    """75.0 -> '75,0%'"""
    return f"{valor:.1f}".replace(".", ",") + "%"


def formatar_inteiro(valor: int) -> str:
    """1234567 -> '1.234.567'"""
    return f"{valor:,}".replace(",", ".")


def formatar_decimal(valor: float, casas: int = 1) -> str:
    """78.5 -> '78,5'"""
    return f"{valor:.{casas}f}".replace(".", ",")


def formatar_quantidade(valor: float) -> str:
    """Quantidade sem zeros inúteis: 100.0 -> '100'; 1234.5 -> '1.234,5'"""
    if float(valor).is_integer():
        return formatar_inteiro(int(valor))
    texto = f"{valor:,.3f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return texto.rstrip("0").rstrip(",")