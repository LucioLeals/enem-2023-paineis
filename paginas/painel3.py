import json

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from comum import AZUL, DADOS, LARANJA, VERDE, VERMELHO, carregar, fmt_int, fmt_num, fmt_pct, layout
from inferencia import ALFA, TESTES, Z, inferir, parametro, simular

info = json.loads((DADOS / "amostra_info.json").read_text())
pop_df, amo_df = carregar("populacao"), carregar("amostra")


@st.cache_data(show_spinner="Calculando intervalos e testes...")
def resultados(chave: str, _pop: pd.DataFrame, _amo: pd.DataFrame) -> list[dict]:
    return [inferir(_amo, t, parametro(_pop, t)) for t in TESTES]


@st.cache_data(show_spinner="Sorteando amostras...")
def simulacao(qual: str, quantas: int, n: int, _valores: np.ndarray) -> pd.DataFrame:
    return simular(_valores, n, quantas, prop=(qual == "P1"))


R = resultados(f"{info['n']}-{info['semente']}", pop_df, amo_df)
POR_ID = {r["id"]: r for r in R}


def fv(r: dict, v: float, casas: int = 2) -> str:
    """Valor no formato do parâmetro: porcentagem para proporção, pontos para média."""
    return fmt_pct(v, casas - 1 if casas > 1 else 1) if r["tipo"] == "prop" else fmt_num(v, casas)


def fdif(r: dict, d: float) -> str:
    return (f"{d * 100:+.2f}".replace(".", ",") + " p.p.") if r["tipo"] == "prop" else \
        (f"{d:+.2f}".replace(".", ",") + " pontos")


def fh0(r: dict) -> str:
    """Valor de H0 como foi escrito na hipótese (87,2% ou 500)."""
    if r["tipo"] == "media":
        return fmt_int(r["valor0"])
    return fmt_pct(r["valor0"], 0 if round(r["valor0"] * 100, 6).is_integer() else 1)


def pv(x: float) -> str:
    return "< 0,0001" if x < 1e-4 else fmt_num(x, 4)


def grafico_ic(r: dict) -> go.Figure:
    k = 100 if r["tipo"] == "prop" else 1
    lo, hi, e, par, v0 = (v * k for v in (*r["ic"], r["est"], r["param"], r["valor0"]))
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[lo, hi], y=[0, 0], mode="lines", line=dict(color=LARANJA, width=16),
                             name="IC de 95%", hovertemplate="%{x:.2f}<extra>IC de 95%</extra>"))
    fig.add_trace(go.Scatter(x=[e], y=[0], mode="markers", name="estimativa",
                             marker=dict(color="white", size=11, line=dict(color="black", width=1)),
                             hovertemplate="estimativa: %{x:.2f}<extra></extra>"))
    pts = [lo, hi, par, v0]
    meio = (min(pts) + max(pts)) / 2

    def lado(x):   # o rótulo abre para o lado que tem espaço
        return dict(xanchor="right", xshift=-6) if x > meio else dict(xanchor="left", xshift=6)
    fig.add_vline(x=par, line=dict(color=AZUL, width=3, dash="dot"))
    fig.add_annotation(x=par, y=0.75, text=f"parâmetro = {fmt_num(par, 2)}", showarrow=False,
                       font=dict(color=AZUL), yanchor="bottom", **lado(par))
    fig.add_vline(x=v0, line=dict(color="gray", width=2, dash="dash"))
    fig.add_annotation(x=v0, y=-0.75, text=f"valor de H0 = {fh0(r)}", showarrow=False,
                       font=dict(color="gray"), yanchor="top", **lado(v0))
    folga = (max(pts) - min(pts)) * 0.12
    fig.update_xaxes(range=[min(pts) - folga, max(pts) + folga],
                     title="porcentagem (%)" if r["tipo"] == "prop" else "nota de matemática")
    fig.update_yaxes(visible=False, range=[-1.3, 1.3])
    return layout(fig, f"IC de 95%: [{fmt_num(lo, 2)} ; {fmt_num(hi, 2)}]", height=260, showlegend=False)


