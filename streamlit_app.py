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

# ==========================================
# 1. CONFIGURACIÓN INICIAL DEL SOFTWARE
# ==========================================
st.set_page_config(
    page_title="Nexus Obra - Control Presupuestal", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# ==========================================
# CONSTANTES GLOBALES Y COLORES
# ==========================================
meses_espanol = ["", "ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO", "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"]
COLOR_AZUL_ELECTRICO = "#005af0" 
COLOR_TEXTO = "#1e293b"

# ==========================================
# 2. BASE DE DATOS PERMANENTE Y TABLAS
# ==========================================
conn = sqlite3.connect('obra_nexus.db', timeout=10.0, check_same_thread=False)
c = conn.cursor()

c.execute('CREATE TABLE IF NOT EXISTS usuarios (email TEXT UNIQUE, password TEXT)')
c.execute('CREATE TABLE IF NOT EXISTS personal (partida TEXT, nombre TEXT, especialidad TEXT, jornal REAL DEFAULT 120.0, almuerzo_costo REAL DEFAULT 7.0, UNIQUE(partida, nombre))')
c.execute('CREATE TABLE IF NOT EXISTS materiales (partida TEXT, fecha TEXT, insumo TEXT, und TEXT, cantidad REAL, precio REAL, descuento REAL DEFAULT 0.0)')
c.execute('CREATE TABLE IF NOT EXISTS asistencia (partida TEXT, trabajador TEXT, fecha TEXT, estado TEXT, almuerzo TEXT, actividad TEXT, UNIQUE(partida, trabajador, fecha))')
c.execute('CREATE TABLE IF NOT EXISTS presupuestos (partida TEXT PRIMARY KEY, modo TEXT, total REAL, materiales REAL, mano_obra REAL, fecha_creacion TEXT)')
conn.commit()

# Actualizaciones estructurales
try: c.execute('ALTER TABLE personal ADD COLUMN jornal REAL DEFAULT 120.0'); conn.commit()
except: pass
try: c.execute('ALTER TABLE personal ADD COLUMN almuerzo_costo REAL DEFAULT 7.0'); conn.commit()
except: pass
try: c.execute('ALTER TABLE materiales ADD COLUMN und TEXT'); conn.commit()
except: pass
try: c.execute('ALTER TABLE materiales ADD COLUMN descuento REAL DEFAULT 0.0'); conn.commit()
except: pass
try: c.execute('ALTER TABLE asistencia ADD COLUMN actividad TEXT'); conn.commit()
except: pass
try: 
    c.execute('ALTER TABLE presupuestos ADD COLUMN fecha_creacion TEXT')
    c.execute('UPDATE presupuestos SET fecha_creacion = ? WHERE fecha_creacion IS NULL', (str(date.today()),))
    conn.commit()
except: pass

def encriptar_clave(clave): return hashlib.sha256(str.encode(clave)).hexdigest()

def agregar_usuario(email, clave): 
    try:
        c.execute('INSERT INTO usuarios (email, password) VALUES (?, ?)', (email, encriptar_clave(clave)))
        conn.commit()
        return True
    except: return False

def verificar_usuario(email, clave):
    c.execute('SELECT * FROM usuarios WHERE email=? AND password=?', (email, encriptar_clave(clave)))
    return c.fetchone() is not None

def guardar_presupuesto_bd(partida, modo, total, mat, mo):
    c.execute("SELECT 1 FROM presupuestos WHERE partida=?", (partida,))
    existe = c.fetchone()
    if existe:
        c.execute("UPDATE presupuestos SET modo=?, total=?, materiales=?, mano_obra=? WHERE partida=?", 
                  (modo, float(total), float(mat), float(mo), partida))
    else:
        fecha_hoy = str(date.today())
        c.execute("INSERT INTO presupuestos (partida, modo, total, materiales, mano_obra, fecha_creacion) VALUES (?, ?, ?, ?, ?, ?)", 
                  (partida, modo, float(total), float(mat), float(mo), fecha_hoy))
    conn.commit()

if 'autenticado' not in st.session_state: st.session_state['autenticado'] = False
if 'mostrar_registro' not in st.session_state: st.session_state['mostrar_registro'] = False
if 'partida_actual' not in st.session_state: st.session_state['partida_actual'] = None
if 'cal_mes' not in st.session_state: st.session_state['cal_mes'] = 10 
if 'cal_ano' not in st.session_state: st.session_state['cal_ano'] = 2026

if 'lista_partidas' not in st.session_state: 
    c.execute("SELECT DISTINCT partida FROM presupuestos")
    partidas_bd = [row[0] for row in c.fetchall() if row[0] is not None and str(row[0]).strip() != ""]
    st.session_state['lista_partidas'] = partidas_bd if partidas_bd else ["Obras Provisionales"]

# ==========================================
# 3. DISEÑO DE INTERFAZ PROFESIONAL 
# ==========================================
st.markdown(f"""
    <style>
    .stApp, .main {{ background-color: #F8FAFC !important; color: {COLOR_TEXTO} !important; font-family: 'Segoe UI', Arial, sans-serif !important; }}
    h1, h2, h3, h4, h5, h6, p, label, span, div {{ color: {COLOR_TEXTO} !important; }}
    label {{ font-weight: 600 !important; font-size: 0.9rem !important; margin-bottom: 2px !important; }}
    
    /* BOTONES AZUL ELÉCTRICO COMPACTOS */
    div[data-testid="stButton"] > button {{
        background-color: {COLOR_AZUL_ELECTRICO} !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 4px !important;
        padding: 0.4rem 1.2rem !important;
        font-weight: bold !important;
        font-size: 0.85rem !important;
        text-transform: uppercase;
        width: auto !important; /* REDUCE EL TAMAÑO A LO ESTRICTAMENTE NECESARIO */
        box-shadow: 0 2px 4px rgba(0, 90, 240, 0.3) !important;
        transition: all 0.2s;
    }}
    div[data-testid="stButton"] > button:hover {{
        background-color: #0046cc !important;
        transform: translateY(-1px);
    }}
    
    /* Inputs minimalistas */
    .stTextInput input, .stNumberInput input, .stSelectbox div, .stTextArea textarea {{
        background-color: #ffffff !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 4px !important;
        padding: 0.4rem !important;
        font-size: 0.9rem !important;
    }}
    
    /* Contenedores blancos limpios */
    div[data-testid="metric-container"], .stForm, div[data-testid="stExpander"] {{
        background-color: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 6px !important;
    }}
    
    /* Encabezados de sección limpios */
    .section-header {{
        border-bottom: 2px solid {COLOR_AZUL_ELECTRICO};
        padding-bottom: 5px;
        margin: 20px 0 15px 0;
        font-weight: 800;
        font-size: 1.1rem;
        color: {COLOR_AZUL_ELECTRICO} !important;
        text-transform: uppercase;
    }}
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 4. PANTALLA DE LOGIN
# ==========================================
if not st.session_state['autenticado']:
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown(f"<div style='text-align: center; margin-top: 5vh; margin-bottom: 20px;'><h1 style='color:{COLOR_AZUL_ELECTRICO} !important; font-size:3rem; font-weight:900;'>NEXUS OBRA</h1><p style='font-weight:bold;'>SISTEMA DE CONTROL Y PRESUPUESTOS</p></div>", unsafe_allow_html=True)
        if not st.session_state['mostrar_registro']:
            with st.form("form_login"):
                st.markdown("<h3 style='text-align: center; font-size: 1.1rem; margin-bottom:15px;'>ACCESO</h3>", unsafe_allow_html=True)
                email_login = st.text_input("Usuario")
                clave_login = st.text_input("Contraseña", type="password")
                btn_login = st.form_submit_button("INGRESAR")
                
                if btn_login:
                    if verificar_usuario(email_login, clave_login):
                        st.session_state['autenticado'] = True
                        st.session_state['usuario_actual'] = email_login
                        st.rerun()
                    else: st.error("Credenciales incorrectas.")
            if st.button("Registrar Cuenta"):
                st.session_state['mostrar_registro'] = True
                st.rerun()
        else:
            with st.form("form_registro"):
                st.markdown("<h3 style='text-align: center; font-size: 1.1rem; margin-bottom:15px;'>NUEVO USUARIO</h3>", unsafe_allow_html=True)
                email_reg = st.text_input("Correo")
                clave_reg = st.text_input("Contraseña", type="password")
                btn_reg = st.form_submit_button("CREAR CUENTA")
                if btn_reg:
                    if agregar_usuario(email_reg, clave_reg):
                        st.success("Cuenta creada.")
                        st.session_state['mostrar_registro'] = False
                        st.rerun()
            if st.button("Volver"):
                st.session_state['mostrar_registro'] = False
                st.rerun()
    st.stop()

# ==========================================
# 5. GESTOR DE PARTIDAS (PORTAFOLIO MEJORADO)
# ==========================================
if st.session_state['partida_actual'] is None:
    # Encabezado estilo FOLIO COLORIDO
    st.markdown("""
        <div style="background: linear-gradient(135deg, #005af0, #00b4d8); padding: 15px 25px; border-radius: 10px 10px 0 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1); border-bottom: 4px solid #f59e0b; margin-bottom: 20px;">
            <h1 style="color: #ffffff !important; margin: 0; font-size: 1.8rem; font-weight: 800; display:flex; align-items:center; gap:10px;">
                🗂️ PORTAFOLIO DE PROYECTOS
            </h1>
            <p style="color: #e0f2fe !important; margin: 2px 0 0 0; font-size: 0.9rem; font-weight: bold;">Gestión centralizada de expedientes y partidas</p>
        </div>
    """, unsafe_allow_html=True)
    
    col_p1, col_space, col_p2 = st.columns([1, 0.1, 1])
    
    with col_p1:
        st.markdown("<div style='background:#ffffff; padding:15px; border-radius:6px; border:1px solid #e2e8f0;'>", unsafe_allow_html=True)
        st.markdown("<h4 style='color:#005af0 !important; margin-top:0; font-size:1.1rem;'>📂 ABRIR PARTIDA EXISTENTE</h4>", unsafe_allow_html=True)
        partida_seleccionada = st.selectbox("Seleccionar partida:", st.session_state['lista_partidas'])
        
        c.execute("SELECT total FROM presupuestos WHERE partida=?", (partida_seleccionada,))
        res_p = c.fetchone()
        presup_actual_gestion = 0.0
        if res_p and res_p[0] is not None:
            try: presup_actual_gestion = float(res_p[0])
            except: pass
            
        def auto_guardar_presup_existente():
            nuevo_val = st.session_state[f"edit_gestor_{partida_seleccionada}"]
            guardar_presupuesto_bd(partida_seleccionada, "Ingreso Directo del Total", nuevo_val, 0.0, 0.0)

        # Cajas reducidas solo a lo necesario usando columnas internas
        c1, c2 = st.columns([1.5, 1])
        with c1: nuevo_presupuesto_edicion = st.number_input("Presupuesto Asignado (S/):", value=presup_actual_gestion, step=500.0, key=f"edit_gestor_{partida_seleccionada}", on_change=auto_guardar_presup_existente)
        
        # Botón compacto sin width 100%
        if st.button("INGRESAR A LA PARTIDA ➡️", use_container_width=False):
            if partida_seleccionada:
                guardar_presupuesto_bd(partida_seleccionada, "Ingreso Directo del Total", nuevo_presupuesto_edicion, 0.0, 0.0)
                st.session_state['partida_actual'] = partida_seleccionada
                st.rerun()
            else: st.warning("Seleccione una partida.")
        st.markdown("</div>", unsafe_allow_html=True)
            
    with col_p2:
        st.markdown("<div style='background:#ffffff; padding:15px; border-radius:6px; border:1px solid #e2e8f0;'>", unsafe_allow_html=True)
        st.markdown("<h4 style='color:#10b981 !important; margin-top:0; font-size:1.1rem;'>➕ CREAR NUEVA PARTIDA</h4>", unsafe_allow_html=True)
        nueva_partida = st.text_input("Nombre de la nueva partida:")
        
        c3, c4 = st.columns([1.5, 1])
        with c3: presupuesto_inicial_crear = st.number_input("Presupuesto Inicial (S/):", min_value=0.0, value=0.0, step=500.0, key="nuevo_presup_creacion")
        
        # Botón compacto
        if st.button("CREAR Y ENTRAR ⚡", use_container_width=False):
            if nueva_partida.strip():
                if nueva_partida not in st.session_state['lista_partidas']:
                    st.session_state['lista_partidas'].append(nueva_partida)
                guardar_presupuesto_bd(nueva_partida, "Ingreso Directo del Total", presupuesto_inicial_crear, 0.0, 0.0)
                st.session_state['partida_actual'] = nueva_partida
                st.rerun()
            else: st.error("Debe ingresar un nombre.")
        st.markdown("</div>", unsafe_allow_html=True)
                
    st.markdown("<div class='section-header'>⚙️ ADMINISTRADOR DE EXPEDIENTES</div>", unsafe_allow_html=True)
    
    if st.session_state['lista_partidas']:
        datos_admin = []
        for p in st.session_state['lista_partidas']:
            c.execute("SELECT total, fecha_creacion FROM presupuestos WHERE partida=?", (p,))
            row_pres = c.fetchone()
            presupuesto_val = float(row_pres[0]) if (row_pres and row_pres[0] is not None) else 0.0
            fecha_creacion = row_pres[1] if (row_pres and len(row_pres) > 1 and row_pres[1]) else str(date.today())
            c.execute("SELECT COUNT(*) FROM personal WHERE partida=?", (p,))
            cant_personal = int(c.fetchone()[0])
            datos_admin.append({"Partida Original": p, "Fecha Creación": fecha_creacion, "Personal Reg.": cant_personal, "Presupuesto (S/)": presupuesto_val, "Nuevo Nombre": p, "Eliminar": False})
            
        df_editado = st.data_editor(pd.DataFrame(datos_admin), hide_index=True, use_container_width=True, disabled=["Partida Original", "Fecha Creación", "Personal Reg.", "Presupuesto (S/)"], column_config={"Partida Original": st.column_config.TextColumn("Código de Partida"), "Nuevo Nombre": st.column_config.TextColumn("✏️ Renombrar"), "Eliminar": st.column_config.CheckboxColumn("🗑️ Borrar", default=False)}, key="tabla_admin_partidas")
        
        if st.button("GUARDAR CAMBIOS EN ADMINISTRADOR", use_container_width=False):
            cambios = False
            for i, row in df_editado.iterrows():
                v_nom = row["Partida Original"]; n_nom = str(row["Nuevo Nombre"]).strip(); borrar = row["Eliminar"]
                if borrar:
                    c.execute("DELETE FROM presupuestos WHERE partida=?", (v_nom,)); c.execute("DELETE FROM materiales WHERE partida=?", (v_nom,)); c.execute("DELETE FROM personal WHERE partida=?", (v_nom,)); c.execute("DELETE FROM asistencia WHERE partida=?", (v_nom,))
                    cambios = True
                elif n_nom and n_nom != v_nom:
                    c.execute("SELECT 1 FROM presupuestos WHERE partida=?", (n_nom,))
                    if not c.fetchone():
                        c.execute("UPDATE presupuestos SET partida=? WHERE partida=?", (n_nom, v_nom)); c.execute("UPDATE materiales SET partida=? WHERE partida=?", (n_nom, v_nom)); c.execute("UPDATE personal SET partida=? WHERE partida=?", (n_nom, v_nom)); c.execute("UPDATE asistencia SET partida=? WHERE partida=?", (n_nom, v_nom))
                        cambios = True
            if cambios:
                conn.commit()
                c.execute("SELECT DISTINCT partida FROM presupuestos")
                st.session_state['lista_partidas'] = [r[0] for r in c.fetchall() if r[0] and str(r[0]).strip() != ""]
                st.rerun()

    st.write("---")
    if os.path.exists('obra_nexus.db'):
        with open("obra_nexus.db", "rb") as file:
            st.download_button(label="📥 DESCARGAR BASE DE DATOS LOCAL (.DB)", data=file, file_name="proyecto_nexus.db", mime="application/octet-stream", use_container_width=False)
    st.stop()

# ==========================================
# 6. DASHBOARD DE LA PARTIDA Y PRESUPUESTO
# ==========================================
st.markdown(f"""
    <div style="background-color: #ffffff; border-left: 5px solid {COLOR_AZUL_ELECTRICO}; padding: 10px 20px; border-radius: 4px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #e2e8f0; margin-bottom: 15px;">
        <h2 style="color: {COLOR_AZUL_ELECTRICO} !important; margin: 0; font-size: 1.5rem; font-weight:bold; text-transform:uppercase;">MÓDULO: {st.session_state['partida_actual']}</h2>
    </div>
""", unsafe_allow_html=True)

if st.button("⬅️ VOLVER AL PORTAFOLIO", use_container_width=False):
    st.session_state['partida_actual'] = None
    st.rerun()

try: c.execute("SELECT total FROM presupuestos WHERE partida=?", (st.session_state['partida_actual'],)); row_presupuesto = c.fetchone()
except: row_presupuesto = None

presupuesto_actual_total = float(row_presupuesto[0]) if row_presupuesto and row_presupuesto[0] is not None else 0.0

# ==========================================
# RECOLECCIÓN DE DATOS Y CÁLCULOS GLOBALES
# ==========================================
df_personal_db = pd.read_sql(f"SELECT nombre, especialidad, jornal, almuerzo_costo FROM personal WHERE partida='{st.session_state['partida_actual']}'", conn)
lista_trabajadores_db = df_personal_db['nombre'].tolist() if not df_personal_db.empty else []

df_mat_db = pd.read_sql(f"SELECT * FROM materiales WHERE partida='{st.session_state['partida_actual']}'", conn)
if not df_mat_db.empty:
    df_mat_db['fecha_dt'] = pd.to_datetime(df_mat_db['fecha']).dt.date
    df_mat_db['cantidad'] = pd.to_numeric(df_mat_db['cantidad'], errors='coerce').fillna(0.0)
    df_mat_db['precio'] = pd.to_numeric(df_mat_db['precio'], errors='coerce').fillna(0.0)
    df_mat_db['descuento'] = pd.to_numeric(df_mat_db['descuento'], errors='coerce').fillna(0.0) if 'descuento' in df_mat_db.columns else 0.0
else:
    df_mat_db['fecha_dt'] = pd.Series(dtype='object'); df_mat_db['cantidad'] = pd.Series(dtype='float64'); df_mat_db['precio'] = pd.Series(dtype='float64'); df_mat_db['descuento'] = pd.Series(dtype='float64')

df_asist_db = pd.read_sql(f"SELECT * FROM asistencia WHERE partida='{st.session_state['partida_actual']}'", conn)
if not df_asist_db.empty: df_asist_db['fecha_dt'] = pd.to_datetime(df_asist_db['fecha']).dt.date
else: df_asist_db['fecha_dt'] = pd.Series(dtype='object')

trabajadores_registrados = lista_trabajadores_db
todas_las_fechas = []
if not df_mat_db.empty: todas_las_fechas.extend(df_mat_db['fecha_dt'].tolist())
if not df_asist_db.empty: todas_las_fechas.extend(df_asist_db['fecha_dt'].tolist())

min_fecha_obra = min(todas_las_fechas) if todas_las_fechas else date.today()
max_fecha_obra = max(todas_las_fechas) if todas_las_fechas else date.today()

start_current_week_res = min_fecha_obra - timedelta(days=min_fecha_obra.weekday())
datos_resumen_semanas = []; gasto_acum_temp = 0.0; semana_contador = 1

while start_current_week_res <= max_fecha_obra + timedelta(days=7):
    end_current_week_res = start_current_week_res + timedelta(days=5) 
    mo_sem = 0.0
    if not df_asist_db.empty:
        mask_w = (df_asist_db['fecha_dt'] >= start_current_week_res) & (df_asist_db['fecha_dt'] <= end_current_week_res) & (df_asist_db['partida'] == st.session_state['partida_actual'])
        df_w_asist = df_asist_db.loc[mask_w]
        for trab in trabajadores_registrados:
            df_tw = df_w_asist[df_w_asist['trabajador'] == trab]
            c_comp = len(df_tw[df_tw['estado'] == 'Día Completo'])
            c_med = len(df_tw[df_tw['estado'] == 'Medio Día'])
            c_alm = len(df_tw[df_tw['almuerzo'].str.startswith('Sale', na=False)])
            c.execute("SELECT jornal, almuerzo_costo FROM personal WHERE partida=? AND nombre=?", (st.session_state['partida_actual'], trab))
            p_row = c.fetchone()
            jornal_val = float(p_row[0]) if p_row and pd.notna(p_row[0]) else 120.0
            alm_val = float(p_row[1]) if p_row and pd.notna(p_row[1]) else 7.0
            mo_sem += (c_comp * jornal_val) + (c_med * (jornal_val / 2.0)) + (c_alm * alm_val)

    mat_sem = 0.0
    if not df_mat_db.empty:
        mask_m = (df_mat_db['fecha_dt'] >= start_current_week_res) & (df_mat_db['fecha_dt'] <= end_current_week_res) & (df_mat_db['partida'] == st.session_state['partida_actual'])
        df_w_mat = df_mat_db.loc[mask_m].copy()
        df_w_mat['parcial_calc'] = df_w_mat['cantidad'] * df_w_mat['precio'] * (1 - (df_w_mat['descuento'] / 100.0))
        mat_sem = df_w_mat['parcial_calc'].sum()

    total_sem = round(mo_sem + mat_sem, 2)
    gasto_acum_temp = round(gasto_acum_temp + total_sem, 2)
    saldo_s = round(presupuesto_actual_total - gasto_acum_temp, 2)
    mes_num = start_current_week_res.month

    datos_resumen_semanas.append({
        "Mes": meses_espanol[mes_num] if mes_num < len(meses_espanol) else "", "Semana": f"Semana {semana_contador}",
        "Rango (Lunes a Sábado)": f"{start_current_week_res.strftime('%d/%m/%Y')} al {end_current_week_res.strftime('%d/%m/%Y')}",
        "Gasto Mano Obra (S/)": round(mo_sem, 2), "Gasto Materiales (S/)": round(mat_sem, 2),
        "Gasto Total Semanal (S/)": total_sem, "Gasto Acumulado (S/)": gasto_acum_temp, "Saldo vs Presupuesto (S/)": saldo_s
    })
    semana_contador += 1; start_current_week_res += timedelta(days=7)

df_resumen_final = pd.DataFrame(datos_resumen_semanas)
gasto_mo_real_total = round(df_resumen_final["Gasto Mano Obra (S/)"].sum(), 2) if not df_resumen_final.empty else 0.0
gasto_mat_real_total = round(df_resumen_final["Gasto Materiales (S/)"].sum(), 2) if not df_resumen_final.empty else 0.0
gasto_total_acumulado = round(df_resumen_final["Gasto Acumulado (S/)"].iloc[-1], 2) if not df_resumen_final.empty else 0.0

# ==========================================
# 7. GRÁFICOS DINÁMICOS FINANCIEROS
# ==========================================
st.markdown("<div class='section-header'>📊 DASHBOARD FINANCIERO</div>", unsafe_allow_html=True)
col_graf_circulo, col_graf_linea = st.columns([1, 1.5])

with col_graf_circulo:
    labels = ['Materiales', 'Mano de Obra', 'Saldo Disponible']
    values = [gasto_mat_real_total, gasto_mo_real_total, max(0, presupuesto_actual_total - (gasto_mat_real_total + gasto_mo_real_total))] 
    colores = [COLOR_AZUL_ELECTRICO, '#ea580c', '#e2e8f0'] 
    if sum(values) == 0: values = [0.0001, 0.0001, max(1.0, presupuesto_actual_total)]
    fig_dona = go.Figure(data=[go.Pie(labels=labels, values=values, marker_colors=colores, hole=0.5)])
    fig_dona.update_layout(title=dict(text="Distribución de Costos", font=dict(color=COLOR_TEXTO, size=14)), paper_bgcolor="#ffffff", plot_bgcolor="#ffffff", margin=dict(t=40, b=10, l=0, r=0), legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5))
    st.plotly_chart(fig_dona, use_container_width=True)

with col_graf_linea:
    semanas_graf = df_resumen_final['Semana'].tolist() if not df_resumen_final.empty else ['Sem 1']
    pres_total_linea = [presupuesto_actual_total] * len(semanas_graf)
    gasto_acumulado_graf = df_resumen_final['Gasto Acumulado (S/)'].tolist() if not df_resumen_final.empty else [0]
    fig_linea = go.Figure()
    fig_linea.add_trace(go.Scatter(x=semanas_graf, y=pres_total_linea, mode='lines', name='Presupuesto', line=dict(color='#10b981', dash='dash', width=2)))
    fig_linea.add_trace(go.Scatter(x=semanas_graf, y=gasto_acumulado_graf, mode='lines+markers', name='Ejecutado', line=dict(color='#ef4444', width=3)))
    fig_linea.update_layout(title=dict(text="Curva Presupuesto vs Gasto", font=dict(color=COLOR_TEXTO, size=14)), paper_bgcolor="#ffffff", plot_bgcolor="#ffffff", margin=dict(t=40, b=10, l=10, r=10), legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5), xaxis=dict(gridcolor="#e2e8f0"), yaxis=dict(tickprefix="S/ ", gridcolor="#e2e8f0"))
    st.plotly_chart(fig_linea, use_container_width=True)

# ==========================================
# 8. CENTRO DE REGISTRO
# ==========================================
st.markdown("<div class='section-header'>📝 CONSOLA DE DATOS</div>", unsafe_allow_html=True)
tab_mat, tab_pers, tab_mo = st.tabs(["📦 Ingreso Materiales", "👤 Alta Personal", "👷 Control Asistencia"])

with tab_mat:
    with st.form("form_materiales"):
        f_mat = st.date_input("Fecha", date.today(), key="f1")
        mat_nom = st.text_input("Descripción Insumo")
        tipo_und = st.selectbox("Unidad", ["bol (Bolsas)", "caja (Cajas)", "m3 (Metro cúbico)", "m2 (Metro cuadrado)", "kg (Kilogramo)", "und (Unidad)", "gln (Galón)", "glb (Global)", "pza (Pieza)", "ml (Metro lineal)", "Otra unidad..."])
        und_final = tipo_und.split(" ")[0] if tipo_und != "Otra unidad..." else st.text_input("Especifique su unidad:")
        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1: cant = st.number_input("Cantidad", min_value=0.01, value=1.0)
        with col_m2: pre = st.number_input("Precio U. (S/)", min_value=0.0)
        with col_m3: desc = st.number_input("Desc. (%)", min_value=0.0, max_value=100.0, value=0.0, step=0.01)
        
        col_mb1, col_mb2 = st.columns(2)
        with col_mb1: btn_guardar_mat = st.form_submit_button("GUARDAR", use_container_width=False)
        with col_mb2: btn_limpiar_mat = st.form_submit_button("LIMPIAR", use_container_width=False)

        if btn_guardar_mat and mat_nom and und_final:
            c.execute("INSERT INTO materiales (partida, fecha, insumo, und, cantidad, precio, descuento) VALUES (?, ?, ?, ?, ?, ?, ?)", (st.session_state['partida_actual'], str(f_mat), mat_nom, und_final, cant, pre, desc))
            conn.commit(); st.rerun()

with tab_pers:
    with st.form("form_nuevo_personal"):
        col_np1, col_np2 = st.columns(2)
        with col_np1: nuevo_nombre = st.text_input("Nombres y Apellidos")
        with col_np2: nueva_esp = st.selectbox("Especialidad", ["Operario", "Enchapador", "Oficial", "Ayudante / Peón", "Pintor", "Electricista", "Plomero"])
        col_np3, col_np4 = st.columns(2)
        with col_np3: def_jornal = st.number_input("Jornal (S/)", value=120.0, step=10.0)
        with col_np4: def_alm = st.number_input("Almuerzo (S/)", value=7.0, step=1.0)
        if st.form_submit_button("REGISTRAR", use_container_width=False) and nuevo_nombre:
            try: c.execute("INSERT INTO personal (partida, nombre, especialidad, jornal, almuerzo_costo) VALUES (?, ?, ?, ?, ?)", (st.session_state['partida_actual'], nuevo_nombre.strip(), nueva_esp, def_jornal, def_alm)); conn.commit(); st.rerun()
            except: st.warning("Ya existe.")

with tab_mo:
    with st.form("form_mano_obra"):
        f_mo = st.date_input("Fecha", date.today(), key="f2")
        trabajador = st.selectbox("Personal", lista_trabajadores_db) if lista_trabajadores_db else st.text_input("Nombre")
        estado_asis = st.selectbox("Asistencia", ["Día Completo", "Medio Día", "Falta / Emergencia"])
        almuerzo_opc = st.radio("Almuerzo", ["Almuerza en obra / con comida de obra - S/ 0 extra", "Sale a comer afuera - S/ 7 extra"], horizontal=True)
        actividad = st.text_area("Actividad")
        col_fb1, col_fb2 = st.columns(2)
        with col_fb1: btn_guardar = st.form_submit_button("GUARDAR ASISTENCIA", use_container_width=False)
        with col_fb2: btn_limpiar_dia = st.form_submit_button("BORRAR DÍA", use_container_width=False)

        if btn_guardar and trabajador:
            c.execute("INSERT OR REPLACE INTO asistencia (partida, trabajador, fecha, estado, almuerzo, actividad) VALUES (?, ?, ?, ?, ?, ?)", (st.session_state['partida_actual'], trabajador, str(f_mo), estado_asis, almuerzo_opc, actividad))
            conn.commit(); st.rerun()

# ==========================================
# 11. TABLA RESUMEN FINANCIERO
# ==========================================
st.markdown("<div class='section-header'>📈 CONSOLIDADO FINANCIERO</div>", unsafe_allow_html=True)
df_resumen_mostrar = df_resumen_final.copy()
if not df_resumen_mostrar.empty:
    df_resumen_mostrar.loc["Total"] = {"Mes": "", "Semana": "TOTAL", "Rango (Lunes a Sábado)": "", "Gasto Mano Obra (S/)": gasto_mo_real_total, "Gasto Materiales (S/)": gasto_mat_real_total, "Gasto Total Semanal (S/)": round(gasto_mo_real_total + gasto_mat_real_total, 2), "Gasto Acumulado (S/)": "", "Saldo vs Presupuesto (S/)": ""}
    for col in ["Gasto Mano Obra (S/)", "Gasto Materiales (S/)", "Gasto Total Semanal (S/)", "Gasto Acumulado (S/)", "Saldo vs Presupuesto (S/)"]:
        df_resumen_mostrar[col] = df_resumen_mostrar[col].apply(lambda x: f"{x:,.2f}" if isinstance(x, (int, float)) else x)
st.dataframe(df_resumen_mostrar, use_container_width=True, hide_index=True)

saldo_final = round(presupuesto_actual_total - gasto_total_acumulado, 2)
col_res1, col_res2, col_res3 = st.columns(3)
with col_res1: st.markdown(f"<div style='background:white; padding:15px; border-radius:4px; border:1px solid #e2e8f0; text-align:center;'><h4 style='margin:0; font-size:0.9rem;'>Presupuesto Base</h4><h2 style='margin:5px 0 0 0; color:#1e293b;'>S/ {presupuesto_actual_total:,.2f}</h2></div>", unsafe_allow_html=True)
with col_res2: st.markdown(f"<div style='background:white; padding:15px; border-radius:4px; border:1px solid #e2e8f0; text-align:center;'><h4 style='margin:0; font-size:0.9rem;'>Costo Ejecutado</h4><h2 style='margin:5px 0 0 0; color:{COLOR_AZUL_ELECTRICO};'>S/ {gasto_total_acumulado:,.2f}</h2></div>", unsafe_allow_html=True)
with col_res3: st.markdown(f"<div style='background:white; padding:15px; border-radius:4px; border:1px solid #e2e8f0; text-align:center;'><h4 style='margin:0; font-size:0.9rem;'>Saldo Total</h4><h2 style='margin:5px 0 0 0; color:#10b981;'>S/ {abs(saldo_final):,.2f}</h2></div>", unsafe_allow_html=True)

# ==========================================
# 12. GENERADOR PDF (DISEÑO MEMBRETE CAJAS)
# ==========================================
st.markdown("<div class='section-header'>🖨️ EXPORTAR PDF OFICIAL</div>", unsafe_allow_html=True)
if st.button("GENERAR INFORME PDF", use_container_width=False):
    dias_es_map_rep = {0: 'Lunes', 1: 'Martes', 2: 'Miércoles', 3: 'Jueves', 4: 'Viernes', 5: 'Sábado', 6: 'Domingo'}
    fecha_impresion_str = date.today().strftime('%d/%m/%Y')
    
    first_m = date(st.session_state['cal_ano'], st.session_state['cal_mes'], 1)
    if st.session_state['cal_mes'] == 12: last_m = date(st.session_state['cal_ano'] + 1, 1, 1) - timedelta(days=1)
    else: last_m = date(st.session_state['cal_ano'], st.session_state['cal_mes'] + 1, 1) - timedelta(days=1)
    curr_w = first_m - timedelta(days=first_m.weekday())
    semanas_mes_lista = []; idx_s = 1
    while curr_w <= last_m:
        end_w = curr_w + timedelta(days=5); semanas_mes_lista.append((f"Semana {idx_s}", curr_w, end_w)); idx_s += 1; curr_w += timedelta(days=7)

    labels_print = ['Materiales', 'Mano de Obra', 'Saldo Restante']
    values_print = [gasto_mat_real_total, gasto_mo_real_total, max(0, presupuesto_actual_total - (gasto_mat_real_total + gasto_mo_real_total))]
    fig_dona_print = go.Figure(data=[go.Pie(labels=labels_print, values=values_print, marker_colors=[COLOR_AZUL_ELECTRICO, '#ea580c', '#e2e8f0'])])
    fig_dona_print.update_layout(title=dict(text="Distribución de Costos", font=dict(color="#000", size=13, weight="bold")), paper_bgcolor="white", plot_bgcolor="white", margin=dict(t=30, b=10, l=10, r=10), legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5, font=dict(color="#000", size=9)), width=480, height=280)
    fig_dona_print.update_traces(texttemplate='%{percent}<br>S/ %{value:,.2f}', textposition='inside', textfont=dict(size=9.5, color='black'))

    semanas_graf_p = df_resumen_final['Semana'].tolist() if not df_resumen_final.empty else ['Sem 1']
    pres_total_linea_p = [presupuesto_actual_total] * len(semanas_graf_p)
    gasto_acumulado_graf_p = df_resumen_final['Gasto Acumulado (S/)'].tolist() if not df_resumen_final.empty else [0]
    
    # Colores exactos a tu PDF original (Línea roja solida, Verde punteada)
    fig_linea_print = go.Figure()
    fig_linea_print.add_trace(go.Scatter(x=semanas_graf_p, y=pres_total_linea_p, mode='lines', name='Presupuesto Total', line=dict(color='#10b981', dash='dash', width=2)))
    fig_linea_print.add_trace(go.Scatter(x=semanas_graf_p, y=gasto_acumulado_graf_p, mode='lines+markers', name='Gasto Acumulado', line=dict(color='#ef4444', width=3)))
    fig_linea_print.update_layout(title=dict(text="Curva Presupuesto vs Gasto Acumulado", font=dict(color="#000", size=13, weight="bold")), paper_bgcolor="white", plot_bgcolor="white", margin=dict(t=30, b=40, l=70, r=20), legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5, font=dict(color="#000", size=9)), xaxis=dict(tickangle=0, gridcolor="#e2e8f0", showline=True, linecolor='#000'), yaxis=dict(tickprefix="S/ ", tickformat=",.0f", gridcolor="#e2e8f0", showline=True, linecolor='#000'), width=480, height=280)

    html_dona_str = fig_dona_print.to_html(include_plotlyjs='inline', full_html=False, config={'displayModeBar': False})
    html_linea_str = fig_linea_print.to_html(include_plotlyjs='inline', full_html=False, config={'displayModeBar': False})

    # ESTILO MEMBRETE CUADROS
    html_reporte = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Informe Técnico - Nexus Obra</title>
        <style>
            @page {{ size: A4; margin: 15mm; }}
            body {{ font-family: 'Segoe UI', Arial, sans-serif; color: #000000; margin: 0; padding: 0; font-size: 8pt; line-height: 1.3; background: #ffffff; }}
            .membrete-table {{ width: 100%; border-collapse: collapse; margin-bottom: 15px; border: 2px solid #000; }}
            .membrete-table td {{ border: 1px solid #000; padding: 8px; vertical-align: top; }}
            .info-table {{ width: 100%; border-collapse: collapse; margin-bottom: 15px; font-size: 8pt; }}
            .info-table td {{ border: 1px solid #000; padding: 5px; }}
            .info-label {{ background-color: #f1f5f9; font-weight: bold; width: 20%; }}
            .section-title {{ font-size: 10pt; font-weight: bold; color: {COLOR_AZUL_ELECTRICO}; margin-top: 15px; margin-bottom: 8px; text-transform: uppercase; }}
            .data-table {{ width: 100%; border-collapse: collapse; margin-bottom: 10px; }}
            .data-table th, .data-table td {{ border: 1px solid #000; padding: 4px; text-align: left; }}
            .data-table th {{ background: #f1f5f9; font-weight: bold; text-align: center; }}
            .text-right {{ text-align: right; }} .text-center {{ text-align: center; }}
            .grafico-center {{ text-align: center; margin: 5px auto; page-break-inside: avoid; display: flex; justify-content: center; }}
            @media print {{ button {{ display: none; }} }}
        </style>
    </head>
    <body>
        <table class="membrete-table">
            <tr>
                <td style="width: 65%; background-color: #f8fafc;">
                    <h1 style="font-size: 14pt; margin: 0; color: {COLOR_AZUL_ELECTRICO}; font-weight:900;">SISTEMA DE CONTROL DE PROYECTOS - NEXUS OBRA</h1>
                    <h2 style="font-size: 10pt; margin: 5px 0 0 0; color: #000;">INFORME TÉCNICO DE CONTROL PRESUPUESTAL Y MANO DE OBRA</h2>
                </td>
                <td style="width: 35%; font-size: 8pt;">
                    <b>Fecha de Impresión:</b> {fecha_impresion_str}<br>
                    <b>Mes Evaluado:</b> {meses_espanol[st.session_state['cal_mes']]} {st.session_state['cal_ano']}<br>
                    <b>Costo al:</b> {date.today().strftime('%d/%m/%Y')}
                </td>
            </tr>
        </table>
        
        <table class="info-table">
            <tr>
                <td class="info-label">Proyecto / Descripción:</td>
                <td colspan="3">Obras de Construcción Civil y Acabados</td>
            </tr>
            <tr>
                <td class="info-label">Ubicación:</td>
                <td>Distrito Ayacucho, Huamanga</td>
                <td class="info-label">Partida Evaluada:</td>
                <td><b>{st.session_state['partida_actual']}</b></td>
            </tr>
            <tr>
                <td class="info-label">Cliente:</td>
                <td colspan="3">Cliente Principal</td>
            </tr>
        </table>

        <div class="section-title">1. Análisis Financiero y Resumen Global</div>
        <p style="margin: 0 0 10px 0;">El presente informe detalla el estado económico de la partida <b>{st.session_state['partida_actual']}</b>. Se ha asignado un presupuesto total de <b>S/ {presupuesto_actual_total:,.2f}</b>, registrando un gasto acumulado de <b>S/ {gasto_total_acumulado:,.2f}</b>. Esto representa un estado financiero de <b>{'SALDO A FAVOR' if saldo_final >= 0 else 'SOBREGIRO'}</b> por un monto de <b>S/ {abs(saldo_final):,.2f}</b>.</p>

        <div class="section-title">2. Análisis Gráfico de Ejecución</div>
        <div class="grafico-center">{html_dona_str}</div>
        <div class="grafico-center">{html_linea_str}</div>

        <div class="section-title">3. Resumen General por Semanas de Trabajo (Lunes a Sábado)</div>
        <table class="data-table">
            <thead>
                <tr>
                    <th>Mes</th><th>Semana</th><th>Rango</th>
                    <th>Mano Obra (S/)</th><th>Materiales (S/)</th><th>Total Semanal (S/)</th><th>Acumulado (S/)</th><th>Saldo (S/)</th>
                </tr>
            </thead>
            <tbody>
    """
    
    for _, row in df_resumen_final.iterrows():
        html_reporte += f"<tr><td class='text-center'>{row['Mes']}</td><td class='text-center'>{row['Semana']}</td><td class='text-center'>{row['Rango (Lunes a Sábado)']}</td><td class='text-right'>S/ {row['Gasto Mano Obra (S/)']:,.2f}</td><td class='text-right'>S/ {row['Gasto Materiales (S/)']:,.2f}</td><td class='text-right'>S/ {row['Gasto Total Semanal (S/)']:,.2f}</td><td class='text-right'>S/ {row['Gasto Acumulado (S/)']:,.2f}</td><td class='text-right'>S/ {row['Saldo vs Presupuesto (S/)']:,.2f}</td></tr>"
        
    html_reporte += f"<tr style='background-color:#f1f5f9; font-weight:bold;'><td colspan='3' class='text-right'>TOTAL GENERAL:</td><td class='text-right'>S/ {gasto_mo_real_total:,.2f}</td><td class='text-right'>S/ {gasto_mat_real_total:,.2f}</td><td class='text-right'>S/ {gasto_mo_real_total + gasto_mat_real_total:,.2f}</td><td></td><td></td></tr></tbody></table>"

    html_reporte += "<div class='section-title'>4. Detalle de Planilla por Trabajador</div>"
    for _, pers in df_pers_actual.iterrows():
        t_nombre = pers['nombre']; t_esp = pers['especialidad']
        html_reporte += f"<div style='font-weight:bold; margin: 10px 0 5px 0; border-bottom: 1px dashed #000;'>Obrero: {t_esp} - {t_nombre}</div>"
        
        for s_nombre, s_ini, s_fin in semanas_mes_lista:
            df_t_s = pd.DataFrame()
            if not df_asist_db.empty:
                m_ts = (df_asist_db['trabajador'] == t_nombre) & (df_asist_db['fecha_dt'] >= s_ini) & (df_asist_db['fecha_dt'] <= s_fin) & (df_asist_db['partida'] == st.session_state['partida_actual'])
                df_t_s = df_asist_db.loc[m_ts].sort_values('fecha')
                
            c_comp = len(df_t_s[df_t_s['estado'] == 'Día Completo']) if not df_t_s.empty else 0
            c_med = len(df_t_s[df_t_s['estado'] == 'Medio Día']) if not df_t_s.empty else 0
            c_alm = len(df_t_s[df_t_s['almuerzo'].str.startswith('Sale', na=False)]) if not df_t_s.empty else 0
            jornal_v = float(pers['jornal']) if pd.notna(pers['jornal']) else 120.0; alm_v = float(pers['almuerzo_costo']) if pd.notna(pers['almuerzo_costo']) else 7.0
            tot_s_trab = (c_comp * jornal_v) + (c_med * (jornal_v / 2.0)) + (c_alm * alm_v)
            
            html_reporte += f"<p style='margin: 2px 0; font-size: 8pt; font-weight:bold;'>{s_nombre} ({s_ini.strftime('%d/%m/%Y')} al {s_fin.strftime('%d/%m/%Y')}):</p>"
            if not df_t_s.empty:
                html_reporte += "<table class='data-table'><thead><tr><th width='15%'>Fecha</th><th width='15%'>Día</th><th width='25%'>Asistencia</th><th width='45%'>Actividad</th></tr></thead><tbody>"
                for _, r_as in df_t_s.iterrows():
                    dt_f = date.fromisoformat(str(r_as['fecha']))
                    html_reporte += f"<tr><td class='text-center'>{dt_f.strftime('%d/%m/%Y')}</td><td class='text-center'>{dias_es_map_rep[dt_f.weekday()]}</td><td>{r_as['estado']}</td><td>{r_as['actividad']}</td></tr>"
                html_reporte += "</tbody></table>"
            else: html_reporte += "<p style='font-size:7.5pt; margin: 0 0 5px 0;'><i>Sin registros en esta semana.</i></p>"
            html_reporte += f"<div style='text-align:right; font-size:8pt; font-weight:bold; margin-bottom:10px;'>Subtotal {s_nombre}: S/ {tot_s_trab:,.2f}</div>"

    html_reporte += f"""
        <div class="section-title">5. Control de Materiales e Insumos</div>
        <table class="data-table">
            <thead>
                <tr>
                    <th>Fecha</th><th>Insumo / Material</th><th>UND</th><th>Cantidad</th><th>P. Unitario (S/)</th><th>Desc. (%)</th><th>Parcial (S/)</th>
                </tr>
            </thead>
            <tbody>
    """
    gasto_mat_rep = 0.0
    if not df_mat_db.empty:
        df_mat_rep = df_mat_db.sort_values('fecha')
        for _, r_m in df_mat_rep.iterrows():
            dt_m = date.fromisoformat(str(r_m['fecha']))
            cant_m = float(r_m['cantidad']); prec_m = float(r_m['precio'])
            desc_m = float(r_m['descuento']) if 'descuento' in r_m and pd.notna(r_m['descuento']) else 0.0
            parc_m = cant_m * prec_m * (1 - (desc_m / 100.0)); gasto_mat_rep += parc_m
            html_reporte += f"<tr><td class='text-center'>{dt_m.strftime('%d/%m/%Y')}</td><td>{r_m['insumo']}</td><td class='text-center'>{r_m['und']}</td><td class='text-right'>{cant_m:,.2f}</td><td class='text-right'>S/ {prec_m:,.2f}</td><td class='text-right'>{desc_m:.2f}</td><td class='text-right'>S/ {parc_m:,.2f}</td></tr>"
    if gasto_mat_rep == 0.0: html_reporte += "<tr><td colspan='7' class='text-center'><i>Sin movimientos registrados.</i></td></tr>"
        
    html_reporte += f"""
            </tbody>
        </table>
        <div style='text-align:right; font-weight:bold; font-size:9pt;'>TOTAL MATERIALES MES: S/ {gasto_mat_rep:,.2f}</div>
        <script> setTimeout(function() {{ window.print(); }}, 1500); </script>
    </body>
    </html>
    """
    st.components.v1.html(html_reporte, height=800, scrolling=True)
