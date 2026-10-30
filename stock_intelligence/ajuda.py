"""Texto da seção "Como interpretar os indicadores" (etapa 5).

Os pesos, as faixas e as descrições dos critérios vêm do próprio código
(config.py e prioritization.py), então o texto nunca fica desatualizado
se você ajustar esses valores.
"""
from stock_intelligence import config
from stock_intelligence.formatting import formatar_percentual
from stock_intelligence.prioritization import CRITERIOS_PADRAO


def texto_como_interpretar() -> str:
    criterios = "\n".join(
        f"- **{c.rotulo}** (peso {formatar_percentual(c.peso * 100)}): {c.descricao}"
        for c in CRITERIOS_PADRAO
    )
    return f"""
### Como ler este painel

O sistema compara, para cada material em cada depósito, o **estoque do sistema** (o que está
registrado) com o **estoque físico** (o que foi contado). Cada combinação
*código + depósito* é um registro.

### Divergência

- **Divergência = estoque físico − estoque do sistema.**
- Negativa: **falta** (há menos material do que o sistema indica).
- Positiva: **sobra** (há mais material do que o sistema indica).
- Zero: **sem divergência**.

### Indicadores

- **Registros analisados:** linhas válidas usadas nos cálculos.
- **Com divergência / Sem divergência:** quantos registros têm ou não diferença.
- **Itens com falta / Itens com sobra:** número de **itens**, e não de unidades. Materiais
  diferentes podem usar unidades diferentes (peças, metros, litros), então somar quantidades
  de materiais distintos não faz sentido.
- **% com divergência:** registros com divergência ÷ registros analisados.
- **Registros com dados inválidos:** linhas que ficaram fora dos cálculos por erro (veja
  "Dados com problema"). Este número não muda com os filtros.
- **Exposição financeira estimada:** soma de |divergência| × valor unitário. É uma
  **estimativa** do valor envolvido nas diferenças, **não é um prejuízo contábil
  confirmado**. Uma falta pode ser um lançamento atrasado, e uma sobra pode compensar a falta
  de outro item. O efeito contábil real depende da natureza da diferença e das regras da
  empresa.

### Dados com problema

- **Erro:** a linha não pode ser calculada (valor não numérico, negativo ou campo obrigatório
  vazio). Ela fica fora dos cálculos, mas **nunca é apagada**: aparece na lista de problemas e
  no relatório.
- **Aviso:** a linha é calculada, mas há algo suspeito, como o mesmo código no mesmo depósito
  em mais de uma linha. O mesmo código em depósitos diferentes é normal e não gera aviso.

### Priorização das investigações

A aba Priorização sugere **por onde começar**. Cada divergência recebe de 0 a 100 pontos em
cada critério, e a pontuação final é a média ponderada deles:

{criterios}

Faixas: **Alta** a partir de {config.LIMITE_PRIORIDADE_ALTA} pontos, **Média** a partir de
{config.LIMITE_PRIORIDADE_MEDIA} pontos e **Baixa** abaixo disso.

Cuidados ao interpretar:

- É uma **recomendação baseada apenas nos dados da planilha**, não uma decisão definitiva.
  Ainda não considera a criticidade operacional dos materiais.
- A pontuação é **relativa ao conjunto importado**: ela compara os itens entre si.
- Pesos, limites e pontos por tipo são pontos de partida e podem ser ajustados em
  `stock_intelligence/config.py`.
- Para cada item, o campo **Motivos** mostra a conta feita, que pode ser conferida à mão.

### Privacidade

Tudo roda no seu computador: nenhum dado é enviado para serviços externos, e o arquivo
importado nunca é modificado.
"""