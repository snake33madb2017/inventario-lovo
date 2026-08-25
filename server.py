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
import bcrypt
import smtplib
import ssl
from email.message import EmailMessage
import jwt
from datetime import timedelta
from fastapi import Depends

app = FastAPI(title="Inventario Bar API")

SECRET_KEY = "super_secreto_lovo_2026_cambiar_en_prod"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 # 24 horas

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import os
# Si existe la carpeta /data (Disco de Render), usamos esa ruta. Si no, ruta local.
DB_DIR = "/data" if os.path.exists("/data") else "."
DB_FILE = os.path.join(DB_DIR, "inventario.db")

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
    conn = sqlite3.connect(DB_FILE, timeout=10.0)
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
                       ("Z3738848L", "Marco Daza", get_password_hash("Lovo2026*"), "encargado"))
                       
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

from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        dni: str = payload.get("sub")
        if dni is None:
            raise HTTPException(status_code=401, detail="Token inválido")
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token inválido")

def check_is_admin(user: dict = Depends(get_current_user)):
    if user.get("rol") != "encargado":
        raise HTTPException(status_code=403, detail="Permisos insuficientes")
    return user

@app.post("/api/login")
def login(req: LoginRequest):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        dni_clean = req.dni.strip().upper()
        cursor.execute('SELECT nombre, password, rol FROM usuarios WHERE dni = ?', (dni_clean,))
        user = cursor.fetchone()
        conn.close()
        
        if user and verify_password(req.password, user["password"]):
            access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = create_access_token(
                data={"sub": dni_clean, "nombre": user["nombre"], "rol": user["rol"]}, expires_delta=access_token_expires
            )
            return {"status": "success", "nombre": user["nombre"], "rol": user["rol"], "token": access_token}
            
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ----- ENDPOINTS REGISTROS -----

