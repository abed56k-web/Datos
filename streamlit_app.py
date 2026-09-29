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
conn = sqlite3.connect('obra_nexus.db', timeout=10.0, check_same_thread=False)
c = conn.cursor()

c.execute('CREATE TABLE IF NOT EXISTS usuarios (email TEXT UNIQUE, password TEXT)')
c.execute('CREATE TABLE IF NOT EXISTS personal (partida TEXT, nombre TEXT, especialidad TEXT, jornal REAL DEFAULT 120.0, almuerzo_costo REAL DEFAULT 7.0, UNIQUE(partida, nombre))')
c.execute('CREATE TABLE IF NOT EXISTS materiales (partida TEXT, fecha TEXT, insumo TEXT, und TEXT, cantidad REAL, precio REAL)')
c.execute('CREATE TABLE IF NOT EXISTS asistencia (partida TEXT, trabajador TEXT, fecha TEXT, estado TEXT, almuerzo TEXT, actividad TEXT, UNIQUE(partida, trabajador, fecha))')
c.execute('CREATE TABLE IF NOT EXISTS presupuestos (partida TEXT PRIMARY KEY, modo TEXT, total REAL, materiales REAL, mano_obra REAL)')
conn.commit()

try:
    c.execute('ALTER TABLE personal ADD COLUMN jornal REAL DEFAULT 120.0')
    c.execute('ALTER TABLE personal ADD COLUMN almuerzo_costo REAL DEFAULT 7.0')
    conn.commit()
except sqlite3.OperationalError:
    pass

try:
    c.execute('ALTER TABLE materiales ADD COLUMN und TEXT')
    conn.commit()
except sqlite3.OperationalError:
    pass

try:
    c.execute('ALTER TABLE asistencia ADD COLUMN actividad TEXT')
    conn.commit()
except sqlite3.OperationalError:
    pass

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

# Recuperar o inicializar presupuesto en la BD
try:
    c.execute("SELECT modo, total, materiales, mano_obra FROM presupuestos WHERE partida=?", (st.session_state['partida_actual'],))
    row_presupuesto = c.fetchone()
except sqlite3.OperationalError:
    row_presupuesto = None

if row_presupuesto:
    modo_guardado, presupuesto_total_db, presupuesto_mat_db, presupuesto_mo_db = row_presupuesto
else:
    modo_guardado = "Suma Automática (Materiales + Mano de Obra)"
    presupuesto_mat_db, presupuesto_mo_db = 6000.0, 4000.0
    presupuesto_total_db = 10000.0
    c.execute("INSERT OR REPLACE INTO presupuestos VALUES (?, ?, ?, ?, ?)", (st.session_state['partida_actual'], modo_guardado, presupuesto_total_db, presupuesto_mat_db, presupuesto_mo_db))
    conn.commit()

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
    modo_ingreso = st.radio("Método de cálculo:", ["Suma Automática (Materiales + Mano de Obra)", "Ingreso Directo del Total"], horizontal=True, index=0 if modo_guardado=="Suma Automática (Materiales + Mano de Obra)" else 1)
    
    if modo_ingreso == "Suma Automática (Materiales + Mano de Obra)":
        col_b1, col_b2 = st.columns(2)
        with col_b1:
            try: val_mat = float(presupuesto_mat_db)
            except (ValueError, TypeError): val_mat = 6000.0
            nuevo_mat = st.number_input("Presupuesto Materiales (S/)", value=val_mat, step=500.0)
        with col_b2:
            try: val_mo = float(presupuesto_mo_db)
            except (ValueError, TypeError): val_mo = 4000.0
            nuevo_mo = st.number_input("Presupuesto Mano de Obra (S/)", value=val_mo, step=500.0)
        nuevo_total = round(nuevo_mat + nuevo_mo, 2)
        st.markdown(f"### 💡 Presupuesto Total Calculado: <span style='color:#38bdf8;'>S/ {nuevo_total:,.2f}</span>", unsafe_allow_html=True)
    else:
        try: val_tot = float(presupuesto_total_db)
        except (ValueError, TypeError): val_tot = 10000.0
        nuevo_total = st.number_input("Presupuesto Total Directo (S/)", value=val_tot, step=1000.0)
        nuevo_mat = presupuesto_mat_db
        nuevo_mo = presupuesto_mo_db

    if st.button("💾 Guardar Configuración de Presupuesto"):
        c.execute("INSERT OR REPLACE INTO presupuestos VALUES (?, ?, ?, ?, ?)", (st.session_state['partida_actual'], modo_ingreso, round(nuevo_total, 2), round(nuevo_mat, 2), round(nuevo_mo, 2)))
        conn.commit()
        st.success("¡Presupuesto actualizado correctamente!")
        st.rerun()

presupuesto_actual_total = round(nuevo_total, 2)

st.write("---")

df_personal_db = pd.read_sql(f"SELECT nombre, especialidad, jornal, almuerzo_costo FROM personal WHERE partida='{st.session_state['partida_actual']}'", conn)
lista_trabajadores_db = df_personal_db['nombre'].tolist() if not df_personal_db.empty else ["Grover", "Juan Pérez"]

# --- COLUMNA IZQUIERDA UN POCO MÁS ANCHA PARA QUE LAS TABLAS QUEPAN PERFECTO ---
col_form, col_graf_circulo, col_graf_linea = st.columns([1.5, 1, 1])

