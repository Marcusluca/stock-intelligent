"""Priorização das investigações (etapa 3).

A pontuação de cada divergência é a média ponderada de vários CRITÉRIOS.
Cada critério dá de 0 a 100 pontos e sabe explicar, em texto, o seu resultado.

Isto é uma RECOMENDAÇÃO baseada apenas nos dados disponíveis, não uma decisão
definitiva. Tudo é calculado por regras fixas (sem IA generativa), então o
mesmo arquivo sempre gera o mesmo resultado.

Para acrescentar um critério no futuro (criticidade, histórico, curva ABC...):
crie um `Criterio` e coloque-o na lista de critérios. Nada mais precisa mudar.
"""
from dataclasses import dataclass
from typing import Callable

import pandas as pd

from stock_intelligence import config
from stock_intelligence.formatting import formatar_moeda, formatar_percentual

SEPARADOR_MOTIVOS = "; "


@dataclass(frozen=True)
class Criterio:
    """Uma regra de priorização."""

    nome: str        # identificador curto; gera a coluna "pontos_<nome>"
    rotulo: str      # nome exibido ao usuário
    descricao: str   # explicação exibida ao usuário
    peso: float      # importância relativa
    pontuar: Callable[[pd.DataFrame], pd.Series]  # devolve de 0 a 100 por linha
    explicar: Callable[[pd.Series], str]          # texto do motivo de uma linha
    # Colunas que a planilha precisa ter para o critério valer. Se faltar
    # alguma, o critério é ignorado. (Os critérios padrão não exigem nada extra.)
    colunas_necessarias: tuple = ()


# ---------- Critério 1: impacto financeiro ----------

def _pontos_impacto(d: pd.DataFrame) -> pd.Series:
    # rank(pct=True): o maior valor recebe 1.0, o menor recebe 1/n.
    # Usar a POSIÇÃO evita que um único valor gigante esmague todos os outros.
    return d["impacto_financeiro"].rank(pct=True) * 100


def _explicar_impacto(linha: pd.Series) -> str:
    return (
        f"impacto financeiro estimado de {formatar_moeda(linha['impacto_financeiro'])} "
        f"(posição {int(linha['posicao_impacto'])} de {int(linha['total_divergentes'])} "
        "itens divergentes)"
    )


# ---------- Critério 2: proporção da divergência ----------

def _pontos_percentual(d: pd.DataFrame) -> pd.Series:
    return (d["percentual_divergente"] / config.PERCENTUAL_REFERENCIA).clip(upper=1) * 100


def _explicar_percentual(linha: pd.Series) -> str:
    if linha["estoque_sistema"] == 0:
        return "o sistema registra estoque zero, mas existe material físico"
    return (
        f"a divergência equivale a {formatar_percentual(linha['percentual_divergente'] * 100)} "
        "do estoque do sistema"
    )


# ---------- Critério 3: tipo de divergência ----------

def _pontos_tipo(d: pd.DataFrame) -> pd.Series:
    return d["tipo_divergencia"].map(config.PONTOS_POR_TIPO).astype(float)


def _explicar_tipo(linha: pd.Series) -> str:
    if linha["tipo_divergencia"] == config.TIPO_FALTA:
        return "falta física: o sistema indica material que não foi encontrado"
    return "sobra física: há material que o sistema não registra"


# ---------- Critério 4: depósito ----------

def _pontos_deposito(d: pd.DataFrame) -> pd.Series:
    return d["taxa_divergencia_deposito"] * 100


def _explicar_deposito(linha: pd.Series) -> str:
    return (
        f"{formatar_percentual(linha['taxa_divergencia_deposito'] * 100)} dos itens do "
        f"depósito {linha['deposito']} têm divergência"
    )


CRITERIOS_PADRAO = [
    Criterio(
        nome="impacto",
        rotulo="Impacto financeiro",
        descricao=(
            "Posição do item no ranking de impacto financeiro estimado entre as "
            "divergências. O maior impacto recebe 100 pontos e os demais recebem "
            "pontos proporcionais à sua posição."
        ),
        peso=config.PESOS_CRITERIOS["impacto"],
        pontuar=_pontos_impacto,
        explicar=_explicar_impacto,
    ),
    Criterio(
        nome="percentual",
        rotulo="Proporção da divergência",
        descricao=(
            "Tamanho da divergência em relação ao estoque do sistema. Como não "
            "depende da unidade de medida, permite comparar materiais diferentes. "
            f"Divergências de {formatar_percentual(config.PERCENTUAL_REFERENCIA * 100)} "
            "do estoque ou mais valem 100 pontos."
        ),
        peso=config.PESOS_CRITERIOS["percentual"],
        pontuar=_pontos_percentual,
        explicar=_explicar_percentual,
    ),
    Criterio(
        nome="tipo",
        rotulo="Tipo de divergência",
        descricao=(
            f"Falta vale {config.PONTOS_POR_TIPO[config.TIPO_FALTA]} pontos e sobra vale "
            f"{config.PONTOS_POR_TIPO[config.TIPO_SOBRA]}. É uma suposição inicial: a falta "
            "indica material que o sistema diz ter, mas que não foi encontrado."
        ),
        peso=config.PESOS_CRITERIOS["tipo"],
        pontuar=_pontos_tipo,
        explicar=_explicar_tipo,
    ),
    Criterio(
        nome="deposito",
        rotulo="Depósito",
        descricao=(
            "Percentual de itens com divergência no depósito do item. Muitas "
            "divergências no mesmo depósito podem indicar um problema de processo, "
            "e não só erros isolados."
        ),
        peso=config.PESOS_CRITERIOS["deposito"],
        pontuar=_pontos_deposito,
        explicar=_explicar_deposito,
    ),
]


