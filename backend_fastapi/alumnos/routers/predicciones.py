from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
from database import get_db
from alumnos.models import Alumno, Nota, Encuesta, PrediccionAcademica
from alumnos.ml.etiquetado import codificar_condicion_social
from alumnos.ml.prediccion import predecir_tdah

router = APIRouter()

_MAPEO_NOTAS = {"AD": 20, "A": 17, "B": 14, "C": 11}


def _nivel_riesgo_academico(promedio_notas: float, condicion_social: int,
                             edah_tdah_total: int) -> str:
    """
    Replica la formula del dataset para nivel_riesgo_academico:
      score = 0.45*tdah_prob + 0.40*(1-notas/20) + 0.15*(cond/3)
    Se aproxima tdah_prob = edah_tdah_total / 30.
    """
    tdah_prob = min(edah_tdah_total / 30.0, 1.0)
    s = 0.45 * tdah_prob + 0.40 * (1.0 - promedio_notas / 20.0) + 0.15 * (condicion_social / 3.0)
    if s < 0.28:
        return "Bajo"
    elif s < 0.55:
        return "Medio"
    return "Alto"


class GenerarPrediccionIn(BaseModel):
    alumno: int


def _pred_dict(p: PrediccionAcademica, alumno_nombre: str = None) -> dict:
    return {
        "id"                        : p.id,
        "alumno"                    : p.alumno_id,
        "alumno_nombre"             : alumno_nombre,
        "promedio_notas"            : p.promedio_notas,
        "nivel_riesgo"              : p.nivel_riesgo,
        "probabilidad"              : p.probabilidad,
        "prediccion_notas"          : p.prediccion_notas,
        "condiciones_psicoeducativas": p.condiciones_psicoeducativas,
        "explicacion_xai"           : p.explicacion_xai,
        "fecha_prediccion"          : p.fecha_prediccion.isoformat() if p.fecha_prediccion else None,
    }


@router.get("/predicciones/")
def list_predicciones(alumno: Optional[int] = None, db: Session = Depends(get_db)):
    q = db.query(PrediccionAcademica).order_by(PrediccionAcademica.fecha_prediccion.desc())
    if alumno:
        q = q.filter(PrediccionAcademica.alumno_id == alumno)
    result = []
    for p in q.all():
        a = db.query(Alumno).filter(Alumno.id == p.alumno_id).first()
        nombre = f"{a.nombre} {a.apellido}" if a else None
        result.append(_pred_dict(p, nombre))
    return result


@router.post("/predicciones/generar/")
def generar_prediccion(data: GenerarPrediccionIn, db: Session = Depends(get_db)):
    alumno_id = data.alumno
    alumno = db.query(Alumno).filter(Alumno.id == alumno_id).first()
    if not alumno:
        raise HTTPException(status_code=404, detail="Alumno no encontrado.")

    notas = db.query(Nota).filter(Nota.alumno_id == alumno_id).all()
    if not notas:
        raise HTTPException(status_code=400,
                            detail="No se pudo generar prediccion. Verifique notas y encuesta.")

    promedio_notas = sum(_MAPEO_NOTAS.get(n.calificacion_literal, 0) for n in notas) / len(notas)

    encuesta = (
        db.query(Encuesta)
        .filter(Encuesta.alumno_id == alumno_id)
        .order_by(Encuesta.fecha_aplicacion.desc())
        .first()
    )
    if not encuesta:
        raise HTTPException(status_code=400,
                            detail="No se pudo generar prediccion. Verifique notas y encuesta.")

    # EDAH totals (para calcular nivel_riesgo_academico)
    edah_da_total   = sum(getattr(encuesta, f"A{i}") for i in range(1, 6))
    edah_h_total    = sum(getattr(encuesta, f"B{i}") for i in range(1, 6))
    edah_tdah_total = edah_da_total + edah_h_total

    condicion_cod = codificar_condicion_social(alumno.condicion_social)

    # Calcular nivel_riesgo_academico para usarlo como feature del modelo
    nivel_riesgo = _nivel_riesgo_academico(promedio_notas, condicion_cod, edah_tdah_total)

    # Convertir grado a entero
    try:
        grado_num = int(str(alumno.grado).strip().replace("°", "").replace("mo", "").replace("vo", "").replace("no", ""))
    except ValueError:
        grado_num = 7

    # Genero one-hot
    genero_m = 1 if str(alumno.genero).strip().upper() in ("M", "MASCULINO", "HOMBRE") else 0

    resultado, prob_tdah, explicacion = predecir_tdah({
        "edad"           : alumno.edad,
        "grado"          : grado_num,
        "condicion_social": condicion_cod,
        "promedio_notas" : promedio_notas,
        "genero_M"       : genero_m,
        "edah_da_total"  : edah_da_total,
        "edah_h_total"   : edah_h_total,
    })

    condiciones_texto = (
        f"EDAH-DA (atencion): {edah_da_total}/15 | "
        f"EDAH-H (hiperactividad): {edah_h_total}/15 | "
        f"EDAH-TDAH (total): {edah_tdah_total}/30 | "
        f"Riesgo academico: {nivel_riesgo} | "
        f"Promedio notas: {promedio_notas:.2f}"
    )


    pred = (
        db.query(PrediccionAcademica)
        .filter(PrediccionAcademica.alumno_id == alumno_id)
        .first()
    )
    if pred:
        pred.promedio_notas              = promedio_notas
        pred.nivel_riesgo                = nivel_riesgo
        pred.probabilidad                = prob_tdah
        pred.prediccion_notas            = f"{promedio_notas:.2f}"
        pred.condiciones_psicoeducativas = condiciones_texto
        pred.explicacion_xai             = explicacion
    else:
        pred = PrediccionAcademica(
            alumno_id               =alumno_id,
            promedio_notas          =promedio_notas,
            nivel_riesgo            =nivel_riesgo,
            probabilidad            =prob_tdah,
            prediccion_notas        =f"{promedio_notas:.2f}",
            condiciones_psicoeducativas=condiciones_texto,
            explicacion_xai         =explicacion,
        )
        db.add(pred)

    db.commit()
    db.refresh(pred)
    result = _pred_dict(pred, f"{alumno.nombre} {alumno.apellido}")
    result["edah_da_total"]   = edah_da_total
    result["edah_h_total"]    = edah_h_total
    result["edah_tdah_total"] = edah_tdah_total
    result["tdah_resultado"]  = resultado
    result["tdah_presente"]   = 1 if resultado == "Con TDAH" else 0
    return result
