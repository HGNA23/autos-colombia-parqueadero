from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from ..database import get_db
from ..models import Movimiento, Vehiculo, Mensualidad, Usuario, Celda
from .auth import get_current_user

router = APIRouter(prefix="/api/v1/movimientos", tags=["Movimientos y Asignación de Celda"])

@router.post("/ingresos", status_code=status.HTTP_201_CREATED)
def registrar_ingreso(placa: str, observacion: str = "", celda_id: int | None = None, db: Session = Depends(get_db), operario: Usuario = Depends(get_current_user)):
    vehiculo = db.query(Vehiculo).filter(Vehiculo.placa == placa.upper()).first()
    if not vehiculo or vehiculo.estado_registro != "ACTIVO":
        raise HTTPException(status_code=409, detail="Vehículo no registrado o inactivo")

    titular = db.query(Usuario).filter(Usuario.usuario_id == vehiculo.usuario_titular_id).first()
    if not titular or titular.activo != 1:
        raise HTTPException(status_code=409, detail="Titular Inactivo: Acceso denegado")

    hoy_str = datetime.now().strftime("%Y-%m-%d")
    mensualidad = db.query(Mensualidad).filter(Mensualidad.vehiculo_id == vehiculo.vehiculo_id).first()
    if not mensualidad or mensualidad.fecha_fin < hoy_str:
        raise HTTPException(status_code=409, detail="Mensualidad Vencida o inexistente")

    mov_abierto = db.query(Movimiento).filter(
        Movimiento.vehiculo_id == vehiculo.vehiculo_id,
        Movimiento.fecha_hora_salida == None
    ).first()
    if mov_abierto:
        raise HTTPException(status_code=409, detail="Movimiento Duplicado Abierto")

    # Selección de celda individual disponible
    if celda_id:
        celda = db.query(Celda).filter(
            Celda.celda_id == celda_id,
            Celda.tipo_vehiculo == vehiculo.tipo,
            Celda.activa == 1,
            Celda.estado == "DISPONIBLE"
        ).first()
        if not celda:
            raise HTTPException(status_code=409, detail="La celda seleccionada no está disponible o no corresponde al tipo de vehículo")
    else:
        celda = db.query(Celda).filter(
            Celda.tipo_vehiculo == vehiculo.tipo,
            Celda.activa == 1,
            Celda.estado == "DISPONIBLE"
        ).first()
        if not celda:
            raise HTTPException(status_code=409, detail=f"Sobrecupo: No hay celdas individuales disponibles para {vehiculo.tipo}")

    celda.estado = "OCUPADA"
    nuevo_mov = Movimiento(
        vehiculo_id=vehiculo.vehiculo_id,
        celda_id=celda.celda_id,
        operario_id=operario.usuario_id,
        fecha_hora_entrada=datetime.now().isoformat(),
        observacion_entrada=observacion
    )
    db.add(nuevo_mov)
    db.commit()
    db.refresh(nuevo_mov)
    return {
        "mensaje": "Ingreso registrado y celda asignada",
        "movimiento_id": nuevo_mov.movimiento_id,
        "celda_asignada": celda.codigo,
        "operario_id": operario.usuario_id
    }

@router.post("/{movimiento_id}/salida", status_code=status.HTTP_200_OK)
def registrar_salida(movimiento_id: int, observacion_salida: str = "", db: Session = Depends(get_db), operario: Usuario = Depends(get_current_user)):
    movimiento = db.query(Movimiento).filter(
        Movimiento.movimiento_id == movimiento_id,
        Movimiento.fecha_hora_salida == None
    ).first()
    if not movimiento:
        raise HTTPException(status_code=404, detail="Movimiento abierto no encontrado")

    celda = db.query(Celda).filter(Celda.celda_id == movimiento.celda_id).first()
    if celda:
        celda.estado = "DISPONIBLE"

    movimiento.fecha_hora_salida = datetime.now().isoformat()
    movimiento.operario_cierre_id = operario.usuario_id
    movimiento.observacion_salida = observacion_salida
    db.commit()
    return {
        "mensaje": "Salida registrada y celda liberada",
        "operario_cierre_id": operario.usuario_id,
        "celda_liberada": celda.codigo if celda else None
    }

@router.get("/historial")
def consultar_historial(db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    return db.query(Movimiento).all()
