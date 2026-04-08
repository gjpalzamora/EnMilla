import streamlit as st
import pandas as pd
import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Enmilla Pro - Terminal de Despacho", layout="wide")

# --- BASES DE DATOS EN MEMORIA (Simulación de Inventario) ---
if 'db_mensajeros' not in st.session_state:
    st.session_state.db_mens_df = pd.DataFrame(columns=["Nombre", "Placa", "ID"])
if 'db_tarifario' not in st.session_state:
    st.session_state.db_tarifario = pd.DataFrame(columns=["Cliente", "Producto", "Cobro", "Pago"])
if 'db_despacho' not in st.session_state:
    st.session_state.db_despacho = pd.DataFrame(columns=["Fecha", "Guia", "Mensajero", "Cliente", "Producto", "Estado"])

# --- BARRA LATERAL ---
with st.sidebar:
    st.title("📦 ENMILLA OPS")
    rol = st.radio("Acceso", ["Operativo", "Administrador"])
    st.markdown("---")
    if rol == "Administrador":
        pw = st.text_input("Clave", type="password")
        menu = st.selectbox("Maestros", ["Configurar Clientes", "Ver Liquidación"])
    else:
        menu = st.selectbox("Operación", ["Despacho (Modo Pistola)", "Crear Mensajero"])
    
    st.caption("Enlaces Soluciones Logística SAS")

# --- HEADER PROFESIONAL ---
st.markdown("""
    <div style="background-color:#003366;padding:10px;border-radius:5px;text-align:center;">
        <h2 style="color:white;margin:0;">TERMINAL DE CARGUE Y DESPACHO</h2>
    </div>
    """, unsafe_allow_html=True)

# --- MÓDULO: CREAR MENSAJERO (OPERATIVO) ---
if menu == "Crear Mensajero" and rol == "Operativo":
    st.subheader("👤 Registro Rápido de Mensajeros")
    with st.form("crear_m", clear_on_submit=True):
        col1, col2 = st.columns(2)
        n = col1.text_input("Nombre del Mensajero")
        p = col2.text_input("Placa")
        if st.form_submit_button("Registrar"):
            if n:
                nuevo = pd.DataFrame([{"Nombre": n, "Placa": p, "ID": "N/A"}])
                st.session_state.db_mens_df = pd.concat([st.session_state.db_mens_df, nuevo], ignore_index=True)
                st.success(f"Mensajero {n} listo para ruta.")

# --- MÓDULO: DESPACHO MODO PISTOLA (OPERATIVO) ---
elif menu == "Despacho (Modo Pistola)" and rol == "Operativo":
    if st.session_state.db_mens_df.empty or st.session_state.db_tarifario.empty:
        st.warning("⚠️ El Administrador debe configurar Clientes y registrar Mensajeros primero.")
    else:
        st.subheader("🛵 Cargue de Guías a Mensajero")
        
        # Selección Fija (Se queda estática para pistolear rápido)
        c1, c2, c3 = st.columns(3)
        m_sel = c1.selectbox("Mensajero que carga", st.session_state.db_mens_df["Nombre"])
        cli_sel = c2.selectbox("Cliente Origen", st.session_state.db_tarifario["Cliente"].unique())
        prods = st.session_state.db_tarifario[st.session_state.db_tarifario["Cliente"] == cli_sel]["Producto"]
        p_sel = c3.selectbox("Producto/Servicio", prods)

        st.markdown("---")
        # Campo de entrada para la pistola (se limpia tras cada enter)
        guia_input = st.text_input("💥 ESCANEE GUÍA AQUÍ (Pistolee)", key="pistola", help="Pistolee el código de barras y presione Enter")

        if guia_input:
            # Lógica de carga al inventario del mensajero
            fecha = datetime.datetime.now().strftime("%H:%M:%S")
            n_despacho = pd.DataFrame([{
                "Fecha": fecha,
                "Guia": guia_input,
                "Mensajero": m_sel,
                "Cliente": cli_sel,
                "Producto": p_sel,
                "Estado": "Cargado en Vehículo"
            }])
            st.session_state.db_despacho = pd.concat([st.session_state.db_despacho, n_despacho], ignore_index=True)
            st.toast(f"✅ Guía {guia_input} cargada a {m_sel}", icon="📦")

# --- MÓDULO: ADMINISTRADOR ---
if rol == "Administrador" and pw == "1234":
    if menu == "Configurar Clientes":
        st.subheader("🏢 Tarifario Multiproducto")
        with st.form("f_tarifas", clear_on_submit=True):
            c_nom = st.text_input("Nombre Cliente")
            p_nom = st.text_input("Nombre Producto (Ej: Caja, Sobre)")
            v1 = st.number_input("Cobro Cliente", min_value=0)
            v2 = st.number_input("Pago Mensajero", min_value=0)
            if st.form_submit_button("Guardar Tarifa"):
                n_t = pd.DataFrame([{"Cliente": c_nom, "Producto": p_nom, "Cobro": v1, "Pago": v2}])
                st.session_state.db_tarifario = pd.concat([st.session_state.db_tarifario, n_t], ignore_index=True)
                st.success(f"Producto {p_nom} registrado para {c_nom}")

# --- MONITOR DE DESPACHO (INVENTARIO EN TIEMPO REAL) ---
st.markdown("---")
st.subheader("📋 Resumen de Despacho Actual")
if not st.session_state.db_despacho.empty:
    # Mostramos los últimos 10 escaneos para control visual del operario
    st.dataframe(st.session_state.db_despacho.tail(10), use_container_width=True)
    
    # Resumen rápido por mensajero
    resumen = st.session_state.db_despacho.groupby("Mensajero").size().reset_index(name='Guías Cargadas')
    st.table(resumen)
else:
    st.info("Esperando primer escaneo de guía...")