def bloco(r: dict):
    with st.container(border=True):
        st.subheader(f"{r['id']} · {r['titulo']}")
        st.markdown(f"*{r['pergunta']}*")
        evento = f"  \n**Evento de interesse:** {r['evento']}." if r["evento"] else ""
        st.markdown(f"**Variável:** {r['variavel']}.{evento}  \n**Grupo analisado:** {r['grupo']}; "
                    f"n = {fmt_int(r['n'])} na amostra.")
        st.markdown(f"**H0:** {r['h0']}  ·  **H1:** {r['h1']} (bilateral)  ·  **α = {fmt_num(ALFA, 2)}**  \n"
                    f"**Por que esse valor de H0:** {r['justificativa']}")
        st.caption(f"Fonte da referência: {r['fonte']}")

        c = st.columns(3)
        c[0].metric("Parâmetro (população)", fv(r, r["param"]))
        c[1].metric("Estimativa (amostra)", fv(r, r["est"]), fdif(r, r["est"] - r["param"]) + " vs parâmetro",
                    delta_color="off")
        c[2].metric("Margem de erro (95%)", "±" + (fmt_num(r["margem"] * 100, 2) + " p.p." if r["tipo"] == "prop"
                                                  else fmt_num(r["margem"], 2) + " pontos"),
                    help="Margem = 1,96 × erro padrão. O 1,96 vem da curva normal (95% de confiança).")
        st.plotly_chart(grafico_ic(r), width="stretch")
        if r["dentro"]:
            st.success(f"O parâmetro ({fv(r, r['param'])}) caiu **dentro** do intervalo. A estimativa errou por "
                       f"{fmt_num(abs(r['erros_padrao']), 2)} erros padrão, dentro do esperado para 95% das amostras.")
        else:
            st.error(f"O parâmetro ({fv(r, r['param'])}) caiu **fora** do intervalo ({fmt_num(abs(r['erros_padrao']), 2)} "
                     "erros padrão de distância). Não é erro de conta: por construção, 5% das amostras produzem um "
                     "intervalo que não contém o parâmetro. É a variabilidade amostral.")

        decisao = "Rejeita H0" if r["rejeita"] else "Não rejeita H0"
        if r["rejeita"]:
            conclusao = (f"Ao nível de 5%, há evidência de que o parâmetro difere de {fh0(r)}: a "
                         f"estimativa é {fv(r, r['est'])}, {'acima' if r['est'] > r['valor0'] else 'abaixo'} da referência.")
        else:
            conclusao = f"Ao nível de 5%, não há evidência de que o parâmetro difira de {fh0(r)}."
        estat = f"{r['nome_estat']} = {fmt_num(r['estat'], 2)}" + (f" ({fmt_int(r['gl'])} graus de liberdade)"
                                                                     if r["tipo"] == "media" else "")
        st.table(pd.DataFrame({"Resultado": [r["h0"], r["h1"], fmt_num(ALFA, 2), estat, pv(r["p"]), decisao,
                                             conclusao]},
                              index=["Hipótese nula (H0)", "Hipótese alternativa (H1)", "Nível de significância (α)",
                                     "Estatística de teste", "Valor-p (bilateral)", "Decisão", "Conclusão"]))
        st.markdown(
            f"**IC × teste:** o valor de H0 ({fh0(r)}) está "
            f"{'dentro' if r['h0_no_ic'] else 'fora'} do intervalo de 95%, o que é coerente com "
            f"{'não rejeitar' if r['h0_no_ic'] else 'rejeitar'} H0 a 5%.")
        st.caption(f"**Condições:** amostra aleatória simples (observações independentes); amostra muito menor "
                   f"que 10% da população; {r['cond']}")
        with st.expander("Fórmulas e conta"):
            if r["tipo"] == "prop":
                st.latex(r"IC = \hat p \pm 1{,}96\sqrt{\frac{\hat p(1-\hat p)}{n}} \qquad "
                         r"z = \frac{\hat p - p_0}{\sqrt{p_0(1-p_0)/n}}")
                st.markdown(f"p̂ = {fmt_int(r['k'])} / {fmt_int(r['n'])} = {fmt_num(r['est'], 4)}; erro padrão = "
                            f"{fmt_num(r['ep'], 5)}; margem = 1,96 × {fmt_num(r['ep'], 5)} = {fmt_num(r['margem'], 4)}; "
                            f"IC = [{fmt_num(r['ic'][0], 4)} ; {fmt_num(r['ic'][1], 4)}].  \n"
                            f"z = ({fmt_num(r['est'], 4)} − {fmt_num(r['valor0'], 3)}) / {fmt_num(r['ep0'], 5)} = "
                            f"{fmt_num(r['estat'], 2)}; valor-p = {pv(r['p'])}.  \n"
                            "Biblioteca: `statsmodels.stats.proportion.proportions_ztest(k, n, value=p0, prop_var=p0)`.")
            else:
                st.latex(r"IC = \bar x \pm 1{,}96\,\frac{s}{\sqrt n} \qquad t = \frac{\bar x - \mu_0}{s/\sqrt n}")
                st.markdown(f"x̄ = {fmt_num(r['est'], 2)}; s = {fmt_num(r['s'], 2)}; erro padrão = "
                            f"{fmt_num(r['s'], 2)} / √{fmt_int(r['n'])} = {fmt_num(r['ep'], 3)}; margem = "
                            f"{fmt_num(r['margem'], 2)}; IC = [{fmt_num(r['ic'][0], 2)} ; {fmt_num(r['ic'][1], 2)}].  \n"
                            f"t = ({fmt_num(r['est'], 2)} − {fmt_num(r['valor0'], 0)}) / {fmt_num(r['ep'], 3)} = "
                            f"{fmt_num(r['estat'], 2)}; valor-p = {pv(r['p'])}.  \n"
                            "Biblioteca: `scipy.stats.ttest_1samp(notas, 500)`. Com n grande, t e z praticamente "
                            "coincidem (t crítico ≈ 1,96).")


