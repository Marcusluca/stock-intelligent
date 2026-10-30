"""Gráficos Plotly. Este arquivo só monta as figuras; quem exibe é a interface."""
import plotly.graph_objects as go

from stock_intelligence import config
from stock_intelligence.formatting import formatar_moeda

COR_FALTA = "#E74C3C"
COR_SOBRA = "#3498DB"
COR_DESTAQUE = "#F39C12"


def _ajustar_layout(fig, titulo, altura=380):
    """Aparência comum a todos os gráficos.
    separators=",." faz o Plotly usar vírgula decimal e ponto de milhar."""
    fig.update_layout(
        title=titulo,
        height=altura,
        separators=",.",
        margin=dict(l=10, r=10, t=60, b=10),
    )
    return fig


def grafico_faltas_sobras(itens_com_falta: int, itens_com_sobra: int):
    fig = go.Figure(go.Bar(
        x=["Faltas", "Sobras"],
        y=[itens_com_falta, itens_com_sobra],
        marker_color=[COR_FALTA, COR_SOBRA],
        text=[str(itens_com_falta), str(itens_com_sobra)],
        textposition="outside",
        cliponaxis=False,
    ))
    fig.update_layout(showlegend=False, yaxis_title="Número de itens")
    fig.update_yaxes(rangemode="tozero")
    return _ajustar_layout(fig, "Faltas versus sobras (número de itens)")


def grafico_divergencias_por_deposito(tabela):
    """`tabela` vem de analysis.divergencias_por_deposito."""
    fig = go.Figure()
    fig.add_bar(name="Faltas", x=tabela["deposito"], y=tabela[config.TIPO_FALTA],
                marker_color=COR_FALTA)
    fig.add_bar(name="Sobras", x=tabela["deposito"], y=tabela[config.TIPO_SOBRA],
                marker_color=COR_SOBRA)
    fig.update_layout(barmode="group", xaxis_title="Depósito", yaxis_title="Número de itens")
    fig.update_xaxes(type="category")  # depósito "1" não deve virar número
    fig.update_yaxes(rangemode="tozero")
    return _ajustar_layout(fig, "Divergências por depósito (número de itens)")


def grafico_ranking(rotulos, valores, titulo, detalhes=None):
    """Barras horizontais de um ranking (maior valor no topo).

    Usa posições numéricas no eixo Y e coloca os rótulos por cima. Assim,
    dois itens com o mesmo rótulo não se misturam na mesma barra.
    """
    detalhes = detalhes if detalhes is not None else [""] * len(rotulos)
    posicoes = list(range(len(rotulos)))
    maior = max(valores, default=0)

    fig = go.Figure(go.Bar(
        x=valores,
        y=posicoes,
        orientation="h",
        marker_color=COR_DESTAQUE,
        text=[formatar_moeda(v) for v in valores],
        textposition="outside",
        cliponaxis=False,
        customdata=list(zip(rotulos, detalhes)),
        hovertemplate="%{customdata[0]}<br>%{customdata[1]}<br>%{text}<extra></extra>",
    ))
    fig.update_yaxes(tickmode="array", tickvals=posicoes, ticktext=rotulos, autorange="reversed")
    fig.update_xaxes(range=[0, maior * 1.3 if maior > 0 else 1],
                     title="Exposição financeira estimada (R$)")
    return _ajustar_layout(fig, titulo, altura=max(300, 45 * len(rotulos) + 120))