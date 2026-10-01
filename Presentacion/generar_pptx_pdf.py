import pptx
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor
import os

prs = Presentation()
# Set 16:9 ratio (10 inches by 5.625 inches)
prs.slide_width = Inches(10)
prs.slide_height = Inches(5.625)

BG_COLOR = RGBColor(15, 23, 42) # Dark navy blue
TEXT_COLOR = RGBColor(255, 255, 255)
ACCENT_COLOR = RGBColor(56, 189, 248) # Light blue accent
MUTED_COLOR = RGBColor(148, 163, 184) # Slate 400

# Classic Images
img_bartender = r"C:\Users\Snake\.gemini\antigravity-ide\brain\364b75f8-20d9-47ec-a117-26249bc64c86\classic_bartender_1789559574542.jpg"
img_shelf = r"C:\Users\Snake\.gemini\antigravity-ide\brain\364b75f8-20d9-47ec-a117-26249bc64c86\liquor_shelf_1789559586836.jpg"
img_manager = r"C:\Users\Snake\.gemini\antigravity-ide\brain\364b75f8-20d9-47ec-a117-26249bc64c86\restaurant_manager_1789559599532.jpg"
logo_path = r"d:\PWA Inventario Lovo\logo_lovo.png"

def add_bg(slide):
    background = slide.background
    fill = background.fill
    fill.solid()
    fill.fore_color.rgb = BG_COLOR
    if os.path.exists(logo_path):
        slide.shapes.add_picture(logo_path, Inches(8.5), Inches(0.3), height=Inches(0.4))

def add_text(slide, text, left, top, width, height, font_size=18, color=TEXT_COLOR, bold=False, align=PP_ALIGN.LEFT):
    txBox = slide.shapes.add_textbox(left, top, width, height)
    tf = txBox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = text
    p.font.size = Pt(font_size)
    p.font.color.rgb = color
    p.font.bold = bold
    p.alignment = align
    return txBox

def add_bullet(slide, text, left, top, width, height, font_size=16):
    txBox = slide.shapes.add_textbox(left, top, width, height)
    tf = txBox.text_frame
    tf.word_wrap = True
    for line in text.split('\n'):
        if line.strip():
            p = tf.add_paragraph()
            p.text = line
            p.font.size = Pt(font_size)
            p.font.color.rgb = TEXT_COLOR
            p.level = 0
    # Remove empty first paragraph
    if len(tf.paragraphs) > 1 and not tf.paragraphs[0].text.strip():
        # can't easily delete paragraph, so we just set its text to first line
        tf.paragraphs[0].text = tf.paragraphs[1].text
        tf.paragraphs[0].font.size = Pt(font_size)
        tf.paragraphs[0].font.color.rgb = TEXT_COLOR
        tf.paragraphs[0].level = 0
        p_element = tf.paragraphs[1]._element
        p_element.getparent().remove(p_element)
    return txBox

# ----------------- SLIDE 1: Title -----------------
slide = prs.slides.add_slide(prs.slide_layouts[6]) # Blank
add_bg(slide)
add_text(slide, "COCTELERÍA LOVO x MDEV", Inches(1), Inches(1.5), Inches(8), Inches(0.5), 14, ACCENT_COLOR, True, PP_ALIGN.CENTER)
add_text(slide, "Sistema Inteligente\nde Inventario por Voz", Inches(1), Inches(2), Inches(8), Inches(1.5), 36, TEXT_COLOR, True, PP_ALIGN.CENTER)
add_text(slide, "Propuesta técnica y financiera para automatizar el conteo nocturno y maximizar la rentabilidad operativa.", Inches(1.5), Inches(3.5), Inches(7), Inches(1), 16, MUTED_COLOR, False, PP_ALIGN.CENTER)

# ----------------- SLIDE 2: ROI -----------------
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide)
add_text(slide, "Retorno Inmediato de la Inversión", Inches(0.5), Inches(0.5), Inches(9), Inches(0.6), 28, ACCENT_COLOR, True)

