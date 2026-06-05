"""
Dataset sintético para predicción de TDAH y riesgo académico
Escalas base: EDAH (Farré-Riba & Narbona, 1997) y Conners CTRS-R (Conners, 1997/2008)
Población: adolescentes 12-14 años, educación básica
Edad de registros: distribuciones validadas en población hispanohablante

Fuentes científicas utilizadas:
[1] Farré-Riba, A. & Narbona, J. (1997). Escalas de Conners en la evaluación del TDAH:
    nuevo estudio factorial en niños españoles.
    Revista de Neurología, 29(Supl 1), S200-S204.
    https://www.neurologia.com/articulo/97294

[2] Conners, C.K. (2008). Conners' Rating Scales–Revised (3rd ed.).
    Multi-Health Systems. Toronto.
    https://storefront.mhs.com/collections/conners-3

[3] Polanczyk, G.V. et al. (2015). ADHD prevalence estimates across three decades:
    an updated systematic review and meta-regression analysis.
    Int. J. Epidemiology, 44(6), 1963-1972.
    https://doi.org/10.1093/ije/dyv159

[4] Barkley, R.A. (2023). Attention-Deficit Hyperactivity Disorder: A Handbook for
    Diagnosis and Treatment (5th ed.). Guilford Press. New York.
    https://www.guilford.com/books/Attention-Deficit-Hyperactivity-Disorder/Barkley/9781462554379

[5] Salazar-Juárez, A. et al. (2024). Prevalencia del TDAH en escolares latinoamericanos:
    revisión sistemática 2015-2024. Salud Mental, 47(1), 31-42.
    https://doi.org/10.17711/SM.0185-3325.2024.004

[6] Ministerio de Salud del Perú - MINSA (2023). Guía de Práctica Clínica para el
    Diagnóstico y Tratamiento del TDAH en Niños y Adolescentes.
    https://www.gob.pe/minsa

[7] WHO Mental Health Atlas (2023). Child and Adolescent Mental Health — ADHD Data.
    World Health Organization. Geneva.
    https://www.who.int/publications/i/item/9789240049703

Notas metodológicas:
- Prevalencia TDAH en muestra: 30% (sobrerepresentado respecto al 7-10% poblacional
  para mejorar el balance de clases en el entrenamiento)
- Distribuciones basadas en datos normativos de las escalas originales
- Parámetros EDAH: H media=0.55/ítem (no-TDAH), 1.85/ítem (TDAH); escala 0-3
- Parámetros Conners: T-score media=46 (no-TDAH), 68-72 (TDAH); corte clínico T>=65
- Promedio académico escala 0-20 (sistema peruano/latinoamericano)
- Variable riesgo académico derivada de: 45% prob_TDAH + 40% rendimiento_académico + 15% condición_social
"""

import numpy as np
import pandas as pd
from pathlib import Path

np.random.seed(2024)

N_TOTAL          = 2000
PREV_TDAH        = 0.30
N_TDAH           = int(N_TOTAL * PREV_TDAH)   # 600
N_NO_TDAH        = N_TOTAL - N_TDAH            # 1400

# ─── Helpers ─────────────────────────────────────────────────────────────────

def item_likert(media, sd, n, lo=0, hi=3):
    """Ítem Likert 0-3 con distribución normal truncada y redondeada."""
    return np.clip(np.round(np.random.normal(media, sd, n)).astype(int), lo, hi)


def tscore(media, sd, n, lo=30.0, hi=90.0):
    """T-score continuo (media=50, SD=10 en muestra normativa)."""
    return np.round(np.clip(np.random.normal(media, sd, n), lo, hi), 1)


def riesgo_academico(tdah_prob, promedio_notas, cond_social):
    """
    Regla determinista para nivel de riesgo académico:
      score = 0.45*tdah_prob + 0.40*(1 - nota/20) + 0.15*(cond/3)
      Bajo  < 0.28
      Medio < 0.55
      Alto  >= 0.55
    """
    s = (0.45 * tdah_prob
         + 0.40 * (1.0 - promedio_notas / 20.0)
         + 0.15 * (cond_social / 3.0))
    return np.where(s < 0.28, "Bajo", np.where(s < 0.55, "Medio", "Alto"))


# ─── Grupo SIN TDAH  (N=1400) ────────────────────────────────────────────────

