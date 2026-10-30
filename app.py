"""Stock Intelligence: aplicação Streamlit.

Abas: Dashboard, Priorização, Exportar e Como interpretar.
A lógica fica em `stock_intelligence/`; este arquivo só monta a interface.
"""
from datetime import datetime

import streamlit as st

from stock_intelligence import config
from stock_intelligence.ajuda import texto_como_interpretar
from stock_intelligence.analysis import (
    OPCOES_ORDENACAO,
    divergencias_por_deposito,
    filtrar,
    ordenar,
    ranking_depositos,
    ranking_materiais,
)
from stock_intelligence.calculations import calcular_divergencias, calcular_indicadores
from stock_intelligence.charts import (
    grafico_divergencias_por_deposito,
    grafico_faltas_sobras,
    grafico_ranking,
)
from stock_intelligence.demo_data import AVISO_DEMO, NOME_ARQUIVO_DEMO, carregar_dados_demo
from stock_intelligence.formatting import (
    formatar_decimal,
    formatar_inteiro,
    formatar_moeda,
    formatar_percentual,
    formatar_quantidade,
)
from stock_intelligence.loaders import ArquivoInvalidoError, carregar_arquivo
from stock_intelligence.prioritization import CRITERIOS_PADRAO, listar_motivos, priorizar
from stock_intelligence.reports import gerar_relatorio_excel, nome_sugerido_relatorio
from stock_intelligence.validation import validar

# ---------- Tabela do dashboard ----------
NOMES_COLUNAS = {
    "codigo_material": "Código",
    "descricao": "Descrição",
    "deposito": "Depósito",
    "estoque_sistema": "Estoque sistema",
    "estoque_fisico": "Estoque físico",
    "divergencia": "Divergência",
    "tipo_divergencia": "Tipo",
    "quantidade_divergente": "Qtd. divergente",
    "valor_unitario": "Valor unitário",
    "impacto_financeiro": "Exposição estimada",
    "linha_planilha": "Linha na planilha",
}

# Os números continuam numéricos por baixo, então a ordenação pelo cabeçalho funciona
FORMATOS = {
    "estoque_sistema": formatar_quantidade,
    "estoque_fisico": formatar_quantidade,
    "divergencia": formatar_quantidade,
    "quantidade_divergente": formatar_quantidade,
    "valor_unitario": formatar_moeda,
    "impacto_financeiro": formatar_moeda,
}

# ---------- Tabela de priorização ----------
COLUNAS_PONTOS = {f"pontos_{c.nome}": f"Pts: {c.rotulo}" for c in CRITERIOS_PADRAO}

NOMES_PRIORIDADE = {
    "posicao": "Posição",
    "prioridade": "Prioridade",
    "pontuacao": "Pontuação",
    "codigo_material": "Código",
    "descricao": "Descrição",
    "deposito": "Depósito",
    "tipo_divergencia": "Tipo",
    "percentual_divergente": "% do estoque",
    "impacto_financeiro": "Exposição estimada",
    **COLUNAS_PONTOS,
    "motivos": "Motivos",
}

FORMATOS_PRIORIDADE = {
    "pontuacao": formatar_decimal,
    "percentual_divergente": lambda v: formatar_percentual(v * 100),
    "impacto_financeiro": formatar_moeda,
    **{coluna: formatar_decimal for coluna in COLUNAS_PONTOS},
}

EMOJI_PRIORIDADE = {
    config.PRIORIDADE_ALTA: "🔴 Alta",
    config.PRIORIDADE_MEDIA: "🟠 Média",
    config.PRIORIDADE_BAIXA: "🟢 Baixa",
}

st.set_page_config(page_title="Stock Intelligence", page_icon="📦", layout="wide")
st.title("📦 Stock Intelligence")
st.caption("Sistema Inteligente de Análise de Estoque")

arquivo = st.file_uploader("Importe sua planilha de inventário", type=["xlsx", "csv"])

# 1) Origem dos dados: arquivo enviado OU dados demonstrativos fictícios.
# O Streamlit executa este script inteiro a cada clique. Por isso o modo
# demonstração é guardado em st.session_state, que sobrevive entre execuções.
if arquivo is not None:
    try:
        bruto = carregar_arquivo(arquivo)
    except ArquivoInvalidoError as erro:
        st.error(str(erro))
        st.stop()
    nome_origem = arquivo.name
    chave = f"{arquivo.name}_{arquivo.size}"  # muda quando o arquivo muda
