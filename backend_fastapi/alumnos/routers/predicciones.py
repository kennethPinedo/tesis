from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
from database import get_db
from alumnos.models import Alumno, Nota, Encuesta, PrediccionAcademica
from alumnos.ml.etiquetado import codificar_condicion_social
from alumnos.ml.prediccion import predecir_riesgo

router = APIRouter()

_MAPEO_NOTAS = {"AD": 20, "A": 17, "B": 14, "C": 11}


class GenerarPrediccionIn(BaseModel):
    alumno: int


def _pred_dict(p: PrediccionAcademica, alumno_nombre: str = None) -> dict:
    cond = p.condiciones_psicoeducativas or ""
    total_atencion = None
    total_hiperactividad = None
    for part in cond.split("|"):
        part = part.strip()
        if part.startswith("Atención (total):"):
            try:
                total_atencion = int(part.split(":")[1].strip().split("/")[0])
            except Exception:
                pass
        elif part.startswith("Hiperactividad (total):"):
            try:
                total_hiperactividad = int(part.split(":")[1].strip().split("/")[0])
            except Exception:
                pass
    if total_atencion is not None and total_hiperactividad is not None:
        if total_atencion >= 14 and total_hiperactividad >= 14:
            nivel_tdah = "Posible TDAH - Tipo Combinado"
        elif total_atencion >= 14:
            nivel_tdah = "Posible TDAH - Déficit de Atención"
        elif total_hiperactividad >= 14:
            nivel_tdah = "Posible TDAH - Hiperactividad/Impulsividad"
        else:
            nivel_tdah = "Sin indicadores significativos de TDAH"
    else:
        nivel_tdah = None
    return {
        "id": p.id,
        "alumno": p.alumno_id,
        "alumno_nombre": alumno_nombre,
        "promedio_notas": p.promedio_notas,
        "nivel_riesgo": p.nivel_riesgo,
        "probabilidad": p.probabilidad,
        "prediccion_notas": p.prediccion_notas,
        "condiciones_psicoeducativas": p.condiciones_psicoeducativas,
        "fecha_prediccion": p.fecha_prediccion.isoformat() if p.fecha_prediccion else None,
        "nivel_tdah": nivel_tdah,
        "total_atencion": total_atencion,
        "total_hiperactividad": total_hiperactividad,
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
        raise HTTPException(
            status_code=400,
            detail="No se pudo generar prediccion. Verifique notas y encuesta.",
        )

    valores = [_MAPEO_NOTAS.get(n.calificacion_literal, 0) for n in notas]
    promedio_notas = sum(valores) / len(valores)

    encuesta = (
        db.query(Encuesta)
        .filter(Encuesta.alumno_id == alumno_id)
        .order_by(Encuesta.fecha_aplicacion.desc())
        .first()
    )
    if not encuesta:
        raise HTTPException(
            status_code=400,
            detail="No se pudo generar prediccion. Verifique notas y encuesta.",
        )

    total_atencion = sum(getattr(encuesta, f"A{i}") for i in range(1, 11))
    total_hiperactividad = sum(getattr(encuesta, f"B{i}") for i in range(1, 11))
    prom_atencion = total_atencion / 10
    prom_hiperactividad = total_hiperactividad / 10
    condicion_codificada = codificar_condicion_social(alumno.condicion_social)

    riesgo, probabilidad = predecir_riesgo({
        "edad": alumno.edad,
        "condicion_social": condicion_codificada,
        "promedio_notas": promedio_notas,
        "prom_atencion": prom_atencion,
        "prom_hiperactividad": prom_hiperactividad,
    })

    tiene_atencion = total_atencion >= 14
    tiene_hiperactividad = total_hiperactividad >= 14
    if tiene_atencion and tiene_hiperactividad:
        nivel_tdah = "Posible TDAH - Tipo Combinado"
    elif tiene_atencion:
        nivel_tdah = "Posible TDAH - Déficit de Atención"
    elif tiene_hiperactividad:
        nivel_tdah = "Posible TDAH - Hiperactividad/Impulsividad"
    else:
        nivel_tdah = "Sin indicadores significativos de TDAH"

    condiciones_texto = (
        f"Atención (total): {total_atencion}/30 | "
        f"Hiperactividad (total): {total_hiperactividad}/30 | "
        f"Condición social: {alumno.condicion_social} | "
        f"Promedio notas: {promedio_notas:.2f}"
    )

    pred = (
        db.query(PrediccionAcademica)
        .filter(PrediccionAcademica.alumno_id == alumno_id)
        .first()
    )
    if pred:
        pred.promedio_notas = promedio_notas
        pred.nivel_riesgo = riesgo
        pred.probabilidad = probabilidad
        pred.prediccion_notas = f"{promedio_notas:.2f}"
        pred.condiciones_psicoeducativas = condiciones_texto
    else:
        pred = PrediccionAcademica(
            alumno_id=alumno_id,
            promedio_notas=promedio_notas,
            nivel_riesgo=riesgo,
            probabilidad=probabilidad,
            prediccion_notas=f"{promedio_notas:.2f}",
            condiciones_psicoeducativas=condiciones_texto,
        )
        db.add(pred)

    db.commit()
    db.refresh(pred)
    result = _pred_dict(pred, f"{alumno.nombre} {alumno.apellido}")
    result["nivel_tdah"] = nivel_tdah
    result["total_atencion"] = total_atencion
    result["total_hiperactividad"] = total_hiperactividad
    return result
