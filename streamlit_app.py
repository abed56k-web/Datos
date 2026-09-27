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

# 2. BASE DE DATOS Y ESTADOS
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

if 'autenticado' not in st.session_state: st.session_state['autenticado'] = False
if 'mostrar_registro' not in st.session_state: st.session_state['mostrar_registro'] = False
if 'partida_actual' not in st.session_state: st.session_state['partida_actual'] = None
if 'lista_partidas' not in st.session_state: st.session_state['lista_partidas'] = ["Acabados 2do Nivel", "Tarrajeo 3er Nivel"]

# ==========================================
# 3. PANTALLA DE INICIO (DISEÑO MONTAÑA RESTAURADO)
# ==========================================
if not st.session_state['autenticado']:
    st.markdown("""
        <style>
        .stApp {
            background-image: linear-gradient(rgba(0, 0, 0, 0.4), rgba(0, 0, 0, 0.7)), url("https://images.unsplash.com/photo-1519681393784-d120267933ba?q=80&w=2070&auto=format&fit=crop");
            background-size: cover; background-position: center; background-attachment: fixed;
        }
        h1, h2, h3, p, label, .stCheckbox label { color: white !important; }
        
        /* Inputs blancos, texto negro */
        div[data-baseweb="input"] > div { background-color: #ffffff !important; border-radius: 4px; }
        input { color: #000000 !important; font-weight: bold; }
        
        /* Botón Naranja Original */
        div[data-testid="stButton"] button {
            background-color: #d95b32 !important; color: white !important; border: none !important; 
            font-size: 1.1rem; width: 100%; transition: 0.3s;
        }
        div[data-testid="stButton"] button:hover { background-color: #b54925 !important; }
        
        .social-icons { font-size: 1.5rem; letter-spacing: 15px; margin-top: 10px; }
        .social-icons a { text-decoration: none; color: white; }
        </style>
    """, unsafe_allow_html=True)

    col1, col_vacia, col2 = st.columns([1.2, 0.2, 1])
    with col1:
        st.markdown("<h1 style='font-size: 5rem; line-height: 1.1; margin-bottom: 0;'>Welcome<br>Back</h1>", unsafe_allow_html=True)
        st.markdown("<p style='font-size: 1.1rem; margin-top: 15px;'>Plataforma integral para el control de avance, materiales y personal. Registra tus gastos en tiempo real.</p>", unsafe_allow_html=True)
        st.markdown("""
            <div class="social-icons">
                <a href="#">🌐</a> <a href="#">🐦</a> <a href="#">📸</a> <a href="#">▶️</a>
            </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("<h2 style='text-align: center; font-size: 3rem; margin-bottom: 30px;'>Sign in</h2>", unsafe_allow_html=True)
        if not st.session_state['mostrar_registro']:
            email_login = st.text_input("Email Address")
            clave_login = st.text_input("Password", type="password")
            st.checkbox("Remember Me")
            
            if st.button("Sign in now"):
                if verificar_usuario(email_login, clave_login):
                    st.session_state['autenticado'] = True
                    st.session_state['usuario_actual'] = email_login
                    st.rerun()
                else:
                    st.error("Credenciales incorrectas.")
            st.write("---")
            if st.button("¿No tienes cuenta? Regístrate aquí"):
                st.session_state['mostrar_registro'] = True
                st.rerun()
            with st.expander("Terms of Service | Privacy Policy"):
                st.write("**Uso de Datos:** Sistema privado. Datos almacenados con encriptación local.")
        else:
            st.markdown("<p style='text-align: center;'><b>Crea tu cuenta</b></p>", unsafe_allow_html=True)
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
# 4. DISEÑO INTERIOR (Fondo Suave y Profesional)
# ==========================================
st.markdown("""
    <style>
    /* Fondo gris muy suave y limpio */
    .stApp { background-image: none !important; background-color: #f8fafc !important; }
    h1, h2, h3, p, label, span { color: #1e293b !important; }
    
    /* Tarjetas Blancas elegantes */
    div[data-testid="metric-container"], .stForm {
        background-color: white !important; border: 1px solid #e2e8f0; padding: 15px; 
        border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    
    /* Inputs amigables dentro del panel */
    .stTextInput input, .stNumberInput input, .stSelectbox div, .stTextArea textarea { 
        background-color: #f1f5f9 !important; color: #0f172a !important; border: 1px solid #cbd5e1; border-radius: 6px;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 5. GESTOR DE PARTIDAS
# ==========================================
if st.session_state['partida_actual'] is None:
    st.title("🏗️ Gestor de Frentes de Trabajo")
    st.write("Selecciona o crea una partida para iniciar el control de hoy.")
    
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        st.markdown("### 📂 Ingresar a Partida Existente")
        partida_seleccionada = st.selectbox("Mis Partidas:", st.session_state['lista_partidas'])
        if st.button("ENTRAR AL PANEL ➡️", use_container_width=True):
            st.session_state['partida_actual'] = partida_seleccionada
            st.rerun()
            
    with col_p2:
        st.markdown("### ➕ Crear Nueva Partida")
        nueva_partida = st.text_input("Nombre de la nueva partida (Ej. Vaciado de Techo)")
        if st.button("CREAR Y ENTRAR ⚡", use_container_width=True):
            if nueva_partida:
                st.session_state['lista_partidas'].append(nueva_partida)
                st.session_state['partida_actual'] = nueva_partida
                st.rerun()
    st.stop()

# ==========================================
# 6. DASHBOARD DE LA PARTIDA
# ==========================================
col_top1, col_top2 = st.columns([4, 1])
with col_top1: st.title(f"📊 {st.session_state['partida_actual']}")
with col_top2: 
    st.write("")
    if st.button("⬅️ Cambiar Partida"):
        st.session_state['partida_actual'] = None
        st.rerun()

st.write("---")

col_graf, col_form = st.columns([1, 1.2])

with col_graf:
    st.subheader("Distribución de Presupuesto")
    labels = ['Materiales', 'Mano de Obra', 'Saldo/Utilidad']
    values = [4250, 1800, 8950]
    colores = ['#0ea5e9', '#f59e0b', '#10b981'] # Azul, Naranja, Verde
    fig_dona = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.5, marker_colors=colores)])
    fig_dona.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(t=10, b=10, l=0, r=0),
        legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5, font=dict(color="#1e293b"))
    )
    fig_dona.update_traces(textinfo='percent', textfont_color='white')
    st.plotly_chart(fig_dona, use_container_width=True)

