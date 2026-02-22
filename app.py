import streamlit as st
import pandas as pd
import os
import re

# --- CONFIGURACIÓN DE ARCHIVOS ---
DB_FILE = "cancionero.csv"
CAT_FILE = "categorias.csv"

def cargar_datos():
    try:
        if os.path.exists(DB_FILE) and os.path.getsize(DB_FILE) > 0:
            return pd.read_csv(DB_FILE)
    except Exception: pass
    return pd.DataFrame(columns=["Título", "Autor", "Categoría", "Letra"])

def cargar_categorias():
    cat_emergencia = ["Entrada", "Piedad", "Gloria", "Aleluya", "Ofertorio", "Santo", "Cordero", "Comunión", "Salida", "Adoración", "María"]
    try:
        if os.path.exists(CAT_FILE) and os.path.getsize(CAT_FILE) > 0:
            df_cat = pd.read_csv(CAT_FILE)
            return df_cat.iloc[:, 0].dropna().unique().tolist()
    except Exception: pass
    return cat_emergencia

def guardar_datos(df):
    df.to_csv(DB_FILE, index=False)

# --- MOTOR DE TRANSPOSICIÓN INTELIGENTE ---
NOTAS_AMER = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
NOTAS_LAT = ["Do", "Do#", "Re", "Re#", "Mi", "Fa", "Fa#", "Sol", "Sol#", "La", "La#", "Si"]

def transportar_nota(nota, semitonos):
    if nota in NOTAS_AMER:
        idx = (NOTAS_AMER.index(nota) + semitonos) % 12
        return NOTAS_AMER[idx]
    elif nota in NOTAS_LAT:
        idx = (NOTAS_LAT.index(nota) + semitonos) % 12
        return NOTAS_LAT[idx]
    return nota

def procesar_texto_estricto(texto, semitonos, color_acorde):
    if not texto: return ""
    
    # PATRÓN INTELIGENTE: Detecta acordes solo si tienen sufijos musicales 
    # o si están aislados por más de un espacio (típico de cifrados)
    patron = r"(?<=^| {2})\b(Do#?|Re#?|Mi|Fa#?|Sol#?|La#?|Si|[A-G][#b]?)([Mm]|maj7|maj|7|9|sus4|sus2|dim|aug|add9)?\b(?=$| {1})"
    
    lineas = texto.split('\n')
    lineas_procesadas = []

    for linea in lineas:
        if not linea.strip():
            lineas_procesadas.append("&nbsp;")
            continue

        def aplicar_cambios(match):
            nota_raiz = match.group(1)
            modo = match.group(2) if match.group(2) else ""
            
            dic_bemoles = {"Db": "C#", "Eb": "D#", "Gb": "F#", "Ab": "G#", "Bb": "A#"}
            nota_raiz_busqueda = dic_bemoles.get(nota_raiz, nota_raiz)
            
            nueva_nota = transportar_nota(nota_raiz_busqueda, semitonos) if semitonos != 0 else nota_raiz
            acorde_final = nueva_nota + modo
            
            # Aplicamos el color directamente aquí
            return f'<strong style="color:{color_acorde};">{acorde_final}</strong>'

        # 1. Transportar y colorear solo lo que parezca acorde
        linea_final = re.sub(patron, aplicar_cambios, linea)
        
        # 2. Respetar espacios para alineación
        linea_final = linea_final.replace(" ", "&nbsp;")
        lineas_procesadas.append(linea_final)
        
    return "<br>".join(lineas_procesadas)

# --- INTERFAZ ---
st.set_page_config(page_title="ChordMaster Pro", layout="wide")

