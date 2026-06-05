"""
Evaluacion completa del modelo XGBoost — prediccion de riesgo academico.
Modelo entrenado con etiquetas: 0=Bajo, 1=Medio, 2=Alto
"""
import os, warnings
warnings.filterwarnings("ignore")

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score, classification_report, confusion_matrix,
    roc_auc_score, cohen_kappa_score, log_loss, matthews_corrcoef
)

BASE        = os.path.dirname(__file__)
MODELO_PATH = os.path.join(BASE, "backend_fastapi", "alumnos", "ml", "modelo_xgb.pkl")
TRAIN_CSV   = os.path.join(BASE, "dataset", "output", "train.csv")
VAL_CSV     = os.path.join(BASE, "dataset", "output", "val.csv")
TEST_CSV    = os.path.join(BASE, "dataset", "output", "test.csv")

FEATURES   = ["edad", "condicion_social", "promedio_notas", "prom_atencion", "prom_hiperactividad"]
TARGET     = "nivel_riesgo_academico"
STR2INT    = {"Bajo": 0, "Medio": 1, "Alto": 2}
INT2STR    = {0: "Bajo", 1: "Medio", 2: "Alto"}
CLASES     = ["Bajo", "Medio", "Alto"]

modelo = joblib.load(MODELO_PATH)

train = pd.read_csv(TRAIN_CSV)
val   = pd.read_csv(VAL_CSV)
test  = pd.read_csv(TEST_CSV)

def prep(df):
    X = df[FEATURES].values
    y = df[TARGET].map(STR2INT).values
    return X, y

X_tr, y_tr = prep(train)
X_va, y_va = prep(val)
X_te, y_te = prep(test)

y_pred_tr = modelo.predict(X_tr)
y_pred_va = modelo.predict(X_va)
y_pred_te = modelo.predict(X_te)
proba_te  = modelo.predict_proba(X_te)   # shape (300, 3): cols = [Bajo, Medio, Alto]

# Convertir a strings para reporte (con orden explícito via labels=)
y_te_s    = [INT2STR[i] for i in y_te]
y_pred_s  = [INT2STR[i] for i in y_pred_te]

acc_tr = accuracy_score(y_tr, y_pred_tr)
acc_va = accuracy_score(y_va, y_pred_va)
acc_te = accuracy_score(y_te, y_pred_te)

auc   = roc_auc_score(y_te, proba_te, multi_class="ovr", average="macro")
kappa = cohen_kappa_score(y_te, y_pred_te)
mcc   = matthews_corrcoef(y_te, y_pred_te)
ll    = log_loss(y_te, proba_te)

SEP = "=" * 62
print(f"\n{SEP}")
print("  METRICAS  XGBoost  |  Prediccion de Riesgo Academico")
print(f"  Modelo: n_estimators={modelo.n_estimators}  max_depth={modelo.max_depth}")
print(f"  Dataset sintetico: 2000 muestras  |  Train 70%  Val 15%  Test 15%")
print(SEP)

print(f"\n  {'Metrica':<30} {'Train':>7}  {'Val':>7}  {'Test':>7}")
print(f"  {'-'*56}")
print(f"  {'Accuracy':<30} {acc_tr:>7.4f}  {acc_va:>7.4f}  {acc_te:>7.4f}")

print(f"\n  Metricas globales sobre Test (n=300):")
print(f"  {'-'*46}")
print(f"  {'AUC-ROC macro OvR':<30} {auc:>10.4f}")
print(f"  {'Cohen Kappa':<30} {kappa:>10.4f}")
print(f"  {'Matthews Corr. Coef. (MCC)':<30} {mcc:>10.4f}")
print(f"  {'Log-Loss':<30} {ll:>10.4f}")

print(f"\n  Reporte por clase (Test):")
print(f"  {'-'*58}")
# labels= fuerza el orden Bajo/Medio/Alto
rep = classification_report(
    y_te_s, y_pred_s,
    labels=CLASES,
    target_names=CLASES,
    digits=4
)
for line in rep.strip().split("\n"):
    print("  " + line)

print(f"\n  Matriz de Confusion  (filas=real  columnas=predicho)")
cm = confusion_matrix(y_te_s, y_pred_s, labels=CLASES)
print("  " + " " * 12 + "".join(f"  Pred {c:<6}" for c in CLASES))
for i, c in enumerate(CLASES):
    print(f"  Real {c:<8}" + "".join(f"  {cm[i,j]:>11}" for j in range(3)))

print(f"\n  Distribucion real en Test:")
for c in CLASES:
    n = (np.array(y_te_s) == c).sum()
    print(f"    {c:<8}: {n:>4}  ({n/len(y_te_s)*100:.1f}%)")

print(f"\n  Importancia de features (XGBoost gain):")
fi = modelo.feature_importances_
for feat, imp in sorted(zip(FEATURES, fi), key=lambda x: -x[1]):
    bar = "#" * int(imp * 40)
    print(f"    {feat:<25} {imp:.4f}  {bar}")

print(f"\n  INTERPRETACION:")
print(f"    - Accuracy en Test ({acc_te:.1%}) vs baseline ingenuo ({max([(np.array(y_te_s)==c).sum()/len(y_te_s) for c in CLASES]):.1%})")
print(f"    - AUC-ROC {auc:.4f} = capacidad discriminativa {'buena' if auc>0.75 else 'moderada' if auc>0.60 else 'baja'}")
print(f"    - Cohen Kappa {kappa:.4f} = acuerdo {'moderado' if kappa>0.4 else 'justo' if kappa>0.2 else 'bajo'}")

print(f"\n{SEP}")
