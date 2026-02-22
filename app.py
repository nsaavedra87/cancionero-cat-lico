import streamlit as st
import pandas as pd
import os
import re
from PIL import Image

# --- CONFIGURACIÓN DE ARCHIVOS ---
DB_FILE = "cancionero.csv"
CAT_FILE = "categorias.csv"

# --- FUNCIONES DE DATOS BLINDADAS ---
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
            df_cat = pd.read_csv(CAT_FILE, on_bad_lines='skip')
            return df_cat.iloc[:, 0].dropna().unique().tolist()
    except Exception: pass
    return cat_emergencia

def guardar_datos(df):
    df.to_csv(DB_FILE, index=False)

# --- LÓGICA DE TRANSPOSICIÓN Y COLOR DE ACORDES ---
NOTAS = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

def procesar_texto(texto, semitonos, color_acorde):
    if not texto: return ""
    # Patrón para detectar acordes
    patron = r"\b([A-G][#b]?(m|maj|7|9|sus\d|dim|aug|add\d)?)\b"
    
    def reemplazar(match):
        acorde = match.group(1)
        match_nota = re.match(r"([A-G][#b]?)", acorde)
        nota_original = match_nota.group(1)
        dic_bemoles = {"Db": "C#", "Eb": "D#", "Gb": "F#", "Ab": "G#", "Bb": "A#"}
        nota_base = dic_bemoles.get(nota_original, nota_original)
        
        # Transposición
        if nota_base in NOTAS and semitonos != 0:
            nueva_nota = NOTAS[(NOTAS.index(nota_base) + semitonos) % 12]
            acorde = nueva_nota + acorde[len(nota_original):]
        
        # Aplicar color al acorde mediante HTML
        return f'<span style="color:{color_acorde}; font-weight:bold;">{acorde}</span>'
    
    return re.sub(patron, reemplazar, texto)

# --- INTERFAZ ---
st.set_page_config(page_title="ChordMaster Ultra v4", page_icon="🎸", layout="wide")

