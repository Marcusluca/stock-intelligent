"""Geração do relatório Excel (etapa 4).

O relatório é montado em memória e entregue como bytes: o arquivo original
importado nunca é tocado. Textos vindos da planilha são gravados sempre como
TEXTO (nunca como fórmula), para que nada do arquivo importado seja executado
quando o relatório for aberto no Excel.
"""
import io
import re
from datetime import datetime

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from stock_intelligence import config

FORMATO_MOEDA = '"R$" #,##0.00'
FORMATO_PERCENTUAL = "0.0%"
FORMATO_PONTOS = "0.0"

FONTE_CABECALHO = Font(bold=True, color="FFFFFF")
PREENCHIMENTO_CABECALHO = PatternFill("solid", start_color="1F4E78")
FONTE_TITULO = Font(bold=True, size=14)
FONTE_SECAO = Font(bold=True, size=11)
LARGURA_MAXIMA = 80

# Nome da coluna no sistema -> título exibido no Excel
CABECALHOS_DIVERGENCIAS = {
    "codigo_material": "Código",
    "descricao": "Descrição",
    "deposito": "Depósito",
    "estoque_sistema": "Estoque sistema",
    "estoque_fisico": "Estoque físico",
    "divergencia": "Divergência",
    "tipo_divergencia": "Classificação",
    "quantidade_divergente": "Qtd. divergente",
    "valor_unitario": "Valor unitário (R$)",
    "impacto_financeiro": "Exposição financeira estimada (R$)",
    "linha_planilha": "Linha na planilha",
}

CABECALHOS_PROBLEMAS = {
    "linha": "Linha",
    "coluna": "Coluna",
    "gravidade": "Gravidade",
    "problema": "Problema",
    "valor_original": "Valor original",
}

OBSERVACOES = [
    "A exposição financeira é uma ESTIMATIVA (|divergência| x valor unitário), "
    "não um prejuízo contábil confirmado. O impacto real depende da natureza da "
    "diferença e das regras da empresa.",
    "Quantidades de materiais diferentes não são somadas, pois podem usar unidades "
    "de medida diferentes. Faltas e sobras são contadas em número de itens.",
    "A priorização é uma recomendação baseada apenas nos dados da planilha (não "
    "considera criticidade operacional). A decisão final é do analista.",
    "Linhas com erro de validação ficaram fora dos cálculos, mas não foram apagadas: "
    "continuam na aba Dados originais e os motivos aparecem na aba Problemas.",
    "O arquivo original importado não foi modificado.",
]


def nome_sugerido_relatorio(nome_arquivo_origem: str) -> str:
    """'meu arquivo (1).xlsx' -> 'stock_intelligence_meu_arquivo_1.xlsx'"""
    base = re.sub(r"\.[^.]*$", "", nome_arquivo_origem)  # tira a extensão
    base = re.sub(r"[^\w\-]+", "_", base).strip("_") or "inventario"
    return f"stock_intelligence_{base}.xlsx"


def _neutralizar_formulas(planilha) -> None:
    """Garante que nenhuma célula seja gravada como fórmula.

    O openpyxl transforma qualquer texto que comece com "=" em fórmula. Como os
    textos vêm da planilha importada (que não é confiável), forçamos o tipo
    "texto". Assim, "=1+1" aparece como o próprio texto "=1+1" no Excel.
    """
    for linha in planilha.iter_rows():
        for celula in linha:
            if celula.data_type in ("f", "e"):  # f = fórmula, e = código de erro
                celula.data_type = "s"


def _largura(titulo, serie: pd.Series) -> float:
    tamanhos = [len(str(titulo))] + [len(str(v)) for v in serie.head(200) if v is not None]
    return min(max(max(tamanhos) + 2, 10), LARGURA_MAXIMA)


def _escrever_tabela(planilha, df: pd.DataFrame, formatos: dict = None) -> None:
    """Escreve um DataFrame como tabela formatada.

    `formatos` associa o título de uma coluna a um formato numérico do Excel.
    Os números são gravados como números (não como texto), então o usuário
    pode somar, filtrar e ordenar normalmente.
    """
    formatos = formatos or {}
    planilha.append(list(df.columns))

    dados = df.astype(object).where(df.notna(), None)  # células vazias de verdade
    for linha in dados.itertuples(index=False, name=None):
        planilha.append(list(linha))

    for celula in planilha[1]:
        celula.font = FONTE_CABECALHO
        celula.fill = PREENCHIMENTO_CABECALHO
        celula.alignment = Alignment(vertical="center", wrap_text=True)

    planilha.freeze_panes = "A2"
    planilha.auto_filter.ref = planilha.dimensions

    for indice, coluna in enumerate(df.columns, start=1):
        letra = get_column_letter(indice)
        if coluna in formatos:
            for celula in planilha[letra][1:]:  # [1:] pula o cabeçalho
                celula.number_format = formatos[coluna]
        planilha.column_dimensions[letra].width = _largura(coluna, df[coluna])


