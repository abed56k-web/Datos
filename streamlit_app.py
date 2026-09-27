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
conn = sqlite3.connect('obra_nexus.db', check_same_thread=False)
c = conn.cursor()

c.execute('CREATE TABLE IF NOT EXISTS usuarios (email TEXT UNIQUE, password TEXT)')
c.execute('CREATE TABLE IF NOT EXISTS personal (partida TEXT, nombre TEXT, especialidad TEXT)')
c.execute('CREATE TABLE IF NOT EXISTS materiales (partida TEXT, fecha TEXT, insumo TEXT, und TEXT, cantidad REAL, precio REAL)')
c.execute('CREATE TABLE IF NOT EXISTS asistencia (partida TEXT, trabajador TEXT, fecha TEXT, estado TEXT, almuerzo TEXT, UNIQUE(partida, trabajador, fecha))')
c.execute('CREATE TABLE IF NOT EXISTS saldos_trabajadores (partida TEXT, trabajador TEXT, saldo REAL)')
conn.commit()

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
if 'cal_mes' not in st.session_state: st.session_state['cal_mes'] = 9 
if 'cal_ano' not in st.session_state: st.session_state['cal_ano'] = 2026

if 'presupuesto_total' not in st.session_state: st.session_state['presupuesto_total'] = 17000.00
if 'presupuesto_mo' not in st.session_state: st.session_state['presupuesto_mo'] = 5000.00
if 'presupuesto_mat' not in st.session_state: st.session_state['presupuesto_mat'] = 12000.00

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
    modo_ingreso = st.radio("Método de cálculo:", ["Suma Automática (Materiales + Mano de Obra)", "Ingreso Directo del Total"], horizontal=True)
    
    if modo_ingreso == "Suma Automática (Materiales + Mano de Obra)":
        col_b1, col_b2 = st.columns(2)
        with col_b1:
            st.session_state['presupuesto_mat'] = st.number_input("Presupuesto Materiales (S/)", value=st.session_state['presupuesto_mat'], step=500.0)
        with col_b2:
            st.session_state['presupuesto_mo'] = st.number_input("Presupuesto Mano de Obra (S/)", value=st.session_state['presupuesto_mo'], step=500.0)
        st.session_state['presupuesto_total'] = st.session_state['presupuesto_mat'] + st.session_state['presupuesto_mo']
        st.markdown(f"### 💡 Presupuesto Total Calculado: <span style='color:#38bdf8;'>S/ {st.session_state['presupuesto_total']:,.2f}</span>", unsafe_allow_html=True)
    else:
        st.session_state['presupuesto_total'] = st.number_input("Presupuesto Total Directo (S/)", value=st.session_state['presupuesto_total'], step=1000.0)

st.write("---")

df_personal_db = pd.read_sql(f"SELECT * FROM personal WHERE partida='{st.session_state['partida_actual']}'", conn)
lista_trabajadores_db = df_personal_db['nombre'].tolist() if not df_personal_db.empty else ["Grover", "Juan Pérez"]

col_form, col_graf_circulo, col_graf_linea = st.columns([1, 1, 1])