# ============================ página ============================
st.title("Painel 3: inferência estatística e comparação dos resultados")
st.write(f"Todos os intervalos e testes usam **somente a amostra** (n = {fmt_int(info['n'])}), com confiança de 95% e "
         f"nível de significância α = {fmt_num(ALFA, 2)}. Os parâmetros da população (em azul) foram calculados "
         "diretamente na base completa e servem apenas para comparar.")
st.info("**Hipóteses analisadas:** duas para parâmetros de proporção (P1 e P2) e duas para parâmetros de média "
        "(M1 e M2). Cada uma tem H0, H1, intervalo de confiança, teste, conclusão e comparação com a população.")

st.header("a) Inferência para proporções")
bloco(POR_ID["P1"])
bloco(POR_ID["P2"])
st.header("b) Inferência para médias")
bloco(POR_ID["M1"])
bloco(POR_ID["M2"])

# ---------------- comparação ----------------
st.header("Comparação: população × amostra")
linhas = []
for r in R:
    linhas.append({
        "": r["id"], "Parâmetro de interesse": r["titulo"],
        "Parâmetro (população)": fv(r, r["param"]), "Estimativa (amostra)": fv(r, r["est"]),
        "Diferença": fdif(r, r["est"] - r["param"]), "Diferença em erros padrão": fmt_num(abs(r["erros_padrao"]), 2),
        "IC de 95%": f"[{fv(r, r['ic'][0])} ; {fv(r, r['ic'][1])}]",
        "IC contém o parâmetro?": "sim" if r["dentro"] else "não",
        "H0": r["h0"], "Valor-p": pv(r["p"]), "Decisão": "rejeita H0" if r["rejeita"] else "não rejeita H0"})
st.table(pd.DataFrame(linhas).set_index("").T)
st.markdown(
    "**Estimativas pontuais × intervalos:** a estimativa pontual é o centro do intervalo, e o intervalo soma e "
    "subtrai a margem de erro (1,96 erro padrão) para levar em conta a variabilidade amostral. A estimativa "
    "pontual sozinha quase nunca acerta o parâmetro em cheio (veja a linha \"Diferença\"). O intervalo, por "
    "construção, contém o parâmetro em cerca de 95% das amostras. Os intervalos de P2 e M2 são mais largos porque "
    f"usam só os concluintes da amostra (n = {fmt_int(POR_ID['P2']['n'])}), e não a amostra inteira.")

# ---------------- variabilidade amostral ----------------
st.header("O efeito da variabilidade amostral")
st.write(f"E se tivéssemos sorteado outra amostra? Como temos a população inteira, dá para sortear várias amostras "
         f"de n = {fmt_int(info['n'])} e ver quantos intervalos de 95% contêm o parâmetro verdadeiro.")
c1, c2 = st.columns([2, 3])
qual = c1.radio("Parâmetro", ["M1", "P1"],
                format_func=lambda k: {"M1": "Nota média de matemática", "P1": "Proporção de mulheres"}[k])
quantas = c2.slider("Quantas amostras sortear", 20, 200, 100, step=10)
alvo = POR_ID[qual]
valores = (pop_df["TP_SEXO"] == "F").to_numpy("float64") if qual == "P1" else pop_df["NU_NOTA_MT"].to_numpy("float64")
sim = simulacao(qual, quantas, info["n"], valores)
k = 100 if qual == "P1" else 1
dentro = (sim["lo"] <= alvo["param"]) & (alvo["param"] <= sim["hi"])
fig = go.Figure()
for mask, cor, nome in [(dentro, VERDE, "contém o parâmetro"), (~dentro, VERMELHO, "não contém")]:
    xs, ys = [], []
    for i in np.flatnonzero(mask.to_numpy()):
        xs += [sim["lo"].iat[i] * k, sim["hi"].iat[i] * k, None]
        ys += [i + 1, i + 1, None]
    fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", line=dict(color=cor, width=2), name=nome, hoverinfo="skip"))
fig.add_trace(go.Scatter(x=[alvo["ic"][0] * k, alvo["ic"][1] * k], y=[0, 0], mode="lines",
                         line=dict(color=LARANJA, width=6), name="a nossa amostra", hoverinfo="skip"))
