import os
import joblib
import numpy as np
import shap
from xgboost import XGBClassifier

_DIR         = os.path.dirname(__file__)
_MODELO_PATH = os.path.join(_DIR, "modelo_xgb.pkl")

if os.path.exists(_MODELO_PATH):
    modelo = joblib.load(_MODELO_PATH)
else:
    modelo = XGBClassifier(n_estimators=1, max_depth=1, random_state=42)
    print("AVISO: modelo_xgb.pkl no encontrado. Se usara un modelo dummy.")

_explainer = shap.TreeExplainer(modelo)

_FEATURES = [
    'edad',
    'grado',
    'condicion_social',
    'promedio_notas',
    'genero_M',
    'edah_da_total',
    'edah_h_total',
]

_CLASES = {0: "Sin TDAH", 1: "Con TDAH"}

_NOMBRES = {
    'edah_da_total'  : "deficit de atencion EDAH",
    'edah_h_total'   : "hiperactividad EDAH",
    'promedio_notas' : "promedio de notas",
    'condicion_social': "condicion socioeconomica",
    'edad'           : "edad",
    'grado'          : "grado escolar",
    'genero_M'       : "genero masculino",
}

_VALORES_LEGIBLES = {
    'edah_da_total'  : lambda v: f"{int(v)}/15",
    'edah_h_total'   : lambda v: f"{int(v)}/15",
    'genero_M'       : lambda v: "Si" if v else "No",
    'condicion_social': lambda v: ["ninguna", "leve", "moderada", "grave"][int(v)] if 0 <= int(v) <= 3 else str(v),
    'promedio_notas' : lambda v: f"{v:.1f}/20",
    'edad'           : lambda v: f"{int(v)} anios",
    'grado'          : lambda v: f"{int(v)}",
}


def _explicacion_texto(shap_vals: np.ndarray, valores: dict, prob_tdah: float) -> str:
    pares = list(zip(_FEATURES, shap_vals))
    pares_ordenados = sorted(pares, key=lambda x: abs(x[1]), reverse=True)

    factores_riesgo    = [(f, v) for f, v in pares_ordenados if v > 0.01]
    factores_protector = [(f, v) for f, v in pares_ordenados if v < -0.01]

    porcentaje = round(prob_tdah * 100, 1)
    if prob_tdah < 0.35:
        nivel = "bajo"
    elif prob_tdah < 0.60:
        nivel = "moderado"
    else:
        nivel = "alto"

    lineas = [
        f"El modelo estima una probabilidad de TDAH del {porcentaje}%, lo que indica un riesgo {nivel}."
    ]

    if factores_protector:
        tops = factores_protector[:2]
        desc = " y ".join(
            f"{_NOMBRES[f]} ({_VALORES_LEGIBLES[f](valores.get(f, 0))})"
            for f, _ in tops
        )
        lineas.append(f"Los factores que reducen el riesgo son: {desc}.")

    if factores_riesgo:
        tops = factores_riesgo[:2]
        desc = " y ".join(
            f"{_NOMBRES[f]} ({_VALORES_LEGIBLES[f](valores.get(f, 0))})"
            for f, _ in tops
        )
        lineas.append(f"Los factores que incrementan el riesgo son: {desc}.")

    if not factores_riesgo and not factores_protector:
        lineas.append("No se identificaron factores dominantes en esta prediccion.")

    return " ".join(lineas)


def predecir_tdah(datos: dict) -> tuple[str, float, str]:
    X = np.array([[datos.get(f, 0) for f in _FEATURES]], dtype=float)

    prob       = modelo.predict_proba(X)[0]
    clase      = int(prob.argmax())
    prob_tdah  = float(prob[1])

    shap_vals  = _explainer.shap_values(X)[0]
    explicacion = _explicacion_texto(shap_vals, datos, prob_tdah)

    return _CLASES[clase], prob_tdah, explicacion
