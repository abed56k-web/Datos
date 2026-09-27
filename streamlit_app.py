import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date
import random
import sqlite3
import hashlib

# 1. CONFIGURACIÓN INICIAL
st.set_page_config(page_title="Control de Obra", layout="wide", initial_sidebar_state="collapsed")

# 2. CONFIGURACIÓN DE LA BASE DE DATOS DE USUARIOS
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

# Inicializar variables de sesión
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False
if 'mostrar_registro' not in st.session_state:
    st.session_state['mostrar_registro'] = False

# ==========================================
# 3. PANTALLA DE INICIO (ESTILO MONTAÑA NEVADA)
# ==========================================
if not st.session_state['autenticado']:
    
    # CSS Específico para la pantalla de inicio (Fondo de montaña, textos blancos, botón naranja)
    st.markdown("""
        <style>
        /* Imagen de fondo de montaña nevada (puedes cambiar la URL por tu propia imagen) */
        .stApp {
            background-image: linear-gradient(rgba(0, 0, 0, 0.4), rgba(0, 0, 0, 0.7)), url("https://images.unsplash.com/photo-1519681393784-d120267933ba?q=80&w=2070&auto=format&fit=crop");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }
        /* Ocultar barra superior */
        header {visibility: hidden;}
        /* Estilos de texto globales para el login */
        h1, h2, h3, p, label, .stCheckbox label {
            color: white !important;
        }
        /* Forzar los cuadros de texto a ser blancos con letra negra, igual a la imagen */
        div[data-baseweb="input"] > div {
            background-color: white !important;
            border-radius: 4px;
        }
        input {
            color: black !important;
            font-weight: 500;
        }
        /* Estilo del botón naranja principal */
        div[data-testid="stButton"] button {
            background-color: #d95b32 !important;
            color: white !important;
            border: none !important;
            padding: 0.5rem 1rem;
            font-size: 1.1rem;
            width: 100%;
            transition: 0.3s;
        }
        div[data-testid="stButton"] button:hover {
            background-color: #b54925 !important;
        }
        /* Reducir espacio superior */
        .block-container {
            padding-top: 5rem !important;
        }
        </style>
    """, unsafe_allow_html=True)

    # Estructura de Columnas
    col1, col_vacia, col2 = st.columns([1.2, 0.2, 1])
    
    with col1:
        st.markdown("<h1 style='font-size: 5rem; line-height: 1.1; margin-bottom: 0;'>Welcome<br>Back</h1>", unsafe_allow_html=True)
        st.markdown("<p style='font-size: 1.1rem; margin-top: 15px; color: #e5e7eb !important;'>It is a long established fact that a reader will be distracted by the readable content of a page when looking at its layout. The point of using...</p>", unsafe_allow_html=True)
        st.markdown("🌐 🐦 📸 🎥", unsafe_allow_html=True) # Iconos sociales de prueba

    with col2:
        st.markdown("<h2 style='text-align: center; font-size: 3rem; margin-bottom: 30px;'>Sign in</h2>", unsafe_allow_html=True)
        
        if not st.session_state['mostrar_registro']:
            # Formulario de INGRESO
            email_login = st.text_input("Email Address")
            clave_login = st.text_input("Password", type="password")
            st.checkbox("Remember Me")
            
            if st.button("Sign in now"):
                if verificar_usuario(email_login, clave_login):
                    st.session_state['autenticado'] = True
                    st.session_state['usuario_actual'] = email_login
                    st.rerun()
                else:
                    st.error("Correo o contraseña incorrectos. Si eres nuevo, regístrate abajo.")
            
            # Botón para cambiar a registro
            st.write("---")
            if st.button("¿No tienes cuenta? Regístrate aquí"):
                st.session_state['mostrar_registro'] = True
                st.rerun()
                
        else:
            # Formulario de REGISTRO (Crear Usuario)
            st.markdown("<p style='text-align: center;'><b>Crea tu nueva cuenta de obra</b></p>", unsafe_allow_html=True)
            email_reg = st.text_input("Nuevo Email")
            clave_reg = st.text_input("Crear Password", type="password")
            
            if st.button("Crear cuenta y Guardar"):
                if email_reg and clave_reg:
                    agregar_usuario(email_reg, clave_reg)
                    st.success("¡Cuenta creada con éxito!")
                    st.session_state['mostrar_registro'] = False
                    st.rerun()
                else:
                    st.warning("Llena ambos campos.")
            
            if st.button("Volver al inicio de sesión"):
                st.session_state['mostrar_registro'] = False
                st.rerun()

    st.stop() # Detiene el código aquí para que no se vea el dashboard

# ==========================================
# 4. DASHBOARD ESTILO POWER BI (Después de ingresar)
# ==========================================
# CSS para sobreescribir la montaña y poner el fondo claro del Dashboard
st.markdown("""
    <style>
    .stApp {
        background-image: none !important;
        background-color: #f3f4f6 !important;
    }
    h1, h2, h3, p, label {
        color: #1f2937 !important;
    }
    div[data-testid="metric-container"] {
        background-color: white;
        border: 1px solid #e5e7eb;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    </style>
""", unsafe_allow_html=True)

st.title(f"📊 Control de Obra: Enchapado y Tarrajeo")
st.write(f"Conectado como: **{st.session_state['usuario_actual']}**")

# Tarjetas KPI
kpi1, kpi2, kpi3, kpi4 = st.columns(4)
with kpi1: st.metric(label="Presupuesto Total", value="S/ 15,000")
with kpi2: st.metric(label="Gasto en Materiales", value="S/ 4,250", delta="-S/ 450")
with kpi3: st.metric(label="Gasto Mano de Obra", value="S/ 1,800", delta="-S/ 300")
with kpi4: st.metric(label="Saldo Disponible", value="S/ 8,950")

st.write("---")

col_grafico, col_formularios = st.columns([2, 1])

with col_grafico:
    st.subheader("📅 Calendario de Inversión Diaria")
    # Generamos datos de ejemplo para el calendario
    fechas = pd.date_range(start='2026-09-01', end='2026-10-31')
    datos_calendario = pd.DataFrame({'Fecha': fechas})
    datos_calendario['Gasto_Diario'] = [random.choice([0, 150, 300, 450, 0, 80, 0]) for _ in range(len(fechas))]
    datos_calendario['Semana'] = datos_calendario['Fecha'].dt.isocalendar().week
    datos_calendario['Dia_Semana'] = datos_calendario['Fecha'].dt.day_name()
    
    fig = px.density_heatmap(
        datos_calendario, x="Semana", y="Dia_Semana", z="Gasto_Diario",
        color_continuous_scale="Blues", 
        labels={'Semana': 'Semana del Año', 'Dia_Semana': 'Día', 'Gasto_Diario': 'Gasto Total (S/)'}
    )
    fig.update_yaxes(categoryorder='array', categoryarray=['Sunday', 'Saturday', 'Friday', 'Thursday', 'Wednesday', 'Tuesday', 'Monday'])
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#1f2937"))
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
            if st.form_submit_button("Guardar Jornal"): st.success("Guardado exitosamente.")
            
    else:
        with st.form("form_materiales"):
            fecha_m = st.date_input("Fecha", date.today())
            material = st.selectbox("Insumo", ["Cemento", "Cerámicos 60x60", "Pegamento", "Pintura", "Sikaflex-11 FC"])
            costo = st.number_input("Costo Total (S/)", min_value=0.0)
            if st.form_submit_button("Guardar Compra"): st.success("Guardado exitosamente.")