elif st.session_state.get("usar_demo"):
    bruto = carregar_dados_demo()
    nome_origem = NOME_ARQUIVO_DEMO
    chave = "demo"
    st.warning(AVISO_DEMO)
    if st.button("Sair da demonstração"):
        st.session_state["usar_demo"] = False
        st.rerun()
else:
    st.info(
        "Envie um arquivo .xlsx ou .csv com as colunas: codigo_material, descricao, "
        "deposito, estoque_sistema, estoque_fisico, valor_unitario. "
        "Ou veja o sistema funcionando com dados fictícios:"
    )
    if st.button("🧪 Carregar dados demonstrativos (fictícios)"):
        st.session_state["usar_demo"] = True
        st.rerun()
    st.stop()

# 2) Validação
resultado = validar(bruto)
if resultado.colunas_ausentes:
    st.error("A planilha não tem as colunas obrigatórias: "
             + ", ".join(resultado.colunas_ausentes))
    st.stop()

problemas = resultado.problemas
if not problemas.empty:
    qtd_erros = int((problemas["gravidade"] == config.GRAVIDADE_ERRO).sum())
    qtd_avisos = int((problemas["gravidade"] == config.GRAVIDADE_AVISO).sum())
    st.warning(
        f"Foram encontrados {qtd_erros} erro(s) e {qtd_avisos} aviso(s). "
        "Linhas com erro NÃO entram nos cálculos, mas nenhuma foi apagada."
    )
    with st.expander("Ver problemas encontrados"):
        st.dataframe(problemas, hide_index=True)
    if resultado.quantidade_invalidos:
        with st.expander("Ver linhas que ficaram fora dos cálculos"):
            st.dataframe(resultado.dados_invalidos, hide_index=True)
else:
    st.success("Nenhum problema encontrado na validação.")

if resultado.dados_validos.empty:
    st.warning("Não há linhas válidas para calcular. Corrija a planilha e envie novamente.")
    st.stop()

# 3) Cálculos
calculado = calcular_divergencias(resultado.dados_validos)

# A priorização usa TODOS os registros válidos. Assim a nota de um item não muda
# quando o usuário mexe nos filtros; os filtros só escolhem o que é exibido.
prioridades = priorizar(calculado)

# 4) Filtros (barra lateral)
depositos = sorted(calculado["deposito"].unique())
tipos = [config.TIPO_FALTA, config.TIPO_SOBRA, config.TIPO_SEM_DIVERGENCIA]

st.sidebar.header("Filtros")
depositos_sel = st.sidebar.multiselect("Depósito", depositos, default=depositos,
                                       key=f"dep_{chave}")
tipos_sel = st.sidebar.multiselect("Tipo de divergência", tipos, default=tipos,
                                   key=f"tipo_{chave}")
busca = st.sidebar.text_input("Buscar por código ou descrição", key=f"busca_{chave}")

st.sidebar.header("Ordenação da tabela de resultados")
ordenar_por = st.sidebar.selectbox("Ordenar por", list(OPCOES_ORDENACAO))
sentido = st.sidebar.radio("Ordem", ["Decrescente", "Crescente"])

filtrado = filtrar(calculado, depositos_sel, tipos_sel, busca)
if filtrado.empty:
    st.info("Nenhum registro corresponde aos filtros selecionados.")
    st.stop()

ind = calcular_indicadores(filtrado, resultado.quantidade_invalidos)
st.caption(
    f"Exibindo {formatar_inteiro(len(filtrado))} de {formatar_inteiro(len(calculado))} "
    "registros válidos. Os filtros valem para as abas Dashboard e Priorização."
)

aba_dashboard, aba_priorizacao, aba_exportar, aba_ajuda = st.tabs(
    ["📊 Dashboard", "🎯 Priorização", "📥 Exportar", "📖 Como interpretar"]
)

