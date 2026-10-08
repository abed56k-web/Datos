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

# ==========================================
# CONSTANTES GLOBALES
# ==========================================
meses_espanol = ["", "ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO", "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"]

# 1. CONFIGURACIÓN INICIAL
st.set_page_config(
    page_title="Control de Obra - Nexus", 
    layout="wide", 
    initial_sidebar_state="collapsed",
    menu_items={'Get Help': None, 'Report a bug': None, 'About': "# NEXUS OBRA - Sistema de Control de Proyectos"}
)

st.markdown("""
    <head>
        <link rel="apple-touch-icon" href="https://cdn-icons-png.flaticon.com/512/2954/2954848.png">
        <link rel="icon" href="https://cdn-icons-png.flaticon.com/512/2954/2954848.png">
        <meta name="theme-color" content="#0f172a">
    </head>
""", unsafe_allow_html=True)

# 2. BASE DE DATOS PERMANENTE Y TABLAS
conn = sqlite3.connect('obra_nexus.db', timeout=10.0, check_same_thread=False)
c = conn.cursor()

c.execute('CREATE TABLE IF NOT EXISTS usuarios (email TEXT UNIQUE, password TEXT)')
c.execute('CREATE TABLE IF NOT EXISTS personal (partida TEXT, nombre TEXT, especialidad TEXT, jornal REAL DEFAULT 120.0, almuerzo_costo REAL DEFAULT 7.0, UNIQUE(partida, nombre))')
c.execute('CREATE TABLE IF NOT EXISTS materiales (partida TEXT, fecha TEXT, insumo TEXT, und TEXT, cantidad REAL, precio REAL, descuento REAL DEFAULT 0.0)')
c.execute('CREATE TABLE IF NOT EXISTS asistencia (partida TEXT, trabajador TEXT, fecha TEXT, estado TEXT, almuerzo TEXT, actividad TEXT, UNIQUE(partida, trabajador, fecha))')
c.execute('CREATE TABLE IF NOT EXISTS presupuestos (partida TEXT PRIMARY KEY, modo TEXT, total REAL, materiales REAL, mano_obra REAL)')
conn.commit()

try:
    c.execute('ALTER TABLE personal ADD COLUMN jornal REAL DEFAULT 120.0')
    c.execute('ALTER TABLE personal ADD COLUMN almuerzo_costo REAL DEFAULT 7.0')
    conn.commit()
except sqlite3.OperationalError:
    pass

try:
    c.execute('ALTER TABLE materiales ADD COLUMN und TEXT')
    conn.commit()
except sqlite3.OperationalError:
    pass

try:
    c.execute('ALTER TABLE materiales ADD COLUMN descuento REAL DEFAULT 0.0')
    conn.commit()
except sqlite3.OperationalError:
    pass

try:
    c.execute('ALTER TABLE asistencia ADD COLUMN actividad TEXT')
    conn.commit()
except sqlite3.OperationalError:
    pass

def encriptar_clave(clave): return hashlib.sha256(str.encode(clave)).hexdigest()

def agregar_usuario(email, clave): 
    try:
        c.execute('INSERT INTO usuarios (email, password) VALUES (?, ?)', (email, encriptar_clave(clave)))
        conn.commit()
        return True
    except:
        return False

def verificar_usuario(email, clave):
    c.execute('SELECT * FROM usuarios WHERE email=? AND password=?', (email, encriptar_clave(clave)))
    return c.fetchone() is not None

if 'autenticado' not in st.session_state: st.session_state['autenticado'] = False
if 'mostrar_registro' not in st.session_state: st.session_state['mostrar_registro'] = False
if 'partida_actual' not in st.session_state: st.session_state['partida_actual'] = None
if 'lista_partidas' not in st.session_state: 
    st.session_state['lista_partidas'] = ["Acabados 2do Nivel", "Tarrajeo 3er Nivel"]
if 'cal_mes' not in st.session_state: st.session_state['cal_mes'] = 10 
if 'cal_ano' not in st.session_state: st.session_state['cal_ano'] = 2026