with col_form:
    st.subheader("📝 Centro de Registro")
    tab_mat, tab_pers, tab_mo = st.tabs(["📦 Ingresar Materiales", "👤 Registrar Personal", "👷 Registrar Asistencia"])
    
    with tab_mat:
        with st.form("form_materiales"):
            f_mat = st.date_input("Fecha", date.today(), key="f1")
            mat_nom = st.text_input("Material / Insumo (Ej. Cemento Portland)")
            
            tipo_und = st.selectbox("Unidad de Medida (Norma Peruana)", ["bol (Bolsas)", "caja (Cajas)", "m3 (Metro cúbico)", "m2 (Metro cuadrado)", "kg (Kilogramo)", "und (Unidad)", "gln (Galón)", "glb (Global)", "pza (Pieza)", "ml (Metro lineal)", "Otra unidad..."])
            und_final = tipo_und.split(" ")[0] if tipo_und != "Otra unidad...": else st.text_input("Especifique su unidad:")
            
            col_m1, col_m2 = st.columns(2)
            with col_m1: cant = st.number_input("Cantidad", min_value=0.01, value=1.0)
            with col_m2: pre = st.number_input("P. Unitario (S/)", min_value=0.0)
            st.info(f"Total: S/ {cant * pre:.2f}")
            
            col_mb1, col_mb2 = st.columns(2)
            with col_mb1:
                btn_guardar_mat = st.form_submit_button("Guardar Material", use_container_width=True)
            with col_mb2:
                btn_limpiar_mat = st.form_submit_button("🧹 Limpiar Día", use_container_width=True)

            if btn_guardar_mat:
                if mat_nom and und_final:
                    c.execute("INSERT INTO materiales (partida, fecha, insumo, und, cantidad, precio) VALUES (?, ?, ?, ?, ?, ?)", 
                              (st.session_state['partida_actual'], str(f_mat), mat_nom, und_final, cant, pre))
                    conn.commit()
                    st.success("Material guardado correctamente.")
                    st.rerun()
                else:
                    st.warning("Completa el nombre y la unidad del material.")

            if btn_limpiar_mat:
                c.execute("DELETE FROM materiales WHERE partida=? AND fecha=?", (st.session_state['partida_actual'], str(f_mat)))
                conn.commit()
                st.success(f"¡Materiales del {f_mat} eliminados correctamente!")
                st.rerun()
                
        # --- TABLA EDITABLE DE MATERIALES EXPANSIVA ---
        st.write("---")
        st.write("📋 **Editar Base de Materiales**")
        df_mat_actual = pd.read_sql(f"SELECT fecha, insumo, und, cantidad, precio FROM materiales WHERE partida='{st.session_state['partida_actual']}' ORDER BY fecha DESC", conn)
        
        if not df_mat_actual.empty:
            df_mat_actual['fecha'] = pd.to_datetime(df_mat_actual['fecha']).dt.date
        else:
            df_mat_actual = pd.DataFrame(columns=["fecha", "insumo", "und", "cantidad", "precio"])
            
        # Al NO definir un "width" para las columnas largas, Streamlit las expande automáticamente (canto a canto)
        df_mat_editado = st.data_editor(
            df_mat_actual, 
            num_rows="dynamic", 
            use_container_width=True,
            hide_index=True,
            key="editor_tabla_materiales",
            column_config={
                "fecha": st.column_config.DateColumn("Fecha", format="DD/MM/YYYY"),
                "insumo": st.column_config.TextColumn("Insumo / Material"),
                "und": st.column_config.TextColumn("UND"),
                "cantidad": st.column_config.NumberColumn("Cant.", format="%.2f"),
                "precio": st.column_config.NumberColumn("Precio (S/)", format="%.2f")
            }
        )
        
        if st.button("💾 Guardar Cambios en Materiales", use_container_width=True):
            c.execute("DELETE FROM materiales WHERE partida=?", (st.session_state['partida_actual'],))
            for _, row in df_mat_editado.iterrows():
                if pd.notna(row["insumo"]) and str(row["insumo"]).strip() != "":
                    try:
                        f_val = str(row["fecha"]).strip() if pd.notna(row["fecha"]) else str(date.today())
                        c_val = float(row["cantidad"]) if pd.notna(row["cantidad"]) else 1.0
                        p_val = float(row["precio"]) if pd.notna(row["precio"]) else 0.0
                        u_val = str(row["und"]).strip() if pd.notna(row["und"]) else "und"
                        c.execute("INSERT INTO materiales (partida, fecha, insumo, und, cantidad, precio) VALUES (?, ?, ?, ?, ?, ?)", 
                                  (st.session_state['partida_actual'], f_val, str(row["insumo"]).strip(), u_val, c_val, p_val))
                    except:
                        pass
            conn.commit()
            st.success("¡Lista de materiales actualizada con éxito!")
            st.rerun()
                    
    with tab_pers:
        st.write("👤 **Gestión de Personal**")
        with st.form("form_nuevo_personal"):
            col_np1, col_np2 = st.columns(2)
            with col_np1: nuevo_nombre = st.text_input("Nombre y Apellido")
            with col_np2: nueva_esp = st.selectbox("Espec.", ["Operario", "Enchapador", "Oficial", "Ayudante / Peón", "Pintor", "Electricista", "Plomero"])
            
            col_np3, col_np4 = st.columns(2)
            default_jornal_init = 120.0 if nueva_esp in ["Operario", "Enchapador", "Oficial"] else (100.0 if "Peón" in nueva_esp or "Ayudante" in nueva_esp else 120.0)
            with col_np3: def_jornal = st.number_input("Jornal Base (S/)", value=default_jornal_init, step=10.0)
            with col_np4: def_alm = st.number_input("Costo Almuerzo (S/)", value=7.0, step=1.0)

            if st.form_submit_button("➕ Agregar Trabajador", use_container_width=True):
                if nuevo_nombre:
                    try:
                        c.execute("INSERT INTO personal (partida, nombre, especialidad, jornal, almuerzo_costo) VALUES (?, ?, ?, ?, ?)", 
                                  (st.session_state['partida_actual'], nuevo_nombre.strip(), nueva_esp, def_jornal, def_alm))
                        conn.commit()
                        st.success(f"¡{nuevo_nombre} agregado!")
                        st.rerun()
                    except:
                        st.warning("El trabajador ya existe.")
                else:
                    st.warning("Escribe un nombre.")

        st.write("---")
        df_pers_actual = pd.read_sql(f"SELECT nombre, especialidad, jornal, almuerzo_costo FROM personal WHERE partida='{st.session_state['partida_actual']}'", conn)
        if df_pers_actual.empty:
            df_pers_actual = pd.DataFrame(columns=["nombre", "especialidad", "jornal", "almuerzo_costo"])
            
        df_pers_editado = st.data_editor(df_pers_actual, num_rows="dynamic", use_container_width=True, hide_index=True, key="editor_tabla_personal")
        
        if st.button("💾 Guardar Cambios en Personal", use_container_width=True):
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
                    except:
                        pass
            conn.commit()
            st.success("¡Lista de personal actualizada con éxito!")
            st.rerun()

    with tab_mo:
        with st.form("form_mano_obra"):
            f_mo = st.date_input("Fecha", date.today(), key="f2")
            
            if lista_trabajadores_db:
                trabajador = st.selectbox("Seleccione Trabajador", lista_trabajadores_db)
            else:
                trabajador = st.text_input("Nombre del Trabajador (Registra en la pestaña Personal primero)")

            estado_asis = st.selectbox("Estado de Asistencia", ["Día Completo", "Medio Día", "Falta / Emergencia"])
            almuerzo_opc = st.radio("Almuerzo", ["Sí (Almuerza en obra / con comida de obra - S/ 0 extra)", "No (Sale a comer afuera - S/ 7 extra)"], horizontal=True)
            actividad = st.text_area("Actividad / Observaciones", placeholder="Ej. Tarrajeo de muro norte.")
            
            col_fb1, col_fb2 = st.columns(2)
            with col_fb1:
                btn_guardar = st.form_submit_button("Guardar Asistencia", use_container_width=True)
            with col_fb2:
                btn_limpiar_dia = st.form_submit_button("🧹 Limpiar Día", use_container_width=True)

            if btn_guardar:
                if trabajador:
                    c.execute("INSERT OR REPLACE INTO asistencia (partida, trabajador, fecha, estado, almuerzo, actividad) VALUES (?, ?, ?, ?, ?, ?)", 
                              (st.session_state['partida_actual'], trabajador, str(f_mo), estado_asis, almuerzo_opc, actividad))
                    conn.commit()
                    st.success("¡Asistencia guardada!")
                    st.rerun()
                else:
                    st.warning("Selecciona un trabajador.")

            if btn_limpiar_dia:
                if trabajador:
                    c.execute("DELETE FROM asistencia WHERE partida=? AND trabajador=? AND fecha=?", (st.session_state['partida_actual'], trabajador, str(f_mo)))
                    conn.commit()
                    st.success(f"¡Asistencia del {f_mo} borrada!")
                    st.rerun()
                    
        # --- TABLA EDITABLE DE ASISTENCIA EXPANSIVA ---
        st.write("---")
        st.write("📋 **Editar Registro de Asistencia**")
        df_asist_edit_db = pd.read_sql(f"SELECT fecha, trabajador, estado, almuerzo, actividad FROM asistencia WHERE partida='{st.session_state['partida_actual']}' ORDER BY fecha DESC", conn)
        
        if not df_asist_edit_db.empty:
            df_asist_edit_db['fecha'] = pd.to_datetime(df_asist_edit_db['fecha']).dt.date
        else:
            df_asist_edit_db = pd.DataFrame(columns=["fecha", "trabajador", "estado", "almuerzo", "actividad"])

        lista_opciones_trabajadores = lista_trabajadores_db if lista_trabajadores_db else ["Sin registrar"]
        
        df_asist_editado = st.data_editor(
            df_asist_edit_db,
            num_rows="dynamic",
            use_container_width=True,
            hide_index=True,
            key="editor_tabla_asistencia",
            column_config={
                "fecha": st.column_config.DateColumn("Fecha", format="DD/MM/YYYY"),
                "trabajador": st.column_config.SelectboxColumn("Trabajador", options=lista_opciones_trabajadores),
                "estado": st.column_config.SelectboxColumn("Estado", options=["Día Completo", "Medio Día", "Falta / Emergencia"]),
                "almuerzo": st.column_config.SelectboxColumn("Almuerzo", options=["Sí (Almuerza en obra / con comida de obra - S/ 0 extra)", "No (Sale a comer afuera - S/ 7 extra)"]),
                "actividad": st.column_config.TextColumn("Nota")
            }
        )

        if st.button("💾 Guardar Cambios en Asistencia", use_container_width=True):
            c.execute("DELETE FROM asistencia WHERE partida=?", (st.session_state['partida_actual'],))
            for _, row in df_asist_editado.iterrows():
                if pd.notna(row["trabajador"]) and str(row["trabajador"]).strip() != "":
                    try:
                        f_val = str(row["fecha"]).strip() if pd.notna(row["fecha"]) else str(date.today())
                        est_val = str(row["estado"]) if pd.notna(row["estado"]) else "Día Completo"
                        alm_val = str(row["almuerzo"]) if pd.notna(row["almuerzo"]) else "Sí (Almuerza en obra / con comida de obra - S/ 0 extra)"
                        act_val = str(row["actividad"]) if pd.notna(row["actividad"]) else ""
                        c.execute("INSERT INTO asistencia (partida, trabajador, fecha, estado, almuerzo, actividad) VALUES (?, ?, ?, ?, ?, ?)", 
                                  (st.session_state['partida_actual'], str(row["trabajador"]), f_val, est_val, alm_val, act_val))
                    except:
                        pass
            conn.commit()
            st.success("¡Registro de asistencia actualizado con éxito!")
            st.rerun()

