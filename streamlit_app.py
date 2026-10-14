import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, timedelta
import calendar
import sqlite3
import hashlib
import random
import os
import base64

# ==========================================
# 1. CONFIGURACIÓN INICIAL DEL SOFTWARE
# ==========================================
st.set_page_config(
    page_title="Nexus Obra - Control Presupuestal", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# Función para detectar .jpg, .jpeg o .png automáticamente
def get_base64_image(base_name):
    for ext in [".jpg", ".png", ".jpeg"]:
        if os.path.exists(base_name + ext):
            try:
                with open(base_name + ext, "rb") as img_file:
                    return base64.b64encode(img_file.read()).decode()
            except: pass
    return ""

# ==========================================
# CONSTANTES GLOBALES Y COLORES (PALETA INTERIOR)
# ==========================================
meses_espanol = ["", "ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO", "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"]

# Colores de UI (Interior)
COLOR_PRIMARIO = "#2C3E50"      
COLOR_SECUNDARIO = "#4A86E8"    
COLOR_FONDO_CLARO = "#F1F5F9"   
COLOR_TITULOS = "#DC2626"       
COLOR_TEXTO = "#0f172a"         

# Colores exactos para el gráfico de Dona y Calendario
COLOR_DONA_1 = "#224e6e"        
COLOR_DONA_2 = "#1d2b43"        
COLOR_DONA_3 = "#99c488"        
COLOR_AMARILLO = "#facc15"      # Color restaurado para Medio Día

# ==========================================
# 2. BASE DE DATOS PERMANENTE Y TABLAS
# ==========================================
conn = sqlite3.connect('obra_nexus.db', timeout=10.0, check_same_thread=False)
c = conn.cursor()

c.execute('CREATE TABLE IF NOT EXISTS usuarios (email TEXT UNIQUE, password TEXT)')
c.execute('CREATE TABLE IF NOT EXISTS personal (partida TEXT, nombre TEXT, especialidad TEXT, jornal REAL DEFAULT 120.0, almuerzo_costo REAL DEFAULT 7.0, UNIQUE(partida, nombre))')
c.execute('CREATE TABLE IF NOT EXISTS materiales (partida TEXT, fecha TEXT, insumo TEXT, und TEXT, cantidad REAL, precio REAL, descuento REAL DEFAULT 0.0)')
c.execute('CREATE TABLE IF NOT EXISTS asistencia (partida TEXT, trabajador TEXT, fecha TEXT, estado TEXT, almuerzo TEXT, actividad TEXT, UNIQUE(partida, trabajador, fecha))')
c.execute('CREATE TABLE IF NOT EXISTS presupuestos (partida TEXT PRIMARY KEY, modo TEXT, total REAL, materiales REAL, mano_obra REAL, fecha_creacion TEXT)')
conn.commit()

# Actualizaciones estructurales
try: c.execute('ALTER TABLE personal ADD COLUMN jornal REAL DEFAULT 120.0'); conn.commit()
except: pass
try: c.execute('ALTER TABLE personal ADD COLUMN almuerzo_costo REAL DEFAULT 7.0'); conn.commit()
except: pass
try: c.execute('ALTER TABLE materiales ADD COLUMN und TEXT'); conn.commit()
except: pass
try: c.execute('ALTER TABLE materiales ADD COLUMN descuento REAL DEFAULT 0.0'); conn.commit()
except: pass
try: c.execute('ALTER TABLE asistencia ADD COLUMN actividad TEXT'); conn.commit()
except: pass
try: 
    c.execute('ALTER TABLE presupuestos ADD COLUMN fecha_creacion TEXT')
    c.execute('UPDATE presupuestos SET fecha_creacion = ? WHERE fecha_creacion IS NULL', (str(date.today()),))
    conn.commit()
except: pass

def encriptar_clave(clave): return hashlib.sha256(str.encode(clave)).hexdigest()

def agregar_usuario(email, clave): 
    try:
        c.execute('INSERT INTO usuarios (email, password) VALUES (?, ?)', (email, encriptar_clave(clave)))
        conn.commit()
        return True
    except: return False

def verificar_usuario(email, clave):
    c.execute('SELECT * FROM usuarios WHERE email=? AND password=?', (email, encriptar_clave(clave)))
    return c.fetchone() is not None

def guardar_presupuesto_bd(partida, modo, total, mat, mo):
    c.execute("SELECT 1 FROM presupuestos WHERE partida=?", (partida,))
    if c.fetchone():
        c.execute("UPDATE presupuestos SET modo=?, total=?, materiales=?, mano_obra=? WHERE partida=?", 
                  (modo, float(total), float(mat), float(mo), partida))
    else:
        c.execute("INSERT INTO presupuestos (partida, modo, total, materiales, mano_obra, fecha_creacion) VALUES (?, ?, ?, ?, ?, ?)", 
                  (partida, modo, float(total), float(mat), float(mo), str(date.today())))
    conn.commit()

if 'autenticado' not in st.session_state: st.session_state['autenticado'] = False
if 'mostrar_registro' not in st.session_state: st.session_state['mostrar_registro'] = False
if 'partida_actual' not in st.session_state: st.session_state['partida_actual'] = None
if 'cal_mes' not in st.session_state: st.session_state['cal_mes'] = 10 
if 'cal_ano' not in st.session_state: st.session_state['cal_ano'] = 2026

if 'lista_partidas' not in st.session_state: 
    c.execute("SELECT DISTINCT partida FROM presupuestos")
    partidas_bd = [row[0] for row in c.fetchall() if row[0] is not None and str(row[0]).strip() != ""]
    st.session_state['lista_partidas'] = partidas_bd if partidas_bd else ["Obras Provisionales"]

# ==========================================
# 3. PANTALLA DE INICIO (DISEÑO EXACTO AYACUCHO)
# ==========================================
if not st.session_state['autenticado']:
    
    bg_b64 = get_base64_image("fondo")
    logo_b64 = get_base64_image("logo")
    
    bg_url = f"data:image/jpeg;base64,{bg_b64}" if bg_b64 else "https://images.unsplash.com/photo-1541888086425-d81bb19240f5?q=80&w=2070&auto=format&fit=crop"
    
    st.markdown(f"""
        <style>
        /* Fondo principal con gradiente */
        .stApp {{
            background-image: linear-gradient(to right, rgba(6, 25, 56, 0.95) 0%, rgba(6, 25, 56, 0.8) 45%, rgba(6, 25, 56, 0.1) 100%), url("{bg_url}");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
            font-family: 'Segoe UI', Arial, sans-serif;
        }}
        header {{visibility: hidden;}}
        .st-emotion-cache-1jicfl2 {{padding: 2rem 1rem;}}
        
        /* Tarjeta Blanca de Login (Más angosta y elegante) */
        div[data-testid="stForm"] {{
            background-color: white !important;
            border-radius: 12px !important;
            padding: 30px 25px 20px 25px !important;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3) !important;
            border: none !important;
            max-width: 380px !important;
            margin: 0 auto !important;
        }}
        
        /* Ocultar etiquetas predeterminadas */
        div[data-testid="stForm"] label {{ display: none !important; }}
        
        /* Contenedor del Input para no deformar el ojo */
        div[data-testid="stForm"] div[data-baseweb="input"] {{
            background-color: #f8fafc !important;
            border: 1px solid #cbd5e1 !important;
            border-radius: 6px !important;
            overflow: hidden;
            margin-bottom: 5px;
        }}
        div[data-testid="stForm"] div[data-baseweb="input"]:focus-within {{
            border-color: #0056b3 !important;
            box-shadow: 0 0 0 1px #0056b3 !important;
        }}
        
        /* El input real (texto y password) */
        div[data-testid="stForm"] input {{
            background-color: transparent !important;
            color: #0f172a !important;
            border: none !important;
            padding: 12px 15px 12px 40px !important;
            font-size: 0.95rem !important;
            box-shadow: none !important;
        }}
        
        /* Ojo de contraseña intacto */
        div[data-testid="stForm"] div[role="button"] {{
            background-color: transparent !important;
            color: #64748b !important;
            padding: 0 10px !important;
        }}
        
        /* Íconos Modernos SVG usando Background Image */
        div[data-testid="stForm"] input[placeholder="Usuario"] {{
            background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='%2364748b' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2'/%3E%3Ccircle cx='12' cy='7' r='4'/%3E%3C/svg%3E") !important;
            background-repeat: no-repeat !important;
            background-position: 12px center !important;
        }}
        div[data-testid="stForm"] input[type="password"] {{
            background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='%2364748b' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Crect x='3' y='11' width='18' height='18' rx='2' ry='2'/%3E%3Cpath d='M7 11V7a5 5 0 0 1 10 0v4'/%3E%3C/svg%3E") !important;
            background-repeat: no-repeat !important;
            background-position: 12px center !important;
        }}
        
        /* Botón Ingresar Azul Grande */
        div[data-testid="stForm"] button {{ 
            background-color: #0056b3 !important; 
            color: white !important; 
            border: none !important; 
            border-radius: 6px !important; 
            font-size: 1.1rem !important; 
            font-weight: 600 !important;
            padding: 10px !important;
            width: 100% !important; 
            transition: 0.3s; 
            margin-top: 15px !important;
        }}
        div[data-testid="stForm"] button:hover {{ background-color: #004494 !important; transform: translateY(-1px); }}
        
        /* Botón Crear Cuenta (Fuera del Formulario) */
        div[data-testid="column"] div[data-testid="stButton"] button {{
            background-color: white !important;
            color: #0f172a !important;
            border: 1px solid #cbd5e1 !important;
            border-radius: 20px !important; /* Forma de píldora */
            font-size: 0.85rem !important;
            font-weight: 600 !important;
            padding: 6px 15px !important;
            width: 100% !important;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05) !important;
        }}
        div[data-testid="column"] div[data-testid="stButton"] button:hover {{
            background-color: #f1f5f9 !important;
            transform: translateY(-2px);
        }}

        /* Textos Izquierda */
        .left-title {{ color: #ffffff !important; line-height: 1.1; margin-bottom: 15px; font-weight: 800; font-size: 3.2rem; }}
        .left-title span {{ color: #38bdf8 !important; }}
        .left-subtitle {{ color: #e2e8f0; font-size: 1.05rem; line-height: 1.5; max-width: 550px; margin-bottom: 40px; }}
        
        /* Íconos 5 Características */
        .features-container {{ display: flex; gap: 20px; text-align: center; margin-bottom: 30px; flex-wrap: wrap; }}
        .feature-item {{ display: flex; flex-direction: column; align-items: center; width: 85px; }}
        .feature-icon {{ 
            background: transparent; border: 2px solid #38bdf8; color: #38bdf8; 
            width: 65px; height: 65px; border-radius: 50%; display: flex; align-items: center; 
            justify-content: center; margin-bottom: 10px; transition: 0.3s;
        }}
        .feature-icon svg {{ fill: currentColor; width: 30px; height: 30px; }}
        .feature-item:hover .feature-icon {{ background: #38bdf8; color: white; transform: scale(1.05); }}
        .feature-text {{ color: white; font-size: 0.8rem; font-weight: 600; line-height: 1.2; }}
        
        /* Redes Sociales Footer */
        .social-footer {{ display: flex; align-items: center; gap: 15px; color: white; font-weight: 500; font-size: 0.95rem; }}
        .social-separator {{ height: 20px; width: 1px; background-color: rgba(255,255,255,0.3); margin: 0 5px; }}
        .social-icons {{ display: flex; gap: 15px; }}
        .social-icons svg {{ fill: white; width: 22px; height: 22px; cursor: pointer; transition: 0.3s; }}
        .social-icons svg:hover {{ fill: #38bdf8; transform: translateY(-2px); }}
        
        /* Ubicación blanca pura */
        .location {{ color: #ffffff !important; font-size: 0.9rem; margin-top: 15px; display:flex; align-items:center; gap:5px;}}
        
        /* Estilizar el File Uploader */
        div[data-testid="stFileUploader"] {{ margin-top: -15px; max-width: 380px; margin-left: auto; margin-right: auto; }}
        </style>
    """, unsafe_allow_html=True)

    st.write("<br><br>", unsafe_allow_html=True)
    col_izq, col_espacio, col_der = st.columns([1.6, 0.1, 1.1])
    
    with col_izq:
        if logo_b64:
            st.markdown(f"""
                <div style="display:flex; align-items:center; gap:15px; margin-bottom:30px;">
                    <img src="data:image/png;base64,{logo_b64}" width="70">
                    <h2 style="color:white; margin:0; font-weight:900; font-size:1.6rem; line-height:1.2; border-left:3px solid #38bdf8; padding-left:15px;">
                        CONTROL DE OBRAS<br>
                        <span style="color:#38bdf8; font-size:1.3rem;">MINI - AYACUCHO</span>
                    </h2>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
                <div style="display:flex; align-items:center; gap:15px; margin-bottom:30px;">
                    <h2 style="color:white; margin:0; font-weight:900; font-size:1.6rem; line-height:1.2; border-left:4px solid #38bdf8; padding-left:15px;">
                        CONTROL DE OBRAS<br>
                        <span style="color:#38bdf8; font-size:1.4rem;">MINI - AYACUCHO</span>
                    </h2>
                </div>
            """, unsafe_allow_html=True)
            
        st.markdown("""
            <h1 class="left-title">Bienvenido al Sistema<br><span>de Control de Obras</span></h1>
            <p class="left-subtitle">Gestiona el avance de tu proyecto por partidas, controla el personal, registra pagos y mantiene el control de tu presupuesto de materiales y mano de obra.</p>
            
            <div class="features-container">
                <div class="feature-item">
                    <div class="feature-icon"><svg viewBox="0 0 24 24"><path d="M3 3v18h18v-2H5V3H3m4 14h3v-6H7v6m5 0h3V7h-3v10m5 0h3v-4h-3v4z"/></svg></div>
                    <div class="feature-text">Avance por<br>partidas</div>
                </div>
                <div class="feature-item">
                    <div class="feature-icon"><svg viewBox="0 0 24 24"><path d="M16 11c1.66 0 2.99-1.34 2.99-3S17.66 5 16 5c-1.66 0-3 1.34-3 3s1.34 3 3 3zm-8 0c1.66 0 2.99-1.34 2.99-3S9.66 5 8 5C6.34 5 5 6.34 5 8s1.34 3 3 3zm0 2c-2.33 0-7 1.17-7 3.5V19h14v-2.5c0-2.33-4.67-3.5-7-3.5zm8 0c-.29 0-.62.02-.97.05 1.16.84 1.97 1.97 1.97 3.45V19h6v-2.5c0-2.33-4.67-3.5-7-3.5z"/></svg></div>
                    <div class="feature-text">Personal diario<br>y por hora</div>
                </div>
                <div class="feature-item">
                    <div class="feature-icon"><svg viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm.31-8.86c-1.77-.45-2.34-.94-2.34-1.67 0-.84.79-1.43 2.1-1.43 1.38 0 1.9.66 1.94 1.64h1.71c-.05-1.34-.87-2.57-2.49-2.97V5H10.9v1.69c-1.51.32-2.72 1.3-2.72 2.81 0 1.79 1.49 2.69 3.66 3.21 1.95.46 2.34 1.15 2.34 1.87 0 .53-.39 1.64-2.25 1.64-1.74 0-2.26-.87-2.32-1.92H7.85c.08 1.87 1.48 3.01 3.05 3.35V19h2.32v-1.65c1.78-.34 2.94-1.42 2.94-3.03 0-2.3-1.85-3.01-3.85-3.46z"/></svg></div>
                    <div class="feature-text">Rendimiento<br>diario</div>
                </div>
                <div class="feature-item">
                    <div class="feature-icon"><svg viewBox="0 0 24 24"><path d="M11.8 10.9c-2.27-.59-3-1.2-3-2.15 0-1.09 1.01-1.85 2.7-1.85 1.78 0 2.44.85 2.5 2.1h2.21c-.07-1.72-1.12-3.3-3.21-3.81V3h-3v2.16c-1.94.42-3.5 1.68-3.5 3.61 0 2.31 1.91 3.46 4.7 4.13 2.5.6 3 1.48 3 2.41 0 .69-.49 1.79-2.7 1.79-2.06 0-2.87-.92-2.98-2.1h-2.2c.12 2.19 1.76 3.42 3.68 3.83V21h3v-2.15c1.95-.37 3.5-1.5 3.5-3.55 0-2.84-2.43-3.81-4.7-4.4z"/></svg></div>
                    <div class="feature-text">Pagos y<br>observaciones</div>
                </div>
                <div class="feature-item">
                    <div class="feature-icon"><svg viewBox="0 0 24 24"><path d="M21 16.5c0 .38-.21.71-.53.88l-7.9 4.44c-.16.12-.36.18-.57.18-.21 0-.41-.06-.57-.18l-7.9-4.44A.991.991 0 0 1 3 16.5v-9c0-.38.21-.71.53-.88l7.9-4.44c.16-.12.36-.18.57-.18.21 0 .41.06.57.18l7.9 4.44c.32.17.53.5.53.88v9zM12 4.15L6.04 7.5 12 10.85l5.96-3.35L12 4.15zM5 15.91l6 3.38v-6.71L5 9.21v6.7zM19 9.21l-6 3.38v6.71l6-3.38v-6.7z"/></svg></div>
                    <div class="feature-text">Materiales y<br>presupuesto</div>
                </div>
            </div>
            
            <div style="display: flex; justify-content: space-between; align-items: flex-end; margin-top: 30px;">
                <div>
                    <div class="social-footer">
                        <span>Síguenos en nuestras redes</span>
                        <div class="social-separator"></div>
                        <div class="social-icons">
                            <svg viewBox="0 0 24 24"><path d="M22 12c0-5.52-4.48-10-10-10S2 6.48 2 12c0 4.84 3.44 8.87 8 9.8V15H8v-3h2V9.5C10 7.57 11.57 6 13.5 6H16v3h-2c-.55 0-1 .45-1 1v2h3v3h-3v6.95c5.05-.5 9-4.76 9-9.95z"/></svg>
                            <svg viewBox="0 0 24 24"><path d="M12.53.02C13.84 0 15.14.01 16.44 0c.08 1.53.63 3.09 1.75 4.17 1.12 1.11 2.7 1.62 4.24 1.79v4.03c-1.44-.05-2.89-.35-4.2-.97-.57-.26-1.1-.59-1.62-.93-.01 2.92.01 5.84-.02 8.75-.08 1.4-.54 2.79-1.35 3.94-1.31 1.92-3.58 3.17-5.91 3.21-1.43.08-2.86-.31-4.08-1.03-2.02-1.19-3.44-3.37-3.65-5.71-.02-.5-.03-1-.01-1.49.18-1.9 1.12-3.72 2.58-4.96 1.66-1.44 3.98-2.13 6.15-1.72.02 1.48-.04 2.96-.04 4.44-.99-.32-2.15-.23-3.02.37-.63.41-1.11 1.04-1.36 1.75-.21.51-.15 1.07-.14 1.61.24 1.64 1.82 3.02 3.5 2.87 1.12-.01 2.19-.66 2.77-1.61.19-.33.4-.67.41-1.06.1-1.79.06-3.57.07-5.36.01-4.03-.01-8.05.02-12.07z"/></svg>
                            <svg viewBox="0 0 24 24"><path d="M7.8 2h8.4C19.4 2 22 4.6 22 7.8v8.4a5.8 5.8 0 0 1-5.8 5.8H7.8C4.6 22 2 19.4 2 16.2V7.8A5.8 5.8 0 0 1 7.8 2zm-.2 2A3.6 3.6 0 0 0 4 7.6v8.8C4 18.39 5.61 20 7.6 20h8.8a3.6 3.6 0 0 0 3.6-3.6V7.6C20 5.61 18.39 4 16.4 4H7.6zm9.65 1.5a1.25 1.25 0 0 1 0 2.5 1.25 1.25 0 0 1 0-2.5zM12 7a5 5 0 1 1 0 10 5 5 0 0 1 0-10zm0 2a3 3 0 1 0 0 6 3 3 0 0 0 0-6z"/></svg>
                            <svg viewBox="0 0 24 24"><path d="M21.58 7.19c-.23-.86-.91-1.54-1.77-1.77C18.25 5 12 5 12 5s-6.25 0-7.81.42c-.86.23-1.54.91-1.77 1.77C2 8.75 2 12 2 12s0 3.25.42 4.81c.23.86.91 1.54 1.77 1.77C5.75 19 12 19 12 19s6.25 0 7.81-.42c.86-.23 1.54-.91 1.77-1.77C22 15.25 22 12 22 12s0-3.25-.42-4.81zM10 15V9l5.2 3L10 15z"/></svg>
                            <svg viewBox="0 0 24 24"><path d="M12.03 2.5a9.53 9.53 0 0 0-8.25 14.3l-1.3 4.75 4.86-1.27a9.51 9.51 0 1 0 4.69-17.78zM12.03 20c-1.55 0-3.03-.4-4.33-1.14l-.31-.18-3.22.84.86-3.14-.2-.32A7.95 7.95 0 1 1 12.03 20zm4.37-5.96c-.24-.12-1.42-.7-1.64-.78-.22-.08-.38-.12-.54.12-.16.24-.62.78-.76.94-.14.16-.28.18-.52.06-.24-.12-1.02-.38-1.94-1.2-.71-.64-1.2-1.43-1.34-1.67-.14-.24-.01-.37.11-.49.11-.11.24-.28.36-.42.12-.14.16-.24.24-.4.08-.16.04-.3-.02-.42-.06-.12-.54-1.3-.74-1.78-.19-.47-.38-.4-.54-.41-.14 0-.3 0-.46 0-.16 0-.42.06-.64.3-.22.24-.84.82-.84 2s.86 2.32.98 2.48c.12.16 1.68 2.57 4.08 3.61.57.25 1.01.4 1.36.5.57.18 1.09.16 1.5.09.47-.07 1.42-.58 1.62-1.14.2-.56.2-1.04.14-1.14-.06-.1-.22-.16-.46-.28z"/></svg>
                        </div>
                    </div>
                    <div class="location" style="margin-top: 5px;">
                        <svg width="14" height="14" fill="#ffffff" viewBox="0 0 24 24"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5a2.5 2.5 0 1 1 0-5 2.5 2.5 0 0 1 0 5z"/></svg>
                        Ayacucho - Perú
                    </div>
                </div>
                <div style="transform: rotate(-12deg); color: white; font-family: 'Brush Script MT', 'Lucida Handwriting', cursive; font-size: 2.2rem; margin-bottom: 20px; opacity: 0.95;">
                    Tu obra,<br>en buenas manos
                </div>
            </div>
        """, unsafe_allow_html=True)

    with col_der:
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True) 
        
        if not st.session_state['mostrar_registro']:
            with st.form("form_login"):
                if logo_b64:
                    st.markdown(f"""
                        <div style="display:flex; align-items:center; margin-bottom:20px;">
                            <img src="data:image/png;base64,{logo_b64}" width="55" style="margin-right: 15px;">
                            <div style="border-left: 2px solid #cbd5e1; height: 40px; margin-right: 15px;"></div>
                            <h2 style='color:#0f172a; margin:0; font-weight:900; font-size:1.1rem; line-height:1.2;'>
                                CONTROL DE OBRAS<br>
                                <span style='color:#0056b3; font-size:0.95rem;'>MINI - AYACUCHO</span>
                            </h2>
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown("<h2 style='color:#0f172a; margin:0 0 15px 0; font-weight:900; font-size:1.3rem; border-left:3px solid #0056b3; padding-left:10px;'>CONTROL DE OBRAS<br><span style='color:#0056b3;'>MINI</span></h2>", unsafe_allow_html=True)
                
                st.markdown("""
                    <div style='text-align:left; margin-bottom:20px;'>
                        <h2 style='color:#0f172a; margin:0; font-weight:800; font-size:1.8rem;'>Iniciar Sesión</h2>
                        <p style='color:#64748b; margin:5px 0 0 0; font-size:0.9rem;'>Accede a tu cuenta para continuar</p>
                    </div>
                """, unsafe_allow_html=True)
                
                email_login = st.text_input("Usuario", placeholder="Usuario", label_visibility="collapsed")
                clave_login = st.text_input("Contraseña", type="password", placeholder="Contraseña", label_visibility="collapsed")
                
                btn_login = st.form_submit_button("Ingresar ➔")
                
                if btn_login:
                    if verificar_usuario(email_login, clave_login):
                        st.session_state['autenticado'] = True
                        st.session_state['usuario_actual'] = email_login
                        st.rerun()
                    else:
                        st.error("Credenciales incorrectas. Verifique sus datos.")
            
            # Enlaces fuera de la caja blanca (Lado a lado)
            col_links1, col_links2 = st.columns([1.3, 1])
            with col_links1:
                st.markdown("<div style='margin-top:12px; margin-left: 10px;'><a href='#' style='color:#60a5fa; font-weight:500; font-size:0.9rem; text-decoration:none; text-shadow: 0 1px 2px rgba(0,0,0,0.5);'>¿Olvidaste tu contraseña?</a></div>", unsafe_allow_html=True)
            with col_links2:
                if st.button("Crear cuenta", use_container_width=True):
                    st.session_state['mostrar_registro'] = True
                    st.rerun()
            
            # Panel de restauración del servidor ajustado a la imagen
            st.markdown("""
                <div style="background-color: #f0f9ff; border-radius: 6px; padding: 12px 15px; margin-top: 15px; display: flex; align-items: center; justify-content: space-between; border: 1px solid #bae6fd; max-width: 380px; margin-left: auto; margin-right: auto;">
                    <div style="display: flex; align-items: center; gap: 12px;">
                        <div style="width: 5px; height: 5px; background-color: #00e676; border-radius: 50%; box-shadow: 0 0 6px #00e676;"></div>
                        <svg width="20" height="20" fill="#0369a1" viewBox="0 0 24 24"><path d="M4 5v14h16V5H4zm14 12H6v-2h12v2zm0-4H6V9h12v4zm0-4H6V5h12v4z"/></svg>
                        <div style="display: flex; flex-direction: column;">
                            <span style="color:#1e3a8a; font-size:0.85rem; font-weight:500; line-height: 1.2;">Se reinició el servidor</span>
                            <span style="color:#3b82f6; font-size:0.75rem; font-weight:400; line-height: 1.2;">Restaura tu Base de Datos aquí</span>
                        </div>
                    </div>
                    <div style="color: #3b82f6; font-size:1.1rem; font-weight:bold;">➔</div>
                </div>
            """, unsafe_allow_html=True)
            archivo_emergencia = st.file_uploader("Subir DB", type=["db"], label_visibility="collapsed")
            if archivo_emergencia is not None:
                with open("obra_nexus.db", "wb") as f:
                    f.write(archivo_emergencia.getbuffer())
                st.success("¡Base de datos restaurada con éxito! Ya puedes ingresar.")
                st.rerun()
                
        else:
            with st.form("form_registro"):
                if logo_b64:
                    st.markdown(f"""
                        <div style="display:flex; align-items:center; margin-bottom:20px;">
                            <img src="data:image/png;base64,{logo_b64}" width="55" style="margin-right: 15px;">
                            <div style="border-left: 2px solid #cbd5e1; height: 40px; margin-right: 15px;"></div>
                            <h2 style='color:#0f172a; margin:0; font-weight:900; font-size:1.1rem; line-height:1.2;'>
                                CONTROL DE OBRAS<br>
                                <span style='color:#0056b3; font-size:0.95rem;'>MINI - AYACUCHO</span>
                            </h2>
                        </div>
                    """, unsafe_allow_html=True)
                
                st.markdown("""
                    <div style='text-align:left; margin-bottom:20px;'>
                        <h2 style='color:#0f172a; margin:0; font-weight:800; font-size:1.8rem;'>Crear Cuenta</h2>
                        <p style='color:#64748b; margin:5px 0 0 0; font-size:0.9rem;'>Registra un nuevo usuario en el sistema</p>
                    </div>
                """, unsafe_allow_html=True)
                email_reg = st.text_input("Nuevo Correo", placeholder="Correo electrónico", label_visibility="collapsed")
                clave_reg = st.text_input("Crear Contraseña", type="password", placeholder="Nueva contraseña", label_visibility="collapsed")
                btn_reg = st.form_submit_button("Registrar Cuenta ➔")
                
                if btn_reg:
                    if email_reg and clave_reg:
                        if agregar_usuario(email_reg, clave_reg):
                            st.success("¡Cuenta creada exitosamente! Vuelve a iniciar sesión.")
                            st.session_state['mostrar_registro'] = False
                            st.rerun()
                        else:
                            st.error("El usuario ya se encuentra registrado.")
                    else:
                        st.warning("Completa todos los campos solicitados.")
            
            col_links3, col_links4 = st.columns([1.3, 1])
            with col_links4:
                if st.button("Volver al Login", use_container_width=True):
                    st.session_state['mostrar_registro'] = False
                    st.rerun()
    st.stop()


# ==========================================
# 4. DISEÑO DE INTERFAZ INTERNA PROFESIONAL
# ==========================================
st.markdown(f"""
    <style>
    /* Forzar fondo blanco absoluto interior y quitar background image de login */
    .stApp, .main {{ background-color: #FFFFFF !important; background-image: none !important; color: {COLOR_TEXTO} !important; font-family: 'Segoe UI', Arial, sans-serif !important; }}
    
    /* Textos oscuros y negritos */
    h1, h2, h3, h4, h5, h6, p, span, div {{ color: {COLOR_TEXTO} !important; }}
    label {{ font-weight: 800 !important; font-size: 0.9rem !important; color: #000000 !important; }}
    
    /* Eliminar cualquier recuadro de la etiqueta del selectbox para que quede igual al input */
    div[data-testid="stSelectbox"] > label {{ background: transparent !important; border: none !important; }}
    
    /* BOTONES ESTILO OUTLINE LIMPIO */
    div[data-testid="stButton"] > button {{
        background-color: #ffffff !important;
        color: {COLOR_PRIMARIO} !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 6px !important;
        padding: 0.4rem 1.2rem !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        text-transform: none !important; 
        width: auto !important; 
        box-shadow: 0 1px 2px rgba(0,0,0,0.05) !important;
        transition: all 0.2s;
        min-width: 120px;
    }}
    div[data-testid="stButton"] > button:hover {{
        background-color: #f8fafc !important;
        color: #0f172a !important;
        border-color: #94a3b8 !important;
    }}
    
    /* Inputs de texto y números compactos y limpios */
    .stTextInput input, .stNumberInput input, div[data-baseweb="select"] > div, .stTextArea textarea {{
        background-color: #f8fafc !important;
        color: #000000 !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 6px !important;
        font-weight: 600 !important;
        padding: 0.4rem !important;
    }}
    .stTextInput input:focus, .stNumberInput input:focus {{
        border-color: {COLOR_SECUNDARIO} !important;
        box-shadow: 0 0 0 1px {COLOR_SECUNDARIO} !important;
    }}
    
    /* Contenedores con bordes finos */
    div[data-testid="metric-container"], .stForm, div[data-testid="stExpander"] {{
        background-color: #ffffff !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 12px !important;
        padding: 15px !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }}
    
    /* Títulos de sección AZUL PIZARRA */
    .section-header {{
        border-bottom: 2px solid {COLOR_PRIMARIO};
        padding-bottom: 5px;
        margin: 25px 0 15px 0;
        font-weight: 900;
        font-size: 1.1rem;
        color: {COLOR_PRIMARIO} !important;
        text-transform: uppercase;
    }}
    
    /* Tablas estilo Excel */
    .stDataFrame {{ border: 1px solid #cbd5e1 !important; border-radius: 8px; }}
    </style>
""", unsafe_allow_html=True)


# ==========================================
# 5. GESTOR DE PARTIDAS (PORTAFOLIO EN CAJAS BLANCAS ORDENADAS)
# ==========================================
if st.session_state['partida_actual'] is None:
    
    col_izq, col_centro, col_der = st.columns([1, 3, 1])
    
    with col_centro:
        st.markdown(f"""
            <div style="background-color: #ffffff; padding: 20px 25px; border-radius: 8px; border-left: 8px solid {COLOR_PRIMARIO}; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 25px; border-top: 1px solid #e2e8f0; border-right: 1px solid #e2e8f0; border-bottom: 1px solid #e2e8f0;">
                <h1 style="color: {COLOR_TEXTO} !important; margin: 0; font-size: 1.8rem; font-weight: 900; display: flex; align-items: center; gap: 10px;">
                    🗃️ PORTAFOLIO DE PROYECTOS
                </h1>
                <p style="color: #475569 !important; margin: 5px 0 0 45px; font-size: 0.95rem;">Gestión centralizada de expedientes de obra.</p>
            </div>
        """, unsafe_allow_html=True)
        
        col_p1, col_p2 = st.columns(2)
        
        with col_p1:
            try: box_abrir = st.container(border=True)
            except TypeError: box_abrir = st.container()
            
            with box_abrir:
                st.markdown(f"<div style='border-top: 4px solid {COLOR_PRIMARIO}; padding-top: 10px; margin-bottom: 15px;'><h4 style='color:{COLOR_PRIMARIO} !important; margin:0; font-size:1.1rem; font-weight:800;'>📂 ABRIR PARTIDA EXISTENTE</h4></div>", unsafe_allow_html=True)
                
                partida_seleccionada = st.selectbox("Seleccionar partida:", st.session_state['lista_partidas'])
                
                c.execute("SELECT total FROM presupuestos WHERE partida=?", (partida_seleccionada,))
                res_p = c.fetchone()
                presup_actual_gestion = float(res_p[0]) if res_p and res_p[0] is not None else 0.0
                    
                def auto_guardar_presup_existente():
                    nuevo_val = st.session_state[f"edit_gestor_{partida_seleccionada}"]
                    guardar_presupuesto_bd(partida_seleccionada, "Ingreso Directo del Total", nuevo_val, 0.0, 0.0)

                c1, c2 = st.columns([1.2, 1])
                with c1: 
                    nuevo_presupuesto_edicion = st.number_input("Presupuesto Asignado (S/):", value=presup_actual_gestion, step=500.0, key=f"edit_gestor_{partida_seleccionada}", on_change=auto_guardar_presup_existente)
                
                st.write("") 
                if st.button("Ingresar ➡️"):
                    if partida_seleccionada:
                        guardar_presupuesto_bd(partida_seleccionada, "Ingreso Directo del Total", nuevo_presupuesto_edicion, 0.0, 0.0)
                        st.session_state['partida_actual'] = partida_seleccionada
                        st.rerun()
                
        with col_p2:
            try: box_crear = st.container(border=True)
            except TypeError: box_crear = st.container()
            
            with box_crear:
                st.markdown(f"<div style='border-top: 4px solid {COLOR_PRIMARIO}; padding-top: 10px; margin-bottom: 15px;'><h4 style='color:{COLOR_PRIMARIO} !important; margin:0; font-size:1.1rem; font-weight:800;'>➕ CREAR NUEVA PARTIDA</h4></div>", unsafe_allow_html=True)
                
                nueva_partida = st.text_input("Nombre de la nueva partida:")
                
                c3, c4 = st.columns([1.2, 1])
                with c3: 
                    presupuesto_inicial_crear = st.number_input("Presupuesto Inicial (S/):", min_value=0.0, value=0.0, step=500.0, key="nuevo_presup_creacion")
                
                st.write("") 
                if st.button("Crear ⚡"):
                    if nueva_partida.strip():
                        if nueva_partida not in st.session_state['lista_partidas']:
                            st.session_state['lista_partidas'].append(nueva_partida)
                        guardar_presupuesto_bd(nueva_partida, "Ingreso Directo del Total", presupuesto_inicial_crear, 0.0, 0.0)
                        st.session_state['partida_actual'] = nueva_partida
                        st.rerun()
                    else: st.error("Ingrese nombre válido.")
                    
        st.markdown("<div class='section-header' style='margin-top:40px;'>⚙️ ADMINISTRADOR DE EXPEDIENTES</div>", unsafe_allow_html=True)
        
        if st.session_state['lista_partidas']:
            datos_admin = []
            for p in st.session_state['lista_partidas']:
                c.execute("SELECT total, fecha_creacion FROM presupuestos WHERE partida=?", (p,))
                row_pres = c.fetchone()
                presupuesto_val = float(row_pres[0]) if (row_pres and row_pres[0] is not None) else 0.0
                fecha_creacion = row_pres[1] if (row_pres and len(row_pres) > 1 and row_pres[1]) else str(date.today())
                c.execute("SELECT COUNT(*) FROM personal WHERE partida=?", (p,))
                cant_personal = int(c.fetchone()[0])
                datos_admin.append({"Partida Original": p, "Fecha Creación": fecha_creacion, "Personal Reg.": cant_personal, "Presupuesto (S/)": presupuesto_val, "Nuevo Nombre": p, "Eliminar": False})
                
            df_editado = st.data_editor(pd.DataFrame(datos_admin), hide_index=True, use_container_width=True, disabled=["Partida Original", "Fecha Creación", "Personal Reg.", "Presupuesto (S/)"], column_config={"Partida Original": st.column_config.TextColumn("Código de Partida"), "Nuevo Nombre": st.column_config.TextColumn("✏️ Renombrar"), "Eliminar": st.column_config.CheckboxColumn("🗑️ Borrar", default=False)}, key="tabla_admin_partidas")
            
            if st.button("Guardar cambios"):
                cambios = False
                for i, row in df_editado.iterrows():
                    v_nom = row["Partida Original"]; n_nom = str(row["Nuevo Nombre"]).strip(); borrar = row["Eliminar"]
                    if borrar:
                        c.execute("DELETE FROM presupuestos WHERE partida=?", (v_nom,)); c.execute("DELETE FROM materiales WHERE partida=?", (v_nom,)); c.execute("DELETE FROM personal WHERE partida=?", (v_nom,)); c.execute("DELETE FROM asistencia WHERE partida=?", (v_nom,))
                        cambios = True
                    elif n_nom and n_nom != v_nom:
                        c.execute("SELECT 1 FROM presupuestos WHERE partida=?", (n_nom,))
                        if not c.fetchone():
                            c.execute("UPDATE presupuestos SET partida=? WHERE partida=?", (n_nom, v_nom)); c.execute("UPDATE materiales SET partida=? WHERE partida=?", (n_nom, v_nom)); c.execute("UPDATE personal SET partida=? WHERE partida=?", (n_nom, v_nom)); c.execute("UPDATE asistencia SET partida=? WHERE partida=?", (n_nom, v_nom))
                            cambios = True
                if cambios:
                    conn.commit()
                    c.execute("SELECT DISTINCT partida FROM presupuestos")
                    st.session_state['lista_partidas'] = [r[0] for r in c.fetchall() if r[0] and str(r[0]).strip() != ""]
                    st.rerun()

        st.write("---")
        if os.path.exists('obra_nexus.db'):
            with open("obra_nexus.db", "rb") as file:
                st.download_button(label="Descargar Base de Datos (.db)", data=file, file_name="proyecto_nexus.db", mime="application/octet-stream")
    st.stop()

# ==========================================
# 6. MÓDULO DE TRABAJO (DENTRO DE LA PARTIDA)
# ==========================================
st.markdown(f"""
    <div style="background-color: #ffffff; border-left: 6px solid {COLOR_PRIMARIO}; padding: 12px 20px; border-radius: 6px; border-top: 1px solid #cbd5e1; border-right: 1px solid #cbd5e1; border-bottom: 1px solid #cbd5e1; display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
        <h2 style="color: {COLOR_PRIMARIO} !important; margin: 0; font-size: 1.4rem; font-weight:900; text-transform:uppercase;">MÓDULO ACTIVO: {st.session_state['partida_actual']}</h2>
    </div>
""", unsafe_allow_html=True)

if st.button("← Volver al portafolio"):
    st.session_state['partida_actual'] = None
    st.rerun()

try: c.execute("SELECT total FROM presupuestos WHERE partida=?", (st.session_state['partida_actual'],)); row_presupuesto = c.fetchone()
except: row_presupuesto = None

presupuesto_actual_total = float(row_presupuesto[0]) if row_presupuesto and row_presupuesto[0] is not None else 0.0

# ==========================================
# RECOLECCIÓN DE DATOS Y CÁLCULOS GLOBALES
# ==========================================
df_pers_actual = pd.read_sql(f"SELECT * FROM personal WHERE partida='{st.session_state['partida_actual']}'", conn)
if 'jornal' not in df_pers_actual.columns: df_pers_actual['jornal'] = 120.0
if 'almuerzo_costo' not in df_pers_actual.columns: df_pers_actual['almuerzo_costo'] = 7.0
if 'especialidad' not in df_pers_actual.columns: df_pers_actual['especialidad'] = 'Obrero'
lista_trabajadores_db = df_pers_actual['nombre'].tolist() if not df_pers_actual.empty else []

df_mat_db = pd.read_sql(f"SELECT * FROM materiales WHERE partida='{st.session_state['partida_actual']}' ORDER BY fecha DESC", conn)
if 'descuento' not in df_mat_db.columns: df_mat_db['descuento'] = 0.0
if 'und' not in df_mat_db.columns: df_mat_db['und'] = "und"
if not df_mat_db.empty: 
    df_mat_db['fecha_dt'] = pd.to_datetime(df_mat_db['fecha'], errors='coerce').dt.date
    df_mat_db['cantidad'] = pd.to_numeric(df_mat_db['cantidad'], errors='coerce').fillna(0.0)
    df_mat_db['precio'] = pd.to_numeric(df_mat_db['precio'], errors='coerce').fillna(0.0)
    df_mat_db['descuento'] = pd.to_numeric(df_mat_db['descuento'], errors='coerce').fillna(0.0)
else:
    df_mat_db['fecha_dt'] = pd.Series(dtype='object'); df_mat_db['cantidad'] = pd.Series(dtype='float64'); df_mat_db['precio'] = pd.Series(dtype='float64'); df_mat_db['descuento'] = pd.Series(dtype='float64')

df_asist_db = pd.read_sql(f"SELECT * FROM asistencia WHERE partida='{st.session_state['partida_actual']}' ORDER BY fecha DESC", conn)
if 'actividad' not in df_asist_db.columns: df_asist_db['actividad'] = ""
if not df_asist_db.empty: df_asist_db['fecha_dt'] = pd.to_datetime(df_asist_db['fecha'], errors='coerce').dt.date
else: df_asist_db['fecha_dt'] = pd.Series(dtype='object')

trabajadores_registrados = lista_trabajadores_db
todas_las_fechas = []
if not df_mat_db.empty: todas_las_fechas.extend(df_mat_db['fecha_dt'].dropna().tolist())
if not df_asist_db.empty: todas_las_fechas.extend(df_asist_db['fecha_dt'].dropna().tolist())

min_fecha_obra = min(todas_las_fechas) if todas_las_fechas else date.today()
max_fecha_obra = max(todas_las_fechas) if todas_las_fechas else date.today()

start_current_week_res = min_fecha_obra - timedelta(days=min_fecha_obra.weekday())
datos_resumen_semanas = []; gasto_acum_temp = 0.0; semana_contador = 1

while start_current_week_res <= max_fecha_obra + timedelta(days=7):
    end_current_week_res = start_current_week_res + timedelta(days=5) 
    mo_sem = 0.0
    if not df_asist_db.empty:
        mask_w = (df_asist_db['fecha_dt'] >= start_current_week_res) & (df_asist_db['fecha_dt'] <= end_current_week_res) & (df_asist_db['partida'] == st.session_state['partida_actual'])
        df_w_asist = df_asist_db.loc[mask_w]
        for trab in trabajadores_registrados:
            df_tw = df_w_asist[df_w_asist['trabajador'] == trab]
            c_comp = len(df_tw[df_tw['estado'] == 'Día Completo'])
            c_med = len(df_tw[df_tw['estado'] == 'Medio Día'])
            c_alm = len(df_tw[df_tw['almuerzo'].str.startswith('Sale', na=False)])
            
            df_esp = df_pers_actual[df_pers_actual['nombre'] == trab]
            jornal_val = float(df_esp['jornal'].values[0]) if not df_esp.empty and pd.notna(df_esp['jornal'].values[0]) else 120.0
            alm_val = float(df_esp['almuerzo_costo'].values[0]) if not df_esp.empty and pd.notna(df_esp['almuerzo_costo'].values[0]) else 7.0
            
            mo_sem += (c_comp * jornal_val) + (c_med * (jornal_val / 2.0)) + (c_alm * alm_val)

    mat_sem = 0.0
    if not df_mat_db.empty:
        mask_m = (df_mat_db['fecha_dt'] >= start_current_week_res) & (df_mat_db['fecha_dt'] <= end_current_week_res) & (df_mat_db['partida'] == st.session_state['partida_actual'])
        df_w_mat = df_mat_db.loc[mask_m].copy()
        df_w_mat['parcial_calc'] = df_w_mat['cantidad'] * df_w_mat['precio'] * (1 - (df_w_mat['descuento'] / 100.0))
        mat_sem = df_w_mat['parcial_calc'].sum()

    total_sem = round(mo_sem + mat_sem, 2)
    gasto_acum_temp = round(gasto_acum_temp + total_sem, 2)
    saldo_s = round(presupuesto_actual_total - gasto_acum_temp, 2)
    mes_num = start_current_week_res.month

    datos_resumen_semanas.append({
        "Mes": meses_espanol[mes_num] if mes_num < len(meses_espanol) else "", "Semana": f"Semana {semana_contador}",
        "Rango (Lunes a Sábado)": f"{start_current_week_res.strftime('%d/%m/%Y')} al {end_current_week_res.strftime('%d/%m/%Y')}",
        "Gasto Mano Obra (S/)": round(mo_sem, 2), "Gasto Materiales (S/)": round(mat_sem, 2),
        "Gasto Total Semanal (S/)": total_sem, "Gasto Acumulado (S/)": gasto_acum_temp, "Saldo vs Presupuesto (S/)": saldo_s
    })
    semana_contador += 1; start_current_week_res += timedelta(days=7)

df_resumen_final = pd.DataFrame(datos_resumen_semanas)
gasto_mo_real_total = round(df_resumen_final["Gasto Mano Obra (S/)"].sum(), 2) if not df_resumen_final.empty else 0.0
gasto_mat_real_total = round(df_resumen_final["Gasto Materiales (S/)"].sum(), 2) if not df_resumen_final.empty else 0.0
gasto_total_acumulado = round(df_resumen_final["Gasto Acumulado (S/)"].iloc[-1], 2) if not df_resumen_final.empty else 0.0

# ==========================================
# 7. GRÁFICOS DINÁMICOS
# ==========================================
st.markdown("<div class='section-header'>📊 DASHBOARD FINANCIERO</div>", unsafe_allow_html=True)
col_graf_circulo, col_graf_linea = st.columns([1, 1.5])

with col_graf_circulo:
    labels = ['Materiales', 'Mano de Obra', 'Saldo Disponible']
    values = [gasto_mat_real_total, gasto_mo_real_total, max(0, presupuesto_actual_total - (gasto_mat_real_total + gasto_mo_real_total))] 
    
    colores_dona = [COLOR_DONA_1, COLOR_DONA_2, COLOR_DONA_3] 
    
    if sum(values) == 0: values = [0.0001, 0.0001, max(1.0, presupuesto_actual_total)]
    fig_dona = go.Figure(data=[go.Pie(labels=labels, values=values, marker_colors=colores_dona, hole=0.5)])
    fig_dona.update_layout(title=dict(text="Distribución de Costos", font=dict(color=COLOR_PRIMARIO, size=14, weight='bold')), paper_bgcolor="#ffffff", plot_bgcolor="#ffffff", margin=dict(t=40, b=10, l=0, r=0), legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5))
    
    fig_dona.update_traces(textfont=dict(color='white', size=14, weight='bold'), marker=dict(line=dict(color='#ffffff', width=4)))
    st.plotly_chart(fig_dona, use_container_width=True)

with col_graf_linea:
    semanas_graf = df_resumen_final['Semana'].tolist() if not df_resumen_final.empty else ['Sem 1']
    pres_total_linea = [presupuesto_actual_total] * len(semanas_graf)
    gasto_acumulado_graf = df_resumen_final['Gasto Acumulado (S/)'].tolist() if not df_resumen_final.empty else [0]
    fig_linea = go.Figure()
    fig_linea.add_trace(go.Scatter(x=semanas_graf, y=pres_total_linea, mode='lines', name='Presupuesto', line=dict(color=COLOR_DONA_3, dash='dash', width=2)))
    fig_linea.add_trace(go.Scatter(x=semanas_graf, y=gasto_acumulado_graf, mode='lines+markers', name='Ejecutado', line=dict(color=COLOR_DONA_1, width=3)))
    fig_linea.update_layout(title=dict(text="Curva Presupuesto vs Gasto", font=dict(color=COLOR_PRIMARIO, size=14, weight='bold')), paper_bgcolor="#ffffff", plot_bgcolor="#ffffff", margin=dict(t=40, b=10, l=10, r=10), legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5), xaxis=dict(gridcolor="#e2e8f0"), yaxis=dict(tickprefix="S/ ", gridcolor="#e2e8f0"))
    st.plotly_chart(fig_linea, use_container_width=True)

# ==========================================
# 8. CENTRO DE REGISTRO
# ==========================================
st.markdown("<div class='section-header'>📝 CONSOLA DE DATOS</div>", unsafe_allow_html=True)
tab_mat, tab_pers, tab_mo = st.tabs(["📦 Ingreso Materiales", "👤 Alta Personal", "👷 Control Asistencia"])

with tab_mat:
    with st.form("form_materiales"):
        f_mat = st.date_input("Fecha", date.today(), key="f1")
        mat_nom = st.text_input("Descripción Insumo")
        tipo_und = st.selectbox("Unidad", ["bol (Bolsas)", "caja (Cajas)", "m3 (Metro cúbico)", "m2 (Metro cuadrado)", "kg (Kilogramo)", "und (Unidad)", "gln (Galón)", "glb (Global)", "pza (Pieza)", "ml (Metro lineal)", "Otra unidad..."])
        und_final = tipo_und.split(" ")[0] if tipo_und != "Otra unidad..." else st.text_input("Especifique su unidad:")
        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1: cant = st.number_input("Cantidad", min_value=0.01, value=1.0)
        with col_m2: pre = st.number_input("Precio U. (S/)", min_value=0.0)
        with col_m3: desc = st.number_input("Desc. (%)", min_value=0.0, max_value=100.0, value=0.0, step=0.01)
        
        col_mb1, col_mb2 = st.columns(2)
        with col_mb1: btn_guardar_mat = st.form_submit_button("Guardar Ingreso")
        with col_mb2: btn_limpiar_mat = st.form_submit_button("Limpiar Registros")

        if btn_guardar_mat and mat_nom and und_final:
            c.execute("INSERT INTO materiales (partida, fecha, insumo, und, cantidad, precio, descuento) VALUES (?, ?, ?, ?, ?, ?, ?)", (st.session_state['partida_actual'], str(f_mat), mat_nom, und_final, cant, pre, desc))
            conn.commit(); st.rerun()

    df_mat_edit_show = pd.DataFrame(columns=["fecha", "insumo", "und", "cantidad", "precio", "descuento"])
    if not df_mat_db.empty:
        df_mat_edit_show = df_mat_db[['fecha', 'insumo', 'und', 'cantidad', 'precio', 'descuento']].copy()
        df_mat_edit_show['fecha'] = pd.to_datetime(df_mat_edit_show['fecha'], errors='coerce').dt.date

    df_mat_editado = st.data_editor(
        df_mat_edit_show, num_rows="dynamic", use_container_width=True, hide_index=True, key=f"editor_tabla_materiales_{st.session_state['partida_actual']}",
        column_config={"fecha": st.column_config.DateColumn("Fecha", format="DD/MM/YYYY"), "insumo": st.column_config.TextColumn("Insumo"), "und": st.column_config.TextColumn("U.M."), "cantidad": st.column_config.NumberColumn("Cant.", format="%.2f"), "precio": st.column_config.NumberColumn("Precio", format="S/ %.2f"), "descuento": st.column_config.NumberColumn("Desc.%", format="%.2f")}
    )
    if st.button("Actualizar Tabla"):
        c.execute("DELETE FROM materiales WHERE partida=?", (st.session_state['partida_actual'],))
        for _, row in df_mat_editado.iterrows():
            if pd.notna(row["insumo"]) and str(row["insumo"]).strip() != "":
                try: c.execute("INSERT INTO materiales (partida, fecha, insumo, und, cantidad, precio, descuento) VALUES (?, ?, ?, ?, ?, ?, ?)", (st.session_state['partida_actual'], str(row["fecha"]).strip() if pd.notna(row["fecha"]) else str(date.today()), str(row["insumo"]).strip(), str(row["und"]).strip() if pd.notna(row["und"]) else "und", float(row["cantidad"]) if pd.notna(row["cantidad"]) else 1.0, float(row["precio"]) if pd.notna(row["precio"]) else 0.0, float(row["descuento"]) if "descuento" in row and pd.notna(row["descuento"]) else 0.0))
                except: pass
        conn.commit()
        st.success("Actualizado.")
        st.rerun()

with tab_pers:
    with st.form("form_nuevo_personal"):
        col_np1, col_np2 = st.columns(2)
        with col_np1: nuevo_nombre = st.text_input("Nombres y Apellidos")
        with col_np2: nueva_esp = st.selectbox("Especialidad", ["Operario", "Enchapador", "Oficial", "Ayudante / Peón", "Pintor", "Electricista", "Plomero"])
        col_np3, col_np4 = st.columns(2)
        with col_np3: def_jornal = st.number_input("Jornal (S/)", value=120.0, step=10.0)
        with col_np4: def_alm = st.number_input("Almuerzo (S/)", value=7.0, step=1.0)
        if st.form_submit_button("Registrar Personal"):
            if nuevo_nombre:
                try: c.execute("INSERT INTO personal (partida, nombre, especialidad, jornal, almuerzo_costo) VALUES (?, ?, ?, ?, ?)", (st.session_state['partida_actual'], nuevo_nombre.strip(), nueva_esp, def_jornal, def_alm)); conn.commit(); st.rerun()
                except: st.warning("Ya existe.")

    df_pers_edit_show = pd.DataFrame(columns=["nombre", "especialidad", "jornal", "almuerzo_costo"])
    if not df_pers_actual.empty:
        df_pers_edit_show = df_pers_actual[['nombre', 'especialidad', 'jornal', 'almuerzo_costo']].copy()
        df_pers_edit_show['jornal'] = pd.to_numeric(df_pers_edit_show['jornal'], errors='coerce').fillna(0.0)
        df_pers_edit_show['almuerzo_costo'] = pd.to_numeric(df_pers_edit_show['almuerzo_costo'], errors='coerce').fillna(0.0)

    df_pers_editado = st.data_editor(
        df_pers_edit_show, num_rows="dynamic", use_container_width=True, hide_index=True, key=f"editor_tabla_personal_{st.session_state['partida_actual']}",
        column_config={"nombre": st.column_config.TextColumn("Trabajador"), "especialidad": st.column_config.TextColumn("Categoría"), "jornal": st.column_config.NumberColumn("Jornal", format="S/ %.2f"), "almuerzo_costo": st.column_config.NumberColumn("Almuerzo", format="S/ %.2f")}
    )
    if st.button("Actualizar Padrón"):
        c.execute("DELETE FROM personal WHERE partida=?", (st.session_state['partida_actual'],))
        for _, row in df_pers_editado.iterrows():
            if row["nombre"] and str(row["nombre"]).strip() != "":
                try: c.execute("INSERT INTO personal (partida, nombre, especialidad, jornal, almuerzo_costo) VALUES (?, ?, ?, ?, ?)", (st.session_state['partida_actual'], row["nombre"].strip(), row["especialidad"], float(row["jornal"]) if pd.notna(row["jornal"]) else 120.0, float(row["almuerzo_costo"]) if pd.notna(row["almuerzo_costo"]) else 7.0))
                except: pass
        conn.commit(); st.success("Actualizado."); st.rerun()

with tab_mo:
    with st.form("form_mano_obra"):
        f_mo = st.date_input("Fecha", date.today(), key="f2")
        trabajador = st.selectbox("Personal", lista_trabajadores_db) if lista_trabajadores_db else st.text_input("Nombre")
        estado_asis = st.selectbox("Asistencia", ["Día Completo", "Medio Día", "Falta / Emergencia"])
        almuerzo_opc = st.radio("Almuerzo", ["Almuerza en obra / con comida de obra - S/ 0 extra", "Sale a comer afuera - S/ 7 extra"], horizontal=True)
        actividad = st.text_area("Actividad")
        col_fb1, col_fb2 = st.columns(2)
        with col_fb1: btn_guardar = st.form_submit_button("Guardar Asistencia")
        with col_fb2: btn_limpiar_dia = st.form_submit_button("Borrar Día")

        if btn_guardar and trabajador:
            c.execute("INSERT OR REPLACE INTO asistencia (partida, trabajador, fecha, estado, almuerzo, actividad) VALUES (?, ?, ?, ?, ?, ?)", (st.session_state['partida_actual'], trabajador, str(f_mo), estado_asis, almuerzo_opc, actividad)); conn.commit(); st.rerun()

    df_asist_edit_show = pd.DataFrame(columns=["fecha", "trabajador", "estado", "almuerzo", "actividad"])
    if not df_asist_db.empty:
        df_asist_edit_show = df_asist_db[['fecha', 'trabajador', 'estado', 'almuerzo', 'actividad']].copy()
        df_asist_edit_show['fecha'] = pd.to_datetime(df_asist_edit_show['fecha'], errors='coerce').dt.date

    df_asist_editado = st.data_editor(
        df_asist_edit_show, num_rows="dynamic", use_container_width=True, hide_index=True, key=f"editor_tabla_asistencia_{st.session_state['partida_actual']}",
        column_config={"fecha": st.column_config.DateColumn("Fecha", format="DD/MM/YYYY"), "trabajador": st.column_config.SelectboxColumn("Personal", options=lista_trabajadores_db if lista_trabajadores_db else ["Sin registrar"]), "estado": st.column_config.SelectboxColumn("Estado", options=["Día Completo", "Medio Día", "Falta / Emergencia"]), "almuerzo": st.column_config.SelectboxColumn("Almuerzo", options=["Almuerza en obra / con comida de obra - S/ 0 extra", "Sale a comer afuera - S/ 7 extra"]), "actividad": st.column_config.TextColumn("Nota")}
    )
    if st.button("Actualizar Asistencia"):
        c.execute("DELETE FROM asistencia WHERE partida=?", (st.session_state['partida_actual'],))
        for _, row in df_asist_editado.iterrows():
            if pd.notna(row["trabajador"]) and str(row["trabajador"]).strip() != "":
                try: c.execute("INSERT INTO asistencia (partida, trabajador, fecha, estado, almuerzo, actividad) VALUES (?, ?, ?, ?, ?, ?)", (st.session_state['partida_actual'], str(row["trabajador"]), str(row["fecha"]).strip() if pd.notna(row["fecha"]) else str(date.today()), str(row["estado"]) if pd.notna(row["estado"]) else "Día Completo", str(row["almuerzo"]) if pd.notna(row["almuerzo"]) else "Almuerza en obra / con comida de obra - S/ 0 extra", str(row["actividad"]) if pd.notna(row["actividad"]) else ""))
                except: pass
        conn.commit(); st.success("Actualizado."); st.rerun()

# ==========================================
# 9. ALMANAQUE
# ==========================================
st.markdown("<div class='section-header'>📅 CALENDARIO DE ASISTENCIA</div>", unsafe_allow_html=True)
col_btn1, col_tit, col_btn2 = st.columns([1, 2, 1])
with col_btn1:
    if st.button("◀ Mes Anterior"):
        if st.session_state['cal_mes'] == 1: st.session_state['cal_mes'] = 12; st.session_state['cal_ano'] -= 1
        else: st.session_state['cal_mes'] -= 1
        st.rerun()
with col_tit: st.markdown(f"<h3 style='text-align: center; font-weight:900; color:{COLOR_PRIMARIO} !important; margin:0;'>{meses_espanol[st.session_state['cal_mes']]} {st.session_state['cal_ano']}</h3>", unsafe_allow_html=True)
with col_btn2:
    if st.button("Mes Siguiente ▶"):
        if st.session_state['cal_mes'] == 12: st.session_state['cal_mes'] = 1; st.session_state['cal_ano'] += 1
        else: st.session_state['cal_mes'] += 1
        st.rerun()

trabajador_seleccionado = st.selectbox("Filtro Personal:", trabajadores_registrados if trabajadores_registrados else ["Sin registros"])
col_cal, col_leyenda = st.columns([2.5, 1])

with col_cal:
    calendar.setfirstweekday(calendar.SUNDAY)
    mes_cal = calendar.monthcalendar(st.session_state['cal_ano'], st.session_state['cal_mes'])
    asistencia_trabajador = {}; comentarios_trabajador = {}
    if not df_asist_db.empty and trabajador_seleccionado != "Sin registros":
        df_t = df_asist_db[(df_asist_db['trabajador'] == trabajador_seleccionado)]
        for _, row in df_t.iterrows():
            try:
                f_reg = date.fromisoformat(str(row['fecha_dt']))
                if f_reg.year == st.session_state['cal_ano'] and f_reg.month == st.session_state['cal_mes']:
                    asistencia_trabajador[f_reg.day] = row['estado']
                    comentarios_trabajador[f_reg.day] = row['actividad'] if row['actividad'] else "Sin observaciones"
            except: pass

    html_cal = f"""
    <style>
    .cal-table {{ width: 100%; border-collapse: collapse; text-align: center; background: #fff; border: 1px solid #cbd5e1; border-radius:4px; }}
    .cal-table th {{ padding: 10px; background: #f8fafc; color: {COLOR_TEXTO}; border-bottom: 2px solid #cbd5e1; font-weight:900; font-size:0.9rem; }}
    .cal-table td {{ padding: 15px; border: 1px solid #e2e8f0; font-weight: 800; color: #000; font-size:1.1rem; }}
    .cal-vacio {{ background-color: #f1f5f9; color: transparent !important; border:none; }}
    .cal-futuro {{ color: #94a3b8 !important; }}
    .cal-verde {{ background-color: {COLOR_DONA_3}; color: white !important; border: 1px solid #000 !important; }}
    .cal-amarillo {{ background-color: {COLOR_AMARILLO}; color: black !important; border: 1px solid #000 !important; }}
    .cal-rojo {{ background-color: #ef4444; color: white !important; border: 1px solid #000 !important; }}
    </style>
    <table class="cal-table"><tr><th>DOM</th><th>LUN</th><th>MAR</th><th>MIE</th><th>JUE</th><th>VIE</th><th>SAB</th></tr>
    """
    for semana in mes_cal:
        html_cal += "<tr>"
        for dia in semana:
            if dia == 0: html_cal += "<td class='cal-vacio'>0</td>"
            else:
                clase = "cal-futuro"; tooltip = "Sin registro"
                if dia in asistencia_trabajador:
                    est = asistencia_trabajador[dia]
                    tooltip = f"Actividad: {comentarios_trabajador.get(dia, '')}"
                    if "Completo" in est: clase = "cal-verde"
                    elif "Medio" in est: clase = "cal-amarillo"
                    else: clase = "cal-rojo"
                html_cal += f"<td class='{clase}' title='{tooltip}'>{dia}</td>"
        html_cal += "</tr>"
    html_cal += "</table>"
    st.markdown(html_cal, unsafe_allow_html=True)

with col_leyenda:
    st.markdown(f"""
        <div style="background-color: #ffffff; padding: 20px; border-radius: 8px; border: 1px solid #cbd5e1; height: 100%;">
            <h4 style="margin-top:0; border-bottom:2px solid {COLOR_PRIMARIO}; padding-bottom:5px; color:{COLOR_PRIMARIO}; font-weight:900;">LEYENDA</h4>
            <p><span style="display:inline-block; width:15px; height:15px; background:{COLOR_DONA_3}; margin-right:8px; border:1px solid #000;"></span> <b>Día Completo</b></p>
            <p><span style="display:inline-block; width:15px; height:15px; background:{COLOR_AMARILLO}; margin-right:8px; border:1px solid #000;"></span> <b>Medio Día</b></p>
            <p><span style="display:inline-block; width:15px; height:15px; background:#ef4444; margin-right:8px; border:1px solid #000;"></span> <b>Inasistencia</b></p>
        </div>
    """, unsafe_allow_html=True)

# ==========================================
# 10. MÓDULOS SEMANALES
# ==========================================
st.markdown("<div class='section-header'>🧾 VALORIZACIONES SEMANALES</div>", unsafe_allow_html=True)
first_day_month_sel = date(st.session_state['cal_ano'], st.session_state['cal_mes'], 1)
if st.session_state['cal_mes'] == 12: last_day_month_sel = date(st.session_state['cal_ano'] + 1, 1, 1) - timedelta(days=1)
else: last_day_month_sel = date(st.session_state['cal_ano'], st.session_state['cal_mes'] + 1, 1) - timedelta(days=1)

start_current_week_sel = first_day_month_sel - timedelta(days=first_day_month_sel.weekday())
semanas_opciones = []; semana_map = {}; idx = 1
while start_current_week_sel <= last_day_month_sel:
    end_current_week_sel = start_current_week_sel + timedelta(days=5)
    label = f"Valorización {idx}: {start_current_week_sel.strftime('%d/%m/%Y')} al {end_current_week_sel.strftime('%d/%m/%Y')}"
    semanas_opciones.append(label); semana_map[label] = (start_current_week_sel, end_current_week_sel)
    idx += 1; start_current_week_sel += timedelta(days=7)

semana_seleccionada = st.selectbox("Seleccione el Periodo:", semanas_opciones)
fecha_inicio, fecha_fin = semana_map[semana_seleccionada]

tab_planilla, tab_materiales = st.tabs(["👷 Planilla de Personal", "📦 Relación de Materiales"])
with tab_planilla:
    gasto_semana_mo = 0
    df_asist_semana = df_asist_db.loc[(df_asist_db['fecha_dt'] >= fecha_inicio) & (df_asist_db['fecha_dt'] <= fecha_fin) & (df_asist_db['partida'] == st.session_state['partida_actual'])] if not df_asist_db.empty else pd.DataFrame()

    for trabajador in trabajadores_registrados:
        df_esp = df_pers_actual[df_pers_actual['nombre'] == trabajador]
        especialidad_trab = df_esp['especialidad'].values[0] if not df_esp.empty else "Obrero"
        jornal_bd_val = float(df_esp['jornal'].values[0]) if not df_esp.empty and pd.notna(df_esp['jornal'].values[0]) else 120.0
        alm_bd_val = float(df_esp['almuerzo_costo'].values[0]) if not df_esp.empty and pd.notna(df_esp['almuerzo_costo'].values[0]) else 7.0

        df_t_sem = df_asist_semana[df_asist_semana['trabajador'] == trabajador] if not df_asist_semana.empty else pd.DataFrame()
        c_comp = len(df_t_sem[df_t_sem['estado'] == 'Día Completo']) if not df_t_sem.empty else 0
        c_med = len(df_t_sem[df_t_sem['estado'] == 'Medio Día']) if not df_t_sem.empty else 0
        c_alm = len(df_t_sem[df_t_sem['almuerzo'].str.startswith('Sale', na=False)]) if not df_t_sem.empty else 0

        with st.expander(f"👷 {especialidad_trab} — {trabajador}", expanded=True):
            col_w1, col_w2, col_w3 = st.columns(3)
            with col_w1:
                jornal_dia = st.number_input("Jornal (S/)", value=jornal_bd_val, step=10.0, key=f"jornal_{trabajador}")
                costo_almuerzo = st.number_input("Almuerzo (S/)", value=alm_bd_val, step=1.0, key=f"alm_costo_{trabajador}")
            with col_w2:
                comentario_nota = st.text_input("Anotaciones", value="", key=f"comentario_{trabajador}")
            with col_w3:
                monto_extra = st.number_input("Ajuste (S/)", value=0.0, step=10.0, key=f"monto_{trabajador}")

            pago_completos = c_comp * jornal_dia; pago_medios = c_med * (jornal_dia / 2.0); total_almuerzos = c_alm * costo_almuerzo
            total_trabajador = pago_completos + pago_medios + total_almuerzos + monto_extra
            gasto_semana_mo += total_trabajador

            st.markdown(f"""
                <table style="width:100%; text-align: left; border-collapse: collapse; margin-top:10px; border:1px solid #cbd5e1;">
                    <tr style='border-bottom: 1px solid #cbd5e1; background:#f8fafc;'><th style='padding:5px; color:{COLOR_PRIMARIO};'>Concepto</th><th style='color:{COLOR_PRIMARIO};'>Cant.</th><th style='color:{COLOR_PRIMARIO};'>Tasa (S/)</th><th style='color:{COLOR_PRIMARIO};'>Parcial (S/)</th></tr>
                    <tr><td style='padding:5px; font-weight:bold;'>Días Completos</td><td><b>{c_comp}</b></td><td><b>{jornal_dia:.2f}</b></td><td><b>{pago_completos:.2f}</b></td></tr>
                    <tr><td style='padding:5px; font-weight:bold;'>Medios Días</td><td><b>{c_med}</b></td><td><b>{jornal_dia/2:.2f}</b></td><td><b>{pago_medios:.2f}</b></td></tr>
                    <tr><td style='padding:5px; font-weight:bold;'>Almuerzos Extra</td><td><b>{c_alm}</b></td><td><b>{costo_almuerzo:.2f}</b></td><td><b>{total_almuerzos:.2f}</b></td></tr>
                    <tr style='background-color:#f1f5f9; border-top:2px solid #cbd5e1;'><td style='padding:8px;'><b>TOTAL PAGO:</b></td><td colspan="3" style='text-align:right;'><h4 style="color: {COLOR_PRIMARIO}; margin: 0; font-weight:900;">S/ {total_trabajador:.2f}</h4></td></tr>
                </table>
            """, unsafe_allow_html=True)

    st.markdown(f"<div style='background-color: #ffffff; padding: 15px; border-radius: 8px; text-align: right; border: 1px solid #cbd5e1; margin-top: 20px;'><h3 style='margin:0; color:{COLOR_PRIMARIO} !important; font-weight:900;'>SUBTOTAL PLANILLA: S/ {gasto_semana_mo:,.2f}</h3></div>", unsafe_allow_html=True)

with tab_materiales:
    df_mat_filtrado = df_mat_db.loc[(df_mat_db['fecha_dt'] >= fecha_inicio) & (df_mat_db['fecha_dt'] <= fecha_fin) & (df_mat_db['partida'] == st.session_state['partida_actual'])].copy() if not df_mat_db.empty else pd.DataFrame()
    if not df_mat_filtrado.empty:
        df_mat_filtrado['Parcial'] = df_mat_filtrado['cantidad'] * df_mat_filtrado['precio'] * (1 - (df_mat_filtrado['descuento'] / 100.0))
        df_mats_show = df_mat_filtrado[['fecha', 'insumo', 'und', 'cantidad', 'precio', 'descuento', 'Parcial']].rename(columns={'fecha':'Fecha', 'insumo':'Descripción', 'und':'Und', 'cantidad':'Cant.', 'precio':'P.U.', 'descuento':'Desc.%', 'Parcial':'Monto (S/)'})
        df_mats_show['Cant.'] = df_mats_show['Cant.'].apply(lambda x: f"{x:.2f}")
        df_mats_show['P.U.'] = df_mats_show['P.U.'].apply(lambda x: f"{x:,.2f}")
        df_mats_show['Monto (S/)'] = df_mats_show['Monto (S/)'].apply(lambda x: f"{x:,.2f}")
    else: df_mats_show = pd.DataFrame(columns=['Fecha', 'Descripción', 'Und', 'Cant.', 'P.U.', 'Desc.%', 'Monto (S/)'])
        
    st.dataframe(df_mats_show, use_container_width=True, hide_index=True)
    gasto_semana_mat = df_mat_filtrado['Parcial'].sum() if not df_mat_filtrado.empty else 0.0
    
    st.markdown(f"<div style='background-color: #ffffff; padding: 15px; border-radius: 8px; text-align: right; border: 1px solid #cbd5e1; margin-top: 10px;'><h3 style='margin:0; color:{COLOR_PRIMARIO} !important; font-weight:900;'>SUBTOTAL MATERIALES: S/ {gasto_semana_mat:,.2f}</h3></div>", unsafe_allow_html=True)

# ==========================================
# 11. TABLA RESUMEN FINANCIERO
# ==========================================
st.markdown("<div class='section-header'>📈 CONSOLIDADO FINANCIERO</div>", unsafe_allow_html=True)
df_resumen_mostrar = df_resumen_final.copy()
if not df_resumen_mostrar.empty:
    df_resumen_mostrar.loc["Total"] = {
        "Mes": "", "Semana": "TOTAL", "Rango (Lunes a Sábado)": "",
        "Gasto Mano Obra (S/)": gasto_mo_real_total, "Gasto Materiales (S/)": gasto_mat_real_total,
        "Gasto Total Semanal (S/)": round(gasto_mo_real_total + gasto_mat_real_total, 2),
        "Gasto Acumulado (S/)": "", "Saldo vs Presupuesto (S/)": ""
    }
    for col in ["Gasto Mano Obra (S/)", "Gasto Materiales (S/)", "Gasto Total Semanal (S/)", "Gasto Acumulado (S/)", "Saldo vs Presupuesto (S/)"]:
        df_resumen_mostrar[col] = df_resumen_mostrar[col].apply(lambda x: f"{x:,.2f}" if isinstance(x, (int, float)) else x)

st.dataframe(df_resumen_mostrar, use_container_width=True, hide_index=True)

saldo_final = round(presupuesto_actual_total - gasto_total_acumulado, 2)
color_saldo = COLOR_DONA_3 if saldo_final >= 0 else "#ef4444"

col_res1, col_res2, col_res3 = st.columns(3)
with col_res1: st.markdown(f"<div style='background:white; padding:20px; border-radius:4px; border:1px solid #cbd5e1; border-top:5px solid #0f172a; text-align:center;'><h4 style='margin:0; color:#475569; font-weight:800;'>Pto. Aprobado</h4><h2 style='margin:10px 0 0 0; color:#0f172a; font-weight:900;'>S/ {presupuesto_actual_total:,.2f}</h2></div>", unsafe_allow_html=True)
with col_res2: st.markdown(f"<div style='background:white; padding:20px; border-radius:4px; border:1px solid #cbd5e1; border-top:5px solid {COLOR_DONA_1}; text-align:center;'><h4 style='margin:0; color:#475569; font-weight:800;'>Costo Real Acumulado</h4><h2 style='margin:10px 0 0 0; color:{COLOR_DONA_1}; font-weight:900;'>S/ {gasto_total_acumulado:,.2f}</h2></div>", unsafe_allow_html=True)
with col_res3: st.markdown(f"<div style='background:white; padding:20px; border-radius:4px; border:1px solid #cbd5e1; border-top:5px solid {color_saldo}; text-align:center;'><h4 style='margin:0; color:#475569; font-weight:800;'>{'Saldo a Favor' if saldo_final>=0 else 'Sobregiro'}</h4><h2 style='margin:10px 0 0 0; color:{color_saldo}; font-weight:900;'>S/ {abs(saldo_final):,.2f}</h2></div>", unsafe_allow_html=True)

# ==========================================
# 12. GENERADOR PDF
# ==========================================
st.markdown("<div class='section-header'>🖨️ EMISIÓN DE EXPEDIENTE (PDF OFICIAL)</div>", unsafe_allow_html=True)
if st.button("GENERAR INFORME PDF"):
    dias_es_map_rep = {0: 'Lunes', 1: 'Martes', 2: 'Miércoles', 3: 'Jueves', 4: 'Viernes', 5: 'Sábado', 6: 'Domingo'}
    fecha_impresion_str = date.today().strftime('%d/%m/%Y')
    
    first_m = date(st.session_state['cal_ano'], st.session_state['cal_mes'], 1)
    if st.session_state['cal_mes'] == 12: last_m = date(st.session_state['cal_ano'] + 1, 1, 1) - timedelta(days=1)
    else: last_m = date(st.session_state['cal_ano'], st.session_state['cal_mes'] + 1, 1) - timedelta(days=1)
    curr_w = first_m - timedelta(days=first_m.weekday())
    semanas_mes_lista = []; idx_s = 1
    while curr_w <= last_m:
        end_w = curr_w + timedelta(days=5); semanas_mes_lista.append((f"Semana {idx_s}", curr_w, end_w)); idx_s += 1; curr_w += timedelta(days=7)

    labels_print = ['Materiales', 'Mano de Obra', 'Saldo Restante']
    values_print = [gasto_mat_real_total, gasto_mo_real_total, max(0, presupuesto_actual_total - (gasto_mat_real_total + gasto_mo_real_total))]
    
    colores_pdf = [COLOR_DONA_1, COLOR_DONA_2, COLOR_DONA_3]
    
    fig_dona_print = go.Figure(data=[go.Pie(labels=labels_print, values=values_print, marker_colors=colores_pdf, hole=0.5)])
    fig_dona_print.update_layout(title=dict(text="Distribución de Costos", font=dict(color="#000", size=13, weight="bold")), paper_bgcolor="white", plot_bgcolor="white", margin=dict(t=30, b=10, l=10, r=10), legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5, font=dict(color="#000", size=9, weight="bold")), width=480, height=280)
    fig_dona_print.update_traces(texttemplate='%{percent}<br>S/ %{value:,.2f}', textposition='inside', textfont=dict(size=10, color='white', weight='bold'), marker=dict(line=dict(color='#ffffff', width=3)))

    semanas_graf_p = df_resumen_final['Semana'].tolist() if not df_resumen_final.empty else ['Sem 1']
    pres_total_linea_p = [presupuesto_actual_total] * len(semanas_graf_p)
    gasto_acumulado_graf_p = df_resumen_final['Gasto Acumulado (S/)'].tolist() if not df_resumen_final.empty else [0]
    
    fig_linea_print = go.Figure()
    fig_linea_print.add_trace(go.Scatter(x=semanas_graf_p, y=pres_total_linea_p, mode='lines', name='Presupuesto Total', line=dict(color=COLOR_DONA_3, dash='dash', width=2)))
    fig_linea_print.add_trace(go.Scatter(x=semanas_graf_p, y=gasto_acumulado_graf_p, mode='lines+markers', name='Gasto Acumulado', line=dict(color=COLOR_DONA_1, width=3)))
    fig_linea_print.update_layout(title=dict(text="Curva Presupuesto vs Gasto Acumulado", font=dict(color="#000", size=13, weight="bold")), paper_bgcolor="white", plot_bgcolor="white", margin=dict(t=30, b=40, l=70, r=20), legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5, font=dict(color="#000", size=9, weight="bold")), font=dict(color="#000", weight="bold"), xaxis=dict(tickangle=0, gridcolor="#e2e8f0", showline=True, linecolor='#000'), yaxis=dict(tickprefix="S/ ", tickformat=",.0f", gridcolor="#e2e8f0", showline=True, linecolor='#000'), width=480, height=280)

    html_dona_str = fig_dona_print.to_html(include_plotlyjs='inline', full_html=False, config={'displayModeBar': False})
    html_linea_str = fig_linea_print.to_html(include_plotlyjs='inline', full_html=False, config={'displayModeBar': False})

    html_reporte = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Informe Técnico - Nexus Obra</title>
        <style>
            @page {{ size: A4; margin: 15mm; }}
            body {{ font-family: 'Segoe UI', Arial, sans-serif; color: #000000; margin: 0; padding: 0; font-size: 8pt; line-height: 1.3; background: #ffffff; }}
            .membrete-table {{ width: 100%; border-collapse: collapse; margin-bottom: 15px; border: 2px solid #000; }}
            .membrete-table td {{ border: 1px solid #000; padding: 8px; vertical-align: top; }}
            .info-table {{ width: 100%; border-collapse: collapse; margin-bottom: 15px; font-size: 8pt; }}
            .info-table td {{ border: 1px solid #000; padding: 5px; }}
            .info-label {{ background-color: #f1f5f9; font-weight: bold; width: 20%; color: {COLOR_PRIMARIO}; }}
            .section-title {{ font-size: 10pt; font-weight: bold; color: {COLOR_PRIMARIO}; margin-top: 15px; margin-bottom: 8px; text-transform: uppercase; }}
            .data-table {{ width: 100%; border-collapse: collapse; margin-bottom: 10px; }}
            .data-table th, .data-table td {{ border: 1px solid #000; padding: 4px; text-align: left; color: #000; font-weight:bold; }}
            .data-table th {{ background: {COLOR_PRIMARIO}; font-weight: 900; text-align: center; color: #ffffff; text-transform: uppercase; }}
            .text-right {{ text-align: right; }} .text-center {{ text-align: center; }}
            .grafico-center {{ text-align: center; margin: 5px auto; page-break-inside: avoid; display: flex; justify-content: center; }}
        </style>
    </head>
    <body>
        <table class="membrete-table">
            <tr>
                <td style="width: 65%; background-color: #f8fafc;">
                    <h1 style="font-size: 14pt; margin: 0; color: {COLOR_PRIMARIO}; font-weight:900;">CONTROL DE OBRAS MINI - AYACUCHO</h1>
                    <h2 style="font-size: 10pt; margin: 5px 0 0 0; color: #000;">INFORME TÉCNICO DE CONTROL PRESUPUESTAL Y MANO DE OBRA</h2>
                </td>
                <td style="width: 35%; font-size: 8pt;">
                    <b>Fecha de Impresión:</b> {fecha_impresion_str}<br>
                    <b>Mes Evaluado:</b> {meses_espanol[st.session_state['cal_mes']]} {st.session_state['cal_ano']}<br>
                    <b>Costo al:</b> {date.today().strftime('%d/%m/%Y')}
                </td>
            </tr>
        </table>
        
        <table class="info-table">
            <tr>
                <td class="info-label">Proyecto / Descripción:</td>
                <td colspan="3">Obras de Construcción Civil y Acabados</td>
            </tr>
            <tr>
                <td class="info-label">Ubicación:</td>
                <td>Distrito Ayacucho, Huamanga</td>
                <td class="info-label">Partida Evaluada:</td>
                <td><b>{st.session_state['partida_actual']}</b></td>
            </tr>
            <tr>
                <td class="info-label">Cliente:</td>
                <td colspan="3">Cliente Principal</td>
            </tr>
        </table>

        <div class="section-title">1. Análisis Financiero y Resumen Global</div>
        <p style="margin: 0 0 10px 0; font-weight:bold;">El presente informe detalla el estado económico de la partida <b>{st.session_state['partida_actual']}</b>. Se ha asignado un presupuesto total de <b>S/ {presupuesto_actual_total:,.2f}</b>, registrando un gasto acumulado de <b>S/ {gasto_total_acumulado:,.2f}</b>. Esto representa un estado financiero de <b>{'SALDO A FAVOR' if saldo_final >= 0 else 'SOBREGIRO'}</b> por un monto de <b>S/ {abs(saldo_final):,.2f}</b>.</p>

        <div class="section-title">2. Análisis Gráfico de Ejecución</div>
        <div class="grafico-center">{html_dona_str}</div>
        <div class="grafico-center">{html_linea_str}</div>

        <div class="section-title">3. Resumen General por Semanas de Trabajo (Lunes a Sábado)</div>
        <table class="data-table">
            <thead>
                <tr>
                    <th>Mes</th><th>Semana</th><th>Rango</th>
                    <th>Mano Obra (S/)</th><th>Materiales (S/)</th><th>Total Semanal (S/)</th><th>Acumulado (S/)</th><th>Saldo (S/)</th>
                </tr>
            </thead>
            <tbody>
    """
    
    for _, row in df_resumen_final.iterrows():
        total_sem_val = float(str(row['Gasto Total Semanal (S/)']).replace(',', ''))
        if total_sem_val > 0:
            html_reporte += f"<tr><td class='text-center'>{row['Mes']}</td><td class='text-center'>{row['Semana']}</td><td class='text-center'>{row['Rango (Lunes a Sábado)']}</td><td class='text-right'>S/ {row['Gasto Mano Obra (S/)']:,.2f}</td><td class='text-right'>S/ {row['Gasto Materiales (S/)']:,.2f}</td><td class='text-right'>S/ {row['Gasto Total Semanal (S/)']:,.2f}</td><td class='text-right'>S/ {row['Gasto Acumulado (S/)']:,.2f}</td><td class='text-right'>S/ {row['Saldo vs Presupuesto (S/)']:,.2f}</td></tr>"
        
    html_reporte += f"<tr style='background-color:#f1f5f9; font-weight:900;'><td colspan='3' class='text-right' style='color:{COLOR_PRIMARIO};'>TOTAL GENERAL:</td><td class='text-right'>S/ {gasto_mo_real_total:,.2f}</td><td class='text-right'>S/ {gasto_mat_real_total:,.2f}</td><td class='text-right'>S/ {gasto_mo_real_total + gasto_mat_real_total:,.2f}</td><td></td><td></td></tr></tbody></table>"

    html_reporte += "<div class='section-title'>4. Detalle de Planilla por Trabajador</div>"
    
    hubo_trabajadores = False
    for _, pers in df_pers_actual.iterrows():
        t_nombre = pers['nombre']; t_esp = pers['especialidad']
        
        # Verificar si el trabajador asistió en el mes actual para mostrarlo
        trabajo_en_mes = False
        if not df_asist_db.empty:
            m_total = (df_asist_db['trabajador'] == t_nombre) & (df_asist_db['fecha_dt'] >= first_m) & (df_asist_db['fecha_dt'] <= last_m) & (df_asist_db['partida'] == st.session_state['partida_actual'])
            if not df_asist_db.loc[m_total].empty:
                trabajo_en_mes = True
                
        if trabajo_en_mes:
            hubo_trabajadores = True
            html_reporte += f"<div style='font-weight:900; margin: 15px 0 5px 0; border-bottom: 1px dashed #000; color:{COLOR_PRIMARIO}; font-size:9pt;'>Obrero: {t_esp} - {t_nombre}</div>"
            
            for s_nombre, s_ini, s_fin in semanas_mes_lista:
                df_t_s = pd.DataFrame()
                if not df_asist_db.empty:
                    m_ts = (df_asist_db['trabajador'] == t_nombre) & (df_asist_db['fecha_dt'] >= s_ini) & (df_asist_db['fecha_dt'] <= s_fin) & (df_asist_db['partida'] == st.session_state['partida_actual'])
                    df_t_s = df_asist_db.loc[m_ts].sort_values('fecha')
                
                # SOLO MOSTRAR SEMANAS DONDE HUBO TRABAJO (No se muestra el texto 'Sin registros')
                if not df_t_s.empty:
                    c_comp = len(df_t_s[df_t_s['estado'] == 'Día Completo'])
                    c_med = len(df_t_s[df_t_s['estado'] == 'Medio Día'])
                    c_alm = len(df_t_s[df_t_s['almuerzo'].str.startswith('Sale', na=False)])
                    jornal_v = float(pers['jornal']) if pd.notna(pers['jornal']) else 120.0; alm_v = float(pers['almuerzo_costo']) if pd.notna(pers['almuerzo_costo']) else 7.0
                    tot_s_trab = (c_comp * jornal_v) + (c_med * (jornal_v / 2.0)) + (c_alm * alm_v)
                    
                    html_reporte += f"<p style='margin: 4px 0 2px 0; font-size: 8pt; font-weight:bold;'>{s_nombre} ({s_ini.strftime('%d/%m/%Y')} al {s_fin.strftime('%d/%m/%Y')}):</p>"
                    html_reporte += "<table class='data-table'><thead><tr><th width='15%'>Fecha</th><th width='15%'>Día</th><th width='25%'>Asistencia</th><th width='45%'>Actividad</th></tr></thead><tbody>"
                    for _, r_as in df_t_s.iterrows():
                        dt_f = date.fromisoformat(str(r_as['fecha']))
                        html_reporte += f"<tr><td class='text-center'>{dt_f.strftime('%d/%m/%Y')}</td><td class='text-center'>{dias_es_map_rep[dt_f.weekday()]}</td><td>{r_as['estado']}</td><td>{r_as['actividad']}</td></tr>"
                    html_reporte += "</tbody></table>"
                    html_reporte += f"<div style='text-align:right; font-size:8.5pt; font-weight:900; margin-bottom:10px;'>Subtotal {s_nombre}: S/ {tot_s_trab:,.2f}</div>"

    if not hubo_trabajadores:
        html_reporte += "<p style='font-size:7.5pt; font-weight:bold;'><i>Sin registros de personal en este mes.</i></p>"

    html_reporte += f"""
        <div class="section-title">5. Control de Materiales e Insumos</div>
        <table class="data-table">
            <thead>
                <tr>
                    <th>Fecha</th><th>Insumo / Material</th><th>UND</th><th>Cantidad</th><th>P. Unitario (S/)</th><th>Desc. (%)</th><th>Parcial (S/)</th>
                </tr>
            </thead>
            <tbody>
    """
    gasto_mat_rep = 0.0
    if not df_mat_db.empty:
        df_mat_rep = df_mat_db.sort_values('fecha')
        for _, r_m in df_mat_rep.iterrows():
            dt_m = date.fromisoformat(str(r_m['fecha']))
            cant_m = float(r_m['cantidad']); prec_m = float(r_m['precio'])
            desc_m = float(r_m['descuento']) if 'descuento' in r_m and pd.notna(r_m['descuento']) else 0.0
            parc_m = cant_m * prec_m * (1 - (desc_m / 100.0)); gasto_mat_rep += parc_m
            html_reporte += f"<tr><td class='text-center'>{dt_m.strftime('%d/%m/%Y')}</td><td>{r_m['insumo']}</td><td class='text-center'>{r_m['und']}</td><td class='text-right'>{cant_m:,.2f}</td><td class='text-right'>S/ {prec_m:,.2f}</td><td class='text-right'>{desc_m:.2f}</td><td class='text-right'>S/ {parc_m:,.2f}</td></tr>"
    if gasto_mat_rep == 0.0: html_reporte += "<tr><td colspan='7' class='text-center'><i>Sin movimientos registrados.</i></td></tr>"
        
    html_reporte += f"""
            </tbody>
        </table>
        <div style='text-align:right; font-weight:900; font-size:9pt; color:{COLOR_PRIMARIO};'>TOTAL MATERIALES MES: S/ {gasto_mat_rep:,.2f}</div>
        <script> setTimeout(function() {{ window.print(); }}, 1500); </script>
    </body>
    </html>
    """
    st.components.v1.html(html_reporte, height=800, scrolling=True)
