import streamlit as st
import pandas as pd
import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Enmilla Pro - Gestión Logística", layout="wide")

# --- BASES DE DATOS EN MEMORIA ---
if 'db_mensajeros' not in st.session_state:
    st.session_state.db_mensajeros = pd.DataFrame(columns=["ID", "Nombre", "Placa", "Telefono"])

if 'db_tarifario' not in st.session_state:
    st.session_state.db_tarifario = pd.DataFrame(columns=["Cliente", "Producto", "Cobro_Cli", "Pago_Mens"])

if 'db_despacho' not in st.session_state:
    st.session_state.db_despacho = pd.DataFrame(columns=["Fecha", "Guia", "Cliente", "Producto", "Mensajero", "Estado"])

# --- BARRA LATERAL ---
with st.sidebar:
    st.title("📦 ENMILLA OPS")
    st.markdown("---")
    rol = st.radio("Acceso", ["Operativo", "Administrador"])
    st.markdown("---")
    
    if rol == "Administrador":
        password = st.text_input("Clave de Admin", type="password")
        menu = st.selectbox("Maestros Admin", ["Clientes y Productos", "Liquidación Total", "Ver Mensajeros"])
    else:
        # El operario ahora tiene "Crear Mensajeros" disponible
        menu = st.selectbox("Operación Diaria", ["Despacho", "Crear Mensajero"])
    
    st.markdown("---")
    st.caption("Enlaces Soluciones Logística SAS")
    st.caption("NIT: 901.939.284-4")

# --- ENCABEZADO ---
st.markdown(f"""
    <div style="background-color:#003366;padding:15px;border-radius:10px;text-align:center;">
    <h
