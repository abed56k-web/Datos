import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date
import random

# 1. CONFIGURACIÓN DE LA PÁGINA
st.set_page_config(page_title="Control de Obra", layout="wide", initial_sidebar_state="collapsed")

# 2. PANTALLA DE INICIO DE SESIÓN
# Usamos session_state para que recuerde que ya entraste
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False

if not st.session_state['autenticado']:
    # Diseño de la pantalla de login
    st.markdown("<h1 style='text-align: center; color: #ff4b4b;'>🏗️ Bienvenido a la Obra</h1>", unsafe_allow_html=True)
    st.markdown("<h4 style='text-align: center;'>Ingresa para hacer el seguimiento</h4>", unsafe_allow_html=True)
    
    # Usamos columnas para centrar el cuadro de contraseña
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.write("---")
        clave = st.text_input("Contraseña de acceso:", type="password")
        if st.button("Iniciar Sesión", use_container_width=True):
            if clave == "ayacucho2026":  # Tu contraseña
                st.session_state['autenticado'] = True
                st.rerun() # Recarga la página para entrar
            else:
                st.error("Contraseña incorrecta. Intenta de nuevo.")
    st.stop() # Detiene el código aquí si no hay contraseña correcta

# ==========================================
# 3. SISTEMA PRINCIPAL (Solo se ve si entró)
# ==========================================
st.title("📊 Panel de Control: Avance y Gastos")

# Creamos dos pestañas para organizar la pantalla
pestana1, pestana2 = st.tabs(["📝 Ingreso de Datos diarios", "📅 Calendario de Avance"])

with pestana1:
    col_form1, col_form2 = st.columns(2)
    
    with col_form1:
        st.subheader("Registro de Personal")
        with st.form("form_personal"):
            fecha_p = st.date_input("Fecha", date.today())
            nombre = st.text_input("Nombre del Trabajador")
            cargo = st.selectbox("Cargo", ["Operario", "Ayudante"])
            frente = st.selectbox("Frente de Trabajo", ["2do Piso (Enchapado, pintura, puertas)", "3er Piso (Tarrajeo)"])
            jornal = st.number_input("Salario / Jornal (S/)", min_value=0.0, format="%.2f")
            btn_personal = st.form_submit_button("Guardar Asistencia")
            if btn_personal:
                st.success(f"Asistencia de {nombre} guardada correctamente.")

    with col_form2:
        st.subheader("Registro de Materiales")
        with st.form("form_materiales"):
            fecha_m = st.date_input("Fecha de compra", date.today())
            # Opciones precargadas para que sea más rápido llenar desde el celular
            material = st.selectbox("Material", ["Cemento", "Cerámicos 60x60cm", "Pegamento para cerámico", "Pintura", "Sikaflex-11 FC", "Tubos/Conexiones", "Otro"])
            cantidad = st.number_input("Cantidad", min_value=1)
            costo_total = st.number_input("Costo Total (S/)", min_value=0.0, format="%.2f")
            frente_m = st.selectbox("Destino", ["2do Piso", "3er Piso", "General"])
            btn_material = st.form_submit_button("Guardar Material")
            if btn_material:
                st.success(f"Compra de {material} guardada correctamente.")

with pestana2:
    st.subheader("Intensidad de Gastos y Avance por Día")
    st.info("Los cuadros más oscuros indican los días con mayor inversión (S/) en la obra.")
    
    # Generamos datos de ejemplo para que puedas ver cómo funciona el calendario
    fechas = pd.date_range(start='2026-09-01', end='2026-10-31')
    datos_calendario = pd.DataFrame({'Fecha': fechas})
    # Simulamos gastos aleatorios para el ejemplo gráfico
    datos_calendario['Gasto_Diario'] = [random.choice([0, 150, 300, 450, 0, 80, 0]) for _ in range(len(fechas))]
    
    # Extraemos la semana y el día de la semana para armar la cuadrícula
    datos_calendario['Semana'] = datos_calendario['Fecha'].dt.isocalendar().week
    datos_calendario['Dia_Semana'] = datos_calendario['Fecha'].dt.day_name()
    
    # Creamos el mapa de calor (Heatmap) con Plotly
    fig = px.density_heatmap(
        datos_calendario, 
        x="Semana", 
        y="Dia_Semana", 
        z="Gasto_Diario",
        color_continuous_scale="Greens", # Color verde para el avance
        labels={'Semana': 'Semana del Año', 'Dia_Semana': 'Día', 'Gasto_Diario': 'Gasto Total (S/)'}
    )
    
    # Ordenamos los días de lunes a domingo
    fig.update_yaxes(categoryorder='array', categoryarray=['Sunday', 'Saturday', 'Friday', 'Thursday', 'Wednesday', 'Tuesday', 'Monday'])
    
    # Mostramos el gráfico en pantalla completa
    st.plotly_chart(fig, use_container_width=True)