with col_form:
    st.subheader("📝 Centro de Registro")
    tab_mat, tab_pers, tab_mo = st.tabs(["📦 Ingresar Materiales", "👤 Registrar Personal", "👷 Registrar Asistencia"])
    
    with tab_mat:
        with st.form("form_materiales"):
            f_mat = st.date_input("Fecha", date.today(), key="f1")
            mat_nom = st.text_input("Material / Insumo (Ej. Cemento Portland)")
            
            tipo_und = st.selectbox("Unidad de Medida (Norma Peruana)", ["bol (Bolsas)", "m3 (Metro cúbico)", "m2 (Metro cuadrado)", "kg (Kilogramo)", "und (Unidad)", "gln (Galón)", "glb (Global)", "pza (Pieza)", "ml (Metro lineal)", "Otra unidad..."])
            und_final = tipo_und.split(" ")[0] if tipo_und != "Otra unidad..." else st.text_input("Especifique su unidad:")
            
            col_m1, col_m2 = st.columns(2)
            with col_m1: cant = st.number_input("Cantidad", min_value=0.01, value=1.0)
            with col_m2: pre = st.number_input("P. Unitario (S/)", min_value=0.0)
            st.info(f"Total: S/ {cant * pre:.2f}")
            
            if st.form_submit_button("Guardar Material", use_container_width=True):
                if mat_nom and und_final:
                    c.execute("INSERT INTO materiales VALUES (?, ?, ?, ?, ?, ?)", (st.session_state['partida_actual'], str(f_mat), mat_nom, und_final, cant, pre))
                    conn.commit()
                    st.success("Material guardado correctamente en la BD.")
                    st.rerun()
                else:
                    st.warning("Completa el nombre y la unidad del material.")
                    
    with tab_pers:
        with st.form("form_nuevo_personal"):
            st.write("Agrega nuevos obreros para que aparezcan en el menú desplegable.")
            nuevo_nombre = st.text_input("Nombre y Apellido del Trabajador")
            nueva_esp = st.selectbox("Especialidad", ["Operario", "Oficial", "Ayudante / Peón", "Pintor", "Enchapador", "Electricista", "Plomero"])
            
            if st.form_submit_button("Registrar Trabajador", use_container_width=True):
                if nuevo_nombre:
                    try:
                        c.execute("INSERT INTO personal VALUES (?, ?, ?)", (st.session_state['partida_actual'], nuevo_nombre, nueva_esp))
                        conn.commit()
                        st.success(f"¡Trabajador {nuevo_nombre} registrado con éxito!")
                        st.rerun()
                    except:
                        st.warning("Este trabajador ya está registrado en esta partida.")
                else:
                    st.warning("Escribe el nombre del trabajador.")

    with tab_mo:
        with st.form("form_mano_obra"):
            f_mo = st.date_input("Fecha", date.today(), key="f2")
            
            if lista_trabajadores_db:
                trabajador = st.selectbox("Seleccione Trabajador", lista_trabajadores_db)
            else:
                trabajador = st.text_input("Nombre del Trabajador (Registra arriba primero)")

            estado_asis = st.selectbox("Estado de Asistencia", ["Día Completo", "Medio Día", "Falta / Emergencia"])
            almuerzo_opc = st.radio("Almuerzo en Obra", ["No (Almuerza en casa)", "Sí (Se queda a almorzar)"], horizontal=True)
            actividad = st.text_area("Actividad / Observaciones", placeholder="Ej. Tarrajeo de muro norte.")
            
            if st.form_submit_button("Guardar Asistencia", use_container_width=True):
                if trabajador:
                    c.execute("INSERT OR REPLACE INTO asistencia VALUES (?, ?, ?, ?, ?)", (st.session_state['partida_actual'], trabajador, str(f_mo), estado_asis, almuerzo_opc))
                    conn.commit()
                    st.success("¡Asistencia guardada o actualizada correctamente en la BD!")
                    st.rerun()
                else:
                    st.warning("Selecciona o escribe un trabajador.")

# Consultar datos reales de la BD
df_mat_db = pd.read_sql(f"SELECT * FROM materiales WHERE partida='{st.session_state['partida_actual']}'", conn)
gasto_mat_real = (df_mat_db['cantidad'] * df_mat_db['precio']).sum() if not df_mat_db.empty else 0.0

df_asist_db = pd.read_sql(f"SELECT * FROM asistencia WHERE partida='{st.session_state['partida_actual']}'", conn)
trabajadores_registrados = lista_trabajadores_db

