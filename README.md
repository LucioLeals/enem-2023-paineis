# ENEM 2023: população, amostra e inferência

Painéis interativos (Streamlit) que comparam a população de participantes do ENEM 2023 com uma amostra
aleatória simples, com intervalos de confiança e testes de hipóteses para proporções e médias.

- **Painel 1:** análise descritiva da população.
- **Painel 2:** análise descritiva da amostra e comparação com a população.
- **Painel 3:** inferência estatística (4 testes) e comparação dos resultados.

**Fonte dos dados:** Microdados do ENEM 2023, INEP.
https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/enem

## Rodar localmente

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Reproduzir os dados

1. Baixe `microdados_enem_2023.zip` no link acima e extraia em `dados_brutos/`.
2. `python preparar_base.py` lê o CSV, define a população e grava `dados/populacao.parquet`.
3. `python amostrar.py` calcula o tamanho da amostra e sorteia a amostra (semente 2026).

A descrição completa da base, do dimensionamento e das hipóteses está em `descricao_base.md`.
