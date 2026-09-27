import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, timedelta
import calendar
import sqlite3
import hashlib
import random

# 1. CONFIGURACIÓN INICIAL
st.set_page_config(page_title="Control de Obra", layout="wide", initial_sidebar_state="collapsed")

# 2. BASE DE DATOS Y ESTADOS GLOBALES
conn = sqlite3.connect('usuarios.db', check_same_thread=False)
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS usuarios (email TEXT, password TEXT)')
conn.commit()

def encriptar_clave(clave): return hashlib.sha256(str.encode(clave)).hexdigest()
def agregar_usuario(email, clave): 
    c.execute('INSERT INTO usuarios (email, password) VALUES (?, ?)', (email, encriptar_clave(clave)))
    conn.commit()
def verificar_usuario(email, clave):
    c.execute('SELECT * FROM usuarios WHERE email=? AND password=?', (email, encriptar_clave(clave)))
    return c.fetchone() is not None

# Variables de estado
if 'autenticado' not in st.session_state: st.session_state['autenticado'] = False
if 'mostrar_registro' not in st.session_state: st.session_state['mostrar_registro'] = False
if 'partida_actual' not in st.session_state: st.session_state['partida_actual'] = None
if 'lista_partidas' not in st.session_state: st.session_state['lista_partidas'] = ["Acabados 2do Nivel", "Tarrajeo 3er Nivel"]
if 'cal_mes' not in st.session_state: st.session_state['cal_mes'] = 9 
if 'cal_ano' not in st.session_state: st.session_state['cal_ano'] = 2026

# Presupuestos dinámicos
if 'presupuesto_mo' not in st.session_state: st.session_state['presupuesto_mo'] = 5000.00
if 'presupuesto_mat' not in st.session_state: st.session_state['presupuesto_mat'] = 12000.00
if 'gasto_anterior_mo' not in st.session_state: st.session_state['gasto_anterior_mo'] = 2500.00
if 'gasto_anterior_mat' not in st.session_state: st.session_state['gasto_anterior_mat'] = 6000.00

