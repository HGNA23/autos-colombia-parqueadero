from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from .database import Base

class Usuario(Base):
    __tablename__ = "usuario"
    usuario_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    documento = Column(String, unique=True, nullable=False)
    nombres = Column(String, nullable=False)
    apellidos = Column(String, nullable=False)
    username = Column(String, unique=True, nullable=True)
    password_hash = Column(String, nullable=True)
    rol = Column(String, nullable=False)  # ADMIN, OPERARIO, TITULAR
    activo = Column(Integer, default=1)

class Celda(Base):
    __tablename__ = "celda"
    celda_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    codigo = Column(String, unique=True, nullable=False)  # Ej: C-01, C-02, M-01
    tipo_vehiculo = Column(String, nullable=False)  # CARRO, MOTOCICLETA
    ubicacion = Column(String, default="Zona General")
    estado = Column(String, default="DISPONIBLE")  # DISPONIBLE, OCUPADA, MANTENIMIENTO
    activa = Column(Integer, default=1)

class Vehiculo(Base):
    __tablename__ = "vehiculo"
    vehiculo_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    placa = Column(String, unique=True, nullable=False)
    tipo = Column(String, nullable=False)  # CARRO, MOTOCICLETA
    marca = Column(String, default="")
    color = Column(String, default="")
    usuario_titular_id = Column(Integer, ForeignKey("usuario.usuario_id"), nullable=False)
    estado_registro = Column(String, default="ACTIVO")

class Mensualidad(Base):
    __tablename__ = "mensualidad"
    mensualidad_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    vehiculo_id = Column(Integer, ForeignKey("vehiculo.vehiculo_id"), nullable=False)
    fecha_inicio = Column(String, nullable=False)
    fecha_fin = Column(String, nullable=False)
    estado_vigencia = Column(String, default="ACTIVO")

class Movimiento(Base):
    __tablename__ = "movimiento"
    movimiento_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    vehiculo_id = Column(Integer, ForeignKey("vehiculo.vehiculo_id"), nullable=False)
    celda_id = Column(Integer, ForeignKey("celda.celda_id"), nullable=False)
    operario_id = Column(Integer, ForeignKey("usuario.usuario_id"), nullable=False)
    operario_cierre_id = Column(Integer, ForeignKey("usuario.usuario_id"), nullable=True)
    fecha_hora_entrada = Column(String, nullable=False)
    fecha_hora_salida = Column(String, nullable=True)
    observacion_entrada = Column(String, default="")
    observacion_salida = Column(String, default="")
