import streamlit as st
import pandas as pd
import datetime

# --- CONFIGURACIÓN DE INTERFAZ ---
st.set_page_config(page_title="Enmilla Pro - Gestión Logística", layout="wide")

# --- INICIALIZACIÓN DE BASES DE DATOS (Persistencia temporal) ---
if 'db_mensajeros' not in st.session_state:
    st.session_state.db_mensajeros = pd.DataFrame(columns=["ID", "Nombre", "Placa", "Telefono"])
if 'db_clientes' not in st.session_state:
    st.session_state.db_clientes = pd.DataFrame(columns=["NIT", "Nombre", "Tarifa_Cliente", "Tarifa_Mensajero"])
if 'db_despacho' not in st.session_state:
    st.session_state.db_despacho = pd.DataFrame(columns=["Fecha", "Guia", "Mensajero", "Cliente", "Estado"])

# --- BARRA LATERAL: NAVEGACIÓN ---
st.sidebar.title("📦 ENMILLA OPS")
rol = st.sidebar.radio("Nivel de Acceso", ["Operativo", "Administrador (Privado)"])

if rol == "Administrador (Privado)":
    menu = st.sidebar.selectbox("Gestión de Maestros", ["Dashboard Financiero", "Registro de Mensajeros", "Registro de Clientes"])
    password = st.sidebar.text_input("Clave de Seguridad", type="password")
else:
    menu = st.sidebar.selectbox("Operación Diaria", ["Despacho a Mensajero", "Ingreso de Bodega"])

# --- CONTENIDO DE LOS MÓDULOS ---

# MÓDULO 1: CREAR MENSAJERO (Solo Admin)
if menu == "Registro de Mensajeros" and rol == "Administrador (Privado)":
    st.header("👤 Registro de Mensajeros (Recurso Humano)")
    with st.form("form_mensajero", clear_on_submit=True):
        col1, col2 = st.columns(2)
        nom = col1.text_input("Nombre Completo")
        ced = col2.text_input("Cédula/ID")
        pla = col1.text_input("Placa del Vehículo")
        tel = col2.text_input("Teléfono de Contacto")
        
        if st.form_submit_button("Guardar Mensajero"):
            nuevo_m = pd.DataFrame([{"ID": ced, "Nombre": nom, "Placa": pla, "Telefono": tel}])
            st.session_state.db_mensajeros = pd.concat([st.session_state.db_mensajeros, nuevo_m], ignore_index=True)
            st.success(f"Mensajero {nom} vinculado exitosamente.")

# MÓDULO 2: CREAR CLIENTE (Solo Admin)
elif menu == "Registro de Clientes" and rol == "Administrador (Privado)":
    st.header("🏢 Registro de Clientes y Tarifas")
    st.info("Define aquí los valores de liquidación. Estos NO son visibles para los mensajeros.")
    with st.form("form_cliente", clear_on_submit=True):
        c1, c2 = st.columns(2)
        n_cli = c1.text_input("Nombre de la Empresa / Aliado")
        nit_cli = c2.text_input("NIT")
        v_cobro = c1.number_input("Valor a Cobrar al Cliente ($)", min_value=0)
        v_pago = c2.number_input("Valor a Pagar al Mensajero ($)", min_value=0)
        
        if st.form_submit_button("Registrar Cliente"):
            nuevo_c = pd.DataFrame([{"NIT": nit_cli, "Nombre": n_cli, "Tarifa_Cliente": v_cobro, "Tarifa_Mensajero": v_pago}])
            st.session_state.db_clientes = pd.concat([st.session_state.db_clientes, nuevo_c], ignore_index=True)
            st.success(f"Tarifario configurado para {n_cli}.")

# MÓDULO 3: DESPACHO A MENSAJERO (Operativo)
elif menu == "Despacho a Mensajero":
    st.header("🛵 Despacho de Mercancía")
    if st.session_state.db_mensajeros.empty or st.session_state.db_clientes.empty:
        st.warning("⚠️ Primero debes registrar Clientes y Mensajeros en el módulo de Administrador.")
    else:
        with st.form("form_despacho"):
            guia = st.text_input("Número de Guía (Escanea aquí)")
            # Listas desplegables alimentadas por los módulos anteriores
            mensajero_sel = st.selectbox("Seleccionar Mensajero", st.session_state.db_mensajeros["Nombre"])
            cliente_sel = st.selectbox("Cliente Remitente", st.session_state.db_clientes["Nombre"])
            
            if st.form_submit_button("Confirmar Salida a Ruta"):
                fecha_actual = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                despacho = pd.DataFrame([{
                    "Fecha": fecha_actual, "Guia": guia, 
                    "Mensajero": mensajero_sel, "Cliente": cliente_sel, "Estado": "En Ruta"
                }])
                st.session_state.db_despacho = pd.concat([st.session_state.db_despacho, despacho], ignore_index=True)
                st.balloons()
                st.success(f"Guía {guia} entregada a {mensajero_sel}.")

# Vista de tablas para control
if not st.session_state.db_despacho.empty:
    st.subheader("📋 Registro Actual
