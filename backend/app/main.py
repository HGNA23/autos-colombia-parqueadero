from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base, SessionLocal
from .models import Usuario, Celda
from .routers import auth, celdas, gestion, movimientos

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Autos Colombia API — Iteraciones 1 y 2", version="2.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def seed_initial_data():
    db = SessionLocal()
    try:
        if not db.query(Usuario).filter(Usuario.username == "admin").first():
            db.add(Usuario(
                documento="10000001",
                nombres="Administrador",
                apellidos="General",
                username="admin",
                password_hash=auth.hash_password("Admin2026*"),
                rol="ADMIN",
                activo=1
            ))
        if not db.query(Usuario).filter(Usuario.username == "operario1").first():
            db.add(Usuario(
                documento="10000002",
                nombres="Carlos",
                apellidos="Operador",
                username="operario1",
                password_hash=auth.hash_password("Oper2026*"),
                rol="OPERARIO",
                activo=1
            ))
        if db.query(Celda).count() == 0:
            for i in range(1, 71):
                db.add(Celda(codigo=f"C-{i:02d}", tipo_vehiculo="CARRO", ubicacion="Nivel 1", estado="DISPONIBLE", activa=1))
            for i in range(1, 11):
                db.add(Celda(codigo=f"M-{i:02d}", tipo_vehiculo="MOTOCICLETA", ubicacion="Zona Motos", estado="DISPONIBLE", activa=1))
        db.commit()
    finally:
        db.close()

app.include_router(auth.router)
app.include_router(celdas.router)
app.include_router(gestion.router)
app.include_router(movimientos.router)
