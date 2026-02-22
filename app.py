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

def guardar_categorias(lista_cat):
    pd.DataFrame(lista_cat, columns=["Nombre"]).to_csv(CAT_FILE, index=False)

# --- LÓGICA DE TRANSPOSICIÓN Y COLOR CORREGIDA ---
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
    
    # Este patrón detecta la nota y el modo (m, M, 7, etc.)
    patron = r"\b(Do#?|Re#?|Mi|Fa#?|Sol#?|La#?|Si|[A-G][#b]?)([Mm]|maj7|maj|7|9|sus4|sus2|dim|aug|add9)?\b"
    
    lineas = texto.split('\n')
    lineas_procesadas = []

    for linea in lineas:
        if not linea.strip():
            lineas_procesadas.append("&nbsp;")
            continue

        # Función interna para el reemplazo que maneja el color y transporte
        def aplicar_estilo(match):
            nota_raiz = match.group(1)
            modo = match.group(2) if match.group(2) else ""
            
            # Normalizar bemoles para transporte
            dic_bemoles = {"Db": "C#", "Eb": "D#", "Gb": "F#", "Ab": "G#", "Bb": "A#"}
            nota_raiz_busqueda = dic_bemoles.get(nota_raiz, nota_raiz)
            
            nueva_nota = transportar_nota(nota_raiz_busqueda, semitonos) if semitonos != 0 else nota_raiz
            acorde_completo = nueva_nota + modo
            
            # EL TRUCO: Usamos inline-style con !important para forzar el color
            return f'<span style="color:{color_acorde} !important; font-weight:bold; display:inline-block;">{acorde_completo}</span>'

        # 1. Aplicamos el color y transporte a los acordes
        linea_coloreada = re.sub(patron, aplicar_estilo, linea)
        
        # 2. Reemplazamos espacios por espacios rígidos para mantener alineación
        linea_final = linea_coloreada.replace(" ", "&nbsp;")
        lineas_procesadas.append(linea_final)
        
    return "<br>".join(lineas_procesadas)

# --- INTERFAZ ---
st.set_page_config(page_title="ChordMaster Pro", layout="wide")

# CSS para forzar el visor
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono&display=swap');
    textarea { font-family: 'JetBrains Mono', monospace !important; font-size: 16px !important; line-height: 1.2 !important; }
    .visor-musical { 
        border-radius: 12px; 
        padding: 25px; 
        line-height: 1.3; 
        font-family: 'JetBrains Mono', monospace !important; 
        white-space: normal; 
        overflow-x: auto;
    }
    </style>
    """, unsafe_allow_html=True)

df = cargar_datos()
categorias = cargar_categorias()

# --- SIDEBAR ---
st.sidebar.title("🎸 Ajustes")
menu = st.sidebar.selectbox("Ir a:", ["🏠 Cantar", "➕ Agregar", "📂 Gestionar", "⚙️ Categorías"])
c_bg = st.sidebar.color_picker("Fondo", "#000000")
c_txt = st.sidebar.color_picker("Letra", "#FFFFFF")
c_chord = st.sidebar.color_picker("Color Acordes", "#FFD700")
f_size = st.sidebar.slider("Tamaño", 12, 40, 22)

if menu == "➕ Agregar":
    st.header("➕ Nueva Canción")
    c1, c2, c3 = st.columns(3)
    t_n = c1.text_input("Título")
    a_n = c2.text_input("Autor")
    cat_n = c3.selectbox("Categoría", categorias)
    letra_n = st.text_area("Letra y Acordes:", height=300)
    
    if letra_n:
        preview = procesar_texto_estricto(letra_n, 0, c_chord)
        st.markdown(f'<div class="visor-musical" style="background:{c_bg}; color:{c_txt}; font-size:{f_size}px;">{preview}</div>', unsafe_allow_html=True)
        if st.button("Guardar"):
            df = pd.concat([df, pd.DataFrame([[t_n, a_n, cat_n, letra_n]], columns=df.columns)], ignore_index=True)
            guardar_datos(df); st.rerun()

elif menu == "🏠 Cantar":
    col_f1, col_f2 = st.columns([2, 1])
    busq = col_f1.text_input("🔍 Buscar...")
    f_cat = col_f2.selectbox("📂 Categoría", ["Todas"] + categorias)
    
    df_v = df.copy()
    if busq: df_v = df_v[df_v['Título'].str.contains(busq, case=False) | df_v['Autor'].str.contains(busq, case=False)]
    if f_cat != "Todas": df_v = df_v[df_v['Categoría'] == f_cat]

    if not df_v.empty:
        sel = st.selectbox("Canción:", df_v['Título'])
        cancion = df_v[df_v['Título'] == sel].iloc[0]
        tp = st.number_input("Transportar", -6, 6, 0)
        
        final_html = procesar_texto_estricto(cancion['Letra'], tp, c_chord)
        st.markdown(f'''
            <div class="visor-musical" style="background:{c_bg}; color:{c_txt}; font-size:{f_size}px;">
                <div style="border-bottom: 1px solid #444; margin-bottom: 10px;">
                    <b style="font-size: 1.2em;">{cancion["Título"]}</b><br>
                    <small style="color: gray;">{cancion["Autor"]} | {cancion["Categoría"]}</small>
                </div>
                {final_html}
            </div>
        ''', unsafe_allow_html=True)

elif menu == "📂 Gestionar":
    st.header("📂 Biblioteca")
    for i, r in df.iterrows():
        with st.expander(f"{r['Título']}"):
            nl = st.text_area("Editar Letra", r['Letra'], key=f"ed{i}")
            if st.button("Actualizar", key=f"up{i}"):
                df.at[i, 'Letra'] = nl
                guardar_datos(df); st.rerun()
            if st.button("Borrar", key=f"del{i}"):
                df = df.drop(i).reset_index(drop=True); guardar_datos(df); st.rerun()

elif menu == "⚙️ Categorías":
    st.header("⚙️ Categorías")
    nueva = st.text_input("Nueva:")
    if st.button("Añadir"):
        categorias.append(nueva); guardar_categorias(categorias); st.rerun()
    st.write(categorias)
