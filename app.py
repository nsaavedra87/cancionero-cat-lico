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
            df = pd.read_csv(DB_FILE)
            if not df.empty:
                return df
    except Exception as e:
        st.sidebar.warning("Iniciando base de datos de canciones...")
    return pd.DataFrame(columns=["Título", "Autor", "Categoría", "Letra"])

def cargar_categorias():
    categorias_defecto = ["General", "Alabanza", "Rock", "Pop", "Balada"]
    try:
        if os.path.exists(CAT_FILE) and os.path.getsize(CAT_FILE) > 0:
            df_cat = pd.read_csv(CAT_FILE)
            if not df_cat.empty and 'Nombre' in df_cat.columns:
                return df_cat['Nombre'].unique().tolist()
    except Exception as e:
        pass
    return categorias_defecto

def guardar_datos(df):
    df.to_csv(DB_FILE, index=False)

def guardar_categorias(lista):
    pd.DataFrame(lista, columns=['Nombre']).to_csv(CAT_FILE, index=False)

# --- LÓGICA DE TRANSPOSICIÓN ---
NOTAS = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

def transponer_texto(texto, semitonos):
    if semitonos == 0 or not texto: return texto
    patron = r"\b([A-G][#b]?(m|maj|7|9|sus\d|dim|aug|add\d)?)\b"
    def reemplazar(match):
        acorde = match.group(1)
        match_nota = re.match(r"([A-G][#b]?)", acorde)
        nota_original = match_nota.group(1)
        dic_bemoles = {"Db": "C#", "Eb": "D#", "Gb": "F#", "Ab": "G#", "Bb": "A#"}
        nota_base = dic_bemoles.get(nota_original, nota_original)
        resto = acorde[len(nota_original):]
        if nota_base in NOTAS:
            nueva_nota = NOTAS[(NOTAS.index(nota_base) + semitonos) % 12]
            return nueva_nota + resto
        return acorde
    return re.sub(patron, reemplazar, texto)

# --- INTERFAZ ---
st.set_page_config(page_title="ChordMaster Ultra v3", page_icon="🎸", layout="wide")

