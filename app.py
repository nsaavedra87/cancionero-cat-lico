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
    cat_emergencia = ["Alabanza", "Adoracion", "Oracion", "Espiritu Santo", "Entrega", "Sanacion", "Amor de Dios", "Perdon", "Eucaristia-Entrada", "Eucaristia-Perdon", "Eucaristia-Gloria", "Eucaristia-Aclamacion", "Eucaristia Ofertorio", "Eucaristia-Santo", "Eucaristia-Cordero", "Eucaristia-Comunion", "Ecuaristia-Final", "Eucaristia-Maria", "Adviento", "Navidad", "Cuaresma"]
    try:
        if os.path.exists(CAT_FILE) and os.path.getsize(CAT_FILE) > 5:
            df_cat = pd.read_csv(CAT_FILE)
            return df_cat.iloc[:, 0].dropna().unique().tolist()
    except Exception: pass
    return cat_emergencia

def guardar_datos(df):
    df.to_csv(DB_FILE, index=False)

# --- LÓGICA DE PROCESAMIENTO ESTRICTA (CORRIGE ALINEACIÓN Y LÍNEAS BLANCAS) ---
NOTAS = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

def procesar_texto(texto, semitonos, color_acorde):
    if not texto: return ""
    
    # Patrón para detectar acordes (A-G, Do-Si)
    patron = r"\b([A-G][#b]?(m|maj|7|9|sus\d|dim|aug|add\d)?)\b|\b(Do|Re|Mi|Fa|Sol|La|Si)[#b]?(m|maj|7|9|sus\d|dim|aug|add\d)?\b"
    
    def reemplazar(match):
        acorde = match.group(0)
        # Lógica simple de transporte (solo para notación A-G)
        match_nota = re.match(r"([A-G][#b]?)", acorde)
        if match_nota and semitonos != 0:
            nota_original = match_nota.group(1)
            dic_bemoles = {"Db": "C#", "Eb": "D#", "Gb": "F#", "Ab": "G#", "Bb": "A#"}
            nota_base = dic_bemoles.get(nota_original, nota_original)
            if nota_base in NOTAS:
                nueva_nota = NOTAS[(NOTAS.index(nota_base) + semitonos) % 12]
                acorde = nueva_nota + acorde[len(nota_original):]
        
        return f'<span style="color:{color_acorde}; font-weight:bold;">{acorde}</span>'
    
    lineas = texto.split('\n')
    lineas_procesadas = []
    
    for linea in lineas:
        # CORRECCIÓN LÍNEA BLANCA: Si la línea está vacía, forzamos un espacio HTML
        if not linea.strip():
            lineas_procesadas.append("&nbsp;")
            continue
        
        # Procesar acordes
        linea_color = re.sub(patron, reemplazar, linea)
        
        # CORRECCIÓN ALINEACIÓN: Reemplazar espacios por espacios de no-ruptura
        linea_final = linea_color.replace(" ", "&nbsp;")
        lineas_procesadas.append(linea_final)
        
    return "<br>".join(lineas_procesadas)