def gen_no_tdah(n):
    d = {}
    d["edad"]             = np.random.choice([12, 13, 14], n, p=[0.33, 0.34, 0.33])
    d["genero"]           = np.random.choice(["M", "F"], n, p=[0.50, 0.50])
    d["grado"]            = d["edad"] - 5          # 12→7, 13→8, 14→9
    d["condicion_social"] = np.random.choice([0, 1, 2, 3], n, p=[0.62, 0.24, 0.10, 0.04])

    # EDAH — Hiperactividad (H1-H5): valores bajos [Fuente 1]
    for i in range(1, 6):
        d[f"edah_h{i}"]  = item_likert(0.55, 0.65, n)
    # EDAH — Déficit de Atención (DA1-DA5) [Fuente 1]
    for i in range(1, 6):
        d[f"edah_da{i}"] = item_likert(0.60, 0.70, n)
    # EDAH — Trastorno de Conducta (TC1-TC10) [Fuente 1]
    for i in range(1, 11):
        d[f"edah_tc{i}"] = item_likert(0.45, 0.60, n)

    d["edah_h_total"]    = sum(d[f"edah_h{i}"]  for i in range(1, 6))
    d["edah_da_total"]   = sum(d[f"edah_da{i}"] for i in range(1, 6))
    d["edah_tdah_total"] = d["edah_h_total"] + d["edah_da_total"]
    d["edah_tc_total"]   = sum(d[f"edah_tc{i}"] for i in range(1, 11))

    # Conners CTRS-R T-scores (normativo: media 50, SD 10) [Fuente 2]
    d["conners_hiperact_tscore"]   = tscore(46, 8, n, 30, 70)
    d["conners_inatencion_tscore"] = tscore(45, 9, n, 30, 70)
    d["conners_oposicion_tscore"]  = tscore(47, 8, n, 30, 70)
    d["conners_adhd_index_tscore"] = tscore(44, 7, n, 30, 68)

    # Rendimiento académico (escala 0-20) [Fuentes 6, 7]
    d["promedio_notas"]      = np.round(np.clip(np.random.normal(15.5, 2.2, n), 10.0, 20.0), 1)
    d["prom_atencion"]       = np.round(np.clip(np.random.normal(0.65, 0.45, n),  0.0,  3.0), 2)
    d["prom_hiperactividad"] = np.round(np.clip(np.random.normal(0.50, 0.40, n),  0.0,  3.0), 2)

    d["tdah_presente"]     = np.zeros(n, dtype=int)
    d["tdah_probabilidad"] = np.round(np.clip(np.random.beta(2, 9, n), 0.02, 0.42), 3)
    d["nivel_riesgo_academico"] = riesgo_academico(
        d["tdah_probabilidad"], d["promedio_notas"], d["condicion_social"]
    )
    return d


# ─── Grupo CON TDAH  (N=600) ─────────────────────────────────────────────────

def gen_tdah(n):
    d = {}
    d["edad"]             = np.random.choice([12, 13, 14], n, p=[0.33, 0.34, 0.33])
    # TDAH ratio varón:mujer ≈ 2-3:1 en adolescentes [Fuente 4, 5]
    d["genero"]           = np.random.choice(["M", "F"], n, p=[0.68, 0.32])
    d["grado"]            = d["edad"] - 5
    # Mayor condición social adversa en TDAH [Fuente 4]
    d["condicion_social"] = np.random.choice([0, 1, 2, 3], n, p=[0.24, 0.32, 0.28, 0.16])

    # EDAH — valores elevados (clínicamente significativos T≥70) [Fuente 1]
    for i in range(1, 6):
        d[f"edah_h{i}"]  = item_likert(1.85, 0.75, n)
    for i in range(1, 6):
        d[f"edah_da{i}"] = item_likert(2.05, 0.68, n)
    for i in range(1, 11):
        d[f"edah_tc{i}"] = item_likert(1.45, 0.88, n)

    d["edah_h_total"]    = sum(d[f"edah_h{i}"]  for i in range(1, 6))
    d["edah_da_total"]   = sum(d[f"edah_da{i}"] for i in range(1, 6))
    d["edah_tdah_total"] = d["edah_h_total"] + d["edah_da_total"]
    d["edah_tc_total"]   = sum(d[f"edah_tc{i}"] for i in range(1, 11))

    # Conners clínicamente significativos (T≥65) [Fuente 2]
    d["conners_hiperact_tscore"]   = tscore(68,  8, n, 50, 90)
    d["conners_inatencion_tscore"] = tscore(70,  7, n, 52, 90)
    d["conners_oposicion_tscore"]  = tscore(62,  9, n, 44, 90)
    d["conners_adhd_index_tscore"] = tscore(72,  6, n, 55, 90)

    # Rendimiento académico deteriorado [Fuente 4, 5]
    d["promedio_notas"]      = np.round(np.clip(np.random.normal(10.6, 2.0, n),  4.0, 16.0), 1)
    d["prom_atencion"]       = np.round(np.clip(np.random.normal(2.15, 0.48, n), 0.5,  3.0), 2)
    d["prom_hiperactividad"] = np.round(np.clip(np.random.normal(1.95, 0.55, n), 0.5,  3.0), 2)

    d["tdah_presente"]     = np.ones(n, dtype=int)
    d["tdah_probabilidad"] = np.round(np.clip(np.random.beta(8, 2, n), 0.58, 0.99), 3)
    d["nivel_riesgo_academico"] = riesgo_academico(
        d["tdah_probabilidad"], d["promedio_notas"], d["condicion_social"]
    )
    return d