# ======================= ABA 1: DASHBOARD =======================
with aba_dashboard:
    st.subheader("Visão geral")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Registros analisados", formatar_inteiro(ind["total_analisados"]))
    c2.metric("Com divergência", formatar_inteiro(ind["total_divergentes"]))
    c3.metric("Itens com falta", formatar_inteiro(ind["itens_com_falta"]),
              help="Estoque físico menor que o do sistema.")
    c4.metric("Itens com sobra", formatar_inteiro(ind["itens_com_sobra"]),
              help="Estoque físico maior que o do sistema.")

    c5, c6, c7, c8 = st.columns(4)
    c5.metric("Sem divergência", formatar_inteiro(ind["total_sem_divergencia"]))
    c6.metric("% com divergência", formatar_percentual(ind["percentual_divergentes"]))
    c7.metric("Exposição financeira estimada", formatar_moeda(ind["exposicao_financeira"]),
              help="Soma de |divergência| x valor unitário. É uma estimativa de "
                   "exposição, NÃO um prejuízo contábil confirmado.")
    c8.metric("Registros com dados inválidos", formatar_inteiro(ind["registros_invalidos"]),
              help="Linhas da planilha que ficaram fora dos cálculos. Não depende dos filtros.")

    st.subheader("Faltas, sobras e depósitos")
    col_a, col_b = st.columns(2)
    with col_a:
        st.plotly_chart(grafico_faltas_sobras(ind["itens_com_falta"], ind["itens_com_sobra"]))
    with col_b:
        por_deposito = divergencias_por_deposito(filtrado)
        if por_deposito.empty:
            st.info("Não há divergências nos dados filtrados.")
        else:
            st.plotly_chart(grafico_divergencias_por_deposito(por_deposito))

    st.subheader("Rankings por exposição financeira estimada")
    col_c, col_d = st.columns(2)
    with col_c:
        rank_mat = ranking_materiais(filtrado, n=10)
        if rank_mat.empty:
            st.info("Não há divergências nos dados filtrados.")
        else:
            rotulos = (rank_mat["codigo_material"] + " (" + rank_mat["deposito"] + ")").tolist()
            detalhes = (rank_mat["descricao"] + " · " + rank_mat["tipo_divergencia"]).tolist()
            st.plotly_chart(grafico_ranking(
                rotulos, rank_mat["impacto_financeiro"].tolist(), "Top 10 materiais", detalhes,
            ))
    with col_d:
        rank_dep = ranking_depositos(filtrado)
        detalhes_dep = [
            f"{formatar_inteiro(int(div))} de {formatar_inteiro(int(tot))} itens com divergência"
            for div, tot in zip(rank_dep["itens_divergentes"], rank_dep["itens_analisados"])
        ]
        st.plotly_chart(grafico_ranking(
            rank_dep["deposito"].astype(str).tolist(),
            rank_dep["impacto_financeiro"].tolist(),
            "Depósitos", detalhes_dep,
        ))
    st.caption(
        "Estes rankings consideram apenas o impacto financeiro estimado. Para decidir "
        "o que investigar primeiro, veja a aba Priorização, que combina outros critérios."
    )

    st.subheader("Resultado por material")
    ordenado = ordenar(filtrado, OPCOES_ORDENACAO[ordenar_por],
                       crescente=(sentido == "Crescente"))
    tabela = ordenado[list(NOMES_COLUNAS)].rename(columns=NOMES_COLUNAS)
    formatos = {NOMES_COLUNAS[coluna]: funcao for coluna, funcao in FORMATOS.items()}
    st.dataframe(tabela.style.format(formatos), hide_index=True)
    st.caption(
        "A exposição financeira é uma estimativa baseada nos dados importados. "
        "O impacto contábil real depende da natureza da diferença e das regras da empresa."
    )