def _cabecalhos_priorizacao(criterios) -> dict:
    cabecalhos = {
        "posicao": "Posição",
        "prioridade": "Prioridade",
        "pontuacao": "Pontuação (0 a 100)",
        "codigo_material": "Código",
        "descricao": "Descrição",
        "deposito": "Depósito",
        "tipo_divergencia": "Classificação",
        "estoque_sistema": "Estoque sistema",
        "estoque_fisico": "Estoque físico",
        "divergencia": "Divergência",
        "percentual_divergente": "% do estoque do sistema",
        "impacto_financeiro": "Exposição financeira estimada (R$)",
    }
    for criterio in criterios:
        cabecalhos[f"pontos_{criterio.nome}"] = f"Pontos: {criterio.rotulo}"
    cabecalhos["motivos"] = "Motivos"
    cabecalhos["linha_planilha"] = "Linha na planilha"
    return cabecalhos


def _escrever_resumo(planilha, indicadores, prioridades, criterios,
                     nome_arquivo_origem, gerado_em) -> None:
    def linha(rotulo, valor, formato=None):
        planilha.append([rotulo, valor])
        if formato:
            planilha.cell(row=planilha.max_row, column=2).number_format = formato

    def secao(texto):
        planilha.append([])  # linha em branco
        planilha.append([texto])
        planilha.cell(row=planilha.max_row, column=1).font = FONTE_SECAO

    planilha.append(["Stock Intelligence: relatório de análise de estoque"])
    planilha.cell(row=1, column=1).font = FONTE_TITULO
    linha("Arquivo de origem", nome_arquivo_origem)
    linha("Gerado em", gerado_em.strftime("%d/%m/%Y %H:%M"))

    secao("Indicadores gerais")
    linha("Registros analisados", indicadores["total_analisados"])
    linha("Registros com divergência", indicadores["total_divergentes"])
    linha("Registros sem divergência", indicadores["total_sem_divergencia"])
    linha("Itens com falta", indicadores["itens_com_falta"])
    linha("Itens com sobra", indicadores["itens_com_sobra"])
    linha("% de registros com divergência",
          indicadores["percentual_divergentes"] / 100, FORMATO_PERCENTUAL)
    linha("Exposição financeira estimada (R$)",
          indicadores["exposicao_financeira"], FORMATO_MOEDA)
    linha("Registros com dados inválidos (fora dos cálculos)",
          indicadores["registros_invalidos"])

    secao("Itens divergentes por prioridade (recomendação)")
    contagem = prioridades["prioridade"].value_counts()
    for faixa in (config.PRIORIDADE_ALTA, config.PRIORIDADE_MEDIA, config.PRIORIDADE_BAIXA):
        linha(f"Prioridade {faixa.lower()}", int(contagem.get(faixa, 0)))

    secao("Critérios de priorização e pesos")
    for criterio in criterios:
        linha(criterio.rotulo, criterio.peso, FORMATO_PERCENTUAL)
    linha("Faixa Alta", f"a partir de {config.LIMITE_PRIORIDADE_ALTA} pontos")
    linha("Faixa Média", f"a partir de {config.LIMITE_PRIORIDADE_MEDIA} pontos")

    secao("Observações importantes")
    for texto in OBSERVACOES:
        planilha.append([texto])

    planilha.column_dimensions["A"].width = 52
    planilha.column_dimensions["B"].width = 26
    for celula in planilha["B"]:
        celula.alignment = Alignment(horizontal="left")


def gerar_relatorio_excel(dados_originais, calculado, indicadores, prioridades,
                          problemas, criterios, nome_arquivo_origem,
                          gerado_em: datetime) -> bytes:
    """Monta o relatório e devolve o conteúdo do .xlsx (bytes).

    Nenhum dos DataFrames recebidos é modificado, e nenhum arquivo é gravado
    em disco: quem chama decide o que fazer com os bytes (ex.: botão de download).
    """
    pasta = Workbook()

    resumo = pasta.active
    resumo.title = "Resumo"
    _escrever_resumo(resumo, indicadores, prioridades, criterios,
                     nome_arquivo_origem, gerado_em)

    divergencias = calculado[list(CABECALHOS_DIVERGENCIAS)].rename(
        columns=CABECALHOS_DIVERGENCIAS
    )
    _escrever_tabela(
        pasta.create_sheet("Divergências"), divergencias,
        {"Valor unitário (R$)": FORMATO_MOEDA,
         "Exposição financeira estimada (R$)": FORMATO_MOEDA},
    )

    cabecalhos = _cabecalhos_priorizacao(criterios)
    formatos_prioridade = {
        "Pontuação (0 a 100)": FORMATO_PONTOS,
        "% do estoque do sistema": FORMATO_PERCENTUAL,
        "Exposição financeira estimada (R$)": FORMATO_MOEDA,
    }
    for criterio in criterios:
        formatos_prioridade[f"Pontos: {criterio.rotulo}"] = FORMATO_PONTOS
    _escrever_tabela(pasta.create_sheet("Priorização"),
                     prioridades.rename(columns=cabecalhos), formatos_prioridade)

    if not problemas.empty:
        _escrever_tabela(pasta.create_sheet("Problemas"),
                         problemas.rename(columns=CABECALHOS_PROBLEMAS))

    _escrever_tabela(
        pasta.create_sheet("Dados originais"),
        dados_originais.rename(columns={"linha_planilha": "Linha na planilha"}),
    )

    for planilha in pasta.worksheets:
        _neutralizar_formulas(planilha)

    memoria = io.BytesIO()
    pasta.save(memoria)
    return memoria.getvalue()