"""Intervalos de confiança e testes de hipóteses (Missões 3 e 4).

Regra da atividade: a inferência usa SÓ a amostra; os parâmetros da população são calculados diretamente na base
completa e entram apenas para comparar.

Quatro testes, dois de proporção e dois de média, todos bilaterais, com α = 0,05:
  P1  proporção de mulheres entre os participantes            H0: p = 0,50
  P2  proporção de escola pública entre os concluintes 2023   H0: p = 0,872 (Censo Escolar 2023)
  M1  nota média de matemática dos participantes              H0: μ = 500
  M2  nota média de matemática dos concluintes 2023           H0: μ = 500 (referência da escala do ENEM)
"""
import math

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.proportion import proportion_confint, proportions_ztest

ALFA = 0.05
Z = 1.96   # 95% de confiança

FONTE_ESCALA = ("INEP, 'Entenda a sua nota no Enem: guia do participante' (pasta de documentos dos microdados 2023): "
                "o valor 500 representa o desempenho médio dos concluintes regulares do ensino médio de 2009.")
FONTE_CENSO = ("INEP, Resumo Técnico do Censo Escolar da Educação Básica 2023, gráfico 19 (p. 35): matrículas do "
               "ensino médio em 2023 = 83,6% estadual + 3,1% federal + 0,5% municipal = 87,2% na rede pública.")

TESTES = [
    {"id": "P1", "tipo": "prop", "titulo": "Proporção de mulheres entre os participantes",
     "variavel": "sexo (`TP_SEXO`), qualitativa nominal", "evento": "o participante ser mulher (F)",
     "grupo": "todos os participantes da amostra", "valor0": 0.50,
     "h0": "p = 50%", "h1": "p ≠ 50%",
     "pergunta": "As mulheres participam do ENEM na mesma proporção que os homens?",
     "justificativa": "Entre os jovens brasileiros, a divisão por sexo é praticamente meio a meio. Se a participação "
                      "no ENEM não dependesse do sexo, metade dos participantes seriam mulheres.",
     "fonte": "Hipótese de igualdade entre os sexos (referência de 50%)."},
    {"id": "P2", "tipo": "prop", "titulo": "Proporção de escola pública entre os concluintes de 2023",
     "variavel": "tipo de escola (`TP_ESCOLA`), qualitativa nominal",
     "evento": "o concluinte ter estudado em escola pública",
     "grupo": "concluintes do ensino médio em 2023 (os únicos que informam o tipo de escola)", "valor0": 0.872,
     "h0": "p = 87,2%", "h1": "p ≠ 87,2%",
     "pergunta": "Os alunos de escola pública chegam ao ENEM (e fazem as quatro provas) na mesma proporção em "
                 "que estão matriculados no ensino médio?",
     "justificativa": "87,2% das matrículas do ensino médio em 2023 estavam na rede pública. Se o acesso ao ENEM "
                      "fosse igual entre as redes, essa seria a proporção entre os concluintes participantes.",
     "fonte": FONTE_CENSO},
    {"id": "M1", "tipo": "media", "titulo": "Nota média de matemática dos participantes",
     "variavel": "nota de matemática (`NU_NOTA_MT`), quantitativa contínua", "evento": None,
     "grupo": "todos os participantes da amostra", "valor0": 500.0,
     "h0": "μ = 500", "h1": "μ ≠ 500",
     "pergunta": "O desempenho médio em matemática de 2023 é igual ao ponto de referência da escala do ENEM?",
     "justificativa": "A escala do ENEM foi construída de modo que 500 fosse o desempenho médio de referência.",
     "fonte": FONTE_ESCALA},
    {"id": "M2", "tipo": "media", "titulo": "Nota média de matemática dos concluintes de 2023",
     "variavel": "nota de matemática (`NU_NOTA_MT`), quantitativa contínua", "evento": None,
     "grupo": "concluintes do ensino médio em 2023 (o mesmo tipo de aluno que definiu a referência 500)",
     "valor0": 500.0, "h0": "μ = 500", "h1": "μ ≠ 500",
     "pergunta": "Os concluintes de 2023 têm, em matemática, o mesmo desempenho médio que os concluintes de 2009, "
                 "que definiram o 500 da escala?",
     "justificativa": "É a comparação mais justa com a referência: o 500 é a média dos concluintes regulares de 2009, "
                      "e aqui o grupo também é de concluintes.",
     "fonte": FONTE_ESCALA},
]


