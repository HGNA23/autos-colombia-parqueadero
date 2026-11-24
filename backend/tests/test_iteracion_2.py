from fastapi.testclient import TestClient
from app.main import app, seed_initial_data

seed_initial_data()
client = TestClient(app)

def test_flujo_completo_iteracion_2():
    # 1. Login Administrador
    res_admin = client.post("/api/v1/auth/login", json={"username": "admin", "password": "Admin2026*"})
    assert res_admin.status_code == 200
    token_admin = res_admin.json()["access_token"]
    headers_admin = {"Authorization": f"Bearer {token_admin}"}

    # 2. Login Operario
    res_oper = client.post("/api/v1/auth/login", json={"username": "operario1", "password": "Oper2026*"})
    assert res_oper.status_code == 200
    token_oper = res_oper.json()["access_token"]
    headers_oper = {"Authorization": f"Bearer {token_oper}"}

    # 3. Operario intenta crear celda individual -> Debe fallar con 403 Forbidden
    res_forb = client.post("/api/v1/celdas/", json={"codigo": "C-99", "tipo_vehiculo": "CARRO", "ubicacion": "Nivel 2"}, headers=headers_oper)
    assert res_forb.status_code == 403

    # 4. Administrador crea celda individual C-71 -> Debe responder 201 Created
    res_celda = client.post("/api/v1/celdas/", json={"codigo": "C-71", "tipo_vehiculo": "CARRO", "ubicacion": "Nivel 2"}, headers=headers_admin)
    assert res_celda.status_code in (200, 201, 409)

    # 5. Administrador modifica estado de celda individual a MANTENIMIENTO
    lista = client.get("/api/v1/celdas/", headers=headers_admin).json()["celdas"]
    celda_71 = next((c for c in lista if c["codigo"] == "C-71"), None)
    assert celda_71 is not None
    res_patch = client.patch(f"/api/v1/celdas/{celda_71['celda_id']}", json={"estado": "MANTENIMIENTO"}, headers=headers_admin)
    assert res_patch.status_code == 200
    assert res_patch.json()["celda"]["estado"] == "MANTENIMIENTO"
