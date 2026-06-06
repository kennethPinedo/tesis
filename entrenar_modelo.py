import os, warnings, time
warnings.filterwarnings("ignore")

import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, RandomizedSearchCV, StratifiedKFold
from sklearn.metrics import (
    classification_report, confusion_matrix,
    recall_score, roc_auc_score, f1_score, accuracy_score
)
from xgboost import XGBClassifier

BASE        = os.path.dirname(__file__)
DATASET_CSV = os.path.join(BASE, "dataset", "output", "dataset_tdah_completo (1).csv")
MODELO_PATH = os.path.join(BASE, "backend_fastapi", "alumnos", "ml", "modelo_xgb.pkl")
TRAIN_CSV   = os.path.join(BASE, "dataset", "output", "train.csv")
VAL_CSV     = os.path.join(BASE, "dataset", "output", "val.csv")
TEST_CSV    = os.path.join(BASE, "dataset", "output", "test.csv")

SEP = "=" * 64

# ── Cargar dataset ────────────────────────────────────────────────────────────
print(f"\n{SEP}")
print("  CARGA Y PREPARACION DEL DATASET")
print(SEP)

data = pd.read_csv(DATASET_CSV, sep=";")
print(f"  Dataset: {data.shape[0]} registros, {data.shape[1]} columnas")
print(f"  tdah_presente:\n{data['tdah_presente'].value_counts().to_string()}")

# ── Feature engineering (igual que notebook) ─────────────────────────────────
COLS_ELIMINAR = [
    'id', 'tdah_presente', 'tdah_probabilidad', 'split',
    'edah_h1','edah_h2','edah_h3','edah_h4','edah_h5',
    'edah_da1','edah_da2','edah_da3','edah_da4','edah_da5',
    'edah_tc1','edah_tc2','edah_tc3','edah_tc4','edah_tc5',
    'edah_tc6','edah_tc7','edah_tc8','edah_tc9','edah_tc10',
    'edah_tdah_total','edah_tc_total',
    'conners_hiperact_tscore','conners_inatencion_tscore',
    'conners_oposicion_tscore','conners_adhd_index_tscore',
    'prom_atencion','prom_hiperactividad',
    'nivel_riesgo_academico',
]

X = data.drop(columns=COLS_ELIMINAR)
y = data['tdah_presente']

X = pd.get_dummies(X, columns=['genero'], drop_first=True)

# Garantizar columnas exactas en el orden correcto
FEATURE_COLS = ['edad', 'grado', 'condicion_social', 'promedio_notas',
                'genero_M', 'edah_da_total', 'edah_h_total']
for col in FEATURE_COLS:
    if col not in X.columns:
        X[col] = 0
X = X[FEATURE_COLS]

print(f"  Features ({len(FEATURE_COLS)}): {FEATURE_COLS}")
print(f"  Target  : tdah_presente  (0=Sin TDAH, 1=Con TDAH)")

# ── Division 60 / 20 / 20 estratificada ──────────────────────────────────────
print(f"\n{SEP}")
print("  DIVISION  60% train  /  20% val  /  20% test  (estratificada)")
print(SEP)

X_trainval, X_test, y_trainval, y_test = train_test_split(
    X, y, test_size=0.20, random_state=42, stratify=y
)
X_train, X_val, y_train, y_val = train_test_split(
    X_trainval, y_trainval, test_size=0.25, random_state=42, stratify=y_trainval
)

print(f"\n  Train : {X_train.shape[0]} muestras  "
      f"(TDAH={y_train.sum()}, Sin TDAH={( y_train==0).sum()})")
print(f"  Val   : {X_val.shape[0]} muestras  "
      f"(TDAH={y_val.sum()}, Sin TDAH={(y_val==0).sum()})")
print(f"  Test  : {X_test.shape[0]} muestras  "
      f"(TDAH={y_test.sum()}, Sin TDAH={(y_test==0).sum()})")

df_train = X_train.copy(); df_train['tdah_presente'] = y_train.values
df_val   = X_val.copy();   df_val['tdah_presente']   = y_val.values
df_test  = X_test.copy();  df_test['tdah_presente']  = y_test.values
df_train.to_csv(TRAIN_CSV, index=False)
df_val.to_csv(VAL_CSV,     index=False)
df_test.to_csv(TEST_CSV,   index=False)
print(f"\n  Splits guardados en dataset/output/")

# ── RandomizedSearchCV (metrica: recall) ─────────────────────────────────────
print(f"\n{SEP}")
print("  FASE 1: RandomizedSearchCV  (metrica=recall, 5-fold CV, 50 iter)")
print(SEP)

param_grid = {
    'n_estimators'    : np.arange(50, 300, 50),
    'max_depth'       : [3, 4, 5, 6],
    'learning_rate'   : [0.01, 0.05, 0.1],
    'subsample'       : np.linspace(0.6, 1.0, 4),
    'colsample_bytree': np.linspace(0.6, 1.0, 4),
    'reg_alpha'       : [0, 0.1, 1, 5],
    'reg_lambda'      : [1, 5, 10],
    'min_child_weight': [1, 3, 5, 10],
}

skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

xgb_base = XGBClassifier(
    objective         ='binary:logistic',
    eval_metric       =['logloss', 'auc'],
    random_state      =42,
    enable_categorical=False,
    n_jobs            =-1,
)

random_search = RandomizedSearchCV(
    estimator           =xgb_base,
    param_distributions =param_grid,
    cv                  =skf,
    n_iter              =50,
    n_jobs              =-1,
    scoring             ='recall',
    random_state        =42,
    verbose             =1,
)

