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
# CONSTANTES GLOBALES
# ==========================================
meses_espanol = ["", "ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO", "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"]

# 1. CONFIGURACIÓN INICIAL Y TEMA
st.set_page_config(
    page_title="Nexus Obra - Control Profesional", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# 2. BASE DE DATOS PERMANENTE Y TABLAS
conn = sqlite3.connect('obra_nexus.db', timeout=10.0, check_same_thread=False)
c = conn.cursor()

c.execute('CREATE TABLE IF NOT EXISTS usuarios (email TEXT UNIQUE, password TEXT)')
c.execute('CREATE TABLE IF NOT EXISTS personal (partida TEXT, nombre TEXT, especialidad TEXT, jornal REAL DEFAULT 120.0, almuerzo_costo REAL DEFAULT 7.0, UNIQUE(partida, nombre))')
c.execute('CREATE TABLE IF NOT EXISTS materiales (partida TEXT, fecha TEXT, insumo TEXT, und TEXT, cantidad REAL, precio REAL, descuento REAL DEFAULT 0.0)')
c.execute('CREATE TABLE IF NOT EXISTS asistencia (partida TEXT, trabajador TEXT, fecha TEXT, estado TEXT, almuerzo TEXT, actividad TEXT, UNIQUE(partida, trabajador, fecha))')
c.execute('CREATE TABLE IF NOT EXISTS presupuestos (partida TEXT PRIMARY KEY, modo TEXT, total REAL, materiales REAL, mano_obra REAL, fecha_creacion TEXT)')
conn.commit()

# Actualizaciones de Tablas para versiones anteriores
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
    except:
        return False

def verificar_usuario(email, clave):
    c.execute('SELECT * FROM usuarios WHERE email=? AND password=?', (email, encriptar_clave(clave)))
    return c.fetchone() is not None

# --- FUNCIÓN EXPERTA PARA GUARDAR PRESUPUESTO ---
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

# ==========================================
# CARGAR PARTIDAS DESDE LA BASE DE DATOS
# ==========================================
if 'lista_partidas' not in st.session_state: 
    c.execute("SELECT DISTINCT partida FROM presupuestos")
    partidas_bd = [row[0] for row in c.fetchall() if row[0] is not None and str(row[0]).strip() != ""]
    st.session_state['lista_partidas'] = partidas_bd if partidas_bd else ["Acabados 2do Nivel"]

# ==========================================
# 3. PANTALLA DE INICIO (LOGIN)
# ==========================================
if not st.session_state['autenticado']:
    st.markdown("""
        <style>
        .stApp { background-color: #f4f5f7; }
        .login-box { background: white; padding: 40px; border-radius: 4px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); border: 1px solid #e2e8f0; max-width: 400px; margin: auto; margin-top: 50px;}
        h1, h2, p { color: #1e293b !important; font-family: 'Segoe UI', sans-serif;}
        div[data-testid="stButton"] button { background-color: #0056b3 !important; color: white !important; border: none !important; border-radius: 3px; font-weight: 600; width: 100%; transition: 0.2s;}
        div[data-testid="stButton"] button:hover { background-color: #004494 !important; }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("<div style='text-align: center; margin-top: 50px;'><h1>NEXUS OBRA</h1><p style='color: #64748b;'>Software de Control y Presupuestos</p></div>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        if not st.session_state['mostrar_registro']:
            with st.form("form_login"):
                st.markdown("<h3 style='text-align: center; font-size: 1.2rem;'>Iniciar Sesión</h3>", unsafe_allow_html=True)
                email_login = st.text_input("Correo Electrónico")
                clave_login = st.text_input("Contraseña", type="password")
                btn_login = st.form_submit_button("INGRESAR AL SISTEMA")
                
                if btn_login:
                    if verificar_usuario(email_login, clave_login):
                        st.session_state['autenticado'] = True
                        st.session_state['usuario_actual'] = email_login
                        st.rerun()
                    else:
                        st.error("Credenciales incorrectas.")
            
            if st.button("Crear una cuenta nueva"):
                st.session_state['mostrar_registro'] = True
                st.rerun()
        else:
            with st.form("form_registro"):
                st.markdown("<h3 style='text-align: center; font-size: 1.2rem;'>Registro de Usuario</h3>", unsafe_allow_html=True)
                email_reg = st.text_input("Nuevo Correo")
                clave_reg = st.text_input("Crear Contraseña", type="password")
                btn_reg = st.form_submit_button("REGISTRAR CUENTA")
                
                if btn_reg:
                    if email_reg and clave_reg:
                        if agregar_usuario(email_reg, clave_reg):
                            st.success("Cuenta creada. Vuelve al login.")
                            st.session_state['mostrar_registro'] = False
                            st.rerun()
                        else:
                            st.error("El correo ya está registrado.")
                    else:
                        st.warning("Completa los campos.")
            
            if st.button("Volver al Login"):
                st.session_state['mostrar_registro'] = False
                st.rerun()
    st.stop()

# ==========================================
# 4. DISEÑO INTERIOR (ESTILO SOFTWARE PROFESIONAL TIPO REVIT/DELFIN)
# ==========================================
st.markdown("""
    <style>
    /* Fondo principal y textos */
    .stApp { background-color: #f0f2f5 !important; color: #1e293b !important; font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; }
    h1, h2, h3, h4, p, label, span, div { color: #1e293b !important; }
    
    /* Estilo de Contenedores y Tarjetas */
    div[data-testid="metric-container"], .stForm, div[data-testid="stExpander"] { 
        background-color: #ffffff !important; 
        border: 1px solid #cbd5e1 !important; 
        border-radius: 4px !important; 
        box-shadow: 0 1px 2px rgba(0,0,0,0.05); 
    }
    
    /* Botones Estilo Software (Autodesk/Blue) */
    div[data-testid="stButton"] button { 
        background-color: #0056b3 !important; 
        color: #ffffff !important; 
        border: 1px solid #004494 !important; 
        border-radius: 3px !important; 
        font-weight: 600 !important; 
        text-transform: uppercase; 
        font-size: 0.85rem !important;
        letter-spacing: 0.5px;
        transition: all 0.2s ease-in-out; 
    }
    div[data-testid="stButton"] button:hover { 
        background-color: #004494 !important; 
        box-shadow: 0 2px 4px rgba(0,0,0,0.15); 
    }
    
    /* Inputs de texto y números */
    .stTextInput input, .stNumberInput input, .stSelectbox div, .stTextArea textarea { 
        background-color: #ffffff !important; 
        color: #0f172a !important; 
        border: 1px solid #94a3b8 !important; 
        border-radius: 3px !important; 
        font-size: 0.95rem;
    }
    .stTextInput input:focus, .stNumberInput input:focus {
        border-color: #0056b3 !important;
        box-shadow: 0 0 0 1px #0056b3 !important;
    }
    
    /* DataFrames y Tablas */
    .stDataFrame { border: 1px solid #cbd5e1 !important; border-radius: 4px; background: white;}
    
    /* Títulos de sección personalizados */
    .section-header {
        background-color: #ffffff;
        border-left: 5px solid #0056b3;
        padding: 10px 15px;
        margin-top: 20px;
        margin-bottom: 15px;
        border-top: 1px solid #e2e8f0;
        border-right: 1px solid #e2e8f0;
        border-bottom: 1px solid #e2e8f0;
        font-weight: bold;
        font-size: 1.1rem;
        color: #0f172a;
        box-shadow: 0 1px 2px rgba(0,0,0,0.02);
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 5. GESTOR DE PARTIDAS (MENÚ PRINCIPAL ALINEADO)
# ==========================================
if st.session_state['partida_actual'] is None:
    st.markdown("""
        <div style="background-color: #1e293b; padding: 20px; border-radius: 4px; margin-bottom: 20px; text-align: center;">
            <h1 style="color: white !important; margin: 0; font-size: 1.8rem; letter-spacing: 1px;">🏢 GESTOR DE PROYECTOS Y PARTIDAS</h1>
            <p style="color: #94a3b8 !important; margin-top: 5px; font-size: 0.9rem;">Panel Administrativo - Nexus Obra v2.0</p>
        </div>
    """, unsafe_allow_html=True)
    
    col_p1, col_space, col_p2 = st.columns([1, 0.1, 1])
    
    with col_p1:
        st.markdown("<div class='section-header'>📂 SELECCIONAR PARTIDA EXISTENTE</div>", unsafe_allow_html=True)
        partida_seleccionada = st.selectbox("Base de datos activa:", st.session_state['lista_partidas'], label_visibility="collapsed")
        
        presup_actual_gestion = 0.0
        if partida_seleccionada:
            c.execute("SELECT total FROM presupuestos WHERE partida=?", (partida_seleccionada,))
            res_p = c.fetchone()
            if res_p and res_p[0] is not None:
                try: presup_actual_gestion = float(res_p[0])
                except: presup_actual_gestion = 0.0
        
        def auto_guardar_presup_existente():
            nuevo_val = st.session_state[f"edit_gestor_{partida_seleccionada}"]
            guardar_presupuesto_bd(partida_seleccionada, "Ingreso Directo del Total", nuevo_val, 0.0, 0.0)

        nuevo_presupuesto_edicion = st.number_input("Presupuesto Asignado (S/):", value=presup_actual_gestion, step=500.0, key=f"edit_gestor_{partida_seleccionada}", on_change=auto_guardar_presup_existente)
        
        if st.button("INGRESAR AL PANEL DE TRABAJO", use_container_width=True):
            if partida_seleccionada:
                guardar_presupuesto_bd(partida_seleccionada, "Ingreso Directo del Total", nuevo_presupuesto_edicion, 0.0, 0.0)
                st.session_state['partida_actual'] = partida_seleccionada
                st.rerun()
            else:
                st.warning("Seleccione una partida primero.")
            
    with col_p2:
        st.markdown("<div class='section-header'>➕ CREAR NUEVA PARTIDA</div>", unsafe_allow_html=True)
        nueva_partida = st.text_input("Nombre de partida", placeholder="Ej: Vaciado de Losas", label_visibility="collapsed")
        presupuesto_inicial_crear = st.number_input("Presupuesto Inicial Estimado (S/)", min_value=0.0, value=0.0, step=500.0, key="nuevo_presup_creacion")
        
        if st.button("CREAR Y ENTRAR A LA PARTIDA", use_container_width=True):
            if nueva_partida.strip():
                if nueva_partida not in st.session_state['lista_partidas']:
                    st.session_state['lista_partidas'].append(nueva_partida)
                guardar_presupuesto_bd(nueva_partida, "Ingreso Directo del Total", presupuesto_inicial_crear, 0.0, 0.0)
                st.session_state['partida_actual'] = nueva_partida
                st.rerun()
            else: 
                st.error("El nombre de la partida no puede estar vacío.")
                
    st.write("---")
    
    # ==========================================
    # CUADRO ADMINISTRADOR DE PARTIDAS
    # ==========================================
    st.markdown("<div class='section-header'>⚙️ ADMINISTRADOR GENERAL DE PARTIDAS</div>", unsafe_allow_html=True)
    st.write("Vista técnica detallada. Modifique el nombre de los expedientes o elimínelos permanentemente de la base de datos.")
    
    if st.session_state['lista_partidas']:
        datos_admin = []
        for p in st.session_state['lista_partidas']:
            c.execute("SELECT total, fecha_creacion FROM presupuestos WHERE partida=?", (p,))
            row_pres = c.fetchone()
            
            presupuesto_val = 0.0
            if row_pres and row_pres[0] is not None:
                try: presupuesto_val = float(row_pres[0])
                except: presupuesto_val = 0.0
                    
            fecha_creacion = row_pres[1] if (row_pres and len(row_pres) > 1 and row_pres[1]) else str(date.today())
            
            c.execute("SELECT COUNT(*) FROM personal WHERE partida=?", (p,))
            row_pers = c.fetchone()
            cant_personal = int(row_pers[0]) if row_pers else 0
            
            datos_admin.append({
                "Partida Original": p,
                "Fecha Creación": fecha_creacion,
                "Personal Reg.": cant_personal,
                "Presupuesto (S/)": presupuesto_val,
                "Nuevo Nombre": p,
                "Eliminar": False
            })
            
        df_admin = pd.DataFrame(datos_admin)
        
        df_editado = st.data_editor(
            df_admin,
            hide_index=True,
            use_container_width=True,
            disabled=["Partida Original", "Fecha Creación", "Personal Reg.", "Presupuesto (S/)"], 
            column_config={
                "Partida Original": st.column_config.TextColumn("Partida (Lectura)", disabled=True),
                "Fecha Creación": st.column_config.TextColumn("Fecha", disabled=True),
                "Personal Reg.": st.column_config.NumberColumn("Personal", disabled=True),
                "Presupuesto (S/)": st.column_config.NumberColumn("Pto. Asignado", format="S/ %.2f", disabled=True),
                "Nuevo Nombre": st.column_config.TextColumn("Renombrar Partida (Click para editar)"),
                "Eliminar": st.column_config.CheckboxColumn("Borrar Datos", default=False)
            },
            key="tabla_admin_partidas"
        )
        
        if st.button("APLICAR CAMBIOS EN LA BASE DE DATOS", use_container_width=True):
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
                st.success("Base de datos estructurada actualizada correctamente.")
                st.rerun()
    else:
        st.info("El proyecto actual no contiene partidas estructurales.")

    st.write("---")
    st.markdown("<div class='section-header'>📥 EXPORTAR PROYECTO (BACKUP .DB)</div>", unsafe_allow_html=True)
    if os.path.exists('obra_nexus.db'):
        with open("obra_nexus.db", "rb") as file:
            st.download_button(
                label="DESCARGAR BASE DE DATOS LOCAL",
                data=file,
                file_name="proyecto_obra_backup.db",
                mime="application/octet-stream"
            )

    st.stop()

# ==========================================
# 6. DASHBOARD DE LA PARTIDA Y PRESUPUESTO
# ==========================================
col_top1, col_top2 = st.columns([4, 1])
with col_top1:
    st.markdown(f"<h2 style='color: #0056b3 !important; font-size: 1.8rem; margin-top: 10px;'>📑 MÓDULO: {st.session_state['partida_actual'].upper()}</h2>", unsafe_allow_html=True)
with col_top2:
    st.write("") 
    if st.button("CERRAR PARTIDA (VOLVER)"):
        st.session_state['partida_actual'] = None
        st.rerun()

# Cargar el presupuesto actual
try:
    c.execute("SELECT total FROM presupuestos WHERE partida=?", (st.session_state['partida_actual'],))
    row_presupuesto = c.fetchone()
except sqlite3.OperationalError:
    row_presupuesto = None

presupuesto_actual_total = 0.0
if row_presupuesto and row_presupuesto[0] is not None:
    try: presupuesto_actual_total = float(row_presupuesto[0])
    except: presupuesto_actual_total = 0.0

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
    if 'descuento' in df_mat_db.columns:
        df_mat_db['descuento'] = pd.to_numeric(df_mat_db['descuento'], errors='coerce').fillna(0.0)
    else:
        df_mat_db['descuento'] = 0.0
else:
    df_mat_db['fecha_dt'] = pd.Series(dtype='object')
    df_mat_db['cantidad'] = pd.Series(dtype='float64')
    df_mat_db['precio'] = pd.Series(dtype='float64')
    df_mat_db['descuento'] = pd.Series(dtype='float64')

df_asist_db = pd.read_sql(f"SELECT * FROM asistencia WHERE partida='{st.session_state['partida_actual']}'", conn)
if not df_asist_db.empty:
    df_asist_db['fecha_dt'] = pd.to_datetime(df_asist_db['fecha']).dt.date
else:
    df_asist_db['fecha_dt'] = pd.Series(dtype='object')

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
                jornal_val = float(jornal_val) if pd.notna(jornal_val) else 120.0
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
        "Mes": nombre_mes_es,
        "Semana": f"Sem {semana_contador}",
        "Rango (Lunes a Sábado)": f"{start_current_week_res.strftime('%d/%m/%Y')} al {end_current_week_res.strftime('%d/%m/%Y')}",
        "Gasto Mano Obra (S/)": round(mo_sem, 2),
        "Gasto Materiales (S/)": round(mat_sem, 2),
        "Gasto Total Semanal (S/)": total_sem,
        "Gasto Acumulado (S/)": gasto_acum_temp,
        "Saldo vs Presupuesto (S/)": saldo_s
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
# 7. GRÁFICOS DINÁMICOS SUPERIORES (ESTILO PROFESIONAL)
# ==========================================
st.markdown("<div class='section-header'>📊 DASHBOARD DE RENDIMIENTO</div>", unsafe_allow_html=True)
col_graf_circulo, col_graf_linea = st.columns([1, 1.5])

with col_graf_circulo:
    labels = ['Materiales', 'Mano de Obra', 'Saldo Restante']
    values = [gasto_mat_real_total, gasto_mo_real_total, max(0, presupuesto_actual_total - (gasto_mat_real_total + gasto_mo_real_total))] 
    colores = ['#0284c7', '#ea580c', '#10b981'] # Azul técnico, Naranja, Verde
    
    if sum(values) == 0: values = [0.0001, 0.0001, max(1.0, presupuesto_actual_total)]
        
    fig_dona = go.Figure(data=[go.Pie(labels=labels, values=values, marker_colors=colores, hole=0.4)])
    fig_dona.update_layout(
        title=dict(text="Distribución de Costos", font=dict(color="#0f172a", size=14)),
        paper_bgcolor="#ffffff", plot_bgcolor="#ffffff", margin=dict(t=40, b=10, l=0, r=0),
        legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5, font=dict(color="#334155"))
    )
    fig_dona.update_traces(hoverinfo='label+value', textinfo='percent', textfont_color='white', marker=dict(line=dict(color='#ffffff', width=2)))
    st.plotly_chart(fig_dona, use_container_width=True)

with col_graf_linea:
    semanas_graf = df_resumen_final['Semana'].tolist() if not df_resumen_final.empty else ['Sem 1']
    pres_total_linea = [presupuesto_actual_total] * len(semanas_graf)
    gasto_acumulado_graf = df_resumen_final['Gasto Acumulado (S/)'].tolist() if not df_resumen_final.empty else [0]
    
    fig_linea = go.Figure()
    fig_linea.add_trace(go.Scatter(x=semanas_graf, y=pres_total_linea, mode='lines', name='Presupuesto Asignado', line=dict(color='#10b981', dash='dash', width=2)))
    fig_linea.add_trace(go.Scatter(x=semanas_graf, y=gasto_acumulado_graf, mode='lines+markers', name='Gasto Ejecutado', line=dict(color='#0284c7', width=3)))
    
    fig_linea.update_layout(
        title=dict(text="Curva S de Gastos vs Presupuesto", font=dict(color="#0f172a", size=14)),
        paper_bgcolor="#ffffff", plot_bgcolor="#ffffff", margin=dict(t=40, b=10, l=10, r=10),
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5, font=dict(color="#334155")),
        font=dict(color="#334155"),
        xaxis=dict(gridcolor="#f1f5f9"),
        yaxis=dict(tickprefix="S/ ", tickformat=",.0f", gridcolor="#f1f5f9")
    )
    st.plotly_chart(fig_linea, use_container_width=True)

# ==========================================
# 8. CENTRO DE REGISTRO
# ==========================================
st.markdown("<div class='section-header'>📝 MÓDULO DE INGRESO DE DATOS</div>", unsafe_allow_html=True)
tab_mat, tab_pers, tab_mo = st.tabs(["📦 Registro de Materiales", "👤 Directorio de Personal", "👷 Control de Asistencia"])

with tab_mat:
    with st.form("form_materiales"):
        f_mat = st.date_input("Fecha de Adquisición", date.today(), key="f1")
        mat_nom = st.text_input("Descripción del Insumo / Material")
        
        tipo_und = st.selectbox("Unidad de Medida", ["bol (Bolsas)", "caja (Cajas)", "m3 (Metro cúbico)", "m2 (Metro cuadrado)", "kg (Kilogramo)", "und (Unidad)", "gln (Galón)", "glb (Global)", "pza (Pieza)", "ml (Metro lineal)", "Otra unidad..."])
        und_final = tipo_und.split(" ")[0] if tipo_und != "Otra unidad..." else st.text_input("Especifique su unidad:")
        
        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1: cant = st.number_input("Cantidad", min_value=0.01, value=1.0)
        with col_m2: pre = st.number_input("P. Unitario (S/)", min_value=0.0)
        with col_m3: desc = st.number_input("Descuento (%)", min_value=0.0, max_value=100.0, value=0.0, step=0.01)
        
        calc_total_desc = cant * pre * (1 - (desc / 100.0))
        st.info(f"Total a computar: S/ {calc_total_desc:.2f}")
        
        col_mb1, col_mb2 = st.columns(2)
        with col_mb1: btn_guardar_mat = st.form_submit_button("REGISTRAR INSUMO", use_container_width=True)
        with col_mb2: btn_limpiar_mat = st.form_submit_button("LIMPIAR REGISTROS DEL DÍA", use_container_width=True)

        if btn_guardar_mat:
            if mat_nom and und_final:
                c.execute("INSERT INTO materiales (partida, fecha, insumo, und, cantidad, precio, descuento) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                          (st.session_state['partida_actual'], str(f_mat), mat_nom, und_final, cant, pre, desc))
                conn.commit()
                st.success("Material guardado correctamente.")
                st.rerun()
            else: st.warning("Complete la descripción y unidad.")

        if btn_limpiar_mat:
            c.execute("DELETE FROM materiales WHERE partida=? AND fecha=?", (st.session_state['partida_actual'], str(f_mat)))
            conn.commit()
            st.success("Registros eliminados.")
            st.rerun()
            
    st.write("---")
    st.markdown("#### 📋 Base de Datos de Materiales")
    
    try: df_mat_actual = pd.read_sql(f"SELECT fecha, insumo, und, cantidad, precio, descuento FROM materiales WHERE partida='{st.session_state['partida_actual']}' ORDER BY fecha DESC", conn)
    except:
        df_mat_actual = pd.read_sql(f"SELECT fecha, insumo, und, cantidad, precio FROM materiales WHERE partida='{st.session_state['partida_actual']}' ORDER BY fecha DESC", conn)
        df_mat_actual['descuento'] = 0.0
        
    if not df_mat_actual.empty: df_mat_actual['fecha'] = pd.to_datetime(df_mat_actual['fecha']).dt.date
    else: df_mat_actual = pd.DataFrame(columns=["fecha", "insumo", "und", "cantidad", "precio", "descuento"])
        
    df_mat_editado = st.data_editor(
        df_mat_actual, num_rows="dynamic", use_container_width=True, hide_index=True, key=f"editor_tabla_materiales_{st.session_state['partida_actual']}",
        column_config={
            "fecha": st.column_config.DateColumn("Fecha", format="DD/MM/YYYY"),
            "insumo": st.column_config.TextColumn("Descripción"),
            "und": st.column_config.TextColumn("Unidad"),
            "cantidad": st.column_config.NumberColumn("Cant.", format="%.2f"),
            "precio": st.column_config.NumberColumn("Precio U.", format="S/ %.2f"),
            "descuento": st.column_config.NumberColumn("Desc. (%)", format="%.2f")
        }
    )
    
    if st.button("ACTUALIZAR INVENTARIO DE MATERIALES", use_container_width=True):
        c.execute("DELETE FROM materiales WHERE partida=?", (st.session_state['partida_actual'],))
        for _, row in df_mat_editado.iterrows():
            if pd.notna(row["insumo"]) and str(row["insumo"]).strip() != "":
                try:
                    f_val = str(row["fecha"]).strip() if pd.notna(row["fecha"]) else str(date.today())
                    c_val = float(row["cantidad"]) if pd.notna(row["cantidad"]) else 1.0
                    p_val = float(row["precio"]) if pd.notna(row["precio"]) else 0.0
                    u_val = str(row["und"]).strip() if pd.notna(row["und"]) else "und"
                    d_val = float(row["descuento"]) if "descuento" in row and pd.notna(row["descuento"]) else 0.0
                    c.execute("INSERT INTO materiales (partida, fecha, insumo, und, cantidad, precio, descuento) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                              (st.session_state['partida_actual'], f_val, str(row["insumo"]).strip(), u_val, c_val, p_val, d_val))
                except: pass
        conn.commit()
        st.success("Inventario actualizado.")
        st.rerun()
                
with tab_pers:
    with st.form("form_nuevo_personal"):
        col_np1, col_np2 = st.columns(2)
        with col_np1: nuevo_nombre = st.text_input("Nombres y Apellidos")
        with col_np2: nueva_esp = st.selectbox("Especialidad Técnica", ["Operario", "Enchapador", "Oficial", "Ayudante / Peón", "Pintor", "Electricista", "Plomero"])
        
        col_np3, col_np4 = st.columns(2)
        default_jornal_init = 120.0 if nueva_esp in ["Operario", "Enchapador", "Oficial"] else (100.0 if "Peón" in nueva_esp or "Ayudante" in nueva_esp else 120.0)
        with col_np3: def_jornal = st.number_input("Jornal Base Contractual (S/)", value=default_jornal_init, step=10.0)
        with col_np4: def_alm = st.number_input("Asignación Almuerzo (S/)", value=7.0, step=1.0)

        if st.form_submit_button("AÑADIR PERSONAL AL PROYECTO", use_container_width=True):
            if nuevo_nombre:
                try:
                    c.execute("INSERT INTO personal (partida, nombre, especialidad, jornal, almuerzo_costo) VALUES (?, ?, ?, ?, ?)", 
                              (st.session_state['partida_actual'], nuevo_nombre.strip(), nueva_esp, def_jornal, def_alm))
                    conn.commit()
                    st.success("Personal registrado.")
                    st.rerun()
                except: st.warning("El trabajador ya existe en esta partida.")
            else: st.warning("Se requiere un nombre válido.")

    st.write("---")
    st.markdown("#### 📋 Directorio Activo")
    df_pers_actual = pd.read_sql(f"SELECT nombre, especialidad, jornal, almuerzo_costo FROM personal WHERE partida='{st.session_state['partida_actual']}'", conn)
    if df_pers_actual.empty: df_pers_actual = pd.DataFrame(columns=["nombre", "especialidad", "jornal", "almuerzo_costo"])
        
    df_pers_editado = st.data_editor(
        df_pers_actual, num_rows="dynamic", use_container_width=True, hide_index=True, key=f"editor_tabla_personal_{st.session_state['partida_actual']}",
        column_config={
            "nombre": st.column_config.TextColumn("Trabajador"),
            "especialidad": st.column_config.TextColumn("Especialidad"),
            "jornal": st.column_config.NumberColumn("Jornal (S/)", format="S/ %.2f"),
            "almuerzo_costo": st.column_config.NumberColumn("Almuerzo (S/)", format="S/ %.2f")
        }
    )
    
    if st.button("ACTUALIZAR DIRECTORIO TÉCNICO", use_container_width=True):
        c.execute("DELETE FROM personal WHERE partida=?", (st.session_state['partida_actual'],))
        for _, row in df_pers_editado.iterrows():
            if row["nombre"] and str(row["nombre"]).strip() != "":
                try:
                    esp_w = row["especialidad"]
                    j_default = 120.0 if esp_w in ["Operario", "Enchapador", "Oficial"] else (100.0 if "Peón" in esp_w or "Ayudante" in esp_w else 120.0)
                    j_val = float(row["jornal"]) if "jornal" in row and pd.notna(row["jornal"]) else j_default
                    a_val = float(row["almuerzo_costo"]) if "almuerzo_costo" in row and pd.notna(row["almuerzo_costo"]) else 7.0
                    c.execute("INSERT INTO personal (partida, nombre, especialidad, jornal, almuerzo_costo) VALUES (?, ?, ?, ?, ?)", 
                              (st.session_state['partida_actual'], row["nombre"].strip(), esp_w, j_val, a_val))
                except: pass
        conn.commit()
        st.success("Directorio guardado.")
        st.rerun()

with tab_mo:
    with st.form("form_mano_obra"):
        f_mo = st.date_input("Fecha de Control", date.today(), key="f2")
        
        if lista_trabajadores_db: trabajador = st.selectbox("Seleccionar Obrero", lista_trabajadores_db)
        else: trabajador = st.text_input("Nombre del Obrero (Pre-registre en Directorio primero)")

        estado_asis = st.selectbox("Estado Operativo", ["Día Completo", "Medio Día", "Falta / Emergencia"])
        almuerzo_opc = st.radio("Condición de Alimentación", ["Almuerza en obra / con comida de obra - S/ 0 extra", "Sale a comer afuera - S/ 7 extra"], horizontal=True)
        actividad = st.text_area("Notas / Actividad Ejecutada", placeholder="Ej: Avance eje 2-3.")
        
        col_fb1, col_fb2 = st.columns(2)
        with col_fb1: btn_guardar = st.form_submit_button("REGISTRAR ASISTENCIA", use_container_width=True)
        with col_fb2: btn_limpiar_dia = st.form_submit_button("ELIMINAR REGISTRO DIARIO", use_container_width=True)

        if btn_guardar:
            if trabajador:
                c.execute("INSERT OR REPLACE INTO asistencia (partida, trabajador, fecha, estado, almuerzo, actividad) VALUES (?, ?, ?, ?, ?, ?)", 
                          (st.session_state['partida_actual'], trabajador, str(f_mo), estado_asis, almuerzo_opc, actividad))
                conn.commit()
                st.success("Parte diario registrado.")
                st.rerun()
            else: st.warning("Seleccione personal.")

        if btn_limpiar_dia:
            if trabajador:
                c.execute("DELETE FROM asistencia WHERE partida=? AND trabajador=? AND fecha=?", (st.session_state['partida_actual'], trabajador, str(f_mo)))
                conn.commit()
                st.success("Parte diario borrado.")
                st.rerun()
                
    st.write("---")
    st.markdown("#### 📋 Matriz de Asistencia Histórica")
    df_asist_edit_db = pd.read_sql(f"SELECT fecha, trabajador, estado, almuerzo, actividad FROM asistencia WHERE partida='{st.session_state['partida_actual']}' ORDER BY fecha DESC", conn)
    
    if not df_asist_edit_db.empty: df_asist_edit_db['fecha'] = pd.to_datetime(df_asist_edit_db['fecha']).dt.date
    else: df_asist_edit_db = pd.DataFrame(columns=["fecha", "trabajador", "estado", "almuerzo", "actividad"])

    lista_opciones_trabajadores = lista_trabajadores_db if lista_trabajadores_db else ["Sin registrar"]
    
    df_asist_editado = st.data_editor(
        df_asist_edit_db, num_rows="dynamic", use_container_width=True, hide_index=True, key=f"editor_tabla_asistencia_{st.session_state['partida_actual']}",
        column_config={
            "fecha": st.column_config.DateColumn("Fecha", format="DD/MM/YYYY"),
            "trabajador": st.column_config.SelectboxColumn("Personal", options=lista_opciones_trabajadores),
            "estado": st.column_config.SelectboxColumn("Jornada", options=["Día Completo", "Medio Día", "Falta / Emergencia"]),
            "almuerzo": st.column_config.SelectboxColumn("Alimentación", options=["Almuerza en obra / con comida de obra - S/ 0 extra", "Sale a comer afuera - S/ 7 extra"]),
            "actividad": st.column_config.TextColumn("Observaciones")
        }
    )

    if st.button("ACTUALIZAR MATRIZ DE ASISTENCIA", use_container_width=True):
        c.execute("DELETE FROM asistencia WHERE partida=?", (st.session_state['partida_actual'],))
        for _, row in df_asist_editado.iterrows():
            if pd.notna(row["trabajador"]) and str(row["trabajador"]).strip() != "":
                try:
                    f_val = str(row["fecha"]).strip() if pd.notna(row["fecha"]) else str(date.today())
                    est_val = str(row["estado"]) if pd.notna(row["estado"]) else "Día Completo"
                    alm_val = str(row["almuerzo"]) if pd.notna(row["almuerzo"]) else "Almuerza en obra / con comida de obra - S/ 0 extra"
                    act_val = str(row["actividad"]) if pd.notna(row["actividad"]) else ""
                    c.execute("INSERT INTO asistencia (partida, trabajador, fecha, estado, almuerzo, actividad) VALUES (?, ?, ?, ?, ?, ?)", 
                              (st.session_state['partida_actual'], str(row["trabajador"]), f_val, est_val, alm_val, act_val))
                except: pass
        conn.commit()
        st.success("Matriz actualizada correctamente.")
        st.rerun()

# ==========================================
# 9. ALMANAQUE INTERACTIVO CON TOOLTIP
# ==========================================
st.markdown("<div class='section-header'>📅 CONTROL MENSUAL DE CALENDARIO</div>", unsafe_allow_html=True)

col_btn1, col_tit, col_btn2 = st.columns([1, 2, 1])
with col_btn1:
    if st.button("◀ Mes Anterior", key="btn_ant", use_container_width=True):
        if st.session_state['cal_mes'] == 1: st.session_state['cal_mes'] = 12; st.session_state['cal_ano'] -= 1
        else: st.session_state['cal_mes'] -= 1
        st.rerun()
with col_tit:
    st.markdown(f"<h3 style='text-align: center; color: #0f172a !important; margin: 0;'>{meses_espanol[st.session_state['cal_mes']]} {st.session_state['cal_ano']}</h3>", unsafe_allow_html=True)
with col_btn2:
    if st.button("Mes Siguiente ▶", key="btn_sig", use_container_width=True):
        if st.session_state['cal_mes'] == 12: st.session_state['cal_mes'] = 1; st.session_state['cal_ano'] += 1
        else: st.session_state['cal_mes'] += 1
        st.rerun()

st.write("<br>", unsafe_allow_html=True)
if trabajadores_registrados: trabajador_seleccionado = st.selectbox("Filtro por Personal:", trabajadores_registrados)
else: trabajador_seleccionado = st.selectbox("Filtro por Personal:", ["Sin registros"])

col_cal, col_leyenda = st.columns([2.5, 1])

with col_cal:
    calendar.setfirstweekday(calendar.SUNDAY)
    mes_cal = calendar.monthcalendar(st.session_state['cal_ano'], st.session_state['cal_mes'])

    asistencia_trabajador = {}
    comentarios_trabajador = {}
    if not df_asist_db.empty and trabajador_seleccionado != "Sin registros":
        df_t = df_asist_db[(df_asist_db['trabajador'] == trabajador_seleccionado)]
        for _, row in df_t.iterrows():
            try:
                f_reg = date.fromisoformat(str(row['fecha_dt']))
                if f_reg.year == st.session_state['cal_ano'] and f_reg.month == st.session_state['cal_mes']:
                    asistencia_trabajador[f_reg.day] = row['estado']
                    comentarios_trabajador[f_reg.day] = row['actividad'] if row['actividad'] else "Sin observaciones"
            except: pass

    html_cal = """
    <style>
    .cal-wrapper { background-color: #ffffff; border-radius: 4px; border: 1px solid #cbd5e1; padding: 15px; width: 100%; box-sizing: border-box;}
    .cal-table { width: 100%; border-collapse: separate; border-spacing: 4px; text-align: center; font-family: 'Segoe UI', sans-serif;}
    .cal-table th { padding: 8px 0; color: #475569; font-weight: bold; font-size: 1rem; border-bottom: 2px solid #e2e8f0; }
    .cal-table td { padding: 10px 0; border-radius: 3px; font-size: 1.1rem; font-weight: bold; border: 1px solid #e2e8f0; position: relative; cursor: pointer; }
    .cal-vacio { background-color: #ffffff; color: transparent !important; border: none !important; cursor: default !important; }
    .cal-futuro { background-color: #f8fafc; color: #94a3b8; }
    .cal-verde { background-color: #10b981; color: white !important; border-color: #059669; }
    .cal-amarillo { background-color: #f59e0b; color: white !important; border-color: #d97706; }
    .cal-rojo { background-color: #ef4444; color: white !important; border-color: #dc2626; }
    </style>
    <div class="cal-wrapper"><table class="cal-table"><tr><th>DOM</th><th>LUN</th><th>MAR</th><th>MIÉ</th><th>JUE</th><th>VIE</th><th>SÁB</th></tr>
    """
    for semana in mes_cal:
        html_cal += "<tr>"
        for dia in semana:
            if dia == 0: html_cal += "<td class='cal-vacio'>0</td>"
            else:
                clase = "cal-futuro"
                tooltip = "Sin registro"
                if dia in asistencia_trabajador:
                    est = asistencia_trabajador[dia]
                    tooltip = f"Actividad: {comentarios_trabajador.get(dia, '')}"
                    if "Completo" in est: clase = "cal-verde"
                    elif "Medio" in est: clase = "cal-amarillo"
                    else: clase = "cal-rojo"
                html_cal += f"<td class='{clase}' title='{tooltip}'>{dia}</td>"
        html_cal += "</tr>"
    html_cal += "</table></div>"
    st.markdown(html_cal, unsafe_allow_html=True)

with col_leyenda:
    st.markdown("""
        <div style="background-color: #ffffff; padding: 20px; border-radius: 4px; border: 1px solid #cbd5e1; height: 100%;">
            <h4 style="color: #0f172a; margin-top: 0; margin-bottom: 15px; border-bottom: 1px solid #e2e8f0; padding-bottom: 5px;">🎨 Leyenda Técnica</h4>
            <p><span style="display:inline-block; width:16px; height:16px; background-color:#10b981; border-radius:2px; margin-right:8px; vertical-align: middle;"></span> <b style='color:#334155;'>Jornada Completa</b></p>
            <p><span style="display:inline-block; width:16px; height:16px; background-color:#f59e0b; border-radius:2px; margin-right:8px; vertical-align: middle;"></span> <b style='color:#334155;'>Media Jornada</b></p>
            <p><span style="display:inline-block; width:16px; height:16px; background-color:#ef4444; border-radius:2px; margin-right:8px; vertical-align: middle;"></span> <b style='color:#334155;'>Ausencia / Falta</b></p>
        </div>
    """, unsafe_allow_html=True)

# ==========================================
# 10. MÓDULOS SEMANALES
# ==========================================
st.markdown("<div class='section-header'>🧾 REPORTE Y CIERRE DE VALORIZACIÓN SEMANAL</div>", unsafe_allow_html=True)

first_day_month_sel = date(st.session_state['cal_ano'], st.session_state['cal_mes'], 1)
if st.session_state['cal_mes'] == 12: last_day_month_sel = date(st.session_state['cal_ano'] + 1, 1, 1) - timedelta(days=1)
else: last_day_month_sel = date(st.session_state['cal_ano'], st.session_state['cal_mes'] + 1, 1) - timedelta(days=1)

start_current_week_sel = first_day_month_sel - timedelta(days=first_day_month_sel.weekday())
semanas_opciones = []
semana_map = {}
idx = 1

while start_current_week_sel <= last_day_month_sel:
    end_current_week_sel = start_current_week_sel + timedelta(days=5) # Lunes a Sábado
    label = f"Valorización {idx}: {start_current_week_sel.strftime('%d/%m/%Y')} al {end_current_week_sel.strftime('%d/%m/%Y')}"
    semanas_opciones.append(label)
    semana_map[label] = (start_current_week_sel, end_current_week_sel)
    idx += 1
    start_current_week_sel += timedelta(days=7)

semana_seleccionada = st.selectbox("Seleccione el Periodo de Ejecución:", semanas_opciones)
fecha_inicio, fecha_fin = semana_map[semana_seleccionada]

tab_planilla, tab_materiales = st.tabs(["👷 Planilla Acumulada (Personal)", "📦 Relación de Materiales Suministrados"])

with tab_planilla:
    gasto_semana_mo = 0
    if not df_asist_db.empty:
        mask_asis = (df_asist_db['fecha_dt'] >= fecha_inicio) & (df_asist_db['fecha_dt'] <= fecha_fin) & (df_asist_db['partida'] == st.session_state['partida_actual'])
        df_asist_semana = df_asist_db.loc[mask_asis]
    else: df_asist_semana = pd.DataFrame(columns=['trabajador', 'fecha', 'estado', 'almuerzo'])

    for trabajador in trabajadores_registrados:
        df_esp = df_pers_actual[df_pers_actual['nombre'] == trabajador]
        especialidad_trab = df_esp['especialidad'].values[0] if not df_esp.empty else "Obrero"
        
        esp_w = especialidad_trab
        jornal_default_reg = 120.0 if esp_w in ["Operario", "Enchapador", "Oficial"] else (100.0 if "Peón" in esp_w or "Ayudante" in esp_w else 120.0)
        jornal_bd_val = float(df_esp['jornal'].values[0]) if not df_esp.empty and pd.notna(df_esp['jornal'].values[0]) else jornal_default_reg
        alm_bd_val = float(df_esp['almuerzo_costo'].values[0]) if not df_esp.empty and pd.notna(df_esp['almuerzo_costo'].values[0]) else 7.0

        df_t_sem = df_asist_semana[df_asist_semana['trabajador'] == trabajador] if not df_asist_semana.empty else pd.DataFrame()
        
        cant_completos = len(df_t_sem[df_t_sem['estado'] == 'Día Completo']) if not df_t_sem.empty else 0
        cant_medios = len(df_t_sem[df_t_sem['estado'] == 'Medio Día']) if not df_t_sem.empty else 0
        cant_faltas = len(df_t_sem[df_t_sem['estado'].str.contains('Falta|Emergencia', na=False)]) if not df_t_sem.empty else 0
        cant_almuerzos = len(df_t_sem[df_t_sem['almuerzo'].str.startswith('Sale', na=False)]) if not df_t_sem.empty else 0

        with st.expander(f"Ficha Técnica: {especialidad_trab} — {trabajador}", expanded=True):
            col_w1, col_w2, col_w3 = st.columns(3)
            with col_w1:
                jornal_dia = st.number_input(f"Jornal Diario (S/)", value=jornal_bd_val, step=10.0, key=f"jornal_{trabajador}")
                costo_almuerzo = st.number_input(f"Asignación Almuerzo (S/)", value=alm_bd_val, step=1.0, key=f"alm_costo_{trabajador}")
            with col_w2:
                comentario_nota = st.text_input(f"Anotaciones Contables", value="", key=f"comentario_{trabajador}")
            with col_w3:
                monto_extra = st.number_input(f"Monto de Ajuste (S/)", value=0.0, step=10.0, key=f"monto_{trabajador}")

            pago_completos = cant_completos * jornal_dia
            pago_medios = cant_medios * (jornal_dia / 2.0)
            total_almuerzos = cant_almuerzos * costo_almuerzo
            total_trabajador = pago_completos + pago_medios + total_almuerzos
            gasto_semana_mo += total_trabajador

            st.markdown(f"""
                <div style="background-color: #f8fafc; padding: 15px; border-radius: 4px; border: 1px solid #e2e8f0; margin-top: 10px;">
                    <table style="width:100%; color: #334155; text-align: left; font-size: 0.95rem; border-collapse: collapse;">
                        <tr style='border-bottom: 1px solid #cbd5e1;'><th style='padding:5px;'>Concepto</th><th>Cant.</th><th>Tasa (S/)</th><th>Parcial (S/)</th></tr>
                        <tr><td style='padding:5px;'>Días Completos</td><td><b>{cant_completos}</b></td><td>{jornal_dia:.2f}</td><td>{pago_completos:.2f}</td></tr>
                        <tr><td style='padding:5px;'>Medios Días</td><td><b>{cant_medios}</b></td><td>{jornal_dia/2:.2f}</td><td>{pago_medios:.2f}</td></tr>
                        <tr><td style='padding:5px;'>Almuerzos (Adicional)</td><td><b>{cant_almuerzos}</b></td><td>{costo_almuerzo:.2f}</td><td>{total_almuerzos:.2f}</td></tr>
                        <tr style='background-color:#f1f5f9;'><td style='padding:5px;'><b>TOTAL LIQUIDACIÓN:</b></td><td colspan="3" style='text-align:right;'><h4 style="color: #0056b3; margin: 0;">S/ {total_trabajador:.2f}</h4></td></tr>
                    </table>
                </div>
            """, unsafe_allow_html=True)

    st.markdown(f"<div style='background-color: #0056b3; padding: 15px; border-radius: 4px; text-align: center; color: white; margin-top: 20px;'><h3 style='margin:0; color:white !important;'>SUBTOTAL PLANILLA DE LA SEMANA: S/ {gasto_semana_mo:,.2f}</h3></div>", unsafe_allow_html=True)

with tab_materiales:
    if not df_mat_db.empty:
        mask = (df_mat_db['fecha_dt'] >= fecha_inicio) & (df_mat_db['fecha_dt'] <= fecha_fin) & (df_mat_db['partida'] == st.session_state['partida_actual'])
        df_mat_filtrado = df_mat_db.loc[mask].copy()
    else: df_mat_filtrado = pd.DataFrame(columns=['partida', 'fecha', 'insumo', 'und', 'cantidad', 'precio', 'descuento', 'fecha_dt'])

    if not df_mat_filtrado.empty:
        dias_es_map = {0: 'Lunes', 1: 'Martes', 2: 'Miércoles', 3: 'Jueves', 4: 'Viernes', 5: 'Sábado', 6: 'Domingo'}
        df_mat_filtrado['Fecha_Formateada'] = df_mat_filtrado['fecha'].apply(lambda f: f"{date.fromisoformat(str(f)).strftime('%d/%m/%Y')} ({dias_es_map[date.fromisoformat(str(f)).weekday()]})" if pd.notna(f) else "")
        df_mat_filtrado['Parcial'] = df_mat_filtrado['cantidad'] * df_mat_filtrado['precio'] * (1 - (df_mat_filtrado['descuento'] / 100.0))
        
        df_mats_show = df_mat_filtrado[['Fecha_Formateada', 'insumo', 'und', 'cantidad', 'precio', 'descuento', 'Parcial']].rename(columns={
            'Fecha_Formateada': 'Fecha', 'insumo': 'Descripción', 'und': 'Und.', 'cantidad': 'Cant.', 'precio': 'P.U.', 'descuento': 'Desc.%', 'Parcial': 'Monto (S/)'
        })
        
        df_mats_show['Cant.'] = df_mats_show['Cant.'].apply(lambda x: f"{x:.2f}")
        df_mats_show['P.U.'] = df_mats_show['P.U.'].apply(lambda x: f"{x:,.2f}")
        df_mats_show['Desc.%'] = df_mats_show['Desc.%'].apply(lambda x: f"{x:.2f}")
        df_mats_show['Monto (S/)'] = df_mats_show['Monto (S/)'].apply(lambda x: f"{x:,.2f}")
    else: df_mats_show = pd.DataFrame(columns=['Fecha', 'Descripción', 'Und.', 'Cant.', 'P.U.', 'Desc.%', 'Monto (S/)'])
        
    st.dataframe(df_mats_show, use_container_width=True, hide_index=True)
    gasto_semana_mat = df_mat_filtrado['Parcial'].sum() if not df_mat_filtrado.empty else 0.0
    st.markdown(f"<div style='background-color: #0056b3; padding: 15px; border-radius: 4px; text-align: center; color: white; margin-top: 10px;'><h3 style='margin:0; color:white !important;'>SUBTOTAL MATERIALES DE LA SEMANA: S/ {gasto_semana_mat:,.2f}</h3></div>", unsafe_allow_html=True)

# ==========================================
# 11. TABLA RESUMEN SEMANAL
# ==========================================
st.markdown("<div class='section-header'>📈 MATRIZ DE RESUMEN GLOBAL (ESTADO FINANCIERO)</div>", unsafe_allow_html=True)

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
color_saldo = "#10b981" if saldo_final >= 0 else "#ef4444"
estado_saldo = "Saldo a Favor (Superávit)" if saldo_final >= 0 else "Sobregiro (Déficit)"

col_res1, col_res2, col_res3 = st.columns(3)
with col_res1:
    st.markdown(f"<div style='background-color: #ffffff; padding: 20px; border-radius: 4px; border: 1px solid #cbd5e1; border-top: 4px solid #0f172a; text-align: center;'><h4 style='margin:0; color:#475569;'>Pto. Aprobado</h4><h2 style='margin:0; color:#0f172a;'>S/ {presupuesto_actual_total:,.2f}</h2></div>", unsafe_allow_html=True)
with col_res2:
    st.markdown(f"<div style='background-color: #ffffff; padding: 20px; border-radius: 4px; border: 1px solid #cbd5e1; border-top: 4px solid #0056b3; text-align: center;'><h4 style='margin:0; color:#475569;'>Costo Real Acumulado</h4><h2 style='margin:0; color:#0056b3;'>S/ {gasto_total_acumulado:,.2f}</h2></div>", unsafe_allow_html=True)
with col_res3:
    st.markdown(f"<div style='background-color: #ffffff; padding: 20px; border-radius: 4px; border: 1px solid #cbd5e1; border-top: 4px solid {color_saldo}; text-align: center;'><h4 style='margin:0; color:#475569;'>{estado_saldo}</h4><h2 style='margin:0; color:{color_saldo};'>S/ {abs(saldo_final):,.2f}</h2></div>", unsafe_allow_html=True)

# ==========================================
# 12. GENERADOR DE REPORTE PDF
# ==========================================
st.markdown("<div class='section-header'>🖨️ DOCUMENTACIÓN OFICIAL Y CIERRE</div>", unsafe_allow_html=True)
if st.button("GENERAR INFORME TÉCNICO (VERSIÓN IMPRIMIBLE / PDF)", use_container_width=True):
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
    colores_print = ['#0056b3', '#ea580c', '#10b981']

    fig_dona_print = go.Figure(data=[go.Pie(labels=labels_print, values=values_print, marker_colors=colores_print)])
    fig_dona_print.update_layout(title=dict(text="Distribución Global de Costos", font=dict(color="#0f172a", size=13)), paper_bgcolor="white", plot_bgcolor="white", margin=dict(t=30, b=10, l=10, r=10), legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5, font=dict(color="#0f172a", size=9)), width=480, height=280)
    fig_dona_print.update_traces(texttemplate='%{percent}<br>S/ %{value:,.2f}', textposition='inside', textfont=dict(size=9.5, color='white'), insidetextorientation='horizontal')

    semanas_graf_p = df_resumen_final['Semana'].tolist() if not df_resumen_final.empty else ['Sem 1']
    pres_total_linea_p = [presupuesto_actual_total] * len(semanas_graf_p)
    gasto_acumulado_graf_p = df_resumen_final['Gasto Acumulado (S/)'].tolist() if not df_resumen_final.empty else [0]

    fig_linea_print = go.Figure()
    fig_linea_print.add_trace(go.Scatter(x=semanas_graf_p, y=pres_total_linea_p, mode='lines', name='Pto. Total', line=dict(color='#10b981', dash='dash', width=2)))
    fig_linea_print.add_trace(go.Scatter(x=semanas_graf_p, y=gasto_acumulado_graf_p, mode='lines+markers', name='Ejecutado', line=dict(color='#0056b3', width=3)))
    fig_linea_print.update_layout(title=dict(text="Curva S de Gasto Acumulado", font=dict(color="#0f172a", size=13)), paper_bgcolor="white", plot_bgcolor="white", margin=dict(t=30, b=40, l=70, r=20), legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5, font=dict(color="#0f172a", size=9)), font=dict(color="#0f172a"), xaxis=dict(tickangle=0, gridcolor="#e2e8f0"), yaxis=dict(tickprefix="S/ ", tickformat=",.0f", gridcolor="#e2e8f0", dtick=2000), width=480, height=280)

    html_dona_str = fig_dona_print.to_html(include_plotlyjs='inline', full_html=False, config={'displayModeBar': False})
    html_linea_str = fig_linea_print.to_html(include_plotlyjs='inline', full_html=False, config={'displayModeBar': False})

    html_reporte = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Informe Técnico - Nexus Obra</title>
        <style>
            @page {{ size: A4; margin: 10mm; }}
            body {{ font-family: 'Segoe UI', Arial, sans-serif; color: #0f172a; margin: 0; padding: 0; font-size: 8.5pt; line-height: 1.15; background: #fff; }}
            .header {{ border-bottom: 2px solid #0056b3; padding-bottom: 4px; margin-bottom: 8px; }}
            .header h1 {{ font-size: 12pt; margin: 0 0 2px 0; color: #0056b3; text-transform: uppercase; }}
            .header h2 {{ font-size: 8.5pt; margin: 0; color: #475569; font-weight: normal; }}
            .info-box {{ background: #f8fafc; border: 1px solid #cbd5e1; padding: 5px 7px; margin-bottom: 8px; font-size: 8pt; }}
            .section-title {{ font-size: 9.5pt; font-weight: bold; color: #0056b3; margin-top: 8px; margin-bottom: 2px; border-bottom: 1px solid #0056b3; padding-bottom: 1px; page-break-after: avoid; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 2px; margin-bottom: 4px; font-size: 7.5pt; page-break-inside: avoid; }}
            th, td {{ border: 1px solid #cbd5e1; padding: 3px 4px; text-align: left; }}
            th {{ background: #f1f5f9; color: #0f172a; font-weight: bold; }}
            .text-right {{ text-align: right; }}
            .text-center {{ text-align: center; }}
            .grafico-center {{ text-align: center; margin: 6px auto; page-break-inside: avoid; display: flex; justify-content: center; }}
            .worker-section {{ page-break-inside: avoid; margin-bottom: 8px; border: 1px solid #e2e8f0; }}
            @media print {{ button {{ display: none; }} }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>SISTEMA DE GESTIÓN Y CONTROL - NEXUS OBRA</h1>
            <h2>Informe Técnico de Ejecución Presupuestal y Avance</h2>
        </div>
        
        <div class="info-box">
            <b>Proyecto:</b> Obras de Construcción Civil<br>
            <b>Partida Evaluada:</b> {st.session_state['partida_actual']}<br>
            <b>Fecha de Generación:</b> {fecha_impresion_str}
        </div>

        <div class="section-title">1. Estado Financiero Consolidado</div>
        <p style="margin: 4px 0 6px 0;">
            Presupuesto Asignado: <b>S/ {presupuesto_actual_total:,.2f}</b> | 
            Gasto Ejecutado: <b>S/ {gasto_total_acumulado:,.2f}</b> | 
            Estado: <b>{estado_saldo}</b> por <b>S/ {abs(presupuesto_actual_total - gasto_total_acumulado):,.2f}</b>.
        </p>

        <div class="section-title">2. Gráficos de Rendimiento y Curva S</div>
        <div class="grafico-center">{html_dona_str}</div>
        <div class="grafico-center">{html_linea_str}</div>

        <div class="section-title">3. Matriz Analítica por Semanas de Ejecución</div>
        <table>
            <thead>
                <tr>
                    <th>Mes</th>
                    <th>Semana</th>
                    <th class="text-right">Costo Personal (S/)</th>
                    <th class="text-right">Costo Materiales (S/)</th>
                    <th class="text-right">Gasto Semanal (S/)</th>
                    <th class="text-right">Costo Acumulado (S/)</th>
                </tr>
            </thead>
            <tbody>
    """
    
    for _, row in df_resumen_final.iterrows():
        html_reporte += f"""
                <tr>
                    <td>{row['Mes']}</td>
                    <td>{row['Semana']}</td>
                    <td class="text-right">S/ {row['Gasto Mano Obra (S/)']:,.2f}</td>
                    <td class="text-right">S/ {row['Gasto Materiales (S/)']:,.2f}</td>
                    <td class="text-right">S/ {row['Gasto Total Semanal (S/)']:,.2f}</td>
                    <td class="text-right">S/ {row['Gasto Acumulado (S/)']:,.2f}</td>
                </tr>
        """
        
    html_reporte += f"""
                <tr style='background-color:#f1f5f9; font-weight:bold;'>
                    <td colspan="2" class="text-right">TOTAL GENERAL:</td>
                    <td class="text-right">S/ {gasto_mo_real_total:,.2f}</td>
                    <td class="text-right">S/ {gasto_mat_real_total:,.2f}</td>
                    <td class="text-right">S/ {gasto_mo_real_total + gasto_mat_real_total:,.2f}</td>
                    <td></td>
                </tr>
            </tbody>
        </table>

        <div class="section-title">4. Desglose de Tareos (Planilla de Personal)</div>
    """
    
    for _, pers in df_pers_actual.iterrows():
        t_nombre = pers['nombre']
        t_esp = pers['especialidad']
        
        html_reporte += f"""
        <div class="worker-section">
            <div style="background: #f1f5f9; padding: 4px 6px; font-weight: bold; border-bottom: 1px solid #cbd5e1; font-size: 8pt; color: #0f172a;">
                {t_esp.upper()} - {t_nombre.upper()}
            </div>
            <div style="padding: 4px;">
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
            
            if not df_t_s.empty:
                html_reporte += f"""
                <p style="margin: 2px 0 2px 0; font-size: 7.5pt; font-weight:bold; color: #334155;">{s_nombre} ({s_ini.strftime('%d/%m/%Y')} - {s_fin.strftime('%d/%m/%Y')}):</p>
                <table style='margin-bottom: 6px;'>
                    <thead>
                        <tr>
                            <th width="15%">Fecha</th>
                            <th width="25%">Asistencia</th>
                            <th width="20%">Almuerzo</th>
                            <th width="40%">Observaciones / Avance</th>
                        </tr>
                    </thead>
                    <tbody>
                """
                for _, r_as in df_t_s.iterrows():
                    dt_f = date.fromisoformat(str(r_as['fecha']))
                    html_reporte += f"<tr><td>{dt_f.strftime('%d/%m/%Y')}</td><td>{r_as['estado']}</td><td>{r_as['almuerzo']}</td><td>{r_as['actividad']}</td></tr>"
                html_reporte += f"<tr><td colspan='4' class='text-right' style='background-color:#f8fafc;'><b>Pago Periodo: S/ {tot_s_trab:,.2f}</b></td></tr></tbody></table>"
        
        html_reporte += "</div></div>"

    html_reporte += f"""
        <div class="section-title">5. Kardex Histórico de Suministros y Materiales</div>
        <table>
            <thead>
                <tr>
                    <th>Fecha Compra</th>
                    <th>Descripción de Insumo</th>
                    <th class="text-center">U.M.</th>
                    <th class="text-right">Cant.</th>
                    <th class="text-right">Precio U. (S/)</th>
                    <th class="text-right">Desc. (%)</th>
                    <th class="text-right">Total Neto (S/)</th>
                </tr>
            </thead>
            <tbody>
    """
    
    gasto_mat_rep = 0.0
    if not df_mat_db.empty:
        df_mat_rep = df_mat_db.sort_values('fecha')
        for _, r_m in df_mat_rep.iterrows():
            dt_m = date.fromisoformat(str(r_m['fecha']))
            cant_m = float(r_m['cantidad'])
            prec_m = float(r_m['precio'])
            desc_m = float(r_m['descuento']) if 'descuento' in r_m and pd.notna(r_m['descuento']) else 0.0
            parc_m = cant_m * prec_m * (1 - (desc_m / 100.0))
            gasto_mat_rep += parc_m
            
            html_reporte += f"<tr><td>{dt_m.strftime('%d/%m/%Y')}</td><td>{r_m['insumo']}</td><td class='text-center'>{r_m['und']}</td><td class='text-right'>{cant_m:,.2f}</td><td class='text-right'>S/ {prec_m:,.2f}</td><td class='text-right'>{desc_m:.2f}</td><td class='text-right'>S/ {parc_m:,.2f}</td></tr>"
            
    if gasto_mat_rep == 0.0:
        html_reporte += "<tr><td colspan='7' class='text-center'><i>Sin movimientos registrados en este periodo.</i></td></tr>"
        
    html_reporte += f"""
                <tr style='background-color:#f1f5f9; font-weight:bold;'>
                    <td colspan="6" class="text-right">TOTAL MATERIALES E INSUMOS:</td>
                    <td class="text-right">S/ {gasto_mat_rep:,.2f}</td>
                </tr>
            </tbody>
        </table>
        
        <br>
        <div style="text-align: center; font-size: 8pt; color: #64748b; border-top: 1px solid #cbd5e1; padding-top: 6px;">
            Documento emitido por plataforma <b>Nexus Obra</b>. Control Técnico y Administrativo.
        </div>
        
        <script> setTimeout(function() {{ window.print(); }}, 1500); </script>
    </body>
    </html>
    """
    st.components.v1.html(html_reporte, height=800, scrolling=True)
