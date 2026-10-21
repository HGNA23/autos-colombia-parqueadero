from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from app.main import connect, create_app, plus_one_month


@pytest.fixture
def client(tmp_path):
    app = create_app(tmp_path / "test.sqlite3")
    with TestClient(app) as test_client:
        yield test_client


def test_health_and_capacity_are_separated(client):
    assert client.get("/api/v1/health").json()["status"] == "ok"
    capacity = client.get("/api/v1/ocupacion").json()
    assert capacity["CARRO"] == {"ocupados": 0, "capacidad": 70, "disponibles": 70}
    assert capacity["MOTOCICLETA"] == {"ocupados": 0, "capacidad": 10, "disponibles": 10}


def test_unregistered_vehicle_is_rejected(client):
    response = client.post("/api/v1/movimientos/ingresos", json={"placa": "NO-REG-1"})
    assert response.status_code == 409
    assert response.json()["detail"]["codigo"] == "VEHICULO_NO_REGISTRADO"
    assert client.get("/api/v1/ocupacion").json()["CARRO"]["ocupados"] == 0


def test_registered_vehicle_can_enter_and_exit(client):
    entry = client.post("/api/v1/movimientos/ingresos", json={"placa": "abc 123", "observacion": "Espejo revisado"})
    assert entry.status_code == 201
    movement = entry.json()
    assert movement["placa"] == "ABC123"
    assert movement["estado"] == "ABIERTO"
    assert client.get("/api/v1/ocupacion").json()["CARRO"]["ocupados"] == 1
    exit_response = client.post(
        f"/api/v1/movimientos/{movement['movimiento_id']}/salida",
        json={"observacion": "Salida normal"},
    )
    assert exit_response.status_code == 200
    assert exit_response.json()["estado"] == "CERRADO"
    assert client.get("/api/v1/ocupacion").json()["CARRO"]["disponibles"] == 70


def test_duplicate_open_entry_is_rejected(client):
    assert client.post("/api/v1/movimientos/ingresos", json={"placa": "ABC123"}).status_code == 201
    response = client.post("/api/v1/movimientos/ingresos", json={"placa": "ABC123"})
    assert response.status_code == 409
    assert response.json()["detail"]["codigo"] == "INGRESO_DUPLICADO"


def test_expired_membership_is_rejected(client):
    response = client.post("/api/v1/movimientos/ingresos", json={"placa": "CAR999"})
    assert response.status_code == 409
    assert response.json()["detail"]["codigo"] == "MENSUALIDAD_VENCIDA"


def test_category_capacity_limit_is_enforced(client):
    db_path = client.app.state.db_path
    tomorrow = (date.today() + timedelta(days=60)).isoformat()
    with connect(db_path) as conn:
        for i in range(1, 71):
            conn.execute(
                "INSERT INTO vehiculo(placa,tipo,titular,fecha_vencimiento) VALUES(?,?,?,?)",
                (f"T{i:05d}", "CARRO", "Prueba", tomorrow),
            )
        conn.execute(
            """INSERT INTO movimiento(vehiculo_id,operario_id,fecha_hora_entrada)
               SELECT vehiculo_id,1,? FROM vehiculo WHERE placa LIKE 'T%'""",
            ("2026-01-01T08:00:00-05:00",),
        )
    response = client.post("/api/v1/movimientos/ingresos", json={"placa": "ABC123"})
    assert response.status_code == 409
    assert response.json()["detail"]["codigo"] == "CUPO_COMPLETO"


def test_anniversary_clamps_at_month_end():
    assert plus_one_month(date(2026, 1, 31)) == date(2026, 2, 28)
    assert plus_one_month(date(2028, 1, 31)) == date(2028, 2, 29)
    assert plus_one_month(date(2026, 10, 10)) == date(2026, 11, 10)
