import os
import shutil
import sqlite3
import pytest
import hashlib

TEST_DB = "test_inventario.db"

# Setup db before server is fully initialized by other things
if os.path.exists("inventario.db"):
    shutil.copy("inventario.db", TEST_DB)
else:
    open(TEST_DB, 'w').close()

os.environ["DB_FILE"] = TEST_DB

import server
server.init_db()

conn = server.get_db_connection()
c = conn.cursor()
pwd = server.get_password_hash("testpass")
try:
    c.execute("INSERT INTO usuarios (dni, nombre, rol, password) VALUES (?, ?, ?, ?)",
              ("TESTADMIN", "Test Admin", "encargado", pwd))
except:
    c.execute("UPDATE usuarios SET password = ?, rol = ? WHERE dni = ?", (pwd, "encargado", "TESTADMIN"))
try:
     c.execute("INSERT INTO stock_referencia (categoria, producto, precio_unitario) VALUES (?, ?, ?)",
               ("TestCat", "Test Product", 10.0))
except:
     pass
conn.commit()
conn.close()

from fastapi.testclient import TestClient
from server import app

@pytest.fixture(scope="session", autouse=True)
def cleanup():
    yield
    if os.path.exists(TEST_DB):
        try:
            os.remove(TEST_DB)
        except:
            pass

@pytest.fixture
def client():
    return TestClient(app, raise_server_exceptions=True)

@pytest.fixture
def admin_token(client):
    response = client.post("/api/login", json={"dni": "TESTADMIN", "password": "testpass"})
    return response.json()["token"]

def test_login_success(client):
    response = client.post("/api/login", json={"dni": "TESTADMIN", "password": "testpass"})
    assert response.status_code == 200
    data = response.json()
    assert "token" in data

def test_login_failure(client):
    response = client.post("/api/login", json={"dni": "TESTADMIN", "password": "wrong"})
    assert response.status_code == 401

def test_get_categorias(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = client.get("/api/admin/categorias", headers=headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_productos(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = client.get("/api/productos", headers=headers)
    assert response.status_code == 200
    assert "productos" in response.json()

def test_get_diccionario(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = client.get("/api/admin/diccionario", headers=headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_guardar_inventario(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    payload = {
        "categoria": "TestCat",
        "producto": "Test Product",
        "cantidad_dictada": 2.5,
        "usuario": "TESTADMIN"
    }
    response = client.post("/api/registro", json=payload, headers=headers)
    assert response.status_code == 200
    
    # Verify in DB
    import server
    conn = server.get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM registros WHERE producto = 'Test Product'")
    rows = c.fetchall()
    conn.close()
    assert len(rows) > 0

def test_progreso_inventario(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    # Get today's date dynamically for this test
    from datetime import datetime
    today_str = datetime.now().strftime("%Y-%m-%d")
    response = client.get(f"/api/inventario/hoy?fecha={today_str}", headers=headers)
    assert response.status_code == 200

def test_descargar_hoy(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    # Download uses current date if none provided, or today_str from above
    from datetime import datetime
    today_str = datetime.now().strftime("%Y-%m-%d")
    response = client.get(f"/api/descargar/hoy?fecha={today_str}", headers=headers)
    print("STATUS:", response.status_code)
    print("BODY:", response.text)
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

def test_cierres_historico(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = client.get("/api/inventario/fechas", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert "fechas" in data

def test_borrar_historico(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    # Setup data
    import server
    conn = server.get_db_connection()
    c = conn.cursor()
    c.execute("INSERT INTO registros (fecha, hora, categoria, producto, cantidad_dictada, usuario) VALUES (?, ?, ?, ?, ?, ?)",
              ("01/01/1999", "12:00", "TestCat", "To Delete", 1.0, "TESTADMIN"))
    conn.commit()
    conn.close()
    # Delete
    response = client.delete("/api/inventario/historial?fecha=01/01/1999", headers=headers)
    assert response.status_code == 200