# --- INTERFAZ ---
st.set_page_config(page_title="ChordMaster Pro", page_icon="🎸", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono&family=Montserrat:wght@700&display=swap');
    
    /* Forzar editor monoespaciado */
    textarea {
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 16px !important;
        line-height: 1.2 !important;
        background-color: #000 !important;
        color: #ddd !important;
    }
    
    .visor-musical {
        border-radius: 12px;
        padding: 20px;
        background-color: #121212;
        border: 1px solid #444;
        font-family: 'JetBrains Mono', monospace !important;
        line-height: 1.2;
        overflow-x: auto;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

if 'setlist' not in st.session_state: st.session_state.setlist = []
df = cargar_datos()
categorias = cargar_categorias()

# --- SIDEBAR ---
st.sidebar.title("🎸 ChordMaster")
menu = st.sidebar.selectbox("Ir a:", ["🏠 Cantar / Vivo", "➕ Agregar Canción", "📂 Gestionar", "📋 Setlist"])

c_bg = st.sidebar.color_picker("Fondo Visor", "#121212")
c_txt = st.sidebar.color_picker("Color Letra", "#FFFFFF")
c_chord = st.sidebar.color_picker("Color Acordes", "#FFD700")
f_size = st.sidebar.slider("Tamaño Fuente", 12, 45, 20)

# --- MÓDULO: AGREGAR ---
if menu == "➕ Agregar Canción":
    st.header("➕ Nueva Canción")
    
    archivo_txt = st.file_uploader("Opcional: Importar desde .txt", type=["txt"])
    if archivo_txt:
        st.session_state.texto_temp = archivo_txt.read().decode("utf-8")

    if 'texto_temp' not in st.session_state: st.session_state.texto_temp = ""

    col1, col2 = st.columns(2)
    titulo_n = col1.text_input("Título")
    autor_n = col2.text_input("Autor")
    cat_n = st.selectbox("Categoría", categorias)
    
    letra_n = st.text_area("Editor (Alineación Manual):", value=st.session_state.texto_temp, height=400)
    
    if letra_n:
        st.subheader("👀 Vista Previa Estricta")
        preview_html = procesar_texto(letra_n, 0, c_chord)
        st.markdown(f"""
            <div class="visor-musical" style="background:{c_bg}; color:{c_txt}; font-size:{f_size}px;">
                {preview_html}
            </div>
        """, unsafe_allow_html=True)

        if st.button("💾 GUARDAR CANCIÓN", use_container_width=True):
            if titulo_n and letra_n:
                nueva_fila = pd.DataFrame([[titulo_n, autor_n, cat_n, letra_n]], columns=df.columns)
                df = pd.concat([df, nueva_fila], ignore_index=True)
                guardar_datos(df)
                st.success("¡Guardada!")
                st.session_state.texto_temp = ""
                st.rerun()

# --- MÓDULO: CANTAR ---
elif menu == "🏠 Cantar / Vivo":
    busqueda = st.text_input("🔍 Buscar por título o autor...")
    filtro_cat = st.multiselect("🏷️ Filtrar por Categoría", categorias)

    df_v = df.copy()
    if busqueda: df_v = df_v[df_v['Título'].str.contains(busqueda, case=False, na=False)]
    if filtro_cat: df_v = df_v[df_v['Categoría'].isin(filtro_cat)]

    if not df_v.empty:
        sel_c = st.selectbox("Selecciona una canción:", df_v['Título'])
        data_c = df_v[df_v['Título'] == sel_c].iloc[0]
        
        col_t1, col_t2 = st.columns([1, 1])
        tp = col_t1.number_input("Transportar (Semitonos)", -6, 6, 0)
        if col_t2.button("⭐ Añadir al Setlist"):
            st.session_state.setlist.append(sel_c)
            st.toast("Añadida al Setlist")

        l_html = procesar_texto(data_c['Letra'], tp, c_chord)
        st.markdown(f"""
            <div class="visor-musical" style="background:{c_bg}; color:{c_txt}; font-size:{f_size}px;">
                <h2 style="margin:0; color:white;">{data_c['Título']}</h2>
                <small style="color:#888;">{data_c['Autor']} | {data_c['Categoría']}</small>
                <hr style="border-color:#333;">
                {l_html}
            </div>
        """, unsafe_allow_html=True)

# --- GESTIONAR ---
elif menu == "📂 Gestionar":
    st.header("📂 Biblioteca")
    st.dataframe(df[["Título", "Autor", "Categoría"]], use_container_width=True)
    if st.button("Eliminar última"):
        df = df[:-1]; guardar_datos(df); st.rerun()

# --- SETLIST ---
elif menu == "📋 Setlist":
    st.header("📋 Mi Setlist del Día")
    if st.session_state.setlist:
        for s in st.session_state.setlist:
            st.markdown(f"**• {s}**")
        if st.button("Limpiar Setlist"):
            st.session_state.setlist = []; st.rerun()
    else:
        st.info("El setlist está vacío.")