# CSS MEJORADO: Inyectamos el color de los acordes dinámicamente
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono&display=swap');
    textarea { font-family: 'JetBrains Mono', monospace !important; }
    .visor-musical { 
        border-radius: 12px; 
        padding: 25px; 
        line-height: 1.4; 
        font-family: 'JetBrains Mono', monospace !important; 
        overflow-x: auto;
    }
    </style>
    """, unsafe_allow_html=True)

df = cargar_datos()
categorias = cargar_categorias()

# --- SIDEBAR ---
st.sidebar.title("🎸 Panel de Control")
menu = st.sidebar.selectbox("Ir a:", ["🏠 Cantar", "➕ Agregar", "📂 Gestionar"])

c_bg = st.sidebar.color_picker("Color de Fondo", "#121212")
c_txt = st.sidebar.color_picker("Color de Letra", "#FFFFFF")
c_chord = st.sidebar.color_picker("Color de Acordes", "#FFD700")
f_size = st.sidebar.slider("Tamaño de Fuente", 14, 40, 22)

# --- MÓDULO CANTAR ---
if menu == "🏠 Cantar":
    col_f1, col_f2 = st.columns([2, 1])
    busq = col_f1.text_input("🔍 Buscar...")
    f_cat = col_f2.selectbox("📂 Categoría", ["Todas"] + categorias)
    
    df_v = df.copy()
    if busq: df_v = df_v[df_v['Título'].str.contains(busq, case=False) | df_v['Autor'].str.contains(busq, case=False)]
    if f_cat != "Todas": df_v = df_v[df_v['Categoría'] == f_cat]

    if not df_v.empty:
        sel = st.selectbox("Elegir canción:", df_v['Título'])
        cancion = df_v[df_v['Título'] == sel].iloc[0]
        
        st.sidebar.divider()
        tp = st.sidebar.number_input("Transportar Tonalidad", -6, 6, 0)
        
        # PROCESAMIENTO
        html_final = procesar_texto_estricto(cancion['Letra'], tp, c_chord)
        
        st.markdown(f'''
            <div class="visor-musical" style="background-color:{c_bg}; color:{c_txt}; font-size:{f_size}px;">
                <div style="border-bottom: 1px solid #444; margin-bottom: 15px; padding-bottom: 5px;">
                    <b style="font-size: 1.3em;">{cancion["Título"]}</b><br>
                    <span style="color: gray;">{cancion["Autor"]} | {cancion["Categoría"]}</span>
                </div>
                {html_final}
            </div>
        ''', unsafe_allow_html=True)

# --- MÓDULO AGREGAR ---
elif menu == "➕ Agregar":
    st.header("➕ Nueva Canción")
    c1, c2, c3 = st.columns(3)
    t_n = c1.text_input("Título")
    a_n = c2.text_input("Autor")
    cat_n = c3.selectbox("Categoría", categorias)
    letra_n = st.text_area("Pega aquí la letra con acordes:", height=300, help="Importante: Deja al menos dos espacios entre la letra y el acorde para que el sistema lo reconozca.")
    
    if letra_n:
        st.subheader("Vista Previa")
        preview = procesar_texto_estricto(letra_n, 0, c_chord)
        st.markdown(f'<div class="visor-musical" style="background-color:{c_bg}; color:{c_txt}; font-size:{f_size}px;">{preview}</div>', unsafe_allow_html=True)
        
        if st.button("Guardar Canción"):
            nueva_fila = pd.DataFrame([[t_n, a_n if a_n else "Anónimo", cat_n, letra_n]], columns=df.columns)
            df = pd.concat([df, nueva_fila], ignore_index=True)
            guardar_datos(df)
            st.success("Canción guardada correctamente.")
            st.rerun()

# --- MÓDULO GESTIONAR ---
elif menu == "📂 Gestionar":
    st.header("📂 Biblioteca")
    for i, r in df.iterrows():
        with st.expander(f"{r['Título']} ({r['Autor']})"):
            new_l = st.text_area("Editar contenido:", r['Letra'], key=f"edit_{i}")
            if st.button("Guardar cambios", key=f"btn_{i}"):
                df.at[i, 'Letra'] = new_l
                guardar_datos(df)
                st.rerun()
            if st.button("Eliminar canción", key=f"del_{i}"):
                df = df.drop(i).reset_index(drop=True)
                guardar_datos(df)
                st.rerun()
