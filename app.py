import streamlit as st
import pandas as pd
import os
import re

# --- CONFIGURACIÓN DE ARCHIVOS ---
DB_FILE = "cancionero.csv"
CAT_FILE = "categorias.csv"
SETLIST_FILE = "setlist_fijo.csv"

# --- FUNCIONES DE DATOS (Mantenidas) ---
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

# --- LÓGICA DE TRANSPOSICIÓN Y DETECCIÓN ---
NOTAS_AMER = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
NOTAS_LAT = ["Do", "Do#", "Re", "Re#", "Mi", "Fa", "Fa#", "Sol", "Sol#", "La", "La#", "Si"]

def transportar_nota(nota, semitonos):
    for lista in [NOTAS_AMER, NOTAS_LAT]:
        if nota in lista:
            idx = (lista.index(nota) + semitonos) % 12
            return lista[idx]
    return nota

def procesar_palabra_estricta(palabra, semitonos, es_linea_acordes):
    # Patrón: Nota base + (cualquier combinación de #, b, m, M, números, sus, maj, add)
    # El uso de [\#bmM79a-z0-9]* asegura que capture TODO el acorde sin romperse
    patron = r"^(Do#?|Re#?|Mi|Fa#?|Sol#?|La#?|Si|[A-G][#b]?)([\#bmM79dimatusj0-9]*)$"
    match = re.match(patron, palabra)
    
    if match:
        raiz = match.group(1)
        resto = match.group(2)
        
        # FILTRO DE LETRA: Evitar que "Si", "La" o "A" en frases normales se marquen
        # Solo se marcan si la línea es de acordes o si tienen extensiones (ej: LaM)
        if raiz in ["Si", "La", "A"] and not resto and not es_linea_acordes:
            return palabra
            
        if semitonos == 0:
            return f"<b>{palabra}</b>"
        
        # Transposición
        dic_bemoles = {"Db": "C#", "Eb": "D#", "Gb": "F#", "Ab": "G#", "Bb": "A#"}
        nota_busqueda = dic_bemoles.get(raiz, raiz)
        nueva_raiz = transportar_nota(nota_busqueda, semitonos)
        return f"<b>{nueva_raiz}{resto}</b>"
    
    return palabra

def procesar_linea_final(linea, semitonos):
    if not linea.strip(): return "&nbsp;"
    
    # Decidir si la línea es de acordes (más del 20% de espacios o muy corta)
    espacios = linea.count(" ")
    es_linea_acordes = espacios / len(linea) > 0.2 if len(linea) > 6 else True

    # Dividir por espacios preservándolos
    partes = re.split(r"(\s+)", linea)
    nueva_linea = []
    
    for p in partes:
        if p.strip() == "":
            nueva_linea.append(p)
        else:
            # Procesar palabra completa como un solo "token"
            nueva_linea.append(procesar_palabra_estricta(p, semitonos, es_linea_acordes))
            
    return "".join(nueva_linea).replace(" ", "&nbsp;")

# --- INTERFAZ STREAMLIT ---
st.set_page_config(page_title="ChordMaster Pro", layout="wide")

if 'setlist' not in st.session_state:
    st.session_state.setlist = cargar_setlist()

# Sidebar
st.sidebar.title("🎸 ChordMaster Pro")
menu = st.sidebar.selectbox("Menú:", ["🏠 Vivo", "📋 Setlist", "➕ Agregar", "📂 Editar", "⚙️ Categorías"])

st.sidebar.markdown("---")
c_bg = st.sidebar.color_picker("Fondo", "#FFFFFF")
c_txt = st.sidebar.color_picker("Letra", "#000000")
f_size = st.sidebar.slider("Fuente", 12, 45, 19)

st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono&display=swap');
    .visor-musical {{ 
        background-color: {c_bg} !important; 
        color: {c_txt} !important; 
        border-radius: 12px; padding: 30px; border: 1px solid #ddd;
        font-family: 'JetBrains Mono', monospace !important; 
        line-height: 1.5; font-size: {f_size}px;
    }}
    .visor-musical b {{ 
        font-weight: 900 !important; 
        color: inherit;
        /* Evita que el acorde se parta en dos líneas */
        white-space: nowrap; 
    }}
    </style>
    """, unsafe_allow_html=True)

df = cargar_datos()
categorias = cargar_categorias()

if menu == "🏠 Vivo":
    col1, col2 = st.columns([2, 1])
    with col1: busqueda = st.text_input("🔍 Buscar...")
    with col2: filtro_cat = st.selectbox("Categoría", ["Todas"] + categorias)
    
    df_v = df.copy()
    if busqueda: df_v = df_v[df_v['Título'].str.contains(busqueda, case=False, na=False)]
    if filtro_cat != "Todas": df_v = df_v[df_v['Categoría'] == filtro_cat]

    if not df_v.empty:
        c_sel, c_btn = st.columns([3, 1])
        sel_c = c_sel.selectbox("Canción:", df_v['Título'])
        data = df_v[df_v['Título'] == sel_c].iloc[0]
        
        if c_btn.button("➕ Setlist", use_container_width=True):
            if sel_c not in st.session_state.setlist:
                st.session_state.setlist.append(sel_c)
                guardar_setlist(st.session_state.setlist)
                st.toast("Añadida")

        tp = st.number_input("Transportar", -6, 6, 0)
        
        lineas = data['Letra'].split('\n')
        html_final = "<br>".join([procesar_linea_final(l, tp) for l in lineas])
        
        st.markdown(f'<div class="visor-musical"><b>{data["Título"]}</b><br><small>{data["Autor"]}</small><hr>{html_final}</div>', unsafe_allow_html=True)

# (Los demás módulos se mantienen iguales para ahorrar espacio, ya que la lógica central es la que cambió)
elif menu == "📋 Setlist":
    st.header("📋 Mi Setlist")
    for i, t in enumerate(st.session_state.setlist):
        col_t, col_b = st.columns([4, 1])
        col_t.write(f"**{i+1}. {t}**")
        if col_b.button("❌", key=f"del_{i}"):
            st.session_state.setlist.pop(i); guardar_setlist(st.session_state.setlist); st.rerun()

elif menu == "➕ Agregar":
    st.header("➕ Nueva")
    c1, c2, c3 = st.columns(3)
    t_n, a_n, cat_n = c1.text_input("Título"), c2.text_input("Autor"), c3.selectbox("Categoría", categorias)
    l_n = st.text_area("Letra:", height=400)
    if st.button("💾 Guardar"):
        nueva = pd.DataFrame([[t_n, a_n if a_n else "Anónimo", cat_n, l_n]], columns=df.columns)
        df = pd.concat([df, nueva], ignore_index=True); guardar_datos(df); st.success("Guardada"); st.rerun()

elif menu == "📂 Editar":
    for i, row in df.iterrows():
        with st.expander(f"📝 {row['Título']}"):
            nt = st.text_input("Título", row['Título'], key=f"t{i}")
            nl = st.text_area("Letra", row['Letra'], height=200, key=f"l{i}")
            if st.button("Actualizar", key=f"b{i}"):
                df.at[i, 'Título'], df.at[i, 'Letra'] = nt, nl; guardar_datos(df); st.rerun()
            if st.button("Eliminar", key=f"d{i}"):
                df = df.drop(i).reset_index(drop=True); guardar_datos(df); st.rerun()

elif menu == "⚙️ Categorías":
    n_cat = st.text_input("Nueva:")
    if st.button("Añadir"): categorias.append(n_cat); guardar_categorias(categorias); st.rerun()
