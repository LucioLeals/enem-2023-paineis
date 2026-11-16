# ENEM 2023: população, amostra e inferência

Documento de apoio. Tudo o que está aqui também aparece nos painéis, que são o que o avaliador recebe.

## 1. A base de dados (Painel 1)

**Fonte:** Microdados do ENEM 2023, do INEP (Instituto Nacional de Estudos e Pesquisas Educacionais Anísio Teixeira).
É uma base pública e oficial.

**Link:** https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/enem
O arquivo é o `microdados_enem_2023.zip`, com `DADOS/MICRODADOS_ENEM_2023.csv` (1,7 GB, separador `;`, latin-1) e o
dicionário de variáveis.

**Contexto e objetivo:** o ENEM é o exame nacional usado para o acesso ao ensino superior (SiSU, ProUni, Fies).
Os microdados trazem, para cada inscrito, as notas das quatro provas objetivas e da redação, dados pessoais (sexo,
cor/raça, tipo de escola) e o local de prova. O INEP publica a base para pesquisa e avaliação da educação. Aqui ela
é usada para comparar parâmetros da população com estimativas de uma amostra aleatória simples.

**Tamanho:** 3.933.955 observações (inscritos) e 76 variáveis.

**População de interesse:** participantes presentes nas quatro provas objetivas (os dois dias) e com nota maior que
zero em todas elas. São **N = 2.658.763**, ou 67,6% dos inscritos. Ficaram de fora 1.275.192 inscritos que faltaram,
foram eliminados ou tiveram nota zero. Treineiros e egressos fazem parte da população.

**Unidade amostral:** o participante.

**Variáveis selecionadas:**

| Variável | Significado | Tipo |
|---|---|---|
| `NU_NOTA_MT` | Nota de matemática (principal) | quantitativa contínua |
| `NU_NOTA_CN` | Nota de ciências da natureza | quantitativa contínua |
| `NU_NOTA_CH` | Nota de ciências humanas | quantitativa contínua |
| `NU_NOTA_LC` | Nota de linguagens e códigos | quantitativa contínua |
| `NU_NOTA_REDACAO` | Nota da redação (0 a 1000, de 20 em 20) | quantitativa discreta |
| `TP_SEXO` | Sexo (F/M) | qualitativa nominal |
| `TP_ESCOLA` | Tipo de escola do ensino médio: pública/privada | qualitativa nominal |
| `TP_COR_RACA` | Cor/raça autodeclarada | qualitativa nominal |
| `SG_UF_PROVA` | UF onde fez a prova | qualitativa nominal |

**Sobre o `TP_ESCOLA`:** o tipo de escola só é informado por quem **conclui o ensino médio em 2023**
(`TP_ST_CONCLUSAO` = 2). Na população, são 1.044.048 participantes (39,3%). Os demais, egressos e treineiros,
aparecem como "não se aplica": não é falta de resposta. Por isso, as proporções de escola pública são calculadas
entre os concluintes.

**Parâmetros da população (calculados na base inteira):**

| Parâmetro | Valor |
|---|---|
| Média da nota de matemática | 537,37 |
| Mediana da nota de matemática | 525,10 |
| Desvio padrão da nota de matemática | 125,09 |
| Proporção de mulheres | 61,40% |
| Proporção de escola pública (concluintes 2023) | 78,85% |
| Média de matemática dos concluintes 2023 | 533,80 |

## 2. Dimensionamento e seleção da amostra (Painel 2)

| Objetivo | Parâmetros (95%, z = 1,96) | Fórmula | n |
|---|---|---|---|
| Proporção | margem de 2 p.p., p = 50% | n = z²·p·(1−p) / E² | 2.401 |
| Média de matemática | margem de 4 pontos, σ = 125,09 | n = (z·σ / E)² | 3.757 |

**n escolhido = 3.757**, o maior dos dois, para atender aos dois objetivos.

**Justificativa dos parâmetros:**
- **Confiança de 95%:** é o padrão da área.
- **Margens de 2 p.p. e de 4 pontos:** são erros pequenos diante da escala (desvio de 125).
- **p = 50%:** é o valor mais conservador, porque maximiza p·(1−p).
- **σ:** veio da população (Missão 1).
- **Tamanho da população:** com a correção de população finita o n seria 3.752, praticamente igual, então a
  população foi tratada como infinita.

Conferência na calculadora do SurveyMonkey (população 2.658.763, 95%, margem de 2%): ela dá **2.399**, porque
aplica a correção para população finita. Sem a correção, a fórmula dá 2.401. O print está em
`prints/calculadora_surveymonkey.jpeg` e aparece no Painel 2.

