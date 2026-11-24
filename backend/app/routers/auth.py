import hashlib
import secrets
from fastapi import APIRouter, Depends, HTTPException, Header, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Usuario

router = APIRouter(prefix="/api/v1/auth", tags=["Autenticación y Permisos"])

# Almacén en memoria de sesiones activas para validación de rol y permisos
ACTIVE_SESSIONS = {}

def hash_password(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

class LoginRequest(BaseModel):
    username: str
    password: str

class CrearCredencialRequest(BaseModel):
    documento: str
    nombres: str
    apellidos: str
    username: str
    password: str
    rol: str  # ADMIN o OPERARIO

def get_current_user(authorization: str = Header(None), db: Session = Depends(get_db)) -> Usuario:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token de sesión requerido")
    token = authorization.replace("Bearer ", "").strip()
    user_id = ACTIVE_SESSIONS.get(token)
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sesión inválida o expirada")
    user = db.query(Usuario).filter(Usuario.usuario_id == user_id, Usuario.activo == 1).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario inactivo o no encontrado")
    return user

def require_admin(current_user: Usuario = Depends(get_current_user)) -> Usuario:
    if current_user.rol != "ADMIN":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permiso denegado: Se requiere rol ADMIN")
    return current_user

@router.post("/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(Usuario).filter(Usuario.username == payload.username).first()
    if not user or not user.password_hash or user.password_hash != hash_password(payload.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales incorrectas")
    if user.activo != 1:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cuenta de usuario inactiva")
    if user.rol not in ("ADMIN", "OPERARIO"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Rol sin acceso al sistema operativo")

    token = secrets.token_hex(24)
    ACTIVE_SESSIONS[token] = user.usuario_id
    return {
        "access_token": token,
        "token_type": "bearer",
        "usuario": {
            "usuario_id": user.usuario_id,
            "nombres": user.nombres,
            "apellidos": user.apellidos,
            "username": user.username,
            "rol": user.rol
        }
    }

@router.post("/cuentas", status_code=status.HTTP_201_CREATED)
def crear_cuenta_operativa(payload: CrearCredencialRequest, db: Session = Depends(get_db), admin: Usuario = Depends(require_admin)):
    if payload.rol not in ("ADMIN", "OPERARIO"):
        raise HTTPException(status_code=400, detail="El rol debe ser ADMIN o OPERARIO")
    if db.query(Usuario).filter((Usuario.username == payload.username) | (Usuario.documento == payload.documento)).first():
        raise HTTPException(status_code=409, detail="El username o documento ya existe")
    nuevo = Usuario(
        documento=payload.documento,
        nombres=payload.nombres,
        apellidos=payload.apellidos,
        username=payload.username,
        password_hash=hash_password(payload.password),
        rol=payload.rol,
        activo=1
    )
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return {"mensaje": "Cuenta creada exitosamente", "usuario_id": nuevo.usuario_id, "rol": nuevo.rol}
