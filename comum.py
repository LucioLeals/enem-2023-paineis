"""Funções compartilhadas pelos painéis: escritas uma vez, usadas com a população (Painel 1) e com a amostra (Painel 2).

Desempenho: nada de dados brutos vai para o navegador. `resumir` calcula uma vez (e fica em cache) só o que os
gráficos precisam: contagens dos histogramas, estatísticas dos boxplots e frequências. Os gráficos são desenhados a
partir desses resumos, o que mantém o painel leve mesmo com 2,6 milhões de linhas.
"""
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

DADOS = Path(__file__).resolve().parent / "dados"
AZUL, LARANJA = "#4aa3ff", "#ff9f43"   # azul = população (parâmetro), laranja = amostra (estimativa)
VERDE, VERMELHO = "#2ecc71", "#ff6b6b"
ESCOLA = {1: "Não se aplica (não concluinte)", 2: "Pública", 3: "Privada"}
SEXO = {"F": "Feminino", "M": "Masculino"}
COR = {0: "Não declarada", 1: "Branca", 2: "Preta", 3: "Parda", 4: "Amarela", 5: "Indígena",
       6: "Não dispõe da informação"}
NOMES_NOTAS = {"NU_NOTA_MT": "Matemática", "NU_NOTA_CN": "Ciências da natureza", "NU_NOTA_CH": "Ciências humanas",
               "NU_NOTA_LC": "Linguagens e códigos", "NU_NOTA_REDACAO": "Redação"}
QUALITATIVAS = ["Sexo", "Tipo de escola (concluintes 2023)", "Cor/raça", "UF da prova"]


def freq_grafico(r: dict, var: str) -> pd.Series:
    """Frequências usadas nos gráficos: o tipo de escola só entre os concluintes (os que informam)."""
    return r["escola_concl"] if var.startswith("Tipo de escola") else r["freq"][var]
MT = "NU_NOTA_MT"
# faixas fixas dos histogramas: as mesmas na população e na amostra, para poder comparar
BORDAS = {c: np.arange(280, 981, 14) for c in NOMES_NOTAS}
BORDAS["NU_NOTA_REDACAO"] = np.arange(-10, 1011, 20)   # redação: notas múltiplas de 20, uma barra por nota


@st.cache_data
def carregar(nome: str) -> pd.DataFrame:
    return pd.read_parquet(DADOS / f"{nome}.parquet")


def _caixa(x: pd.Series) -> dict:
    """Estatísticas de um boxplot (bigodes a 1,5·IQR, limitados aos dados)."""
    x = x.astype("float64")
    q1, med, q3 = x.quantile([.25, .5, .75])
    iqr = q3 - q1
    return {"n": len(x), "q1": q1, "mediana": med, "q3": q3, "media": x.mean(), "desvio": x.std(),
            "min": x.min(), "max": x.max(),
            "bigode_inf": x[x >= q1 - 1.5 * iqr].min(), "bigode_sup": x[x <= q3 + 1.5 * iqr].max()}


@st.cache_data(show_spinner="Calculando os resumos...")
def resumir(chave: str, _df: pd.DataFrame) -> dict:
    """Tudo que os painéis 1 e 2 mostram, calculado uma vez por base (`chave` identifica a base no cache)."""
    df = _df
    mt = df[MT].astype("float64")
    concl = df[df["TP_ESCOLA"] > 1]          # TP_ESCOLA só é respondido por quem conclui o ensino médio em 2023
    escola = df["TP_ESCOLA"].map(ESCOLA)
    return {
        "n": len(df),
        "params": {"media": mt.mean(), "mediana": mt.median(), "desvio": mt.std(),
                   "mulheres": (df["TP_SEXO"] == "F").mean(), "publica": (concl["TP_ESCOLA"] == 2).mean(),
                   "n_concluintes": len(concl)},
        "hist": {c: np.histogram(df[c].astype("float64"), bins=BORDAS[c])[0] for c in NOMES_NOTAS},
        "caixa": {c: _caixa(df[c]) for c in NOMES_NOTAS},
        "caixa_escola": {c: {ESCOLA[k]: _caixa(df.loc[df["TP_ESCOLA"] == k, c]) for k in (2, 3, 1)
                             if (df["TP_ESCOLA"] == k).any()} for c in NOMES_NOTAS},
        "freq": {"Sexo": df["TP_SEXO"].astype(str).map(SEXO).value_counts(),
                 "Tipo de escola": escola.value_counts(),
                 "Cor/raça": df["TP_COR_RACA"].map(COR).value_counts(),
                 "UF da prova": df["SG_UF_PROVA"].astype(str).value_counts()},
        "escola_concl": concl["TP_ESCOLA"].map(ESCOLA).value_counts(),
    }


def fmt_pct(x: float, casas: int = 1) -> str:
    return f"{x * 100:.{casas}f}%".replace(".", ",")


def fmt_num(x: float, casas: int = 1) -> str:
    return f"{x:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_int(x: float) -> str:
    return fmt_num(x, 0)


