import streamlit as st
import pandas as pd
from datetime import datetime
from database import obtener_datos, registrar_fila

st.title("Sistema de Gestión de Inventarios - En enlaces")
st.caption("NIT: 901.939.284-4 | Sede Barrios Unidos")

# --- ELEMENTO 1: RESUMEN DE INVENTARIO ACTUAL ---
st.subheader("📊 Estado del Inventario")
ingresos = pd.DataFrame(obtener_datos("Ingresos"))
despachos = pd.DataFrame(obtener_datos("Despacho"))

if not ingresos.empty:
    guias_en_bodega = len(ingresos) - len(despachos)
    col1, col2 = st.columns(2)
    col1.metric("Total Ingresado", len(ingresos))
    col2.metric("Stock Actual (En Bodega)", guias_en_bodega)
else:
    st.info("Inventario vacío. Inicie recepciones.")

# --- NAVEGACIÓN ---
menu = st.radio("Acción de Inventario:", ["📥 Recepción (Entrada)", "🚚 Despacho (Salida)"], horizontal=True)

# --- ELEMENTO 2: MÓDULO DE RECEPCIÓN ---
if menu == "📥 Recepción (Entrada)":
    clientes = pd.DataFrame(obtener_datos("Clientes"))
    if not clientes.empty:
        c_sel = st.selectbox("Cliente / Asociado Remitente:", clientes['Nombre'])
        
        with st.form("form_ingreso", clear_on_submit=True):
            # El cursor debe estar aquí para el lector de barras
            guia_in = st.text_input("ESCANEAR GUÍA DE ENTRADA:")
            if st.form_submit_button("Confirmar Entrada"):
                ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                # Estructura: Guia, Cliente, Fecha, Estado
                registrar_fila("Ingresos", [guia_in, c_sel, ahora, "EN BODEGA"])
                st.success(f"Registrado: Guía {guia_in} en inventario.")
                st.rerun()

# --- ELEMENTO 3: MÓDULO DE DESPACHO ---
elif menu == "🚚 Despacho (Salida)":
    mensajeros = pd.DataFrame(obtener_datos("Mensajeros"))
    if not mensajeros.empty:
        m_sel = st.selectbox("Asignar a Mensajero:", mensajeros['Nombre'])
        # ELEMENTO MECÁNICO: Traer placa automáticamente
        placa = mensajeros[mensajeros['Nombre'] == m_sel]['Placa'].values[0]
        st.write(f"Vehículo asignado: **{placa}**")
        
        with st.form("form_despacho", clear_on_submit=True):
            guia_out = st.text_input("ESCANEAR GUÍA PARA SALIDA:")
            if st.form_submit_button("Confirmar Salida"):
                # VALIDACIÓN: ¿Está la guía en inventario de entrada?
                if not ingresos.empty and guia_out in ingresos['Guia'].astype(str).values:
                    ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    # Estructura: Guia, Mensajero, Placa, Fecha, Estado
                    registrar_fila("Despacho", [guia_out, m_sel, placa, ahora, "EN RUTA"])
                    st.success(f"Despachado: Guía {guia_out} salió de inventario.")
                else:
                    st.error(f"⚠️ ERROR: La guía {guia_out} no existe en el inventario de entrada.")
                st.rerun()