def classificar_prioridade(pontuacao: float) -> str:
    """Converte a pontuação (0 a 100) em Alta, Média ou Baixa."""
    if pontuacao >= config.LIMITE_PRIORIDADE_ALTA:
        return config.PRIORIDADE_ALTA
    if pontuacao >= config.LIMITE_PRIORIDADE_MEDIA:
        return config.PRIORIDADE_MEDIA
    return config.PRIORIDADE_BAIXA


def _preparar(df_calculado: pd.DataFrame) -> pd.DataFrame:
    """Separa as divergências e cria as colunas auxiliares usadas pelos critérios."""
    d = df_calculado[df_calculado["quantidade_divergente"] > 0].copy()

    # Proporção: divergência / estoque do sistema. Se o sistema registra zero,
    # não dá para dividir: consideramos 100%.
    sistema = d["estoque_sistema"]
    d["percentual_divergente"] = (
        d["quantidade_divergente"] / sistema.where(sistema > 0)
    ).fillna(1.0)

    d["posicao_impacto"] = d["impacto_financeiro"].rank(method="min", ascending=False)
    d["total_divergentes"] = len(d)

    # Taxa de divergência do depósito, calculada com TODOS os registros
    # (e não só os divergentes), senão o resultado seria sempre 100%.
    tem_divergencia = df_calculado["quantidade_divergente"] > 0
    taxa = tem_divergencia.groupby(df_calculado["deposito"]).mean()
    d["taxa_divergencia_deposito"] = d["deposito"].map(taxa)
    return d


def _montar_motivos(linha: pd.Series, criterios: list) -> str:
    texto = SEPARADOR_MOTIVOS.join(c.explicar(linha) for c in criterios)
    return texto[0].upper() + texto[1:]


def listar_motivos(motivos: str) -> list:
    """Quebra o texto de motivos em frases, para exibir em lista."""
    partes = [p.strip() for p in motivos.split(SEPARADOR_MOTIVOS)]
    return [p[0].upper() + p[1:] + "." for p in partes if p]


def priorizar(df_calculado: pd.DataFrame, criterios=None) -> pd.DataFrame:
    """Devolve as divergências ordenadas da maior para a menor prioridade.

    Recebe o resultado de `calcular_divergencias`. Itens sem divergência
    não aparecem. Cada linha traz os pontos por critério e os motivos.
    """
    criterios = CRITERIOS_PADRAO if criterios is None else criterios
    ativos = [
        c for c in criterios
        if all(coluna in df_calculado.columns for coluna in c.colunas_necessarias)
    ]
    if not ativos:
        raise ValueError("Nenhum critério de priorização está disponível para estes dados.")

    colunas_pontos = [f"pontos_{c.nome}" for c in ativos]
    colunas_saida = (
        ["posicao", "prioridade", "pontuacao", "codigo_material", "descricao", "deposito",
         "tipo_divergencia", "estoque_sistema", "estoque_fisico", "divergencia",
         "percentual_divergente", "impacto_financeiro"]
        + colunas_pontos
        + ["motivos", "linha_planilha"]
    )

    d = _preparar(df_calculado)
    if d.empty:
        return pd.DataFrame(columns=colunas_saida)

    soma_pesos = sum(c.peso for c in ativos)
    total = pd.Series(0.0, index=d.index)
    for criterio in ativos:
        pontos = criterio.pontuar(d).astype(float)
        d[f"pontos_{criterio.nome}"] = pontos.round(1)
        total += pontos * criterio.peso

    d["pontuacao"] = (total / soma_pesos).round(1)
    d["prioridade"] = d["pontuacao"].map(classificar_prioridade)
    d["motivos"] = d.apply(lambda linha: _montar_motivos(linha, ativos), axis=1)

    # Empates: maior impacto primeiro; depois código e depósito (ordem fixa)
    d = d.sort_values(
        ["pontuacao", "impacto_financeiro", "codigo_material", "deposito"],
        ascending=[False, False, True, True],
    )
    d["posicao"] = range(1, len(d) + 1)
    return d[colunas_saida].reset_index(drop=True)