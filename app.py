import streamlit as st
import pandas as pd  # <-- Corregido aquí
import os
import re

# --- CONFIGURACIÓN DE ARCHIVOS ---
DB_FILE = "cancionero.csv"
CAT_FILE = "categorias.csv"
SETLIST_FILE = "setlist_fijo.csv"

# --- FUNCIONES DE DATOS (MANTENIDAS) ---
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

def cargar_setlist():
    try:
        if os.path.exists(SETLIST_FILE) and os.path.getsize(SETLIST_FILE) > 0:
            return pd.read_csv(SETLIST_FILE)["Título"].tolist()
    except Exception: pass
    return []

def guardar_datos(df):
    df.to_csv(DB_FILE, index=False)

def guardar_categorias(lista_cat):
    pd.DataFrame(lista_cat, columns=["Nombre"]).to_csv(CAT_FILE, index=False)

def guardar_setlist(lista_sl):
    pd.DataFrame(lista_sl, columns=["Título"]).to_csv(SETLIST_FILE, index=False)

# --- LÓGICA DE TRANSPOSICIÓN Y COLOR ---
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
    
    # PATRÓN DE PROTECCIÓN: Solo reconoce acordes rodeados de espacios o bordes
    patron = r"(^|(?<=\s))(Do#?|Re#?|Mi|Fa#?|Sol#?|La#?|Si|[A-G][#b]?)([Mm]|maj7|maj|7|9|sus4|sus2|dim|aug|add9)?(?=\s|$)"
    
    def reemplazar(match):
        prefijo = match.group(1) 
        nota_raiz = match.group(2)
        modo = match.group(3) if match.group(3) else ""
        
        dic_bemoles = {"Db": "C#", "Eb": "D#", "Gb": "F#", "Ab": "G#", "Bb": "A#"}
        nota_raiz_busqueda = dic_bemoles.get(nota_raiz, nota_raiz)
        
        nueva_nota = transportar_nota(nota_raiz_busqueda, semitonos) if semitonos != 0 else nota_raiz
        acorde_final = nueva_nota + modo
        
        # COLOR DIRECTO
        return f'{prefijo}<span style="color:{color_acorde} !important; font-weight:bold;">{acorde_final}</span>'
    
    lineas = texto.split('\n')
    lineas_procesadas = []
    for linea in lineas:
        if not linea.strip():
            linea_out = "&nbsp;"
        else:
            linea_html = re.sub(patron, reemplazar, linea)
            linea_out = linea_html.replace(" ", "&nbsp;")
        lineas_procesadas.append(linea_out)
        
    return "<br>".join(lineas_procesadas)

# --- INTERFAZ STREAMLIT ---
st.set_page_config(page_title="ChordMaster Pro", layout="wide")

