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
COLOR_VERDOSO = "#059669" # Verde esmeralda profesional
COLOR_TEXTO = "#1e293b"   # Negro/Gris muy oscuro

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
# 3. DISEÑO DE INTERFAZ PROFESIONAL (CSS BLANCO/VERDOSO)
# ==========================================
st.markdown(f"""
    <style>
    /* Forzar modo claro absoluto */
    .stApp, .main {{ background-color: #F8FAFC !important; color: {COLOR_TEXTO} !important; font-family: 'Segoe UI', Arial, sans-serif !important; }}
    
    /* Textos oscuros y negritos */
    h1, h2, h3, h4, h5, h6, p, label, span, div {{ color: {COLOR_TEXTO} !important; }}
    label {{ font-weight: 600 !important; font-size: 0.95rem !important; }}
    
    /* Botones Blancos con borde verdoso */
    div[data-testid="stButton"] > button {{
        background-color: #FFFFFF !important;
        color: {COLOR_VERDOSO} !important;
        border: 2px solid {COLOR_VERDOSO} !important;
        border-radius: 8px !important;
        padding: 0.4rem 1rem !important;
        font-weight: 700 !important;
        font-size: 0.9rem !important;
        text-transform: uppercase;
        transition: all 0.2s ease;
    }}
    div[data-testid="stButton"] > button:hover {{
        background-color: {COLOR_VERDOSO} !important;
        color: #FFFFFF !important;
        box-shadow: 0 4px 6px rgba(5, 150, 105, 0.2) !important;
    }}
    
    /* Inputs de texto y números limpios */
    .stTextInput input, .stNumberInput input, .stSelectbox div, .stTextArea textarea {{
        background-color: #FFFFFF !important;
        color: #000000 !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 6px !important;
        font-weight: 500 !important;
    }}
    .stTextInput input:focus, .stNumberInput input:focus {{
        border-color: {COLOR_VERDOSO} !important;
        box-shadow: 0 0 0 1px {COLOR_VERDOSO} !important;
    }}
    
    /* Contenedores y Cuadros */
    div[data-testid="metric-container"], .stForm, div[data-testid="stExpander"] {{
        background-color: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 10px !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }}
    
    /* Encabezados de sección (Cuadros con borde superior verdoso) */
    .section-header {{
        background-color: #FFFFFF;
        border-top: 4px solid {COLOR_VERDOSO};
        border-left: 1px solid #E2E8F0;
        border-right: 1px solid #E2E8F0;
        border-bottom: 1px solid #E2E8F0;
        padding: 12px 20px;
        margin: 20px 0 15px 0;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
        font-weight: 800;
        font-size: 1.1rem;
        color: {COLOR_VERDOSO} !important;
        text-transform: uppercase;
    }}
    
    /* Tablas Dataframe */
    .stDataFrame {{ background-color: #FFFFFF !important; border: 1px solid #E2E8F0 !important; border-radius: 8px; }}
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 4. PANTALLA DE LOGIN
# ==========================================
if not st.session_state['autenticado']:
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown(f"<div style='text-align: center; margin-top: 5vh; margin-bottom: 20px;'><h1 style='color:{COLOR_VERDOSO} !important; font-size:3.5rem; font-weight:900;'>NEXUS OBRA</h1><p style='font-size:1.1rem; font-weight:bold;'>SISTEMA DE CONTROL Y ALMACÉN</p></div>", unsafe_allow_html=True)
        st.markdown("<div style='background:white; padding:30px; border-radius:12px; border:1px solid #e2e8f0; box-shadow:0 4px 10px rgba(0,0,0,0.05);'>", unsafe_allow_html=True)
        
        if not st.session_state['mostrar_registro']:
            with st.form("form_login"):
                st.markdown("<h3 style='text-align: center; font-size: 1.2rem; margin-bottom:20px; font-weight:800;'>ACCESO AL SISTEMA</h3>", unsafe_allow_html=True)
                email_login = st.text_input("Usuario / Correo Electrónico")
                clave_login = st.text_input("Contraseña", type="password")
                btn_login = st.form_submit_button("INGRESAR", use_container_width=True)
                
                if btn_login:
                    if verificar_usuario(email_login, clave_login):
                        st.session_state['autenticado'] = True
                        st.session_state['usuario_actual'] = email_login
                        st.rerun()
                    else: st.error("Credenciales incorrectas.")
            if st.button("Registrar Nueva Cuenta", use_container_width=True):
                st.session_state['mostrar_registro'] = True
                st.rerun()
        else:
            with st.form("form_registro"):
                st.markdown("<h3 style='text-align: center; font-size: 1.2rem; margin-bottom:20px; font-weight:800;'>NUEVO USUARIO</h3>", unsafe_allow_html=True)
                email_reg = st.text_input("Nuevo Correo")
                clave_reg = st.text_input("Crear Contraseña", type="password")
                btn_reg = st.form_submit_button("CREAR CUENTA", use_container_width=True)
                
                if btn_reg:
                    if email_reg and clave_reg:
                        if agregar_usuario(email_reg, clave_reg):
                            st.success("Cuenta creada exitosamente.")
                            st.session_state['mostrar_registro'] = False
                            st.rerun()
                        else: st.error("El usuario ya existe.")
                    else: st.warning("Complete todos los campos.")
            if st.button("Volver al Login", use_container_width=True):
                st.session_state['mostrar_registro'] = False
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# ==========================================
# 5. GESTOR DE PARTIDAS (PORTAFOLIO)
# ==========================================
if st.session_state['partida_actual'] is None:
    st.markdown(f"""
        <div style="background-color: #FFFFFF; padding: 20px; border-radius: 10px; margin-bottom: 20px; border: 1px solid #E2E8F0; text-align: center;">
            <h1 style="color: {COLOR_VERDOSO} !important; margin: 0; font-size: 2rem; font-weight: 800;">PORTAFOLIO DE PROYECTOS</h1>
            <p style="margin: 5px 0 0 0; font-weight: bold;">Control de Partidas y Expedientes</p>
        </div>
    """, unsafe_allow_html=True)
    
    col_p1, col_space, col_p2 = st.columns([1, 0.05, 1])
    
    with col_p1:
        st.markdown("<div class='section-header'>📂 ABRIR PARTIDA EXISTENTE</div>", unsafe_allow_html=True)
        partida_seleccionada = st.selectbox("Seleccionar partida del expediente:", st.session_state['lista_partidas'])
        
        c.execute("SELECT total FROM presupuestos WHERE partida=?", (partida_seleccionada,))
        res_p = c.fetchone()
        presup_actual_gestion = 0.0
        if res_p and res_p[0] is not None:
            try: presup_actual_gestion = float(res_p[0])
            except: pass
            
        def auto_guardar_presup_existente():
            nuevo_val = st.session_state[f"edit_gestor_{partida_seleccionada}"]
            guardar_presupuesto_bd(partida_seleccionada, "Ingreso Directo del Total", nuevo_val, 0.0, 0.0)

        nuevo_presupuesto_edicion = st.number_input("Presupuesto Asignado (S/):", value=presup_actual_gestion, step=500.0, key=f"edit_gestor_{partida_seleccionada}", on_change=auto_guardar_presup_existente)
        
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        if st.button("INGRESAR A LA PARTIDA ➡️", use_container_width=True):
            if partida_seleccionada:
                guardar_presupuesto_bd(partida_seleccionada, "Ingreso Directo del Total", nuevo_presupuesto_edicion, 0.0, 0.0)
                st.session_state['partida_actual'] = partida_seleccionada
                st.rerun()
            else: st.warning("Seleccione una partida.")
            
    with col_p2:
        st.markdown("<div class='section-header'>➕ CREAR NUEVA PARTIDA</div>", unsafe_allow_html=True)
        nueva_partida = st.text_input("Nombre de la nueva partida:")
        presupuesto_inicial_crear = st.number_input("Presupuesto Inicial (S/):", min_value=0.0, value=0.0, step=500.0, key="nuevo_presup_creacion")
        
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        if st.button("CREAR Y ENTRAR ⚡", use_container_width=True):
            if nueva_partida.strip():
                if nueva_partida not in st.session_state['lista_partidas']:
                    st.session_state['lista_partidas'].append(nueva_partida)
                guardar_presupuesto_bd(nueva_partida, "Ingreso Directo del Total", presupuesto_inicial_crear, 0.0, 0.0)
                st.session_state['partida_actual'] = nueva_partida
                st.rerun()
            else: st.error("Debe ingresar un nombre válido.")
                
    st.markdown("<div class='section-header'>⚙️ ADMINISTRADOR DE EXPEDIENTES</div>", unsafe_allow_html=True)
    
    if st.session_state['lista_partidas']:
        datos_admin = []
        for p in st.session_state['lista_partidas']:
            c.execute("SELECT total, fecha_creacion FROM presupuestos WHERE partida=?", (p,))
            row_pres = c.fetchone()
            
            presupuesto_val = 0.0
            if row_pres and row_pres[0] is not None:
                try: presupuesto_val = float(row_pres[0])
                except: pass
                    
            fecha_creacion = row_pres[1] if (row_pres and len(row_pres) > 1 and row_pres[1]) else str(date.today())
            
            c.execute("SELECT COUNT(*) FROM personal WHERE partida=?", (p,))
            row_pers = c.fetchone()
            cant_personal = int(row_pers[0]) if row_pers else 0
            
            datos_admin.append({
                "Partida Original": p, "Fecha Creación": fecha_creacion, "Personal Reg.": cant_personal,
                "Presupuesto (S/)": presupuesto_val, "Nuevo Nombre": p, "Eliminar": False
            })
            
        df_admin = pd.DataFrame(datos_admin)
        
        df_editado = st.data_editor(
            df_admin, hide_index=True, use_container_width=True,
            disabled=["Partida Original", "Fecha Creación", "Personal Reg.", "Presupuesto (S/)"], 
            column_config={
                "Partida Original": st.column_config.TextColumn("Código de Partida", disabled=True),
                "Fecha Creación": st.column_config.TextColumn("Fecha Registro", disabled=True),
                "Personal Reg.": st.column_config.NumberColumn("Cuadrilla", disabled=True),
                "Presupuesto (S/)": st.column_config.NumberColumn("Presupuesto", format="S/ %.2f", disabled=True),
                "Nuevo Nombre": st.column_config.TextColumn("✏️ Renombrar"),
                "Eliminar": st.column_config.CheckboxColumn("🗑️ Borrar", default=False)
            },
            key="tabla_admin_partidas"
        )
        
        if st.button("GUARDAR CAMBIOS EN ADMINISTRADOR", use_container_width=True):
            cambios = False
            for i, row in df_editado.iterrows():
                v_nom = row["Partida Original"]
                n_nom = str(row["Nuevo Nombre"]).strip()
                borrar = row["Eliminar"]
                
                if borrar:
                    c.execute("DELETE FROM presupuestos WHERE partida=?", (v_nom,))
                    c.execute("DELETE FROM materiales WHERE partida=?", (v_nom,))
                    c.execute("DELETE FROM personal WHERE partida=?", (v_nom,))
                    c.execute("DELETE FROM asistencia WHERE partida=?", (v_nom,))
                    cambios = True
                elif n_nom and n_nom != v_nom:
                    c.execute("SELECT 1 FROM presupuestos WHERE partida=?", (n_nom,))
                    if not c.fetchone():
                        c.execute("UPDATE presupuestos SET partida=? WHERE partida=?", (n_nom, v_nom))
                        c.execute("UPDATE materiales SET partida=? WHERE partida=?", (n_nom, v_nom))
                        c.execute("UPDATE personal SET partida=? WHERE partida=?", (n_nom, v_nom))
                        c.execute("UPDATE asistencia SET partida=? WHERE partida=?", (n_nom, v_nom))
                        cambios = True
            
            if cambios:
                conn.commit()
                c.execute("SELECT DISTINCT partida FROM presupuestos")
                nuevas_partidas = [r[0] for r in c.fetchall() if r[0] and str(r[0]).strip() != ""]
                st.session_state['lista_partidas'] = nuevas_partidas
                st.success("Base de datos actualizada.")
                st.rerun()
    else:
        st.info("No hay partidas registradas.")

    st.markdown("<div class='section-header'>📥 RESPALDO DE BASE DE DATOS</div>", unsafe_allow_html=True)
    if os.path.exists('obra_nexus.db'):
        with open("obra_nexus.db", "rb") as file:
            st.download_button(
                label="DESCARGAR ARCHIVO LOCAL (.DB)", data=file, file_name="proyecto_nexus.db",
                mime="application/octet-stream", use_container_width=True
            )
    st.stop()

# ==========================================
# 6. MÓDULO DE TRABAJO
# ==========================================
st.markdown(f"""
    <div style="background-color: #FFFFFF; border-left: 8px solid {COLOR_VERDOSO}; padding: 15px 25px; border-radius: 8px; border-top: 1px solid #E2E8F0; border-right: 1px solid #E2E8F0; border-bottom: 1px solid #E2E8F0; display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
        <div>
            <p style="margin:0; color:#64748b; font-size:0.9rem; font-weight:bold; text-transform:uppercase;">Módulo Activo</p>
            <h2 style="color: {COLOR_VERDOSO} !important; margin: 0; font-size: 1.8rem; font-weight:900; text-transform:uppercase;">{st.session_state['partida_actual']}</h2>
        </div>
    </div>
""", unsafe_allow_html=True)

if st.button("⬅️ VOLVER AL PORTAFOLIO"):
    st.session_state['partida_actual'] = None
    st.rerun()

try:
    c.execute("SELECT total FROM presupuestos WHERE partida=?", (st.session_state['partida_actual'],))
    row_presupuesto = c.fetchone()
except sqlite3.OperationalError: row_presupuesto = None

presupuesto_actual_total = 0.0
if row_presupuesto and row_presupuesto[0] is not None:
    try: presupuesto_actual_total = float(row_presupuesto[0])
    except: pass
else: guardar_presupuesto_bd(st.session_state['partida_actual'], "Ingreso Directo del Total", 0.0, 0.0, 0.0)

# ==========================================
# RECOLECCIÓN DE DATOS
# ==========================================
df_personal_db = pd.read_sql(f"SELECT nombre, especialidad, jornal, almuerzo_costo FROM personal WHERE partida='{st.session_state['partida_actual']}'", conn)
lista_trabajadores_db = df_personal_db['nombre'].tolist() if not df_personal_db.empty else ["Juan Pérez"]

df_mat_db = pd.read_sql(f"SELECT * FROM materiales WHERE partida='{st.session_state['partida_actual']}'", conn)
if not df_mat_db.empty:
    df_mat_db['fecha_dt'] = pd.to_datetime(df_mat_db['fecha']).dt.date
    df_mat_db['cantidad'] = pd.to_numeric(df_mat_db['cantidad'], errors='coerce').fillna(0.0)
    df_mat_db['precio'] = pd.to_numeric(df_mat_db['precio'], errors='coerce').fillna(0.0)
    if 'descuento' in df_mat_db.columns: df_mat_db['descuento'] = pd.to_numeric(df_mat_db['descuento'], errors='coerce').fillna(0.0)
    else: df_mat_db['descuento'] = 0.0
else:
    df_mat_db['fecha_dt'] = pd.Series(dtype='object')
    df_mat_db['cantidad'] = pd.Series(dtype='float64')
    df_mat_db['precio'] = pd.Series(dtype='float64')
    df_mat_db['descuento'] = pd.Series(dtype='float64')

df_asist_db = pd.read_sql(f"SELECT * FROM asistencia WHERE partida='{st.session_state['partida_actual']}'", conn)
if not df_asist_db.empty: df_asist_db['fecha_dt'] = pd.to_datetime(df_asist_db['fecha']).dt.date
else: df_asist_db['fecha_dt'] = pd.Series(dtype='object')

trabajadores_registrados = lista_trabajadores_db

todas_las_fechas = []
if not df_mat_db.empty: todas_las_fechas.extend(df_mat_db['fecha_dt'].tolist())
if not df_asist_db.empty: todas_las_fechas.extend(df_asist_db['fecha_dt'].tolist())

if todas_las_fechas:
    min_fecha_obra = min(todas_las_fechas)
    max_fecha_obra = max(todas_las_fechas)
else:
    min_fecha_obra = date.today()
    max_fecha_obra = date.today()

start_current_week_res = min_fecha_obra - timedelta(days=min_fecha_obra.weekday())
datos_resumen_semanas = []
gasto_acum_temp = 0.0
semana_contador = 1

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
            
            c.execute("SELECT especialidad, jornal, almuerzo_costo FROM personal WHERE partida=? AND nombre=?", (st.session_state['partida_actual'], trab))
            p_row = c.fetchone()
            if p_row:
                esp_t, jornal_val, alm_val = p_row
                jornal_val = float(jornal_val) if pd.notna(jornal_val) else (120.0 if esp_t in ["Operario", "Enchapador", "Oficial"] else 100.0)
                alm_val = float(alm_val) if pd.notna(alm_val) else 7.0
            else:
                jornal_val, alm_val = 120.0, 7.0
            
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
    nombre_mes_es = meses_espanol[mes_num] if mes_num < len(meses_espanol) else ""

    datos_resumen_semanas.append({
        "Mes": nombre_mes_es, "Semana": f"Sem {semana_contador}",
        "Rango (Lunes a Sábado)": f"{start_current_week_res.strftime('%d/%m/%Y')} al {end_current_week_res.strftime('%d/%m/%Y')}",
        "Gasto Mano Obra (S/)": round(mo_sem, 2), "Gasto Materiales (S/)": round(mat_sem, 2),
        "Gasto Total Semanal (S/)": total_sem, "Gasto Acumulado (S/)": gasto_acum_temp, "Saldo vs Presupuesto (S/)": saldo_s
    })

    semana_contador += 1
    start_current_week_res += timedelta(days=7)

df_resumen_final = pd.DataFrame(datos_resumen_semanas)

gasto_mo_real_total = 0.0
gasto_mat_real_total = 0.0
gasto_total_acumulado = 0.0

if not df_resumen_final.empty:
    if "Gasto Mano Obra (S/)" in df_resumen_final.columns: gasto_mo_real_total = round(df_resumen_final["Gasto Mano Obra (S/)"].sum(), 2)
    if "Gasto Materiales (S/)" in df_resumen_final.columns: gasto_mat_real_total = round(df_resumen_final["Gasto Materiales (S/)"].sum(), 2)
    if "Gasto Acumulado (S/)" in df_resumen_final.columns: gasto_total_acumulado = round(df_resumen_final["Gasto Acumulado (S/)"].iloc[-1], 2)

# ==========================================
# 7. GRÁFICOS DINÁMICOS FINANCIEROS
# ==========================================
st.markdown("<div class='section-header'>📊 DASHBOARD FINANCIERO</div>", unsafe_allow_html=True)
col_graf_circulo, col_graf_linea = st.columns([1, 1.5])

with col_graf_circulo:
    labels = ['Materiales', 'Mano de Obra', 'Saldo Disponible']
    values = [gasto_mat_real_total, gasto_mo_real_total, max(0, presupuesto_actual_total - (gasto_mat_real_total + gasto_mo_real_total))] 
    colores = [COLOR_VERDOSO, '#ea580c', '#e2e8f0'] 
    
    if sum(values) == 0: values = [0.0001, 0.0001, max(1.0, presupuesto_actual_total)]
        
    fig_dona = go.Figure(data=[go.Pie(labels=labels, values=values, marker_colors=colores, hole=0.5)])
    fig_dona.update_layout(
        title=dict(text="Distribución de Costos", font=dict(color=COLOR_TEXTO, size=16, family="Segoe UI", weight="bold")),
        paper_bgcolor="#ffffff", plot_bgcolor="#ffffff", margin=dict(t=40, b=10, l=0, r=0),
        legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5, font=dict(color=COLOR_TEXTO, weight="bold"))
    )
    fig_dona.update_traces(hoverinfo='label+value', textinfo='percent', textfont_color='black', marker=dict(line=dict(color='#000000', width=1)))
    st.plotly_chart(fig_dona, use_container_width=True)

with col_graf_linea:
    semanas_graf = df_resumen_final['Semana'].tolist() if not df_resumen_final.empty else ['Sem 1']
    pres_total_linea = [presupuesto_actual_total] * len(semanas_graf)
    gasto_acumulado_graf = df_resumen_final['Gasto Acumulado (S/)'].tolist() if not df_resumen_final.empty else [0]
    
    fig_linea = go.Figure()
    fig_linea.add_trace(go.Scatter(x=semanas_graf, y=pres_total_linea, mode='lines', name='Presupuesto Asignado', line=dict(color='#10b981', dash='dash', width=2)))
    fig_linea.add_trace(go.Scatter(x=semanas_graf, y=gasto_acumulado_graf, mode='lines+markers', name='Costo Real', line=dict(color='#ea580c', width=3)))
    
    fig_linea.update_layout(
        title=dict(text="Curva S de Ejecución", font=dict(color=COLOR_TEXTO, size=16, family="Segoe UI", weight="bold")),
        paper_bgcolor="#ffffff", plot_bgcolor="#ffffff", margin=dict(t=40, b=10, l=10, r=10),
        legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5, font=dict(color=COLOR_TEXTO, weight="bold")),
        font=dict(color=COLOR_TEXTO, weight="bold"),
        xaxis=dict(gridcolor="#e2e8f0", showline=True, linewidth=1, linecolor='black'),
        yaxis=dict(tickprefix="S/ ", tickformat=",.0f", gridcolor="#e2e8f0", showline=True, linewidth=1, linecolor='black')
    )
    st.plotly_chart(fig_linea, use_container_width=True)

# ==========================================
# 8. CENTRO DE REGISTRO
# ==========================================
st.markdown("<div class='section-header'>📝 REGISTRO DE DATOS</div>", unsafe_allow_html=True)
tab_mat, tab_pers, tab_mo = st.tabs(["📦 Ingreso Materiales", "👤 Alta Personal", "👷 Tareo Asistencia"])

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
        
        calc_total_desc = cant * pre * (1 - (desc / 100.0))
        st.info(f"Subtotal: S/ {calc_total_desc:.2f}")
        
        col_mb1, col_mb2 = st.columns(2)
        with col_mb1: btn_guardar_mat = st.form_submit_button("GUARDAR MATERIAL", use_container_width=True)
        with col_mb2: btn_limpiar_mat = st.form_submit_button("LIMPIAR REGISTROS", use_container_width=True)

        if btn_guardar_mat:
            if mat_nom and und_final:
                c.execute("INSERT INTO materiales (partida, fecha, insumo, und, cantidad, precio, descuento) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                          (st.session_state['partida_actual'], str(f_mat), mat_nom, und_final, cant, pre, desc))
                conn.commit()
                st.success("Guardado.")
                st.rerun()
            else: st.warning("Complete campos.")
        if btn_limpiar_mat:
            c.execute("DELETE FROM materiales WHERE partida=? AND fecha=?", (st.session_state['partida_actual'], str(f_mat)))
            conn.commit()
            st.success("Eliminado.")
            st.rerun()
            
    try: df_mat_actual = pd.read_sql(f"SELECT fecha, insumo, und, cantidad, precio, descuento FROM materiales WHERE partida='{st.session_state['partida_actual']}' ORDER BY fecha DESC", conn)
    except: df_mat_actual = pd.DataFrame()
    if not df_mat_actual.empty: df_mat_actual['fecha'] = pd.to_datetime(df_mat_actual['fecha']).dt.date
    else: df_mat_actual = pd.DataFrame(columns=["fecha", "insumo", "und", "cantidad", "precio", "descuento"])
        
    df_mat_editado = st.data_editor(
        df_mat_actual, num_rows="dynamic", use_container_width=True, hide_index=True, key=f"editor_tabla_materiales_{st.session_state['partida_actual']}",
        column_config={
            "fecha": st.column_config.DateColumn("Fecha", format="DD/MM/YYYY"),
            "insumo": st.column_config.TextColumn("Insumo"), "und": st.column_config.TextColumn("U.M."),
            "cantidad": st.column_config.NumberColumn("Cant.", format="%.2f"),
            "precio": st.column_config.NumberColumn("Precio", format="S/ %.2f"),
            "descuento": st.column_config.NumberColumn("Desc.%", format="%.2f")
        }
    )
    if st.button("ACTUALIZAR TABLA MATERIALES", use_container_width=True):
        c.execute("DELETE FROM materiales WHERE partida=?", (st.session_state['partida_actual'],))
        for _, row in df_mat_editado.iterrows():
            if pd.notna(row["insumo"]) and str(row["insumo"]).strip() != "":
                try:
                    f_val = str(row["fecha"]).strip() if pd.notna(row["fecha"]) else str(date.today())
                    c.execute("INSERT INTO materiales (partida, fecha, insumo, und, cantidad, precio, descuento) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                              (st.session_state['partida_actual'], f_val, str(row["insumo"]).strip(), str(row["und"]).strip() if pd.notna(row["und"]) else "und", float(row["cantidad"]) if pd.notna(row["cantidad"]) else 1.0, float(row["precio"]) if pd.notna(row["precio"]) else 0.0, float(row["descuento"]) if "descuento" in row and pd.notna(row["descuento"]) else 0.0))
                except: pass
        conn.commit()
        st.success("Actualizado.")
        st.rerun()

with tab_pers:
    with st.form("form_nuevo_personal"):
        col_np1, col_np2 = st.columns(2)
        with col_np1: nuevo_nombre = st.text_input("Nombres y Apellidos")
        with col_np2: nueva_esp = st.selectbox("Especialidad", ["Operario", "Enchapador", "Oficial", "Ayudante / Peón", "Pintor", "Electricista", "Plomero"])
        col_np3, col_np4 = st.columns(2)
        with col_np3: def_jornal = st.number_input("Jornal (S/)", value=120.0, step=10.0)
        with col_np4: def_alm = st.number_input("Almuerzo (S/)", value=7.0, step=1.0)
        if st.form_submit_button("REGISTRAR PERSONAL", use_container_width=True):
            if nuevo_nombre:
                try:
                    c.execute("INSERT INTO personal (partida, nombre, especialidad, jornal, almuerzo_costo) VALUES (?, ?, ?, ?, ?)", (st.session_state['partida_actual'], nuevo_nombre.strip(), nueva_esp, def_jornal, def_alm))
                    conn.commit()
                    st.success("Guardado.")
                    st.rerun()
                except: st.warning("Ya existe.")
            else: st.warning("Ingrese nombre.")

    df_pers_actual = pd.read_sql(f"SELECT nombre, especialidad, jornal, almuerzo_costo FROM personal WHERE partida='{st.session_state['partida_actual']}'", conn)
    if df_pers_actual.empty: df_pers_actual = pd.DataFrame(columns=["nombre", "especialidad", "jornal", "almuerzo_costo"])
    df_pers_editado = st.data_editor(
        df_pers_actual, num_rows="dynamic", use_container_width=True, hide_index=True, key=f"editor_tabla_personal_{st.session_state['partida_actual']}",
        column_config={"nombre": st.column_config.TextColumn("Trabajador"), "especialidad": st.column_config.TextColumn("Categoría"), "jornal": st.column_config.NumberColumn("Jornal", format="S/ %.2f"), "almuerzo_costo": st.column_config.NumberColumn("Almuerzo", format="S/ %.2f")}
    )
    if st.button("ACTUALIZAR PERSONAL", use_container_width=True):
        c.execute("DELETE FROM personal WHERE partida=?", (st.session_state['partida_actual'],))
        for _, row in df_pers_editado.iterrows():
            if row["nombre"] and str(row["nombre"]).strip() != "":
                try: c.execute("INSERT INTO personal (partida, nombre, especialidad, jornal, almuerzo_costo) VALUES (?, ?, ?, ?, ?)", (st.session_state['partida_actual'], row["nombre"].strip(), row["especialidad"], float(row["jornal"]) if pd.notna(row["jornal"]) else 120.0, float(row["almuerzo_costo"]) if pd.notna(row["almuerzo_costo"]) else 7.0))
                except: pass
        conn.commit()
        st.success("Actualizado.")
        st.rerun()

with tab_mo:
    with st.form("form_mano_obra"):
        f_mo = st.date_input("Fecha", date.today(), key="f2")
        trabajador = st.selectbox("Personal", lista_trabajadores_db) if lista_trabajadores_db else st.text_input("Nombre")
        estado_asis = st.selectbox("Asistencia", ["Día Completo", "Medio Día", "Falta / Emergencia"])
        almuerzo_opc = st.radio("Almuerzo", ["Almuerza en obra / con comida de obra - S/ 0 extra", "Sale a comer afuera - S/ 7 extra"], horizontal=True)
        actividad = st.text_area("Actividad")
        col_fb1, col_fb2 = st.columns(2)
        with col_fb1: btn_guardar = st.form_submit_button("GUARDAR ASISTENCIA", use_container_width=True)
        with col_fb2: btn_limpiar_dia = st.form_submit_button("BORRAR DÍA", use_container_width=True)

        if btn_guardar and trabajador:
            c.execute("INSERT OR REPLACE INTO asistencia (partida, trabajador, fecha, estado, almuerzo, actividad) VALUES (?, ?, ?, ?, ?, ?)", (st.session_state['partida_actual'], trabajador, str(f_mo), estado_asis, almuerzo_opc, actividad))
            conn.commit()
            st.success("Guardado.")
            st.rerun()
        if btn_limpiar_dia and trabajador:
            c.execute("DELETE FROM asistencia WHERE partida=? AND trabajador=? AND fecha=?", (st.session_state['partida_actual'], trabajador, str(f_mo)))
            conn.commit()
            st.success("Borrado.")
            st.rerun()
            
    df_asist_edit_db = pd.read_sql(f"SELECT fecha, trabajador, estado, almuerzo, actividad FROM asistencia WHERE partida='{st.session_state['partida_actual']}' ORDER BY fecha DESC", conn)
    if not df_asist_edit_db.empty: df_asist_edit_db['fecha'] = pd.to_datetime(df_asist_edit_db['fecha']).dt.date
    else: df_asist_edit_db = pd.DataFrame(columns=["fecha", "trabajador", "estado", "almuerzo", "actividad"])
    df_asist_editado = st.data_editor(
        df_asist_edit_db, num_rows="dynamic", use_container_width=True, hide_index=True, key=f"editor_tabla_asistencia_{st.session_state['partida_actual']}",
        column_config={"fecha": st.column_config.DateColumn("Fecha", format="DD/MM/YYYY"), "trabajador": st.column_config.SelectboxColumn("Personal", options=lista_trabajadores_db if lista_trabajadores_db else ["Sin registrar"]), "estado": st.column_config.SelectboxColumn("Estado", options=["Día Completo", "Medio Día", "Falta / Emergencia"]), "almuerzo": st.column_config.SelectboxColumn("Almuerzo", options=["Almuerza en obra / con comida de obra - S/ 0 extra", "Sale a comer afuera - S/ 7 extra"]), "actividad": st.column_config.TextColumn("Nota")}
    )
    if st.button("ACTUALIZAR ASISTENCIA", use_container_width=True):
        c.execute("DELETE FROM asistencia WHERE partida=?", (st.session_state['partida_actual'],))
        for _, row in df_asist_editado.iterrows():
            if pd.notna(row["trabajador"]) and str(row["trabajador"]).strip() != "":
                try: c.execute("INSERT INTO asistencia (partida, trabajador, fecha, estado, almuerzo, actividad) VALUES (?, ?, ?, ?, ?, ?)", (st.session_state['partida_actual'], str(row["trabajador"]), str(row["fecha"]).strip() if pd.notna(row["fecha"]) else str(date.today()), str(row["estado"]) if pd.notna(row["estado"]) else "Día Completo", str(row["almuerzo"]) if pd.notna(row["almuerzo"]) else "Almuerza en obra / con comida de obra - S/ 0 extra", str(row["actividad"]) if pd.notna(row["actividad"]) else ""))
                except: pass
        conn.commit()
        st.success("Actualizado.")
        st.rerun()

# ==========================================
# 9. ALMANAQUE
# ==========================================
st.markdown("<div class='section-header'>📅 CALENDARIO DE ASISTENCIA</div>", unsafe_allow_html=True)
col_btn1, col_tit, col_btn2 = st.columns([1, 2, 1])
with col_btn1:
    if st.button("◀ Mes Anterior", use_container_width=True):
        if st.session_state['cal_mes'] == 1: st.session_state['cal_mes'] = 12; st.session_state['cal_ano'] -= 1
        else: st.session_state['cal_mes'] -= 1
        st.rerun()
with col_tit: st.markdown(f"<h3 style='text-align: center; font-weight:800; color:{COLOR_TEXTO} !important; margin:0;'>{meses_espanol[st.session_state['cal_mes']]} {st.session_state['cal_ano']}</h3>", unsafe_allow_html=True)
with col_btn2:
    if st.button("Mes Siguiente ▶", use_container_width=True):
        if st.session_state['cal_mes'] == 12: st.session_state['cal_mes'] = 1; st.session_state['cal_ano'] += 1
        else: st.session_state['cal_mes'] += 1
        st.rerun()

trabajador_seleccionado = st.selectbox("Personal:", trabajadores_registrados if trabajadores_registrados else ["Sin registros"])
col_cal, col_leyenda = st.columns([2.5, 1])

with col_cal:
    calendar.setfirstweekday(calendar.SUNDAY)
    mes_cal = calendar.monthcalendar(st.session_state['cal_ano'], st.session_state['cal_mes'])
    asistencia_trabajador = {}; comentarios_trabajador = {}
    if not df_asist_db.empty and trabajador_seleccionado != "Sin registros":
        df_t = df_asist_db[(df_asist_db['trabajador'] == trabajador_seleccionado)]
        for _, row in df_t.iterrows():
            try:
                f_reg = date.fromisoformat(str(row['fecha_dt']))
                if f_reg.year == st.session_state['cal_ano'] and f_reg.month == st.session_state['cal_mes']:
                    asistencia_trabajador[f_reg.day] = row['estado']
                    comentarios_trabajador[f_reg.day] = row['actividad'] if row['actividad'] else "Sin observaciones"
            except: pass

    html_cal = f"""
    <style>
    .cal-table {{ width: 100%; border-collapse: collapse; text-align: center; background: #fff; border: 1px solid #e2e8f0; border-radius:8px; }}
    .cal-table th {{ padding: 10px; background: #f8fafc; color: {COLOR_VERDOSO}; border-bottom: 2px solid #cbd5e1; font-weight:900; }}
    .cal-table td {{ padding: 15px; border: 1px solid #e2e8f0; font-weight: 800; color: #000; }}
    .cal-vacio {{ background-color: #f1f5f9; color: transparent !important; }}
    .cal-futuro {{ color: #94a3b8 !important; }}
    .cal-verde {{ background-color: {COLOR_VERDOSO}; color: white !important; border: 1px solid #000 !important; }}
    .cal-amarillo {{ background-color: #f59e0b; color: white !important; border: 1px solid #000 !important; }}
    .cal-rojo {{ background-color: #ef4444; color: white !important; border: 1px solid #000 !important; }}
    </style>
    <table class="cal-table"><tr><th>DOM</th><th>LUN</th><th>MAR</th><th>MIE</th><th>JUE</th><th>VIE</th><th>SAB</th></tr>
    """
    for semana in mes_cal:
        html_cal += "<tr>"
        for dia in semana:
            if dia == 0: html_cal += "<td class='cal-vacio'>0</td>"
            else:
                clase = "cal-futuro"; tooltip = "Sin registro"
                if dia in asistencia_trabajador:
                    est = asistencia_trabajador[dia]
                    tooltip = f"Actividad: {comentarios_trabajador.get(dia, '')}"
                    if "Completo" in est: clase = "cal-verde"
                    elif "Medio" in est: clase = "cal-amarillo"
                    else: clase = "cal-rojo"
                html_cal += f"<td class='{clase}' title='{tooltip}'>{dia}</td>"
        html_cal += "</tr>"
    html_cal += "</table>"
    st.markdown(html_cal, unsafe_allow_html=True)

with col_leyenda:
    st.markdown(f"""
        <div style="background-color: #ffffff; padding: 20px; border-radius: 8px; border: 1px solid #e2e8f0; height: 100%;">
            <h4 style="margin-top:0; border-bottom:1px solid #e2e8f0; padding-bottom:10px; color:{COLOR_VERDOSO};">Leyenda</h4>
            <p><span style="display:inline-block; width:15px; height:15px; background:{COLOR_VERDOSO}; margin-right:8px; border:1px solid #000;"></span> <b>Completo</b></p>
            <p><span style="display:inline-block; width:15px; height:15px; background:#f59e0b; margin-right:8px; border:1px solid #000;"></span> <b>Medio Día</b></p>
            <p><span style="display:inline-block; width:15px; height:15px; background:#ef4444; margin-right:8px; border:1px solid #000;"></span> <b>Falta</b></p>
        </div>
    """, unsafe_allow_html=True)

# ==========================================
# 10. MÓDULOS SEMANALES
# ==========================================
st.markdown("<div class='section-header'>🧾 VALORIZACIONES SEMANALES</div>", unsafe_allow_html=True)
first_day_month_sel = date(st.session_state['cal_ano'], st.session_state['cal_mes'], 1)
if st.session_state['cal_mes'] == 12: last_day_month_sel = date(st.session_state['cal_ano'] + 1, 1, 1) - timedelta(days=1)
else: last_day_month_sel = date(st.session_state['cal_ano'], st.session_state['cal_mes'] + 1, 1) - timedelta(days=1)

start_current_week_sel = first_day_month_sel - timedelta(days=first_day_month_sel.weekday())
semanas_opciones = []; semana_map = {}; idx = 1
while start_current_week_sel <= last_day_month_sel:
    end_current_week_sel = start_current_week_sel + timedelta(days=5)
    label = f"Valorización {idx}: {start_current_week_sel.strftime('%d/%m/%Y')} al {end_current_week_sel.strftime('%d/%m/%Y')}"
    semanas_opciones.append(label); semana_map[label] = (start_current_week_sel, end_current_week_sel)
    idx += 1; start_current_week_sel += timedelta(days=7)

semana_seleccionada = st.selectbox("Seleccione el Periodo:", semanas_opciones)
fecha_inicio, fecha_fin = semana_map[semana_seleccionada]

tab_planilla, tab_materiales = st.tabs(["👷 Planilla de Personal", "📦 Relación de Materiales"])
with tab_planilla:
    gasto_semana_mo = 0
    df_asist_semana = df_asist_db.loc[(df_asist_db['fecha_dt'] >= fecha_inicio) & (df_asist_db['fecha_dt'] <= fecha_fin) & (df_asist_db['partida'] == st.session_state['partida_actual'])] if not df_asist_db.empty else pd.DataFrame()

    for trabajador in trabajadores_registrados:
        df_esp = df_pers_actual[df_pers_actual['nombre'] == trabajador]
        especialidad_trab = df_esp['especialidad'].values[0] if not df_esp.empty else "Obrero"
        jornal_bd_val = float(df_esp['jornal'].values[0]) if not df_esp.empty and pd.notna(df_esp['jornal'].values[0]) else 120.0
        alm_bd_val = float(df_esp['almuerzo_costo'].values[0]) if not df_esp.empty and pd.notna(df_esp['almuerzo_costo'].values[0]) else 7.0

        df_t_sem = df_asist_semana[df_asist_semana['trabajador'] == trabajador] if not df_asist_semana.empty else pd.DataFrame()
        c_comp = len(df_t_sem[df_t_sem['estado'] == 'Día Completo']) if not df_t_sem.empty else 0
        c_med = len(df_t_sem[df_t_sem['estado'] == 'Medio Día']) if not df_t_sem.empty else 0
        c_alm = len(df_t_sem[df_t_sem['almuerzo'].str.startswith('Sale', na=False)]) if not df_t_sem.empty else 0

        with st.expander(f"👷 {especialidad_trab} — {trabajador}", expanded=True):
            col_w1, col_w2, col_w3 = st.columns(3)
            with col_w1:
                jornal_dia = st.number_input("Jornal (S/)", value=jornal_bd_val, step=10.0, key=f"jornal_{trabajador}")
                costo_almuerzo = st.number_input("Almuerzo (S/)", value=alm_bd_val, step=1.0, key=f"alm_costo_{trabajador}")
            with col_w2:
                comentario_nota = st.text_input("Anotaciones", value="", key=f"comentario_{trabajador}")
            with col_w3:
                monto_extra = st.number_input("Ajuste (S/)", value=0.0, step=10.0, key=f"monto_{trabajador}")

            pago_completos = c_comp * jornal_dia; pago_medios = c_med * (jornal_dia / 2.0); total_almuerzos = c_alm * costo_almuerzo
            total_trabajador = pago_completos + pago_medios + total_almuerzos + monto_extra
            gasto_semana_mo += total_trabajador

            st.markdown(f"""
                <table style="width:100%; text-align: left; border-collapse: collapse; margin-top:10px; border:1px solid #000;">
                    <tr style='border-bottom: 2px solid #000; background:#f8fafc;'><th style='padding:5px; color:{COLOR_VERDOSO};'>Concepto</th><th style='color:{COLOR_VERDOSO};'>Cant.</th><th style='color:{COLOR_VERDOSO};'>Tasa (S/)</th><th style='color:{COLOR_VERDOSO};'>Parcial (S/)</th></tr>
                    <tr><td style='padding:5px; font-weight:bold;'>Días Completos</td><td><b>{c_comp}</b></td><td><b>{jornal_dia:.2f}</b></td><td><b>{pago_completos:.2f}</b></td></tr>
                    <tr><td style='padding:5px; font-weight:bold;'>Medios Días</td><td><b>{c_med}</b></td><td><b>{jornal_dia/2:.2f}</b></td><td><b>{pago_medios:.2f}</b></td></tr>
                    <tr><td style='padding:5px; font-weight:bold;'>Almuerzos Extra</td><td><b>{c_alm}</b></td><td><b>{costo_almuerzo:.2f}</b></td><td><b>{total_almuerzos:.2f}</b></td></tr>
                    <tr style='background-color:#f1f5f9; border-top:2px solid #000;'><td style='padding:8px;'><b>TOTAL PAGO:</b></td><td colspan="3" style='text-align:right;'><h4 style="color: {COLOR_VERDOSO}; margin: 0; font-weight:900;">S/ {total_trabajador:.2f}</h4></td></tr>
                </table>
            """, unsafe_allow_html=True)

    st.markdown(f"<div style='background-color: {COLOR_VERDOSO}; padding: 15px; border-radius: 8px; text-align: right; color: white; margin-top: 20px;'><h3 style='margin:0; color:white !important; font-weight:900;'>SUBTOTAL PLANILLA: S/ {gasto_semana_mo:,.2f}</h3></div>", unsafe_allow_html=True)

with tab_materiales:
    df_mat_filtrado = df_mat_db.loc[(df_mat_db['fecha_dt'] >= fecha_inicio) & (df_mat_db['fecha_dt'] <= fecha_fin) & (df_mat_db['partida'] == st.session_state['partida_actual'])].copy() if not df_mat_db.empty else pd.DataFrame()
    if not df_mat_filtrado.empty:
        df_mat_filtrado['Parcial'] = df_mat_filtrado['cantidad'] * df_mat_filtrado['precio'] * (1 - (df_mat_filtrado['descuento'] / 100.0))
        df_mats_show = df_mat_filtrado[['fecha', 'insumo', 'und', 'cantidad', 'precio', 'descuento', 'Parcial']].rename(columns={'fecha':'Fecha', 'insumo':'Descripción', 'und':'Und', 'cantidad':'Cant.', 'precio':'P.U.', 'descuento':'Desc.%', 'Parcial':'Monto (S/)'})
        df_mats_show['Cant.'] = df_mats_show['Cant.'].apply(lambda x: f"{x:.2f}")
        df_mats_show['P.U.'] = df_mats_show['P.U.'].apply(lambda x: f"{x:,.2f}")
        df_mats_show['Monto (S/)'] = df_mats_show['Monto (S/)'].apply(lambda x: f"{x:,.2f}")
    else: df_mats_show = pd.DataFrame(columns=['Fecha', 'Descripción', 'Und', 'Cant.', 'P.U.', 'Desc.%', 'Monto (S/)'])
        
    st.dataframe(df_mats_show, use_container_width=True, hide_index=True)
    gasto_semana_mat = df_mat_filtrado['Parcial'].sum() if not df_mat_filtrado.empty else 0.0
    st.markdown(f"<div style='background-color: {COLOR_VERDOSO}; padding: 15px; border-radius: 8px; text-align: right; color: white; margin-top: 10px;'><h3 style='margin:0; color:white !important; font-weight:900;'>SUBTOTAL MATERIALES: S/ {gasto_semana_mat:,.2f}</h3></div>", unsafe_allow_html=True)

# ==========================================
# 11. TABLA RESUMEN FINANCIERO
# ==========================================
st.markdown("<div class='section-header'>📈 CONSOLIDADO FINANCIERO</div>", unsafe_allow_html=True)
df_resumen_mostrar = df_resumen_final.copy()
if not df_resumen_mostrar.empty:
    df_resumen_mostrar.loc["Total"] = {
        "Mes": "", "Semana": "TOTAL", "Rango (Lunes a Sábado)": "",
        "Gasto Mano Obra (S/)": gasto_mo_real_total, "Gasto Materiales (S/)": gasto_mat_real_total,
        "Gasto Total Semanal (S/)": round(gasto_mo_real_total + gasto_mat_real_total, 2),
        "Gasto Acumulado (S/)": "", "Saldo vs Presupuesto (S/)": ""
    }
    for col in ["Gasto Mano Obra (S/)", "Gasto Materiales (S/)", "Gasto Total Semanal (S/)", "Gasto Acumulado (S/)", "Saldo vs Presupuesto (S/)"]:
        df_resumen_mostrar[col] = df_resumen_mostrar[col].apply(lambda x: f"{x:,.2f}" if isinstance(x, (int, float)) else x)

st.dataframe(df_resumen_mostrar, use_container_width=True, hide_index=True)

saldo_final = round(presupuesto_actual_total - gasto_total_acumulado, 2)
color_saldo = COLOR_VERDOSO if saldo_final >= 0 else "#ef4444"

col_res1, col_res2, col_res3 = st.columns(3)
with col_res1: st.markdown(f"<div style='background:white; padding:20px; border-radius:8px; border:1px solid #e2e8f0; border-top:5px solid #0f172a; text-align:center;'><h4 style='margin:0; color:#475569;'>Pto. Aprobado</h4><h2 style='margin:10px 0 0 0; color:#0f172a; font-weight:900;'>S/ {presupuesto_actual_total:,.2f}</h2></div>", unsafe_allow_html=True)
with col_res2: st.markdown(f"<div style='background:white; padding:20px; border-radius:8px; border:1px solid #e2e8f0; border-top:5px solid #0d6efd; text-align:center;'><h4 style='margin:0; color:#475569;'>Costo Real Acumulado</h4><h2 style='margin:10px 0 0 0; color:#0d6efd; font-weight:900;'>S/ {gasto_total_acumulado:,.2f}</h2></div>", unsafe_allow_html=True)
with col_res3: st.markdown(f"<div style='background:white; padding:20px; border-radius:8px; border:1px solid #e2e8f0; border-top:5px solid {color_saldo}; text-align:center;'><h4 style='margin:0; color:#475569;'>{'Saldo a Favor' if saldo_final>=0 else 'Sobregiro'}</h4><h2 style='margin:10px 0 0 0; color:{color_saldo}; font-weight:900;'>S/ {abs(saldo_final):,.2f}</h2></div>", unsafe_allow_html=True)

# ==========================================
# 12. GENERADOR PDF MODO PROFESIONAL BLANCO
# ==========================================
st.markdown("<div class='section-header'>🖨️ EMISIÓN DE EXPEDIENTE (PDF BLANCO)</div>", unsafe_allow_html=True)
if st.button("GENERAR INFORME TÉCNICO OFICIAL (PDF)", use_container_width=True):
    dias_es_map_rep = {0: 'Lunes', 1: 'Martes', 2: 'Miércoles', 3: 'Jueves', 4: 'Viernes', 5: 'Sábado', 6: 'Domingo'}
    fecha_impresion_str = date.today().strftime('%d/%m/%Y')
    
    first_m = date(st.session_state['cal_ano'], st.session_state['cal_mes'], 1)
    if st.session_state['cal_mes'] == 12: last_m = date(st.session_state['cal_ano'] + 1, 1, 1) - timedelta(days=1)
    else: last_m = date(st.session_state['cal_ano'], st.session_state['cal_mes'] + 1, 1) - timedelta(days=1)
    
    curr_w = first_m - timedelta(days=first_m.weekday())
    semanas_mes_lista = []
    idx_s = 1
    while curr_w <= last_m:
        end_w = curr_w + timedelta(days=5)
        semanas_mes_lista.append((f"Semana {idx_s}", curr_w, end_w))
        idx_s += 1
        curr_w += timedelta(days=7)

    labels_print = ['Materiales', 'Mano de Obra', 'Saldo Restante']
    values_print = [gasto_mat_real_total, gasto_mo_real_total, max(0, presupuesto_actual_total - (gasto_mat_real_total + gasto_mo_real_total))]
    colores_print = [COLOR_VERDOSO, '#ea580c', '#cbd5e1']

    fig_dona_print = go.Figure(data=[go.Pie(labels=labels_print, values=values_print, marker_colors=colores_print)])
    fig_dona_print.update_layout(title=dict(text="Distribución de Costos", font=dict(color="#000", size=13, weight="bold")), paper_bgcolor="white", plot_bgcolor="white", margin=dict(t=30, b=10, l=10, r=10), legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5, font=dict(color="#000", size=9, weight="bold")), width=480, height=280)
    fig_dona_print.update_traces(texttemplate='%{percent}<br>S/ %{value:,.2f}', textposition='inside', textfont=dict(size=9.5, color='white', weight='bold'), insidetextorientation='horizontal')

    semanas_graf_p = df_resumen_final['Semana'].tolist() if not df_resumen_final.empty else ['Sem 1']
    pres_total_linea_p = [presupuesto_actual_total] * len(semanas_graf_p)
    gasto_acumulado_graf_p = df_resumen_final['Gasto Acumulado (S/)'].tolist() if not df_resumen_final.empty else [0]

    fig_linea_print = go.Figure()
    fig_linea_print.add_trace(go.Scatter(x=semanas_graf_p, y=pres_total_linea_p, mode='lines', name='Presupuesto Total', line=dict(color=COLOR_VERDOSO, dash='dash', width=2)))
    fig_linea_print.add_trace(go.Scatter(x=semanas_graf_p, y=gasto_acumulado_graf_p, mode='lines+markers', name='Gasto Acumulado', line=dict(color='#ea580c', width=3)))
    fig_linea_print.update_layout(title=dict(text="Curva Presupuesto vs Gasto Acumulado", font=dict(color="#000", size=13, weight="bold")), paper_bgcolor="white", plot_bgcolor="white", margin=dict(t=30, b=40, l=70, r=20), legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5, font=dict(color="#000", size=9, weight="bold")), font=dict(color="#000", weight="bold"), xaxis=dict(tickangle=0, gridcolor="#e2e8f0", showline=True, linecolor='#000'), yaxis=dict(tickprefix="S/ ", tickformat=",.0f", gridcolor="#e2e8f0", showline=True, linecolor='#000'), width=480, height=280)

    html_dona_str = fig_dona_print.to_html(include_plotlyjs='inline', full_html=False, config={'displayModeBar': False})
    html_linea_str = fig_linea_print.to_html(include_plotlyjs='inline', full_html=False, config={'displayModeBar': False})

    html_reporte = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Informe Técnico - Nexus Obra</title>
        <style>
            @page {{ size: A4; margin: 15mm; }}
            body {{ font-family: 'Segoe UI', Arial, sans-serif; color: #000000; margin: 0; padding: 0; font-size: 8.5pt; line-height: 1.3; background: #ffffff; }}
            .header {{ text-align: center; margin-bottom: 20px; }}
            .header h1 {{ font-size: 14pt; margin: 0 0 5px 0; color: {COLOR_VERDOSO}; text-transform: uppercase; font-weight: 900; }}
            .header h2 {{ font-size: 10pt; margin: 0; color: #000000; font-weight: bold; }}
            .info-box {{ font-size: 9pt; margin-bottom: 15px; font-weight: bold; line-height:1.5; }}
            .info-box span {{ font-weight: normal; }}
            .section-title {{ font-size: 10.5pt; font-weight: bold; color: {COLOR_VERDOSO}; margin-top: 15px; margin-bottom: 8px; border-bottom: 1.5px solid {COLOR_VERDOSO}; padding-bottom: 3px; page-break-after: avoid; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 5px; margin-bottom: 10px; font-size: 8pt; }}
            th, td {{ border: 1px solid #000000; padding: 5px; text-align: left; color: #000000; font-weight: bold; }}
            th {{ background: #f8fafc; color: {COLOR_VERDOSO}; font-weight: 900; text-transform: uppercase; text-align: center; }}
            .text-right {{ text-align: right; }}
            .text-center {{ text-align: center; }}
            .grafico-center {{ text-align: center; margin: 10px auto; page-break-inside: avoid; display: flex; justify-content: center; }}
            .worker-section {{ page-break-inside: avoid; margin-bottom: 15px; }}
            .worker-title {{ font-size: 9.5pt; font-weight: 900; color: {COLOR_VERDOSO}; border-bottom: 1px dashed #000; margin-bottom: 5px; padding-bottom: 2px; }}
            @media print {{ button {{ display: none; }} }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>SISTEMA DE CONTROL DE PROYECTOS - NEXUS OBRA</h1>
            <h2>Informe Técnico de Control Presupuestal y Mano de Obra</h2>
        </div>
        
        <div class="info-box">
            Proyecto / Descripción: <span>Trabajo de construcción y acabados.</span><br>
            Ubicación: <span>Distrito Ayacucho, Provincia Huamanga, Departamento Ayacucho</span><br>
            Partida Evaluada: <span>{st.session_state['partida_actual']}</span><br>
            Cliente: <span>Cliente Principal</span><br>
            Mes Evaluado: <span>{meses_espanol[st.session_state['cal_mes']]} {st.session_state['cal_ano']}</span><br>
            Costo al: <span>{date.today().strftime('%d/%m/%Y')}</span> | Fecha de Impresión: <span>{fecha_impresion_str}</span>
        </div>

        <div class="section-title">1. Análisis Financiero y Resumen Global</div>
        <p style="margin: 4px 0 6px 0; font-weight:bold;">
            El presente informe detalla el estado económico y operativo histórico de la partida {st.session_state['partida_actual']}. 
            Hasta la fecha de corte, se ha asignado un presupuesto total de S/ {presupuesto_actual_total:,.2f}, 
            registrando un gasto acumulado de S/ {gasto_total_acumulado:,.2f}. 
            Esto representa un estado financiero de {'SALDO A FAVOR' if saldo_final >= 0 else 'SOBREGIRO'} 
            por un monto de S/ {abs(saldo_final):,.2f}.
        </p>

        <div class="section-title">2. Análisis Gráfico de Ejecución (Distribución y Tendencia)</div>
        <div class="grafico-center">{html_dona_str}</div>
        <div class="grafico-center">{html_linea_str}</div>

        <div class="section-title">3. Resumen General por Semanas de Trabajo (Lunes a Sábado)</div>
        <table>
            <thead>
                <tr>
                    <th>Mes</th>
                    <th>Semana</th>
                    <th>Rango (Lunes a Sábado)</th>
                    <th class="text-right">Mano Obra (S/)</th>
                    <th class="text-right">Materiales (S/)</th>
                    <th class="text-right">Total Semanal (S/)</th>
                    <th class="text-right">Acumulado (S/)</th>
                    <th class="text-right">Saldo (S/)</th>
                </tr>
            </thead>
            <tbody>
    """
    
    for _, row in df_resumen_final.iterrows():
        html_reporte += f"""
                <tr>
                    <td class="text-center">{row['Mes']}</td>
                    <td class="text-center">{row['Semana']}</td>
                    <td class="text-center">{row['Rango (Lunes a Sábado)']}</td>
                    <td class="text-right">S/ {row['Gasto Mano Obra (S/)']:,.2f}</td>
                    <td class="text-right">S/ {row['Gasto Materiales (S/)']:,.2f}</td>
                    <td class="text-right">S/ {row['Gasto Total Semanal (S/)']:,.2f}</td>
                    <td class="text-right">S/ {row['Gasto Acumulado (S/)']:,.2f}</td>
                    <td class="text-right">S/ {row['Saldo vs Presupuesto (S/)']:,.2f}</td>
                </tr>
        """
        
    html_reporte += f"""
                <tr>
                    <td colspan="3" class="text-right" style="color:{COLOR_VERDOSO};">TOTAL GENERAL:</td>
                    <td class="text-right">S/ {gasto_mo_real_total:,.2f}</td>
                    <td class="text-right">S/ {gasto_mat_real_total:,.2f}</td>
                    <td class="text-right">S/ {gasto_mo_real_total + gasto_mat_real_total:,.2f}</td>
                    <td></td>
                    <td></td>
                </tr>
            </tbody>
        </table>

        <div class="section-title">4. Detalle de Planilla por Trabajador (Desglose de las Semanas del Mes)</div>
    """
    
    for _, pers in df_pers_actual.iterrows():
        t_nombre = pers['nombre']
        t_esp = pers['especialidad']
        
        html_reporte += f"""
        <div class="worker-section">
            <div class="worker-title">Obrero: {t_esp} - {t_nombre}</div>
        """
        
        for s_nombre, s_ini, s_fin in semanas_mes_lista:
            df_t_s = pd.DataFrame()
            if not df_asist_db.empty:
                m_ts = (df_asist_db['trabajador'] == t_nombre) & (df_asist_db['fecha_dt'] >= s_ini) & (df_asist_db['fecha_dt'] <= s_fin) & (df_asist_db['partida'] == st.session_state['partida_actual'])
                df_t_s = df_asist_db.loc[m_ts].sort_values('fecha')
                
            c_comp = len(df_t_s[df_t_s['estado'] == 'Día Completo']) if not df_t_s.empty else 0
            c_med = len(df_t_s[df_t_s['estado'] == 'Medio Día']) if not df_t_s.empty else 0
            c_alm = len(df_t_s[df_t_s['almuerzo'].str.startswith('Sale', na=False)]) if not df_t_s.empty else 0
            
            jornal_v = float(pers['jornal']) if pd.notna(pers['jornal']) else 120.0
            alm_v = float(pers['almuerzo_costo']) if pd.notna(pers['almuerzo_costo']) else 7.0
            
            tot_s_trab = (c_comp * jornal_v) + (c_med * (jornal_v / 2.0)) + (c_alm * alm_v)
            
            html_reporte += f"<p style='margin: 4px 0 2px 0; font-size: 8.5pt; font-weight:bold;'>{s_nombre} ({s_ini.strftime('%d/%m/%Y')} al {s_fin.strftime('%d/%m/%Y')}):</p>"
            
            if not df_t_s.empty:
                html_reporte += f"""
                <table>
                    <thead>
                        <tr>
                            <th width="15%">Fecha</th>
                            <th width="15%">Día</th>
                            <th width="20%">Estado Asistencia</th>
                            <th width="20%">Almuerzo</th>
                            <th width="30%">Actividad / Observación</th>
                        </tr>
                    </thead>
                    <tbody>
                """
                for _, r_as in df_t_s.iterrows():
                    dt_f = date.fromisoformat(str(r_as['fecha']))
                    d_nombre = dias_es_map_rep[dt_f.weekday()]
                    html_reporte += f"<tr><td class='text-center'>{dt_f.strftime('%d/%m/%Y')}</td><td class='text-center'>{d_nombre}</td><td>{r_as['estado']}</td><td>{r_as['almuerzo']}</td><td>{r_as['actividad']}</td></tr>"
                html_reporte += "</tbody></table>"
            else:
                html_reporte += "<table><tr><td class='text-center'><i>Sin registros en esta semana.</i></td></tr></table>"
                
            html_reporte += f"<div style='text-align:right; font-size:8.5pt; font-weight:bold; margin-bottom:8px;'>Subtotal {s_nombre}: S/ {tot_s_trab:,.2f}</div>"
        
        html_reporte += "</div>"

    html_reporte += f"""
        <div class="section-title">5. Control de Materiales e Insumos (Mes Completo)</div>
        <table>
            <thead>
                <tr>
                    <th>Fecha</th>
                    <th>Insumo / Material</th>
                    <th class="text-center">UND</th>
                    <th class="text-right">Cantidad</th>
                    <th class="text-right">P. Unitario (S/)</th>
                    <th class="text-right">Desc. (%)</th>
                    <th class="text-right">Parcial (S/)</th>
                </tr>
            </thead>
            <tbody>
    """
    
    gasto_mat_rep = 0.0
    if not df_mat_db.empty:
        df_mat_rep = df_mat_db.sort_values('fecha')
        for _, r_m in df_mat_rep.iterrows():
            dt_m = date.fromisoformat(str(r_m['fecha']))
            d_m_nom = dias_es_map_rep[dt_m.weekday()]
            cant_m = float(r_m['cantidad'])
            prec_m = float(r_m['precio'])
            desc_m = float(r_m['descuento']) if 'descuento' in r_m and pd.notna(r_m['descuento']) else 0.0
            parc_m = cant_m * prec_m * (1 - (desc_m / 100.0))
            gasto_mat_rep += parc_m
            
            html_reporte += f"<tr><td class='text-center'>{dt_m.strftime('%d/%m/%Y')}<br>({d_m_nom})</td><td>{r_m['insumo']}</td><td class='text-center'>{r_m['und']}</td><td class='text-right'>{cant_m:,.2f}</td><td class='text-right'>S/ {prec_m:,.2f}</td><td class='text-right'>{desc_m:.2f}</td><td class='text-right'>S/ {parc_m:,.2f}</td></tr>"
            
    if gasto_mat_rep == 0.0:
        html_reporte += "<tr><td colspan='7' class='text-center'><i>Sin movimientos registrados en este periodo.</i></td></tr>"
        
    html_reporte += f"""
            </tbody>
        </table>
        <div style='text-align:right; font-size:9pt; font-weight:bold; margin-top:5px; color:{COLOR_VERDOSO};'>TOTAL MATERIALES MES: S/ {gasto_mat_rep:,.2f}</div>
        
        <br><br>
        <div style="text-align: center; font-size: 8pt; font-weight:bold; border-top: 1.5px solid #000; padding-top: 6px;">
            Reporte Ejecutivo Oficial Plataforma Nexus Obra Ayacucho, Perú
        </div>
        
        <script> setTimeout(function() {{ window.print(); }}, 1500); </script>
    </body>
    </html>
    """
    st.components.v1.html(html_reporte, height=800, scrolling=True)
