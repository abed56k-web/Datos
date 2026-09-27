import streamlit as st

# --- 1. PANTALLA DE SEGURIDAD ---
st.title("🔒 Acceso Restringido")
clave_ingresada = st.text_input("Contraseña de acceso:", type="password")

# Cambia "ayacucho2026" por la clave que prefieras
if clave_ingresada != "ayacucho2026":
    st.warning("Ingresa la contraseña para ver los datos de la obra.")
    st.stop()  # El código se detiene aquí. Nadie ve lo de abajo sin la clave.

# --- 2. TU SISTEMA DE OBRA (Solo se ejecuta si la clave es correcta) ---
st.empty() # Limpia el mensaje de arriba
st.success("Acceso concedido.")

# Aquí pegas todo el código de tu Dashboard, el calendario y los registros
st.title("🏗️ Control de Obra: Enchapado y Tarrajeo")
# ... (resto de tu programa)