def cartoes(r: dict, ref: dict | None = None):
    """5 cartões de métrica. Com `ref` (params da população), mostra a diferença no campo delta."""
    p = r["params"]

    def delta(k, pct=False):
        if ref is None:
            return None
        d = (p[k] - ref[k]) * (100 if pct else 1)
        return f"{d:+.2f}".replace(".", ",") + (" p.p." if pct else "") + " vs população"
    c = st.columns(5)
    c[0].metric("Média MT", fmt_num(p["media"]), delta("media"), delta_color="off")
    c[1].metric("Mediana MT", fmt_num(p["mediana"]), delta("mediana"), delta_color="off")
    c[2].metric("Desvio padrão MT", fmt_num(p["desvio"]), delta("desvio"), delta_color="off")
    c[3].metric("% mulheres", fmt_pct(p["mulheres"]), delta("mulheres", True), delta_color="off")
    c[4].metric("% escola pública*", fmt_pct(p["publica"]), delta("publica", True), delta_color="off")
    st.caption(f"MT = nota de matemática. *Entre os concluintes do ensino médio em 2023 "
               f"({fmt_int(p['n_concluintes'])} participantes), os únicos que informam o tipo de escola.")


def layout(fig: go.Figure, titulo: str, **extra) -> go.Figure:
    """Layout padrão: números no formato brasileiro (vírgula decimal, ponto de milhar)."""
    return fig.update_layout(title=titulo, margin=dict(l=10, r=10, t=70, b=10), separators=",.", **extra)


def _box(nome: str, c: dict, cor: str, horizontal: bool) -> go.Box:
    est = dict(q1=[c["q1"]], median=[c["mediana"]], q3=[c["q3"]], mean=[c["media"]], sd=[c["desvio"]],
               lowerfence=[c["bigode_inf"]], upperfence=[c["bigode_sup"]], marker_color=cor, name=nome,
               boxmean="sd")
    return go.Box(**est, **({"y": [nome], "orientation": "h"} if horizontal else {"x": [nome]}))


def _centros(c: str) -> np.ndarray:
    b = BORDAS[c]
    return (b[:-1] + b[1:]) / 2


def _barras(serie: pd.Series, rotulo: str, cor: str, titulo: str) -> go.Figure:
    s = serie / serie.sum()
    fig = go.Figure(go.Bar(x=s.index, y=s.values, marker_color=cor,
                           text=[fmt_pct(v) for v in s.values], textposition="outside",
                           hovertemplate="%{x}: %{y:.1%}<extra></extra>"))
    return layout(fig, titulo, yaxis=dict(tickformat=".0%"), xaxis_title=rotulo, showlegend=False)


def escolher_nota(chave: str) -> str:
    return st.selectbox("Variável quantitativa (nota)", list(NOMES_NOTAS), format_func=NOMES_NOTAS.get, key=chave)


def graficos(r: dict, cor: str, nota: str):
    """Distribuição da nota escolhida (histograma, boxplot, boxplot por escola) e barras das qualitativas."""
    nome = NOMES_NOTAS[nota]
    h = go.Figure(go.Bar(x=_centros(nota), y=r["hist"][nota], width=np.diff(BORDAS[nota]), marker_color=cor,
                         hovertemplate="%{x:.0f} pontos: %{y:,} participantes<extra></extra>"))
    esq, dir_ = st.columns(2)
    esq.plotly_chart(layout(h, f"Histograma: nota de {nome.lower()}", xaxis_title="Nota",
                            yaxis=dict(title="Participantes", tickformat=",d"), bargap=0.02, showlegend=False),
                     width="stretch")
    b = go.Figure(_box(nome, r["caixa"][nota], cor, horizontal=True))
    dir_.plotly_chart(layout(b, f"Boxplot: nota de {nome.lower()}", xaxis_title="Nota", showlegend=False),
                      width="stretch")
    g = go.Figure([_box(k, v, cor, horizontal=False) for k, v in r["caixa_escola"][nota].items()])
    st.plotly_chart(layout(g, f"Nota de {nome.lower()} por tipo de escola", yaxis_title="Nota", showlegend=False),
                    width="stretch")
    st.caption("Boxplots: caixa de Q1 a Q3, linha cheia = mediana, linha tracejada e losango = média ± desvio "
               "padrão, bigodes a 1,5·IQR. Os pontos além dos bigodes foram omitidos para manter o painel leve.")
    a, c = st.columns(2)
    a.plotly_chart(_barras(r["freq"]["Sexo"], "Sexo", cor, "Proporção por sexo"), width="stretch")
    c.plotly_chart(_barras(r["escola_concl"], "Tipo de escola", cor,
                           "Tipo de escola entre os concluintes de 2023"), width="stretch")
    st.plotly_chart(_barras(r["freq"]["Cor/raça"], "Cor/raça declarada", cor, "Proporção por cor/raça"),
                    width="stretch")
    st.plotly_chart(_barras(r["freq"]["UF da prova"], "UF", cor, "Proporção por UF de realização da prova")
                    .update_traces(textposition="none"), width="stretch")