with col_graf_circulo:
    st.subheader("💰 Distribución")
    labels = ['Materiales', 'Mano de Obra', 'Saldo Restante']
    gasto_mo_simulado = 2500.0 
    values = [gasto_mat_real, gasto_mo_simulado, max(0, st.session_state['presupuesto_total'] - (gasto_mat_real + gasto_mo_simulado))] 
    colores = ['#06b6d4', '#f59e0b', '#10b981']
    
    fig_dona = go.Figure(data=[go.Pie(labels=labels, values=values, marker_colors=colores)])
    fig_dona.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(t=10, b=10, l=0, r=0),
        legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5, font=dict(color="white"))
    )
    fig_dona.update_traces(hoverinfo='label+value', textinfo='percent', textfont_color='white', marker=dict(line=dict(color='#0f172a', width=2)))
    st.plotly_chart(fig_dona, use_container_width=True)

with col_graf_linea:
    st.subheader("📈 Presupuesto vs Gasto")
    semanas_graf = ['Sem 1', 'Sem 2', 'Sem 3', 'Sem 4']
    pres_total_linea = [st.session_state['presupuesto_total']] * 4
    gasto_acumulado = [2000, 4500, 6800, gasto_mat_real + 2500] 
    
    fig_linea = go.Figure()
    fig_linea.add_trace(go.Scatter(x=semanas_graf, y=pres_total_linea, mode='lines', name='Presupuesto Total', line=dict(color='#10b981', dash='dash')))
    fig_linea.add_trace(go.Scatter(x=semanas_graf, y=gasto_acumulado, mode='lines+markers', name='Gasto Acumulado', line=dict(color='#ef4444', width=3)))
    
    fig_linea.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(t=10, b=10, l=0, r=0),
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5, font=dict(color="white")),
        font=dict(color="white")
    )
    st.plotly_chart(fig_linea, use_container_width=True)

st.write("---")

# ==========================================
# 7. ALMANAQUE INTERACTIVO CONECTADO A LA BD
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
if trabajadores_registrados:
    trabajador_seleccionado = st.selectbox("Seleccione Trabajador para ver su Almanaque:", trabajadores_registrados)
else:
    trabajador_seleccionado = st.selectbox("Seleccione Trabajador para ver su Almanaque:", ["Sin registros"])

col_cal, col_leyenda = st.columns([2.5, 1])

with col_cal:
    calendar.setfirstweekday(calendar.SUNDAY)
    mes_cal = calendar.monthcalendar(st.session_state['cal_ano'], st.session_state['cal_mes'])

    asistencia_trabajador = {}
    if not df_asist_db.empty and trabajador_seleccionado != "Sin registros":
        df_t = df_asist_db[(df_asist_db['trabajador'] == trabajador_seleccionado)]
        for _, row in df_t.iterrows():
            try:
                f_reg = date.fromisoformat(row['fecha'])
                if f_reg.year == st.session_state['cal_ano'] and f_reg.month == st.session_state['cal_mes']:
                    asistencia_trabajador[f_reg.day] = row['estado']
            except:
                pass

    html_cal = """
    <style>
    .cal-wrapper { background-color: #1e293b; border-radius: 12px; box-shadow: 0 0 10px rgba(56, 189, 248, 0.2); border: 1px solid #38bdf8; padding: clamp(10px, 3vw, 20px); width: 100%; box-sizing: border-box; overflow: hidden;}
    .cal-table { width: 100%; border-collapse: separate; border-spacing: clamp(2px, 1vw, 4px); text-align: center; font-family: sans-serif; table-layout: fixed;}
    .cal-table th { padding: clamp(5px, 1.5vw, 10px) 0; color: #94a3b8; font-weight: bold; font-size: clamp(0.8rem, 2.5vw, 1.1rem); }
    .cal-table td { padding: clamp(8px, 2vw, 15px) 0; border-radius: 4px; font-size: clamp(0.9rem, 3vw, 1.2rem); font-weight: bold; border: 1px solid #334155; }
    .cal-vacio { background-color: #1e293b; color: transparent !important; border: none !important; }
    .cal-futuro { background-color: #0f172a; color: #475569; }
    .cal-verde { background-color: #10b981; color: white !important; }
    .cal-amarillo { background-color: #f59e0b; color: white !important; }
    .cal-rojo { background-color: #ef4444; color: white !important; }
    </style>
    <div class="cal-wrapper"><table class="cal-table"><tr><th>D</th><th>L</th><th>M</th><th>M</th><th>J</th><th>V</th><th>S</th></tr>
    """
    for semana in mes_cal:
        html_cal += "<tr>"
        for dia in semana:
            if dia == 0: html_cal += "<td class='cal-vacio'>0</td>"
            else:
                clase = "cal-futuro"
                if dia in asistencia_trabajador:
                    est = asistencia_trabajador[dia]
                    if "Completo" in est: clase = "cal-verde"
                    elif "Medio" in est: clase = "cal-amarillo"
                    else: clase = "cal-rojo"
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
# 8. MÓDULOS SEMANALES CON CONTROL DE SALDOS SIMPLIFICADO
# ==========================================
st.markdown("<h2 style='color: #a855f7 !important;'>🗓️ Cierre y Reporte Semanal</h2>", unsafe_allow_html=True)
col_sem1, col_sem2 = st.columns(2)
with col_sem1: fecha_inicio = st.date_input("Inicio de la Semana", value=date(2026, 9, 14))
with col_sem2: fecha_fin = st.date_input("Fin de la Semana", value=date(2026, 9, 20))
st.markdown(f"**Filtrando transacciones del {fecha_inicio.strftime('%d/%m/%Y')} al {fecha_fin.strftime('%d/%m/%Y')}**")

