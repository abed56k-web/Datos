import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date
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

# Variables para navegar en el calendario
if 'cal_mes' not in st.session_state: st.session_state['cal_mes'] = 9 # Septiembre por defecto
if 'cal_ano' not in st.session_state: st.session_state['cal_ano'] = 2026

# ==========================================
# 3. PANTALLA DE INICIO (NEXUS OBRA - NEÓN OSCURO)
# ==========================================
if not st.session_state['autenticado']:
    st.markdown("""
        <style>
        .stApp { background-color: #0f172a !important; color: #e2e8f0 !important; }
        h1, h2, h3, p, label, span { color: #e2e8f0 !important; }
        
        div[data-testid="stButton"] button {
            background: linear-gradient(90deg, #06b6d4 0%, #3b82f6 100%) !important;
            color: white !important; border: none !important; border-radius: 8px;
            font-weight: bold; letter-spacing: 1px; transition: 0.3s;
        }
        div[data-testid="stButton"] button:hover { box-shadow: 0 0 15px rgba(6, 182, 212, 0.6); transform: scale(1.02); }
        
        .stTextInput input, .stPasswordInput input { 
            background-color: #1e293b !important; color: #38bdf8 !important; border: 1px solid #475569; 
        }
        
        .social-container img { width: 32px; height: 32px; margin-right: 15px; cursor: pointer; filter: drop-shadow(0 0 5px #38bdf8); transition: 0.3s; }
        .social-container img:hover { transform: translateY(-3px); }
        </style>
    """, unsafe_allow_html=True)

    col1, col_vacia, col2 = st.columns([1.2, 0.2, 1])
    with col1:
        st.markdown("<h1 style='font-size: 5rem; color: #38bdf8 !important; text-shadow: 0 0 20px #38bdf8;'>NEXUS<br>OBRA</h1>", unsafe_allow_html=True)
        st.markdown("<p style='font-size: 1.2rem;'>Sistema Inteligente de Control de Proyectos - Ayacucho</p>", unsafe_allow_html=True)
        st.markdown("""
            <div class="social-container" style="margin-top: 30px;">
                <a href="#"><img src="https://cdn-icons-png.flaticon.com/512/20/20673.png" alt="Facebook"></a>
                <a href="#"><img src="https://cdn-icons-png.flaticon.com/512/3046/3046128.png" alt="TikTok"></a>
                <a href="#"><img src="https://cdn-icons-png.flaticon.com/512/1384/1384031.png" alt="Instagram"></a>
                <a href="#"><img src="https://cdn-icons-png.flaticon.com/512/1384/1384028.png" alt="YouTube"></a>
                <a href="#"><img src="https://cdn-icons-png.flaticon.com/512/1384/1384023.png" alt="WhatsApp"></a>
            </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("<div style='background-color: #1e293b; padding: 30px; border-radius: 15px; border: 1px solid #334155;'>", unsafe_allow_html=True)
        st.markdown("<h2 style='text-align: center; color: #a855f7 !important;'>Acceso al Sistema</h2>", unsafe_allow_html=True)
        if not st.session_state['mostrar_registro']:
            email_login = st.text_input("Usuario / Email")
            clave_login = st.text_input("Contraseña", type="password")
            if st.button("INICIAR SESIÓN 🚀"):
                if verificar_usuario(email_login, clave_login):
                    st.session_state['autenticado'] = True
                    st.session_state['usuario_actual'] = email_login
                    st.rerun()
                else:
                    st.error("Credenciales incorrectas.")
            st.write("---")
            if st.button("Crear un nuevo usuario"):
                st.session_state['mostrar_registro'] = True
                st.rerun()
        else:
            email_reg = st.text_input("Nuevo Correo")
            clave_reg = st.text_input("Crear Contraseña", type="password")
            if st.button("Registrar Usuario"):
                if email_reg and clave_reg:
                    agregar_usuario(email_reg, clave_reg)
                    st.success("¡Usuario creado!")
                    st.session_state['mostrar_registro'] = False
                    st.rerun()
            if st.button("Volver atrás"):
                st.session_state['mostrar_registro'] = False
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# ==========================================
# 4. DISEÑO INTERIOR (CELESTE CLARO FUTURISTA)
# ==========================================
st.markdown("""
    <style>
    /* Fondo celeste casi blanco (#f0f9ff es un Sky Blue muy suave) */
    .stApp { background-image: none !important; background-color: #f0f9ff !important; }
    h1, h2, h3, p, label, span, div { color: #0f172a !important; }
    
    /* Tarjetas Blancas con bordes celestes para que resalten */
    div[data-testid="metric-container"], .stForm, .stDataFrame {
        background-color: white !important; border: 1px solid #bae6fd !important; 
        padding: 15px; border-radius: 12px; box-shadow: 0 4px 10px rgba(14, 165, 233, 0.1);
    }
    
    /* Inputs amigables y visibles dentro del programa */
    .stTextInput input, .stNumberInput input, .stSelectbox div, .stTextArea textarea { 
        background-color: #ffffff !important; color: #0f172a !important; border: 1px solid #94a3b8 !important; border-radius: 6px;
    }
    
    /* Botones internos en azul elegante */
    div[data-testid="stButton"] button {
        background: #0ea5e9 !important; color: white !important; border-radius: 6px; font-weight: bold;
    }
    div[data-testid="stButton"] button:hover { background: #0284c7 !important; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 5. GESTOR DE PARTIDAS
# ==========================================
if st.session_state['partida_actual'] is None:
    st.markdown("<h1 style='text-align: center; color: #0284c7 !important;'>🏗️ Gestor de Proyectos</h1>", unsafe_allow_html=True)
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
        nueva_partida = st.text_input("Nombre de la nueva partida (Ej. Instalaciones)")
        if st.button("CREAR Y ENTRAR ⚡", use_container_width=True):
            if nueva_partida:
                st.session_state['lista_partidas'].append(nueva_partida)
                st.session_state['partida_actual'] = nueva_partida
                st.rerun()
    st.stop()

# ==========================================
# 6. DASHBOARD DE LA PARTIDA SELECCIONADA
# ==========================================
col_top1, col_top2 = st.columns([4, 1])
with col_top1:
    st.markdown(f"<h2 style='color: #0284c7 !important;'>📍 Modulo: {st.session_state['partida_actual']}</h2>", unsafe_allow_html=True)
with col_top2:
    st.write("") 
    if st.button("⬅️ Volver a Partidas"):
        st.session_state['partida_actual'] = None
        st.rerun()

st.write("---")

col_graf, col_form = st.columns([1.2, 1])

with col_graf:
    st.subheader("💰 Distribución de Presupuesto")
    labels = ['Materiales', 'Mano de Obra', 'Saldo/Utilidad']
    values = [4250, 1800, 8950]
    colores = ['#0ea5e9', '#f59e0b', '#10b981'] 
    
    fig_dona = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.6, marker_colors=colores)])
    fig_dona.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(t=10, b=10, l=0, r=0),
        legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5, font=dict(color="#0f172a"))
    )
    fig_dona.update_traces(hoverinfo='label+value', textinfo='percent', textfont_color='white')
    st.plotly_chart(fig_dona, use_container_width=True)

