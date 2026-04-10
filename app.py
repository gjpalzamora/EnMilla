import streamlit as st
import pandas as pd
from datetime import datetime

# --- 0. CONFIGURACIÓN E IDENTIDAD CORPORATIVA ---
st.set_page_config(page_title="Enlaces - Soluciones Logísticas", layout="wide", page_icon="📦")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; border-left: 5px solid #f37021; box-shadow: 2px 2px 5px rgba(0,0,0,0.05); }
    div[data-testid="stSidebarNav"] { background-color: #006064; }
    h1, h2, h3 { color: #006064; }
    .stButton>button { background-color: #f37021; color: white; width: 100%; }
    .status-badge { padding: 5px 10px; border-radius: 15px; font-size: 12px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- INICIALIZACIÓN DE BASES DE DATOS (STATE) ---
if 'db' not in st.session_state:
    st.session_state.db = {
        'clientes': pd.DataFrame(columns=["NIT", "Nombre", "Contacto", "Sede"]),
        'tarifario': pd.DataFrame(columns=["Cliente", "Producto", "Tarifa_Venta", "Tarifa_Pago"]),
        'mensajeros': pd.DataFrame(columns=["Nombre", "Vehiculo", "Placa", "Zona"]),
        'inventario': pd.DataFrame(columns=["Guia", "Fecha_In", "Cliente", "Producto", "Destinatario", "Direccion", "Cobro_COD", "Estado", "Mensajero"]),
        'novedades': pd.DataFrame(columns=["Fecha", "Guia", "Motivo", "Estado_Retorno"])
    }

# --- BARRA LATERAL: ESTRUCTURA DE 8 MÓDULOS ---
with st.sidebar:
    st.image("https://imgur.com", use_container_width=True) # Logo Enlaces
    st.markdown("<h3 style='text-align: center; color: white;'>ENLACES LOGÍSTICA</h3>", unsafe_allow_html=True)
    st.markdown("---")
    menu = st.selectbox("MENÚ PRINCIPAL", [
        "1. Administración",
        "2. Admisión e Ingesta",
        "3. Recepción y Bodega (WMS)",
        "4. Operaciones y Despacho",
        "5. App Móvil (Simulación)",
        "6. Liquidación y Caja",
        "7. Logística Inversa",
        "8. Portal de Autogestión"
    ])
    st.markdown("---")
    st.caption("Enlaces Tech v2.0")

# --- 1. MÓDULO DE ADMINISTRACIÓN ---
if menu == "1. Administración":
    st.header("⚙️ Módulo de Administración")
    tab1, tab2, tab3 = st.tabs(["1.1 Clientes", "1.2 Productos y Precios", "1.4 Gestión Mensajeros"])
    
    with tab1:
        with st.form("f_cli"):
            c1, c2 = st.columns(2)
            nit = c1.text_input("NIT")
            nom = c2.text_input("Nombre Empresa")
            if st.form_submit_button("Registrar Cliente"):
                st.session_state.db['clientes'] = pd.concat([st.session_state.db['clientes'], pd.DataFrame([{"NIT": nit, "Nombre": nom}])], ignore_index=True)
        st.write("Clientes registrados:", st.session_state.db['clientes'])

    with tab2:
        with st.form("f_pre"):
            col1, col2 = st.columns(2)
            cli_sel = col1.selectbox("Cliente", st.session_state.db['clientes']['Nombre'].unique())
            prod = col2.selectbox("Categoría", ["Sobre", "Paquete", "Carga"])
            v_venta = col1.number_input("Tarifa Venta (Cobro)", min_value=0)
            v_pago = col2.number_input("Tarifa Pago (Destajo)", min_value=0)
            if st.form_submit_button("Guardar Precio"):
                st.session_state.db['tarifario'] = pd.concat([st.session_state.db['tarifario'], pd.DataFrame([{"Cliente": cli_sel, "Producto": prod, "Tarifa_Venta": v_venta, "Tarifa_Pago": v_pago}])], ignore_index=True)
        st.write("Matriz de precios:", st.session_state.db['tarifario'])

    with tab3:
        with st.form("f_mens"):
            n_mens = st.text_input("Nombre Conductor")
            plac = st.text_input("Placa Vehículo")
            if st.form_submit_button("Registrar Mensajero"):
                st.session_state.db['mensajeros'] = pd.concat([st.session_state.db['mensajeros'], pd.DataFrame([{"Nombre": n_mens, "Placa": plac}])], ignore_index=True)
        st.write("Flota activa:", st.session_state.db['mensajeros'])

# --- 2. MÓDULO DE ADMISIÓN E INGESTA ---
elif menu == "2. Admisión e Ingesta":
    st.header("📂 Admisión de Datos")
    st.subheader("2.1 Importador Masivo")
    up = st.file_uploader("Subir Excel del Cliente", type=["xlsx", "csv"])
    if up:
        st.success("Archivo cargado. Use el Módulo 3.2 para conciliar.")
    
    st.subheader("2.3 Motor de Identidad")
    if st.button("Generar Etiquetas Enlaces (QR)"):
        st.info("Función de impresión de etiquetas con logo y QR activada.")

# --- 3. MÓDULO DE RECEPCIÓN Y BODEGA (WMS) ---
elif menu == "3. Recepción y Bodega (WMS)":
    st.header("📦 Gestión de Bodega")
    st.subheader("3.1 Ingreso a Ciegas (Inbound)")
    guia_scan = st.text_input("ESCÁNER: Lea el código de barras")
    if guia_scan:
        if guia_scan not in st.session_state.db['inventario']['Guia'].values:
            nuevo = {"Guia": guia_scan, "Fecha_In": datetime.now(), "Estado": "En Bodega (Físico)", "Cliente": "PENDIENTE", "Destinatario": "PENDIENTE"}
            st.session_state.db['inventario'] = pd.concat([st.session_state.db['inventario'], pd.DataFrame([nuevo])], ignore_index=True)
            st.success(f"Guía {guia_scan} registrada físicamente.")
    
    st.subheader("3.2 Conciliador de Carga")
    if st.button("Cruzar Datos con Importación"):
        st.warning("Buscando coincidencias en base de datos...")

# --- 4. MÓDULO DE OPERACIONES Y DESPACHO ---
elif menu == "4. Operaciones y Despacho":
    st.header("🚚 Despacho y Control")
    col1, col2 = st.columns(2)
    with col1:
        m_sel = st.selectbox("4.1 Seleccionar Mensajero", st.session_state.db['mensajeros']['Nombre'].unique())
        guia_desp = st.text_input("Escanear Guía para Despacho")
    
    with col2:
        st.subheader("4.3 Torre de Control")
        st.write(st.session_state.db['inventario'][['Guia', 'Estado', 'Mensajero']])

# --- 6. MÓDULO DE LIQUIDACIÓN Y CAJA ---
elif menu == "6. Liquidación y Caja":
    st.header("💰 Liquidación Financiera")
    df_liq = pd.merge(st.session_state.db['inventario'], st.session_state.db['tarifario'], on=["Cliente", "Producto"], how="left")
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("6.3 Facturación Clientes", f"${df_liq['Tarifa_Venta'].sum():,.0f}")
    c2.metric("6.2 Nómina Destajo", f"${df_liq['Tarifa_Pago'].sum():,.0f}")
    c3.metric("6.1 Recaudos COD", f"${df_liq['Cobro_COD'].sum():,.0f}")
    c4.metric("6.4 Margen Bruto", f"${(df_liq['Tarifa_Venta'].sum() - df_liq['Tarifa_Pago'].sum()):,.0f}")
    
    st.dataframe(df_liq)

# --- 7. LOGÍSTICA INVERSA ---
elif menu == "7. Logística Inversa":
    st.header("🔄 Novedades y Devoluciones")
    st.subheader("7.1 Re-ingreso por Novedad")
    nov_guia = st.text_input("Escanear Guía Devuelta")
    motivo = st.selectbox("Motivo", ["Dirección Errada", "Cliente Ausente", "Rechazado"])
    if st.button("Registrar Devolución"):
        st.success(f"Guía {nov_guia} re-ingresada a bodega.")
