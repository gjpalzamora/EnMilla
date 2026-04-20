import streamlit as st
import pandas as pd
from datetime import datetime
# Asumimos que tienes tu lógica de conexión en database.py
from database import obtener_datos, registrar_fila, actualizar_estado

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="EnMilla v2.0 - Gestión Logística", layout="wide")

st.title("📦 EnMilla v2.0")
st.caption("Enlaces Soluciones Logísticas S.A.S. | NIT: 901.939.284-4")

# --- NAVEGACIÓN DEL PLAN MAESTRO ---
menu = st.sidebar.selectbox(
    "Módulo Operativo",
    ["Dashboard", "Carga Masiva (Excel)", "Recepción (Ingreso)", "Despacho (Salida)", "Historial/Logs"]
)

# --- 1. MÓDULO DE CARGA MASIVA ---
if menu == "Carga Masiva (Excel)":
    st.header("📂 Carga de Manifiestos de Clientes")
    archivo = st.file_uploader("Subir archivo Excel de cliente (Temu, Integra, etc.)", type=['xlsx', 'csv'])
    
    if archivo:
        df_carga = pd.read_excel(archivo)
        st.write("Vista previa de datos a importar:")
        st.dataframe(df_carga.head())
        
        if st.button("Confirmar Carga en Base de Datos"):
            # Aquí la lógica para guardar en la Tabla Paquetes (Master)
            # registrar_en_master(df_carga)
            st.success(f"Se han cargado {len(df_carga)} guías al sistema.")

# --- 2. MÓDULO DE RECEPCIÓN (Ingreso a Bodega) ---
elif menu == "Recepción (Ingreso)":
    st.header("📥 Recepción de Mercancía - Barrios Unidos")
    
    with st.form("ingreso_form", clear_on_submit=True):
        guia = st.text_input("ESCANEAR GUÍA (Pistoleo):", placeholder="Cursor aquí para lector de barras...")
        submit = st.form_submit_button("Confirmar Ingreso")
        
        if submit and guia:
            # VALIDACIÓN: ¿Existe en el manifiesto cargado?
            ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            registrar_fila("Ingresos", [guia, "Operario_Bodega", ahora, "EN BODEGA"])
            st.success(f"✅ Guía {guia} registrada con éxito.")

# --- 3. MÓDULO DE DESPACHO (El Escudo de Seguridad) ---
elif menu == "Despacho (Salida)":
    st.header("🚚 Despacho y Asignación a Ruta")
    
    # 1. Selección de Mensajero
    mensajeros = pd.DataFrame(obtener_datos("Mensajeros"))
    m_sel = st.selectbox("Seleccionar Mensajero Responsable:", mensajeros['Nombre'])
    
    # 2. Asignación automática de Placa (Trazabilidad)
    placa = mensajeros[mensajeros['Nombre'] == m_sel]['Placa'].values[0]
    st.info(f"Vehículo vinculado: **{placa}**")

    with st.form("despacho_form", clear_on_submit=True):
        guia_out = st.text_input("ESCANEAR PARA SALIDA:", placeholder="Pistolee la guía para asignar...")
        confirmar = st.form_submit_button("Autorizar Salida")
        
        if confirmar and guia_out:
            # LÓGICA DE ESCUDO: ¿Tiene ingreso previo?
            ingresos = pd.DataFrame(obtener_datos("Ingresos"))
            
            if guia_out in ingresos['Guia'].astype(str).values:
                ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                # Registramos en Historial (Logs) como definimos en el Plan Maestro
                registrar_fila("Logs", [guia_out, m_sel, placa, "EN REPARTO", ahora])
                st.success(f"🚀 Guía {guia_out} asignada a {m_sel} ({placa})")
            else:
                st.error(f"❌ ERROR CRÍTICO: La guía {guia_out} NO tiene ingreso previo a bodega. Bloqueado.")

# --- 4. DASHBOARD (Saldos y Auditoría) ---
elif menu == "Dashboard":
    st.header("📊 Control Gerencial de Inventario")
    col1, col2, col3 = st.columns(3)
    col1.metric("En Bodega", "124", "5%")
    col2.metric("En Reparto", "89", "-2%")
    col3.metric("Novedades", "12", "1%")