# ======================= ABA 2: PRIORIZAÇÃO =======================
with aba_priorizacao:
    st.subheader("Priorização das investigações")
    st.info(
        "**Recomendação inicial, não decisão definitiva.** A classificação usa apenas os "
        "dados da planilha (impacto financeiro, proporção da divergência, tipo e depósito). "
        "Ela ainda não considera a criticidade operacional dos materiais: uma divergência "
        "pequena em um material crítico pode merecer atenção mesmo com nota baixa. "
        "A decisão final é do analista."
    )

    with st.expander("Como a pontuação é calculada"):
        st.markdown(
            "Cada divergência recebe de 0 a 100 pontos em cada critério. A **pontuação final** "
            "é a média desses pontos, ponderada pelos pesos abaixo. A pontuação é relativa ao "
            "conjunto de dados importado."
        )
        for criterio in CRITERIOS_PADRAO:
            st.markdown(
                f"- **{criterio.rotulo}** (peso {formatar_percentual(criterio.peso * 100)}): "
                f"{criterio.descricao}"
            )
        st.markdown(
            f"**Faixas:** Alta a partir de {config.LIMITE_PRIORIDADE_ALTA} pontos, "
            f"Média a partir de {config.LIMITE_PRIORIDADE_MEDIA} e Baixa abaixo disso. "
            "Pesos, limites e pontos por tipo são pontos de partida e podem ser ajustados "
            "em `stock_intelligence/config.py`."
        )

    lista = filtrar(prioridades, depositos_sel, tipos_sel, busca)
    if lista.empty:
        st.info("Nenhuma divergência corresponde aos filtros selecionados.")
    else:
        st.caption("A pontuação é calculada com todos os registros válidos. Os filtros "
                   "apenas escolhem o que aparece aqui.")

        m1, m2, m3 = st.columns(3)
        for coluna, faixa in zip((m1, m2, m3), (config.PRIORIDADE_ALTA,
                                                config.PRIORIDADE_MEDIA,
                                                config.PRIORIDADE_BAIXA)):
            coluna.metric(f"Prioridade {faixa.lower()}",
                          formatar_inteiro(int((lista["prioridade"] == faixa).sum())))

        tabela_prior = lista[list(NOMES_PRIORIDADE)].rename(columns=NOMES_PRIORIDADE)
        tabela_prior["Prioridade"] = tabela_prior["Prioridade"].map(EMOJI_PRIORIDADE)
        formatos_prior = {NOMES_PRIORIDADE[c]: f for c, f in FORMATOS_PRIORIDADE.items()}
        st.dataframe(
            tabela_prior.style.format(formatos_prior),
            hide_index=True,
            column_config={"Motivos": st.column_config.TextColumn(width="large")},
        )

        st.markdown("##### Por que este item foi priorizado?")
        opcoes = [
            f"{int(linha['posicao'])}º · {linha['codigo_material']} ({linha['deposito']}) "
            f"· {linha['descricao']}"
            for _, linha in lista.iterrows()
        ]
        escolha = st.selectbox("Escolha um item", opcoes)
        item = lista.iloc[opcoes.index(escolha)]
        st.markdown(
            f"**Prioridade {item['prioridade']}** · pontuação "
            f"{formatar_decimal(item['pontuacao'])} de 100"
        )
        for motivo in listar_motivos(item["motivos"]):
            st.markdown(f"- {motivo}")

# ======================= ABA 3: EXPORTAR =======================
with aba_exportar:
    st.subheader("Exportar relatório em Excel")
    st.write(
        "O relatório reúne em um único arquivo .xlsx: resumo dos indicadores, divergências "
        "calculadas (com classificação e exposição financeira estimada), ranking de "
        "priorização com os motivos, problemas de validação (se houver) e os dados "
        "originais como foram importados."
    )
    st.info(
        "O relatório sempre inclui **todos** os registros válidos, independentemente dos "
        "filtros da tela. O arquivo que você importou não é alterado."
    )

    indicadores_gerais = calcular_indicadores(calculado, resultado.quantidade_invalidos)
    relatorio = gerar_relatorio_excel(
        dados_originais=bruto,
        calculado=calculado,
        indicadores=indicadores_gerais,
        prioridades=prioridades,
        problemas=problemas,
        criterios=CRITERIOS_PADRAO,
        nome_arquivo_origem=nome_origem,
        gerado_em=datetime.now(),
    )
    st.download_button(
        "📥 Baixar relatório em Excel",
        data=relatorio,
        file_name=nome_sugerido_relatorio(nome_origem),
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

# ======================= ABA 4: COMO INTERPRETAR =======================
with aba_ajuda:
    st.subheader("Como interpretar os indicadores")
    st.markdown(texto_como_interpretar())