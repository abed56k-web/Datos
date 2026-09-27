import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, timedelta
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

# Variables de estado
if 'autenticado' not in st.session_state: st.session_state['autenticado'] = False
if 'mostrar_registro' not in st.session_state: st.session_state['mostrar_registro'] = False
if 'partida_actual' not in st.session_state: st.session_state['partida_actual'] = None
# Lista de partidas guardadas en memoria
if 'lista_partidas' not in st.session_state: 
    st.session_state['lista_partidas'] = ["Acabados 2do Nivel", "Tarrajeo 3er Nivel"]

# ==========================================
# 3. ESTILOS FUTURISTAS NEÓN (Para toda la app)
# ==========================================
st.markdown("""
    <style>
    /* Fondo oscuro futurista */
    .stApp { background-color: #0f172a !important; color: #e2e8f0 !important; }
    h1, h2, h3, p, label, span { color: #e2e8f0 !important; }
    
    /* Cajas y tarjetas con bordes neón */
    div[data-testid="metric-container"] {
        background-color: #1e293b; border: 1px solid #38bdf8; padding: 15px; 
        border-radius: 12px; box-shadow: 0 0 10px rgba(56, 189, 248, 0.2);
    }
    
    /* Botones estilo Cyber */
    div[data-testid="stButton"] button {
        background: linear-gradient(90deg, #06b6d4 0%, #3b82f6 100%) !important;
        color: white !important; border: none !important; border-radius: 8px;
        font-weight: bold; letter-spacing: 1px; transition: 0.3s;
    }
    div[data-testid="stButton"] button:hover {
        box-shadow: 0 0 15px rgba(6, 182, 212, 0.6); transform: scale(1.02);
    }
    
    /* Inputs amigables y visibles */
    .stTextInput input, .stNumberInput input, .stSelectbox div { 
        background-color: #1e293b !important; color: #38bdf8 !important; border: 1px solid #475569; 
    }
    
    /* Redes sociales */
    .social-container img { width: 32px; height: 32px; margin-right: 15px; filter: drop-shadow(0 0 5px #38bdf8); transition: 0.3s; }
    .social-container img:hover { transform: translateY(-3px); }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 4. PANTALLA DE INICIO (LOGIN)
# ==========================================
if not st.session_state['autenticado']:
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
            else:
                st.warning("Escribe un nombre primero.")
    st.stop()

# ==========================================
# 6. DASHBOARD FUTURISTA DE LA PARTIDA
# ==========================================
col_top1, col_top2 = st.columns([4, 1])
with col_top1:
    st.markdown(f"<h2 style='color: #a855f7 !important;'>📍 Modulo: {st.session_state['partida_actual']}</h2>", unsafe_allow_html=True)
with col_top2:
    st.write("") 
    if st.button("⬅️ Volver a Partidas"):
        st.session_state['partida_actual'] = None
        st.rerun()

st.write("---")

# Gráfico de Dona Neón y Formularios Separados
col_graf, col_form = st.columns([1.2, 1])

with col_graf:
    st.subheader("💰 Distribución de Presupuesto")
    labels = ['Materiales', 'Mano de Obra', 'Saldo/Utilidad']
    values = [4250, 1800, 8950]
    colores = ['#06b6d4', '#f59e0b', '#10b981'] # Cyan, Naranja, Verde Neón
    
    fig_dona = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.6, marker_colors=colores)])
    fig_dona.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(t=10, b=10, l=0, r=0),
        legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5, font=dict(color="white"))
    )
    fig_dona.update_traces(hoverinfo='label+value', textinfo='percent', textfont_color='white', marker=dict(line=dict(color='#0f172a', width=3)))
    st.plotly_chart(fig_dona, use_container_width=True)

with col_form:
    st.subheader("📝 Centro de Registro")
    # PESTAÑAS PARA SEPARAR MATERIALES Y MANO DE OBRA
    tab_mat, tab_mo = st.tabs(["📦 Ingresar Materiales", "👷 Registrar Actividad"])
    
    with tab_mat:
        with st.form("form_materiales"):
            st.date_input("Fecha", date.today(), key="f1")
            mat_nombre = st.text_input("Material / Insumo (Ej. Cemento)")
            col_m1, col_m2 = st.columns(2)
            with col_m1: cant = st.number_input("Cantidad", min_value=1.0, value=1.0)
            with col_m2: pre = st.number_input("Precio Unitario (S/)", min_value=0.0)
            st.info(f"Total Calculado: S/ {cant * pre:.2f}")
            if st.form_submit_button("Guardar Material", use_container_width=True): st.success("Guardado.")
            
    with tab_mo:
        with st.form("form_mano_obra"):
            st.date_input("Fecha", date.today(), key="f2")
            st.text_input("Nombre del Trabajador")
            st.text_area("Actividad realizada / Comentarios", placeholder="Ej. Tarrajeo de muro norte. Llegó 1 hora tarde.")
            # No pedimos jornal aquí, se negocia abajo
            if st.form_submit_button("Guardar Actividad", use_container_width=True): st.success("Actividad registrada.")

st.write("---")

# ==========================================
# 7. ALMANAQUE DE ASISTENCIA (30 DÍAS)
# ==========================================
st.subheader("📅 Almanaque de Asistencia Mensual")
st.write("Visualiza rápidamente el estado del personal (Verde: Asistió | Amarillo: Medio Día/Tarde | Rojo: Falta)")

# Generar datos simulados para un mes (30 días) para 3 trabajadores
dias_mes = pd.date_range(start='2026-09-01', end='2026-09-30')
datos_asistencia = []
trabajadores = ["Juan Pérez", "Luis Gómez", "Carlos Ruiz"]

for t in trabajadores:
    for d in dias_mes:
        estado = random.choices(["Asistió", "Medio Día", "Falta"], weights=[70, 20, 10])[0]
        datos_asistencia.append({"Trabajador": t, "Día": d.day, "Estado": estado})

df_alm = pd.DataFrame(datos_asistencia)

# Crear el Almanaque tipo Scatter Plot (Matriz)
fig_alm = px.scatter(df_alm, x="Día", y="Trabajador", color="Estado", 
                     color_discrete_map={"Asistió": "#10b981", "Medio Día": "#eab308", "Falta": "#ef4444"},
                     size_max=15)
fig_alm.update_traces(marker=dict(size=14, symbol="square", line=dict(width=1, color="white")))
fig_alm.update_layout(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    xaxis=dict(tickmode='linear', tick0=1, dtick=1, title="Días del Mes", gridcolor="#334155"),
    yaxis=dict(title="", gridcolor="#334155"), font=dict(color="#e2e8f0")
)
st.plotly_chart(fig_alm, use_container_width=True)

st.write("---")

# ==========================================
# 8. PLANILLA Y NEGOCIACIÓN DE JORNALES
# ==========================================
st.subheader("🤝 Planilla de Negociación Semanal")
st.write("Ingresa los días trabajados y **evalúa/negocia el jornal final**. El sistema calculará automáticamente el pago.")

# Tabla editable donde el usuario SÍ pone el jornal a negociar
df_planilla = pd.DataFrame({
    "Trabajador": ["Juan Pérez (Operario)", "Luis Gómez (Ayudante)", "Carlos Ruiz (Pintor)", ""],
    "Días Completos": [5, 4, 4, 0],
    "Medios Días": [1, 0, 2, 0],
    "Jornal Negociado (S/)": [80.0, 50.0, 90.0, 0.0]
})

df_editado = st.data_editor(df_planilla, num_rows="dynamic", use_container_width=True, hide_index=True)

# Cálculo automático estilo recibo
st.markdown("<div style='background-color: #1e293b; padding: 20px; border-radius: 10px; border-left: 5px solid #a855f7;'>", unsafe_allow_html=True)
st.markdown("#### 🧾 Resumen de Pagos a Realizar")
total_obra = 0
for index, row in df_editado.iterrows():
    if row["Trabajador"]:
        # Medio día se cuenta como 0.5 del jornal
        pago_total = (row["Días Completos"] + (row["Medios Días"] * 0.5)) * row["Jornal Negociado (S/)"]
        total_obra += pago_total
        st.markdown(f"**{row['Trabajador']}**: {row['Días Completos']} días enteros + {row['Medios Días']} medios días a S/{row['Jornal Negociado (S/)']} = **<span style='color:#38bdf8;'>S/ {pago_total:.2f}</span>**", unsafe_allow_html=True)
st.markdown(f"<h3 style='color: #10b981 !important;'>Total a desembolsar: S/ {total_obra:.2f}</h3>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)
