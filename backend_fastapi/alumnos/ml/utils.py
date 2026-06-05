MAPA_NOTAS = {"AD": 20, "A": 17, "B": 14, "C": 11}


def convertir_nota_a_numero(nota_literal: str) -> int:
    return MAPA_NOTAS.get(nota_literal, 0)


def promedio_a_literal(promedio: float) -> str:
    if promedio >= 18:
        return "AD"
    elif promedio >= 16:
        return "A"
    elif promedio >= 13:
        return "B"
    return "C"
