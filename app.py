import streamlit as st
import pandas as pd
import time

# --- CONFIGURACIÓN LEGAL Y MARCA ---
st.set_page_config(page_title="Enmilla - Enlaces Logística", layout="wide")

st.markdown(f"""
    <div style="background-color:#003366;padding:10px;border-radius:10px">
    <h1 style="color:white;text-align:center;">ENMILLA - Gestión Logística</h1>
    <p style="color:white;text-align:center;">Propiedad de: <b>Enlaces Soluciones Logística SAS</b> | NIT: 901939284 | Bogotá D.C.</p>
    </div>
    """, unsafe_allow_name_tags=True)

# --- BASE DE DATOS TEMPORAL ---
if 'db' not in st.session_state:
    st.session_state.db = pd.DataFrame(columns=["ID", "Cliente", "Destino", "Estado", "Tipo"])

# --- MENÚ LATERAL ---
opcion = st.sidebar.selectbox("Módulo Operativo", ["Dashboard", "Ingreso / Inventario", "Generar POD Interno"])

if opcion == "Generar POD Interno":
    st.header("📝 Emisión de Guía Interna (POD)")
    with st.form("pod_form"):
        cliente = st.text_input("Asociado / Remitente")
        destino = st.text_input("Nombre del Destinatario")
        direccion = st.text_input("Dirección de Entrega (Bogotá)")
        if st.form_submit_button("Generar Guía"):
            nuevo_id = f"ENM-{time.strftime('%H%M%S')}"
            st.success(f"Guía {nuevo_id} generada para {destino}")
            # Aquí se guarda en la tabla
            nueva_data = {"ID": nuevo_id, "Cliente": cliente, "Destino": destino, "Estado": "Bodega", "Tipo": "Interna"}
            st.session_state.db = pd.concat([st.session_state.db, pd.DataFrame([nueva_data])], ignore_index=True)

if opcion == "Dashboard":
    st.header("📊 Inventario en Tiempo Real")
    st.table(st.session_state.db)
