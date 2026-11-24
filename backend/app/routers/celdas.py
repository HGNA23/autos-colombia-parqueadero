from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Celda, Usuario
from .auth import get_current_user, require_admin

router = APIRouter(prefix="/api/v1/celdas", tags=["Administración de Celdas Individuales"])

class CeldaCreate(BaseModel):
    codigo: str
    tipo_vehiculo: str  # CARRO o MOTOCICLETA
    ubicacion: str = "Zona General"

class CeldaUpdate(BaseModel):
    tipo_vehiculo: str | None = None
    ubicacion: str | None = None
    estado: str | None = None  # DISPONIBLE, MANTENIMIENTO
    activa: int | None = None

@router.get("/")
def listar_celdas(db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    celdas = db.query(Celda).all()
    total_carros = sum(1 for c in celdas if c.tipo_vehiculo == "CARRO" and c.activa == 1)
    ocupados_carros = sum(1 for c in celdas if c.tipo_vehiculo == "CARRO" and c.activa == 1 and c.estado == "OCUPADA")
    total_motos = sum(1 for c in celdas if c.tipo_vehiculo == "MOTOCICLETA" and c.activa == 1)
    ocupados_motos = sum(1 for c in celdas if c.tipo_vehiculo == "MOTOCICLETA" and c.activa == 1 and c.estado == "OCUPADA")
    return {
        "resumen_aforo": {
            "carros": {"ocupadas": ocupados_carros, "capacidad": total_carros},
            "motocicletas": {"ocupadas": ocupados_motos, "capacidad": total_motos}
        },
        "celdas": celdas
    }

@router.post("/", status_code=status.HTTP_201_CREATED)
def crear_celda_individual(payload: CeldaCreate, db: Session = Depends(get_db), admin: Usuario = Depends(require_admin)):
    if payload.tipo_vehiculo not in ("CARRO", "MOTOCICLETA"):
        raise HTTPException(status_code=400, detail="tipo_vehiculo debe ser CARRO o MOTOCICLETA")
    if db.query(Celda).filter(Celda.codigo == payload.codigo.upper()).first():
        raise HTTPException(status_code=409, detail=f"Ya existe una celda con el código {payload.codigo.upper()}")
    celda = Celda(
        codigo=payload.codigo.upper(),
        tipo_vehiculo=payload.tipo_vehiculo,
        ubicacion=payload.ubicacion,
        estado="DISPONIBLE",
        activa=1
    )
    db.add(celda)
    db.commit()
    db.refresh(celda)
    return {"mensaje": "Celda individual creada", "celda": celda}

@router.patch("/{celda_id}")
def modificar_celda_individual(celda_id: int, payload: CeldaUpdate, db: Session = Depends(get_db), admin: Usuario = Depends(require_admin)):
    celda = db.query(Celda).filter(Celda.celda_id == celda_id).first()
    if not celda:
        raise HTTPException(status_code=404, detail="Celda no encontrada")
    if celda.estado == "OCUPADA" and (payload.activa == 0 or payload.estado == "MANTENIMIENTO"):
        raise HTTPException(status_code=409, detail="No se puede desactivar o poner en mantenimiento una celda ocupada")
    if payload.tipo_vehiculo:
        celda.tipo_vehiculo = payload.tipo_vehiculo
    if payload.ubicacion:
        celda.ubicacion = payload.ubicacion
    if payload.estado:
        celda.estado = payload.estado
    if payload.activa is not None:
        celda.activa = payload.activa
    db.commit()
    db.refresh(celda)
    return {"mensaje": "Celda actualizada", "celda": celda}
