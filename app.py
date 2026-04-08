import streamlit as st
import pandas as pd
import datetime

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Enmilla Pro - Enlaces Logística", layout="wide")

# --- BASES DE DATOS EN MEMORIA ---
if 'db_mensajeros' not in st.session_state:
    st.session_state.db_mensajeros = pd.DataFrame(columns=["ID", "Nombre", "Placa", "Telefono"])
if 'db_clientes' not in st.session_state:
    st.session_state.db_clientes = pd.DataFrame(columns=["NIT", "Nombre", "Cobro_Cli", "Pago_Mens"])
if 'db_despacho' not in st.session_state:
    st.session_state.db_despacho = pd.DataFrame(columns=["Fecha", "Guia", "Mensajero", "Cliente", "Estado"])

# --- BARRA LATERAL ---
with st.sidebar:
    st.title("📦 ENMILLA OPS")
    rol = st.radio("Nivel de Acceso", ["Operativo", "Administrador"])
    st.markdown("---")
    
    if rol == "Administrador":
        password = st.text_input("Contraseña", type="password")
        menu = st.selectbox("Menú Admin", ["Registro de Mensajeros", "Registro de Clientes", "Dashboard"])
    else:
        menu = st.selectbox("Menú Operativo", ["Despacho a Mensajero"])
    
    st.caption("Enlaces Soluciones Logística SAS")

# --- ENCABEZADO ---
st.markdown(f"""
    <div style="background-color:#003366;padding:15px;border-radius:10px;text-align:center;">
    <h1 style="color:white;margin:0;">SISTEMA LOGÍSTICO ENMILLA</h1>
    </div><br>
    """, unsafe_allow_html=True)

# --- LÓGICA DE MÓDULOS ---

# 1. REGISTRO DE MENSAJEROS (ADMIN)
if rol == "Administrador" and password == "1234":
    if menu == "Registro de Mensajeros":
        st.header("👤 Registro de Mensajeros")
        with st.form("f_mensajeros", clear_on_submit=True):
            nom = st.text_input("Nombre Completo")
            ced = st.text_input("Cédula")
            pla = st.text_input("Placa")
            tel = st.text_input("Teléfono")
            if st.form_submit_button("Guardar"):
                if nom and ced:
                    n_m = pd.DataFrame([{"ID": ced, "Nombre": nom, "Placa": pla, "Telefono": tel}])
                    st.session_state.db_mensajeros = pd.concat([st.session_state.db_mensajeros, n_m], ignore_index=True)
                    st.success(f"Registrado: {nom}")

    # 2. REGISTRO DE CLIENTES (ADMIN)
    elif menu == "Registro de Clientes":
        st.header("🏢 Registro de Clientes y Tarifas")
        with st.form("f_clientes", clear_on_submit=True):
            n_cli = st.text_input("Nombre del Cliente")
            v_cobro = st.number_input("Cobro al Cliente ($)", min_value=0)
            v_pago = st.number_input("Pago al Mensajero ($)", min_value=0)
            if st.form_submit_button("Registrar"):
                n_c = pd.DataFrame([{"NIT": "S/N", "Nombre": n_cli, "Cobro_Cli": v_cobro, "Pago_Mens": v_pago}])
                st.session_state.db_clientes = pd.concat([st.session_state.db_clientes, n_c], ignore_index=True)
                st.success(f"Cliente {n_cli} configurado.")

# 3. DESPACHO (OPERATIVO)
elif rol == "Operativo":
    if menu == "Despacho a Mensajero":
        st.header("🛵 Despacho de Mercancía")
        if st.session_state.db_mensajeros.empty or st.session_state.db_clientes.empty:
            st.warning("El administrador debe cargar mensajeros y clientes primero.")
        else:
            with st.form("f_despacho", clear_on_submit=True):
                guia = st.text_input("Número de Guía")
                m_sel = st.selectbox("Mensajero", st.session_state.db_mensajeros["Nombre"])
                c_sel = st.selectbox("Cliente", st.session_state.db_clientes["Nombre"])
                if st.form_submit_button("Despachar"):
                    f = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                    n_d = pd.DataFrame([{"Fecha": f, "Guia": guia, "Mensajero": m_sel, "Cliente": c_sel, "Estado": "En Ruta"}])
                    st.session_state.db_despacho = pd.concat([st.session_state.db_despacho, n_d], ignore_index=True)
                    st.success(f"Guía {guia} en ruta con {m_sel}")

# --- TABLA DE RESULTADOS ---
st.markdown("---")
st.subheader("📋 Últimos Despachos")
st.dataframe(st.session_state.db_despacho.tail(10), use_container_width=True)
