"""Missão 1: lê só as colunas certas do ENEM 2023, define a população, salva em parquet e calcula os parâmetros.

Uso:  .venv/bin/python preparar_base.py
Saídas: dados/populacao.parquet, dados/parametros.json
"""
import json
from pathlib import Path

import pandas as pd

AQUI = Path(__file__).resolve().parent
CSV = AQUI / "dados_brutos/microdados_enem_2023/DADOS/MICRODADOS_ENEM_2023.csv"
SAIDA = AQUI / "dados"
SAIDA.mkdir(exist_ok=True)

NOTAS = ["NU_NOTA_CN", "NU_NOTA_CH", "NU_NOTA_LC", "NU_NOTA_MT", "NU_NOTA_REDACAO"]
PRESENCAS = ["TP_PRESENCA_CN", "TP_PRESENCA_CH", "TP_PRESENCA_LC", "TP_PRESENCA_MT"]
QUAL = ["TP_SEXO", "TP_ESCOLA", "SG_UF_PROVA", "TP_COR_RACA"]
COLUNAS = NOTAS + PRESENCAS + QUAL

# passo 2: ler só o que importa (o CSV tem 1,7 GB e 76 colunas)
bruto = pd.read_csv(CSV, sep=";", encoding="latin-1", usecols=COLUNAS)
n_bruto, c_bruto = bruto.shape
print(f"CSV inteiro: {n_bruto:,} inscritos; lidas {len(COLUNAS)} colunas")

# passo 3: população = presentes nas provas objetivas dos dois dias, com nota > 0 em todas
presentes = bruto[(bruto[PRESENCAS] == 1).all(axis=1)]
pop = presentes[(presentes[NOTAS[:4]] > 0).all(axis=1)].copy()
pop = pop.drop(columns=PRESENCAS).reset_index(drop=True)
for c in ["TP_SEXO", "SG_UF_PROVA"]:
    pop[c] = pop[c].astype("category")
for c in ["TP_ESCOLA", "TP_COR_RACA"]:
    pop[c] = pop[c].astype("int8")
for c in NOTAS:
    pop[c] = pop[c].astype("float32")
pop.to_parquet(SAIDA / "populacao.parquet", index=False, compression="zstd")
print(f"população: {len(pop):,} linhas, {pop.shape[1]} colunas")

# parâmetros (os "números azuis")
mt = pop["NU_NOTA_MT"].astype("float64")
resp = pop[pop["TP_ESCOLA"] > 1]          # TP_ESCOLA: 1 não respondeu, 2 pública, 3 privada
par = {
    "n_inscritos_csv": int(n_bruto),
    "n_presentes_4_provas": int(len(presentes)),
    "N_populacao": int(len(pop)),
    "n_colunas_csv": 76,
    "media_mt": float(mt.mean()),
    "mediana_mt": float(mt.median()),
    "desvio_mt": float(mt.std()),
    "prop_mulheres": float((pop["TP_SEXO"] == "F").mean()),
    "prop_escola_publica": float((resp["TP_ESCOLA"] == 2).mean()),
    "n_escola_respondeu": int(len(resp)),
    "prop_escola_nao_respondeu": float((pop["TP_ESCOLA"] == 1).mean()),
}
(SAIDA / "parametros.json").write_text(json.dumps(par, indent=2, ensure_ascii=False))
print(json.dumps(par, indent=2, ensure_ascii=False))
