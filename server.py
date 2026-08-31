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
from fastapi import Depends, UploadFile, File, Form
from typing import Optional

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

class NuevaReceta(BaseModel):
    nombre: str
    ingredientes: str
    procedimiento: str
    coste: str
    categoria: str

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
    # Recetas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS recetas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT UNIQUE,
            ingredientes TEXT,
            procedimiento TEXT,
            coste TEXT,
            categoria TEXT
        )
    ''')
    
    # Stock de Referencia
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stock_referencia (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            producto TEXT UNIQUE,
            categoria TEXT,
            stock_anterior REAL,
            precio_unitario REAL
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
    load_stock_referencia(conn)
    inicializar_stock_julio(conn)
    sincronizar_categorias(conn)
    conn.close()

def sincronizar_categorias(conn):
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT categoria FROM registros WHERE categoria IS NOT NULL AND categoria != ''")
        categorias_usadas = cursor.fetchall()
        for row in categorias_usadas:
            cat = row[0].strip()
            cursor.execute("SELECT COUNT(*) FROM categorias WHERE nombre = ?", (cat,))
            if cursor.fetchone()[0] == 0:
                cursor.execute("INSERT INTO categorias (nombre) VALUES (?)", (cat,))
        conn.commit()
    except Exception as e:
        print("Error sincronizando categorias:", e)

def inicializar_stock_julio(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM registros WHERE fecha = '31/07/2026'")
    if cursor.fetchone()[0] > 0:
        return "Ya existe"
        
    import os
    if not os.path.exists("STOCK JULIO.xlsx"):
        return "No existe el archivo"
        
    try:
        import pandas as pd
        import math
        
        cursor.execute("SELECT alias, real_name FROM diccionario")
        dic_rows = cursor.fetchall()
        diccionario = {row['alias'].lower(): row['real_name'] for row in dic_rows}

        def normalizar_producto(nombre_raw):
            if not isinstance(nombre_raw, str): return ""
            clean = nombre_raw.strip().lower()
            return diccionario.get(clean, nombre_raw.strip())
            
        def clean_quantity(val):
            if pd.isna(val) or val is None or str(val).strip() == "": return 0.0
            val_str = str(val).strip().upper().replace("O", "0").replace(",", ".")
            try: return max(0.0, float(val_str))
            except: return 0.0
            
        def split_bottles_and_pct(cantidad):
            botellas_llenas = int(math.floor(cantidad))
            decimal_part = round(cantidad - botellas_llenas, 3)
            pct_val = int(round(decimal_part * 100))
            return botellas_llenas, f"{pct_val}%"
            
        dfs = pd.read_excel("STOCK JULIO.xlsx", sheet_name=None)
        
        records = []
        
        if 'Stock lovo' in dfs:
            hojas_detectadas.append('Stock lovo')
            df = dfs['Stock lovo']
            df.columns = df.columns.astype(str).str.strip().str.lower()
            if 'articulos' in df.columns and 'botellas llenas' in df.columns:
                for _, row in df.iterrows():
                    prod = row['articulos']
                    if pd.isna(prod): continue
                    producto_real = normalizar_producto(str(prod))
                    llenas = row['botellas llenas']
                    try:
                        llenas_val = int(llenas) if pd.notna(llenas) else 0
                    except:
                        llenas_val = 0
                    restante = row.get('botella empezada (%)', row.get('botella empezada'))
                    try:
                        restante_val = float(restante) * 100 if isinstance(restante, float) and pd.notna(restante) else (float(restante) if pd.notna(restante) else 0.0)
                        if math.isnan(restante_val): restante_val = 0.0
                    except:
                        restante_val = 0.0
                    
                    nuevos_registros.append((
                        fecha, "00:00", "Spirits / Licores", producto_real, 
                        f"Llenas: {llenas_val}, Restante: {restante_val}%", 
                        llenas_val, float(restante_val), user.get("nombre", "Sistema")
                    ))
            elif 'producto' in df.columns and 'total' in df.columns:
                for _, row in df.iterrows():
                    prod = row['producto']
                    if pd.isna(prod): continue
                    if pd.isna(row['total']): continue # Separator rows
                    producto_real = normalizar_producto(str(prod))
                    total_val = float(row['total']) if pd.notna(row['total']) else 0.0
                    llenas_val = int(total_val)
                    restante_val = (total_val - llenas_val) * 100
                    nuevos_registros.append((
                        fecha, "00:00", "Spirits / Licores", producto_real, 
                        f"Llenas: {llenas_val}, Restante: {restante_val:.0f}%", 
                        llenas_val, float(restante_val), user.get("nombre", "Sistema")
                    ))
        
        if 'Cristaleria' in dfs:
            hojas_detectadas.append('Cristaleria')
            df = dfs['Cristaleria']
            df.columns = df.columns.astype(str).str.strip().str.lower()
            col_prod = 'articulos' if 'articulos' in df.columns else ('cristaleria' if 'cristaleria' in df.columns else None)
            
            if col_prod and 'unidades' in df.columns:
                for _, row in df.iterrows():
                    prod = row[col_prod]
                    if pd.isna(prod): continue
                    producto_real = normalizar_producto(str(prod))
                    unidades = row['unidades']
                    try:
                        llenas_val = int(unidades) if pd.notna(unidades) else 0
                    except:
                        llenas_val = 0
                    
                    nuevos_registros.append((
                        fecha, "00:00", "Cristaleria / Vinos", producto_real, 
                        f"Unidades: {llenas_val}", 
                        llenas_val, 0.0, user.get("nombre", "Sistema")
                    ))
            elif 'producto' in df.columns and 'total' in df.columns:
                for _, row in df.iterrows():
                    prod = row['producto']
                    if pd.isna(prod): continue
                    if pd.isna(row['total']): continue
                    producto_real = normalizar_producto(str(prod))
                    llenas_val = int(float(row['total']) if pd.notna(row['total']) else 0.0)
                    nuevos_registros.append((
                        fecha, "00:00", "Cristaleria / Vinos", producto_real, 
                        f"Unidades: {llenas_val}", 
                        llenas_val, 0.0, user.get("nombre", "Sistema")
                    ))
                    
        if 'Stock producciones' in dfs:
            hojas_detectadas.append('Stock producciones')
            df = dfs['Stock producciones']
            df.columns = df.columns.astype(str).str.strip().str.lower()
            col_prod = 'articulos' if 'articulos' in df.columns else ('producciones' if 'producciones' in df.columns else None)
            
            if col_prod and 'unidades' in df.columns:
                for _, row in df.iterrows():
                    prod = row[col_prod]
                    if pd.isna(prod): continue
                    producto_real = normalizar_producto(str(prod))
                    unidades = row['unidades']
                    try:
                        llenas_val = int(unidades) if pd.notna(unidades) else 0
                    except:
                        llenas_val = 0
                    
                    nuevos_registros.append((
                        fecha, "00:00", "Producciones / Batch", producto_real, 
                        f"Unidades: {llenas_val}", 
                        llenas_val, 0.0, user.get("nombre", "Sistema")
                    ))
            elif 'producto' in df.columns and 'total' in df.columns:
                for _, row in df.iterrows():
                    prod = row['producto']
                    if pd.isna(prod): continue
                    if pd.isna(row['total']): continue
                    producto_real = normalizar_producto(str(prod))
                    llenas_val = int(float(row['total']) if pd.notna(row['total']) else 0.0)
                    nuevos_registros.append((
                        fecha, "00:00", "Producciones / Batch", producto_real, 
                        f"Unidades: {llenas_val}", 
                        llenas_val, 0.0, user.get("nombre", "Sistema")
                    ))
        if nuevos_registros:
            cursor.executemany('''
                INSERT INTO registros (fecha, hora, categoria, producto, cantidad_dictada, botellas_llenas, restante_porcentaje, usuario)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', nuevos_registros)
            conn.commit()
            conn.close()
            return {"message": f"Excel importado. Hojas procesadas: {', '.join(hojas_detectadas)}. {len(nuevos_registros)} registros guardados."}
        else:
            conn.close()
            raise HTTPException(status_code=400, detail="No se encontraron datos compatibles en el Excel.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error importando Excel: {str(e)}")

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

