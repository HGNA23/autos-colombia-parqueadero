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

- `backend/app/main.py`: API, validaciones de negocio y persistencia.
- `backend/tests/`: pruebas automatizadas de reglas de acceso.
- `frontend/src/app/`: panel de ocupación, ingreso, salida e historial.
- `backend/data/`: base SQLite local ignorada por Git.
