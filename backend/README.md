# Backend · Autos Colombia

API del Módulo 1 para registrar entradas y salidas, consultar ocupación e historial.

## Requisitos

- Python 3.10 o superior.

## Ejecutar en Windows

Desde esta carpeta:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
```

La API queda disponible en `http://127.0.0.1:8000`; su documentación interactiva en `http://127.0.0.1:8000/docs`.

## Datos de demostración

- `ABC123`: carro registrado, mensualidad vigente.
- `MOT123`: motocicleta registrada, mensualidad vigente.
- `CAR999`: carro registrado, mensualidad vencida.
- Cualquier placa diferente no está registrada y no puede ingresar.

Los registros de demostración usan titulares ficticios. La fecha de vencimiento de ABC123 y MOT123 se calcula como el aniversario del mes siguiente; el módulo de pagos será quien gestione renovaciones en una iteración posterior.

## API principal

- `GET /api/v1/health`
- `GET /api/v1/vehiculos` y `GET /api/v1/vehiculos/{placa}`
- `GET /api/v1/ocupacion`
- `POST /api/v1/movimientos/ingresos`
- `GET /api/v1/movimientos/abiertos/{placa}`
- `POST /api/v1/movimientos/{id}/salida`
- `GET /api/v1/movimientos?placa=&desde=&hasta=&estado=`

Capacidad: 70 carros y 10 motocicletas. La API valida registro activo, mensualidad vigente, entrada abierta y cupo antes de insertar. Las fechas se registran en `America/Bogota`. La fecha de vencimiento se considera válida durante todo ese día; la renovación vence después de esa fecha.

## Pruebas

```powershell
pytest -q
```

Esta primera versión es un prototipo académico local: aún no incluye inicio de sesión/autorización real ni despliegue para uso de producción.
