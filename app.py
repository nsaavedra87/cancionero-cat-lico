import streamlit as st
import pandas as pd
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

# --- LÓGICA DE TRANSPOSICIÓN ---
NOTAS_AMER = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
NOTAS_LAT = ["Do", "Do#", "Re", "Re#", "Mi", "Fa", "Fa#", "Sol", "Sol#", "La", "La#", "Si"]

def transportar_nota(nota, semitonos):
    for lista in [NOTAS_AMER, NOTAS_LAT]:
        if nota in lista:
            idx = (lista.index(nota) + semitonos) % 12
            return lista[idx]
    return nota

def procesar_texto_estricto(texto, semitonos):
    if not texto: return ""
    # Patrón que protege la letra (solo detecta acordes rodeados de espacios)
    patron = r"(^|(?<=\s))(Do#?|Re#?|Mi|Fa#?|Sol#?|La#?|Si|[A-G][#b]?)([Mm]|maj7|maj|7|9|sus4|sus2|dim|aug|add9)?(?=\s|$)"
    
    def reemplazar(match):
        prefijo = match.group(1) 
        nota_raiz = match.group(2)
        modo = match.group(3) if match.group(3) else ""
        
        dic_bemoles = {"Db": "C#", "Eb": "D#", "Gb": "F#", "Ab": "G#", "Bb": "A#"}
        nota_raiz_busqueda = dic_bemoles.get(nota_raiz, nota_raiz)
        
        nueva_nota = transportar_nota(nota_raiz_busqueda, semitonos)
        acorde_final = nueva_nota + modo
        
        # Marcamos el acorde con una clase CSS especial
        return f'{prefijo}<span class="chord-mark">{acorde_final}</span>'
    
    lineas_procesadas = []
    for linea in texto.split('\n'):
        if not linea.strip():
            lineas_procesadas.append("&nbsp;")
        else:
            linea_html = re.sub(patron, reemplazar, linea)
            lineas_procesadas.append(linea_html.replace(" ", "&nbsp;"))
        
    return "<br>".join(lineas_procesadas)

# --- INTERFAZ STREAMLIT ---
st.set_page_config(page_title="ChordMaster Pro", layout="wide")

if 'setlist' not in st.session_state:
    st.session_state.setlist = cargar_setlist()

# --- SIDEBAR (SELECTORES DE COLOR) ---
st.sidebar.title("🎸 Ajustes Visuales")
c_bg = st.sidebar.color_picker("Color de Fondo", "#FFFFFF")
c_txt = st.sidebar.color_picker("Color de Letra", "#000000")
c_chord = st.sidebar.color_picker("Color de Acordes", "#FF0000")
f_size = st.sidebar.slider("Tamaño de Letra", 12, 45, 19)

# --- INYECCIÓN DE CSS DINÁMICO (Esto soluciona el problema definitivamente) ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono&display=swap');
    
    /* Contenedor del Visor */
    .visor-musical {{ 
        background-color: {c_bg} !important; 
        color: {c_txt} !important; 
        border-radius: 12px; 
        padding: 25px; 
        border: 1px solid #ddd;
        font-family: 'JetBrains Mono', monospace !important; 
        line-height: 1.2; 
        font-size: {f_size}px;
        overflow-x: auto;
    }}
    
    /* REGLA MAESTRA PARA LOS ACORDES */
    .chord-mark {{ 
        color: {c_chord} !important; 
        font-weight: bold !important;
        font-style: normal !important;
        display: inline-block;
    }}
    </style>
    """, unsafe_allow_html=True)

df = cargar_datos()
categorias = cargar_categorias()

menu = st.sidebar.selectbox("Ir a:", ["🏠 Cantar / Vivo", "📋 Mi Setlist", "➕ Agregar Canción", "📂 Gestionar / Editar", "⚙️ Categorías"])

# --- LÓGICA DE MÓDULOS ---
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
        sel_c = col_sel.selectbox("Canción:", df_v['Título'])
        data = df_v[df_v['Título'] == sel_c].iloc[0]
        
        if col_btn.button("➕ Al Setlist", use_container_width=True):
            if sel_c not in st.session_state.setlist:
                st.session_state.setlist.append(sel_c)
                guardar_setlist(st.session_state.setlist)
                st.toast(f"'{sel_c}' añadida")

        tp = st.number_input("Transportar (Semitonos)", -6, 6, 0)
        final_html = procesar_texto_estricto(data['Letra'], tp)
        
        st.markdown(f'''
            <div class="visor-musical">
                <div style="font-size:1.2em; font-weight:bold;">{data["Título"]}</div>
                <div style="color:gray; font-style:italic; font-size:0.8em;">{data["Autor"]} | {data["Categoría"]}</div>
                <hr style="border-color:#eee; margin:10px 0;">
                {final_html}
            </div>
        ''', unsafe_allow_html=True)

elif menu == "📋 Mi Setlist":
    st.header("📋 Mi Setlist Guardado")
    if not st.session_state.setlist:
        st.info("Tu setlist está vacío.")
    else:
        for i, cancion_nombre in enumerate(st.session_state.setlist):
            col_t, col_b = st.columns([4, 1])
            col_t.subheader(f"{i+1}. {cancion_nombre}")
            if col_b.button("❌ Quitar", key=f"del_set_{i}"):
                st.session_state.setlist.pop(i)
                guardar_setlist(st.session_state.setlist)
                st.rerun()
        if st.button("🗑️ Vaciar Setlist"):
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
        preview = procesar_texto_estricto(letra_n, 0)
        st.markdown(f'<div class="visor-musical">{preview}</div>', unsafe_allow_html=True)
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

elif menu == "⚙️ Categorías":
    st.header("⚙️ Categorías")
    n_cat = st.text_input("Nueva:")
    if st.button("Añadir"):
        if n_cat and n_cat not in categorias:
            categorias.append(n_cat); guardar_categorias(categorias); st.rerun()
    st.write(categorias)
