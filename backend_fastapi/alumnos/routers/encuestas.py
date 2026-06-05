from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
from database import get_db
from alumnos.models import Encuesta

router = APIRouter()

_KEYS_A = [f"A{i}" for i in range(1, 11)]
_KEYS_B = [f"B{i}" for i in range(1, 11)]
_ALL_KEYS = _KEYS_A + _KEYS_B


class EncuestaCreate(BaseModel):
    alumno: int
    A1: int; A2: int; A3: int; A4: int; A5: int
    A6: int; A7: int; A8: int; A9: int; A10: int
    B1: int; B2: int; B3: int; B4: int; B5: int
    B6: int; B7: int; B8: int; B9: int; B10: int


def _encuesta_dict(e: Encuesta) -> dict:
    d = {"id": e.id, "alumno": e.alumno_id}
    for k in _ALL_KEYS:
        d[k] = getattr(e, k)
    d["fecha_aplicacion"] = str(e.fecha_aplicacion) if e.fecha_aplicacion else None
    return d


@router.get("/encuestas/")
def list_encuestas(alumno: Optional[int] = None, db: Session = Depends(get_db)):
    q = db.query(Encuesta).order_by(Encuesta.fecha_aplicacion.desc())
    if alumno:
        q = q.filter(Encuesta.alumno_id == alumno)
    return [_encuesta_dict(e) for e in q.all()]


@router.post("/encuestas/", status_code=201)
def create_encuesta(data: EncuestaCreate, db: Session = Depends(get_db)):
    d = data.model_dump()
    alumno_id = d.pop("alumno")
    e = Encuesta(alumno_id=alumno_id, **d)
    db.add(e)
    db.commit()
    db.refresh(e)
    return _encuesta_dict(e)