# ----- ENDPOINTS LABORATORIO / RECETAS -----

@app.get("/api/recetas")
def get_recetas(user: dict = Depends(check_is_produccion_or_admin)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM recetas')
    rows = cursor.fetchall()
    conn.close()
    recetas = []
    for r in rows:
        receta = dict(r)
        if user.get("rol") != "encargado":
            receta["coste"] = "***" # Ocultar coste
        recetas.append(receta)
    return recetas

@app.post("/api/recetas")
def crear_receta(r: NuevaReceta, user: dict = Depends(check_is_admin)):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO recetas (nombre, ingredientes, procedimiento, coste, categoria) VALUES (?, ?, ?, ?, ?)", 
                       (r.nombre, r.ingredientes, r.procedimiento, r.coste, r.categoria))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="La receta ya existe")
    conn.close()
    return {"status": "success"}

@app.delete("/api/recetas/{rid}")
def borrar_receta(rid: int, user: dict = Depends(check_is_admin)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM recetas WHERE id = ?', (rid,))
    conn.commit()
    conn.close()
    return {"status": "success"}

@app.post("/api/recetas/{rid}/producir")
def producir_receta(rid: int, user: dict = Depends(check_is_produccion_or_admin)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT nombre, categoria FROM recetas WHERE id = ?', (rid,))
    receta = cursor.fetchone()
    if not receta:
        conn.close()
        raise HTTPException(status_code=404, detail="Receta no encontrada")
    
    # Registrar en el inventario como 1 botella/lote producido
    now = datetime.now()
    fecha = now.strftime("%d/%m/%Y")
    hora = now.strftime("%H:%M:%S")
    
    cursor.execute('''
        INSERT INTO registros (fecha, hora, categoria, producto, cantidad_dictada, botellas_llenas, restante_porcentaje, usuario)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (fecha, hora, receta["categoria"], receta["nombre"], 1.0, 1, "-", f'{user.get("nombre")} (Lab)'))
    
    conn.commit()
    conn.close()
    return {"status": "success", "message": "Lote registrado en inventario"}

# Servir archivos estáticos del frontend en la raíz
app.mount("/", StaticFiles(directory=".", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
