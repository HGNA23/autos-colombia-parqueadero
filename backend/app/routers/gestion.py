from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Usuario, Vehiculo, Mensualidad
from .auth import get_current_user, require_admin

router = APIRouter(prefix="/api/v1/gestion", tags=["Gestión de Usuarios y Vehículos"])

class TitularCreate(BaseModel):
    documento: str
    nombres: str
    apellidos: str

class VehiculoCreate(BaseModel):
    placa: str
    tipo: str
    marca: str = ""
    color: str = ""
    usuario_titular_id: int
    fecha_inicio: str
    fecha_fin: str

@router.get("/usuarios")
def listar_usuarios(db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    return db.query(Usuario).all()

@router.post("/titulares", status_code=status.HTTP_201_CREATED)
def registrar_titular(payload: TitularCreate, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    if db.query(Usuario).filter(Usuario.documento == payload.documento).first():
        raise HTTPException(status_code=409, detail="El documento ya se encuentra registrado")
    nuevo = Usuario(
        documento=payload.documento,
        nombres=payload.nombres,
        apellidos=payload.apellidos,
        rol="TITULAR",
        activo=1
    )
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo

@router.patch("/usuarios/{usuario_id}/estado")
def cambiar_estado_usuario(usuario_id: int, activo: int, db: Session = Depends(get_db), admin: Usuario = Depends(require_admin)):
    usuario = db.query(Usuario).filter(Usuario.usuario_id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    usuario.activo = activo
    db.commit()
    return {"mensaje": "Estado actualizado", "usuario_id": usuario_id, "activo": activo}

@router.post("/vehiculos", status_code=status.HTTP_201_CREATED)
def registrar_vehiculo(payload: VehiculoCreate, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    titular = db.query(Usuario).filter(Usuario.usuario_id == payload.usuario_titular_id, Usuario.activo == 1).first()
    if not titular:
        raise HTTPException(status_code=404, detail="Titular no encontrado o inactivo")
    if db.query(Vehiculo).filter(Vehiculo.placa == payload.placa.upper()).first():
        raise HTTPException(status_code=409, detail="La placa ya está registrada")
    veh = Vehiculo(
        placa=payload.placa.upper(),
        tipo=payload.tipo,
        marca=payload.marca,
        color=payload.color,
        usuario_titular_id=payload.usuario_titular_id,
        estado_registro="ACTIVO"
    )
    db.add(veh)
    db.commit()
    db.refresh(veh)
    mens = Mensualidad(
        vehiculo_id=veh.vehiculo_id,
        fecha_inicio=payload.fecha_inicio,
        fecha_fin=payload.fecha_fin,
        estado_vigencia="ACTIVO"
    )
    db.add(mens)
    db.commit()
    return {"mensaje": "Vehículo y mensualidad registrados", "vehiculo": veh}
