import streamlit as st
import pandas as pd
import time

# --- CONFIGURACIÓN LEGAL Y MARCA ---
st.set_page_config(page_title="Enmilla - Enlaces Logística", layout="wide")

st.markdown(f"""
    <div style="background-color:#003366;padding:20px;border-radius:10px">
    <h1 style="color:white;text-align:center;margin:0;">ENMILLA - Gestión Logística</h1>
    <p style="color:white;text-align:center;margin:5px;">Propiedad de: <b>Enlaces Soluciones Logística SAS</b> | NIT: 901.939.284-4 | Bogotá D.C.</p>
    </div>
    <br>
    """, unsafe_allow_html=True)

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
            nueva_data = {"ID": nuevo_id, "Cliente": cliente, "Destino": destino, "Estado": "Bodega", "Tipo": "Interna"}
            st.session_state.db = pd.concat([st.session_state.db, pd.DataFrame([nueva_data])], ignore_index=True)

if opcion == "Dashboard":
    st.header("📊 Inventario en Tiempo Real")
    st.dataframe(st.session_state.db, use_container_width=True)