def _mil(x: float) -> str:
    """Inteiro com ponto de milhar (1.878)."""
    return f"{round(x):,}".replace(",", ".")


def _grupo(df: pd.DataFrame, t: dict) -> pd.DataFrame:
    return df[df["TP_ESCOLA"] > 1] if t["id"] in ("P2", "M2") else df


def _evento(df: pd.DataFrame, t: dict) -> pd.Series:
    return (df["TP_SEXO"] == "F") if t["id"] == "P1" else (df["TP_ESCOLA"] == 2)


def parametro(pop: pd.DataFrame, t: dict) -> float:
    """Valor verdadeiro, calculado diretamente na população."""
    g = _grupo(pop, t)
    return float(_evento(g, t).mean()) if t["tipo"] == "prop" else float(g["NU_NOTA_MT"].astype("float64").mean())


def inferir(amostra: pd.DataFrame, t: dict, param: float) -> dict:
    """IC de 95% (fórmulas do curso, z = 1,96) e teste bilateral, com os dados da amostra."""
    g = _grupo(amostra, t)
    n = len(g)
    r = {**t, "n": n, "param": param}
    if t["tipo"] == "prop":
        k = int(_evento(g, t).sum())
        est = k / n
        ep = math.sqrt(est * (1 - est) / n)
        estat, valor_p = proportions_ztest(k, n, value=t["valor0"], prop_var=t["valor0"])  # EP sob H0
        assert abs(proportion_confint(k, n, alpha=ALFA, method="normal")[0] - (est - Z * ep)) < 1e-3
        r.update(k=k, nome_estat="z", ep0=math.sqrt(t["valor0"] * (1 - t["valor0"]) / n),
                 cond=f"n·p₀ = {_mil(n * t['valor0'])} e n·(1−p₀) = {_mil(n * (1 - t['valor0']))}, ambos ≥ 10; "
                      f"na amostra há {_mil(k)} sucessos e {_mil(n - k)} fracassos (≥ 10 cada).")
    else:
        x = g["NU_NOTA_MT"].astype("float64")
        est, s = x.mean(), x.std(ddof=1)
        ep = s / math.sqrt(n)
        estat, valor_p = stats.ttest_1samp(x, t["valor0"])
        assert abs(stats.norm.interval(0.95, loc=est, scale=ep)[0] - (est - Z * ep)) < 0.05
        r.update(s=s, nome_estat="t", gl=n - 1,
                 cond=f"n = {_mil(n)} é muito maior que 30, então a média amostral é aproximadamente normal "
                      "(teorema central do limite), mesmo que a nota não seja exatamente normal.")
    ic = (est - Z * ep, est + Z * ep)
    r.update(est=est, ep=ep, margem=Z * ep, ic=ic, estat=float(estat), p=float(valor_p),
             rejeita=valor_p < ALFA, dentro=ic[0] <= param <= ic[1],
             h0_no_ic=ic[0] <= t["valor0"] <= ic[1], erros_padrao=(est - param) / ep)
    return r


def simular(valores: np.ndarray, n: int, quantas: int, prop: bool, semente: int = 2026) -> pd.DataFrame:
    """Sorteia `quantas` amostras aleatórias simples de tamanho n e devolve o IC de 95% de cada uma.

    `valores` é a variável na população (nota, ou 0/1 para proporção); serve para mostrar a variabilidade amostral.
    """
    rng = np.random.default_rng(semente)
    linhas = []
    for _ in range(quantas):
        x = valores[rng.choice(len(valores), n, replace=False)]
        m = x.mean()
        ep = math.sqrt(m * (1 - m) / n) if prop else x.std(ddof=1) / math.sqrt(n)
        linhas.append((m, m - Z * ep, m + Z * ep))
    return pd.DataFrame(linhas, columns=["est", "lo", "hi"])
