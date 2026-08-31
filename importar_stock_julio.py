# -*- coding: utf-8 -*-
import math
import sqlite3
import pandas as pd

EXCEL_FILE = "STOCK JULIO.xlsx"
DB_FILE = "inventario.db"

def clean_quantity(val):
    if pd.isna(val) or val is None or str(val).strip() == "":
        return 0.0
    val_str = str(val).strip().upper().replace("O", "0").replace(",", ".")
    try:
        num = float(val_str)
        return max(0.0, num)
    except ValueError:
        return 0.0

def split_bottles_and_pct(cantidad):
    botellas_llenas = int(math.floor(cantidad))
    decimal_part = round(cantidad - botellas_llenas, 3)
    pct_val = int(round(decimal_part * 100))
    return botellas_llenas, f"{pct_val}%"

def get_aliases_dictionary(conn):
    try:
        df_dict = pd.read_sql_query("SELECT alias, real_name FROM Diccionario", conn)
        return dict(zip(df_dict['alias'].str.strip().str.lower(), df_dict['real_name'].str.strip()))
    except Exception:
        return {}

def parse_stock_lovo(excel_path, alias_dict):
    df = pd.read_excel(excel_path, sheet_name="Stock lovo", header=None)
    records = []
    current_category = "General"

    for idx, row in df.iterrows():
        col_b = str(row[1]).strip() if pd.notna(row[1]) else ""
        col_c = row[2]
        col_d = row[3]

        if not col_b or col_b.lower() == "producto":
            continue

        if col_b.isupper() and len(col_b) > 1 and (pd.isna(col_c) or str(col_c).strip() == "") and (pd.isna(col_d) or str(col_d).strip() == ""):
            current_category = col_b.title()
            continue

        cleaned_prod = alias_dict.get(col_b.lower(), col_b)
        qty = clean_quantity(col_c)
        botellas, pct = split_bottles_and_pct(qty)

        records.append({
            "fecha": "31/07/2026",
            "hora": "00:00:00",
            "categoria": current_category,
            "producto": cleaned_prod,
            "cantidad_dictada": qty,
            "botellas_llenas": botellas,
            "restante_porcentaje": pct,
            "usuario": "Importación Automática"
        })
    return records

def parse_cristaleria(excel_path, alias_dict):
    df = pd.read_excel(excel_path, sheet_name="Cristaleria")
    records = []
    item_cols = [c for c in df.columns if "VASOS" in str(c).upper() or "PRODUCTO" in str(c).upper()]
    total_cols = [c for c in df.columns if "TOTAL" in str(c).upper()]
    if not item_cols or not total_cols:
        return records

    for _, row in df.iterrows():
        item = str(row[item_cols[0]]).strip() if pd.notna(row[item_cols[0]]) else ""
        if not item or item.lower() == "nan":
            continue
        qty = clean_quantity(row[total_cols[0]])
        botellas, pct = split_bottles_and_pct(qty)
        records.append({
            "fecha": "31/07/2026",
            "hora": "00:00:00",
            "categoria": "Cristalería",
            "producto": alias_dict.get(item.lower(), item),
            "cantidad_dictada": qty,
            "botellas_llenas": botellas,
            "restante_porcentaje": pct,
            "usuario": "Importación Automática"
        })
    return records

def parse_stock_producciones(excel_path, alias_dict):
    df = pd.read_excel(excel_path, sheet_name="Stock producciones")
    records = []
    for _, row in df.iterrows():
        prod_b = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else ""
        qty_b = clean_quantity(row.iloc[2]) if len(row) > 2 else 0.0
        if prod_b and prod_b.lower() not in ["nan", "producto en botella", "producciones"]:
            botellas, pct = split_bottles_and_pct(qty_b)
            records.append({
                "fecha": "31/07/2026",
                "hora": "00:00:00",
                "categoria": "Producción Botellas",
                "producto": alias_dict.get(prod_b.lower(), prod_b),
                "cantidad_dictada": qty_b,
                "botellas_llenas": botellas,
                "restante_porcentaje": pct,
                "usuario": "Importación Automática"
            })

        prod_g = str(row.iloc[4]).strip() if len(row) > 4 and pd.notna(row.iloc[4]) else ""
        qty_g = clean_quantity(row.iloc[5]) if len(row) > 5 else 0.0
        if prod_g and prod_g.lower() not in ["nan", "garrafas"]:
            botellas, pct = split_bottles_and_pct(qty_g)
            records.append({
                "fecha": "31/07/2026",
                "hora": "00:00:00",
                "categoria": "Producción Garrafas",
                "producto": alias_dict.get(prod_g.lower(), prod_g),
                "cantidad_dictada": qty_g,
                "botellas_llenas": botellas,
                "restante_porcentaje": pct,
                "usuario": "Importación Automática"
            })
    return records

def run_import():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS RegistroInventario (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha TEXT NOT NULL,
        hora TEXT NOT NULL,
        categoria TEXT NOT NULL,
        producto TEXT NOT NULL,
        cantidad_dictada REAL NOT NULL,
        botellas_llenas INTEGER NOT NULL,
        restante_porcentaje TEXT NOT NULL,
        usuario TEXT NOT NULL
    )
    """)
    conn.commit()

    alias_dict = get_aliases_dictionary(conn)
    all_records = parse_stock_lovo(EXCEL_FILE, alias_dict) + parse_cristaleria(EXCEL_FILE, alias_dict) + parse_stock_producciones(EXCEL_FILE, alias_dict)

    print(f"Total registros listos: {len(all_records)}")
    insert_query = """
    INSERT INTO RegistroInventario 
    (fecha, hora, categoria, producto, cantidad_dictada, botellas_llenas, restante_porcentaje, usuario)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """
    batch_data = [
        (r["fecha"], r["hora"], r["categoria"], r["producto"], r["cantidad_dictada"], r["botellas_llenas"], r["restante_porcentaje"], r["usuario"])
        for r in all_records
    ]
    cursor.executemany(insert_query, batch_data)
    conn.commit()
    conn.close()
    print("✅ ¡Importación completada con éxito en SQLite!")

if __name__ == "__main__":
    run_import()