if 'setlist' not in st.session_state:
    st.session_state.setlist = cargar_setlist()

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono&display=swap');
    textarea { font-family: 'JetBrains Mono', monospace !important; font-size: 16px !important; line-height: 1.2 !important; background-color: #000 !important; color: #ddd !important; }
    .visor-musical { border-radius: 12px; padding: 25px; border: 1px solid #444; font-family: 'JetBrains Mono', monospace !important; line-height: 1.2; overflow-x: auto; }
    .meta-data { color: #888; font-style: italic; margin-bottom: 5px; font-size: 0.9em; }
    </style>
    """, unsafe_allow_html=True)

df = cargar_datos()
categorias = cargar_categorias()

# --- SIDEBAR ---
st.sidebar.title("🎸 Menú")
menu = st.sidebar.selectbox("Ir a:", ["🏠 Cantar / Vivo", "📋 Mi Setlist", "➕ Agregar Canción", "📂 Gestionar / Editar", "⚙️ Configurar Categorías"])

c_bg = st.sidebar.color_picker("Fondo Visor", "#FFFFFF")
c_txt = st.sidebar.color_picker("Color Letra", "#000000")
c_chord = st.sidebar.color_picker("Color Acordes", "#FF0000")
f_size = st.sidebar.slider("Tamaño Fuente", 12, 45, 19)

# --- MÓDULOS ---
if menu == "🏠 Cantar / Vivo":
    st.header("🏠 Biblioteca en Vivo")
    col_f1, col_f2 = st.columns([2, 1])
    with col_f1: busqueda = st.text_input("🔍 Buscar...")
    with col_f2: filtro_cat = st.selectbox("📂 Categoría", ["Todas"] + categorias)
    
    df_v = df.copy()
    if busqueda:
        df_v = df_v[df_v['Título'].str.contains(busqueda, case=False, na=False) | df_v['Autor'].str.contains(busqueda, case=False, na=False)]
    if filtro_cat != "Todas":
        df_v = df_v[df_v['Categoría'] == filtro_cat]

    if not df_v.empty:
        col_sel, col_btn = st.columns([3, 1])
        sel_c = col_sel.selectbox("Seleccionar canción:", df_v['Título'])
        data = df_v[df_v['Título'] == sel_c].iloc[0]
        
        if col_btn.button("➕ Al Setlist", use_container_width=True):
            if sel_c not in st.session_state.setlist:
                st.session_state.setlist.append(sel_c)
                guardar_setlist(st.session_state.setlist)
                st.toast(f"'{sel_c}' añadida")

        tp = st.number_input("Transportar (Semitonos)", -6, 6, 0)
        final_html = procesar_texto_estricto(data['Letra'], tp, c_chord)
        st.markdown(f'<div class="visor-musical" style="background:{c_bg}; color:{c_txt}; font-size:{f_size}px;"><div style="font-size:1.2em; font-weight:bold;">{data["Título"]}</div><div class="meta-data">{data["Autor"]} | {data["Categoría"]}</div><hr style="border-color:#333;">{final_html}</div>', unsafe_allow_html=True)

elif menu == "📋 Mi Setlist":
    st.header("📋 Mi Setlist")
    if not st.session_state.setlist:
        st.info("Setlist vacío.")
    else:
        for i, cancion_nombre in enumerate(st.session_state.setlist):
            col_t, col_b = st.columns([4, 1])
            col_t.write(f"**{i+1}. {cancion_nombre}**")
            if col_b.button("❌", key=f"del_set_{i}"):
                st.session_state.setlist.pop(i)
                guardar_setlist(st.session_state.setlist)
                st.rerun()
        if st.button("🗑️ Vaciar Todo"):
            st.session_state.setlist = []
            guardar_setlist([])
            st.rerun()

elif menu == "➕ Agregar Canción":
    st.header("➕ Nueva Canción")
    col1, col2, col3 = st.columns(3)
    titulo_n = col1.text_input("Título")
    autor_n = col2.text_input("Autor")
    cat_n = col3.selectbox("Categoría", categorias)
    letra_n = st.text_area("Letra:", height=400)
    if letra_n:
        preview = procesar_texto_estricto(letra_n, 0, c_chord)
        st.markdown(f'<div class="visor-musical" style="background:{c_bg}; color:{c_txt}; font-size:{f_size}px;">{preview}</div>', unsafe_allow_html=True)
        if st.button("💾 Guardar"):
            nueva = pd.DataFrame([[titulo_n, autor_n if autor_n else "Anónimo", cat_n, letra_n]], columns=df.columns)
            df = pd.concat([df, nueva], ignore_index=True)
            guardar_datos(df); st.success("¡Guardada!"); st.rerun()

elif menu == "📂 Gestionar / Editar":
    st.header("📂 Gestión")
    for i, row in df.iterrows():
        with st.expander(f"📝 {row['Título']}"):
            c1, c2, c3 = st.columns(3)
            nt = c1.text_input("Título", row['Título'], key=f"t{i}")
            na = c2.text_input("Autor", row['Autor'], key=f"a{i}")
            nc = c3.selectbox("Categoría", categorias, index=categorias.index(row['Categoría']) if row['Categoría'] in categorias else 0, key=f"c{i}")
            nl = st.text_area("Letra", row['Letra'], height=200, key=f"l{i}")
            if st.button("Actualizar", key=f"b{i}"):
                df.at[i, 'Título'], df.at[i, 'Autor'], df.at[i, 'Categoría'], df.at[i, 'Letra'] = nt, na, nc, nl
                guardar_datos(df); st.rerun()
            if st.button("Eliminar", key=f"d{i}"):
                df = df.drop(i).reset_index(drop=True); guardar_datos(df); st.rerun()

elif menu == "⚙️ Configurar Categorías":
    st.header("⚙️ Categorías")
    n_cat = st.text_input("Nueva:")
    if st.button("Añadir"):
        if n_cat and n_cat not in categorias:
            categorias.append(n_cat); guardar_categorias(categorias); st.rerun()
    st.write(categorias)
