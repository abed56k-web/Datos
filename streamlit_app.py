import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date
import sqlite3
import hashlib
import random

# 1. CONFIGURACIÓN INICIAL (Fondo 100% Blanco)
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

# Variables de estado
if 'autenticado' not in st.session_state: st.session_state['autenticado'] = False
if 'mostrar_registro' not in st.session_state: st.session_state['mostrar_registro'] = False
if 'partida_actual' not in st.session_state: st.session_state['partida_actual'] = None

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
# 4. PANTALLA DE SELECCIÓN DE PARTIDA
# ==========================================
# Forzar fondo blanco y letras negras para todo el interior
st.markdown("""
    <style>
    .stApp { background-image: none !important; background-color: #ffffff !important; }
    h1, h2, h3, p, label, span, div { color: #000000 !important; }
    .stTextInput input, .stNumberInput input, .stTextArea textarea, .stSelectbox div { 
        background-color: #f8fafc !important; color: black !important; border: 1px solid #cbd5e1; 
    }
    div[data-testid="metric-container"] {
        background-color: white; border: 1px solid #e5e7eb; padding: 15px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    </style>
""", unsafe_allow_html=True)

if st.session_state['partida_actual'] is None:
    st.title("🏗️ Selecciona el Frente de Trabajo")
    st.write("¿A qué área de la obra deseas hacerle seguimiento hoy?")
    
    col_sel1, col_sel2, col_sel3 = st.columns([1,2,1])
    with col_sel2:
        partida_seleccionada = st.selectbox("Lista de Partidas Activas:", 
                                            ["Acabados 2do Nivel (Enchapado y Pintura)", 
                                             "Tarrajeo 3er Nivel", 
                                             "Instalaciones Eléctricas / Sanitarias"])
        if st.button("Ingresar al Panel ➡️", use_container_width=True):
            st.session_state['partida_actual'] = partida_seleccionada
            st.rerun()
    st.stop()

# ==========================================
# 5. DASHBOARD DE LA PARTIDA SELECCIONADA
# ==========================================
col_top1, col_top2 = st.columns([4, 1])
with col_top1:
    st.title(f"📊 Panel: {st.session_state['partida_actual']}")
with col_top2:
    st.write("") # Espaciador
    if st.button("⬅️ Cambiar de Partida"):
        st.session_state['partida_actual'] = None
        st.rerun()

st.write("---")

# Gráfico de Dona y Formulario Compacto
col_graf, col_form = st.columns([1.2, 1])

with col_graf:
    st.subheader("Distribución de Presupuesto")
    labels = ['Gasto Materiales', 'Gasto Mano de Obra', 'Utilidad / Saldo']
    values = [4250, 1800, 8950]
    colores = ['#0ea5e9', '#f59e0b', '#10b981']
    
    fig_dona = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.5, marker_colors=colores)])
    fig_dona.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(t=20, b=20, l=0, r=0),
        legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5),
        font=dict(color="black") # Letras negras forzadas
    )
    fig_dona.update_traces(hoverinfo='label+value', textinfo='percent', textfont_color='black')
    st.plotly_chart(fig_dona, use_container_width=True)

with col_form:
    st.subheader("📝 Ingreso de Actividades")
    with st.form("form_compacto"):
        # Cajas divididas en columnas para que no sean tan largas
        f_col1, f_col2 = st.columns(2)
        with f_col1:
            st.date_input("Fecha", date.today())
            st.selectbox("Tipo", ["Material / Insumo", "Mano de Obra", "Herramientas"])
        with f_col2:
            st.text_input("Nombre (Corto)")
            st.number_input("Costo / Jornal (S/)", min_value=0.0)
            
        st.text_input("Comentarios / Observaciones (Opcional)", placeholder="Ej. Juan llegó 1 hr tarde...")
        if st.form_submit_button("Guardar en esta Partida", use_container_width=True): 
            st.success("Dato registrado correctamente.")

st.write("---")

# ==========================================
# 6. CUADRO DE ASISTENCIA Y METRADOS (Tablas)
# ==========================================
st.subheader("🗓️ Control Semanal de Jornales (Estilo Calendario)")
st.write("Marca los días trabajados. El 'Total Pago' se calcula automáticamente (Días marcados × Jornal).")

# Datos de ejemplo para la tabla interactiva
df_asistencia = pd.DataFrame({
    "Trabajador / Cargo": ["Juan Pérez (Operario)", "Luis Gómez (Ayudante)", "Carlos Ruiz (Pintor)"],
    "Lun": [True, True, False], "Mar": [True, False, False], "Mie": [True, True, True],
    "Jue": [True, True, True], "Vie": [True, True, True], "Sab": [True, False, True],
    "Jornal Diario (S/)": [80.0, 50.0, 90.0]
})

# El usuario puede editar esta tabla directamente en la pantalla
df_editado = st.data_editor(df_asistencia, num_rows="dynamic", use_container_width=True, hide_index=True)

# Cálculo automático y mostrar el resultado en una tarjeta limpia
st.write("**Resumen de Planilla a Pagar esta Semana:**")
for index, row in df_editado.iterrows():
    if row["Trabajador / Cargo"]: # Si no está vacío
        dias_trabajados = sum([row["Lun"], row["Mar"], row["Mie"], row["Jue"], row["Vie"], row["Sab"]])
        pago_total = dias_trabajados * row["Jornal Diario (S/)"]
        st.markdown(f"- **{row['Trabajador / Cargo']}**: Trabajó {dias_trabajados} días. Total a pagar: **S/ {pago_total:.2f}**")

st.write("---")

st.subheader("📦 Metrado General Consolidado (Materiales)")
# Tabla de resumen de materiales idéntica a tu imagen
df_materiales = pd.DataFrame({
    "MATERIAL / INSUMO": ["Agua m3", "Arena Gruesa m3", "Cemento 42.5kg", "Ladrillo de Techo und.", "Piedra 1/2\" m3"],
    "UND": ["m3", "m3", "bls", "und", "m3"],
    "CANTIDAD": [3.54, 9.88, 184.93, 519.00, 10.07],
    "P. UNITARIO": [1.50, 50.00, 27.00, 2.20, 60.00]
})
# Multiplicación automática para el parcial
df_materiales["PARCIAL (S/.)"] = (df_materiales["CANTIDAD"] * df_materiales["P. UNITARIO"]).round(2)

# Mostrar la tabla formateada
st.dataframe(df_materiales, use_container_width=True, hide_index=True)