with col_form:
    st.subheader("📝 Centro de Registro")
    tab_mat, tab_mo = st.tabs(["📦 Materiales", "👷 Asistencia y Actividad"])
    
    with tab_mat:
        with st.form("form_materiales"):
            st.date_input("Fecha de Compra", date.today())
            mat_nombre = st.text_input("Material / Insumo (Ej. Cemento Portland)")
            col_m1, col_m2 = st.columns(2)
            with col_m1: cant = st.number_input("Cantidad", min_value=1.0)
            with col_m2: pre = st.number_input("Precio Unitario (S/)", min_value=0.0)
            if st.form_submit_button("Guardar Material", use_container_width=True): st.success("Guardado.")
            
    with tab_mo:
        with st.form("form_mano_obra"):
            st.date_input("Fecha", date.today())
            st.text_input("Trabajador (Ej. Juan Pérez)")
            st.text_input("Actividad (Ej. Tarrajeo muro 2x3m)")
            
            # Selector de estado de asistencia
            estado_asistencia = st.selectbox("Estado de Asistencia", ["Día Completo", "Medio Día", "Emergencia / Falta"])
            
            # Si hubo emergencia, mostrar campo de motivo
            motivo = ""
            if estado_asistencia == "Emergencia / Falta":
                motivo = st.text_input("Motivo (Opcional - Ej. Permiso médico, lluvia)")
                
            if st.form_submit_button("Guardar Actividad", use_container_width=True): 
                st.success("Actividad registrada.")

st.write("---")

# ==========================================
# 7. CALENDARIO DE PARED (ALMANAQUE)
# ==========================================
st.subheader("📅 Control Mensual de Asistencia por Trabajador")

