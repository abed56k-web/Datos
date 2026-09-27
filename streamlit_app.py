import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date
import random
import sqlite3
import hashlib

# 1. CONFIGURACIÓN INICIAL (Modo ancho para parecer PowerBI)
st.set_page_config(page_title="Control de Obra", layout="wide", initial_sidebar_state="collapsed")

# 2. CONFIGURACIÓN DE LA BASE DE DATOS DE USUARIOS
# Esto crea un archivo llamado "usuarios.db" para guardar las cuentas
conn = sqlite3.connect('usuarios.db', check_same_thread=False)
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS usuarios (email TEXT, password TEXT)')
conn.commit()

def encriptar_clave(clave):
    return hashlib.sha256(str.encode(clave)).hexdigest()

def agregar_usuario(email, clave):
    c.execute('INSERT INTO usuarios (email, password) VALUES (?, ?)', (email, encriptar_clave(clave)))
    conn.commit()

def verificar_usuario(email, clave):
    c.execute('SELECT * FROM usuarios WHERE email=? AND password=?', (email, encriptar_clave(clave)))
    return c.fetchone() is not None

# 3. ESTILOS CSS (Para el diseño PowerBI y la pantalla dividida)
st.markdown("""
    <style>
    /* Fondo claro estilo PowerBI para toda la app */
    .stApp {
        background-color: #f3f4f6;
    }
    /* Estilo de la caja izquierda del Login */
    .caja-izquierda {
        background: linear-gradient(135deg, #6b7280 0%, #374151 100%);
        padding: 40px;
        border-radius: 10px;
        color: white;
        height: 100%;
    }
    /* Tarjetas de métricas estilo PowerBI */
    div[data-testid="metric-container"] {
        background-color: white;
        border: 1px solid #e5e7eb;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    </style>
""", unsafe_allow_html=True)

# 4. PANTALLA DE INICIO DE SESIÓN / REGISTRO
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False

if not st.session_state['autenticado']:
    # Creamos dos columnas simulando tu imagen de referencia
    col1, col2 = st.columns([1, 1], gap="large")
    
    with col1:
        st.markdown("""
        <div class="caja-izquierda">
            <h1 style='font-size: 3rem;'>Bienvenido<br>de Vuelta</h1>
            <p style='font-size: 1.2rem; margin-top: 20px;'>Plataforma integral para el control de avance, materiales y personal de obra. Registra tus gastos y visualiza tu progreso en tiempo real.</p>
            <br><br><br>
            <p>📍 Obra: Ayacucho - Enchapado y Tarrajeo</p>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.write("<br><br>", unsafe_allow_html=True)
        st.title("Sign in")
        
        # Pestañas para elegir entre Iniciar Sesión o Crear Cuenta
        tab_login, tab_registro = st.tabs(["Ingresar", "Crear nueva cuenta"])
        
        with tab_login:
            with st.form("form_login"):
                email_login = st.text_input("Email Address")
                clave_login = st.text_input("Password", type="password")
                btn_login = st.form_submit_button("Sign in now", use_container_width=True)
                
                if btn_login:
                    if verificar_usuario(email_login, clave_login):
                        st.session_state['autenticado'] = True
                        st.session_state['usuario_actual'] = email_login
                        st.rerun()
                    else:
                        st.error("Correo o contraseña incorrectos.")
                        
        with tab_registro:
            with st.form("form_registro"):
                email_reg = st.text_input("Nuevo Email")
                clave_reg = st.text_input("Crear Password", type="password")
                btn_reg = st.form_submit_button("Registrar cuenta", use_container_width=True)
                
                if btn_reg:
                    if email_reg and clave_reg:
                        agregar_usuario(email_reg, clave_reg)
                        st.success("¡Cuenta creada! Ahora ve a la pestaña 'Ingresar' para entrar.")
                    else:
                        st.warning("Por favor, llena ambos campos.")
                        
    st.stop() # Detiene el código para que no se vea el dashboard sin entrar

# ==========================================
# 5. DASHBOARD ESTILO POWER BI
# ==========================================
st.title(f"📊 Dashboard de Obra (Usuario: {st.session_state['usuario_actual']})")

# Tarjetas KPI (Indicadores clave) estilo PowerBI
kpi1, kpi2, kpi3, kpi4 = st.columns(4)
with kpi1: st.metric(label="Presupuesto Total", value="S/ 15,000", delta="Base")
with kpi2: st.metric(label="Gasto en Materiales", value="S/ 4,250", delta="-S/ 450 esta semana", delta_color="inverse")
with kpi3: st.metric(label="Gasto en Mano de Obra", value="S/ 1,800", delta="-S/ 300 esta semana", delta_color="inverse")
with kpi4: st.metric(label="Saldo Disponible", value="S/ 8,950", delta="59% Restante")

st.write("---")

# Contenedores principales
col_grafico, col_formularios = st.columns([2, 1])

with col_grafico:
    st.subheader("📅 Calendario de Inversión Diaria")
    
    # Generamos datos de ejemplo para el calendario
    fechas = pd.date_range(start='2026-09-01', end='2026-10-31')
    datos_calendario = pd.DataFrame({'Fecha': fechas})
    datos_calendario['Gasto_Diario'] = [random.choice([0, 150, 300, 450, 0, 80, 0]) for _ in range(len(fechas))]
    datos_calendario['Semana'] = datos_calendario['Fecha'].dt.isocalendar().week
    datos_calendario['Dia_Semana'] = datos_calendario['Fecha'].dt.day_name()
    
    # Gráfico interactivo estilo PowerBI
    fig = px.density_heatmap(
        datos_calendario, x="Semana", y="Dia_Semana", z="Gasto_Diario",
        color_continuous_scale="Blues", # Tonos azules empresariales
        labels={'Semana': 'Semana del Año', 'Dia_Semana': 'Día', 'Gasto_Diario': 'Gasto Total (S/)'}
    )
    fig.update_yaxes(categoryorder='array', categoryarray=['Sunday', 'Saturday', 'Friday', 'Thursday', 'Wednesday', 'Tuesday', 'Monday'])
    
    # Hacemos que el fondo del gráfico sea transparente para que encaje con el gris claro del panel
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig, use_container_width=True)

with col_formularios:
    st.subheader("📝 Ingreso Rápido")
    seleccion = st.radio("¿Qué vas a registrar?", ["Mano de Obra", "Materiales"])
    
    if seleccion == "Mano de Obra":
        with st.form("form_personal"):
            fecha_p = st.date_input("Fecha", date.today())
            nombre = st.text_input("Trabajador")
            frente = st.selectbox("Frente", ["2do Piso (Enchapado)", "3er Piso (Tarrajeo)"])
            jornal = st.number_input("Monto (S/)", min_value=0.0)
            if st.form_submit_button("Guardar"): st.success("Guardado.")
            
    else:
        with st.form("form_materiales"):
            fecha_m = st.date_input("Fecha", date.today())
            material = st.selectbox("Insumo", ["Cemento", "Cerámicos", "Pegamento", "Sikaflex", "Otros"])
            costo = st.number_input("Costo Total (S/)", min_value=0.0)
            if st.form_submit_button("Guardar"): st.success("Guardado.")
