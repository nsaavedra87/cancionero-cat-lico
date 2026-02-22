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

def guardar_datos(df): df.to_csv(DB_FILE, index=False)
def guardar_categorias(lista_cat): pd.DataFrame(lista_cat, columns=["Nombre"]).to_csv(CAT_FILE, index=False)
def guardar_setlist(lista_sl): pd.DataFrame(lista_sl, columns=["Título"]).to_csv(SETLIST_FILE, index=False)

# --- LÓGICA DE PROCESAMIENTO MUSICAL ---
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
            return f"<b>{palabra}</b>"
        dic_bemoles = {"Db": "C#", "Eb": "D#", "Gb": "F#", "Ab": "G#", "Bb": "A#"}
        nota_busqueda = dic_bemoles.get(raiz, raiz)
        nueva_raiz = transportar_nota(nota_busqueda, semitonos)
        return f"<b>{nueva_raiz}{resto}</b>"
    return palabra

def procesar_texto_final(texto, semitonos):
    if not texto: return ""
    lineas_finales = []
    for linea in texto.split('\n'):
        if not linea.strip(): 
            lineas_finales.append(" ") # Espacio simple para mantener el salto
            continue
        es_linea_acordes = (linea.count(" ") / len(linea)) > 0.15 if len(linea) > 6 else True
        partes = re.split(r"(\s+)", linea)
        procesada = "".join([p if p.strip() == "" else procesar_palabra_estricta(p, semitonos, es_linea_acordes) for p in partes])
        lineas_finales.append(procesada)
    return "\n".join(lineas_finales)

# --- INTERFAZ STREAMLIT ---
st.set_page_config(page_title="ChordMaster Pro", layout="wide")
if 'setlist' not in st.session_state: st.session_state.setlist = cargar_setlist()

# Sidebar
st.sidebar.title("🎸 ChordMaster")
menu = st.sidebar.selectbox("Menú:", ["🏠 Cantar / Vivo", "📋 Mi Setlist", "➕ Agregar Canción", "📂 Gestionar / Editar", "⚙️ Categorías"])
st.sidebar.markdown("---")
c_bg = st.sidebar.color_picker("Fondo Visor", "#FFFFFF")
c_txt = st.sidebar.color_picker("Color Letra", "#000000")
f_size = st.sidebar.slider("Tamaño Fuente", 12, 45, 19)

