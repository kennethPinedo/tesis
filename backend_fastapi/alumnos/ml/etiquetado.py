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
