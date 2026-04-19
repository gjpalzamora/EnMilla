import streamlit as st
import pandas as pd
from datetime import datetime
from database import obtener_datos, registrar_fila

# --- CONFIGURACIÓN E IDENTIDAD ---
st.set_page_config(page_title="EnMilla - Logística", layout="wide")

st.sidebar.markdown(f"""
    ### 🚚 EnMilla v2.0
    **Enlaces Soluciones Logísticas SAS**
    NIT: 901.939.284-4
    *Bogotá, Colombia*
    ---
""")

menu = st.sidebar.radio("Operación", ["Administración", "Recepción (Ingreso)", "Despacho (Salida)"])

# --- LÓGICA DE DESPACHO (SALIDA) ---
if menu == "Despacho (Salida)":
    st.header("🚚 Despacho a Ruta")
    
    # Traemos mensajeros desde Google Sheets
    mensajeros = obtener_datos("Mensajeros")
    if mensajeros:
        df_m = pd.DataFrame(mensajeros)
        m_nombre = st.selectbox("Seleccione Mensajero:", df_m['Nombre'])
        m_datos = df_m[df_m['Nombre'] == m_nombre].iloc[0]
        
        st.success(f"Asignado a: {m_nombre} | Vehículo: {m_datos['Vehiculo']} | Placa: {m_datos['Placa']}")
        
        with st.form("salida", clear_on_submit=True):
            guia = st.text_input("ESCANEAR GUÍA PARA SALIDA:")
            if st.form_submit_button("Confirmar Despacho"):
                ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                # Registramos en la pestaña 'Despacho' de su Google Sheet
                registrar_fila("Despacho", [guia, m_nombre, m_datos['Placa'], ahora, "EN RUTA"])
                st.balloons()
                st.info(f"Guía {guia} asignada correctamente.")
    else:
        st.error("No hay mensajeros registrados en Google Sheets.")

# --- LÓGICA DE RECEPCIÓN (INGRESO) ---
elif menu == "Recepción (Ingreso)":
    st.header("📥 Ingreso a Bodega")
    clientes = obtener_datos("Clientes")
    if clientes:
        df_c = pd.DataFrame(clientes)
        cliente_sel = st.selectbox("Cliente / Asociado:", df_c['Nombre'])
        
        with st.form("ingreso", clear_on_submit=True):
            guia_in = st.text_input("ESCANEAR GUÍA DE ENTRADA:")
            if st.form_submit_button("Registrar Ingreso"):
                ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                registrar_fila("Ingresos", [guia_in, cliente_sel, ahora, "EN BODEGA"])
                st.success(f"Guía {guia_in} registrada para {cliente_sel}")
