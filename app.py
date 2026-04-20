import streamlit as st
import pandas as pd
from datetime import datetime
# Importamos las funciones con los nombres EXACTOS que definimos arriba
from database import obtener_datos, registrar_fila

# Configuración de página (Esto debe ir de primero)
st.set_page_config(page_title="EnMilla Logistics", layout="wide")

# Identidad Corporativa
st.sidebar.title("🚚 EnMilla v2.0")
st.sidebar.markdown("**Enlaces Soluciones Logísticas SAS**")
st.sidebar.write("NIT: 901.939.284-4")

menu = st.sidebar.radio("Operación", ["Ingreso (Bodega)", "Despacho (Ruta)"])

# --- LÓGICA DE INGRESO ---
if menu == "Ingreso (Bodega)":
    st.header("📥 Registro de Ingreso")
    # Intentar traer clientes de la pestaña 'Clientes'
    clientes = obtener_datos("Clientes")
    if clientes:
        df_c = pd.DataFrame(clientes)
        cliente_sel = st.selectbox("Seleccione Cliente:", df_c['Nombre'])
        
        with st.form("form_ingreso", clear_on_submit=True):
            guia = st.text_input("ESCANEAR GUÍA:")
            if st.form_submit_button("Registrar Entrada"):
                ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                exito = registrar_fila("Ingresos", [guia, cliente_sel, ahora, "EN BODEGA"])
                if exito:
                    st.success(f"✅ Guía {guia} registrada")
                else:
                    st.error("Error al guardar en Google Sheets")
    else:
        st.warning("⚠️ No se encontraron clientes en la hoja 'Clientes' de Google Sheets.")

# --- LÓGICA DE DESPACHO ---
elif menu == "Despacho (Ruta)":
    st.header("🚚 Salida de Mercancía")
    mensajeros = obtener_datos("Mensajeros")
    if mensajeros:
        df_m = pd.DataFrame(mensajeros)
        m_sel = st.selectbox("Asignar a:", df_m['Nombre'])
        
        with st.form("form_despacho", clear_on_submit=True):
            guia_out = st.text_input("ESCANEAR GUÍA PARA SALIDA:")
            if st.form_submit_button("Confirmar Despacho"):
                ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                # Buscamos la placa del mensajero seleccionado
                placa = df_m[df_m['Nombre'] == m_sel]['Placa'].values[0]
                exito = registrar_fila("Despacho", [guia_out, m_sel, placa, ahora, "EN RUTA"])
                if exito:
                    st.success(f"🚀 Guía {guia_out} en ruta con {m_sel}")
    else:
        st.warning("⚠️ No hay mensajeros en la hoja 'Mensajeros'.")
