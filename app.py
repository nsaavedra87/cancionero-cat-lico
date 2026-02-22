import streamlit as st
import pandas as pd
import os
import re
from PIL import Image

# --- CONFIGURACIÓN DE ARCHIVOS ---
DB_FILE = "cancionero.csv"
CAT_FILE = "categorias.csv"

# --- FUNCIONES DE DATOS ---
def cargar_datos():
    try:
        if os.path.exists(DB_FILE) and os.path.getsize(DB_FILE) > 0:
            return pd.read_csv(DB_FILE)
    except Exception: pass
    return pd.DataFrame(columns=["Título", "Autor", "Categoría", "Letra"])

def cargar_categorias():
    cat_emergencia = ["Alabanza", "Adoracion", "Oracion", "Eucaristia", "Maria"]
    try:
        if os.path.exists(CAT_FILE) and os.path.getsize(CAT_FILE) > 5:
            df_cat = pd.read_csv(CAT_FILE)
            return df_cat.iloc[:, 0].dropna().unique().tolist()
    except Exception: pass
    return cat_emergencia

def guardar_datos(df):
    df.to_csv(DB_FILE, index=False)

# --- LÓGICA DE PROCESAMIENTO MEJORADA ---
NOTAS = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

def procesar_texto(texto, semitonos, color_acorde):
    if not texto: return ""
    
    # Patrón para detectar acordes (C, Dm, G7, etc. y también notación Do, Re, Mi)
    patron = r"\b([A-G][#b]?(m|maj|7|9|sus\d|dim|aug|add\d)?)\b"
    
    def reemplazar(match):
        acorde = match.group(1)
        match_nota = re.match(r"([A-G][#b]?)", acorde)
        nota_original = match_nota.group(1)
        dic_bemoles = {"Db": "C#", "Eb": "D#", "Gb": "F#", "Ab": "G#", "Bb": "A#"}
        nota_base = dic_bemoles.get(nota_original, nota_original)
        
        if nota_base in NOTAS and semitonos != 0:
            nueva_nota = NOTAS[(NOTAS.index(nota_base) + semitonos) % 12]
            acorde = nueva_nota + acorde[len(nota_original):]
        
        return f'<span style="color:{color_acorde}; font-weight:bold;">{acorde}</span>'
    
    lineas = texto.split('\n')
    lineas_procesadas = []
    
    for linea in lineas:
        # 1. SOLUCIÓN BARRA BLANCA: Si la línea está vacía o solo tiene espacios, 
        # ponemos un espacio de no-ruptura para que el navegador no cree un bloque vacío.
        if not linea.strip():
            lineas_procesadas.append("&nbsp;")
            continue
        
        # 2. Procesar acordes en la línea
        linea_color = re.sub(patron, reemplazar, linea)
        
        # 3. SOLUCIÓN ALINEACIÓN: Reemplazamos espacios normales por espacios rígidos (&nbsp;)
        # Esto evita que el navegador colapse múltiples espacios en uno solo.
        linea_final = linea_color.replace(" ", "&nbsp;")
        lineas_procesadas.append(linea_final)
        
    return "<br>".join(lineas_procesadas)

def limpiar_texto(t):
    t = re.sub(r'[^\w\s#+m7áéíóúÁÉÍÓÚñÑ.,\-()|/]', '', t)
    return t.strip()

# --- INTERFAZ ---
st.set_page_config(page_title="ChordMaster Pro", page_icon="🎸", layout="wide")

# CSS Ajustado
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono&family=Montserrat:wght@700&display=swap');
    [data-testid="stHeader"] {{ visibility: hidden; }}
    
    /* El editor DEBE tener la misma fuente que el visor para que la alineación coincida */
    textarea {{
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 16px !important;
        line-height: 1.2 !important;
    }}
    
    .visor-musical {{
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0px 4px 15px rgba(0,0,0,0.3);
        border: 1px solid #444;
        line-height: 1.2;
        overflow-x: auto;
        word-wrap: break-word;
        white-space: pre-wrap; /* Mantiene la estructura pero permite salto si es muy largo */
    }}
    .titulo-visor {{ font-family: 'Montserrat', sans-serif; margin-bottom: 0px; line-height: 1.0; font-size: 1.5em; }}
    .autor-visor {{ color: #777; margin-bottom: 5px; font-size: 0.85em; }}
    </style>
    """, unsafe_allow_html=True)

# ... (El resto de tu lógica de carga de datos y sidebar se mantiene igual)
