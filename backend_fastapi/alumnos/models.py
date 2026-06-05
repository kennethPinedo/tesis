from datetime import date, datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Date
from database import Base


class Alumno(Base):
    __tablename__ = "alumnos"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    apellido = Column(String(100), nullable=False)
    edad = Column(Integer, nullable=False)
    grado = Column(String(10), nullable=False)
    anio_cursada = Column(Integer, default=2024)
    contacto_emergente = Column(String(20), nullable=False)
    condicion_social = Column(String(10), default="NINGUNA")
    genero = Column(String(20), default="No especificado")


class Encuesta(Base):
    __tablename__ = "encuestas"

    id = Column(Integer, primary_key=True, index=True)
    alumno_id = Column(Integer, ForeignKey("alumnos.id"), nullable=False)
    A1 = Column(Integer, nullable=False)
    A2 = Column(Integer, nullable=False)
    A3 = Column(Integer, nullable=False)
    A4 = Column(Integer, nullable=False)
    A5 = Column(Integer, nullable=False)
    A6 = Column(Integer, nullable=False)
    A7 = Column(Integer, nullable=False)
    A8 = Column(Integer, nullable=False)
    A9 = Column(Integer, nullable=False)
    A10 = Column(Integer, nullable=False)
    B1 = Column(Integer, nullable=False)
    B2 = Column(Integer, nullable=False)
    B3 = Column(Integer, nullable=False)
    B4 = Column(Integer, nullable=False)
    B5 = Column(Integer, nullable=False)
    B6 = Column(Integer, nullable=False)
    B7 = Column(Integer, nullable=False)
    B8 = Column(Integer, nullable=False)
    B9 = Column(Integer, nullable=False)
    B10 = Column(Integer, nullable=False)
    fecha_aplicacion = Column(Date, default=date.today)


class Nota(Base):
    __tablename__ = "notas"

    id = Column(Integer, primary_key=True, index=True)
    alumno_id = Column(Integer, ForeignKey("alumnos.id"), nullable=False)
    asignatura = Column(String(100), nullable=False)
    calificacion_literal = Column(String(2), nullable=False)
    fecha_registro = Column(Date, default=date.today)


class PrediccionAcademica(Base):
    __tablename__ = "predicciones"

    id = Column(Integer, primary_key=True, index=True)
    alumno_id = Column(Integer, ForeignKey("alumnos.id"), nullable=False)
    promedio_notas = Column(Float, nullable=False)
    nivel_riesgo = Column(String(10), nullable=False)
    probabilidad = Column(Float, nullable=True)
    prediccion_notas = Column(String, nullable=False)
    condiciones_psicoeducativas = Column(String, nullable=False)
    fecha_prediccion = Column(DateTime, default=datetime.utcnow)


class ExpedientePsicologico(Base):
    __tablename__ = "expedientes"

    id = Column(Integer, primary_key=True, index=True)
    alumno_id = Column(Integer, ForeignKey("alumnos.id"), nullable=False)
    nivel_preocupacion = Column(Integer, nullable=False)
    archivo_pdf = Column(String, nullable=False)
    fecha_registro = Column(DateTime, default=datetime.utcnow)
