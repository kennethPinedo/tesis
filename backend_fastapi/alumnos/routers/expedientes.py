import os
import shutil
from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session
from typing import Optional
from database import get_db
from alumnos.models import ExpedientePsicologico

router = APIRouter()

# Sube tres niveles: routers/ -> alumnos/ -> backend_fastapi/
_UPLOAD_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "media", "expedientes"
)
os.makedirs(_UPLOAD_DIR, exist_ok=True)


def _exp_dict(e: ExpedientePsicologico) -> dict:
    return {
        "id": e.id,
        "alumno": e.alumno_id,
        "nivel_preocupacion": e.nivel_preocupacion,
        "archivo_pdf": e.archivo_pdf,
        "fecha_registro": e.fecha_registro.isoformat() if e.fecha_registro else None,
    }


@router.get("/expedientes/")
def list_expedientes(alumno: Optional[int] = None, db: Session = Depends(get_db)):
    q = db.query(ExpedientePsicologico).order_by(ExpedientePsicologico.fecha_registro.desc())
    if alumno:
        q = q.filter(ExpedientePsicologico.alumno_id == alumno)
    return [_exp_dict(e) for e in q.all()]


@router.post("/expedientes/", status_code=201)
async def create_expediente(
    alumno: int = Form(...),
    nivel_preocupacion: int = Form(...),
    archivo_pdf: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    filename = f"{alumno}_{archivo_pdf.filename}"
    filepath = os.path.join(_UPLOAD_DIR, filename)
    with open(filepath, "wb") as f:
        shutil.copyfileobj(archivo_pdf.file, f)

    e = ExpedientePsicologico(
        alumno_id=alumno,
        nivel_preocupacion=nivel_preocupacion,
        archivo_pdf=f"expedientes/{filename}",
    )
    db.add(e)
    db.commit()
    db.refresh(e)
    return _exp_dict(e)
