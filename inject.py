import sqlite3
import re
import math

data = """
GARRAFA 8L:
Leona 0.1
Nórdico 0.5
Sencha 0.2
Bandito 0.1

GARRAFA 8L
Pandam 0.2
S. Cítrica 0.7
J&7 0

GARRAFA 5L
Bourbon mantequilla 0
Mowgli 0.4
T&S 0.9
Pipa 0.8
Licor Salmon y E. 0.5
Bubi 0.1
Tequila Shisho 0.6
Caballo 0.7
Gin Matcha 0.4
Jazz 0.3
EO 0.2
Licor Herbal 0.5
L. Kaffir 0.7
Tortuga 0.5
Reno 0.4
L.lemongrass 0.9
Navajo 0.4
Tequila Shisho 0.6
Sami 0.1
Maorí 0.2
Sesahatan 0.4
S. Higuera 0.5
Expresso 0.5
Jupe 0.7
Samurai 0.3
Manabi 0.3
Masai 0.4
Cordial fresas 1
Serpiente 0

GARRAFA 2L
Z.Tomate Árbol 0.4
Agua tomate 0.2
S. HierbaLuisa 0.6
Fatwash Ron mantequilla 0.2
L. Café queso 1
Whisky plátano mantequilla 0.1
Mix Criollo 0.1
Plantain 0.1

BOTELLA 2L
S. Marraschino 0.4
S. Peras al horno 0
S. Plátano verde 0.4
Piparra 0.1
Orange l. 1
Mix amaros 0.8
Champs sin 0.6
Gin Fresas 0.5
Shunme Sin 0
L. Maíz morado 1.1
L. cacahuete 0.1
L. Mango picante 1
Festín Maya sin 0.1
Café 0.3
Té Hibiscus 0.8
Josephine sin 0.2
C.Hojicha 0.8
Pipa Sin 0
S. Tamarindo 0.2
C.Agua tomate 0.9
Yuzu Clarificado 0.9
Vermouth Calabaza 0.2
Watermelon highball 0.8
Nordico sin 0.7

GARRAFA 4L
S.simple 1
Pornstar 0.1
Mix Vodka 0
Mix Gin 0.2
S. Eneldo 0.9
Devil 0.8
Mix Ron 0
Long island 0
Mix Whisky 0.3

BOTELLA 700
Hellfire 0
Tint contriti 0.4

BOTELLA 500
Algarroba 0.5
Comino 0.8
Aceite plátano 0.4
S.salina 0.5
"""

records = []
current_group = ""
multiplier = 1

lines = data.strip().split('\n')
for line in lines:
    line = line.strip()
    if not line:
        continue
    
    # Check for group header
    if "GARRAFA" in line.upper() or "BOTELLA" in line.upper():
        current_group = line.replace(":", "").strip()
        match = re.search(r'(\d+)\s*L', current_group, re.IGNORECASE)
        if match:
            multiplier = int(match.group(1)) * 1000
        else:
            match = re.search(r'(\d+)', current_group)
            if match:
                multiplier = int(match.group(1))
            else:
                multiplier = 1
        continue
    
    # Process item line
    # Match product name and quantity at the end
    match = re.search(r'^(.*?)\s+([\d\.]+)$', line)
    if match:
        product = match.group(1).strip() + f" {current_group}"
        quantity = float(match.group(2))
        
        # Calculate final quantity based on the frontend logic we agreed on
        # If it's a garrafa or contains L, multiply it. If it's BOTELLA 700, multiply it? 
        # The user wanted equivalences for everything they sent.
        final_quantity = quantity * multiplier
        
        records.append({
            'categoria': 'Producciones',
            'producto': product,
            'cantidad_dictada': final_quantity,
            'fecha': '01/09/2026',
            'hora': '23:59:00',
            'usuario': 'Sergio'
        })

conn = sqlite3.connect('inventario.db')
cursor = conn.cursor()

inserted = 0
for r in records:
    # botellas_llenas and restante_porcentaje calculation
    botellas_llenas = int(r['cantidad_dictada'])
    restante = r['cantidad_dictada'] - botellas_llenas
    restante_str = f"{round(restante * 100)}%" if restante > 0 or "." in str(r['cantidad_dictada']) else "-"
    
    cursor.execute('''
        INSERT INTO registros (fecha, hora, categoria, producto, cantidad_dictada, botellas_llenas, restante_porcentaje, usuario)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (r['fecha'], r['hora'], r['categoria'], r['producto'], r['cantidad_dictada'], botellas_llenas, restante_str, r['usuario']))
    inserted += 1

conn.commit()
conn.close()
print(f"Successfully inserted {inserted} records.")
