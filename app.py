import streamlit as st
import requests
from datetime import datetime

# --- CONFIGURACIÓN DE IMAGEN CORPORATIVA ---
st.set_page_config(
    page_title="Enmilla ERP - Enlace Soluciones Logísticas", 
    layout="wide", 
    page_icon="🚚"
)

# URL de tu nueva API (Enlaces-360-API)
API_BASE_URL = "http://localhost:3000/api" # Cambiar por tu URL de producción

# --- ESTILOS ---
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #004a99; color: white; }
    </style>
    """, unsafe_allow_html=True)

# --- CABECERA ---
st.title("🚚 Enmilla ERP")
st.caption("Plataforma de Gestión Logística | Enlace Soluciones Logísticas SAS")

# --- MENÚ DE OPERACIONES (RF5.1 - RF5.4) ---
menu = st.sidebar.radio("Navegación Operativa", [
    "📦 Recepción Masiva", 
    "⛟ Distribución de Clientes", 
    "🔍 Rastreo 360",
    "👤 Gestión de Mensajeros"
])

# --- LÓGICA DE MÓDULOS ---

if menu == "📦 Recepción Masiva":
    st.header("Escaneo Rápido de Bodega (RF5.3)")
    st.info("Utilice el lector de códigos de barras para ingresos masivos.")
    
    # El campo de texto captura la entrada del scanner
    tracking_input = st.text_input("Esperando lectura de código...", key="scanner_input")
    
    if tracking_input:
        # Llamada al servicio de recepción de la API
        try:
            response = requests.post(f"{API_BASE_URL}/reception/scan", json={"tracking": tracking_input})
            if response.status_code == 200:
                st.success(f"✅ Guía {tracking_input} ingresada correctamente a bodega.")
            else:
                st.error(f"❌ Error en API: {response.json().get('message', 'Desconocido')}")
        except Exception as e:
            st.error(f"🔌 Error de conexión con Enlaces-360-API: {e}")

elif menu == "⛟ Distribución de Clientes":
    st.header("Distribución B2B (RF5.2)")
    st.write("Vincular envíos de clientes corporativos a destinatarios finales.")
    
    # Simulación de obtención de envíos pendientes desde la API
    with st.form("distribucion_form"):
        col1, col2 = st.columns(2)
        with col1:
            cliente = st.selectbox("Seleccionar Cliente Corporativo", ["Cliente A", "Cliente B"])
            lote = st.text_input("Número de Lote/Shipment")
        with col2:
            destinatario = st.text_input("Nombre Destinatario Final")
            direccion = st.text_input("Dirección Completa")
        
        if st.form_submit_button("Generar Guía Interna y Etiqueta"):
            # Aquí se llamaría a label.service.js a través de la API
            st.warning("🔄 Procesando en Enlaces-360-API...")
            st.info("🖨️ Generando POD/Etiqueta PDF vía fpdf2...")

elif menu == "🔍 Rastreo 360":
    st.header("Trazabilidad Total")
    busqueda = st.text_input("Ingrese Guía Interna o de Cliente")
    if busqueda:
        # Consulta al controlador de paquetes de la API
        res = requests.get(f"{API_BASE_URL}/package/{busqueda}")
        if res.status_code == 200:
            data = res.json()
            st.json(data) # Muestra el historial de movimientos (Movements)
        else:
            st.error("Guía no encontrada en el sistema.")

# --- FOOTER ---
st.sidebar.markdown("---")
st.sidebar.write(f"© {datetime.now().year} Enlace Soluciones Logísticas SAS")
st.sidebar.write("Versión 1.0 - Architecture 360")
