def codificar_condicion_social(valor: str) -> int:
    if not valor:
        return 0
    mapa = {
        "ningún problema": 0,
        "ninguna": 0,
        "leve": 1,
        "moderado": 2,
        "moderada": 2,
        "grave": 3,
    }
    return mapa.get(valor.lower().strip(), 0)


def etiquetar_riesgo(promedio: float) -> int:
    if promedio >= 15:
        return 0
    elif promedio >= 12:
        return 1
    return 2
