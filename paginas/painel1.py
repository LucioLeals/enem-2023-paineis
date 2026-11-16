import json

import pandas as pd
import streamlit as st

from comum import AZUL, DADOS, QUALITATIVAS, carregar, cartoes, escolher_nota, fmt_int, graficos, resumir, tabelas

par = json.loads((DADOS / "parametros.json").read_text())
r = resumir("populacao", carregar("populacao"))

st.title("Painel 1: análise descritiva da população")
st.write("Microdados do ENEM 2023. Como temos a base inteira, os números desta página são os **parâmetros "
         "verdadeiros** da população (em azul). Os Painéis 2 e 3 tentam estimá-los com uma amostra.")

st.header("A base de dados")
c1, c2 = st.columns([3, 2])
with c1:
    st.markdown(
        "**Fonte:** Microdados do ENEM 2023, INEP (Instituto Nacional de Estudos e Pesquisas Educacionais Anísio "
        "Teixeira), base pública e oficial.  \n"
        "**Link:** [gov.br/inep → dados abertos → microdados → ENEM]"
        "(https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/enem)  \n"
        "**Contexto e objetivo:** o ENEM é o exame nacional usado para o acesso ao ensino superior (SiSU, ProUni, "
        "Fies). Os microdados trazem, para cada inscrito, as notas das quatro provas objetivas e da redação, dados "
        "pessoais (sexo, cor/raça, tipo de escola) e o local de prova. O INEP publica a base para pesquisa e "
        "avaliação da educação. Aqui ela é usada para comparar parâmetros da população com estimativas de uma "
        "amostra aleatória simples.")
with c2:
    st.markdown(
        f"**Tamanho da base original:** {fmt_int(par['n_inscritos_csv'])} observações (inscritos) e "
        f"{par['n_colunas_csv']} variáveis.  \n"
        f"**População de interesse:** participantes **presentes nas quatro provas objetivas** (os dois dias), "
        f"com nota maior que zero em todas: **N = {fmt_int(par['N_populacao'])}**.  \n"
        "**Unidade amostral:** o participante.  \n"
        "**Variáveis usadas:** 9 (tabela abaixo).")

with st.expander("Variáveis selecionadas e seus tipos", expanded=True):
    st.table(pd.DataFrame([
        ("NU_NOTA_MT", "Nota de matemática (principal)", "Quantitativa contínua"),
        ("NU_NOTA_CN", "Nota de ciências da natureza", "Quantitativa contínua"),
        ("NU_NOTA_CH", "Nota de ciências humanas", "Quantitativa contínua"),
        ("NU_NOTA_LC", "Nota de linguagens e códigos", "Quantitativa contínua"),
        ("NU_NOTA_REDACAO", "Nota da redação (0 a 1000, de 20 em 20)", "Quantitativa discreta"),
        ("TP_SEXO", "Sexo (F/M)", "Qualitativa nominal"),
        ("TP_ESCOLA", "Tipo de escola do ensino médio (pública/privada), informado só por quem conclui o "
                      "ensino médio em 2023", "Qualitativa nominal"),
        ("TP_COR_RACA", "Cor/raça autodeclarada", "Qualitativa nominal"),
        ("SG_UF_PROVA", "UF onde fez a prova", "Qualitativa nominal"),
    ], columns=["Variável", "Descrição", "Tipo"]).set_index("Variável"))
    st.caption("A população deixou de fora 1.275.192 inscritos que faltaram a alguma prova objetiva, foram "
               "eliminados ou tiveram nota zero. Treineiros e egressos fazem parte da população.")

st.header("Indicadores da população")
cartoes(r)

st.header("Distribuições")
nota = escolher_nota("nota_p1")
graficos(r, AZUL, nota)

tabelas(r)
st.caption("Os gráficos são interativos: passe o mouse para ver os valores, arraste para dar zoom e clique "
           "duas vezes para voltar. " + "Variáveis qualitativas: " + ", ".join(QUALITATIVAS) + ".")
