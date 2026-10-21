from __future__ import annotations

import calendar
import os
import sqlite3
from contextlib import asynccontextmanager
from datetime import date, datetime
from pathlib import Path
from typing import Literal
from zoneinfo import ZoneInfo

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

BOGOTA = ZoneInfo("America/Bogota")
CAPACITY = {"CARRO": 70, "MOTOCICLETA": 10}
DEFAULT_DB = Path(__file__).resolve().parents[1] / "data" / "autos_colombia.sqlite3"


def now_local() -> datetime:
    return datetime.now(BOGOTA).replace(microsecond=0)


def normalize_plate(value: str) -> str:
    return "".join(ch for ch in value.upper().strip() if ch.isalnum())


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path, timeout=10, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 10000")
    return conn


class ClosingConnection:
    def __init__(self, db_path: Path):
        self.connection = connect(db_path)
    def __enter__(self):
        return self.connection
    def __exit__(self, exc_type, exc, tb):
        if exc_type:
            self.connection.rollback()
        self.connection.close()
        return False


def db_connection(db_path: Path) -> ClosingConnection:
    return ClosingConnection(db_path)


def plus_one_month(value: date) -> date:
    year = value.year + (value.month == 12)
    month = 1 if value.month == 12 else value.month + 1
    return value.replace(year=year, month=month, day=min(value.day, calendar.monthrange(year, month)[1]))


