import os
import sqlite3
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from openpyxl import Workbook
import json
import time

app = FastAPI(title="Inventario Bar API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_FILE = "inventario.db"

class Registro(BaseModel):
    categoria: str
    producto: str
    cantidad_dictada: float
    usuario: str = "Desconocido"

class LoginRequest(BaseModel):
    dni: str
    password: str

class NuevoUsuario(BaseModel):
    dni: str
    nombre: str
    password: str
    rol: str

class NuevaCategoria(BaseModel):
    nombre: str

class NuevoDiccionario(BaseModel):
    alias: str
    real_name: str

last_registro_time = 0.0
last_registro_payload = ""

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    # Registros
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS registros (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT,
            hora TEXT,
            categoria TEXT,
            producto TEXT,
            cantidad_dictada REAL,
            botellas_llenas INTEGER,
            restante_porcentaje TEXT,
            usuario TEXT
        )
    ''')
    # Usuarios
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dni TEXT UNIQUE,
            nombre TEXT,
            password TEXT,
            rol TEXT
        )
    ''')
    # Categorias
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categorias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT UNIQUE
        )
    ''')
    # Diccionario
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS diccionario (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            alias TEXT UNIQUE,
            real_name TEXT
        )
    ''')
    
    # Defaults
    cursor.execute('SELECT COUNT(*) FROM usuarios')
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO usuarios (dni, nombre, password, rol) VALUES (?, ?, ?, ?)", 
                       ("Z3738848L", "Marco Daza", "Lovo2026*", "encargado"))
                       
    cursor.execute('SELECT COUNT(*) FROM categorias')
    if cursor.fetchone()[0] == 0:
        default_cats = ["Cristalería", "Licores", "Refrescos", "Cervezas", "Destilados", "Zumos"]
        for cat in default_cats:
            cursor.execute("INSERT INTO categorias (nombre) VALUES (?)", (cat,))
            
    cursor.execute('SELECT COUNT(*) FROM diccionario')
    if cursor.fetchone()[0] == 0:
        default_dict = [("brugau", "Brugal"), ("barcelo", "Barceló"), ("tonica", "Tónica"), ("cocacola", "Coca-Cola")]
        for alias, real_name in default_dict:
            cursor.execute("INSERT INTO diccionario (alias, real_name) VALUES (?, ?)", (alias, real_name))

    conn.commit()
    conn.close()

@app.on_event("startup")
def startup_event():
    init_db()

@app.post("/api/login")
async def login(req: LoginRequest):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        dni_clean = req.dni.strip().upper()
        cursor.execute('SELECT nombre, password, rol FROM usuarios WHERE dni = ?', (dni_clean,))
        user = cursor.fetchone()
        conn.close()
        
        if user and user["password"] == req.password:
            return {"status": "success", "nombre": user["nombre"], "rol": user["rol"]}
            
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ----- ENDPOINTS REGISTROS -----