tab_planilla, tab_materiales = st.tabs(["👷 Planilla de Mano de Obra (Semanal)", "📦 Control de Materiales (Semanal)"])

with tab_planilla:
    st.write("Cálculo automático de jornales basados estrictamente en el calendario registrado para cada trabajador.")

    gasto_semana_mo = 0

    if not df_asist_db.empty:
        df_asist_db['fecha_dt'] = pd.to_datetime(df_asist_db['fecha']).dt.date
        mask_asis = (df_asist_db['fecha_dt'] >= fecha_inicio) & (df_asist_db['fecha_dt'] <= fecha_fin) & (df_asist_db['partida'] == st.session_state['partida_actual'])
        df_asist_semana = df_asist_db.loc[mask_asis]
    else:
        df_asist_semana = pd.DataFrame(columns=['trabajador', 'fecha', 'estado', 'almuerzo'])

    for trabajador in trabajadores_registrados:
        df_t_sem = df_asist_semana[df_asist_semana['trabajador'] == trabajador] if not df_asist_semana.empty else pd.DataFrame()
        
        cant_completos = len(df_t_sem[df_t_sem['estado'] == 'Día Completo']) if not df_t_sem.empty else 0
        cant_medios = len(df_t_sem[df_t_sem['estado'] == 'Medio Día']) if not df_t_sem.empty else 0
        cant_faltas = len(df_t_sem[df_t_sem['estado'].str.contains('Falta|Emergencia', na=False)]) if not df_t_sem.empty else 0
        cant_almuerzos = len(df_t_sem[df_t_sem['almuerzo'].str.contains('Sí', na=False)]) if not df_t_sem.empty else 0

        st.markdown(f"""
            <div style="background-color: #1e293b; padding: 20px; border-radius: 12px; margin-bottom: 20px; border: 1px solid #38bdf8;">
                <h3 style="color: #38bdf8; margin-top: 0;">👷 {trabajador}</h3>
            </div>
        """, unsafe_allow_html=True)

        col_w1, col_w2 = st.columns(2)
        with col_w1:
            jornal_dia = st.number_input(f"Jornal Diario por Día (S/) - {trabajador}", value=80.0, step=10.0, key=f"jornal_{trabajador}")
            costo_almuerzo = st.number_input(f"Costo por Almuerzo (S/) - {trabajador}", value=7.0, step=1.0, key=f"alm_costo_{trabajador}")
            
        with col_w2:
            # Consultar saldo anterior en BD
            c.execute("SELECT saldo FROM saldos_trabajadores WHERE partida=? AND trabajador=?", (st.session_state['partida_actual'], trabajador))
            res_saldo = c.fetchone()
            saldo_anterior = res_saldo[0] if res_saldo else 0.0

            # Cuadro único y directo: +debe, -adelanto, 0 si ya se arregló
            nuevo_saldo = st.number_input(f"Saldo / Adelanto (S/) (+Debe / -Adelanto / 0=Arreglado) - {trabajador}", value=saldo_anterior, step=10.0, key=f"saldo_{trabajador}")
            if nuevo_saldo != saldo_anterior:
                c.execute("INSERT OR REPLACE INTO saldos_trabajadores VALUES (?, ?, ?)", (st.session_state['partida_actual'], trabajador, nuevo_saldo))
                conn.commit()

        pago_completos = cant_completos * jornal_dia
        pago_medios = cant_medios * (jornal_dia / 2.0)
        total_almuerzos = cant_almuerzos * costo_almuerzo
        total_trabajador = pago_completos + pago_medios + total_almuerzos + nuevo_saldo
        gasto_semana_mo += total_trabajador

        # Mostrar desglose idéntico al esquema dibujado
        st.markdown(f"""
            <div style="background-color: #0f172a; padding: 15px; border-radius: 8px; border: 1px solid #334155; margin-bottom: 25px;">
                <table style="width:100%; color: #e2e8f0; text-align: left; font-size: 1.05rem;">
                    <tr><th>Concepto</th><th>Cantidad</th><th>Jornal / Costo</th><th>Parcial (S/)</th></tr>
                    <tr><td>Días Completos</td><td><b>{cant_completos}</b></td><td>S/ {jornal_dia:.2f}</td><td>S/ {pago_completos:.2f}</td></tr>
                    <tr><td>Medios Días</td><td><b>{cant_medios}</b></td><td>S/ {jornal_dia/2:.2f}</td><td>S/ {pago_medios:.2f}</td></tr>
                    <tr><td>Inasistencias</td><td><b>{cant_faltas}</b></td><td>S/ 0.00</td><td>S/ 0.00</td></tr>
                    <tr><td>Comida - Almuerzo</td><td><b>{cant_almuerzos}</b></td><td>S/ {costo_almuerzo:.2f}</td><td>S/ {total_almuerzos:.2f}</td></tr>
                    <tr><td>Saldo Anterior (Debe / Adelanto)</td><td colspan="2">Ajuste de cuenta</td><td><b>S/ {nuevo_saldo:.2f}</b></td></tr>
                </table>
                <hr style="border-color: #334155;">
                <h3 style="color: #10b981; text-align: right; margin: 0;">TOTAL A PAGAR: S/ {total_trabajador:.2f}</h3>
            </div>
        """, unsafe_allow_html=True)

    st.markdown(f"<h2 style='color: #38bdf8; text-align: center; background-color: #1e293b; padding: 15px; border-radius: 8px;'>Total Planilla General de la Semana: S/ {gasto_semana_mo:.2f}</h2>", unsafe_allow_html=True)

