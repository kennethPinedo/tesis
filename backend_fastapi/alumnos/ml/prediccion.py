import os
import joblib
import numpy as np
from xgboost import XGBClassifier

_MODELO_PATH = os.path.join(os.path.dirname(__file__), "modelo_xgb.pkl")

if os.path.exists(_MODELO_PATH):
    modelo = joblib.load(_MODELO_PATH)
else:
    modelo = XGBClassifier(n_estimators=1, max_depth=1, random_state=42)
    print("AVISO: Modelo no encontrado en alumnos/ml/modelo_xgb.pkl. Se usara un modelo dummy.")


def predecir_riesgo(datos: dict) -> tuple:
    X = np.array([[
        datos["edad"],
        datos["condicion_social"],
        datos["promedio_notas"],
        datos["prom_atencion"],
        datos["prom_hiperactividad"],
    ]])
    prob = modelo.predict_proba(X)[0]
    clase = int(prob.argmax())
    riesgo_map = {0: "Bajo", 1: "Medio", 2: "Alto"}
    return riesgo_map[clase], float(prob[clase])