# CSS para Estética Escenario
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono&family=Roboto+Slab&family=Montserrat:wght@700&display=swap');
    [data-testid="stHeader"] { visibility: hidden; }
    .visor-musical {
        border-radius: 20px;
        padding: 40px;
        box-shadow: 0px 10px 30px rgba(0,0,0,0.5);
        border: 1px solid #444;
        white-space: pre-wrap;
    }
    </style>
    """, unsafe_allow_html=True)

if 'setlist' not in st.session_state: st.session_state.setlist = []

df = cargar_datos()
categorias = cargar_categorias()

# --- SIDEBAR ---
st.sidebar.title("🎸 ChordMaster Ultra")
menu = st.sidebar.selectbox("Menú", ["🏠 Cantar / Vivo", "📸 Importar Foto", "📝 Registro Manual", "⚙️ Categorías", "📋 Setlist"])

st.sidebar.divider()
st.sidebar.subheader("🎨 Estilo Escenario")
c_bg = st.sidebar.color_picker("Fondo", "#121212")
c_txt = st.sidebar.color_picker("Texto", "#00FF00")
f_size = st.sidebar.slider("Tamaño de Letra", 18, 45, 24)
f_family = st.sidebar.selectbox("Fuente", ["'JetBrains Mono', monospace", "'Roboto Slab', serif", "sans-serif"])

# Botón Pantalla Completa
if st.sidebar.button("📺 Pantalla Completa"):
    st.components.v1.html("<script>window.parent.document.documentElement.requestFullscreen();</script>", height=0)

# --- LÓGICA DE MENÚS ---

if menu == "⚙️ Categorías":
    st.header("⚙️ Gestión de Categorías")
    nueva_cat = st.text_input("Nueva Categoría")
    if st.button("➕ Crear"):
        if nueva_cat and nueva_cat not in categorias:
            categorias.append(nueva_cat)
            guardar_categorias(categorias)
            st.success(f"'{nueva_cat}' añadida.")
            st.rerun()
    st.write("Categorías actuales:", categorias)

elif menu == "📝 Registro Manual":
    st.header("📝 Nueva Canción")
    with st.form("registro"):
        t = st.text_input("Título")
        a = st.text_input("Autor")
        cat = st.selectbox("Categoría", categorias)
        let = st.text_area("Letra y Acordes", height=300)
        if st.form_submit_button("Guardar"):
            if t and let:
                nueva = pd.DataFrame([[t, a, cat, let]], columns=["Título", "Autor", "Categoría", "Letra"])
                df = pd.concat([df, nueva], ignore_index=True)
                guardar_datos(df)
                st.success("¡Guardada!")
            else: st.warning("Título y letra requeridos.")

elif menu == "📸 Importar Foto":
    st.header("📸 Escáner OCR")
    try:
        import pytesseract
        img_file = st.camera_input("Foto del manuscrito")
        if img_file:
            img = Image.open(img_file)
            with st.spinner("Leyendo imagen..."):
                texto_ocr = pytesseract.image_to_string(img, lang='spa')
                with st.form("ocr_edit"):
                    t_f = st.text_input("Título", value="Nueva Escaneada")
                    a_f = st.text_input("Autor", value="Desconocido")
                    c_f = st.selectbox("Categoría", categorias)
                    l_f = st.text_area("Texto detectado (Añade acordes)", value=texto_ocr, height=300)
                    if st.form_submit_button("Confirmar Guardado"):
                        nueva = pd.DataFrame([[t_f, a_f, c_f, l_f]], columns=df.columns)
                        df = pd.concat([df, nueva], ignore_index=True)
                        guardar_datos(df)
                        st.success("¡Importado!")
    except ImportError:
        st.error("Instalando motor OCR... espera unos segundos.")

elif menu == "🏠 Cantar / Vivo":
    col_busq, col_cat = st.columns([2, 1])
    with col_busq: busq = st.text_input("🔍 Buscar canción...")
    with col_cat: fil_cat = st.multiselect("🏷️ Filtrar Categoría", categorias)

    df_f = df.copy()
    if busq: df_f = df_f[df_f['Título'].str.contains(busq, case=False) | df_f['Autor'].str.contains(busq, case=False)]
    if fil_cat: df_f = df_f[df_f['Categoría'].isin(fil_cat)]

    if not df_f.empty:
        sel = st.selectbox("Canción:", df_f['Título'])
        c_data = df_f[df_f['Título'] == sel].iloc[0]
        
        c1, c2, c3 = st.columns(3)
        transp = c1.number_input("Transportar", -6, 6, 0)
        scroll = c2.slider("Auto-Scroll", 0, 10, 0)
        if c3.button("⭐ Al Setlist"):
            st.session_state.setlist.append(sel)
            st.toast("Añadida")

        if scroll > 0:
            st.components.v1.html(f"<script>setInterval(()=>window.parent.scrollBy(0,1),{100/scroll});</script>", height=0)

        # Visor Musical
        letra_f = transponer_texto(c_data['Letra'], transp)
        st.markdown(f"""
            <div class="visor-musical" style="background:{c_bg}; color:{c_txt}; font-size:{f_size}px; font-family:{f_family};">
            <h1 style="color:white; font-family:'Montserrat', sans-serif; margin:0;">{c_data['Título']}</h1>
            <p style="color:#888;">{c_data['Autor']} | {c_data['Categoría']}</p>
            <hr style="border-color:#444;">
            {letra_f}
            </div>
        """, unsafe_allow_html=True)
    else:
        st.info("No hay canciones disponibles. ¡Agrega una!")

elif menu == "📋 Mi Setlist":
    st.header("📋 Mi Setlist")
    if st.session_state.setlist:
        for s in st.session_state.setlist: st.write(f"• {s}")
        if st.button("Vaciar Lista"):
            st.session_state.setlist = []
            st.rerun()
    else: st.info("Lista vacía.")