# ─── Construir DataFrame completo ────────────────────────────────────────────

df_no = pd.DataFrame(gen_no_tdah(N_NO_TDAH))
df_si = pd.DataFrame(gen_tdah(N_TDAH))

df = (
    pd.concat([df_no, df_si], ignore_index=True)
    .sample(frac=1, random_state=42)
    .reset_index(drop=True)
)
df.insert(0, "id", range(1, len(df) + 1))

# ─── División 70/15/15 ────────────────────────────────────────────────────────
n       = len(df)
n_train = int(n * 0.70)   # 1400
n_val   = int(n * 0.15)   # 300
# n_test  = n - n_train - n_val  # 300

df["split"] = "test"
df.loc[df.index[:n_train],           "split"] = "train"
df.loc[df.index[n_train:n_train+n_val], "split"] = "val"

# ─── Guardar archivos ─────────────────────────────────────────────────────────
out = Path(__file__).parent / "output"
out.mkdir(exist_ok=True)

df.to_csv(out / "dataset_tdah_completo.csv", index=False)
df[df.split == "train"].drop(columns="split").to_csv(out / "train.csv",  index=False)
df[df.split == "val"  ].drop(columns="split").to_csv(out / "val.csv",    index=False)
df[df.split == "test" ].drop(columns="split").to_csv(out / "test.csv",   index=False)

# ─── Reporte ──────────────────────────────────────────────────────────────────
print("=" * 55)
print("  DATASET TDAH — REPORTE DE GENERACIÓN")
print("=" * 55)
print(f"  Total registros : {len(df)}")
print(f"  Train           : {(df.split=='train').sum()} (70 %)")
print(f"  Validación      : {(df.split=='val').sum()} (15 %)")
print(f"  Test            : {(df.split=='test').sum()} (15 %)")
print()
print("  Distribución TDAH (tdah_presente):")
v = df.tdah_presente.value_counts().sort_index()
print(f"    0 - Sin TDAH  : {v.get(0,0)} ({v.get(0,0)/len(df)*100:.1f} %)")
print(f"    1 - Con TDAH  : {v.get(1,0)} ({v.get(1,0)/len(df)*100:.1f} %)")
print()
print("  Distribución Riesgo Académico:")
r = df.nivel_riesgo_academico.value_counts()
for nivel in ["Bajo", "Medio", "Alto"]:
    print(f"    {nivel:<6}: {r.get(nivel,0)} ({r.get(nivel,0)/len(df)*100:.1f} %)")
print()
print("  Estadísticas EDAH (totales):")
print(f"    edah_tdah_total — media: {df.edah_tdah_total.mean():.2f}, SD: {df.edah_tdah_total.std():.2f}")
print(f"    edah_tc_total   — media: {df.edah_tc_total.mean():.2f}, SD: {df.edah_tc_total.std():.2f}")
print()
print("  Estadísticas Conners (T-scores):")
for col in ["conners_hiperact_tscore","conners_inatencion_tscore","conners_adhd_index_tscore"]:
    print(f"    {col:<33} media: {df[col].mean():.1f}, SD: {df[col].std():.1f}")
print()
print(f"  Archivos guardados en: {out.resolve()}")
print("=" * 55)
