import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# --- CONFIGURACIÓN DE ALTO RENDIMIENTO ---
st.set_page_config(page_title="EnMilla ERP - Full Suite", layout="wide")
API_URL = "http://localhost:3000/api"

# --- INTERFAZ UNIFICADA ---
st.sidebar.title("🚚 EnMilla ERP v1.0")
opcion = st.sidebar.selectbox("Módulo Operativo", [
    "⚡ Recepción Masiva (Muelle)",
    "📦 Gestión de Inventario & Conciliación",
    "🚚 Despacho y Última Milla",
    "📊 Reportes y Auditoría"
])

# --- MÓDULO 1: RECEPCIÓN MASIVA (EL ESCENARIO DE LAS 10 PM) ---
if opcion == "⚡ Recepción Masiva (Muelle)":
    st.header("Entrada Rápida de Mercancía")
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Foco automático para scanner: Registro ciego inmediato
        with st.form("quick_scan", clear_on_submit=True):
            t_input = st.text_input("ESCANEE CÓDIGO", placeholder="Esperando lectura...")
            if st.form_submit_button("REGISTRAR") or t_input:
                # Lógica: Registra en BD solo con ID, hora y ubicación
                res = requests.post(f"{API_URL}/packages/fast-track", json={"tracking": t_input})
                st.toast(f"Registrado: {t_input}")

# --- MÓDULO 2: CONCILIACIÓN (ENRIQUECIMIENTO DE DATOS) ---
elif opcion == "📦 Gestión de Inventario & Conciliación":
    st.header("Carga de Manifiestos de Clientes")
    st.info("Suba el archivo del cliente para completar los datos de los paquetes ya escaneados.")
    file = st.file_uploader("Archivo CSV/Excel del Cliente")
    if file:
        df = pd.read_csv(file)
        if st.button("Sincronizar Datos"):
            # Proceso masivo: Une el tracking escaneado con Nombre/Dirección/Ciudad
            res = requests.patch(f"{API_URL}/packages/bulk-update", json=df.to_dict('records'))
            st.success(f"Se actualizaron {len(df)} registros exitosamente.")

# --- MÓDULO 3: DESPACHO Y POD (GENERACIÓN DE DOCUMENTOS) ---
elif opcion == "🚚 Despacho y Última Milla":
    st.header("Asignación de Rutas y Cierre de Entrega")
    tab_ruta, tab_entrega = st.tabs(["Asignar Mensajero", "Registrar POD"])
    
    with tab_entrega:
        guia = st.text_input("Confirmar Guía Entregada")
        foto = st.camera_input("Capturar Evidencia (Opcional)")
        if st.button("Finalizar Entrega"):
            # Genera PDF mediante el servicio de la API (fpdf2)
            requests.post(f"{API_URL}/packages/deliver", json={"tracking": guia})
            st.success("POD generado y almacenado en la nube.")

# --- MÓDULO 4: REPORTES ---
elif opcion == "📊 Reportes y Auditoría":
    st.header("Estado Global de la Operación")
    # Gráficos de cumplimiento y tiempos de entrega
    res = requests.get(f"{API_URL}/analytics/summary")
    st.write("Visualización de KPI logísticos.")
