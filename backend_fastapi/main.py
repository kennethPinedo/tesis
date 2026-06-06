from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
import os

from database import engine, Base
import alumnos.models  # noqa: F401 — registra todos los modelos ORM antes de create_all
from alumnos.routers import alumnos, encuestas, notas, predicciones, expedientes

Base.metadata.create_all(bind=engine)

with engine.connect() as _conn:
    for _sql in [
        "ALTER TABLE alumnos ADD COLUMN genero VARCHAR(20) DEFAULT 'No especificado'",
        "ALTER TABLE predicciones ADD COLUMN explicacion_xai TEXT",
    ]:
        try:
            _conn.execute(text(_sql))
            _conn.commit()
        except Exception:
            pass

app = FastAPI(title="Tesis API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_MEDIA_DIR = os.path.join(os.path.dirname(__file__), "media")
os.makedirs(_MEDIA_DIR, exist_ok=True)
app.mount("/media", StaticFiles(directory=_MEDIA_DIR), name="media")

app.include_router(alumnos.router, prefix="/api")
app.include_router(encuestas.router, prefix="/api")
app.include_router(notas.router, prefix="/api")
app.include_router(predicciones.router, prefix="/api")
app.include_router(expedientes.router, prefix="/api")


@app.get("/")
def root():
    return {"status": "ok", "message": "Tesis API corriendo con FastAPI"}
