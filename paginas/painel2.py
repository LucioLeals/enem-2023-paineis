import json

import pandas as pd
import streamlit as st

from comum import (DADOS, LARANJA, QUALITATIVAS, carregar, cartoes, comparar_categorias, comparar_distribuicao,
                   escolher_nota, fmt_int, fmt_num, graficos, resumir, tabela_comparacao, tabelas)

info = json.loads((DADOS / "amostra_info.json").read_text())
pop = resumir("populacao", carregar("populacao"))
amo = resumir(f"amostra-{info['n']}-{info['semente']}", carregar("amostra"))

st.title("Painel 2: análise descritiva da amostra")
st.write(f"Mesma análise do Painel 1, feita **só com a amostra aleatória simples** de n = {fmt_int(info['n'])} "
         "participantes (em laranja). Nos cartões, a diferença para a população mostra a **variabilidade amostral**.")

st.header("Dimensionamento e seleção da amostra")
st.markdown("**Tamanho da amostra**, com 95% de confiança (z = 1,96):")
st.dataframe(pd.DataFrame([
    ("Proporção (ex.: mulheres)", "margem E = 2 pontos percentuais, p = 50%", "n = z²·p·(1−p) / E²",
     fmt_int(info["n_proporcao"])),
    ("Média da nota de matemática", f"margem E = 4 pontos, σ = {fmt_num(info['sigma'], 2)}", "n = (z·σ / E)²",
     fmt_int(info["n_media"])),
], columns=["Objetivo", "Parâmetros", "Fórmula", "n necessário"]), hide_index=True, width="stretch")
st.markdown(
    f"**n escolhido = {fmt_int(info['n'])}**, o maior dos dois, para atender aos dois objetivos ao mesmo tempo.\n\n"
    "**Justificativa dos parâmetros:**\n"
    "- **Confiança de 95%:** padrão da área; aceita-se que 5% dos intervalos construídos assim não contenham o "
    "parâmetro.\n"
    "- **Margem de 2 p.p. na proporção e de 4 pontos na média:** erros pequenos diante da escala (notas de 0 a 1000 "
    f"com desvio de {fmt_num(info['sigma'], 0)}), o que torna as estimativas úteis.\n"
    "- **p = 50%:** é o valor que maximiza p·(1−p), logo o mais conservador (maior n) quando não se conhece a "
    "proporção de antemão.\n"
    f"- **σ = {fmt_num(info['sigma'], 2)}:** desvio padrão da nota de matemática na população (Painel 1).\n"
    f"- **Tamanho da população:** com N = {fmt_int(info['N'])}, a correção para população finita muda o n para "
    f"{fmt_int(info['n_finita'])}, praticamente o mesmo; por isso a população foi tratada como infinita.")
with st.expander("Conferência na calculadora de tamanho amostral (proporção)", expanded=True):
    c1, c2 = st.columns([3, 2])
    c1.image(str(DADOS.parent / "prints" / "calculadora_surveymonkey.jpeg"), width="stretch")
    c2.markdown(
        f"Calculadora do SurveyMonkey, com população de {fmt_int(info['N'])}, confiança de 95% e margem de erro de "
        "2%: **2.399** (o site escreve 2,399, no padrão americano). Ela já aplica a correção para população finita "
        f"e considera p = 50%. Sem a correção, a fórmula dá {fmt_int(info['n_proporcao'])}: só 2 pessoas de "
        "diferença.  \n\n"
        "A calculadora trata apenas de proporções. O n da média vem da fórmula n = (z·σ / E)² da tabela acima.")
st.markdown(
    "**Seleção:** amostra aleatória simples, sem reposição, sorteada por computador entre os "
    f"{fmt_int(info['N'])} participantes da população, com semente fixa ({info['semente']}) para que o sorteio "
    "possa ser reproduzido. **Cada participante da população tinha a mesma probabilidade de ser selecionado** "
    f"({fmt_int(info['n'])} em {fmt_int(info['N'])}, ou {fmt_num(info['n'] / info['N'] * 100, 2)}%).")
st.code(f'amostra = populacao.sample(n={info["n"]}, random_state={info["semente"]})  # pandas', language="python")

st.header("Indicadores da amostra")
cartoes(amo, ref=pop["params"])

st.header("Distribuições na amostra")
nota = escolher_nota("nota_p2")
graficos(amo, LARANJA, nota)

st.header("Amostra × população")
st.write("Os gráficos abaixo põem a amostra ao lado da população para mostrar onde elas se parecem e onde diferem. "
         "Diferenças pequenas e sem padrão são o esperado de uma amostra aleatória.")
comparar_distribuicao(pop, amo, nota)
var = st.selectbox("Variável qualitativa", QUALITATIVAS, key="qual_p2")
comparar_categorias(pop, amo, var)
st.subheader("Medidas descritivas: população × amostra")
tabela_comparacao(pop, amo)

tabelas(amo)