# ==========================================
# 3. PANTALLA DE INICIO (MONTAÑA)
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
            email_login = st.text_input("Email Address")
            clave_login = st.text_input("Password", type="password")
            if st.button("Sign in now"):
                if verificar_usuario(email_login, clave_login):
                    st.session_state['autenticado'] = True
                    st.session_state['usuario_actual'] = email_login
                    st.rerun()
                else:
                    st.error("Error al iniciar sesión.")
            st.write("---")
            if st.button("¿No tienes cuenta? Regístrate aquí"):
                st.session_state['mostrar_registro'] = True
                st.rerun()
        else:
            st.markdown("<p style='text-align: center;'><b>Crea tu cuenta de obra</b></p>", unsafe_allow_html=True)
            email_reg = st.text_input("Nuevo Correo")
            clave_reg = st.text_input("Crear Contraseña", type="password")
            if st.button("Guardar Cuenta"):
                if email_reg and clave_reg:
                    agregar_usuario(email_reg, clave_reg)
                    st.success("¡Cuenta creada!")
                    st.session_state['mostrar_registro'] = False
                    st.rerun()
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
    .stDataFrame { background-color: #1e293b !important; border-radius: 10px; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 5. GESTOR DE PARTIDAS
# ==========================================
if st.session_state['partida_actual'] is None:
    st.markdown("<h1 style='text-align: center; color: #38bdf8 !important;'>🌌 Gestor de Proyectos</h1>", unsafe_allow_html=True)
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
        nueva_partida = st.text_input("Nombre de la nueva partida")
        if st.button("CREAR Y ENTRAR ⚡", use_container_width=True):
            if nueva_partida:
                st.session_state['lista_partidas'].append(nueva_partida)
                st.session_state['partida_actual'] = nueva_partida
                st.rerun()
    st.stop()

# ==========================================
# 6. DASHBOARD DE LA PARTIDA Y PRESUPUESTO
# ==========================================
col_top1, col_top2 = st.columns([4, 1])
with col_top1:
    st.markdown(f"<h2 style='color: #a855f7 !important;'>📍 Partida: {st.session_state['partida_actual']}</h2>", unsafe_allow_html=True)
with col_top2:
    if st.button("⬅️ Volver a Partidas"):
        st.session_state['partida_actual'] = None
        st.rerun()

# CONFIGURACIÓN DE PRESUPUESTO BASE
with st.expander("⚙️ Configurar Presupuesto Base de la Partida"):
    col_b1, col_b2, col_b3 = st.columns(3)
    with col_b1:
        st.session_state['presupuesto_mo'] = st.number_input("Presupuesto Mano de Obra (S/)", value=st.session_state['presupuesto_mo'], step=500.0)
    with col_b2:
        st.session_state['presupuesto_mat'] = st.number_input("Presupuesto Materiales (S/)", value=st.session_state['presupuesto_mat'], step=500.0)
    with col_b3:
        st.info(f"Presupuesto Total: S/ {st.session_state['presupuesto_mo'] + st.session_state['presupuesto_mat']:,.2f}")

st.write("---")

# ==========================================
# 7. ALMANAQUE INTERACTIVO (CON LEYENDA A LA DERECHA)
# ==========================================
st.subheader("📅 Control Mensual de Asistencia")

meses_espanol = ["", "ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO", "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"]
col_btn1, col_tit, col_btn2 = st.columns([1, 2, 1])

with col_btn1:
    if st.button("◀ Mes Anterior", key="btn_ant", use_container_width=True):
        if st.session_state['cal_mes'] == 1: st.session_state['cal_mes'] = 12; st.session_state['cal_ano'] -= 1
        else: st.session_state['cal_mes'] -= 1
        st.rerun()
with col_tit:
    st.markdown(f"<h3 style='text-align: center; color: #38bdf8 !important; margin: 0;'>{meses_espanol[st.session_state['cal_mes']]} {st.session_state['cal_ano']}</h3>", unsafe_allow_html=True)
with col_btn2:
    if st.button("Mes Siguiente ▶", key="btn_sig", use_container_width=True):
        if st.session_state['cal_mes'] == 12: st.session_state['cal_mes'] = 1; st.session_state['cal_ano'] += 1
        else: st.session_state['cal_mes'] += 1
        st.rerun()

st.write("<br>", unsafe_allow_html=True)
trabajador_seleccionado = st.selectbox("Seleccione Trabajador para ver su Almanaque:", ["Juan Pérez", "Luis Gómez", "Carlos Ruiz"])

# Layout del Calendario y Leyenda juntos
col_cal, col_leyenda = st.columns([2.5, 1])

with col_cal:
    calendar.setfirstweekday(calendar.SUNDAY)
    mes_cal = calendar.monthcalendar(st.session_state['cal_ano'], st.session_state['cal_mes'])
    random.seed(hash(trabajador_seleccionado + str(st.session_state['cal_mes'])))

    html_cal = """
    <style>
    .cal-wrapper { background-color: #1e293b; border-radius: 12px; box-shadow: 0 0 10px rgba(56, 189, 248, 0.2); border: 1px solid #38bdf8; padding: 20px; max-width: 100%;}
    .cal-table { width: 100%; border-collapse: separate; border-spacing: 4px; text-align: center; font-family: sans-serif; }
    .cal-table th { padding: 10px; color: #94a3b8; font-weight: bold; font-size: 1.1rem; }
    .cal-table td { padding: 12px; border-radius: 4px; font-size: 1.2rem; font-weight: bold; border: 1px solid #334155; }
    .cal-vacio { background-color: #1e293b; color: transparent; border: none !important; }
    .cal-futuro { background-color: #0f172a; color: #475569; }
    .cal-verde { background-color: #10b981; color: white !important; }
    .cal-amarillo { background-color: #f59e0b; color: white !important; }
    .cal-rojo { background-color: #ef4444; color: white !important; }
    </style>
    <div class="cal-wrapper">
    <table class="cal-table">
        <tr><th>D</th><th>L</th><th>M</th><th>M</th><th>J</th><th>V</th><th>S</th></tr>
    """
    for semana in mes_cal:
        html_cal += "<tr>"
        for dia in semana:
            if dia == 0: html_cal += "<td class='cal-vacio'>0</td>"
            else:
                clase = "cal-futuro"
                if date(st.session_state['cal_ano'], st.session_state['cal_mes'], dia) <= date.today() + pd.Timedelta(days=30):
                    estado = random.choices(["verde", "amarillo", "rojo"], weights=[75, 15, 10])[0]
                    if estado == "verde": clase = "cal-verde"
                    elif estado == "amarillo": clase = "cal-amarillo"
                    elif estado == "rojo": clase = "cal-rojo"
                html_cal += f"<td class='{clase}'>{dia}</td>"
        html_cal += "</tr>"
    html_cal += "</table></div>"
    st.markdown(html_cal, unsafe_allow_html=True)

with col_leyenda:
    st.markdown("""
        <div style="background-color: #1e293b; padding: 25px; border-radius: 12px; border: 1px solid #475569; height: 100%;">
            <h4 style="color: #e2e8f0; margin-top: 0; margin-bottom: 20px;">🎨 Leyenda</h4>
            <p><span style="display:inline-block; width:20px; height:20px; background-color:#10b981; border-radius:4px; margin-right:10px; vertical-align: middle;"></span> <b>Día Completo</b><br><span style="color:#94a3b8; font-size:0.9rem;">Asistencia normal.</span></p>
            <br>
            <p><span style="display:inline-block; width:20px; height:20px; background-color:#f59e0b; border-radius:4px; margin-right:10px; vertical-align: middle;"></span> <b>Medio Día / Tarde</b><br><span style="color:#94a3b8; font-size:0.9rem;">Asistencia parcial.</span></p>
            <br>
            <p><span style="display:inline-block; width:20px; height:20px; background-color:#ef4444; border-radius:4px; margin-right:10px; vertical-align: middle;"></span> <b>Emergencia / Falta</b><br><span style="color:#94a3b8; font-size:0.9rem;">Inasistencia.</span></p>
        </div>
    """, unsafe_allow_html=True)

st.write("---")

# ==========================================
# 8. MÓDULOS SEMANALES (MANO DE OBRA Y MATERIALES)
# ==========================================
# Selector Global de Semana
st.markdown("<h2 style='color: #a855f7 !important;'>🗓️ Cierre y Reporte Semanal</h2>", unsafe_allow_html=True)
col_sem1, col_sem2 = st.columns(2)
with col_sem1: fecha_inicio = st.date_input("Inicio de la Semana", value=date(2026, 9, 21))
with col_sem2: fecha_fin = st.date_input("Fin de la Semana", value=date(2026, 9, 26))
st.markdown(f"**Calculando gastos de la semana: {fecha_inicio.strftime('%d/%m/%Y')} al {fecha_fin.strftime('%d/%m/%Y')}**")

tab_planilla, tab_materiales = st.tabs(["👷 Planilla de Mano de Obra (Semanal)", "📦 Control de Materiales (Semanal)"])

# 8.1 PLANILLA SEMANAL MANO DE OBRA
with tab_planilla:
    st.write("Calcula los pagos correspondientes a esta semana, ajustando jornales y saldos pendientes.")
    df_planilla = pd.DataFrame({
        "Trabajador": ["Juan Pérez (Operario)", "Luis Gómez (Ayudante)", "Carlos Ruiz (Pintor)", ""],
        "Días Completos": [5, 4, 4, 0],
        "Medios Días": [1, 0, 2, 0],
        "Jornal Negociado (S/)": [80.0, 50.0, 90.0, 0.0],
        "Saldo Anterior (S/)": [20.0, -10.0, 0.0, 0.0],
        "Nota del Saldo": ["Favor: Se le quedó a deber", "Contra: Adelanto semana pasada", "", ""]
    })
    df_edit_mo = st.data_editor(df_planilla, num_rows="dynamic", use_container_width=True, hide_index=True)

    gasto_semana_mo = 0
    for index, row in df_edit_mo.iterrows():
        if row["Trabajador"]:
            pago_final = ((row["Días Completos"] + (row["Medios Días"] * 0.5)) * row["Jornal Negociado (S/)"]) + row["Saldo Anterior (S/)"]
            gasto_semana_mo += pago_final
    st.markdown(f"<h3 style='color: #38bdf8;'>Total Planilla Semana: S/ {gasto_semana_mo:.2f}</h3>", unsafe_allow_html=True)

# 8.2 CONTROL SEMANAL DE MATERIALES
with tab_materiales:
    st.write("Ingresa las facturas/boletas de los materiales comprados durante esta semana.")
    df_mats = pd.DataFrame({
        "Insumo / Material": ["Cemento Portland (Bolsa)", "Arena Fina (m3)", "Pegamento (Bolsa)", ""],
        "Cantidad": [20, 3, 10, 0],
        "Precio Unit. (S/)": [28.50, 45.00, 25.00, 0.00]
    })
    df_edit_mat = st.data_editor(df_mats, num_rows="dynamic", use_container_width=True, hide_index=True)
    
    gasto_semana_mat = 0
    for index, row in df_edit_mat.iterrows():
        if row["Insumo / Material"]:
            gasto_semana_mat += (row["Cantidad"] * row["Precio Unit. (S/)"])
    st.markdown(f"<h3 style='color: #38bdf8;'>Total Materiales Semana: S/ {gasto_semana_mat:.2f}</h3>", unsafe_allow_html=True)

st.write("---")

# ==========================================
# 9. BALANCE ACUMULATIVO VS PRESUPUESTO
# ==========================================
st.markdown("<h2 style='color: #10b981 !important;'>📊 Resumen Acumulado de la Partida</h2>", unsafe_allow_html=True)

mo_acumulado = st.session_state['gasto_anterior_mo'] + gasto_semana_mo
mat_acumulado = st.session_state['gasto_anterior_mat'] + gasto_semana_mat

saldo_mo = st.session_state['presupuesto_mo'] - mo_acumulado
saldo_mat = st.session_state['presupuesto_mat'] - mat_acumulado

col_res1, col_res2 = st.columns(2)

with col_res1:
    st.markdown("<div style='background-color: #1e293b; padding: 20px; border-radius: 12px; border-top: 5px solid #f59e0b;'>", unsafe_allow_html=True)
    st.markdown("#### 👷 Balance Mano de Obra")
    st.write(f"**Presupuesto Asignado:** S/ {st.session_state['presupuesto_mo']:.2f}")
    st.write(f"**Gastado Semanas Anteriores:** S/ {st.session_state['gasto_anterior_mo']:.2f}")
    st.write(f"**Gastado ESTA Semana:** S/ {gasto_semana_mo:.2f}")
    st.write(f"**Gasto Total Acumulado:** S/ {mo_acumulado:.2f}")
    
    if saldo_mo >= 0: st.markdown(f"<h3 style='color:#10b981;'>Saldo a Favor: S/ {saldo_mo:.2f}</h3>", unsafe_allow_html=True)
    else: st.markdown(f"<h3 style='color:#ef4444;'>Sobregiro: S/ {abs(saldo_mo):.2f}</h3>", unsafe_allow_html=True)
    
    # Barra de progreso visual
    porcentaje_mo = min(mo_acumulado / st.session_state['presupuesto_mo'], 1.0) if st.session_state['presupuesto_mo'] > 0 else 1.0
    st.progress(porcentaje_mo)
    st.markdown("</div>", unsafe_allow_html=True)

with col_res2:
    st.markdown("<div style='background-color: #1e293b; padding: 20px; border-radius: 12px; border-top: 5px solid #06b6d4;'>", unsafe_allow_html=True)
    st.markdown("#### 📦 Balance Materiales")
    st.write(f"**Presupuesto Asignado:** S/ {st.session_state['presupuesto_mat']:.2f}")
    st.write(f"**Gastado Semanas Anteriores:** S/ {st.session_state['gasto_anterior_mat']:.2f}")
    st.write(f"**Gastado ESTA Semana:** S/ {gasto_semana_mat:.2f}")
    st.write(f"**Gasto Total Acumulado:** S/ {mat_acumulado:.2f}")
    
    if saldo_mat >= 0: st.markdown(f"<h3 style='color:#10b981;'>Saldo a Favor: S/ {saldo_mat:.2f}</h3>", unsafe_allow_html=True)
    else: st.markdown(f"<h3 style='color:#ef4444;'>Sobregiro: S/ {abs(saldo_mat):.2f}</h3>", unsafe_allow_html=True)
    
    porcentaje_mat = min(mat_acumulado / st.session_state['presupuesto_mat'], 1.0) if st.session_state['presupuesto_mat'] > 0 else 1.0
    st.progress(porcentaje_mat)
    st.markdown("</div>", unsafe_allow_html=True)