# Box 1
add_text(slide, "552€", Inches(1), Inches(2), Inches(3), Inches(1), 60, ACCENT_COLOR, True, PP_ALIGN.CENTER)
add_text(slide, "Ahorro Neto Mensual", Inches(1), Inches(3), Inches(3), Inches(0.5), 18, TEXT_COLOR, True, PP_ALIGN.CENTER)

# Text Right
add_text(slide, "Reducción del 80% en Tiempo", Inches(5), Inches(1.8), Inches(4.5), Inches(0.5), 20, TEXT_COLOR, True)
add_text(slide, "Pasar de 12.5 horas semanales de personal a solo 1 hora gracias al dictado por voz directo en barra.\n\nEl modelo de suscripción (75€/mes) se autofinancia desde la primera semana de uso exclusivamente con el ahorro en horas extra.", Inches(5), Inches(2.4), Inches(4.5), Inches(2), 16, MUTED_COLOR)

# ----------------- SLIDE 3: El Problema -----------------
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide)
add_text(slide, "El Problema del Conteo Manual", Inches(0.5), Inches(0.5), Inches(9), Inches(0.6), 28, ACCENT_COLOR, True)

bullets = (
    "2.5 horas de madrugada: Hasta 5 empleados dedicados a contar botella por botella tras el cierre.\n"
    "Errores de transcripción: Mermas imprecisas al pasar datos de papel o notas manuales a Excel.\n"
    "Fatiga operacional: Tarea pesada que afecta el rendimiento del equipo en barra.\n"
    "Falta de tiempo real: Imposibilidad de tener stock actualizado antes de la llegada de proveedores."
)
add_bullet(slide, bullets, Inches(0.5), Inches(1.5), Inches(4.5), Inches(3.5), 14)

if os.path.exists(img_bartender):
    slide.shapes.add_picture(img_bartender, Inches(5.2), Inches(1.5), width=Inches(4.3), height=Inches(3.5))

# ----------------- SLIDE 4: Funcionalidades PWA -----------------
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide)
add_text(slide, "Funcionalidades Clave PWA", Inches(0.5), Inches(0.5), Inches(9), Inches(0.6), 28, ACCENT_COLOR, True)

add_text(slide, "Dictado por Voz", Inches(0.5), Inches(2), Inches(2.8), Inches(0.5), 18, TEXT_COLOR, True)
add_text(slide, "Conteo 100% manos libres. El camarero dicta productos directamente mientras manipula las botellas en barra.", Inches(0.5), Inches(2.5), Inches(2.8), Inches(2), 14, MUTED_COLOR)

add_text(slide, "Diccionario Fonético", Inches(3.6), Inches(2), Inches(2.8), Inches(0.5), 18, TEXT_COLOR, True)
add_text(slide, "Autocorrector inteligente entrenado para hostelería (transcribe p. ej. 'Jagger' a 'Jägermeister' automáticamente).", Inches(3.6), Inches(2.5), Inches(2.8), Inches(2), 14, MUTED_COLOR)

add_text(slide, "Multiusuario Real", Inches(6.7), Inches(2), Inches(2.8), Inches(0.5), 18, TEXT_COLOR, True)
add_text(slide, "Hasta 5 o más empleados contando simultáneamente distintas áreas sin sobrescribir información.", Inches(6.7), Inches(2.5), Inches(2.8), Inches(2), 14, MUTED_COLOR)

# ----------------- SLIDE 5: Barra vs Gerencial -----------------
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide)
add_text(slide, "Barra vs Control Gerencial", Inches(0.5), Inches(0.5), Inches(9), Inches(0.6), 28, ACCENT_COLOR, True)

add_text(slide, "Operativa en Barra", Inches(0.5), Inches(1.8), Inches(4), Inches(0.5), 20, TEXT_COLOR, True)
bullets_barra = (
    "Interfaz Modo Oscuro: Diseñada para la iluminación de Lovo sin deslumbrar.\n"
    "Cero Tecleo: Rapidez máxima con dictado continuo y categorías visuales dinámicas.\n"
    "Instalación PWA: Funciona directamente en iOS y Android sin pasar por app stores."
)
add_bullet(slide, bullets_barra, Inches(0.5), Inches(2.4), Inches(4.2), Inches(2.5), 14)

