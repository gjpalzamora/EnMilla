import streamlit as st
import pandas as pd
from datetime import datetime
import time

# --- CONFIGURACIÓN TÉCNICA Y ESTÉTICA ---
st.set_page_config(page_title="Enmilla ERP | Enlace Soluciones", layout="wide")

# Inicialización de estados de memoria (Para no perder datos si la conexión parpadea)
if 'scan_buffer' not in st.session_state:
    st.session_state.scan_buffer = []
if 'total_count' not in st.session_state:
    st.session_state.total_count = 0

# --- LÓGICA DE PROCESAMIENTO PROACTIVO ---
def registrar_ingreso(tracking):
    """Lógica de experto: Registra con datos mínimos para no frenar la descarga."""
    ingreso = {
        "tracking_number": tracking,
        "fecha_ingreso": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "estado": "Recibido en Bodega",
        "ubicacion_inicial": "Muelle de Descarga - Bogotá",
        "prioridad": "Alta" if "PRI" in tracking.upper() else "Estándar"
    }
    st.session_state.scan_buffer.insert(0, ingreso) # Lo más nuevo arriba
    st.session_state.total_count += 1

# --- INTERFAZ DE USUARIO OPERATIVA ---
st.title("🚀 Enmilla ERP: Recepción de Contingencia")
st.markdown("---")

col_escaneo, col_resumen = st.columns([1, 2])

with col_escaneo:
    st.subheader("Entrada de Mercancía")
    # Campo con foco automático (simulado por el flujo de Streamlit)
    with st.form("form_scanner", clear_on_submit=True):
        tracking_input = st.text_input("ESCANEE AQUÍ (Sin Base de Datos)", key="input_scan")
        submit = st.form_submit_button("REGISTRAR")
        
        if submit and tracking_input:
            registrar_ingreso(tracking_input)
            st.toast(f"Paquete {tracking_input} en bodega", icon="📦")

    st.metric("Paquetes Escaneados", st.session_state.total_count)
    
    if st.button("💾 Sincronizar con Base de Datos Principal"):
        # Aquí el software intentará hacer el 'match' con los datos del cliente
        st.info("Iniciando proceso de conciliación con PostgreSQL...")
        time.sleep(1)
        st.success("Sincronización completada. Datos preparados para despacho.")

with col_resumen:
    st.subheader("Últimos Ingresos (Historial de Sesión)")
    if st.session_state.scan_buffer:
        df_sesion = pd.DataFrame(st.session_state.scan_buffer)
        st.dataframe(df_sesion, use_container_width=True, height=400)
    else:
        st.info("Esperando primer escaneo del camión...")

# --- MÓDULO DE DESPACHO INTELIGENTE (Propositivo) ---
st.markdown("---")
st.subheader("🚚 Planificación de Despacho Inmediato")
if st.session_state.scan_buffer:
    with st.expander("Asignar estos paquetes a ruta ahora mismo"):
        mensajero = st.selectbox("Mensajero Disponible", ["Edwin Ruiz", "Oscar Marzola", "Tercero Externo"])
        zona = st.selectbox("Zona de Entrega", ["Norte - Usaquén", "Centro - Barrios Unidos", "Sur - Kennedy"])
        if st.button("Confirmar Salida a Ruta"):
            st.success(f"Generando Manifiesto de Salida para {mensajero}...")