with col_form:
    st.subheader("📝 Centro de Registro")
    tab_mat, tab_mo = st.tabs(["📦 Ingresar Materiales", "👷 Registrar Actividad"])
    
    with tab_mat:
        with st.form("form_materiales"):
            st.date_input("Fecha", date.today(), key="f1")
            mat_nombre = st.text_input("Material / Insumo (Ej. Cemento)")
            col_m1, col_m2 = st.columns(2)
            with col_m1: cant = st.number_input("Cantidad", min_value=1.0, value=1.0)
            with col_m2: pre = st.number_input("Precio Unitario (S/)", min_value=0.0)
            if st.form_submit_button("Guardar Material", use_container_width=True): st.success("Guardado.")
            
    with tab_mo:
        with st.form("form_mano_obra"):
            st.date_input("Fecha", date.today(), key="f2")
            st.text_input("Nombre del Trabajador")
            st.text_area("Actividad realizada (Ej. Tarrajeo muro 2x3m)")
            
            estado_asistencia = st.selectbox("Estado de Asistencia", ["🟩 Día Completo", "🟨 Medio Día / Tarde", "🟥 Emergencia / Falta"])
            if estado_asistencia == "🟥 Emergencia / Falta":
                st.text_input("Motivo de la Emergencia (Opcional)", placeholder="Ej. Lluvia fuerte, problema de salud...")
                
            if st.form_submit_button("Guardar Actividad", use_container_width=True): st.success("Actividad registrada.")

st.write("---")

# ==========================================
# 7. ALMANAQUE INTERACTIVO CON NAVEGACIÓN
# ==========================================
st.subheader("📅 Control Mensual de Asistencia")

# Controles de navegación del mes
meses_espanol = ["", "ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO", "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"]
col_btn1, col_tit, col_btn2 = st.columns([1, 2, 1])

with col_btn1:
    if st.button("◀ Mes Anterior", use_container_width=True):
        if st.session_state['cal_mes'] == 1:
            st.session_state['cal_mes'] = 12
            st.session_state['cal_ano'] -= 1
        else:
            st.session_state['cal_mes'] -= 1
        st.rerun()