@app.post("/api/registro")
async def añadir_registro(registro: Registro):
    global last_registro_time, last_registro_payload
    payload_str = f"{registro.categoria}|{registro.producto}|{registro.cantidad_dictada}|{registro.usuario}"
    current_time = time.time()
    if payload_str == last_registro_payload and (current_time - last_registro_time) < 4.0:
        return {"status": "success", "message": "Registro duplicado ignorado por el servidor"}
    last_registro_payload = payload_str
    last_registro_time = current_time

    try:
        now = datetime.now()
        fecha = now.strftime("%d/%m/%Y")
        hora = now.strftime("%H:%M:%S")

        botellas_llenas = int(registro.cantidad_dictada)
        restante_porcentaje = round((registro.cantidad_dictada - botellas_llenas) * 100)

        if restante_porcentaje > 0 or "." in str(registro.cantidad_dictada):
            restante_str = f"{restante_porcentaje}%"
        else:
            botellas_llenas = int(registro.cantidad_dictada)
            restante_str = "-"

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO registros (fecha, hora, categoria, producto, cantidad_dictada, botellas_llenas, restante_porcentaje, usuario)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (fecha, hora, registro.categoria, registro.producto, registro.cantidad_dictada, botellas_llenas, restante_str, registro.usuario))
        conn.commit()
        conn.close()
        return {"status": "success", "message": "Registro añadido correctamente"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/registro/ultimo")
async def borrar_ultimo():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM registros ORDER BY id DESC LIMIT 1')
        row = cursor.fetchone()
        if row:
            cursor.execute('DELETE FROM registros WHERE id = ?', (row['id'],))
            conn.commit()
            conn.close()
            return {"status": "success", "message": "Último registro eliminado"}
        conn.close()
        return {"status": "warning", "message": "No hay registros"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/inventario/todo")
async def borrar_todo_inventario():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM registros')
        conn.commit()
        conn.close()
        return {"status": "success", "message": "Inventario borrado"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/inventario/hoy")
async def obtener_inventario_hoy():
    try:
        now = datetime.now()
        fecha_hoy = now.strftime("%d/%m/%Y")
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM registros WHERE fecha = ? ORDER BY hora DESC', (fecha_hoy,))
        rows = cursor.fetchall()
        conn.close()
        
        registros = []
        for row in rows:
            registros.append(dict(row))
        return {"registros": registros}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/productos")
async def obtener_productos_historicos():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT DISTINCT producto FROM registros')
        rows = cursor.fetchall()
        conn.close()
        lista = [r["producto"] for r in rows if r["producto"]]
        lista.sort()
        return {"productos": lista}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/descargar/hoy")
async def descargar_excel_hoy():
    try:
        now = datetime.now()
        fecha_hoy = now.strftime("%d/%m/%Y")
        fecha_archivo = now.strftime("%Y-%m-%d")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM registros WHERE fecha = ? ORDER BY categoria ASC, hora ASC', (fecha_hoy,))
        rows = cursor.fetchall()
        conn.close()
        
        wb_hoy = Workbook()
        wb_hoy.remove(wb_hoy.active)
        
        categorias_dict = {}
        for row in rows:
            cat = row["categoria"]
            if cat not in categorias_dict:
                categorias_dict[cat] = []
            categorias_dict[cat].append([row["fecha"], row["hora"], row["categoria"], row["producto"], row["cantidad_dictada"], row["botellas_llenas"], row["restante_porcentaje"], row["usuario"]])
            
        encabezados = ["Fecha", "Hora", "Categoría", "Producto", "Cantidad Dictada", "Botellas Llenas", "Restante (%)", "Usuario"]
        
        for cat, filas in categorias_dict.items():
            ws = wb_hoy.create_sheet(title=cat[:31])
            ws.append(encabezados)
            for f in filas: ws.append(f)
                
        if len(wb_hoy.sheetnames) == 0:
             ws = wb_hoy.create_sheet(title="Vacio")
             ws.append(["No hay registros hoy"])
                
        temp_file = f"Inventario_Hoy_{fecha_archivo}.xlsx"
        wb_hoy.save(temp_file)
        return FileResponse(path=temp_file, filename=temp_file, media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ----- ENDPOINTS ADMIN -----

@app.get("/api/admin/usuarios")
async def get_usuarios():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, dni, nombre, rol FROM usuarios')
    users = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return users

@app.post("/api/admin/usuarios")
async def crear_usuario(u: NuevoUsuario):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO usuarios (dni, nombre, password, rol) VALUES (?, ?, ?, ?)", (u.dni.strip().upper(), u.nombre, u.password, u.rol))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="El DNI ya existe")
    conn.close()
    return {"status": "success"}

@app.delete("/api/admin/usuarios/{uid}")
async def borrar_usuario(uid: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM usuarios WHERE id = ?', (uid,))
    conn.commit()
    conn.close()
    return {"status": "success"}

@app.get("/api/admin/categorias")
async def get_categorias():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, nombre FROM categorias')
    cats = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return cats

@app.post("/api/admin/categorias")
async def crear_categoria(c: NuevaCategoria):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO categorias (nombre) VALUES (?)", (c.nombre,))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="La categoría ya existe")
    conn.close()
    return {"status": "success"}

@app.delete("/api/admin/categorias/{cid}")
async def borrar_categoria(cid: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM categorias WHERE id = ?', (cid,))
    conn.commit()
    conn.close()
    return {"status": "success"}

@app.get("/api/admin/diccionario")
async def get_diccionario():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, alias, real_name FROM diccionario')
    d = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return d

@app.post("/api/admin/diccionario")
async def crear_diccionario(d: NuevoDiccionario):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO diccionario (alias, real_name) VALUES (?, ?)", (d.alias.lower(), d.real_name))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="El alias ya existe")
    conn.close()
    return {"status": "success"}

@app.delete("/api/admin/diccionario/{did}")
async def borrar_diccionario(did: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM diccionario WHERE id = ?', (did,))
    conn.commit()
    conn.close()
    return {"status": "success"}

# Servir archivos estáticos del frontend en la raíz
app.mount("/", StaticFiles(directory=".", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
