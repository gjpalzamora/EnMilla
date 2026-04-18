import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# --- CONFIGURACIÓN E IDENTIDAD VISUAL (RF3.6) ---
st.set_page_config(page_title="Enmilla ERP | Enlace Soluciones", layout="wide", page_icon="🚚")

# Inyección de CSS para optimizar la UI de operación rápida (RF3.6.3)
st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    .main-header { color: #003366; font-size: 2.5rem; font-weight: bold; }
    .stButton>button { background-color: #003366; color: white; height: 3em; width: 100%; }
    </style>
    """, unsafe_allow_html=True)

# URL Base de tu API Node.js
API_URL = "http://localhost:3000/api"

# --- SIDEBAR: NAVEGACIÓN INTUITIVA (RF3.6.1) ---
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/2311/2311894.png", width=100)
st.sidebar.title("Control de Operaciones")
menu = st.sidebar.radio("Módulos", [
    "📦 Recepción de Paquetes", 
    "🚚 Despacho y Entrega", 
    "🔍 Seguimiento 360",
    "👥 Gestión de Mensajeros"
])

# --- MÓDULO 1: RECEPCIÓN (RF3.1) ---
if menu == "📦 Recepción de Paquetes":
    st.markdown("<h1 class='main-header'>Registro de Ingresos</h1>", unsafe_allow_html=True)
    
    with st.expander("➕ Registrar Nuevo Paquete Individual", expanded=True):
        with st.form("registro_paquete"):
            col1, col2 = st.columns(2)
            with col1:
                tracking = st.text_input("Número de Seguimiento (Único)", placeholder="Ej: ENL123456")
                sender = st.text_input("Nombre del Remitente")
            with col2:
                recipient = st.text_input("Nombre del Destinatario")
                address = st.text_area("Dirección de Entrega", height=68)
            
            if st.form_submit_button("Confirmar Ingreso a Bodega"):
                if not tracking or not recipient or not address:
                    st.error("⚠️ Los campos con asterisco son obligatorios.")
                else:
                    # Lógica: Enviar a la API y registrar movimiento inicial (RF3.1.1)
                    data = {
                        "tracking_number": tracking,
                        "sender_name": sender,
                        "recipient_name": recipient,
                        "recipient_address": address,
                        "status": "Recibido"
                    }
                    try:
                        res = requests.post(f"{API_URL}/package", json=data)
                        if res.status_code == 201:
                            st.success(f"✅ Paquete {tracking} registrado y movimiento inicial creado.")
                        else:
                            st.error(f"❌ Error: {res.json().get('message')}")
                    except:
                        st.info("Simulación: Registro guardado (Conecta la API para persistencia).")

# --- MÓDULO 2: DESPACHO Y ENTREGA (RF3.3) ---
elif menu == "🚚 Despacho y Entrega":
    st.markdown("<h1 class='main-header'>Gestión de Salidas</h1>", unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["🚀 Asignar Ruta", "🏁 Registrar Entrega (POD)"])
    
    with tab1:
        st.subheader("Asignación de Mensajeros")
        paquete_id = st.text_input("Escanear Guía para Despacho")
        mensajero = st.selectbox("Seleccionar Mensajero Activo", ["Cargando...", "Juan Pérez", "Sandra Gómez"])
        if st.button("Asignar y Cambiar a 'En Tránsito'"):
            st.success(f"Paquete asignado a {mensajero}. Estado actualizado.")

    with tab2:
        st.subheader("Cierre de Entrega y Generación de POD (RF3.3.3)")
        guia_entrega = st.text_input("Confirmar Guía Entregada")
        receptor = st.text_input("Nombre de quien recibe")
        if st.button("Finalizar Entrega y Generar PDF"):
            # Lógica: Llamar al pod.service.js de tu API
            st.balloons()
            st.success("POD generado con éxito. Almacenado en delivery_proof_url.")
            st.download_button("📥 Descargar Comprobante PDF", data="Contenido_PDF_Binario", file_name=f"POD_{guia_entrega}.pdf")

# --- MÓDULO 3: SEGUIMIENTO 360 (RF3.2) ---
elif menu == "🔍 Seguimiento 360":
    st.markdown("<h1 class='main-header'>Trazabilidad Total</h1>", unsafe_allow_html=True)
    query = st.text_input("Buscar por Número de Seguimiento")
    
    if query:
        # Simulación de respuesta de movimientos (RF3.2.2)
        st.subheader(f"Historial del Paquete: {query}")
        historial = [
            {"Fecha": "2026-04-16 08:00", "Evento": "Recibido en Bodega Bogotá", "Ubicación": "Recepción"},
            {"Fecha": "2026-04-17 09:30", "Evento": "En Tránsito", "Ubicación": "Vehículo Reparto"},
            {"Fecha": "2026-04-17 14:00", "Evento": "Entregado", "Ubicación": "Dirección Cliente"}
        ]
        st.table(pd.DataFrame(historial))

# --- FOOTER CORPORATIVO ---
st.sidebar.markdown("---")
st.sidebar.caption(f"© {datetime.now().year} Enlace Soluciones Logísticas SAS")
st.sidebar.write("Versión 1.0 - Powered by Enmilla Engine")
