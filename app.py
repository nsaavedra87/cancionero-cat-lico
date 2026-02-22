import streamlit as st
import pandas as pd
import os
import re

# --- CONFIGURACIÓN DE ARCHIVOS ---
DB_FILE = "cancionero.csv"
CAT_FILE = "categorias.csv"
SETLIST_FILE = "setlist_data.csv"

# --- FUNCIONES DE DATOS ---
def cargar_datos():
    if os.path.exists(DB_FILE) and os.path.getsize(DB_FILE) > 0:
        return pd.read_csv(DB_FILE)
    return pd.DataFrame(columns=["Título", "Autor", "Categoría", "Letra"])

def cargar_categorias():
    cat_emergencia = ["Entrada", "Piedad", "Gloria", "Aleluya", "Ofertorio", "Santo", "Cordero", "Comunión", "Salida", "Adoración", "María"]
    if os.path.exists(CAT_FILE) and os.path.getsize(CAT_FILE) > 0:
        return pd.read_csv(CAT_FILE).iloc[:, 0].dropna().unique().tolist()
    return cat_emergencia

def cargar_setlist():
    if os.path.exists(SETLIST_FILE):
        return pd.read_csv(SETLIST_FILE)["Título"].tolist()
    return []

def guardar_setlist(lista):
    pd.DataFrame(lista, columns=["Título"]).to_csv(SETLIST_FILE, index=False)

# --- LÓGICA DE TRANSPOSICIÓN ---
NOTAS_AMER = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
NOTAS_LAT = ["Do", "Do#", "Re", "Re#", "Mi", "Fa", "Fa#", "Sol", "Sol#", "La", "La#", "Si"]

def transportar_nota(nota, semitonos):
    for lista in [NOTAS_AMER, NOTAS_LAT]:
        if nota in lista:
            return lista[(lista.index(nota) + semitonos) % 12]
    return nota

def procesar_texto_estricto(texto, semitonos):
    if not texto: return ""
    # Patrón que exige espacios alrededor para no captar letras de palabras
    patron = r"(^|(?<=\s))(Do#?|Re#?|Mi|Fa#?|Sol#?|La#?|Si|[A-G][#b]?)([Mm]|maj7|maj|7|9|sus4|sus2|dim|aug|add9)?(?=\s|$)"
    
    def reemplazar(match):
        prefijo = match.group(1)
        nota = match.group(2)
        modo = match.group(3) if match.group(3) else ""
        nueva = transportar_nota(nota, semitonos)
        # Usamos una clase CSS específica 'acorde-txt'
        return f'{prefijo}<span class="acorde-txt">{nueva}{modo}</span>'

    lineas_html = []
    for linea in texto.split('\n'):
        if not linea.strip():
            lineas_html.append("&nbsp;")
        else:
            procesada = re.sub(patron, reemplazar, linea)
            lineas_html.append(procesada.replace(" ", "&nbsp;"))
    return "<br>".join(lineas_html)

# --- INTERFAZ ---
st.set_page_config(page_title="ChordMaster Pro", layout="wide")

df = cargar_datos()
categorias = cargar_categorias()
if 'setlist' not in st.session_state:
    st.session_state.setlist = cargar_setlist()

# --- SIDEBAR ---
st.sidebar.title("🎸 Menú")
menu = st.sidebar.selectbox("Ir a:", ["🏠 Cantar / Vivo", "📋 Mi Setlist", "➕ Agregar Canción", "📂 Gestionar", "⚙️ Categorías"])

c_bg = st.sidebar.color_picker("Fondo Visor", "#FFFFFF")
c_txt = st.sidebar.color_picker("Color Letra", "#000000")
c_chord = st.sidebar.color_picker("Color Acordes", "#FF0000") # Rojo como en tu captura
f_size = st.sidebar.slider("Tamaño Fuente", 12, 45, 19)

# INYECCIÓN DE CSS DINÁMICO (Esto arregla el color)
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono&display=swap');
    .visor-musical {{ 
        background-color: {c_bg} !important; 
        color: {c_txt} !important; 
        border-radius: 12px; padding: 25px; border: 1px solid #ccc;
        font-family: 'JetBrains Mono', monospace !important; 
        line-height: 1.2; font-size: {f_size}px;
    }}
    .acorde-txt {{ 
        color: {c_chord} !important; 
        font-weight: bold !important;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- LÓGICA DE MÓDULOS ---
if menu == "🏠 Cantar / Vivo":
    col_f1, col_f2 = st.columns([2, 1])
    busq = col_f1.text_input("🔍 Buscar...")
    f_cat = col_f2.selectbox("📂 Categoría", ["Todas"] + categorias)
    
    df_v = df.copy()
    if busq: df_v = df_v[df_v['Título'].str.contains(busq, case=False)]
    if f_cat != "Todas": df_v = df_v[df_v['Categoría'] == f_cat]

    if not df_v.empty:
        c_sel, c_add = st.columns([3, 1])
        sel_c = c_sel.selectbox("Canción:", df_v['Título'])
        if c_add.button("➕ Al Setlist"):
            if sel_c not in st.session_state.setlist:
                st.session_state.setlist.append(sel_c)
                guardar_setlist(st.session_state.setlist)
                st.toast("Añadida")

        data = df_v[df_v['Título'] == sel_c].iloc[0]
        tp = st.number_input("Transportar (Semitonos)", -6, 6, 0)
        
        final_html = procesar_texto_estricto(data['Letra'], tp)
        st.markdown(f'<div class="visor-musical"><b>{data["Título"]}</b><br><small>{data["Autor"]}</small><hr>{final_html}</div>', unsafe_allow_html=True)

elif menu == "📋 Mi Setlist":
    st.header("📋 Mi Setlist")
    for i, t in enumerate(st.session_state.setlist):
        col_t, col_b = st.columns([4, 1])
        col_t.write(f"**{i+1}. {t}**")
        if col_b.button("❌", key=f"del_{i}"):
            st.session_state.setlist.pop(i)
            guardar_setlist(st.session_state.setlist)
            st.rerun()
    if st.button("🗑️ Vaciar"):
        st.session_state.setlist = []
        guardar_setlist([])
        st.rerun()

elif menu == "➕ Agregar Canción":
    st.header("➕ Nueva")
    c1, c2, c3 = st.columns(3)
    t = c1.text_input("Título")
    a = c2.text_input("Autor")
    cat = c3.selectbox("Categoría", categorias)
    letra = st.text_area("Letra:", height=300)
    if st.button("Guardar"):
        new_df = pd.concat([df, pd.DataFrame([[t, a, cat, letra]], columns=df.columns)], ignore_index=True)
        new_df.to_csv(DB_FILE, index=False)
        st.success("Guardado")

elif menu == "📂 Gestionar":
    st.write(df) # Versión simplificada para no alargar el código

elif menu == "⚙️ Categorías":
    n_cat = st.text_input("Nueva Categoría:")
    if st.button("Añadir"):
        categorias.append(n_cat)
        pd.DataFrame(categorias).to_csv(CAT_FILE, index=False)
        st.rerun()