# Consultar datos reales de la BD
df_mat_db = pd.read_sql(f"SELECT * FROM materiales WHERE partida='{st.session_state['partida_actual']}'", conn)
if not df_mat_db.empty:
    df_mat_db['fecha_dt'] = pd.to_datetime(df_mat_db['fecha']).dt.date
    df_mat_db['cantidad'] = pd.to_numeric(df_mat_db['cantidad'], errors='coerce').fillna(0.0)
    df_mat_db['precio'] = pd.to_numeric(df_mat_db['precio'], errors='coerce').fillna(0.0)
else:
    df_mat_db['fecha_dt'] = pd.Series(dtype='object')
    df_mat_db['cantidad'] = pd.Series(dtype='float64')
    df_mat_db['precio'] = pd.Series(dtype='float64')

df_asist_db = pd.read_sql(f"SELECT * FROM asistencia WHERE partida='{st.session_state['partida_actual']}'", conn)
if not df_asist_db.empty:
    df_asist_db['fecha_dt'] = pd.to_datetime(df_asist_db['fecha']).dt.date
else:
    df_asist_db['fecha_dt'] = pd.Series(dtype='object')

trabajadores_registrados = lista_trabajadores_db

# ==========================================
# CÁLCULO PREVIO DE SEMANAS (LUNES A SÁBADO) PARA GRÁFICOS Y TABLA
# ==========================================
first_day_month = date(st.session_state['cal_ano'], st.session_state['cal_mes'], 1)
if st.session_state['cal_mes'] == 12:
    last_day_month = date(st.session_state['cal_ano'] + 1, 1, 1) - timedelta(days=1)
else:
    last_day_month = date(st.session_state['cal_ano'], st.session_state['cal_mes'] + 1, 1) - timedelta(days=1)

start_current_week_res = first_day_month - timedelta(days=first_day_month.weekday())
datos_resumen_semanas = []
gasto_acum_temp = 0.0
semana_contador = 1

