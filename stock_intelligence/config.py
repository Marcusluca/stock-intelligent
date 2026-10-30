"""Configurações centrais do sistema: nomes de colunas e constantes."""

# Colunas que a planilha importada precisa ter
COLUNAS_OBRIGATORIAS = [
    "codigo_material",
    "descricao",
    "deposito",
    "estoque_sistema",
    "estoque_fisico",
    "valor_unitario",
]

# Colunas que devem conter números
COLUNAS_NUMERICAS = ["estoque_sistema", "estoque_fisico", "valor_unitario"]

# O que identifica um registro de forma única.
# O mesmo material pode existir em depósitos diferentes, então
# a chave é a COMBINAÇÃO código + depósito.
COLUNAS_CHAVE = ["codigo_material", "deposito"]

# Colunas da tabela de problemas encontrados na validação
COLUNAS_PROBLEMAS = ["linha", "coluna", "gravidade", "problema", "valor_original"]

# Gravidade dos problemas
GRAVIDADE_ERRO = "erro"    # impede o cálculo da linha
GRAVIDADE_AVISO = "aviso"  # a linha é calculada, mas merece atenção

# Classificação das divergências
TIPO_FALTA = "Falta"
TIPO_SOBRA = "Sobra"
TIPO_SEM_DIVERGENCIA = "Sem divergência"

# Evita que erros de arredondamento do computador (ex.: 0.1 + 0.2)
# criem divergências falsas
CASAS_DECIMAIS_QUANTIDADE = 6

# --- Priorização das investigações (etapa 3) ---
# Os valores abaixo são PONTOS DE PARTIDA ajustáveis, não verdades absolutas.

# Importância relativa de cada critério (a soma não precisa dar 1: o sistema
# divide pela soma dos pesos dos critérios que estão ativos)
PESOS_CRITERIOS = {
    "impacto": 0.35,
    "percentual": 0.30,
    "tipo": 0.20,
    "deposito": 0.15,
}

# Divergência (em fração do estoque do sistema) a partir da qual o critério
# "proporção" já vale a nota máxima. 0.25 = 25%.
PERCENTUAL_REFERENCIA = 0.25

# Pontos por tipo. Suposição inicial: a falta é mais urgente, porque o sistema
# indica material que pode não existir.
PONTOS_POR_TIPO = {TIPO_FALTA: 100, TIPO_SOBRA: 60}

# Faixas de prioridade (sobre a pontuação final, de 0 a 100)
PRIORIDADE_ALTA = "Alta"
PRIORIDADE_MEDIA = "Média"
PRIORIDADE_BAIXA = "Baixa"
LIMITE_PRIORIDADE_ALTA = 65
LIMITE_PRIORIDADE_MEDIA = 40