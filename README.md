# Autos Colombia - Sistema de parqueadero

Prototipo ejecutable para la Iteración 1: control de entrada y salida de vehículos. El frontend usa Angular; la API usa Python/FastAPI y SQLite.

## Reglas del parqueadero

- Capacidad separada: 70 carros y 10 motocicletas.
- Solo ingresa una placa registrada y activa.
- Se requiere mensualidad vigente.
- Tarifas informativas: $250.000 COP por carro y $100.000 COP por motocicleta al mes.
- El vencimiento mensual es el mismo día calendario del mes siguiente. La fecha de vencimiento es válida durante ese día; a partir del día siguiente se considera vencida. Si ese día no existe, se usa el último día del mes.
- No se permiten dos entradas abiertas para el mismo vehículo.

## Requisitos

- Python 3.10 o superior.
- Node.js 22.22.3 o superior y npm (Angular CLI actual).

## Iniciar en Windows

Abre dos terminales de PowerShell en la raíz del proyecto.

### 1. API

```powershell
cd backend
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
```

API: `http://127.0.0.1:8000` · Documentación: `http://127.0.0.1:8000/docs`.

### 2. Interfaz Angular

```powershell
cd frontend
npm install
npm start
```

Frontend: `http://localhost:4200`.

## Pruebas del backend

```powershell
cd backend
pytest -q
```

## Datos de prueba

- `ABC123`: carro registrado, mensualidad vigente.
- `MOT123`: motocicleta registrada, mensualidad vigente.
- `CAR999`: carro registrado con mensualidad vencida.
- Cualquier otra placa no está registrada y debe ser rechazada.

Al iniciar, la API crea `backend/data/autos_colombia.sqlite3`. El archivo de base de datos y el entorno virtual quedan excluidos de Git.

## Alcance y seguridad

Este es un prototipo académico local. Todavía no integra el módulo de usuarios/vehículos ni el módulo de pagos, no expone formulario de registro, y no incluye autenticación real de operarios. Por tanto, los datos de prueba son ficticios y el prototipo no debe desplegarse en Internet para uso real. El control de acceso, registro de placas y pagos debe completarse antes de operación productiva.

## Estructura

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


- `backend/app/main.py`: API, validaciones de negocio y persistencia.
- `backend/tests/`: pruebas automatizadas de reglas de acceso.
- `frontend/src/app/`: panel de ocupación, ingreso, salida e historial.
- `backend/data/`: base SQLite local ignorada por Git.
