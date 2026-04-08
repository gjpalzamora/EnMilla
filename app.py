import streamlit as st
import pandas as pd
import datetime

# --- 1. CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Enmilla Pro - Enlaces Logística", layout="wide")

# --- 2. BASES DE DATOS EN MEMORIA ---
# (Nota: Se reinician si se actualiza la app hasta que conectemos Google Sheets)
if 'db_mensajeros' not in st.session_state:
    st.session_state.db_mensajeros = pd.DataFrame(columns=["ID", "Nombre", "Placa", "Telefono"])

if 'db_clientes' not in st.session_state:
    st.session_state.db_clientes = pd.DataFrame(columns=["NIT", "Nombre", "Cobro_Cli", "Pago_Mens"])

if 'db_despacho' not in st.session_state:
    st.session_state.db_despacho = pd.DataFrame(columns=["Fecha", "Guia", "Mensajero", "Cliente", "Estado"])

# --- 3. BARRA LATERAL (NAVEGACIÓN) ---
with st.sidebar:
    st.title("📦 ENMILLA OPS")
    st.markdown("---")
    rol = st.radio("Nivel de Acceso", ["Operativo", "Administrador (Privado)"])
    st.markdown("---")
    
    if rol == "Administrador (Privado)":
        password = st.text_input("Contraseña de Admin", type="password")
        menu = st.selectbox("Gestión de Maestros", ["Dashboard Financiero", "Registro de Mensajeros", "Registro de Clientes"])
    else:
        menu = st.selectbox("Operación Diaria", ["Despacho a Mensajero", "Estado de Entregas"])
    
    st.markdown("---")
    st.caption("Enlaces Soluciones Logística SAS")
    st.caption("NIT: 901.939.284-4")

# --- 4. ENCABEZADO PRINCIPAL ---
st.markdown(f"""
    <div style="background-color:#003366;padding:15px;border-radius:10px">
    <h1 style="color:white;text-align:center;margin:0;">ENMILLA: Gestión de Distribución</h1>
    </div><br>
    """, unsafe_allow_html=True)

# --- 5. LÓGICA DE MÓDULOS ---

# A. REGISTRO DE MENSAJEROS (ADMIN)
if rol == "Administrador (Privado)" and password == "1234": # Cambia '1234' por tu clave
    if menu == "Registro de Mensajeros":
        st.header("👤 Registro de Mensajeros")
        with st.form("form_mensajeros", clear_on_submit=True):
            col1, col2 = st.columns(2)
            nom = col1.text_input("