add_text(slide, "Control de Gerencia", Inches(5.3), Inches(1.8), Inches(4), Inches(0.5), 20, TEXT_COLOR, True)
bullets_gerencia = (
    "Exportación en 1 Clic: Compila y envía reportes automáticos en Excel al correo de contabilidad.\n"
    "Roles y Permisos: Camareros solo cuentan; encargados editan, auditan y gestionan datos.\n"
    "Seguridad Total: Servidor privado en la nube con copias de seguridad automáticas."
)
add_bullet(slide, bullets_gerencia, Inches(5.3), Inches(2.4), Inches(4.2), Inches(2.5), 14)

# ----------------- SLIDE 6: Costes -----------------
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide)
add_text(slide, "Análisis de Costes Operativos", Inches(0.5), Inches(0.5), Inches(9), Inches(0.6), 28, ACCENT_COLOR, True)

# Create a simple visual table
y_start = 1.8
spacing = 0.6
headers = ["Concepto", "Método Manual Tradicional", "Sistema Inteligente PWA", "Impacto / Ahorro"]
cols = [Inches(0.5), Inches(3.5), Inches(6.0), Inches(8.0)]

for i, h in enumerate(headers):
    add_text(slide, h, cols[i], Inches(y_start), Inches(2.5), Inches(0.5), 14, ACCENT_COLOR, True)

data = [
    ["Personal por Conteo", "5 personas", "2 personas", "-60% personal"],
    ["Tiempo por Inventario", "2.5 horas", "30 minutos", "-80% tiempo"],
    ["Horas Totales / Mes", "50 horas", "4 horas", "-46 horas/mes"],
    ["Coste Operativo / Mes", "600 € / mes", "48 € / mes", "Ahorro: 552 € / mes"]
]

for row_idx, row in enumerate(data):
    y = Inches(y_start + (row_idx + 1) * spacing)
    for col_idx, text in enumerate(row):
        color = TEXT_COLOR
        if row_idx == 3 and col_idx == 1: color = RGBColor(239, 68, 68) # Red
        if row_idx == 3 and col_idx == 2: color = RGBColor(34, 197, 94) # Green
        if col_idx == 3: color = ACCENT_COLOR
        add_text(slide, text, cols[col_idx], y, Inches(2.5), Inches(0.5), 14, color)

# ----------------- SLIDE 7: Inversion -----------------
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide)
add_text(slide, "Modelos de Inversión", Inches(1), Inches(2), Inches(8), Inches(1), 32, TEXT_COLOR, True, PP_ALIGN.CENTER)
add_text(slide, "Tres opciones transparentes adaptadas a las necesidades\nfinancieras y la visión de Coctelería Lovo.", Inches(1), Inches(3), Inches(8), Inches(1), 16, MUTED_COLOR, False, PP_ALIGN.CENTER)

# ----------------- SLIDE 8: Opciones -----------------
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide)
add_text(slide, "Opciones de Adquisición", Inches(0.5), Inches(0.5), Inches(9), Inches(0.6), 28, ACCENT_COLOR, True)

add_text(slide, "SaaS (Recomendado)", Inches(0.5), Inches(1.5), Inches(2.8), Inches(0.5), 18, ACCENT_COLOR, True)
add_text(slide, "75 €/mes (Setup: 350 €)\n\nInversión mínima inicial, servidores y soporte técnico continuo incluidos. Autofinanciado en la semana 1.", Inches(0.5), Inches(2.0), Inches(2.8), Inches(2.5), 14, MUTED_COLOR)

if os.path.exists(img_shelf):
    slide.shapes.add_picture(img_shelf, Inches(3.6), Inches(1.5), width=Inches(2.8), height=Inches(1.5))
add_text(slide, "Licencia Perpetua", Inches(3.6), Inches(3.1), Inches(2.8), Inches(0.5), 18, ACCENT_COLOR, True)
add_text(slide, "3.850 € (Pago único)\n\nLicencia vitalicia para Lovo sin cuotas de software. Amortización completa en apenas 7 meses.", Inches(3.6), Inches(3.6), Inches(2.8), Inches(2), 14, MUTED_COLOR)