with col_tit:
    st.markdown(f"<h3 style='text-align: center; color: #0284c7 !important; margin: 0;'>{meses_espanol[st.session_state['cal_mes']]} {st.session_state['cal_ano']}</h3>", unsafe_allow_html=True)

with col_btn2:
    if st.button("Mes Siguiente ▶", use_container_width=True):
        if st.session_state['cal_mes'] == 12:
            st.session_state['cal_mes'] = 1
            st.session_state['cal_ano'] += 1
        else:
            st.session_state['cal_mes'] += 1
        st.rerun()

st.markdown("<br>", unsafe_allow_html=True)
trabajador_seleccionado = st.selectbox("Seleccione Trabajador para ver su Almanaque:", ["Juan Pérez", "Luis Gómez", "Carlos Ruiz"])

# Generador de Calendario HTML interactivo (Estilo bloques sólidos)
calendar.setfirstweekday(calendar.SUNDAY)
mes_cal = calendar.monthcalendar(st.session_state['cal_ano'], st.session_state['cal_mes'])

# Simulador de asistencias basado en el mes y el nombre para que tenga sentido visual
random.seed(hash(trabajador_seleccionado + str(st.session_state['cal_mes'])))

html_cal = """
<style>
.cal-wrapper { background-color: white; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); padding: 20px; max-width: 700px; margin: 0 auto;}
.cal-table { width: 100%; border-collapse: separate; border-spacing: 4px; text-align: center; font-family: sans-serif; }
.cal-table th { padding: 10px; color: #475569; font-weight: bold; font-size: 1.1rem; }
.cal-table td { padding: 15px; border-radius: 4px; font-size: 1.2rem; font-weight: bold; border: 1px solid #f1f5f9; }
.cal-vacio { background-color: #ffffff; color: transparent; border: none !important; }
.cal-futuro { background-color: #f8fafc; color: #cbd5e1; }
/* Colores Sólidos tipo Almanaque */
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
        if dia == 0:
            html_cal += "<td class='cal-vacio'>0</td>"
        else:
            # Lógica simulada de asistencia (Domingos descansan o asisten medio día, días aleatorios faltan)
            clase = "cal-futuro"
            if date(st.session_state['cal_ano'], st.session_state['cal_mes'], dia) <= date.today() + pd.Timedelta(days=30): # Mostrar datos hasta la actualidad
                estado = random.choices(["verde", "amarillo", "rojo"], weights=[75, 15, 10])[0]
                if estado == "verde": clase = "cal-verde"
                elif estado == "amarillo": clase = "cal-amarillo"
                elif estado == "rojo": clase = "cal-rojo"
            
            html_cal += f"<td class='{clase}'>{dia}</td>"
    html_cal += "</tr>"
html_cal += "</table></div>"

st.markdown(html_cal, unsafe_allow_html=True)
st.write("---")

# ==========================================
# 8. PLANILLA DE NEGOCIACIÓN SEMANAL
# ==========================================
st.subheader("🤝 Planilla de Negociación y Pagos")
st.write("Ingresa los días trabajados en la semana y el **jornal final acordado** para calcular el pago automático.")

df_planilla = pd.DataFrame({
    "Trabajador": ["Juan Pérez (Operario)", "Luis Gómez (Ayudante)", "Carlos Ruiz", ""],
    "Días Completos": [5, 4, 2, 0],
    "Medios Días": [1, 0, 1, 0],
    "Jornal Negociado (S/)": [80.0, 50.0, 90.0, 0.0]
})

df_editado = st.data_editor(df_planilla, num_rows="dynamic", use_container_width=True, hide_index=True)

st.markdown("<div style='background-color: white; padding: 20px; border-radius: 10px; border-left: 5px solid #0ea5e9; box-shadow: 0 4px 6px rgba(0,0,0,0.05);'>", unsafe_allow_html=True)
st.markdown("#### 🧾 Resumen de Pagos")
total_obra = 0
for index, row in df_editado.iterrows():
    if row["Trabajador"]:
        pago_total = (row["Días Completos"] + (row["Medios Días"] * 0.5)) * row["Jornal Negociado (S/)"]
        total_obra += pago_total
        st.markdown(f"**{row['Trabajador']}**: {row['Días Completos']} días + {row['Medios Días']} medios días a S/{row['Jornal Negociado (S/)']} = **<span style='color:#0ea5e9;'>S/ {pago_total:.2f}</span>**", unsafe_allow_html=True)
st.markdown(f"<h3 style='color: #10b981 !important; margin-top: 15px;'>Total a desembolsar: S/ {total_obra:.2f}</h3>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)
