import streamlit as st
import pandas as pd
import os
import re

# --- CONFIGURACIÓN DE ARCHIVOS (MANTENIDO) ---
DB_FILE = "cancionero.csv"
CAT_FILE = "categorias.csv"
SETLIST_FILE = "setlist_fijo.csv"

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

def guardar_datos(df): df.to_csv(DB_FILE, index=False)
def guardar_categorias(lista_cat): pd.DataFrame(lista_cat, columns=["Nombre"]).to_csv(CAT_FILE, index=False)
def guardar_setlist(lista_sl): pd.DataFrame(lista_sl, columns=["Título"]).to_csv(SETLIST_FILE, index=False)

# --- LÓGICA DE TRANSPOSICIÓN (MANTENIDA TU LÓGICA ORIGINAL) ---
NOTAS_LAT = ["Do", "Do#", "Re", "Re#", "Mi", "Fa", "Fa#", "Sol", "Sol#", "La", "La#", "Si"]
NOTAS_AMER = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

def transportar_nota(nota, semitonos):
    for lista in [NOTAS_AMER, NOTAS_LAT]:
        if nota in lista:
            idx = (lista.index(nota) + semitonos) % 12
            return lista[idx]
    return nota

def procesar_palabra_estricta(palabra, semitonos, es_linea_acordes):
    patron = r"^(Do#?|Re#?|Mi|Fa#?|Sol#?|La#?|Si|[A-G][#b]?)([\#bmM79dimatusj0-9]*)$"
    match = re.match(patron, palabra)
    if match:
        raiz, resto = match.group(1), match.group(2)
        if raiz in ["Si", "La", "A"] and not resto and not es_linea_acordes:
            return palabra
        if semitonos == 0:
            return palabra # Devolvemos limpio para el espejo
        dic_bemoles = {"Db": "C#", "Eb": "D#", "Gb": "F#", "Ab": "G#", "Bb": "A#"}
        nota_busqueda = dic_bemoles.get(raiz, raiz)
        nueva_raiz = transportar_nota(nota_busqueda, semitonos)
        return f"{nueva_raiz}{resto}"
    return palabra

def procesar_texto_final(texto, semitonos):
    if not texto: return ""
    lineas_finales = []
    for linea in texto.split('\n'):
        if not linea.strip(): 
            lineas_finales.append("")
            continue
        es_linea_acordes = (linea.count(" ") / len(linea)) > 0.2 if len(linea) > 6 else True
        partes = re.split(r"(\s+)", linea)
        procesada = "".join([p if p.strip() == "" else procesar_palabra_estricta(p, semitonos, es_linea_acordes) for p in partes])
        lineas_finales.append(procesada)
    return "\n".join(lineas_finales)

# --- INTERFAZ ---
st.set_page_config(page_title="ChordMaster Pro", layout="wide")
if 'setlist' not in st.session_state: st.session_state.setlist = cargar_setlist()

# Sidebar
st.sidebar.title("🎸 ChordMaster")
menu = st.sidebar.selectbox("Menú:", ["🏠 Cantar / Vivo", "📋 Mi Setlist", "➕ Agregar Canción", "📂 Gestionar / Editar", "⚙️ Categorías"])
f_size = st.sidebar.slider("Tamaño Fuente", 12, 45, 19)

# Estilo para el visor (MANTENIDO Y REFORZADO PARA EL ESPEJO)
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono&display=swap');
    .visor-espejo {{ 
        background-color: white; color: black; 
        border-radius: 8px; padding: 20px; border: 1px solid #eee; 
        font-family: 'JetBrains Mono', monospace !important; 
        font-size: {f_size}px; white-space: pre !important; 
        line-height: 1.2; overflow-x: auto;
    }}
    </style>
    """, unsafe_allow_html=True)

df = cargar_datos()
categorias = cargar_categorias()

if menu == "🏠 Cantar / Vivo":
    busqueda = st.text_input("🔍 Buscar...")
    df_v = df[df['Título'].str.contains(busqueda, case=False, na=False)] if busqueda else df
    if not df_v.empty:
        sel_c = st.selectbox("Canción:", df_v['Título'])
        data = df_v[df_v['Título'] == sel_c].iloc[0]
        if st.button("➕ Al Setlist"):
            if sel_c not in st.session_state.setlist:
                st.session_state.setlist.append(sel_c)
                guardar_setlist(st.session_state.setlist); st.toast("Añadida")
        tp = st.number_input("Transportar", -6, 6, 0)
        cuerpo = procesar_texto_final(data['Letra'], tp)
        st.markdown(f'<div class="visor-espejo"><b>{data["Título"]}</b>\n{cuerpo}</div>', unsafe_allow_html=True)

elif menu == "📋 Mi Setlist":
    st.header("📋 Mi Setlist")
    for i, t in enumerate(st.session_state.setlist):
        col_c, col_b = st.columns([5, 1])
        with col_c:
            with st.expander(f"🎵 {t}"):
                c_data = df[df['Título'] == t].iloc[0]
                tp_sl = st.number_input("Tono", -6, 6, 0, key=f"s{i}")
                st.markdown(f'<div class="visor-espejo">{procesar_texto_final(c_data["Letra"], tp_sl)}</div>', unsafe_allow_html=True)
        with col_b:
            if st.button("🗑️", key=f"del{i}"):
                st.session_state.setlist.pop(i); guardar_setlist(st.session_state.setlist); st.rerun()

elif menu == "➕ Agregar Canción":
    st.header("➕ Nueva Canción")
    c1, c2, c3 = st.columns(3)
    t_n, a_n, cat_n = c1.text_input("Título"), c2.text_input("Autor"), c3.selectbox("Categoría", categorias)
    l_n = st.text_area("Letra y Acordes:", height=300)
    if l_n:
        st.subheader("👀 Vista Previa (Espejo)")
        # USAMOS TEXTO PLANO CON PRE PARA QUE SEA IDENTICO AL TEXT AREA
        st.markdown(f'<div class="visor-espejo">{l_n}</div>', unsafe_allow_html=True)
    if st.button("💾 Guardar"):
        nuevo = pd.DataFrame([[t_n, a_n if a_n else "Anónimo", cat_n, l_n]], columns=df.columns)
        df = pd.concat([df, nuevo], ignore_index=True); guardar_datos(df); st.rerun()

elif menu == "📂 Gestionar / Editar":
    for i, row in df.iterrows():
        with st.expander(f"📝 {row['Título']}"):
            ut = st.text_input("Título", row['Título'], key=f"ut{i}")
            ul = st.text_area("Letra", row['Letra'], height=200, key=f"ul{i}")
            if st.button("Actualizar", key=f"ub{i}"):
                df.at[i, 'Título'], df.at[i, 'Letra'] = ut, ul; guardar_datos(df); st.rerun()
            if st.button("Eliminar", key=f"ud{i}"):
                df = df.drop(i).reset_index(drop=True); guardar_datos(df); st.rerun()

elif menu == "⚙️ Categorías":
    for c in categorias:
        st.write(f"• {c}")
        if st.button("Eliminar", key=f"c{c}"):
            categorias.remove(c); guardar_categorias(categorias); st.rerun()
    n_cat = st.text_input("Nueva:")
    if st.button("Añadir"):
        categorias.append(n_cat); guardar_categorias(categorias); st.rerun()