while start_current_week_res <= last_day_month:
    end_current_week_res = start_current_week_res + timedelta(days=5) # Lunes a Sábado
    
    mo_sem = 0.0
    if not df_asist_db.empty:
        mask_w = (df_asist_db['fecha_dt'] >= start_current_week_res) & (df_asist_db['fecha_dt'] <= end_current_week_res) & (df_asist_db['partida'] == st.session_state['partida_actual'])
        df_w_asist = df_asist_db.loc[mask_w]
        for trab in trabajadores_registrados:
            df_tw = df_w_asist[df_w_asist['trabajador'] == trab]
            c_comp = len(df_tw[df_tw['estado'] == 'Día Completo'])
            c_med = len(df_tw[df_tw['estado'] == 'Medio Día'])
            c_alm = len(df_tw[df_tw['almuerzo'].str.startswith('No', na=False)])
            
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
        df_w_mat = df_mat_db.loc[mask_m]
        mat_sem = (df_w_mat['cantidad'] * df_w_mat['precio']).sum()

    total_sem = round(mo_sem + mat_sem, 2)
    gasto_acum_temp = round(gasto_acum_temp + total_sem, 2)
    saldo_s = round(presupuesto_actual_total - gasto_acum_temp, 2)

    datos_resumen_semanas.append({
        "Semana": f"Semana {semana_contador}",
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
gasto_mo_real_total = round(df_resumen_final["Gasto Mano Obra (S/)"].sum(), 2) if not df_resumen_final.empty else 0.0
gasto_mat_real_total = round(df_resumen_final["Gasto Materiales (S/)"].sum(), 2) if not df_resumen_final.empty else 0.0
gasto_total_acumulado = round(df_resumen_final["Gasto Acumulado (S/)"].iloc[-1], 2) if not df_resumen_final.empty else 0.0

# ==========================================
# GRÁFICOS DINÁMICOS SUPERIORES (UI DASHBOARD)
# ==========================================
with col_graf_circulo:
    st.subheader("💰 Distribución")
    labels = ['Materiales', 'Mano de Obra', 'Saldo Restante']
    values = [gasto_mat_real_total, gasto_mo_real_total, max(0, presupuesto_actual_total - (gasto_mat_real_total + gasto_mo_real_total))] 
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
    semanas_graf = df_resumen_final['Semana'].tolist() if not df_resumen_final.empty else ['Sem 1']
    pres_total_linea = [presupuesto_actual_total] * len(semanas_graf)
    gasto_acumulado_graf = df_resumen_final['Gasto Acumulado (S/)'].tolist() if not df_resumen_final.empty else [0]
    
    fig_linea = go.Figure()
    fig_linea.add_trace(go.Scatter(x=semanas_graf, y=pres_total_linea, mode='lines', name='Presupuesto Total', line=dict(color='#10b981', dash='dash')))
    fig_linea.add_trace(go.Scatter(x=semanas_graf, y=gasto_acumulado_graf, mode='lines+markers', name='Gasto Acumulado', line=dict(color='#ef4444', width=3)))
    
    fig_linea.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(t=10, b=10, l=50, r=0),
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5, font=dict(color="white")),
        font=dict(color="white"),
        yaxis=dict(tickprefix="S/ ", tickformat=",.0f", gridcolor="#334155")
    )
    st.plotly_chart(fig_linea, use_container_width=True)

st.write("---")