if os.path.exists(img_manager):
    slide.shapes.add_picture(img_manager, Inches(6.7), Inches(1.5), width=Inches(2.8), height=Inches(1.5))
add_text(slide, "Propiedad Exclusiva", Inches(6.7), Inches(3.1), Inches(2.8), Inches(0.5), 18, ACCENT_COLOR, True)
add_text(slide, "9.500 € (Pago único)\n\nCesión total del código fuente, propiedad intelectual y contrato de exclusividad geográfica sectorial.", Inches(6.7), Inches(3.6), Inches(2.8), Inches(2), 14, MUTED_COLOR)

# ----------------- SLIDE 9: Puesta en Marcha -----------------
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide)
add_text(slide, "Puesta en Marcha Rápida", Inches(0.5), Inches(0.5), Inches(9), Inches(0.6), 28, ACCENT_COLOR, True)

add_text(slide, "Día 1: Catálogo", Inches(0.5), Inches(2), Inches(2.1), Inches(0.5), 16, ACCENT_COLOR, True)
add_text(slide, "Carga e importación inicial de la carta de licores y cristalería de Lovo.", Inches(0.5), Inches(2.4), Inches(2.1), Inches(1.5), 12, MUTED_COLOR)

add_text(slide, "Día 2: Diccionario", Inches(2.8), Inches(2), Inches(2.1), Inches(0.5), 16, ACCENT_COLOR, True)
add_text(slide, "Entrenamiento del motor de voz con marcas y jerga específica de la barra.", Inches(2.8), Inches(2.4), Inches(2.1), Inches(1.5), 12, MUTED_COLOR)

add_text(slide, "Día 3: Prueba", Inches(5.1), Inches(2), Inches(2.1), Inches(0.5), 16, ACCENT_COLOR, True)
add_text(slide, "Sesión práctica de 15 minutos con el equipo de camareros y encargados.", Inches(5.1), Inches(2.4), Inches(2.1), Inches(1.5), 12, MUTED_COLOR)

add_text(slide, "Día 4: Despliegue", Inches(7.4), Inches(2), Inches(2.1), Inches(0.5), 16, ACCENT_COLOR, True)
add_text(slide, "Lanzamiento oficial para el primer inventario inteligente en vivo.", Inches(7.4), Inches(2.4), Inches(2.1), Inches(1.5), 12, MUTED_COLOR)

# ----------------- SLIDE 10: Garantia -----------------
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide)
add_text(slide, "Garantía Piloto Cero Riesgo", Inches(0.5), Inches(0.5), Inches(9), Inches(0.6), 28, ACCENT_COLOR, True)

add_text(slide, "1 Inventario de Prueba Sin Compromiso", Inches(0.5), Inches(1.5), Inches(4.5), Inches(0.5), 18, TEXT_COLOR, True)
add_text(slide, "Cargamos la carta de Lovo y realizamos el próximo inventario real en vivo directamente en barra.\n\nSi el tiempo de conteo no se reduce a menos de la mitad y el equipo no queda encantado, no abonan absolutamente nada.", Inches(0.5), Inches(2.2), Inches(4.5), Inches(2.5), 14, MUTED_COLOR)

if os.path.exists(img_bartender):
    slide.shapes.add_picture(img_bartender, Inches(5.2), Inches(1.2), width=Inches(4.5), height=Inches(4))

# ----------------- SLIDE 11: Fin -----------------
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide)
add_text(slide, "¿Hacemos la prueba en barra?", Inches(1), Inches(2), Inches(8), Inches(0.8), 36, TEXT_COLOR, True, PP_ALIGN.CENTER)
add_text(slide, "Prueba la demo con reconocimiento por voz en tiempo real:\n\nMDev - Soluciones Tecnológicas | Marco Daza", Inches(1), Inches(3), Inches(8), Inches(1), 16, MUTED_COLOR, False, PP_ALIGN.CENTER)

prs.save("Presentacion_Voz_PDF.pptx")
