import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date
import sqlite3
import hashlib

# 1. CONFIGURACIÓN INICIAL
st.set_page_config(page_title="Control de Obra", layout="wide", initial_sidebar_state="collapsed")

# 2. BASE DE DATOS DE USUARIOS
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

# ==========================================
# 3. PANTALLA DE INICIO (ESTILO MONTAÑA)
# ==========================================
if not st.session_state['autenticado']:
    
    st.markdown("""
        <style>
        .stApp {
            background-image: linear-gradient(rgba(0, 0, 0, 0.4), rgba(0, 0, 0, 0.7)), url("https://images.unsplash.com/photo-1519681393784-d120267933ba?q=80&w=2070&auto=format&fit=crop");
            background-size: cover; background-position: center; background-attachment: fixed;
        }
        h1, h2, h3, p, label, .stCheckbox label { color: white !important; }
        /* Cuadros de texto forzados a blanco con letra negra */
        div[data-baseweb="input"] > div { background-color: #ffffff !important; border-radius: 4px; }
        input { color: #000000 !important; font-weight: bold; }
        /* Botón Naranja */
        div[data-testid="stButton"] button {
            background-color: #d95b32 !important; color: white !important;
            border: none !important; font-size: 1.1rem; width: 100%; transition: 0.3s;
        }
        div[data-testid="stButton"] button:hover { background-color: #b54925 !important; }
        /* Iconos de redes sociales */
        .social-icons { font-size: 1.5rem; letter-spacing: 15px; margin-top: 10px; }
        .social-icons a { text-decoration: none; color: white; }
        </style>
    """, unsafe_allow_html=True)

    col1, col_vacia, col2 = st.columns([1.2, 0.2, 1])
    
    with col1:
        st.markdown("<h1 style='font-size: 5rem; line-height: 1.1; margin-bottom: 0;'>Bienvenido<br>de nuevo</h1>", unsafe_allow_html=True)
        st.markdown("<p style='font-size: 1.1rem; margin-top: 15px;'>Plataforma integral para el control de avance, materiales y personal. Administra el enchapado y tarrajeo de forma precisa.</p>", unsafe_allow_html=True)
        # Redes sociales simuladas
        st.markdown("""
            <div class="social-icons">
                <a href="#">🌐</a> <a href="#">🐦</a> <a href="#">📸</a> <a href="#">▶️</a>
            </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("<h2 style='text-align: center; font-size: 3rem; margin-bottom: 30px;'>Iniciar sesión</h2>", unsafe_allow_html=True)
        
        if not st.session_state['mostrar_registro']:
            email_login = st.text_input("Dirección de correo electrónico")
            clave_login = st.text_input("Contraseña", type="password")
            st.checkbox("Acuérdate de mí")
            
            if st.button("Inicia sesión ahora"):
                if verificar_usuario(email_login, clave_login):
                    st.session_state['autenticado'] = True
                    st.session_state['usuario_actual'] = email_login
                    st.rerun()
                else:
                    st.error("Error. Si no tienes cuenta, regístrate abajo.")
            
            st.write("---")
            if st.button("¿No tienes cuenta? Regístrate aquí"):
                st.session_state['mostrar_registro'] = True
                st.rerun()
                
            # Documentos Legales Expansibles
            with st.expander("Términos de Servicio y Privacidad"):
                st.write("**Términos de Servicio:** Esta plataforma es de uso exclusivo para la gestión de la obra en Ayacucho. Todos los datos ingresados son confidenciales.")
                st.write("**Política de Privacidad:** Los correos y contraseñas registrados se almacenan de forma local y encriptada (SHA-256). No compartimos información con terceros.")
                
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
# 4. DASHBOARD ESTILO POWER BI 
# ==========================================
# Forzamos fondo gris claro para gráficos nítidos
st.markdown("""
    <style>
    .stApp { background-image: none !important; background-color: #f3f4f6 !important; }
    h1, h2, h3, p, label { color: #1f2937 !important; }
    div[data-testid="metric-container"] {
        background-color: white; border: 1px solid #e5e7eb; padding: 15px; border-radius: 8px;
    }
    /* Estilo del formulario de ingreso rápido para que resalte */
    .stForm { background-color: white; padding: 20px; border-radius: 8px; border: 1px solid #e5e7eb; }
    </style>
""", unsafe_allow_html=True)

st.title("📊 Panel Ejecutivo de Obra (Enchapado y Tarrajeo)")
st.write(f"Usuario: **{st.session_state['usuario_actual']}**")

# Tarjetas KPI (Primera Fila)
kpi1, kpi2, kpi3, kpi4 = st.columns(4)
with kpi1: st.metric(label="Presupuesto Base", value="S/ 15,000.00")
with kpi2: st.metric(label="Gasto Materiales", value="S/ 4,250.00", delta="- S/ 450.00", delta_color="inverse")
with kpi3: st.metric(label="Gasto Mano de Obra", value="S/ 1,800.00", delta="- S/ 300.00", delta_color="inverse")
with kpi4: st.metric(label="Saldo Restante", value="S/ 8,950.00", delta="59.6% disponible")

st.write("---")

# Segunda Fila: Gráfico Comparativo de Montaña y Formulario
col_graf_montana, col_form = st.columns([2.5, 1])

with col_graf_montana:
    st.subheader("📈 Evolución de Gastos (Materiales vs Mano de Obra)")
    
    # Datos simulados para el gráfico de montaña
    dias = ['Lun', 'Mar', 'Mie', 'Jue', 'Vie', 'Sab', 'Dom']
    gasto_mat = [1500, 800, 250, 400, 900, 300, 100]
    gasto_mo = [250, 250, 300, 250, 350, 400, 0]
    
    # Gráfico de líneas (Montaña) con Plotly Objects para mejor diseño
    fig_lineas = go.Figure()
    fig_lineas.add_trace(go.Scatter(x=dias, y=gasto_mat, mode='lines+markers', name='Materiales',
                                    line=dict(color='#0ea5e9', width=3),
                                    fill='tozeroy', fillcolor='rgba(14, 165, 233, 0.2)')) # Efecto montaña
    fig_lineas.add_trace(go.Scatter(x=dias, y=gasto_mo, mode='lines+markers', name='Mano de Obra',
                                    line=dict(color='#f59e0b', width=3),
                                    fill='tozeroy', fillcolor='rgba(245, 158, 11, 0.2)'))
    
    fig_lineas.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="white",
        hovermode="x unified", # Muestra todos los datos al pasar el mouse por un día
        margin=dict(l=20, r=20, t=30, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig_lineas, use_container_width=True)

with col_form:
    st.subheader("📝 Ingreso Rápido")
    seleccion = st.radio("Registrar:", ["Trabajador", "Insumos"], horizontal=True)
    
    if seleccion == "Trabajador":
        with st.form("form_personal"):
            st.date_input("Fecha", date.today())
            st.text_input("Nombre / Cargo")
            st.selectbox("Frente", ["2do Piso (Enchapado/Pintura)", "3er Piso (Tarrajeo)"])
            st.number_input("Jornal Diario (S/)", min_value=0.0)
            if st.form_submit_button("Guardar Registro", use_container_width=True): 
                st.success("Guardado.")
    else:
        with st.form("form_materiales"):
            st.date_input("Fecha", date.today())
            st.selectbox("Material", ["Cemento", "Cerámico 60x60", "Pegamento", "Pintura", "Sikaflex", "Otros"])
            st.number_input("Costo (S/)", min_value=0.0)
            if st.form_submit_button("Guardar Compra", use_container_width=True): 
                st.success("Guardado.")

# Tercera Fila: Mapa de Calor (Calendario) para vista general
st.write("---")
st.subheader("📅 Mapa de Intensidad (Vista Mensual)")
# Datos simulados para el calendario
fechas = pd.date_range(start='2026-09-01', end='2026-09-30')
df_cal = pd.DataFrame({'Fecha': fechas})
import random
df_cal['Gasto'] = [random.choice([0, 150, 300, 450, 0, 80, 0]) for _ in range(len(fechas))]
df_cal['Semana'] = df_cal['Fecha'].dt.isocalendar().week
df_cal['Día'] = df_cal['Fecha'].dt.day_name()

fig_cal = px.density_heatmap(
    df_cal, x="Semana", y="Día", z="Gasto",
    color_continuous_scale="Teal",
    labels={'Semana': 'Sem. del Año', 'Día': 'Día', 'Gasto': 'Gasto S/'}
)
fig_cal.update_yaxes(categoryorder='array', categoryarray=['Sunday', 'Saturday', 'Friday', 'Thursday', 'Wednesday', 'Tuesday', 'Monday'])
fig_cal.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=300)
st.plotly_chart(fig_cal, use_container_width=True)