# ==========================================
# 7. ALMANAQUE INTERACTIVO CON TOOLTIP DE COMENTARIO
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
    comentarios_trabajador = {}
    if not df_asist_db.empty and trabajador_seleccionado != "Sin registros":
        df_t = df_asist_db[(df_asist_db['trabajador'] == trabajador_seleccionado)]
        for _, row in df_t.iterrows():
            try:
                f_reg = date.fromisoformat(row['fecha'])
                if f_reg.year == st.session_state['cal_ano'] and f_reg.month == st.session_state['cal_mes']:
                    asistencia_trabajador[f_reg.day] = row['estado']
                    comentarios_trabajador[f_reg.day] = row['actividad'] if row['actividad'] else "Sin observaciones"
            except:
                pass

    html_cal = """
    <style>
    .cal-wrapper { background-color: #1e293b; border-radius: 12px; box-shadow: 0 0 10px rgba(56, 189, 248, 0.2); border: 1px solid #38bdf8; padding: clamp(10px, 3vw, 20px); width: 100%; box-sizing: border-box; overflow: hidden;}
    .cal-table { width: 100%; border-collapse: separate; border-spacing: clamp(2px, 1vw, 4px); text-align: center; font-family: sans-serif; table-layout: fixed;}
    .cal-table th { padding: clamp(5px, 1.5vw, 10px) 0; color: #94a3b8; font-weight: bold; font-size: clamp(0.8rem, 2.5vw, 1.1rem); }
    .cal-table td { padding: clamp(8px, 2vw, 15px) 0; border-radius: 4px; font-size: clamp(0.9rem, 3vw, 1.2rem); font-weight: bold; border: 1px solid #334155; position: relative; cursor: pointer; }
    .cal-vacio { background-color: #1e293b; color: transparent !important; border: none !important; cursor: default !important; }
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
# 8. MÓDULOS SEMANALES CON SELECTOR DE SEMANA (LUNES A SÁBADO)
# ==========================================
st.markdown("<h2 style='color: #a855f7 !important;'>🗓 Cierre y Reporte Semanal</h2>", unsafe_allow_html=True)

first_day_month_sel = date(st.session_state['cal_ano'], st.session_state['cal_mes'], 1)
if st.session_state['cal_mes'] == 12:
    last_day_month_sel = date(st.session_state['cal_ano'] + 1, 1, 1) - timedelta(days=1)
else:
    last_day_month_sel = date(st.session_state['cal_ano'], st.session_state['cal_mes'] + 1, 1) - timedelta(days=1)

start_current_week_sel = first_day_month_sel - timedelta(days=first_day_month_sel.weekday())
semanas_opciones = []
semana_map = {}
idx = 1

while start_current_week_sel <= last_day_month_sel:
    end_current_week_sel = start_current_week_sel + timedelta(days=5) # Lunes a Sábado
    label = f"Semana {idx}: {start_current_week_sel.strftime('%d/%m/%Y')} al {end_current_week_sel.strftime('%d/%m/%Y')}"
    semanas_opciones.append(label)
    semana_map[label] = (start_current_week_sel, end_current_week_sel)
    idx += 1
    start_current_week_sel += timedelta(days=7)

semana_seleccionada = st.selectbox("Seleccione la Semana de Trabajo (Lunes a Sábado):", semanas_opciones)
fecha_inicio, fecha_fin = semana_map[semana_seleccionada]

st.markdown(f"**Calculando gastos para la {semana_seleccionada}**")

tab_planilla, tab_materiales = st.tabs(["👷 Planilla de Mano de Obra (Semanal)", "📦 Control de Materiales (Semanal)"])

with tab_planilla:
    st.write("Cálculo automático de jornales basados estrictamente en el calendario registrado.")

    gasto_semana_mo = 0

    if not df_asist_db.empty:
        mask_asis = (df_asist_db['fecha_dt'] >= fecha_inicio) & (df_asist_db['fecha_dt'] <= fecha_fin) & (df_asist_db['partida'] == st.session_state['partida_actual'])
        df_asist_semana = df_asist_db.loc[mask_asis]
    else:
        df_asist_semana = pd.DataFrame(columns=['trabajador', 'fecha', 'estado', 'almuerzo'])

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
        cant_almuerzos = len(df_t_sem[df_t_sem['almuerzo'].str.startswith('No', na=False)]) if not df_t_sem.empty else 0

        with st.expander(f"Obrero: {especialidad_trab} — {trabajador}", expanded=True):
            st.markdown(f"### *{especialidad_trab}* — **{trabajador}**", unsafe_allow_html=True)
            
            col_w1, col_w2, col_w3 = st.columns(3)
            with col_w1:
                jornal_dia = st.number_input(f"Jornal Diario (S/)", value=jornal_bd_val, step=10.0, key=f"jornal_{trabajador}")
                costo_almuerzo = st.number_input(f"Costo Almuerzo (S/)", value=alm_bd_val, step=1.0, key=f"alm_costo_{trabajador}")
            with col_w2:
                comentario_nota = st.text_input(f"Cuadro Comentario (Ej. Adelanto / Arreglado)", value="", key=f"comentario_{trabajador}")
            with col_w3:
                monto_extra = st.number_input(f"Monto (Opcional)", value=0.0, step=10.0, key=f"monto_{trabajador}")

            pago_completos = cant_completos * jornal_dia
            pago_medios = cant_medios * (jornal_dia / 2.0)
            total_almuerzos = cant_almuerzos * costo_almuerzo
            
            total_trabajador = pago_completos + pago_medios + total_almuerzos
            gasto_semana_mo += total_trabajador

            st.markdown(f"""
                <div style="background-color: #0f172a; padding: 15px; border-radius: 8px; border: 1px solid #334155; margin-top: 10px; margin-bottom: 10px;">
                    <table style="width:100%; color: #e2e8f0; text-align: left; font-size: 1.05rem;">
                        <tr><th>Concepto</th><th>Cantidad</th><th>Jornal / Costo</th><th>Parcial (S/)</th></tr>
                        <tr><td>Días Completos</td><td><b>{cant_completos}</b></td><td>S/ {jornal_dia:.2f}</td><td>S/ {pago_completos:.2f}</td></tr>
                        <tr><td>Medios Días</td><td><b>{cant_medios}</b></td><td>S/ {jornal_dia/2:.2f}</td><td>S/ {pago_medios:.2f}</td></tr>
                        <tr><td>Inasistencias</td><td><b>{cant_faltas}</b></td><td>S/ 0.00</td><td>S/ 0.00</td></tr>
                        <tr><td>Almuerzos Afuera (S/ 7 extra)</td><td><b>{cant_almuerzos}</b></td><td>S/ {costo_almuerzo:.2f}</td><td>S/ {total_almuerzos:.2f}</td></tr>
                        <tr><td><b>Nota / Comentario:</b></td><td colspan="3"><i>{comentario_nota if comentario_nota else 'Sin comentarios'} (Monto ref: S/ {monto_extra:.2f})</i></td></tr>
                    </table>
                    <hr style="border-color: #334155;">
                    <h3 style="color: #10b981; text-align: right; margin: 0;">TOTAL A PAGAR: S/ {total_trabajador:.2f}</h3>
                </div>
            """, unsafe_allow_html=True)

    st.markdown(f"<h2 style='color: #38bdf8; text-align: center; background-color: #1e293b; padding: 15px; border-radius: 8px;'>Total Planilla General de la Semana: S/ {gasto_semana_mo:,.2f}</h2>", unsafe_allow_html=True)

with tab_materiales:
    st.write("Materiales comprados **exactamente dentro del rango de fechas** de la semana seleccionada.")
    
    if not df_mat_db.empty:
        mask = (df_mat_db['fecha_dt'] >= fecha_inicio) & (df_mat_db['fecha_dt'] <= fecha_fin) & (df_mat_db['partida'] == st.session_state['partida_actual'])
        df_mat_filtrado = df_mat_db.loc[mask].copy()
    else:
        df_mat_filtrado = pd.DataFrame(columns=['partida', 'fecha', 'insumo', 'und', 'cantidad', 'precio', 'fecha_dt'])

    if not df_mat_filtrado.empty:
        dias_es_map = {0: 'Lunes', 1: 'Martes', 2: 'Miércoles', 3: 'Jueves', 4: 'Viernes', 5: 'Sábado', 6: 'Domingo'}
        def formatear_fecha_mat(f_str):
            try:
                dt = date.fromisoformat(str(f_str))
                return f"{dt.strftime('%d/%m/%Y')} ({dias_es_map[dt.weekday()]})"
            except:
                return str(f_str)

        df_mat_filtrado['Fecha_Formateada'] = df_mat_filtrado['fecha'].apply(formatear_fecha_mat)
        df_mat_filtrado['Parcial'] = df_mat_filtrado['cantidad'] * df_mat_filtrado['precio']
        
        df_mats_show = df_mat_filtrado[['Fecha_Formateada', 'insumo', 'und', 'cantidad', 'precio', 'Parcial']].rename(columns={
            'Fecha_Formateada': 'Fecha',
            'insumo': 'Insumo / Material',
            'und': 'UND',
            'cantidad': 'Cantidad',
            'precio': 'Precio Unit. (S/)',
            'Parcial': 'Parcial (S/)'
        })
    else:
        df_mats_show = pd.DataFrame(columns=['Fecha', 'Insumo / Material', 'UND', 'Cantidad', 'Precio Unit. (S/)', 'Parcial (S/)'])
        
    # --- TABLA DE LECTURA (CANTIDADES SIN LA REDUNDANCIA S/) ---
    st.dataframe(
        df_mats_show,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Fecha": st.column_config.TextColumn("Fecha"),
            "Insumo / Material": st.column_config.TextColumn("Insumo / Material"),
            "UND": st.column_config.TextColumn("UND"),
            "Cantidad": st.column_config.NumberColumn("Cantidad", format="%.2f"),
            "Precio Unit. (S/)": st.column_config.NumberColumn("Precio Unit. (S/)", format="%.2f"),
            "Parcial (S/)": st.column_config.NumberColumn("Parcial (S/)", format="%.2f")
        }
    )

    gasto_semana_mat = 0.0
    if not df_mat_filtrado.empty:
        gasto_semana_mat = df_mat_filtrado['Parcial'].sum()
            
    st.markdown(f"<h3 style='color: #38bdf8; text-align: right;'>Total Materiales Semana: S/ {gasto_semana_mat:,.2f}</h3>", unsafe_allow_html=True)

st.write("---")

# ==========================================
# 9. TABLA RESUMEN SEMANAL (BLOQUES DE LUNES A SÁBADO)
# ==========================================
st.markdown("<h2 style='color: #10b981 !important;'>📊 Tabla Resumen Semanal de Gastos (Semanas de Lunes a Sábado)</h2>", unsafe_allow_html=True)
st.write(f"Desglose por semanas de trabajo (Lunes a Sábado) para el mes de **{meses_espanol[st.session_state['cal_mes']]} {st.session_state['cal_ano']}**:")

# --- CREAMOS UNA COPIA PARA MOSTRAR LOS TOTALES SIN ROMPER LOS GRÁFICOS ---
df_resumen_mostrar = df_resumen_final.copy()
if not df_resumen_mostrar.empty:
    df_resumen_mostrar.loc["Total"] = {
        "Semana": "TOTAL",
        "Rango (Lunes a Sábado)": "",
        "Gasto Mano Obra (S/)": gasto_mo_real_total,
        "Gasto Materiales (S/)": gasto_mat_real_total,
        "Gasto Total Semanal (S/)": round(gasto_mo_real_total + gasto_mat_real_total, 2),
        "Gasto Acumulado (S/)": "",
        "Saldo vs Presupuesto (S/)": ""
    }
    
    # Damos un formato bonito con comas y 2 decimales para leerlo bien
    for col in ["Gasto Mano Obra (S/)", "Gasto Materiales (S/)", "Gasto Total Semanal (S/)", "Gasto Acumulado (S/)", "Saldo vs Presupuesto (S/)"]:
        df_resumen_mostrar[col] = df_resumen_mostrar[col].apply(lambda x: f"{x:,.2f}" if isinstance(x, (int, float)) else x)

st.dataframe(df_resumen_mostrar, use_container_width=True, hide_index=True)
# --------------------------------------------------------------------------

saldo_final = round(presupuesto_actual_total - gasto_total_acumulado, 2)

col_res1, col_res2, col_res3 = st.columns(3)
with col_res1:
    st.markdown(f"""
        <div style='background-color: #1e293b; padding: 20px; border-radius: 12px; border-left: 5px solid #3b82f6; text-align: center;'>
            <h4 style='margin:0; color:#94a3b8;'>Presupuesto Asignado</h4>
            <h2 style='margin:0; color:#38bdf8;'>S/ {presupuesto_actual_total:,.2f}</h2>
        </div>
    """, unsafe_allow_html=True)
with col_res2:
    st.markdown(f"""
        <div style='background-color: #1e293b; padding: 20px; border-radius: 12px; border-left: 5px solid #f59e0b; text-align: center;'>
            <h4 style='margin:0; color:#94a3b8;'>Gasto Acumulado a la fecha</h4>
            <h2 style='margin:0; color:#f59e0b;'>S/ {gasto_total_acumulado:,.2f}</h2>
        </div>
    """, unsafe_allow_html=True)
with col_res3:
    color_saldo = "#10b981" if saldo_final >= 0 else "#ef4444"
    estado_saldo = "Saldo a Favor" if saldo_final >= 0 else "Sobregiro"
    st.markdown(f"""
        <div style='background-color: #1e293b; padding: 20px; border-radius: 12px; border-left: 5px solid {color_saldo}; text-align: center;'>
            <h4 style='margin:0; color:#94a3b8;'>Estado: {estado_saldo}</h4>
            <h2 style='margin:0; color:{color_saldo};'>S/ {abs(saldo_final):,.2f}</h2>
        </div>
    """, unsafe_allow_html=True)

st.write("---")

# ==========================================
# 10. GENERADOR DE REPORTE PROFESIONAL PARA IMPRESIÓN / PDF
# ==========================================
st.markdown("<h2 style='color: #38bdf8 !important;'>📥 Exportar Informe Ejecutivo de Obra</h2>", unsafe_allow_html=True)
st.write("Haz clic en el botón para abrir la vista de impresión formal con membrete de ingeniería. Podrás guardarlo directamente como **PDF** usando tu navegador.")

if st.button("🖨️ Generar e Imprimir / Guardar Reporte PDF", use_container_width=True):
    dias_es_map_rep = {0: 'Lunes', 1: 'Martes', 2: 'Miércoles', 3: 'Jueves', 4: 'Viernes', 5: 'Sábado', 6: 'Domingo'}
    fecha_impresion_str = date.today().strftime('%d/%m/%Y')
    
    first_m = date(st.session_state['cal_ano'], st.session_state['cal_mes'], 1)
    if st.session_state['cal_mes'] == 12:
        last_m = date(st.session_state['cal_ano'] + 1, 1, 1) - timedelta(days=1)
    else:
        last_m = date(st.session_state['cal_ano'], st.session_state['cal_mes'] + 1, 1) - timedelta(days=1)
    
    curr_w = first_m - timedelta(days=first_m.weekday())
    semanas_mes_lista = []
    idx_s = 1
    while curr_w <= last_m:
        end_w = curr_w + timedelta(days=5)
        semanas_mes_lista.append((f"Semana {idx_s}", curr_w, end_w))
        idx_s += 1
        curr_w += timedelta(days=7)

    # Gráfico circular optimizado
    labels_print = ['Materiales', 'Mano de Obra', 'Saldo Restante']
    values_print = [gasto_mat_real_total, gasto_mo_real_total, max(0, presupuesto_actual_total - (gasto_mat_real_total + gasto_mo_real_total))]
    colores_print = ['#06b6d4', '#f59e0b', '#10b981']

    fig_dona_print = go.Figure(data=[go.Pie(labels=labels_print, values=values_print, marker_colors=colores_print)])
    fig_dona_print.update_layout(
        title=dict(text="Distribución de Costos", font=dict(color="#0f172a", size=13)),
        paper_bgcolor="white", plot_bgcolor="white", margin=dict(t=30, b=10, l=10, r=10),
        legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5, font=dict(color="#0f172a", size=9)),
        width=480, height=280
    )
    fig_dona_print.update_traces(texttemplate='%{percent}<br>S/ %{value:,.2f}', textposition='inside', textfont=dict(size=9.5, color='white'), insidetextorientation='horizontal')

    # Gráfico de líneas vertical optimizado
    semanas_graf_p = df_resumen_final['Semana'].tolist() if not df_resumen_final.empty else ['Sem 1']
    pres_total_linea_p = [presupuesto_actual_total] * len(semanas_graf_p)
    gasto_acumulado_graf_p = df_resumen_final['Gasto Acumulado (S/)'].tolist() if not df_resumen_final.empty else [0]

    fig_linea_print = go.Figure()
    fig_linea_print.add_trace(go.Scatter(x=semanas_graf_p, y=pres_total_linea_p, mode='lines', name='Presupuesto Total', line=dict(color='#10b981', dash='dash', width=2)))
    fig_linea_print.add_trace(go.Scatter(x=semanas_graf_p, y=gasto_acumulado_graf_p, mode='lines+markers', name='Gasto Acumulado', line=dict(color='#ef4444', width=3)))
    fig_linea_print.update_layout(
        title=dict(text="Curva Presupuesto vs Gasto Acumulado", font=dict(color="#0f172a", size=13)),
        paper_bgcolor="white", plot_bgcolor="white", margin=dict(t=30, b=40, l=70, r=20),
        legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5, font=dict(color="#0f172a", size=9)),
        font=dict(color="#0f172a"),
        xaxis=dict(tickangle=0, gridcolor="#e2e8f0"),
        yaxis=dict(tickprefix="S/ ", tickformat=",.0f", gridcolor="#e2e8f0", dtick=2000),
        width=480, height=280
    )

    html_dona_str = fig_dona_print.to_html(include_plotlyjs='inline', full_html=False, config={'displayModeBar': False})
    html_linea_str = fig_linea_print.to_html(include_plotlyjs='inline', full_html=False, config={'displayModeBar': False})

    # ==========================================
    # ENSAMBLAJE HTML
    # ==========================================
    html_reporte = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Informe Técnico - Nexus Obra</title>
        <style>
            @page {{ size: A4; margin: 10mm; }}
            body {{ font-family: Arial, sans-serif; color: #000; margin: 0; padding: 0; font-size: 8.5pt; line-height: 1.15; background: #fff; }}
            .header {{ border-bottom: 2px solid #0f172a; padding-bottom: 4px; margin-bottom: 8px; }}
            .header h1 {{ font-size: 12pt; margin: 0 0 2px 0; color: #0f172a; text-transform: uppercase; }}
            .header h2 {{ font-size: 8.5pt; margin: 0; color: #334155; font-weight: normal; }}
            .info-box {{ background: #f8fafc; border: 1px solid #cbd5e1; padding: 5px 7px; margin-bottom: 8px; font-size: 8pt; }}
            .section-title {{ font-size: 9.5pt; font-weight: bold; color: #0284c7; margin-top: 8px; margin-bottom: 2px; border-bottom: 1px solid #0284c7; padding-bottom: 1px; page-break-after: avoid; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 2px; margin-bottom: 4px; font-size: 7.5pt; page-break-inside: avoid; }}
            th, td {{ border: 1px solid #94a3b8; padding: 2px 3px; text-align: left; }}
            th {{ background: #1e293b; color: white; }}
            .text-right {{ text-align: right; }}
            .text-center {{ text-align: center; }}
            .grafico-center {{ text-align: center; margin: 6px auto; page-break-inside: avoid; display: flex; justify-content: center; }}
            .worker-section {{ page-break-inside: avoid; }}
            @media print {{
                button {{ display: none; }}
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>SISTEMA DE CONTROL DE PROYECTOS - NEXUS OBRA</h1>
            <h2>Informe Técnico de Control Presupuestal y Mano de Obra</h2>
        </div>
        
        <div class="info-box">
            <b>Proyecto / Descripción:</b> Se hizo el trabajo en el tercer nivel vivienda unifamiliar en ADCIDEPATA Mz. E Lt. 3<br>
            <b>Ubicación:</b> Distrito Ayacucho, Provincia Huamanga, Departamento Ayacucho<br>
            <b>Partida Evaluada:</b> {st.session_state['partida_actual']}<br>
            <b>Cliente:</b> Cliente X<br>
            <b>Mes Evaluado:</b> {meses_espanol[st.session_state['cal_mes']]} {st.session_state['cal_ano']}<br>
            <b>Costo al:</b> {date.today().strftime('%d/%m/%Y')} &nbsp;&nbsp;|&nbsp;&nbsp; <b>Fecha de Impresión:</b> {fecha_impresion_str}
        </div>

        <!-- 1. ANÁLISIS FINANCIERO Y RESUMEN GLOBAL -->
        <div class="section-title">1. Análisis Financiero y Resumen Global</div>
        <p style="margin: 2px 0 4px 0;">
            El presente informe detalla el estado económico y operativo de la partida <b>{st.session_state['partida_actual']}</b>. 
            Hasta la fecha de corte, se ha asignado un presupuesto total de <b>S/ {presupuesto_actual_total:,.2f}</b>, 
            registrando un gasto acumulado de <b>S/ {gasto_total_acumulado:,.2f}</b>. 
            Esto representa un estado financiero de <b>{"SALDO A FAVOR" if (presupuesto_actual_total - gasto_total_acumulado) >= 0 else "SOBREGIRO"}</b> 
            por un monto de <b>S/ {abs(presupuesto_actual_total - gasto_total_acumulado):,.2f}</b>. 
            El análisis de distribución muestra un control riguroso de la ejecución en campo dentro del ámbito de Ayacucho-Huamanga.
        </p>

        <!-- 2. ANÁLISIS GRÁFICO DE EJECUCIÓN (En columna vertical centrada) -->
        <div class="section-title">2. Análisis Gráfico de Ejecución (Distribución y Tendencia)</div>
        <div class="grafico-center">{html_dona_str}</div>
        <div class="grafico-center">{html_linea_str}</div>

        <!-- 3. RESUMEN GENERAL POR SEMANAS DE TRABAJO -->
        <div class="section-title">3. Resumen General por Semanas de Trabajo (Lunes a Sábado)</div>
        <table>
            <thead>
                <tr>
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
                    <td>{row['Semana']}</td>
                    <td>{row['Rango (Lunes a Sábado)']}</td>
                    <td class="text-right">S/ {row['Gasto Mano Obra (S/)']:,.2f}</td>
                    <td class="text-right">S/ {row['Gasto Materiales (S/)']:,.2f}</td>
                    <td class="text-right">S/ {row['Gasto Total Semanal (S/)']:,.2f}</td>
                    <td class="text-right">S/ {row['Gasto Acumulado (S/)']:,.2f}</td>
                    <td class="text-right">S/ {row['Saldo vs Presupuesto (S/)']:,.2f}</td>
                </tr>
        """
        
    html_reporte += f"""
                <tr>
                    <td><b>TOTAL</b></td>
                    <td></td>
                    <td class="text-right"><b>S/ {gasto_mo_real_total:,.2f}</b></td>
                    <td class="text-right"><b>S/ {gasto_mat_real_total:,.2f}</b></td>
                    <td class="text-right"><b>S/ {gasto_mo_real_total + gasto_mat_real_total:,.2f}</b></td>
                    <td></td>
                    <td></td>
                </tr>
            </tbody>
        </table>

        <!-- 4. DETALLE DE PLANILLA POR TRABAJADOR -->
        <div class="section-title">4. Detalle de Planilla por Trabajador (Desglose de las 4 Semanas del Mes)</div>
    """
    
    for _, pers in df_pers_actual.iterrows():
        t_nombre = pers['nombre']
        t_esp = pers['especialidad']
        
        html_reporte += f"""
        <div class="worker-section">
            <div style="background: #e2e8f0; padding: 3px 6px; font-weight: bold; margin-top: 6px; margin-bottom: 2px; font-size: 8.5pt;">
                👷 Obrero: <i>{t_esp}</i> — <b>{t_nombre}</b>
            </div>
        """
        
        for s_nombre, s_ini, s_fin in semanas_mes_lista:
            df_t_s = pd.DataFrame()
            if not df_asist_db.empty:
                m_ts = (df_asist_db['trabajador'] == t_nombre) & (df_asist_db['fecha_dt'] >= s_ini) & (df_asist_db['fecha_dt'] <= s_fin) & (df_asist_db['partida'] == st.session_state['partida_actual'])
                df_t_s = df_asist_db.loc[m_ts].sort_values('fecha')
                
            c_comp = len(df_t_s[df_t_s['estado'] == 'Día Completo']) if not df_t_s.empty else 0
            c_med = len(df_t_s[df_t_s['estado'] == 'Medio Día']) if not df_t_s.empty else 0
            c_alm = len(df_t_s[df_t_s['almuerzo'].str.startswith('No', na=False)]) if not df_t_s.empty else 0
            
            jornal_v = float(pers['jornal']) if pd.notna(pers['jornal']) else 120.0
            alm_v = float(pers['almuerzo_costo']) if pd.notna(pers['almuerzo_costo']) else 7.0
            
            p_comp = c_comp * jornal_v
            p_med = c_med * (jornal_v / 2.0)
            p_alm = c_alm * alm_v
            tot_s_trab = p_comp + p_med + p_alm
            
            html_reporte += f"""
            <p style="margin: 2px 0 1px 4px; font-size: 8pt;"><b>{s_nombre}</b> ({s_ini.strftime('%d/%m/%Y')} al {s_fin.strftime('%d/%m/%Y')}):</p>
            <table>
                <thead>
                    <tr>
                        <th>Fecha</th>
                        <th>Día</th>
                        <th>Estado Asistencia</th>
                        <th>Almuerzo Afuera</th>
                        <th>Actividad / Observación</th>
                    </tr>
                </thead>
                <tbody>
            """
            
            if not df_t_s.empty:
                for _, r_as in df_t_s.iterrows():
                    dt_f = date.fromisoformat(str(r_as['fecha']))
                    d_nombre = dias_es_map_rep[dt_f.weekday()]
                    html_reporte += f"""
                    <tr>
                        <td>{dt_f.strftime('%d/%m/%Y')}</td>
                        <td>{d_nombre}</td>
                        <td>{r_as['estado']}</td>
                        <td>{r_as['almuerzo']}</td>
                        <td>{r_as['actividad'] if r_as['actividad'] else 'Sin observaciones'}</td>
                    </tr>
                    """
            else:
                html_reporte += """
                    <tr>
                        <td colspan="5" class="text-center"><i>Sin registros en esta semana.</i></td>
                    </tr>
                """
            html_reporte += f"""
                </tbody>
            </table>
            <p class="text-right" style="font-size: 8pt; margin: 0 0 4px 0; font-weight: bold;">Subtotal {s_nombre}: S/ {tot_s_trab:,.2f}</p>
            """
        html_reporte += "</div>"

    # 5. Control de Materiales e Insumos
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
                    <th class="text-right">Parcial (S/)</th>
                </tr>
            </thead>
            <tbody>
    """
    
    gasto_mat_rep = 0.0
    if not df_mat_db.empty:
        mask_m_rep = (df_mat_db['fecha_dt'] >= first_m) & (df_mat_db['fecha_dt'] <= last_m) & (df_mat_db['partida'] == st.session_state['partida_actual'])
        df_mat_rep = df_mat_db.loc[mask_m_rep].sort_values('fecha')
        for _, r_m in df_mat_rep.iterrows():
            dt_m = date.fromisoformat(str(r_m['fecha']))
            d_m_nom = dias_es_map_rep[dt_m.weekday()]
            cant_m = float(r_m['cantidad'])
            prec_m = float(r_m['precio'])
            parc_m = cant_m * prec_m
            gasto_mat_rep += parc_m
            
            html_reporte += f"""
                <tr>
                    <td>{dt_m.strftime('%d/%m/%Y')} ({d_m_nom})</td>
                    <td>{r_m['insumo']}</td>
                    <td class="text-center">{r_m['und']}</td>
                    <td class="text-right">{cant_m:,.2f}</td>
                    <td class="text-right">S/ {prec_m:,.2f}</td>
                    <td class="text-right">S/ {parc_m:,.2f}</td>
                </tr>
            """
            
    if gasto_mat_rep == 0.0:
        html_reporte += """
                <tr>
                    <td colspan="6" class="text-center"><i>No se registraron materiales en este mes.</i></td>
                </tr>
        """
        
    html_reporte += f"""
            </tbody>
        </table>
        <p class="text-right" style="font-size: 9pt; font-weight: bold; margin-top: 3px;">TOTAL MATERIALES MES: S/ {gasto_mat_rep:,.2f}</p>
        
        <br>
        <div style="text-align: center; font-size: 8pt; color: #64748b; border-top: 1px solid #cbd5e1; padding-top: 6px;">
            Reporte Ejecutivo Oficial &bull; Plataforma Nexus Obra &bull; Ayacucho, Perú
        </div>
        
        <script>
            setTimeout(function() {{
                window.print();
            }}, 1500);
        </script>
    </body>
    </html>
    """
    
    st.components.v1.html(html_reporte, height=800, scrolling=True)
