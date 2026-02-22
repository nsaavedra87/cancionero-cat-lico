import streamlit as st
import pandas as pd
import os
import re

# --- CONFIGURACIÓN DE ARCHIVOS ---
DB_FILE = "cancionero.csv"
CAT_FILE = "categorias.csv"
SETLIST_FILE = "setlist_fijo.csv"

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

def es_acorde_real(palabra):
    # Lista estricta de inicios de acordes
    notas_validas = ("Do", "Re", "Mi", "Fa", "Sol", "La", "Si", "A", "B", "C", "D", "E", "F", "G")
    # Si no empieza con una nota, no es acorde
    if not palabra.startswith(notas_validas):
        return False
    # Si la palabra es "Si" o "La" y hay texto alrededor, suele ser letra.
    # Pero si tiene símbolos musicales, es acorde.
    if palabra in ["Si", "La", "A"]:
        return False # Se manejará por contexto de línea
    return True

def procesar_palabra_total(palabra, semitonos, es_linea_acordes):
    # Patrón que captura la RAÍZ (ej: Fa# o Do) y el RESTO (ej: m7)
    patron = r"^(Do#?|Re#?|Mi|Fa#?|Sol#?|La#?|Si|[A-G][#b]?)(.*)$"
    match = re.match(patron, palabra)
    
    if match:
        raiz = match.group(1)
        resto = match.group(2)
        
        # Validación de "Falsos Positivos" como la palabra "Si" o "La"
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

def procesar_linea_definitiva(linea, semitonos):
    if not linea.strip():
        return "&nbsp;"
    
    # Detectar si la línea es de acordes: tiene pocos caracteres en comparación con su longitud total
    # o tiene muchos espacios.
    espacios = linea.count(" ")
    es_linea_acordes = espacios / len(linea) > 0.2 if len(linea) > 5 else True

    # Dividimos por espacios pero manteniendo los espacios originales para el visor
    partes = re.split(r"(\s+)", linea)
    nueva_linea = []
    
    for p in partes:
        if p.strip() == "":
            nueva_linea.append(p)
        else:
            # Procesamos la palabra
            nueva_linea.append(procesar_palabra_total(p, semitonos, es_linea_acordes))
            
    return "".join(nueva_linea).replace(" ", "&nbsp;")

# --- INTERFAZ STREAMLIT ---
st.set_page_config(page_title="ChordMaster Pro", layout="wide")

if 'setlist' not in st.session_state:
    st.session_state.setlist = cargar_setlist()

# Sidebar
st.sidebar.title("🎸 ChordMaster Pro")
menu = st.sidebar.selectbox("Ir a:", ["🏠 Cantar / Vivo", "📋 Mi Setlist", "➕ Agregar Canción", "📂 Gestionar / Editar", "⚙️ Categorías"])

st.sidebar.markdown("---")
st.sidebar.subheader("🎨 Ajustes Visuales")
c_bg = st.sidebar.color_picker("Fondo Visor", "#FFFFFF")
c_txt = st.sidebar.color_picker("Color Letra", "#000000")
f_size = st.sidebar.slider("Tamaño Fuente", 12, 45, 19)

st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono&display=swap');
    .visor-musical {{ 
        background-color: {c_bg} !important; 
        color: {c_txt} !important; 
        border-radius: 12px; padding: 30px; border: 1px solid #ddd;
        font-family: 'JetBrains Mono', monospace !important; 
        line-height: 1.4; font-size: {f_size}px;
        white-space: nowrap;
    }}
    .visor-musical b {{ 
        font-weight: 900 !important; 
        color: inherit;
    }}
    </style>
    """, unsafe_allow_html=True)

df = cargar_datos()
categorias = cargar_categorias()

if menu == "🏠 Cantar / Vivo":
    col_f1, col_f2 = st.columns([2, 1])
    with col_f1: busqueda = st.text_input("🔍 Buscar canción...")
    with col_f2: filtro_cat = st.selectbox("📂 Categoría", ["Todas"] + categorias)
    
    df_v = df.copy()
    if busqueda:
        df_v = df_v[df_v['Título'].str.contains(busqueda, case=False, na=False)]
    if filtro_cat != "Todas":
        df_v = df_v[df_v['Categoría'] == filtro_cat]

    if not df_v.empty:
        col_sel, col_btn = st.columns([3, 1])
        sel_c = col_sel.selectbox("Seleccionar:", df_v['Título'])
        data = df_v[df_v['Título'] == sel_c].iloc[0]
        
        if col_btn.button("➕ Al Setlist", use_container_width=True):
            if sel_c not in st.session_state.setlist:
                st.session_state.setlist.append(sel_c)
                guardar_setlist(st.session_state.setlist)
                st.toast(f"'{sel_c}' añadida")

        tp = st.number_input("Transportar (Semitonos)", -6, 6, 0)
        
        lineas = data['Letra'].split('\n')
        html_final = "<br>".join([procesar_linea_definitiva(l, tp) for l in lineas])
        
        st.markdown(f'<div class="visor-musical"><b>{data["Título"]}</b><br><small>{data["Autor"]}</small><hr>{html_final}</div>', unsafe_allow_html=True)

# Módulos secundarios (Igual que antes)
elif menu == "📋 Mi Setlist":
    st.header("📋 Mi Setlist")
    for i, t in enumerate(st.session_state.setlist):
        col_t, col_b = st.columns([4, 1])
        col_t.write(f"**{i+1}. {t}**")
        if col_b.button("❌ Quitar", key=f"del_{i}"):
            st.session_state.setlist.pop(i)
            guardar_setlist(st.session_state.setlist)
            st.rerun()

elif menu == "➕ Agregar Canción":
    st.header("➕ Nueva Canción")
    c1, c2, c3 = st.columns(3)
    t_n, a_n, cat_n = c1.text_input("Título"), c2.text_input("Autor"), c3.selectbox("Categoría", categorias)
    l_n = st.text_area("Letra:", height=400)
    if st.button("💾 Guardar"):
        nueva = pd.DataFrame([[t_n, a_n if a_n else "Anónimo", cat_n, l_n]], columns=df.columns)
        df = pd.concat([df, nueva], ignore_index=True)
        guardar_datos(df); st.success("¡Guardada!"); st.rerun()

elif menu == "📂 Gestionar / Editar":
    for i, row in df.iterrows():
        with st.expander(f"📝 {row['Título']}"):
            nt = st.text_input("Título", row['Título'], key=f"t{i}")
            nl = st.text_area("Letra", row['Letra'], height=200, key=f"l{i}")
            if st.button("Actualizar", key=f"b{i}"):
                df.at[i, 'Título'], df.at[i, 'Letra'] = nt, nl
                guardar_datos(df); st.rerun()
            if st.button("Eliminar", key=f"d{i}"):
                df = df.drop(i).reset_index(drop=True); guardar_datos(df); st.rerun()

elif menu == "⚙️ Categorías":
    n_cat = st.text_input("Nueva:")
    if st.button("Añadir"):
        categorias.append(n_cat); guardar_categorias(categorias); st.rerun()
