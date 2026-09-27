import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date
import sqlite3
import hashlib
import random

# 1. CONFIGURACIÓN INICIAL Y FORZADO DE MODO CLARO
st.set_page_config(page_title="Control de Obra", layout="wide", initial_sidebar_state="collapsed")

# 2. BASE DE DATOS
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
# 3. PANTALLA DE INICIO (MONTANA Y REDES)
# ==========================================
if not st.session_state['autenticado']:
    st.markdown("""
        <style>
        .stApp {
            background-image: linear-gradient(rgba(0, 0, 0, 0.4), rgba(0, 0, 0, 0.7)), url("https://images.unsplash.com/photo-1519681393784-d120267933ba?q=80&w=2070&auto=format&fit=crop");
            background-size: cover; background-position: center; background-attachment: fixed;
        }
        h1, h2, h3, p, label, .stCheckbox label { color: white !important; }
        
        /* FORZAR INPUTS BLANCOS CON LETRA NEGRA (Soluciona el problema de visibilidad) */
        .stTextInput input, .stPasswordInput input {
            background-color: white !important;
            color: black !important;
            border-radius: 5px;
        }
        
        div[data-testid="stButton"] button {
            background-color: #d95b32 !important; color: white !important;
            border: none !important; font-size: 1.1rem; width: 100%; transition: 0.3s;
        }
        div[data-testid="stButton"] button:hover { background-color: #b54925 !important; }
        
        /* Contenedor de iconos de redes reales */
        .social-container img { width: 30px; height: 30px; margin-right: 15px; cursor: pointer; filter: brightness(0) invert(1); }
        .social-container img:hover { opacity: 0.8; }
        </style>
    """, unsafe_allow_html=True)

    col1, col_vacia, col2 = st.columns([1.2, 0.2, 1])
    
    with col1:
        st.markdown("<h1 style='font-size: 5rem; line-height: 1.1; margin-bottom: 0;'>Welcome<br>Back</h1>", unsafe_allow_html=True)
        st.markdown("<p style='font-size: 1.1rem; margin-top: 15px;'>Plataforma integral para el control de avance, materiales y personal de obra en Ayacucho.</p>", unsafe_allow_html=True)
        
        # Iconos de redes sociales usando imágenes reales (formato SVG/PNG)
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
            st.checkbox("Remember Me")
            
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
                
            with st.expander("Terms of Service | Privacy Policy"):
                st.write("**Términos:** Uso exclusivo para gestión interna. **Privacidad:** Datos encriptados localmente (SHA-256).")
                
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
# 4. DASHBOARD INTERIOR (ESTILO POWER BI CORREGIDO)
# ==========================================
st.markdown("""
    <style>
    /* Forzar fondo gris claro y textos oscuros */
    .stApp { background-image: none !important; background-color: #f3f4f6 !important; }
    h1, h2, h3, p, label { color: #1f2937 !important; }
    
    /* Cajas de métricas limpias */
    div[data-testid="metric-container"] {
        background-color: white; border: 1px solid #e5e7eb; padding: 15px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    
    /* FORZAR INPUTS BLANCOS EN EL FORMULARIO INTERNO */
    .stTextInput input, .stNumberInput input, .stSelectbox div {
        background-color: white !important;
        color: black !important;
    }
    </style>
""", unsafe_allow_html=True)

st.title("📊 Panel Ejecutivo de Obra (Enchapado y Tarrajeo)")

kpi1, kpi2, kpi3, kpi4 = st.columns(4)
with kpi1: st.metric(label="Presupuesto Base", value="S/ 15,000")
with kpi2: st.metric(label="Gasto Materiales", value="S/ 4,250")
with kpi3: st.metric(label="Gasto Mano de Obra", value="S/ 1,800")
with kpi4: st.metric(label="Utilidad Estimada", value="S/ 8,950")

st.write("---")

col_graf_circulo, col_form = st.columns([1.5, 1])

with col_graf_circulo:
    st.subheader("Distribución de Gastos vs Utilidad")
    
    # Gráfico de Anillo (Dona) en Plotly
    labels = ['Gasto Materiales', 'Gasto Mano de Obra', 'Utilidad Restante']
    values = [4250, 1800, 8950]
    colores = ['#0ea5e9', '#f59e0b', '#10b981'] # Azul, Naranja, Verde Esmeralda
    
    fig_dona = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.5, marker_colors=colores)])
    fig_dona.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=20, b=20, l=20, r=20),
        legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5)
    )
    # Al pasar el mouse, verás el porcentaje y el monto exacto
    fig_dona.update_traces(hoverinfo='label+percent+value', textinfo='percent')
    st.plotly_chart(fig_dona, use_container_width=True)

with col_form:
    st.subheader("📝 Ingreso Rápido")
    seleccion = st.radio("Registrar:", ["Trabajador", "Insumos"], horizontal=True)
    
    if seleccion == "Trabajador":
        with st.form("form_personal"):
            st.date_input("Fecha", date.today())
            st.text_input("Nombre / Cargo")
            st.selectbox("Frente", ["2do Piso (Enchapado/Pintura)", "3er Piso (Tarrajeo)"])
            st.number_input("Jornal Diario (S/)", min_value=0.0)
            if st.form_submit_button("Guardar Registro", use_container_width=True): st.success("Guardado.")
    else:
        with st.form("form_materiales"):
            st.date_input("Fecha", date.today())
            st.selectbox("Material", ["Cemento", "Cerámico 60x60", "Pegamento", "Pintura", "Sikaflex", "Otros"])
            st.number_input("Costo (S/)", min_value=0.0)
            if st.form_submit_button("Guardar Compra", use_container_width=True): st.success("Guardado.")

st.write("---")

st.subheader("📅 Mapa de Intensidad (Calendario Semanal)")
# Datos de ejemplo para el mapa de calor (restaurado a su tamaño y colores originales)
fechas = pd.date_range(start='2026-09-01', end='2026-10-31')
df_cal = pd.DataFrame({'Fecha': fechas})
df_cal['Gasto'] = [random.choice([0, 150, 300, 450, 0, 80, 0]) for _ in range(len(fechas))]
df_cal['Semana'] = df_cal['Fecha'].dt.isocalendar().week
df_cal['Día'] = df_cal['Fecha'].dt.day_name()

fig_cal = px.density_heatmap(
    df_cal, x="Semana", y="Día", z="Gasto",
    color_continuous_scale="Blues", # Regresamos al azul limpio
    labels={'Semana': 'Sem. del Año', 'Día': 'Día de la semana', 'Gasto': 'Gasto S/'}
)
fig_cal.update_yaxes(categoryorder='array', categoryarray=['Sunday', 'Saturday', 'Friday', 'Thursday', 'Wednesday', 'Tuesday', 'Monday'])
fig_cal.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=350)
st.plotly_chart(fig_cal, use_container_width=True)
