"""Missão 2: dimensiona e sorteia a amostra aleatória simples.

Uso:  .venv/bin/python amostrar.py
Saídas: dados/amostra.parquet, dados/amostra_info.json
"""
import json
import math
from pathlib import Path

import pandas as pd

AQUI = Path(__file__).resolve().parent
SEMENTE = 2026
Z = 1.96            # confiança de 95%
E_PROP = 0.02       # margem de 2 pontos percentuais na proporção
P = 0.50            # proporção mais conservadora (maximiza p·(1-p))
E_MEDIA = 4.0       # margem de 4 pontos de nota na média

pop = pd.read_parquet(AQUI / "dados/populacao.parquet")
par = json.loads((AQUI / "dados/parametros.json").read_text())
sigma = par["desvio_mt"]              # desvio padrão da população (Missão 1)
N = len(pop)

n_prop = Z**2 * P * (1 - P) / E_PROP**2
n_media = (Z * sigma / E_MEDIA) ** 2
n = math.ceil(max(n_prop, n_media))   # fica com o maior, para valer para os dois objetivos
# correção para população finita: com N de milhões, o efeito é desprezível
n_fin = math.ceil(n / (1 + (n - 1) / N))
print(f"n proporção = {n_prop:.1f} -> {math.ceil(n_prop)}")
print(f"n média (σ={sigma:.2f}, E={E_MEDIA}) = {n_media:.1f} -> {math.ceil(n_media)}")
print(f"escolhido n = {n}  (com correção de população finita seria {n_fin}, igual na prática)")

amostra = pop.sample(n=n, random_state=SEMENTE).reset_index(drop=True)
amostra.to_parquet(AQUI / "dados/amostra.parquet", index=False, compression="zstd")
info = {"n": n, "n_proporcao": math.ceil(n_prop), "n_media": math.ceil(n_media), "sigma": sigma, "z": Z,
        "e_prop": E_PROP, "p": P, "e_media": E_MEDIA, "semente": SEMENTE, "N": N, "n_finita": n_fin,
        "media_amostra": float(amostra["NU_NOTA_MT"].astype("float64").mean()),
        "prop_mulheres_amostra": float((amostra["TP_SEXO"] == "F").mean())}
(AQUI / "dados/amostra_info.json").write_text(json.dumps(info, indent=2))
print(json.dumps(info, indent=2))