print("\n  Iniciando busqueda...")
t0 = time.time()
random_search.fit(X_train, y_train)
print(f"  Completado en {time.time()-t0:.1f}s")
print(f"\n  Mejor recall CV: {random_search.best_score_:.4f}")
print("  Mejores parametros:")
best_params = random_search.best_params_
for k, v in best_params.items():
    print(f"    {k:<22}: {v}")

# ── Entrenamiento con early stopping sobre validacion ────────────────────────
print(f"\n{SEP}")
print("  FASE 2: Early stopping  (eval_set=val, early_stopping_rounds=10)")
print(SEP)

params_es = best_params.copy()
params_es.pop('n_estimators', None)

xgb_es = XGBClassifier(
    **params_es,
    n_estimators          =500,
    objective             ='binary:logistic',
    eval_metric           =['auc', 'logloss'],
    early_stopping_rounds =10,
    random_state          =42,
    enable_categorical    =False,
    verbosity             =0,
)
xgb_es.fit(
    X_train, y_train,
    eval_set=[(X_train, y_train), (X_val, y_val)],
    verbose=False,
)
best_iter = xgb_es.best_iteration
print(f"\n  Mejor iteracion (early stopping): {best_iter}")

# ── Modelo final: train + val, n_estimators = best_iter + 1 ──────────────────
print(f"\n{SEP}")
print("  FASE 3: Modelo final  (train+val, n_estimators={best_iter+1})")
print(SEP)

final_model = XGBClassifier(
    **params_es,
    n_estimators      =best_iter + 1,
    objective         ='binary:logistic',
    random_state      =42,
    enable_categorical=False,
)
final_model.fit(X_trainval, y_trainval)
print("  Modelo final entrenado.")

# ── Evaluacion en los tres splits ────────────────────────────────────────────
print(f"\n{SEP}")
print("  FASE 4: Metricas en Train / Val / Test")
print(SEP)

def metricas(mdl, X, y, nombre):
    yp  = mdl.predict(X)
    acc = accuracy_score(y, yp)
    rec = recall_score(y, yp)
    f1  = f1_score(y, yp)
    print(f"\n  [{nombre}]  n={len(y)}  (TDAH={y.sum()}, Sin TDAH={(y==0).sum()})")
    print(f"  Accuracy : {acc:.4f}")
    print(f"  Recall   : {rec:.4f}  <- evitar falsos negativos")
    print(f"  F1-score : {f1:.4f}")
    print(f"  Matriz de confusion:")
    cm = confusion_matrix(y, yp)
    print(f"             Pred 0  Pred 1")
    print(f"  Real 0      {cm[0,0]:>5}   {cm[0,1]:>5}")
    print(f"  Real 1      {cm[1,0]:>5}   {cm[1,1]:>5}")
    print(f"  Reporte completo:")
    print(classification_report(y, yp, target_names=['Sin TDAH', 'Con TDAH']))
    return acc, rec, f1

acc_tr, rec_tr, f1_tr = metricas(final_model, X_train,    y_train,    "TRAIN")
acc_va, rec_va, f1_va = metricas(final_model, X_val,      y_val,      "VAL")
acc_te, rec_te, f1_te = metricas(final_model, X_test,     y_test,     "TEST")
auc_te = roc_auc_score(y_test, final_model.predict_proba(X_test)[:,1])

print(f"\n{SEP}")
print("  RESUMEN FINAL")
print(SEP)
print(f"\n  {'Metrica':<18} {'Train':>8}  {'Val':>8}  {'Test':>8}")
print(f"  {'-'*46}")
print(f"  {'Accuracy':<18} {acc_tr:>8.4f}  {acc_va:>8.4f}  {acc_te:>8.4f}")
print(f"  {'Recall':<18} {rec_tr:>8.4f}  {rec_va:>8.4f}  {rec_te:>8.4f}")
print(f"  {'F1-score':<18} {f1_tr:>8.4f}  {f1_va:>8.4f}  {f1_te:>8.4f}")
print(f"  {'AUC-ROC (test)':<18} {'':>8}  {'':>8}  {auc_te:>8.4f}")

print(f"\n  Importancia de features (XGBoost gain):")
fi = final_model.feature_importances_
for feat, imp in sorted(zip(FEATURE_COLS, fi), key=lambda x: -x[1]):
    bar = "#" * int(imp * 40)
    print(f"    {feat:<35} {imp:.4f}  {bar}")

# ── Guardar modelo y metadata ─────────────────────────────────────────────────
print(f"\n{SEP}")
print("  FASE 5: Guardando modelo")
print(SEP)

joblib.dump(final_model, MODELO_PATH)

# Guardar metadata de features para el backend
META_PATH = os.path.join(BASE, "backend_fastapi", "alumnos", "ml", "modelo_meta.json")
import json
meta = {
    "features"      : FEATURE_COLS,
    "target"        : "tdah_presente",
    "clases"        : {0: "Sin TDAH", 1: "Con TDAH"},
    "n_estimators"  : best_iter + 1,
    "best_recall_cv": float(random_search.best_score_),
    "test_accuracy" : float(acc_te),
    "test_recall"   : float(rec_te),
    "test_auc"      : float(auc_te),
}
with open(META_PATH, "w") as f:
    json.dump(meta, f, indent=2)

print(f"\n  Modelo guardado  : {MODELO_PATH}")
print(f"  Metadata guardada: {META_PATH}")
print(f"\n  Accuracy Test : {acc_te:.4f}")
print(f"  Recall   Test : {rec_te:.4f}")
print(f"  AUC-ROC  Test : {auc_te:.4f}")
print(f"\n{SEP}\n")