@app.post("/api/registro")
def añadir_registro(registro: Registro, user: dict = Depends(get_current_user)):
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
def borrar_ultimo(user: dict = Depends(get_current_user)):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if user.get("rol") == "encargado":
            cursor.execute('SELECT id FROM registros ORDER BY id DESC LIMIT 1')
        else:
            cursor.execute('SELECT id FROM registros WHERE usuario = ? ORDER BY id DESC LIMIT 1', (user.get("nombre"),))
            
        row = cursor.fetchone()
        if row:
            cursor.execute('DELETE FROM registros WHERE id = ?', (row['id'],))
            conn.commit()
            conn.close()
            return {"status": "success", "message": "Último registro eliminado"}
        conn.close()
        return {"status": "warning", "message": "No hay registros tuyos para borrar"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/inventario/todo")
def borrar_todo_inventario(user: dict = Depends(check_is_admin)):
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
def obtener_inventario_hoy(user: dict = Depends(get_current_user)):
    try:
        now = datetime.now()
        fecha_hoy = now.strftime("%d/%m/%Y")
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM registros WHERE fecha = ? ORDER BY hora DESC LIMIT 150', (fecha_hoy,))
        rows = cursor.fetchall()
        conn.close()
        
        registros = []
        for row in rows:
            registros.append(dict(row))
        return {"registros": registros}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/productos")
def obtener_productos_historicos(user: dict = Depends(get_current_user)):
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
def descargar_excel_hoy(user: dict = Depends(check_is_admin)):
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
        
        import re
        for cat, filas in categorias_dict.items():
            cat_safe = re.sub(r'[\\*?:/\[\]]', '', cat)[:31]
            if not cat_safe:
                cat_safe = "Categoria"
            ws = wb_hoy.create_sheet(title=cat_safe)
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

@app.post("/api/admin/enviar-excel")
def enviar_excel_correo(user: dict = Depends(check_is_admin)):
    sender_email = os.getenv("SMTP_EMAIL")
    sender_password = os.getenv("SMTP_PASSWORD")
    receiver_email = os.getenv("SMTP_DESTINATION")

    if not sender_email or not sender_password or not receiver_email:
        raise HTTPException(status_code=400, detail="El correo no está configurado en el servidor (faltan variables SMTP).")

    try:
        now = datetime.now()
        fecha_hoy = now.strftime("%d/%m/%Y")
        fecha_archivo = now.strftime("%Y-%m-%d")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM registros WHERE fecha = ? ORDER BY categoria ASC, hora ASC', (fecha_hoy,))
        rows = cursor.fetchall()
        conn.close()
        
        wb = Workbook()
        wb.remove(wb.active)
        
        categorias_dict = {}
        for row in rows:
            cat = row["categoria"]
            if cat not in categorias_dict: categorias_dict[cat] = []
            categorias_dict[cat].append([row["fecha"], row["hora"], row["categoria"], row["producto"], row["cantidad_dictada"], row["botellas_llenas"], row["restante_porcentaje"], row["usuario"]])
            
        encabezados = ["Fecha", "Hora", "Categoría", "Producto", "Cantidad Dictada", "Botellas Llenas", "Restante (%)", "Usuario"]
        
        import re
        for cat, filas in categorias_dict.items():
            cat_safe = re.sub(r'[\\*?:/\[\]]', '', cat)[:31]
            if not cat_safe: cat_safe = "Categoria"
            ws = wb.create_sheet(title=cat_safe)
            ws.append(encabezados)
            for f in filas: ws.append(f)
                
        if len(wb.sheetnames) == 0:
             ws = wb.create_sheet(title="Vacio")
             ws.append(["No hay registros hoy"])
                
        temp_file = f"Inventario_Hoy_{fecha_archivo}.xlsx"
        wb.save(temp_file)

        # Enviar por correo
        msg = EmailMessage()
        msg['Subject'] = f'Inventario Lovo - {fecha_hoy}'
        msg['From'] = sender_email
        msg['To'] = receiver_email
        msg.set_content(f"Hola,\n\nAdjunto el inventario del día {fecha_hoy} generado automáticamente por el sistema.\n\nSaludos,\nInventario Coctelería Lovo")

        with open(temp_file, 'rb') as f:
            file_data = f.read()
            
        msg.add_attachment(file_data, maintype='application', subtype='vnd.openxmlformats-officedocument.spreadsheetml.sheet', filename=temp_file)

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(sender_email, sender_password)
            server.send_message(msg)

        os.remove(temp_file)
        return {"status": "success", "message": "Correo enviado correctamente."}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al enviar correo: {str(e)}")

# ----- ENDPOINTS ADMIN -----

@app.get("/api/admin/usuarios")
def get_usuarios(user: dict = Depends(check_is_admin)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, dni, nombre, rol FROM usuarios')
    users = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return users

@app.post("/api/admin/usuarios")
def crear_usuario(u: NuevoUsuario, user: dict = Depends(check_is_admin)):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO usuarios (dni, nombre, password, rol) VALUES (?, ?, ?, ?)", (u.dni.strip().upper(), u.nombre, get_password_hash(u.password), u.rol))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="El DNI ya existe")
    conn.close()
    return {"status": "success"}

@app.delete("/api/admin/usuarios/{uid}")
def borrar_usuario(uid: int, user: dict = Depends(check_is_admin)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM usuarios WHERE id = ?', (uid,))
    conn.commit()
    conn.close()
    return {"status": "success"}

@app.get("/api/admin/categorias")
def get_categorias(user: dict = Depends(check_is_admin)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, nombre FROM categorias')
    cats = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return cats

@app.post("/api/admin/categorias")
def crear_categoria(c: NuevaCategoria, user: dict = Depends(check_is_admin)):
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
def borrar_categoria(cid: int, user: dict = Depends(check_is_admin)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM categorias WHERE id = ?', (cid,))
    conn.commit()
    conn.close()
    return {"status": "success"}

@app.get("/api/admin/diccionario")
def get_diccionario(user: dict = Depends(check_is_admin)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, alias, real_name FROM diccionario')
    d = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return d

@app.post("/api/admin/diccionario")
def crear_diccionario(d: NuevoDiccionario, user: dict = Depends(check_is_admin)):
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
def borrar_diccionario(did: int, user: dict = Depends(check_is_admin)):
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
