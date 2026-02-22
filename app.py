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

# --- LÓGICA DE TRANSPOSICIÓN Y COLOR (M/m) ---
NOTAS_AMER = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
NOTAS_LAT = ["Do", "Do#", "Re", "Re#", "Mi", "Fa", "Fa#", "Sol", "Sol#", "La", "La#", "Si"]

def transportar_nota(nota, semitonos):
    # Detectar sistema y transportar manteniendo integridad
    if nota in NOTAS_AMER:
        idx = (NOTAS_AMER.index(nota) + semitonos) % 12
        return NOTAS_AMER[idx]
    elif nota in NOTAS_LAT:
        idx = (NOTAS_LAT.index(nota) + semitonos) % 12
        return NOTAS_LAT[idx]
    return nota

def procesar_texto_estricto(texto, semitonos, color_acorde):
    if not texto: return ""
    
    # PATRÓN DEFINITIVO: 
    # Grupo 1: Nota Base (A-G o Do-Si) + alteración (# o b)
    # Grupo 2: Modo/Complemento (M, m, maj, dim, etc.)
    patron = r"\b(Do#?|Re#?|Mi|Fa#?|Sol#?|La#?|Si|[A-G][#b]?)([Mm]|maj7|maj|7|9|sus4|sus2|dim|aug|add9)?\b"
    
    def reemplazar(match):
        nota_raiz = match.group(1)
        modo_complemento = match.group(2) if match.group(2) else ""
        
        # Normalizar bemoles a sostenidos para el diccionario
        dic_bemoles = {"Db": "C#", "Eb": "D#", "Gb": "F#", "Ab": "G#", "Bb": "A#"}
        nota_raiz_busqueda = dic_bemoles.get(nota_raiz, nota_raiz)
        
        # Transportar nota raíz
        nueva_nota = transportar_nota(nota_raiz_busqueda, semitonos) if semitonos != 0 else nota_raiz
        
        # Unir con su modo (M o m)
        acorde_final = nueva_nota + modo_complemento
        
        return f'<span style="color:{color_acorde}; font-weight:bold;">{acorde_final}</span>'
    
    lineas = texto.split('\n')
    lineas_procesadas = []
    for linea in lineas:
        if not linea.strip():
            lineas_procesadas.append("&nbsp;")
            continue
        
        # Procesar acordes
        linea_html = re.sub(patron, reemplazar, linea)
        # Forzar alineación de espacios
        linea_final = linea_html.replace(" ", "&nbsp;")
        lineas_procesadas.append(linea_final)
        
    return "<br>".join(lineas_procesadas)

