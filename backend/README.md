# Autos Colombia — Sistema de Gestión de Parqueadero (Iteraciones 1 y 2)

Repositorio oficial del proyecto **Autos Colombia** (Ingeniería de Software y Datos — IU Digital de Antioquia).

## Funcionalidades Implementadas en Código
1. **Autenticación y Control de Permisos RBAC (`backend/app/routers/auth.py`):**
   - Login con credenciales (`POST /api/v1/auth/login`) para roles `ADMIN` y `OPERARIO`.
   - Creación de cuentas operativas con credenciales y rol (`POST /api/v1/auth/cuentas`) restringida a `ADMIN`.
2. **Creación y Administración de Celdas Individuales (`backend/app/routers/celdas.py`):**
   - Inventario individual de celdas (`C-01`..`C-70` para carros y `M-01`..`M-10` para motocicletas).
   - Creación de nuevas celdas individuales (`POST /api/v1/celdas/`) y modificación de estado/disponibilidad (`PATCH /api/v1/celdas/{celda_id}`) exclusiva para `ADMIN`.
3. **Gestión de Titulares, Vehículos y Movimientos (`gestion.py` y `movimientos.py`):**
   - Validación de titular activo, vigencia estricta de mensualidad, no duplicidad y asignación/liberación real de celda individual.
   - Trazabilidad de doble operario (`operario_id` y `operario_cierre_id`).

## Estructura del Repositorio
- `backend/app/`: Código fuente FastAPI + SQLAlchemy (`auth.py`, `celdas.py`, `gestion.py`, `movimientos.py`, `models.py`, `database.py`, `main.py`).
- `backend/tests/test_iteracion_2.py`: Pruebas automatizadas de login, permisos, celdas individuales y movimientos.
- `docs/diagramas/`: Diagramas UML en PNG (`01_Diagrama_Casos_Uso.png`, `02_Diagrama_Clases_Unificado.png`, `03_Diagrama_Secuencia.png`, `04_Diagrama_Componentes.png`).
- `docs/mockups/`: Mockups visuales de Login/Credenciales, Celdas Individuales e Ingreso/Auditoría.
- `docs/entregables/Niño_Hector_EA2.docx`: Informe completo con modelos UML, mockups y evidencias reales de ejecución.

## Ejecución Local
```bash
cd backend
python -m pip install fastapi uvicorn sqlalchemy pytest httpx
python -m uvicorn app.main:app --reload
```
Credenciales iniciales creadas automáticamente al iniciar:
- **Administrador:** `admin` / `Admin2026*`
- **Operario:** `operario1` / `Oper2026*`