def tabelas(r: dict):
    """Medidas descritivas das cinco notas e tabelas de frequência/proporção das variáveis qualitativas."""
    st.subheader("Medidas descritivas das variáveis quantitativas")
    n = pd.DataFrame(r["caixa"]).T.rename(index=NOMES_NOTAS)
    t = pd.DataFrame({"Média": n["media"], "Mediana": n["mediana"], "Desvio padrão": n["desvio"],
                      "Mínimo": n["min"], "Q1": n["q1"], "Q3": n["q3"], "Máximo": n["max"]}).astype(float)
    t["Amplitude interquartil"] = t["Q3"] - t["Q1"]
    t["Coef. de variação"] = t["Desvio padrão"] / t["Média"]
    st.dataframe(t.style.format(lambda v: fmt_num(v, 1), subset=t.columns[:-1])
                 .format(lambda v: fmt_pct(v), subset=["Coef. de variação"]), width="stretch")
    st.subheader("Frequências e proporções das variáveis qualitativas")
    itens = list(r["freq"].items())
    for par in (itens[:2], itens[2:]):
        for col, (rot, s) in zip(st.columns(2), par):
            f = s.rename_axis(rot).reset_index(name="Frequência")
            f["Proporção"] = f["Frequência"] / f["Frequência"].sum()
            col.markdown(f"**{rot}**")
            col.dataframe(f.style.format({"Frequência": fmt_int, "Proporção": fmt_pct}), hide_index=True,
                          width="stretch", height=min(36 * (len(f) + 1) + 3, 320))
    st.caption("Tipo de escola: \"Não se aplica\" são os participantes que não concluem o ensino médio em 2023 "
               "(egressos e treineiros); só os concluintes informam o tipo de escola.")


# ---------- comparação população × amostra (Painel 2) ----------

def comparar_distribuicao(pop: dict, amo: dict, nota: str):
    """Histogramas em proporção (% dos participantes em cada faixa), população e amostra sobrepostas."""
    nome = NOMES_NOTAS[nota]
    x, w = _centros(nota), np.diff(BORDAS[nota])
    hp, ha = pop["hist"][nota], amo["hist"][nota]
    fig = go.Figure([
        go.Bar(x=x, y=hp / hp.sum(), width=w, name="População", marker_color=AZUL, opacity=0.55,
               hovertemplate="%{x:.0f}: %{y:.2%}<extra>população</extra>"),
        go.Bar(x=x, y=ha / ha.sum(), width=w, name="Amostra", marker_color=LARANJA, opacity=0.55,
               hovertemplate="%{x:.0f}: %{y:.2%}<extra>amostra</extra>"),
    ])
    st.plotly_chart(layout(fig, f"Distribuição da nota de {nome.lower()}: população × amostra", barmode="overlay",
                           xaxis_title="Nota", yaxis=dict(tickformat=".1%", title="% dos participantes"),
                           legend=dict(orientation="h", y=1.0, yanchor="bottom", x=1, xanchor="right")), width="stretch")


def comparar_categorias(pop: dict, amo: dict, var: str):
    """Barras lado a lado com a proporção de cada categoria na população e na amostra."""
    fp, fa = freq_grafico(pop, var), freq_grafico(amo, var)
    p = fp / fp.sum()
    a = (fa / fa.sum()).reindex(p.index).fillna(0)
    fig = go.Figure([
        go.Bar(x=p.index, y=p.values, name="População", marker_color=AZUL, hovertemplate="%{x}: %{y:.1%}<extra>população</extra>"),
        go.Bar(x=a.index, y=a.values, name="Amostra", marker_color=LARANJA, hovertemplate="%{x}: %{y:.1%}<extra>amostra</extra>"),
    ])
    st.plotly_chart(layout(fig, f"{var}: população × amostra", barmode="group", yaxis=dict(tickformat=".0%"),
                           legend=dict(orientation="h", y=1.0, yanchor="bottom", x=1, xanchor="right")), width="stretch")


def tabela_comparacao(pop: dict, amo: dict):
    """Média, mediana e desvio de cada nota, na população e na amostra, com a diferença."""
    linhas = []
    for c, nome in NOMES_NOTAS.items():
        p, a = pop["caixa"][c], amo["caixa"][c]
        linhas.append({"Nota": nome, "Média (pop.)": p["media"], "Média (amostra)": a["media"],
                       "Dif. média": a["media"] - p["media"], "Mediana (pop.)": p["mediana"],
                       "Mediana (amostra)": a["mediana"], "Desvio (pop.)": p["desvio"], "Desvio (amostra)": a["desvio"]})
    t = pd.DataFrame(linhas).set_index("Nota")
    st.dataframe(t.style.format(lambda v: fmt_num(v, 1)), width="stretch")