# --- INTERFAZ STREAMLIT ---
st.set_page_config(page_title="ChordMaster Pro", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono&display=swap');
    textarea { font-family: 'JetBrains Mono', monospace !important; font-size: 16px !important; line-height: 1.2 !important; background-color: #000 !important; color: #ddd !important; }
    .visor-musical { border-radius: 12px; padding: 25px; background-color: #121212; border: 1px solid #444; font-family: 'JetBrains Mono', monospace !important; line-height: 1.2; overflow-x: auto; color: white; }
    .meta-data { color: #888; font-style: italic; margin-bottom: 5px; font-size: 0.9em; }
    </style>
    """, unsafe_allow_html=True)

df = cargar_datos()
categorias = cargar_categorias()

# --- SIDEBAR ---
st.sidebar.title("🎸 Menú")
menu = st.sidebar.selectbox("Ir a:", ["🏠 Cantar / Vivo", "➕ Agregar Canción", "📂 Gestionar / Editar", "⚙️ Configurar Categorías"])

c_bg = st.sidebar.color_picker("Fondo Visor", "#121212")
c_txt = st.sidebar.color_picker("Color Letra", "#FFFFFF")
c_chord = st.sidebar.color_picker("Color Acordes", "#FFD700")
f_size = st.sidebar.slider("Tamaño Fuente", 12, 45, 20)

# --- MÓDULO: AGREGAR ---
if menu == "➕ Agregar Canción":
    st.header("➕ Nueva Canción")
    col1, col2, col3 = st.columns(3)
    titulo_n = col1.text_input("Título")
    autor_n = col2.text_input("Autor")
    cat_n = col3.selectbox("Categoría", categorias)
    letra_n = st.text_area("Editor (Alinea los acordes con espacios):", height=400, placeholder="Ejemplo:\n  C       G\nAleluya, Aleluya")
    
    if letra_n:
        preview = procesar_texto_estricto(letra_n, 0, c_chord)
        st.markdown(f'<div class="visor-musical" style="background:{c_bg}; color:{c_txt}; font-size:{f_size}px;"><div class="meta-data">{titulo_n} - {autor_n}</div>{preview}</div>', unsafe_allow_html=True)
        if st.button("💾 GUARDAR"):
            nueva = pd.DataFrame([[titulo_n, autor_n if autor_n else "Anónimo", cat_n, letra_n]], columns=df.columns)
            df = pd.concat([df, nueva], ignore_index=True)
            guardar_datos(df)
            st.success("¡Guardada!"); st.rerun()

# --- MÓDULO: CANTAR CON FILTROS ---
elif menu == "🏠 Cantar / Vivo":
    st.header("🏠 Biblioteca en Vivo")
    col_f1, col_f2 = st.columns([2, 1])
    with col_f1: busqueda = st.text_input("🔍 Buscar por título o autor...")
    with col_f2: filtro_cat = st.selectbox("📂 Filtrar por Categoría", ["Todas"] + categorias)
    
    df_v = df.copy()
    if busqueda:
        df_v = df_v[df_v['Título'].str.contains(busqueda, case=False, na=False) | df_v['Autor'].str.contains(busqueda, case=False, na=False)]
    if filtro_cat != "Todas":
        df_v = df_v[df_v['Categoría'] == filtro_cat]

    if not df_v.empty:
        sel_c = st.selectbox("Seleccionar canción:", df_v['Título'])
        data = df_v[df_v['Título'] == sel_c].iloc[0]
        
        tp = st.number_input("Transportar (Semitonos)", -6, 6, 0)
        final_html = procesar_texto_estricto(data['Letra'], tp, c_chord)
        
        st.markdown(f'<div class="visor-musical" style="background:{c_bg}; color:{c_txt}; font-size:{f_size}px;"><div style="font-size:1.2em; font-weight:bold;">{data["Título"]}</div><div class="meta-data">{data["Autor"]} | {data["Categoría"]}</div><hr style="border-color:#333;">{final_html}</div>', unsafe_allow_html=True)
    else:
        st.info("No se encontraron canciones con esos filtros.")

# --- GESTIONAR ---
elif menu == "📂 Gestionar / Editar":
    st.header("📂 Gestión de Biblioteca")
    for i, row in df.iterrows():
        with st.expander(f"📝 {row['Título']}"):
            c1, c2, c3 = st.columns(3)
            nt = c1.text_input("Título", row['Título'], key=f"t{i}")
            na = c2.text_input("Autor", row['Autor'], key=f"a{i}")
            nc = c3.selectbox("Categoría", categorias, index=categorias.index(row['Categoría']) if row['Categoría'] in categorias else 0, key=f"c{i}")
            nl = st.text_area("Letra", row['Letra'], height=200, key=f"l{i}")
            if st.button("Actualizar", key=f"b{i}"):
                df.at[i, 'Título'], df.at[i, 'Autor'], df.at[i, 'Categoría'], df.at[i, 'Letra'] = nt, na, nc, nl
                guardar_datos(df); st.success("Actualizado"); st.rerun()
            if st.button("Eliminar", key=f"d{i}"):
                df = df.drop(i).reset_index(drop=True); guardar_datos(df); st.rerun()

# --- CONFIGURAR CATEGORÍAS ---
elif menu == "⚙️ Configurar Categorías":
    st.header("⚙️ Categorías")
    n_cat = st.text_input("Nueva:")
    if st.button("Añadir"):
        if n_cat and n_cat not in categorias:
            categorias.append(n_cat); guardar_categorias(categorias); st.rerun()
    st.write(categorias)
