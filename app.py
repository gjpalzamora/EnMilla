import streamlit as st
import pandas as pd
import time

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Enmilla - Administración Logística", layout="wide")

# --- INICIALIZACIÓN DE BASES DE DATOS (En memoria por ahora) ---
if 'mensajeros' not in st.session_state:
    st.session_state.mensajeros = pd.DataFrame(columns=["Nombre", "Vehículo", "Teléfono"])
if 'clientes' not in st.session_state:
    st.session_state.clientes = pd.DataFrame(columns=["Nombre/Empresa", "NIT", "Dirección"])
if 'servicios' not in st.session_state:
    st.session_state.servicios = pd.DataFrame(columns=["Servicio", "Cobro_Cliente", "Pago_Mensajero"])
if 'operaciones' not in st.session_state:
    st.session_state.operaciones = pd.DataFrame(columns=["Guía", "Mensajero", "Cliente", "Valor_Cobrado", "Valor_Pagado", "Fecha"])

# --- SEGURIDAD: CONTROL DE ACCESO ---
st.sidebar.title("🔐 Acceso al Sistema")
rol = st.sidebar.radio("Selecciona tu Perfil", ["Operativo", "Administrador"])

password = ""
if rol == "Administrador":
    password = st.sidebar.text_input("Contraseña de Admin", type="password")

# --- MENÚ DE NAVEGACIÓN ---
st.sidebar.markdown("---")
if rol == "Administrador" and password == "1234": # Cambia '1234' por tu clave
    menu = st.sidebar.selectbox("Gestión Administrativa", ["Dashboard General", "Crear Mensajeros", "Crear Clientes/Servicios", "Liquidación de Mensajeros"])
else:
    menu = st.sidebar.selectbox("Módulo Operativo", ["Ingreso de Guías", "Estado de Entregas"])
    if rol == "Administrador" and password != "":
        st.sidebar.error("Contraseña Incorrecta")

# --- ENCABEZADO ---
st.markdown(f"""
    <div style="background-color:#003366;padding:15px;border-radius:10px">
    <h1 style="color:white;text-align:center;margin:0;">ENMILLA - Enlaces Soluciones Logística</h1>
    <p style="color:white;text-align:center;margin:5px;">Gestión de Mensajería y Liquidación Profesional</p>
    </div><br>
    """, unsafe_allow_html=True)

# --- LÓGICA DE MÓDULOS ADMINISTRATIVOS ---
if rol == "Administrador" and password == "1234":
    
    if menu == "Crear Mensajeros":
        st.header("👤 Registro de Nuevos Mensajeros")
        with st.form("crear_mensajero"):
            nombre = st.text_input("Nombre Completo")
            vehiculo = st.text_input("Placa / Vehículo")
            tel = st.text_input("Teléfono")
            if st.form_submit_button("Guardar Mensajero"):
                nuevo = pd.DataFrame([{"Nombre": nombre, "Vehículo": vehiculo, "Teléfono": tel}])
                st.session_state.mensajeros = pd.concat([st.session_state.mensajeros, nuevo], ignore_index=True)
                st.success(f"Mensajero {nombre} registrado.")

    elif menu == "Liquidación de Mensajeros":
        st.header("💰 Panel de Liquidación y Rentabilidad")
        st.info("Solo tú puedes ver los valores de cobro vs. pago.")
        # Aquí se mostrará el resumen de lo que se le debe a cada uno y la ganancia de la empresa
        st.dataframe(st.session_state.operaciones)

# --- LÓGICA DE MÓDULOS OPERATIVOS ---
else:
    if menu == "Ingreso de Guías":
        st.header("📦 Registro de Operación Diaria")
        # Aquí el equipo solo ingresa guías, sin ver precios de liquidación
        st.write("Módulo para el equipo de despacho.")

st.sidebar.caption("Enlaces Soluciones Logística SAS | NIT: 901.939.284-4")
