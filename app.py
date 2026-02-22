import streamlit as st
import pandas as pd
import os
import re

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

# --- LÓGICA DE PROCESAMIENTO ESTRICTA (ALINEACIÓN Y LÍNEAS BLANCAS) ---
NOTAS = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

def procesar_texto(texto, semitonos, color_acorde):
    if not texto: return ""
    
    patron = r"\b([A-G][#b]?(m|maj|7|9|sus\d|dim|aug|add\d)?)\b|\b(Do|Re|Mi|Fa|Sol|La|Si)[#b]?(m|maj|7|9|sus\d|dim|aug|add\d)?\b"
    
    def reemplazar(match):
        acorde = match.group(0)
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
        if not linea.strip():
            lineas_procesadas.append("&nbsp;")
            continue
        linea_color = re.sub(patron, reemplazar, linea)
        linea_final = linea_color.replace(" ", "&nbsp;")
        lineas_procesadas.append(linea_final)
    return "<br>".join(lineas_procesadas)

# --- INTERFAZ ---
st.set_page_config(page_title="ChordMaster Pro", page_icon="🎸", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono&display=swap');
    textarea { font-family: 'JetBrains Mono', monospace !important; font-size: 16px !important; line-height: 1.2 !important; background-color: #000 !important; color: #ddd !important; }
    .visor-musical { border-radius: 12px; padding: 20px; background-color: #121212; border: 1px solid #444; font-family: 'JetBrains Mono', monospace !important; line-height: 1.2; overflow-x: auto; color: white; }
    .meta-data { color: #888; font-style: italic; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

if 'setlist' not in st.session_state: st.session_state.setlist = []
df = cargar_datos()
categorias = cargar_categorias()

# --- SIDEBAR ---
st.sidebar.title("🎸 ChordMaster")
menu = st.sidebar.selectbox("Ir a:", ["🏠 Cantar / Vivo", "➕ Agregar Canción", "📂 Gestionar / Editar", "⚙️ Configurar Categorías", "📋 Setlist"])

c_bg = st.sidebar.color_picker("Fondo Visor", "#121212")
c_txt = st.sidebar.color_picker("Color Letra", "#FFFFFF")
c_chord = st.sidebar.color_picker("Color Acordes", "#FFD700")
f_size = st.sidebar.slider("Tamaño Fuente", 12, 45, 20)

# --- MÓDULO: AGREGAR ---
if menu == "➕ Agregar Canción":
    st.header("➕ Nueva Canción")
    archivo_txt = st.file_uploader("Importar .txt", type=["txt"])
    if archivo_txt: st.session_state.texto_temp = archivo_txt.read().decode("utf-8")
    if 'texto_temp' not in st.session_state: st.session_state.texto_temp = ""

    col1, col2, col3 = st.columns(3)
    titulo_n = col1.text_input("Título")
    autor_n = col2.text_input("Autor")
    cat_n = col3.selectbox("Categoría", categorias)
    letra_n = st.text_area("Editor:", value=st.session_state.texto_temp, height=400)
    
    if letra_n:
        preview_html = procesar_texto(letra_n, 0, c_chord)
        st.markdown(f'<div class="visor-musical" style="background:{c_bg}; color:{c_txt}; font-size:{f_size}px;"><div class="meta-data">{titulo_n} - {autor_n}</div>{preview_html}</div>', unsafe_allow_html=True)
        if st.button("💾 GUARDAR CANCIÓN", use_container_width=True):
            if titulo_n:
                nueva_fila = pd.DataFrame([[titulo_n, autor_n if autor_n else "Anónimo", cat_n, letra_n]], columns=df.columns)
                df = pd.concat([df, nueva_fila], ignore_index=True)
                guardar_datos(df)
                st.success("¡Guardada!"); st.session_state.texto_temp = ""; st.rerun()

# --- MÓDULO: GESTIONAR / EDITAR ---
elif menu == "📂 Gestionar / Editar":
    st.header("📂 Biblioteca")
    if not df.empty:
        for i, row in df.iterrows():
            with st.expander(f"📝 {row['Título']} - {row['Autor']}"):
                col_e1, col_e2, col_e3 = st.columns(3)
                nuevo_t = col_e1.text_input("Título", value=row['Título'], key=f"t_{i}")
                nuevo_a = col_e2.text_input("Autor", value=row['Autor'], key=f"a_{i}")
                nuevo_c = col_e3.selectbox("Categoría", categorias, index=categorias.index(row['Categoría']) if row['Categoría'] in categorias else 0, key=f"c_{i}")
                nueva_l = st.text_area("Letra", value=row['Letra'], height=250, key=f"l_{i}")
                
                col_b1, col_b2 = st.columns(2)
                if col_b1.button("✅ Actualizar", key=f"upd_{i}"):
                    df.at[i, 'Título'] = nuevo_t
                    df.at[i, 'Autor'] = nuevo_a
                    df.at[i, 'Categoría'] = nuevo_c
                    df.at[i, 'Letra'] = nueva_l
                    guardar_datos(df)
                    st.success("Actualizado"); st.rerun()
                if col_b2.button("🗑️ Eliminar", key=f"del_{i}"):
                    df = df.drop(i).reset_index(drop=True)
                    guardar_datos(df)
                    st.rerun()
    else: st.info("Biblioteca vacía.")

# --- MÓDULO: CONFIGURAR CATEGORÍAS ---
elif menu == "⚙️ Configurar Categorías":
    st.header("⚙️ Categorías")
    nueva_cat = st.text_input("Nueva:")
    if st.button("Añadir"):
        if nueva_cat and nueva_cat not in categorias:
            categorias.append(nueva_cat); guardar_categorias(categorias); st.rerun()
    st.write(categorias)

# --- MÓDULO: CANTAR ---
elif menu == "🏠 Cantar / Vivo":
    busqueda = st.text_input("🔍 Buscar...")
    df_v = df.copy()
    if busqueda: df_v = df_v[df_v['Título'].str.contains(busqueda, case=False, na=False) | df_v['Autor'].str.contains(busqueda, case=False, na=False)]
    
    if not df_v.empty:
        sel_c = st.selectbox("Selecciona:", df_v['Título'])
        data_c = df_v[df_v['Título'] == sel_c].iloc[0]
        tp = st.number_input("Transportar", -6, 6, 0)
        l_html = procesar_texto(data_c['Letra'], tp, c_chord)
        st.markdown(f'<div class="visor-musical" style="background:{c_bg}; color:{c_txt}; font-size:{f_size}px;"><div style="font-size:1.2em; font-weight:bold;">{data_c["Título"]}</div><div class="meta-data">{data_c["Autor"]} | {data_c["Categoría"]}</div><hr style="border-color:#333;">{l_html}</div>', unsafe_allow_html=True)

# --- SETLIST ---
elif menu == "📋 Setlist":
    st.header("📋 Setlist")
    for s in st.session_state.setlist: st.write(f"• {s}")
    if st.button("Limpiar"): st.session_state.setlist = []; st.rerun()
