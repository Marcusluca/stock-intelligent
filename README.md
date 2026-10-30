
Sistema inteligente de análise de estoque desenvolvido com Python.
# 📦 Stock Intelligence

Sistema Inteligente de Análise de Estoque: importa uma planilha de inventário, calcula as divergências entre o estoque físico e o estoque do sistema e ajuda o analista a decidir **o que investigar primeiro**.

Projeto de portfólio em **Python**, **Pandas** e **Streamlit**, feito por [Marcus Luca de sousa].

> Os dados de exemplo deste repositório são **fictícios**. Não publique planilhas reais de empresas.

<!-- Adicione capturas de tela da aplicação em docs/ e referencie aqui:
![Dashboard](docs/dashboard.png) -->

## O que o sistema faz

- **Importa** planilhas `.xlsx` ou `.csv` (fórmulas e macros nunca são executadas).
- **Valida** os dados e explica os problemas em linguagem simples, sem apagar nenhuma linha.
- **Calcula** divergências (falta, sobra, sem divergência), quantidade divergente e exposição financeira estimada.
- **Mostra** indicadores, gráficos, rankings, tabela com filtros, pesquisa e ordenação.
- **Prioriza** as investigações com uma pontuação explicável e determinística (sem IA generativa).
- **Exporta** um relatório Excel completo, sem modificar o arquivo original.
- **Ensina** a interpretar cada indicador (aba "Como interpretar").
- Inclui **dados demonstrativos fictícios** para testar sem nenhuma planilha.

## Como funciona a priorização

Cada divergência recebe de 0 a 100 pontos em quatro critérios, combinados por uma média ponderada:

| Critério | Peso | Ideia |
|---|---|---|
| Impacto financeiro | 35% | Posição no ranking de exposição estimada |
| Proporção da divergência | 30% | Divergência ÷ estoque do sistema (comparável entre unidades diferentes) |
| Tipo de divergência | 20% | Falta pontua mais que sobra |
| Depósito | 15% | Concentração de divergências no depósito |

Cada item mostra os pontos por critério e o motivo em texto, então a conta pode ser conferida à mão. A classificação é uma **recomendação** baseada nos dados disponíveis, não uma decisão definitiva. Novos critérios (criticidade, histórico, curva ABC) entram como novas peças na lista de critérios, sem mexer no resto.

## Decisões de projeto

- **Lógica separada da interface:** tudo o que calcula fica em `stock_intelligence/` (sem Streamlit) e é coberto por testes.
- **Registro = código + depósito:** o mesmo material pode existir em depósitos diferentes sem ser duplicidade.
- **Exposição financeira ≠ prejuízo:** o valor é sempre apresentado como estimativa.
- **Sem soma de quantidades de materiais diferentes:** as unidades de medida podem diferir, então faltas e sobras são contadas em número de itens.
- **Segurança da saída:** textos da planilha importada são gravados no relatório como texto, nunca como fórmula.
- **Privacidade:** tudo roda localmente, sem chaves de API nem serviços externos.

## Como executar (Windows, VS Code)

```powershell
git clone <url-do-repositorio>
cd stock-intelligence
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Abra `http://localhost:8501`, envie uma planilha ou clique em **Carregar dados demonstrativos**.

### Formato da planilha

| codigo_material | descricao | deposito | estoque_sistema | estoque_fisico | valor_unitario |
|---|---|---|---|---|---|
| MAT001 | Parafuso industrial | A | 100 | 90 | 2.50 |

Exemplos prontos em `data/sample/`.

### Testes

```powershell
python -m pytest -v
```

## Estrutura

```
stock-intelligence/
├── app.py                        # Interface (Streamlit)
├── stock_intelligence/
│   ├── config.py                 # Colunas, pesos, faixas e constantes
│   ├── loaders.py                # Leitura segura de .xlsx/.csv
│   ├── validation.py             # Validação e relatório de problemas
│   ├── calculations.py           # Divergências e indicadores
│   ├── analysis.py               # Filtros, ordenação e rankings
│   ├── prioritization.py         # Pontuação explicável dos critérios
│   ├── reports.py                # Exportação para Excel
│   ├── charts.py                 # Gráficos Plotly
│   ├── formatting.py             # Formato brasileiro (R$ 1.234,56)
│   ├── demo_data.py              # Dados fictícios de demonstração
│   └── ajuda.py                  # Texto de "Como interpretar"
├── tests/                        # Testes automatizados (Pytest)
├── data/sample/                  # Planilhas de exemplo
├── requirements.txt
└── pytest.ini
```

## Limitações e próximos passos

- A priorização ainda não considera **criticidade operacional**, **histórico de divergências**, **frequência de erros** nem **curva ABC**. A arquitetura já prevê esses critérios.
- Os dados vêm de arquivos. A arquitetura permite trocar o carregamento por um **banco de dados** no futuro.
- Pesos e limites da priorização são pontos de partida, ajustáveis em `config.py`.