# Estilos CSS
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono&family=Montserrat:wght@700&display=swap');
    [data-testid="stHeader"] {{ visibility: hidden; }}
    .visor-musical {{
        border-radius: 15px;
        padding: 20px 30px;
        box-shadow: 0px 5px 20px rgba(0,0,0,0.4);
        border: 1px solid #444;
        white-space: pre-wrap;
        line-height: 1.4;
    }}
    .titulo-visor {{ font-family: 'Montserrat', sans-serif; margin-bottom: 2px; line-height: 1.1; }}
    .autor-visor {{ color: #888; margin-bottom: 15px; font-size: 0.9em; }}
    </style>
    """, unsafe_allow_html=True)

if 'setlist' not in st.session_state: st.session_state.setlist = []

df = cargar_datos()
categorias = cargar_categorias()

# --- SIDEBAR ---
st.sidebar.title("🎸 ChordMaster Pro")
menu = st.sidebar.selectbox("Menú", ["🏠 Cantar / Vivo", "➕ Agregar Canción", "📂 Gestionar Biblioteca", "⚙️ Categorías", "📋 Setlist"])

st.sidebar.divider()
st.sidebar.subheader("🎨 Paleta de Colores")
c_bg = st.sidebar.color_picker("Fondo Visor", "#121212")
c_txt = st.sidebar.color_picker("Color Letra", "#FFFFFF")
c_chord = st.sidebar.color_picker("Color Acordes", "#00FF00")
f_size = st.sidebar.slider("Tamaño Fuente", 16, 50, 22)
f_family = st.sidebar.selectbox("Fuente", ["'JetBrains Mono', monospace", "sans-serif", "serif"])

# --- LÓGICA DE MENÚS ---

if menu == "➕ Agregar Canción":
    st.header("📝 Agregar al Repertorio")
    metodo = st.radio("Método de entrada:", ["Escritura Manual", "Cámara / Foto (OCR)"], horizontal=True)
    
    texto_inicial = ""
    if metodo == "Cámara / Foto (OCR)":
        try:
            import pytesseract
            img_file = st.camera_input("Capturar hoja")
            if img_file:
                img = Image.open(img_file)
                texto_inicial = pytesseract.image_to_string(img, lang='spa')
        except: st.error("Motor OCR no disponible.")

    with st.container(border=True):
        col1, col2 = st.columns(2)
        t_n = col1.text_input("Título")
        a_n = col2.text_input("Autor")
        cat_n = st.selectbox("Categoría", categorias)
        let_n = st.text_area("Letra y Acordes (Edita aquí)", value=texto_inicial, height=250)
        
        if t_n and let_n:
            st.subheader("👀 Vista Previa (Revisa antes de guardar)")
            preview = procesar_texto(let_n, 0, c_chord)
            st.markdown(f"""<div class="visor-musical" style="background:{c_bg}; color:{c_txt}; font-size:{f_size}px; font-family:{f_family};">
            <div class="titulo-visor">{t_n}</div><div class="autor-visor">{a_n}</div>{preview}</div>""", unsafe_allow_html=True)
            
            if st.button("✅ Confirmar y Guardar en Biblioteca"):
                nueva = pd.DataFrame([[t_n, a_n, cat_n, let_n]], columns=df.columns)
                df = pd.concat([df, nueva], ignore_index=True)
                guardar_datos(df)
                st.success("¡Canción guardada con éxito!")

elif menu == "📂 Gestionar Biblioteca":
    st.header("📂 Mi Biblioteca")
    if not df.empty:
        st.write("Selecciona canciones para eliminar:")
        for i, row in df.iterrows():
            col_t, col_b = st.columns([4, 1])
            col_t.write(f"**{row['Título']}** - {row['Autor']} ({row['Categoría']})")
            if col_b.button("🗑️ Eliminar", key=f"del_{i}"):
                df = df.drop(i).reset_index(drop=True)
                guardar_datos(df)
                st.rerun()
    else: st.info("Biblioteca vacía.")

elif menu == "🏠 Cantar / Vivo":
    col_busq, col_cat = st.columns([2, 1])
    with col_busq: busq = st.text_input("🔍 Buscar canción o autor...")
    with col_cat: fil_cat = st.multiselect("🏷️ Categorías", categorias)

    df_f = df.copy()
    if busq: df_f = df_f[df_f['Título'].str.contains(busq, case=False, na=False) | df_f['Autor'].str.contains(busq, case=False, na=False)]
    if fil_cat: df_f = df_f[df_f['Categoría'].isin(fil_cat)]

    if not df_f.empty:
        sel = st.selectbox("Selecciona:", df_f['Título'])
        c_data = df_f[df_f['Título'] == sel].iloc[0]
        
        c1, c2, c3 = st.columns(3)
        transp = c1.number_input("Transportar", -6, 6, 0)
        scroll = c2.slider("Auto-Scroll", 0, 10, 0)
        if c3.button("⭐ Al Setlist"):
            st.session_state.setlist.append(sel)
            st.toast("Añadida")

        if scroll > 0:
            st.components.v1.html(f"<script>setInterval(()=>window.parent.scrollBy(0,1),{100/scroll});</script>", height=0)

        # Renderizado Final
        letra_html = procesar_texto(c_data['Letra'], transp, c_chord)
        st.markdown(f"""
            <div class="visor-musical" style="background:{c_bg}; color:{c_txt}; font-size:{f_size}px; font-family:{f_family};">
            <h2 class="titulo-visor" style="color:white;">{c_data['Título']}</h2>
            <div class="autor-visor">{c_data['Autor']} | {c_data['Categoría']}</div>
            {letra_html}
            </div>
        """, unsafe_allow_html=True)
    else: st.info("Usa los filtros para encontrar una canción.")

elif menu == "⚙️ Categorías":
    st.header("⚙️ Gestión de Categorías")
    nueva_cat = st.text_input("Nueva Categoría")
    if st.button("➕ Crear"):
        if nueva_cat and nueva_cat not in categorias:
            categorias.append(nueva_cat)
            pd.DataFrame(categorias, columns=['Nombre']).to_csv(CAT_FILE, index=False)
            st.rerun()
    st.write(categorias)

elif menu == "📋 Setlist":
    st.header("📋 Mi Setlist")
    if st.session_state.setlist:
        for s in st.session_state.setlist: st.write(f"• {s}")
        if st.button("Vaciar Lista"):
            st.session_state.setlist = []
            st.rerun()
    else: st.info("Lista vacía.")
