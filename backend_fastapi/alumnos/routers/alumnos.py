from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import get_db
from alumnos.models import Alumno

router = APIRouter()


class AlumnoCreate(BaseModel):
    nombre: str
    apellido: str
    edad: int
    grado: str
    anio_cursada: int = 2024
    contacto_emergente: str
    condicion_social: str = "NINGUNA"
    genero: str = "No especificado"


def _alumno_dict(a: Alumno) -> dict:
    return {
        "id": a.id,
        "nombre": a.nombre,
        "apellido": a.apellido,
        "edad": a.edad,
        "grado": a.grado,
        "anio_cursada": a.anio_cursada,
        "contacto_emergente": a.contacto_emergente,
        "condicion_social": a.condicion_social,
        "genero": a.genero,
    }


@router.get("/alumnos/")
def list_alumnos(db: Session = Depends(get_db)):
    return [_alumno_dict(a) for a in db.query(Alumno).all()]


@router.post("/alumnos/", status_code=201)
def create_alumno(data: AlumnoCreate, db: Session = Depends(get_db)):
    a = Alumno(**data.model_dump())
    db.add(a)
    db.commit()
    db.refresh(a)
    return _alumno_dict(a)


@router.get("/alumnos/{alumno_id}/")
def get_alumno(alumno_id: int, db: Session = Depends(get_db)):
    a = db.query(Alumno).filter(Alumno.id == alumno_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="Alumno no encontrado.")
    return _alumno_dict(a)


@router.put("/alumnos/{alumno_id}/")
def update_alumno(alumno_id: int, data: AlumnoCreate, db: Session = Depends(get_db)):
    a = db.query(Alumno).filter(Alumno.id == alumno_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="Alumno no encontrado.")
    for k, v in data.model_dump().items():
        setattr(a, k, v)
    db.commit()
    db.refresh(a)
    return _alumno_dict(a)


@router.delete("/alumnos/{alumno_id}/", status_code=204)
def delete_alumno(alumno_id: int, db: Session = Depends(get_db)):
    a = db.query(Alumno).filter(Alumno.id == alumno_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="Alumno no encontrado.")
    db.delete(a)
    db.commit()
