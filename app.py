import streamlit as st
import pandas as pd
import os
import re

# --- CONFIGURACIÓN ---
DB_FILE = "cancionero.csv"

# Diccionario de notas para iluminar el piano (0=Do, 1=Do#, etc.)
PIANO_MAP = {
    "Do": [0, 4, 7], "Dom": [0, 3, 7], "Do7": [0, 4, 7, 10], "Do#m": [1, 4, 8],
    "Re": [2, 6, 9], "Rem": [2, 5, 9], "Re7": [2, 6, 9, 0],
    "Mi": [4, 8, 11], "Mim": [4, 7, 11], "MiM": [4, 8, 11],
    "Fa": [5, 9, 0], "Fam": [5, 8, 0], "Fa#m7": [6, 9, 1, 4],
    "Sol": [7, 11, 2], "Som": [7, 10, 2], "Sol#m7": [8, 11, 3, 6],
    "La": [9, 1, 4], "Lam": [9, 0, 4], "LaM": [9, 1, 4],
    "Si": [11, 3, 6], "Bim": [11, 2, 6], "SiM": [11, 3, 6]
}

def cargar_datos():
    if os.path.exists(DB_FILE) and os.path.getsize(DB_FILE) > 0:
        return pd.read_csv(DB_FILE)
    return pd.DataFrame(columns=["Título", "Autor", "Categoría", "Letra"])

def guardar_datos(df):
    df.to_csv(DB_FILE, index=False)

# --- FUNCIÓN: CONVERTIR LÍNEAS SEPARADAS A FORMATO ANCLADO ---
def auto_convertir_formato(texto_sucio):
    """Toma líneas de acordes arriba y letra abajo y las une en [Acorde]Letra"""
    lineas = texto_sucio.split('\n')
    resultado = []
    i = 0
    while i < len(lineas):
        # Detectar si la línea actual tiene muchos espacios (típica de acordes)
        linea_actual = lineas[i]
        proxima_linea = lineas[i+1] if i+1 < len(lineas) else ""
        
        # Patrón simple: si la línea tiene palabras cortas con #, m, M o números es de acordes
        es_acorde = re.search(r'\b[A-G][#bmM79]*\b|\b(Do|Re|Mi|Fa|Sol|La|Si)[#bmM79]*\b', linea_actual)
        
        if es_acorde and proxima_linea and not re.search(r'\b[A-G]\b', proxima_linea):
            # Fusión mágica: insertamos los acordes de la linea i en la linea i+1
            linea_fusionada = ""
            pos_last = 0
            # Encontrar cada acorde y su posición
            for match in re.finditer(r'\S+', linea_actual):
                acorde = match.group()
                pos = match.start()
                # Añadir texto de la letra hasta la posición del acorde
                linea_fusionada += proxima_linea[pos_last:pos] + f"[{acorde}]"
                pos_last = pos
            linea_fusionada += proxima_linea[pos_last:]
            resultado.append(linea_fusionada)
            i += 2 # Saltamos ambas líneas procesadas
        else:
            resultado.append(linea_actual)
            i += 1
    return "\n".join(resultado)

# --- FUNCIÓN: DIBUJAR PIANO HTML ---
def dibujar_piano(notas_activas):
    teclas = [(0,"w"),(1,"b"),(2,"w"),(3,"b"),(4,"w"),(5,"w"),(6,"b"),(7,"w"),(8,"b"),(9,"w"),(10,"b"),(11,"w")]
    html = '<div style="display:flex; position:relative; height:80px; width:280px; background:#111; padding:5px; border-radius:8px;">'
    x = 0
    for n, tipo in teclas:
        color = "#00FF00" if n in notas_activas else ("white" if tipo=="w" else "black")
        if tipo == "w":
            html += f'<div style="width:35px; height:100%; background:{color}; border:1px solid #999; z-index:1;"></div>'
        else:
            html += f'<div style="width:20px; height:55%; background:{color}; border:1px solid #000; position:absolute; left:{x-10}px; z-index:2;"></div>'
        if tipo == "w": x += 35
    return html + '</div>'

# --- MOTOR DE RENDERIZADO ---
def renderizar_cifrado(texto, color_acorde):
    lineas = texto.split('\n')
    html_out = ""
    for l in lineas:
        if "[" in l:
            partes = re.split(r'(\[[^\]]+\])', l)
            ac, le = "", ""
            for p in partes:
                if p.startswith("["):
                    ac += f'<span style="color:{color_acorde}; font-weight:bold;">{p[1:-1]}</span>'
                else:
                    le += p
                    ac += "&