# ==========================================
# 3. PANTALLA DE INICIO (LOGIN)
# ==========================================
if not st.session_state['autenticado']:
    st.markdown("""
        <style>
        .stApp {
            background-image: linear-gradient(rgba(0, 0, 0, 0.4), rgba(0, 0, 0, 0.7)), url("https://images.unsplash.com/photo-1519681393784-d120267933ba?q=80&w=2070&auto=format&fit=crop");
            background-size: cover; background-position: center; background-attachment: fixed;
        }
        h1, h2, h3, p, label, .stCheckbox label { color: white !important; }
        .stTextInput input, .stPasswordInput input { background-color: white !important; color: black !important; border-radius: 5px; }
        div[data-testid="stButton"] button { background-color: #d95b32 !important; color: white !important; border: none !important; font-size: 1.1rem; width: 100%; transition: 0.3s; }
        div[data-testid="stButton"] button:hover { background-color: #b54925 !important; }
        .social-container img { width: 30px; height: 30px; margin-right: 15px; cursor: pointer; filter: brightness(0) invert(1); }
        .social-container img:hover { opacity: 0.8; }
        </style>
    """, unsafe_allow_html=True)

    col1, col_vacia, col2 = st.columns([1.2, 0.2, 1])
    with col1:
        st.markdown("<h1 style='font-size: 5rem; line-height: 1.1; margin-bottom: 0;'>Welcome<br>Back</h1>", unsafe_allow_html=True)
        st.markdown("<p style='font-size: 1.1rem; margin-top: 15px;'>Plataforma integral para el control de avance, materiales y personal de obra en Ayacucho.</p>", unsafe_allow_html=True)
        st.markdown("""
            <div class="social-container" style="margin-top: 25px;">
                <a href="#"><img src="https://cdn-icons-png.flaticon.com/512/20/20673.png" alt="Facebook"></a>
                <a href="#"><img src="https://cdn-icons-png.flaticon.com/512/3046/3046128.png" alt="TikTok"></a>
                <a href="#"><img src="https://cdn-icons-png.flaticon.com/512/1384/1384031.png" alt="Instagram"></a>
                <a href="#"><img src="https://cdn-icons-png.flaticon.com/512/1384/1384028.png" alt="YouTube"></a>
                <a href="#"><img src="https://cdn-icons-png.flaticon.com/512/1384/1384023.png" alt="WhatsApp"></a>
            </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("<h2 style='text-align: center; font-size: 3rem; margin-bottom: 30px;'>Sign in</h2>", unsafe_allow_html=True)
        
        if not st.session_state['mostrar_registro']:
            with st.form("form_login"):
                email_login = st.text_input("Email Address")
                clave_login = st.text_input("Password", type="password")
                st.checkbox("Remember Me")
                btn_login = st.form_submit_button("Sign in now")
                
                if btn_login:
                    if verificar_usuario(email_login, clave_login):
                        st.session_state['autenticado'] = True
                        st.session_state['usuario_actual'] = email_login
                        st.rerun()
                    else:
                        st.error("Error al iniciar sesión. Verifica tus datos o regístrate.")
            
            if st.button("¿No tienes cuenta? Regístrate aquí"):
                st.session_state['mostrar_registro'] = True
                st.rerun()
                
            with st.expander("🛠️ ¿Se reinició el servidor? Restaura tu Base de Datos aquí"):
                archivo_emergencia = st.file_uploader("Sube tu archivo de respaldo (.db)", type=["db"])
                if archivo_emergencia is not None:
                    with open("obra_nexus.db", "wb") as f:
                        f.write(archivo_emergencia.getbuffer())
                    st.success("¡Base de datos restaurada con éxito! Ya puedes iniciar sesión.")
                    st.rerun()
        else:
            with st.form("form_registro"):
                st.markdown("<p style='text-align: center;'><b>Crea tu cuenta de obra</b></p>", unsafe_allow_html=True)
                email_reg = st.text_input("Nuevo Correo")
                clave_reg = st.text_input("Crear Contraseña", type="password")
                btn_reg = st.form_submit_button("Guardar Cuenta")
                
                if btn_reg:
                    if email_reg and clave_reg:
                        if agregar_usuario(email_reg, clave_reg):
                            st.success("¡Cuenta creada con éxito! Vuelve atrás para ingresar.")
                            st.session_state['mostrar_registro'] = False
                            st.rerun()
                        else:
                            st.error("El correo ya está registrado.")
                    else:
                        st.warning("Completa ambos campos.")
            
            if st.button("Volver al Login"):
                st.session_state['mostrar_registro'] = False
                st.rerun()
    st.stop()

# ==========================================
# 4. DISEÑO INTERIOR (Fondo oscuro futurista)
# ==========================================
st.markdown("""
    <style>
    .stApp { background-image: none !important; background-color: #0f172a !important; color: #e2e8f0 !important; }
    h1, h2, h3, p, label, span { color: #e2e8f0 !important; }
    div[data-testid="metric-container"] { background-color: #1e293b; border: 1px solid #38bdf8; padding: 15px; border-radius: 12px; box-shadow: 0 0 10px rgba(56, 189, 248, 0.2); }
    div[data-testid="stButton"] button { background: linear-gradient(90deg, #06b6d4 0%, #3b82f6 100%) !important; color: white !important; border: none !important; border-radius: 8px; font-weight: bold; transition: 0.3s; }
    div[data-testid="stButton"] button:hover { box-shadow: 0 0 15px rgba(6, 182, 212, 0.6); transform: scale(1.02); }
    .stTextInput input, .stNumberInput input, .stSelectbox div, .stTextArea textarea { background-color: #1e293b !important; color: #38bdf8 !important; border: 1px solid #475569; }
    .stForm, .stDataFrame { background-color: #1e293b !important; border: 1px solid #475569 !important; border-radius: 12px; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 5. GESTOR DE PARTIDAS
# ==========================================
if st.session_state['partida_actual'] is None:
    st.markdown("<h1 style='text-align: center; color: #38bdf8 !important;'>🌌 Gestor de Proyectos</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Selecciona en qué área de la obra vas a trabajar hoy.</p>", unsafe_allow_html=True)
    st.write("<br>", unsafe_allow_html=True)
    
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        st.markdown("### 📂 Entrar a Partida Existente")
        partida_seleccionada = st.selectbox("Mis Partidas Activas:", st.session_state['lista_partidas'])
        if st.button("INGRESAR AL PANEL ➡️", use_container_width=True):
            st.session_state['partida_actual'] = partida_seleccionada
            st.rerun()
            
    with col_p2:
        st.markdown("### ➕ Crear Nueva Partida")
        nueva_partida = st.text_input("Nombre de la nueva partida (Ej. Enchapado Baños)")
        if st.button("CREAR Y ENTRAR ⚡", use_container_width=True):
            if nueva_partida:
                st.session_state['lista_partidas'].append(nueva_partida)
                st.session_state['partida_actual'] = nueva_partida
                st.rerun()
            else: st.warning("Escribe un nombre primero.")
    st.stop()

# ==========================================
# 6. DASHBOARD DE LA PARTIDA Y PRESUPUESTO
# ==========================================
col_top1, col_top2 = st.columns([4, 1])
with col_top1:
    st.markdown(f"<h2 style='color: #a855f7 !important;'>📍 Partida: {st.session_state['partida_actual']}</h2>", unsafe_allow_html=True)
with col_top2:
    st.write("") 
    if st.button("⬅️ Volver a Partidas"):
        st.session_state['partida_actual'] = None
        st.rerun()

# Recuperar o inicializar presupuesto en la BD
try:
    c.execute("SELECT modo, total, materiales, mano_obra FROM presupuestos WHERE partida=?", (st.session_state['partida_actual'],))
    row_presupuesto = c.fetchone()
except sqlite3.OperationalError:
    row_presupuesto = None

if row_presupuesto:
    modo_guardado, presupuesto_total_db, presupuesto_mat_db, presupuesto_mo_db = row_presupuesto
else:
    modo_guardado = "Suma Automática (Materiales + Mano de Obra)"
    presupuesto_mat_db, presupuesto_mo_db = 6000.0, 4000.0
    presupuesto_total_db = 10000.0
    c.execute("INSERT OR REPLACE INTO presupuestos VALUES (?, ?, ?, ?, ?)", (st.session_state['partida_actual'], modo_guardado, presupuesto_total_db, presupuesto_mat_db, presupuesto_mo_db))
    conn.commit()

with st.expander("⚙️ Configurar, Renombrar Partida y Respaldo de Base de Datos"):
    nuevo_nombre_partida = st.text_input("Renombrar esta Partida:", value=st.session_state['partida_actual'])
    if st.button("Actualizar Nombre"):
        if nuevo_nombre_partida:
            idx = st.session_state['lista_partidas'].index(st.session_state['partida_actual'])
            st.session_state['lista_partidas'][idx] = nuevo_nombre_partida
            st.session_state['partida_actual'] = nuevo_nombre_partida
            st.success("¡Nombre actualizado con éxito!")
            st.rerun()

    st.write("---")
    if os.path.exists('obra_nexus.db'):
        with open("obra_nexus.db", "rb") as file:
            st.download_button(
                label="📥 Descargar Respaldo de Base de Datos (Seguridad Obra)",
                data=file,
                file_name="obra_nexus_backup.db",
                mime="application/octet-stream"
            )

    st.write("---")
    modo_ingreso = st.radio("Método de cálculo:", ["Suma Automática (Materiales + Mano de Obra)", "Ingreso Directo del Total"], horizontal=True, index=0 if modo_guardado=="Suma Automática (Materiales + Mano de Obra)" else 1)
    
    if modo_ingreso == "Suma Automática (Materiales + Mano de Obra)":
        col_b1, col_b2 = st.columns(2)
        with col_b1:
            try: val_mat = float(presupuesto_mat_db)
            except (ValueError, TypeError): val_mat = 6000.0
            nuevo_mat = st.number_input("Presupuesto Materiales (S/)", value=val_mat, step=500.0)
        with col_b2:
            try: val_mo = float(presupuesto_mo_db)
            except (ValueError, TypeError): val_mo = 4000.0
            nuevo_mo = st.number_input("Presupuesto Mano de Obra (S/)", value=val_mo, step=500.0)
        nuevo_total = round(nuevo_mat + nuevo_mo, 2)
        st.markdown(f"### 💡 Presupuesto Total Calculado: <span style='color:#38bdf8;'>S/ {nuevo_total:,.2f}</span>", unsafe_allow_html=True)
    else:
        try: val_tot = float(presupuesto_total_db)
        except (ValueError, TypeError): val_tot = 10000.0
        nuevo_total = st.number_input("Presupuesto Total Directo (S/)", value=val_tot, step=1000.0)
        nuevo_mat = presupuesto_mat_db
        nuevo_mo = presupuesto_mo_db

    if st.button("💾 Guardar Configuración de Presupuesto"):
        c.execute("INSERT OR REPLACE INTO presupuestos VALUES (?, ?, ?, ?, ?)", (st.session_state['partida_actual'], modo_ingreso, round(nuevo_total, 2), round(nuevo_mat, 2), round(nuevo_mo, 2)))
        conn.commit()
        st.success("¡Presupuesto actualizado correctamente!")
        st.rerun()

presupuesto_actual_total = round(nuevo_total, 2)
st.write("---")

# ==========================================
# RECOLECCIÓN DE DATOS Y CÁLCULOS GLOBALES (SIN FILTRO DE MES)
# ==========================================
df_personal_db = pd.read_sql(f"SELECT nombre, especialidad, jornal, almuerzo_costo FROM personal WHERE partida='{st.session_state['partida_actual']}'", conn)
lista_trabajadores_db = df_personal_db['nombre'].tolist() if not df_personal_db.empty else ["Grover", "Juan Pérez"]

df_mat_db = pd.read_sql(f"SELECT * FROM materiales WHERE partida='{st.session_state['partida_actual']}'", conn)
if not df_mat_db.empty:
    df_mat_db['fecha_dt'] = pd.to_datetime(df_mat_db['fecha']).dt.date
    df_mat_db['cantidad'] = pd.to_numeric(df_mat_db['cantidad'], errors='coerce').fillna(0.0)
    df_mat_db['precio'] = pd.to_numeric(df_mat_db['precio'], errors='coerce').fillna(0.0)
    if 'descuento' in df_mat_db.columns:
        df_mat_db['descuento'] = pd.to_numeric(df_mat_db['descuento'], errors='coerce').fillna(0.0)
    else:
        df_mat_db['descuento'] = 0.0
else:
    df_mat_db['fecha_dt'] = pd.Series(dtype='object')
    df_mat_db['cantidad'] = pd.Series(dtype='float64')
    df_mat_db['precio'] = pd.Series(dtype='float64')
    df_mat_db['descuento'] = pd.Series(dtype='float64')

df_asist_db = pd.read_sql(f"SELECT * FROM asistencia WHERE partida='{st.session_state['partida_actual']}'", conn)
if not df_asist_db.empty:
    df_asist_db['fecha_dt'] = pd.to_datetime(df_asist_db['fecha']).dt.date
else:
    df_asist_db['fecha_dt'] = pd.Series(dtype='object')

trabajadores_registrados = lista_trabajadores_db

# --- DETERMINAR EL RANGO TOTAL GLOBAL DE LA OBRA ---
todas_las_fechas = []
if not df_mat_db.empty:
    todas_las_fechas.extend(df_mat_db['fecha_dt'].tolist())
if not df_asist_db.empty:
    todas_las_fechas.extend(df_asist_db['fecha_dt'].tolist())

if todas_las_fechas:
    min_fecha_obra = min(todas_las_fechas)
    max_fecha_obra = max(todas_las_fechas)
else:
    min_fecha_obra = date.today()
    max_fecha_obra = date.today()

# Ajustar al Lunes de la semana inicial de manera continua
start_current_week_res = min_fecha_obra - timedelta(days=min_fecha_obra.weekday())
datos_resumen_semanas = []
gasto_acum_temp = 0.0
semana_contador = 1

while start_current_week_res <= max_fecha_obra + timedelta(days=7):
    end_current_week_res = start_current_week_res + timedelta(days=5) # Lunes a Sábado
    
    mo_sem = 0.0
    if not df_asist_db.empty:
        mask_w = (df_asist_db['fecha_dt'] >= start_current_week_res) & (df_asist_db['fecha_dt'] <= end_current_week_res) & (df_asist_db['partida'] == st.session_state['partida_actual'])
        df_w_asist = df_asist_db.loc[mask_w]
        for trab in trabajadores_registrados:
            df_tw = df_w_asist[df_w_asist['trabajador'] == trab]
            c_comp = len(df_tw[df_tw['estado'] == 'Día Completo'])
            c_med = len(df_tw[df_tw['estado'] == 'Medio Día'])
            c_alm = len(df_tw[df_tw['almuerzo'].str.startswith('Sale', na=False)])
            
            c.execute("SELECT especialidad, jornal, almuerzo_costo FROM personal WHERE partida=? AND nombre=?", (st.session_state['partida_actual'], trab))
            p_row = c.fetchone()
            if p_row:
                esp_t, jornal_val, alm_val = p_row
                jornal_val = float(jornal_val) if pd.notna(jornal_val) else (120.0 if esp_t in ["Operario", "Enchapador", "Oficial"] else 100.0)
                alm_val = float(alm_val) if pd.notna(alm
