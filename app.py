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
    <h1 style="color:white;margin:0;">SISTEMA LOGÍSTICO ENMILLA</h1>
    </div><br>
    """, unsafe_allow_html=True)

# --- MÓDULO: CREAR MENSAJERO (Disponible para ambos) ---
if menu == "Crear Mensajero" or (rol == "Administrador" and menu == "Ver Mensajeros" and password == "1234"):
    st.header("👤 Registro de Mensajeros")
    with st.form("f_m", clear_on_submit=True):
        col1, col2 = st.columns(2)
        n = col1.text_input("Nombre Completo")
        c = col2.text_input("Cédula")
        p = col1.text_input("Placa del Vehículo")
        t = col2.text_input("Teléfono")
        if st.form_submit_button("Guardar Mensajero"):
            if n and c:
                nuevo = pd.DataFrame([{"ID": c, "Nombre": n, "Placa": p, "Telefono": t}])
                st.session_state.db_mensajeros = pd.concat([st.session_state.db_mensajeros, nuevo], ignore_index=True)
                st.success(f"Mensajero {n} registrado con éxito.")
            else:
                st.error("Nombre y Cédula son obligatorios.")
    
    if rol == "Administrador":
        st.write("### Base de Datos de Mensajeros")
        st.dataframe(st.session_state.db_mensajeros, use_container_width=True)

# --- MÓDULOS EXCLUSIVOS DE ADMINISTRADOR ---
if rol == "Administrador" and password == "1234":
    if menu == "Clientes y Productos":
        st.header("🏢 Tarifario por Cliente y Producto")
        with st.form("f_c", clear_on_submit=True):
            cli = st.text_input("Nombre del Cliente")
            prod = st.text_input("Producto (Ej: Sobre, Caja, Express)")
            c1, c2 = st.columns(2)
            v_cobro = c1.number_input("Cobro al Cliente ($)", min_value=0, step=100)
            v_pago = c2.number_input("Pago al Mensajero ($)", min_value=0, step=100)
            if st.form_submit_button("Registrar Tarifa"):
                if cli and prod:
                    nuevo_p = pd.DataFrame([{"Cliente": cli, "Producto": prod, "Cobro_Cli": v_cobro, "Pago_Mens": v_pago}])
                    st.session_state.db_tarifario = pd.concat([st.session_state.db_tarifario, nuevo_p], ignore_index=True)
                    st.success(f"Tarifa guardada: {cli} - {prod}")

    elif menu == "Liquidación Total":
        st.header("💰 Control de Liquidación")
        st.dataframe(st.session_state.db_tarifario, use_container_width=True)

# --- MÓDULO: DESPACHO (OPERATIVO) ---
elif rol == "Operativo" and menu == "Despacho":
    st.header("🛵 Despacho de Mercancía")
    if st.session_state.db_tarifario.empty or st.session_state.db_mensajeros.empty:
        st.warning("⚠️ Acción requerida: El sistema necesita que existan Clientes, Productos y Mensajeros creados.")
    else:
        with st.form("f_d", clear_on_submit=True):
            guia = st.text_input("Número de Guía")
            
            # Selección dinámica de Cliente y Producto
            lista_clientes = st.session_state.db_tarifario["Cliente"].unique()
            c_sel = st.selectbox("Seleccione Cliente", lista_clientes)
            
            prods_filtrados = st.session_state.db_tarifario[st.session_state.db_tarifario["Cliente"] == c_sel]["Producto"]
            p_sel = st.selectbox("Seleccione Producto", prods_filtrados)
            
            m_sel = st.selectbox("Asignar Mensajero", st.session_state.db_mensajeros["Nombre"])
            
            if st.form_submit_button("Confirmar Salida"):
                if guia:
                    f_ahora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                    nuevo_d = pd.DataFrame([{"Fecha": f_ahora, "Guia": guia, "Cliente": c_sel, "Producto": p_sel, "Mensajero": m_sel, "Estado": "En Ruta"}])
                    st.session_state.db_despacho = pd.concat([st.session_state.db_despacho, nuevo_d], ignore_index=True)
                    st.success(f"Guía {guia} despachada con {m_sel}.")

# --- TABLA DE REGISTROS (VISIBILIDAD GENERAL) ---
st.markdown("---")
st.subheader("📋 Últimos Movimientos en Bodega")
st.dataframe(st.session_state.db_despacho.tail(15), use_container_width=True)

# Manejo de error de clave
if rol == "Administrador" and password != "" and password != "1234":
    st.sidebar.error("Contraseña incorrecta")