def initialize(db_path: Path, seed_demo: bool = True) -> None:
    with db_connection(db_path) as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS usuario (
                usuario_id INTEGER PRIMARY KEY,
                documento TEXT NOT NULL UNIQUE,
                nombre TEXT NOT NULL,
                rol TEXT NOT NULL CHECK (rol IN ('ADMIN', 'OPERARIO')),
                activo INTEGER NOT NULL DEFAULT 1 CHECK (activo IN (0, 1))
            );
            CREATE TABLE IF NOT EXISTS vehiculo (
                vehiculo_id INTEGER PRIMARY KEY,
                placa TEXT NOT NULL UNIQUE,
                tipo TEXT NOT NULL CHECK (tipo IN ('CARRO', 'MOTOCICLETA')),
                marca TEXT NOT NULL DEFAULT '',
                color TEXT NOT NULL DEFAULT '',
                titular TEXT NOT NULL DEFAULT '',
                estado_registro TEXT NOT NULL DEFAULT 'ACTIVO'
                    CHECK (estado_registro IN ('ACTIVO', 'INACTIVO')),
                fecha_vencimiento TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS movimiento (
                movimiento_id INTEGER PRIMARY KEY,
                vehiculo_id INTEGER NOT NULL REFERENCES vehiculo(vehiculo_id),
                operario_id INTEGER NOT NULL REFERENCES usuario(usuario_id),
                fecha_hora_entrada TEXT NOT NULL,
                fecha_hora_salida TEXT,
                observacion_entrada TEXT NOT NULL DEFAULT '',
                observacion_salida TEXT NOT NULL DEFAULT '',
                CHECK (fecha_hora_salida IS NULL OR fecha_hora_salida >= fecha_hora_entrada)
            );
            CREATE UNIQUE INDEX IF NOT EXISTS uq_movimiento_abierto_vehiculo
                ON movimiento(vehiculo_id) WHERE fecha_hora_salida IS NULL;
            CREATE INDEX IF NOT EXISTS ix_movimiento_entrada
                ON movimiento(fecha_hora_entrada);
            CREATE INDEX IF NOT EXISTS ix_vehiculo_placa ON vehiculo(placa);
            """
        )
        if seed_demo:
            today = now_local().date()
            conn.execute(
                "INSERT OR IGNORE INTO usuario(usuario_id,documento,nombre,rol) VALUES(1,'DEMO-001','Operario demostración','OPERARIO')"
            )
            conn.execute(
                "INSERT OR IGNORE INTO usuario(usuario_id,documento,nombre,rol) VALUES(2,'DEMO-002','Administrador demostración','ADMIN')"
            )
            active_until = plus_one_month(today)
            expired_on = today.replace(day=1)
            samples = [
                ("ABC123", "CARRO", "Automóvil", "Gris", "Titular demo carro", active_until.isoformat()),
                ("MOT123", "MOTOCICLETA", "Motocicleta", "Negra", "Titular demo moto", active_until.isoformat()),
                ("CAR999", "CARRO", "Automóvil", "Blanco", "Titular con mensualidad vencida", expired_on.isoformat()),
            ]
            for plate, kind, brand, color, owner, expiry in samples:
                conn.execute(
                    "INSERT OR IGNORE INTO vehiculo(placa,tipo,marca,color,titular,fecha_vencimiento) VALUES(?,?,?,?,?,?)",
                    (plate, kind, brand, color, owner, expiry),
                )
            # Demo vehicle stays active until the same calendar day next month.


class EntryRequest(BaseModel):
    placa: str = Field(min_length=3, max_length=12)
    observacion: str = Field(default="", max_length=500)
    operario_id: int = Field(default=1, ge=1)

    @field_validator("placa")
    @classmethod
    def clean_plate(cls, value: str) -> str:
        plate = normalize_plate(value)
        if len(plate) < 3:
            raise ValueError("La placa debe contener al menos 3 caracteres alfanuméricos.")
        return plate


class ExitRequest(BaseModel):
    observacion: str = Field(default="", max_length=500)
    operario_id: int = Field(default=1, ge=1)


def vehicle_dict(row: sqlite3.Row) -> dict:
    expiration = date.fromisoformat(row["fecha_vencimiento"])
    return {
        "vehiculo_id": row["vehiculo_id"],
        "placa": row["placa"],
        "tipo": row["tipo"],
        "marca": row["marca"],
        "color": row["color"],
        "titular": row["titular"],
        "estado_registro": row["estado_registro"],
        "fecha_vencimiento": expiration.isoformat(),
        "mensualidad_vigente": expiration >= now_local().date(),
        "tarifa_mensual_cop": 250000 if row["tipo"] == "CARRO" else 100000,
    }


def movement_dict(row: sqlite3.Row) -> dict:
    return {
        "movimiento_id": row["movimiento_id"],
        "placa": row["placa"],
        "tipo": row["tipo"],
        "titular": row["titular"],
        "operario": row["operario"],
        "fecha_hora_entrada": row["fecha_hora_entrada"],
        "fecha_hora_salida": row["fecha_hora_salida"],
        "observacion_entrada": row["observacion_entrada"],
        "observacion_salida": row["observacion_salida"],
        "estado": "ABIERTO" if row["fecha_hora_salida"] is None else "CERRADO",
    }


def create_app(db_path: Path | None = None, seed_demo: bool = True) -> FastAPI:
    database = Path(db_path or os.getenv("AUTOS_COLOMBIA_DB", DEFAULT_DB))

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        initialize(database, seed_demo=seed_demo)
        yield

    app = FastAPI(
        title="Autos Colombia - Gestión de acceso",
        description="API de ingreso, salida, ocupación e historial del Módulo 1.",
        version="1.0.0",
        lifespan=lifespan,
    )
    app.state.db_path = database
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:4200", "http://127.0.0.1:4200"],
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )

    @app.get("/api/v1/health")
    def health():
        return {"status": "ok", "sistema": "Autos Colombia", "modulo": 1}

    @app.get("/api/v1/vehiculos")
    def list_vehicles():
        with db_connection(database) as conn:
            rows = conn.execute("SELECT * FROM vehiculo ORDER BY placa").fetchall()
        return [vehicle_dict(row) for row in rows]

    @app.get("/api/v1/vehiculos/{placa}")
    def get_vehicle(placa: str):
        normalized = normalize_plate(placa)
        with db_connection(database) as conn:
            row = conn.execute("SELECT * FROM vehiculo WHERE placa=?", (normalized,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail={"codigo": "VEHICULO_NO_REGISTRADO", "mensaje": "La placa no está registrada. No se permite el ingreso."})
        return vehicle_dict(row)

    @app.get("/api/v1/ocupacion")
    def occupancy():
        with db_connection(database) as conn:
            rows = conn.execute(
                """SELECT v.tipo, COUNT(m.movimiento_id) AS ocupados
                   FROM vehiculo v LEFT JOIN movimiento m
                   ON m.vehiculo_id=v.vehiculo_id AND m.fecha_hora_salida IS NULL
                   GROUP BY v.tipo"""
            ).fetchall()
        counts = {row["tipo"]: row["ocupados"] for row in rows}
        return {
            "CARRO": {"ocupados": counts.get("CARRO", 0), "capacidad": CAPACITY["CARRO"], "disponibles": CAPACITY["CARRO"] - counts.get("CARRO", 0)},
            "MOTOCICLETA": {"ocupados": counts.get("MOTOCICLETA", 0), "capacidad": CAPACITY["MOTOCICLETA"], "disponibles": CAPACITY["MOTOCICLETA"] - counts.get("MOTOCICLETA", 0)},
        }

    @app.get("/api/v1/movimientos/abiertos/{placa}")
    def open_movement(placa: str):
        normalized = normalize_plate(placa)
        with db_connection(database) as conn:
            row = conn.execute(
                """SELECT m.*,v.placa,v.tipo,v.titular,u.nombre AS operario
                   FROM movimiento m JOIN vehiculo v USING(vehiculo_id)
                   JOIN usuario u ON u.usuario_id=m.operario_id
                   WHERE v.placa=? AND m.fecha_hora_salida IS NULL""",
                (normalized,),
            ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail={"codigo": "INGRESO_ABIERTO_NO_ENCONTRADO", "mensaje": "No hay una entrada abierta para esa placa."})
        return movement_dict(row)

    @app.post("/api/v1/movimientos/ingresos", status_code=201)
    def register_entry(request: EntryRequest):
        with db_connection(database) as conn:
            conn.execute("BEGIN IMMEDIATE")
            vehicle = conn.execute("SELECT * FROM vehiculo WHERE placa=?", (request.placa,)).fetchone()
            if not vehicle:
                raise HTTPException(status_code=409, detail={"codigo": "VEHICULO_NO_REGISTRADO", "mensaje": "La placa no está registrada. No se permite el ingreso."})
            if vehicle["estado_registro"] != "ACTIVO":
                raise HTTPException(status_code=409, detail={"codigo": "VEHICULO_INACTIVO", "mensaje": "El registro del vehículo está inactivo."})
            if date.fromisoformat(vehicle["fecha_vencimiento"]) < now_local().date():
                raise HTTPException(status_code=409, detail={"codigo": "MENSUALIDAD_VENCIDA", "mensaje": "La mensualidad está vencida; el ingreso no fue registrado."})
            if not conn.execute("SELECT 1 FROM usuario WHERE usuario_id=? AND activo=1", (request.operario_id,)).fetchone():
                raise HTTPException(status_code=422, detail={"codigo": "OPERARIO_INVALIDO", "mensaje": "El operario no existe o está inactivo."})
            if conn.execute("SELECT 1 FROM movimiento WHERE vehiculo_id=? AND fecha_hora_salida IS NULL", (vehicle["vehiculo_id"],)).fetchone():
                raise HTTPException(status_code=409, detail={"codigo": "INGRESO_DUPLICADO", "mensaje": "El vehículo ya tiene una entrada abierta."})
            occupied = conn.execute(
                """SELECT COUNT(*) FROM movimiento m JOIN vehiculo v USING(vehiculo_id)
                   WHERE v.tipo=? AND m.fecha_hora_salida IS NULL""",
                (vehicle["tipo"],),
            ).fetchone()[0]
            limit = CAPACITY[vehicle["tipo"]]
            if occupied >= limit:
                category = "carros" if vehicle["tipo"] == "CARRO" else "motocicletas"
                raise HTTPException(status_code=409, detail={"codigo": "CUPO_COMPLETO", "mensaje": f"No hay cupos disponibles para {category} ({occupied}/{limit})."})
            timestamp = now_local().isoformat()
            cursor = conn.execute(
                """INSERT INTO movimiento(vehiculo_id,operario_id,fecha_hora_entrada,observacion_entrada)
                   VALUES(?,?,?,?)""",
                (vehicle["vehiculo_id"], request.operario_id, timestamp, request.observacion.strip()),
            )
            movement_id = cursor.lastrowid
            row = conn.execute(
                """SELECT m.*,v.placa,v.tipo,v.titular,u.nombre AS operario
                   FROM movimiento m JOIN vehiculo v USING(vehiculo_id)
                   JOIN usuario u ON u.usuario_id=m.operario_id WHERE m.movimiento_id=?""",
                (movement_id,),
            ).fetchone()
            conn.commit()
        return movement_dict(row)

    @app.post("/api/v1/movimientos/{movement_id}/salida")
    def register_exit(movement_id: int, request: ExitRequest):
        with db_connection(database) as conn:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute(
                """SELECT m.*,v.placa,v.tipo,v.titular,u.nombre AS operario
                   FROM movimiento m JOIN vehiculo v USING(vehiculo_id)
                   JOIN usuario u ON u.usuario_id=m.operario_id
                   WHERE m.movimiento_id=? AND m.fecha_hora_salida IS NULL""",
                (movement_id,),
            ).fetchone()
            if not row:
                raise HTTPException(status_code=404, detail={"codigo": "INGRESO_ABIERTO_NO_ENCONTRADO", "mensaje": "No hay una entrada abierta con ese identificador."})
            if not conn.execute("SELECT 1 FROM usuario WHERE usuario_id=? AND activo=1", (request.operario_id,)).fetchone():
                raise HTTPException(status_code=422, detail={"codigo": "OPERARIO_INVALIDO", "mensaje": "El operario no existe o está inactivo."})
            conn.execute(
                "UPDATE movimiento SET fecha_hora_salida=?,observacion_salida=? WHERE movimiento_id=? AND fecha_hora_salida IS NULL",
                (now_local().isoformat(), request.observacion.strip(), movement_id),
            )
            updated = conn.execute(
                """SELECT m.*,v.placa,v.tipo,v.titular,u.nombre AS operario
                   FROM movimiento m JOIN vehiculo v USING(vehiculo_id)
                   JOIN usuario u ON u.usuario_id=m.operario_id WHERE m.movimiento_id=?""",
                (movement_id,),
            ).fetchone()
            conn.commit()
        return movement_dict(updated)

    @app.get("/api/v1/movimientos")
    def movement_history(
        placa: str | None = None,
        desde: date | None = None,
        hasta: date | None = None,
        estado: Literal["ABIERTO", "CERRADO"] | None = None,
        limite: int = Query(default=100, ge=1, le=500),
    ):
        if desde and hasta and desde > hasta:
            raise HTTPException(status_code=422, detail="La fecha inicial no puede ser posterior a la fecha final.")
        clauses, args = [], []
        if placa:
            clauses.append("v.placa=?"); args.append(normalize_plate(placa))
        if desde:
            clauses.append("date(m.fecha_hora_entrada)>=?"); args.append(desde.isoformat())
        if hasta:
            clauses.append("date(m.fecha_hora_entrada)<=?"); args.append(hasta.isoformat())
        if estado == "ABIERTO": clauses.append("m.fecha_hora_salida IS NULL")
        if estado == "CERRADO": clauses.append("m.fecha_hora_salida IS NOT NULL")
        where = " WHERE " + " AND ".join(clauses) if clauses else ""
        with db_connection(database) as conn:
            rows = conn.execute(
                """SELECT m.*,v.placa,v.tipo,v.titular,u.nombre AS operario
                   FROM movimiento m JOIN vehiculo v USING(vehiculo_id)
                   JOIN usuario u ON u.usuario_id=m.operario_id""" + where +
                " ORDER BY m.fecha_hora_entrada DESC LIMIT ?", (*args, limite),
            ).fetchall()
        return [movement_dict(row) for row in rows]

    return app


app = create_app()