# ESTILO CORREGIDO PARA RESPETAR ESPACIOS (white-space: pre)
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono&display=swap');
    .visor-musical {{ 
        background-color: {c_bg} !important; 
        color: {c_txt} !important; 
        border-radius: 12px; padding: 25px; border: 1px solid #ddd; 
        font-family: 'JetBrains Mono', monospace !important; 
        line-height: 1.4; font-size: {f_size}px;
        white-space: pre !important; /* CLAVE: Respeta espacios múltiples */
        overflow-x: auto;
    }}
    .visor-musical b {{ font-weight: 900 !important; color: inherit; white-space: pre; }}
    </style>
    """, unsafe_allow_html=True)

df = cargar_datos()
categorias = cargar_categorias()

# --- MÓDULOS ---

if menu == "🏠 Cantar / Vivo":
    col_f1, col_f2 = st.columns([2, 1])
    with col_f1: busqueda = st.text_input("🔍 Buscar...")
    with col_f2: filtro_cat = st.selectbox("📂 Filtrar Categoría", ["Todas"] + categorias)
    
    df_v = df.copy()
    if busqueda: df_v = df_v[df_v['Título'].str.contains(busqueda, case=False, na=False)]
    if filtro_cat != "Todas": df_v = df_v[df_v['Categoría'] == filtro_cat]

    if not df_v.empty:
        c_sel, c_btn = st.columns([3, 1])
        sel_c = c_sel.selectbox("Canción:", df_v['Título'])
        data = df_v[df_v['Título'] == sel_c].iloc[0]
        
        if c_btn.button("➕ Al Setlist", use_container_width=True):
            if sel_c not in st.session_state.setlist:
                st.session_state.setlist.append(sel_c)
                guardar_setlist(st.session_state.setlist); st.toast("Añadida")

        tp = st.number_input("Transportar", -6, 6, 0, key="tp_vivo")
        html_cuerpo = procesar_texto_final(data['Letra'], tp)
        st.markdown(f'<div class="visor-musical"><b>{data["Título"]}</b>\n{data["Autor"]} | {data["Categoría"]}\n<hr style="border:0.5px solid {c_txt}; opacity:0.2;">\n{html_cuerpo}</div>', unsafe_allow_html=True)

elif menu == "📋 Mi Setlist":
    st.header("📋 Mi Setlist")
    if not st.session_state.setlist:
        st.info("No hay canciones en el setlist.")
    else:
        for i, t in enumerate(st.session_state.setlist):
            with st.expander(f"🎵 {i+1}. {t}"):
                cancion_data = df[df['Título'] == t]
                if not cancion_data.empty:
                    data = cancion_data.iloc[0]
                    col_info, col_del = st.columns([4, 1])
                    col_info.write(f"**Autor:** {data['Autor']} | **Categoría:** {data['Categoría']}")
                    if col_del.button("🗑️ Quitar", key=f"del_sl_{i}"):
                        st.session_state.setlist.pop(i)
                        guardar_setlist(st.session_state.setlist); st.rerun()
                    
                    tp_sl = st.number_input("Transportar", -6, 6, 0, key=f"tp_sl_{i}")
                    st.markdown(f'<div class="visor-musical">{procesar_texto_final(data["Letra"], tp_sl)}</div>', unsafe_allow_html=True)

elif menu == "➕ Agregar Canción":
    st.header("➕ Nueva Canción")
    c1, c2, c3 = st.columns(3)
    t_n, a_n, cat_n = c1.text_input("Título"), c2.text_input("Autor"), c3.selectbox("Categoría", categorias)
    l_n = st.text_area("Letra y Acordes:", height=250, help="Usa una fuente monoespaciada para alinear.")
    if l_n:
        st.subheader("👀 Vista Previa")
        st.markdown(f'<div class="visor-musical">{procesar_texto_final(l_n, 0)}</div>', unsafe_allow_html=True)
    if st.button("💾 Guardar"):
        if t_n and l_n:
            nueva = pd.DataFrame([[t_n, a_n if a_n else "Anónimo", cat_n, l_n]], columns=df.columns)
            df = pd.concat([df, nueva], ignore_index=True); guardar_datos(df); st.success("¡Guardada!"); st.rerun()

elif menu == "📂 Gestionar / Editar":
    for i, row in df.iterrows():
        with st.expander(f"📝 {row['Título']}"):
            ut = st.text_input("Título", row['Título'], key=f"ut{i}")
            ua = st.text_input("Autor", row['Autor'], key=f"ua{i}")
            uc = st.selectbox("Categoría", categorias, index=categorias.index(row['Categoría']) if row['Categoría'] in categorias else 0, key=f"uc{i}")
            ul = st.text_area("Letra", row['Letra'], height=200, key=f"ul{i}")
            if st.button("Actualizar", key=f"ub{i}"):
                df.at[i, 'Título'], df.at[i, 'Autor'], df.at[i, 'Categoría'], df.at[i, 'Letra'] = ut, ua, uc, ul
                guardar_datos(df); st.rerun()
            if st.button("Eliminar", key=f"ud{i}"):
                df = df.drop(i).reset_index(drop=True); guardar_datos(df); st.rerun()

elif menu == "⚙️ Categorías":
    st.header("⚙️ Categorías")
    for c in categorias:
        c1, c2 = st.columns([3, 1])
        c1.write(f"• {c}")
        if c2.button("Eliminar", key=f"cat_{c}"):
            categorias.remove(c); guardar_categorias(categorias); st.rerun()
    n_cat = st.text_input("Nueva categoría:")
    if st.button("Añadir"):
        if n_cat and n_cat not in categorias:
            categorias.append(n_cat); guardar_categorias(categorias); st.rerun()