# Leyenda de Colores
st.markdown("""
    <div style="background-color: white; padding: 15px; border-radius: 8px; border: 1px solid #e2e8f0; display: flex; gap: 20px; margin-bottom: 20px;">
        <b>Leyenda:</b>
        <span style="color: #10b981;">🟩 <b>Día Completo</b> (Asistió normal)</span>
        <span style="color: #f59e0b;">🟨 <b>Medio Día</b> (Tarde o media jornada)</span>
        <span style="color: #ef4444;">🟥 <b>Emergencia/Falta</b> (No trabajó)</span>
    </div>
""", unsafe_allow_html=True)

trabajador_seleccionado = st.selectbox("Seleccione el Trabajador para ver su almanaque:", ["Juan Pérez (Operario)", "Luis Gómez (Ayudante)"])

# Generador de Calendario HTML
calendar.setfirstweekday(calendar.SUNDAY)
mes_cal = calendar.monthcalendar(2026, 9) # Septiembre 2026

# Simulamos algunos días para Juan Pérez (Verde=Completo, Amarillo=Medio, Rojo=Emergencia)
dias_verde = [1, 2, 3, 4, 7, 8, 9, 10, 11, 14, 15, 17, 18, 21, 22, 23, 24, 25, 28, 29, 30]
dias_amarillo = [16, 26]
dias_rojo = [5] # Faltó el 5

html_cal = """
<style>
.cal-table { width: 100%; max-width: 600px; border-collapse: collapse; text-align: center; font-family: sans-serif; background-color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1); border-radius: 10px; overflow: hidden; margin: auto; }
.cal-table th { background-color: #f1f5f9; padding: 15px; color: #475569; font-weight: bold; border-bottom: 2px solid #e2e8f0; }
.cal-table td { padding: 15px; border: 1px solid #f1f5f9; font-size: 1.1rem; font-weight: bold; color: #94a3b8; }
.cal-verde { background-color: #10b981; color: white !important; border-radius: 5px; box-shadow: inset 0 0 5px rgba(0,0,0,0.1); }
.cal-amarillo { background-color: #f59e0b; color: white !important; border-radius: 5px; box-shadow: inset 0 0 5px rgba(0,0,0,0.1); }
.cal-rojo { background-color: #ef4444; color: white !important; border-radius: 5px; box-shadow: inset 0 0 5px rgba(0,0,0,0.1); }
.cal-title { text-align: center; color: #0ea5e9; font-size: 1.5rem; font-weight: 800; letter-spacing: 2px; margin-bottom: 10px;}
</style>
<div class="cal-title">SEPTIEMBRE 2026</div>
<table class="cal-table">
    <tr><th>D</th><th>L</th><th>M</th><th>M</th><th>J</th><th>V</th><th>S</th></tr>
"""
for semana in mes_cal:
    html_cal += "<tr>"
    for dia in semana:
        if dia == 0:
            html_cal += "<td></td>"
        else:
            clase = ""
            if trabajador_seleccionado == "Juan Pérez (Operario)":
                if dia in dias_verde: clase = "cal-verde"
                elif dia in dias_amarillo: clase = "cal-amarillo"
                elif dia in dias_rojo: clase = "cal-rojo"
            html_cal += f"<td class='{clase}'>{dia}</td>"
    html_cal += "</tr>"
html_cal += "</table>"

st.markdown(html_cal, unsafe_allow_html=True)

st.write("---")

# ==========================================
# 8. PLANILLA DE NEGOCIACIÓN SEMANAL
# ==========================================
st.subheader("🤝 Planilla de Negociación y Pagos")
st.write("Ingresa los días trabajados en la semana y el **jornal final acordado** para calcular el pago automático.")

df_planilla = pd.DataFrame({
    "Trabajador": ["Juan Pérez (Operario)", "Luis Gómez (Ayudante)", "", ""],
    "Días Completos": [5, 4, 0, 0],
    "Medios Días": [1, 0, 0, 0],
    "Jornal Negociado (S/)": [80.0, 50.0, 0.0, 0.0]
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