fig.add_vline(x=alvo["param"] * k, line=dict(color=AZUL, width=3, dash="dot"))
st.plotly_chart(layout(fig, f"{int(dentro.sum())} de {quantas} intervalos contêm o parâmetro "
                            f"({fmt_pct(dentro.mean())}; o esperado é cerca de 95%)",
                       height=520, yaxis=dict(title="amostra sorteada", showticklabels=False),
                       xaxis_title="porcentagem de mulheres (%)" if qual == "P1" else "nota média de matemática",
                       legend=dict(orientation="h", y=1.0, yanchor="bottom", x=1, xanchor="right")), width="stretch")
st.caption(f"Cada linha é o intervalo de 95% de uma amostra aleatória simples de n = {fmt_int(info['n'])}; a linha "
           "pontilhada azul é o parâmetro; em laranja (embaixo) está a amostra usada neste trabalho. Amostras "
           "sorteadas com semente fixa (2026), diferentes da amostra do trabalho.")

# ---------------- interpretação e limitações ----------------
st.header("Interpretação e limitações")
st.subheader("Interpretação")
for r in R:
    st.markdown(
        f"- **{r['id']} · {r['titulo']}:** o parâmetro na população é {fv(r, r['param'])}; a amostra "
        f"(n = {fmt_int(r['n'])}) estimou {fv(r, r['est'])}, diferença de {fdif(r, r['est'] - r['param'])} "
        f"({fmt_num(abs(r['erros_padrao']), 2)} erros padrão). O IC de 95% foi de {fv(r, r['ic'][0])} a "
        f"{fv(r, r['ic'][1])} e {'contém' if r['dentro'] else 'não contém'} o parâmetro. O teste de H0: {r['h0']} "
        f"deu {r['nome_estat']} = {fmt_num(r['estat'], 2)} e valor-p {pv(r['p'])}, portanto "
        f"{'rejeitamos' if r['rejeita'] else 'não rejeitamos'} H0 ao nível de 5%.")
p1, p2, m1, m2 = (POR_ID[i] for i in ("P1", "P2", "M1", "M2"))
st.markdown(
    f"**Em resumo:** as mulheres são maioria entre os participantes ({fv(p1, p1['est'])} na amostra), e não a metade. "
    f"Os alunos de escola pública aparecem entre os concluintes participantes em proporção ({fv(p2, p2['est'])}) "
    f"menor que a sua participação nas matrículas do ensino médio (87,2%), o que sugere que eles chegam menos ao "
    f"ENEM. Em matemática, a média dos participantes ({fv(m1, m1['est'])}) e a dos concluintes ({fv(m2, m2['est'])}) "
    "ficaram acima da referência 500 da escala. Em todos os casos, o intervalo calculado com a amostra conteve o "
    "valor verdadeiro da população."
    if all(r["dentro"] and r["rejeita"] for r in R) and p1["est"] > 0.5 and p2["est"] < 0.872
    and m1["est"] > 500 and m2["est"] > 500 else "")
st.subheader("Limitações")
st.markdown(
    "- **Variabilidade amostral:** outra amostra aleatória daria estimativas diferentes (veja a simulação acima). "
    "Por construção, cerca de 5% dos intervalos de 95% não contêm o parâmetro, e um teste a 5% erra em 5% das "
    "vezes quando H0 é verdadeira.\n"
    "- **Vários testes:** com quatro testes a 5%, a chance de pelo menos um falso positivo seria de cerca de 18,5% "
    "se todas as H0 fossem verdadeiras. Aqui os valores-p são muito menores que 0,0001, então as conclusões "
    "não mudam.\n"
    "- **Significância não é tamanho:** com amostras grandes, diferenças pequenas já são significativas. O tamanho "
    "da diferença deve ser lido no intervalo de confiança, não no valor-p.\n"
    "- **População restrita:** só os participantes presentes nas quatro provas objetivas com nota maior que zero. "
    "As conclusões não valem para todos os inscritos nem para todos os jovens brasileiros.\n"
    "- **Subgrupo dos concluintes (P2 e M2):** o tipo de escola só é informado por quem conclui o ensino médio em "
    f"2023, então esses testes usam {fmt_int(p2['n'])} pessoas da amostra e têm margens maiores.\n"
    "- **Referências externas aproximadas:** o 87,2% do Censo Escolar vale para todas as matrículas do ensino médio, "
    "não só para os concluintes; o 500 foi fixado com os concluintes de 2009 e o perfil dos participantes mudou "
    "desde então.\n"
    "- **Dados autodeclarados:** sexo, cor/raça e tipo de escola são informados pelo próprio participante.")