with tab_materiales:
    st.write("Materiales comprados **exactamente dentro del rango de fechas** seleccionado arriba.")
    
    if not df_mat_db.empty:
        df_mat_db['fecha_dt'] = pd.to_datetime(df_mat_db['fecha']).dt.date
        mask = (df_mat_db['fecha_dt'] >= fecha_inicio) & (df_mat_db['fecha_dt'] <= fecha_fin)
        df_mat_filtrado = df_mat_db.loc[mask]
    else:
        df_mat_filtrado = pd.DataFrame(columns=['insumo', 'und', 'cantidad', 'precio'])

    if not df_mat_filtrado.empty:
        df_mats_show = df_mat_filtrado[['insumo', 'und', 'cantidad', 'precio']].rename(columns={'insumo': 'Insumo / Material', 'und': 'UND', 'cantidad': 'Cantidad', 'precio': 'Precio Unit. (S/)'})
    else:
        df_mats_show = pd.DataFrame(columns=['Insumo / Material', 'UND', 'Cantidad', 'Precio Unit. (S/)'])
        
    df_edit_mat = st.data_editor(df_mats_show, num_rows="dynamic", use_container_width=True, hide_index=True)
    
    gasto_semana_mat = 0
    for index, row in df_edit_mat.iterrows():
        if row["Insumo / Material"] and row["Cantidad"] > 0:
            gasto_semana_mat += (row["Cantidad"] * row["Precio Unit. (S/)"])
            
    st.markdown(f"<h3 style='color: #38bdf8; text-align: right;'>Total Materiales Semana: S/ {gasto_semana_mat:.2f}</h3>", unsafe_allow_html=True)