**Seleção:** amostra aleatória simples, sem reposição, com `populacao.sample(n=3757, random_state=2026)`
(`amostrar.py`, saída em `dados/amostra.parquet`). Cada participante da população tinha a mesma probabilidade de
seleção: 3.757 em 2.658.763.

## 3. Hipóteses e testes (Painel 3)

Usamos α = 0,05, com testes bilaterais. Todos os intervalos e testes usam só a amostra.

| | Grupo | H0 | H1 | Por que esse valor de H0 |
|---|---|---|---|---|
| **P1** proporção de mulheres | todos (n = 3.757) | p = 50% | p ≠ 50% | igualdade entre os sexos |
| **P2** proporção de escola pública | concluintes 2023 (n = 1.455) | p = 87,2% | p ≠ 87,2% | Censo Escolar 2023: 87,2% das matrículas do ensino médio na rede pública |
| **M1** média de matemática | todos (n = 3.757) | μ = 500 | μ ≠ 500 | 500 é a referência da escala do ENEM |
| **M2** média de matemática | concluintes 2023 (n = 1.455) | μ = 500 | μ ≠ 500 | 500 é a média dos concluintes regulares de 2009 |

**Fontes das referências:**
- **P2:** INEP, Resumo Técnico do Censo Escolar da Educação Básica 2023, gráfico 19 (p. 35). As matrículas do
  ensino médio em 2023 estavam 83,6% na rede estadual, 3,1% na federal, 0,5% na municipal e 12,9% na privada.
- **M1 e M2:** INEP, "Entenda a sua nota no Enem: guia do participante", na pasta de documentos dos microdados. O
  valor 500 representa o desempenho médio dos concluintes regulares do ensino médio de 2009.

**Bibliotecas:**
- **Proporção:** `statsmodels.stats.proportion.proportions_ztest(k, n, value=p0, prop_var=p0)`.
- **Média:** `scipy.stats.ttest_1samp`.
- **Intervalos:** p̂ ± 1,96·√(p̂(1−p̂)/n) e x̄ ± 1,96·s/√n.

**Condições:**
- A amostra aleatória simples garante a independência, e a amostra é muito menor que 10% da população.
- Proporção: n·p₀ e n·(1−p₀) são ≥ 10, e há mais de 10 sucessos e 10 fracassos.
- Média: n é muito maior que 30.

**Resultados:**

| | Parâmetro (pop.) | Estimativa | IC de 95% | Contém? | Estatística | Valor-p | Decisão |
|---|---|---|---|---|---|---|---|
| P1 | 61,4% | 62,3% | [60,8% ; 63,9%] | sim | z = 15,09 | < 0,0001 | rejeita H0 |
| P2 | 78,9% | 80,8% | [78,7% ; 82,8%] | sim | z = −7,36 | < 0,0001 | rejeita H0 |
| M1 | 537,37 | 533,56 | [529,64 ; 537,48] | sim | t = 16,78 | < 0,0001 | rejeita H0 |
| M2 | 533,80 | 529,21 | [523,05 ; 535,36] | sim | t = 9,30 | < 0,0001 | rejeita H0 |

**Leitura dos resultados:**
- As mulheres são maioria entre os participantes.
- A proporção de alunos de escola pública entre os concluintes participantes (cerca de 80%) é menor que a sua fatia
  nas matrículas (87,2%).
- A média de matemática, tanto geral quanto dos concluintes, está acima de 500.
- Os quatro intervalos contêm o parâmetro verdadeiro.
- Numa simulação com 100 amostras, 97 intervalos contiveram a média verdadeira.

**Limitações:**
- **Variabilidade amostral:** cerca de 5% dos intervalos não contêm o parâmetro.
- **Vários testes:** com 4 testes, a chance de pelo menos um falso positivo seria de cerca de 18,5% se todas as H0
  fossem verdadeiras. Aqui os valores-p são muito menores que 0,0001.
- **Significância não é tamanho:** o tamanho de uma diferença se lê no intervalo, não no valor-p.
- **População restrita:** só os presentes nas quatro provas.
- **Referências aproximadas:** o Censo conta todas as matrículas do ensino médio, não só os concluintes, e o 500 vem
  de 2009.
- **Dados autodeclarados:** sexo, cor/raça e tipo de escola são informados pelo próprio participante.

## Como reproduzir

```
python preparar_base.py   # lê o CSV, define a população, grava dados/populacao.parquet e os parâmetros
python amostrar.py        # calcula o n, sorteia a amostra e grava dados/amostra.parquet
streamlit run app.py      # abre os três painéis
```
