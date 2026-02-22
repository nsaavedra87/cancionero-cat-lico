import streamlit as st
import pandas as pd
import os
import re
from fpdf import FPDF
import base64

# --- CONFIGURACIÓN DE ARCHIVOS ---
DB_FILE = "cancionero.csv"
CAT_DEFAULT = ["Entrada", "Piedad", "Gloria", "Aleluya", "Ofertorio", "Santo", "Cordero", "Comunión", "Salida", "María", "Adoración"]

def cargar_datos():
    try:
        if os.path.exists(DB_FILE) and os.path.getsize(DB_FILE) > 0:
            return pd.read_csv(DB_FILE)
    except Exception: pass
    return pd.DataFrame(columns=["Título", "Autor", "Categoría", "Letra"])

def guardar_datos(df):
    df.to_csv(DB_FILE, index=False)

# --- MOTOR DE RENDERIZADO ---
def procesar_texto_estricto(texto, color_acorde):
    if not texto: return ""
    patron = r"\b([A-G][#b]?(m|maj|7|9|sus\d|dim|aug|add\d)?)\b|\b(Do|Re|Mi|Fa|Sol|La|Si)[#b]?(m|maj|7|9|sus\d|dim|aug|add\d)?\b"
    
    def reemplazar(match):
        acorde = match.group(0)
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

# --- GENERADOR DE PDF ---
def generar_pdf(titulo, categoria, letra, color_acorde_hex):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Courier", 'B', 16)
    pdf.cell(0, 10, titulo.upper(), ln=True, align='C')
    pdf.set_font("Courier", 'I', 10)
    pdf.cell(0, 5, f"Momento: {categoria}", ln=True, align='C')
    pdf.ln(5)
    
    h = color_acorde_hex.lstrip('#')
    rgb = tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
    
    pdf.set_font("Courier", '', 11)
    lineas = letra.split('\n')
    for linea in lineas:
        es_acorde = re.search(r'\b[A-G][#bmM79]*\b|\b(Do|Re|Mi|Fa|Sol|La|Si)[#bmM79]*\b', linea)
        if es_acorde:
            pdf.set_text_color(rgb[0], rgb[1], rgb[2])
        else:
            pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 5, linea, ln=True)
    return pdf.output()

# --- INTERFAZ ---
st.set_page_config(page_title="ChordMaster Litúrgico", page_icon="🎸", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono&display=swap');
    textarea { font-family: 'JetBrains Mono', monospace !important; font-size: 16px !important; background-color: #000 !important; color: #ddd !important; }
    .visor-musical { border-radius: 8px; padding: 20px; background-color: #121212; border: 1px solid #333; font-family: 'JetBrains Mono', monospace !important; line-height: 1.2; overflow-x: auto; color: white; }
    </style>
    """, unsafe_allow_html=True)

df = cargar_datos()

# --- SIDEBAR ---
st.sidebar.title("🎸 ChordMaster")
menu = st.sidebar.selectbox("Ir a:", ["🏠 Cantar / Buscar", "➕ Agregar Canción", "📂 Exportar PDF"])
c_chord = st.sidebar.color_picker("Color Acordes", "#FFD700")
f_size = st.sidebar.slider("Tamaño Fuente", 12, 45, 18)

# --- MODULO: AGREGAR ---
if menu == "➕ Agregar Canción":
    st.header("➕ Agregar Nueva Canción")
    col1, col2 = st.columns(2)
    with col1: titulo_n = st.text_input("Título")
    with col2: cat_n = st.selectbox("Momento Litúrgico", CAT_DEFAULT)
    
    letra_n = st.text_area("Editor (Alinea con espacios):", height=400)
    
    if letra_n:
        st.subheader("👀 Vista Previa")
        preview = procesar_texto_estricto(letra_n, c_chord)
        st.markdown(f'<div class="visor-musical" style="font-size:{f_size}px;">{preview}</div>', unsafe_allow_html=True)
        
        if st.button("💾 GUARDAR CANCIÓN", use_container_width=True):
            if titulo_n:
                nueva = pd.DataFrame([[titulo_n, "Autor", cat_n, letra_n]], columns=df.columns)
                df = pd.concat([df, nueva], ignore_index=True)
                guardar_datos(df)
                st.success(f"¡{titulo_n} guardada en {cat_n}!")
                st.rerun()

# --- MODULO: BUSCAR Y CANTAR ---
elif menu == "🏠 Cantar / Buscar":
    st.header("🏠 Biblioteca Litúrgica")
    col_f1, col_f2 = st.columns([2, 1])
    with col_f1: busqueda = st.text_input("🔍 Buscar por título...")
    with col_f2: filtro_cat = st.selectbox("📂 Filtrar por Momento", ["Todas"] + CAT_DEFAULT)

    df_filtrado = df.copy()
    if busqueda: df_filtrado = df_filtrado[df_filtrado['Título'].str.contains(busqueda, case=False)]
    if filtro_cat != "Todas": df_filtrado = df_filtrado[df_filtrado['Categoría'] == filtro_cat]

    if not df_filtrado.empty:
        seleccion = st.selectbox("Selecciona la canción:", df_filtrado['Título'])
        data_c = df_filtrado[df_filtrado['Título'] == seleccion].iloc[0]
        
        st.divider()
        st.subheader(f"{data_c['Título']} ({data_c['Categoría']})")
        final = procesar_texto_estricto(data_c['Letra'], c_chord)
        st.markdown(f'<div class="visor-musical" style="font-size:{f_size}px;">{final}</div>', unsafe_allow_html=True)
    else:
        st.info("No se encontraron canciones.")

# --- MODULO: EXPORTAR ---
elif menu == "📂 Exportar PDF":
    st.header("📂 Exportar Canciones")
    if not df.empty:
        sel_pdf = st.selectbox("Selecciona canción para PDF:", df['Título'])
        data_p = df[df['Título'] == sel_pdf].iloc[0]
        
        if st.button("🚀 Generar PDF"):
            pdf_out = generar_pdf(data_p['Título'], data_p['Categoría'], data_p['Letra'], c_chord)
            st.download_button(label="⬇️ Descargar PDF", data=pdf_out, file_name=f"{sel_pdf}.pdf", mime="application/pdf")