st.write("---")

# ==========================================
# 9. TABLA RESUMEN ACUMULATIVA SEMANAL
# ==========================================
st.markdown("<h2 style='color: #10b981 !important;'>📊 Tabla Resumen Semanal de Gastos (Acumulativo)</h2>", unsafe_allow_html=True)

df_resumen = pd.DataFrame({
    "Semana": ["Semana 1 (Septiembre)", "Semana 2 (Septiembre)", "Semana 3 (Septiembre)", "Semana 4 (Actual)"],
    "Gasto Mano Obra (S/)": [1200.00, 1300.00, 0.00, gasto_semana_mo],
    "Gasto Materiales (S/)": [3000.00, 1500.00, 1500.00, gasto_semana_mat]
})
df_resumen["Gasto Total Semanal (S/)"] = df_resumen["Gasto Mano Obra (S/)"] + df_resumen["Gasto Materiales (S/)"]
df_resumen["Gasto Acumulado (S/)"] = df_resumen["Gasto Total Semanal (S/)"].cumsum()
df_resumen["Saldo vs Presupuesto (S/)"] = st.session_state['presupuesto_total'] - df_resumen["Gasto Acumulado (S/)"]

st.dataframe(df_resumen, use_container_width=True, hide_index=True)

gasto_total_acumulado = df_resumen["Gasto Acumulado (S/)"].iloc[-1]
saldo_final = st.session_state['presupuesto_total'] - gasto_total_acumulado

col_res1, col_res2, col_res3 = st.columns(3)
with col_res1:
    st.markdown(f"""
        <div style='background-color: #1e293b; padding: 20px; border-radius: 12px; border-left: 5px solid #3b82f6;'>
            <h4 style='margin:0; color:#94a3b8;'>Presupuesto Asignado</h4>
            <h2 style='margin:0; color:#38bdf8;'>S/ {st.session_state['presupuesto_total']:.2f}</h2>
        </div>
    """, unsafe_allow_html=True)
with col_res2:
    st.markdown(f"""
        <div style='background-color: #1e293b; padding: 20px; border-radius: 12px; border-left: 5px solid #f59e0b;'>
            <h4 style='margin:0; color:#94a3b8;'>Gasto Acumulado a la fecha</h4>
            <h2 style='margin:0; color:#f59e0b;'>S/ {gasto_total_acumulado:.2f}</h2>
        </div>
    """, unsafe_allow_html=True)
with col_res3:
    color_saldo = "#10b981" if saldo_final >= 0 else "#ef4444"
    estado_saldo = "Saldo a Favor" if saldo_final >= 0 else "Sobregiro"
    st.markdown(f"""
        <div style='background-color: #1e293b; padding: 20px; border-radius: 12px; border-left: 5px solid {color_saldo};'>
            <h4 style='margin:0; color:#94a3b8;'>Estado: {estado_saldo}</h4>
            <h2 style='margin:0; color:{color_saldo};'>S/ {abs(saldo_final):.2f}</h2>
        </div>
    """, unsafe_allow_html=True)
