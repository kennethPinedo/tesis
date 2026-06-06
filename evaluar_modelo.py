import os, warnings
warnings.filterwarnings("ignore")

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score, classification_report, confusion_matrix,
    roc_auc_score, recall_score, f1_score,
    cohen_kappa_score, matthews_corrcoef, log_loss
)

BASE        = os.path.dirname(__file__)
MODELO_PATH = os.path.join(BASE, "backend_fastapi", "alumnos", "ml", "modelo_xgb.pkl")
TRAIN_CSV   = os.path.join(BASE, "dataset", "output", "train.csv")
VAL_CSV     = os.path.join(BASE, "dataset", "output", "val.csv")
TEST_CSV    = os.path.join(BASE, "dataset", "output", "test.csv")

TARGET = "tdah_presente"

modelo = joblib.load(MODELO_PATH)
train  = pd.read_csv(TRAIN_CSV)
val    = pd.read_csv(VAL_CSV)
test   = pd.read_csv(TEST_CSV)

FEATURE_COLS = [c for c in train.columns if c != TARGET]

def prep(df):
    return df[FEATURE_COLS].values, df[TARGET].values

X_tr, y_tr = prep(train)
X_va, y_va = prep(val)
X_te, y_te = prep(test)

yp_tr   = modelo.predict(X_tr)
yp_va   = modelo.predict(X_va)
yp_te   = modelo.predict(X_te)
prob_te = modelo.predict_proba(X_te)[:, 1]

SEP = "=" * 62
print(f"\n{SEP}")
print("  METRICAS XGBoost  |  Prediccion TDAH  (binario)")
print(f"  Modelo: n_estimators={modelo.n_estimators}  max_depth={modelo.max_depth}")
print(f"  Dataset: {len(train)+len(val)+len(test)} registros  |  "
      f"Train {len(train)}  Val {len(val)}  Test {len(test)}")
print(SEP)

print(f"\n  {'Metrica':<25} {'Train':>8}  {'Val':>8}  {'Test':>8}")
print(f"  {'-'*52}")
print(f"  {'Accuracy':<25} {accuracy_score(y_tr,yp_tr):>8.4f}  "
      f"{accuracy_score(y_va,yp_va):>8.4f}  {accuracy_score(y_te,yp_te):>8.4f}")
print(f"  {'Recall (TDAH=1)':<25} {recall_score(y_tr,yp_tr):>8.4f}  "
      f"{recall_score(y_va,yp_va):>8.4f}  {recall_score(y_te,yp_te):>8.4f}")
print(f"  {'F1-score':<25} {f1_score(y_tr,yp_tr):>8.4f}  "
      f"{f1_score(y_va,yp_va):>8.4f}  {f1_score(y_te,yp_te):>8.4f}")

print(f"\n  Metricas globales sobre Test (n={len(y_te)}):")
print(f"  {'-'*46}")
auc   = roc_auc_score(y_te, prob_te)
kappa = cohen_kappa_score(y_te, yp_te)
mcc   = matthews_corrcoef(y_te, yp_te)
ll    = log_loss(y_te, prob_te)
print(f"  {'AUC-ROC':<30} {auc:>10.4f}")
print(f"  {'Cohen Kappa':<30} {kappa:>10.4f}")
print(f"  {'Matthews MCC':<30} {mcc:>10.4f}")
print(f"  {'Log-Loss':<30} {ll:>10.4f}")

print(f"\n  Reporte por clase (Test):")
print(f"  {'-'*54}")
rep = classification_report(y_te, yp_te, target_names=['Sin TDAH', 'Con TDAH'], digits=4)
for line in rep.strip().split("\n"):
    print("  " + line)

print(f"\n  Matriz de Confusion  (filas=real  columnas=predicho)")
cm = confusion_matrix(y_te, yp_te)
print(f"               Pred Sin TDAH   Pred Con TDAH")
print(f"  Real Sin TDAH    {cm[0,0]:>9}       {cm[0,1]:>9}")
print(f"  Real Con TDAH    {cm[1,0]:>9}       {cm[1,1]:>9}")

print(f"\n  Distribucion en Test:")
for lbl, nombre in [(0,'Sin TDAH'), (1,'Con TDAH')]:
    n = (y_te == lbl).sum()
    print(f"    {nombre:<12}: {n:>4}  ({n/len(y_te)*100:.1f}%)")

print(f"\n  Importancia de features (XGBoost gain):")
fi = modelo.feature_importances_
for feat, imp in sorted(zip(FEATURE_COLS, fi), key=lambda x: -x[1]):
    bar = "#" * int(imp * 40)
    print(f"    {feat:<35} {imp:.4f}  {bar}")

baseline = max((y_te == 0).sum(), (y_te == 1).sum()) / len(y_te)
print(f"\n  INTERPRETACION:")
print(f"    - Accuracy Test ({accuracy_score(y_te,yp_te):.1%}) vs baseline ingenuo ({baseline:.1%})")
print(f"    - AUC-ROC {auc:.4f} = capacidad discriminativa "
      f"{'excelente' if auc>0.90 else 'buena' if auc>0.75 else 'moderada'}")
print(f"    - Recall {recall_score(y_te,yp_te):.4f} = "
      f"detecta {recall_score(y_te,yp_te)*100:.1f}% de alumnos con TDAH")
print(f"    - Cohen Kappa {kappa:.4f} = acuerdo "
      f"{'sustancial' if kappa>0.6 else 'moderado' if kappa>0.4 else 'justo'}")
print(f"\n{SEP}")
