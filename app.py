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
    .stButton>button { background-color: #f37021; color: white; width: 100%; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- INICIALIZACIÓN DE BASES DE DATOS (STATE) ---
if 'db' not in st.session_state:
    st.session_state.db = {
        'clientes': pd.DataFrame(columns=["NIT", "Nombre", "Contacto", "Sede"]),
        'tarifario': pd.DataFrame(columns=["Cliente", "Producto", "Tarifa_Venta", "Tarifa_Pago"]),
        'mensajeros': pd.DataFrame(columns=["Nombre", "Vehiculo", "Placa", "Zona"]),
        'inventario': pd.DataFrame(columns=[
            "Guia", "Fecha_In", "Cliente", "Producto", "Contenido", "Destinatario", 
            "Direccion", "Ciudad", "Cobro_COD", "Telefono", "Valor Declarado", "Peso KG", "Estado", "Mensajero"
        ]),
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
        "5. App Móvil (Operación)",
        "6. Liquidación y Caja",
        "7. Logística Inversa",
        "8. Portal de Autogestión"
    ])
    st.markdown("---")
    st.caption("Enlaces Tech v2.8")

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
                new_c = {"NIT": nit, "Nombre": nom}
                st.session_state.db['clientes'] = pd.concat([st.session_state.db['clientes'], pd.DataFrame([new_c])], ignore_index=True)
                st.success("Cliente registrado.")
        st.dataframe(st.session_state.db['clientes'])

    with tab2:
        with st.form("f_pre"):
            col1, col2 = st.columns(2)
            cli_sel = col1.selectbox("Cliente", st.session_state.db['clientes']['Nombre'].unique())
            prod = col2.selectbox("Categoría", ["Sobre", "Paquete", "Carga"])
            v_venta = col1.number_input("Tarifa Venta (Lo que cobras)", min_value=0)
            v_pago = col2.number_input("Tarifa Pago (Lo que pagas al mensajero)", min_value=0)
            if st.form_submit_button("Guardar Precio"):
                new_t = {"Cliente": cli_sel, "Producto": prod, "Tarifa_Venta": v_venta, "Tarifa_Pago": v_pago}
                st.session_state.db['tarifario'] = pd.concat([st.session_state.db['tarifario'], pd.DataFrame([new_t])], ignore_index=True)
                st.success("Tarifa guardada.")
        st.dataframe(st.session_state.db['tarifario'])

    with tab3:
        with st.form("f_mens"):
            n_mens = st.text_input("Nombre Conductor")
            plac = st.text_input("Placa Vehículo")
            if st.form_submit_button("Registrar Mensajero"):
                st.session_state.db['mensajeros'] = pd.concat([st.session_state.db['mensajeros'], pd.DataFrame([{"Nombre": n_mens, "Placa": plac}])], ignore_index=True)
        st.dataframe(st.session_state.db['mensajeros'])

# --- 2. MÓDULO DE ADMISIÓN E INGESTA ---
elif menu == "2. Admisión e Ingesta":
    st.header("📂 Admisión e Ingesta de Datos")
    st.subheader("2.1 Importador Masivo")
    st.info("Utilice el Módulo 3.2 para transmitir y conciliar los datos con la bodega.")
    st.subheader("2.3 Motor de Identidad (Etiquetado)")
    if st.button("Generar Etiquetas Enlaces con QR"):
        st.info("Función de etiquetado activada.")

# --- 3. MÓDULO DE RECEPCIÓN Y BODEGA (WMS) ---
elif menu == "3. Recepción y Bodega (WMS)":
    st.header("📦 Gestión de Bodega (WMS)")
    
    st.subheader("3.1 Ingreso a Ciegas (Inbound)")
    guia_scan = st.text_input("ESCÁNER: Lea el código de barras física", key="scanner")
    if guia_scan:
        if guia_scan not in st.session_state.db['inventario']['Guia'].values:
            nuevo = {"Guia": guia_scan, "Fecha_In": datetime.now(), "Estado": "En Bodega (Físico)"}
            st.session_state.db['inventario'] = pd.concat([st.session_state.db['inventario'], pd.DataFrame([nuevo])], ignore_index=True)
            st.success(f"Guía {guia_scan} registrada físicamente.")
    
    st.markdown("---")
    st.subheader("3.2 Conciliador de Carga")
    up = st.file_uploader("1. Subir Excel del Cliente", type=["xlsx", "csv"])
    
    if up is not None:
        if st.button("🚀 TRANSMITIR Y CONCILIAR DATOS"):
            df_c = pd.read_excel(up) if up.name.endswith('xlsx') else pd.read_csv(up)
            df_c.columns = [c.strip() for c in df_c.columns]
            
            count = 0
            for _, row in df_c.iterrows():
                g = str(row['Guia'])
                if g in st.session_state.db['inventario']['Guia'].values:
                    idx = st.session_state.db['inventario'][st.session_state.db['inventario']['Guia'] == g].index
                    # Mapeo según tu imagen de estructura
                    st.session_state.db['inventario'].at[idx, 'Cliente'] = row.get('Cliente', '')
                    st.session_state.db['inventario'].at[idx, 'Producto'] = row.get('Producto', '')
                    st.session_state.db['inventario'].at[idx, 'Destinatario'] = row.get('Destinatario', '')
                    st.session_state.db['inventario'].at[idx, 'Direccion'] = row.get('Direccion', '')
                    st.session_state.db['inventario'].at[idx, 'Ciudad'] = row.get('Ciudad', '')
                    st.session_state.db['inventario'].at[idx, 'Cobro_COD'] = row.get('Cobro_COD', 0)
                    st.session_state.db['inventario'].at[idx, 'Telefono'] = row.get('Telefono', '')
                    st.session_state.db['inventario'].at[idx, 'Contenido'] = row.get('Contenido', '')
                    st.session_state.db['inventario'].at[idx, 'Valor Declarado'] = row.get('Valor Declarado', 0)
                    st.session_state.db['inventario'].at[idx, 'Peso KG'] = row.get('Peso KG', 0)
                    st.session_state.db['inventario'].at[idx, 'Estado'] = "Listo para Despacho"
                    count += 1
            st.success(f"✅ ¡Transmisión Exitosa! {count} guías conciliadas.")

    st.write("### Inventario en Bodega Actual")
    st.dataframe(st.session_state.db['inventario'], use_container_width=True)

# --- 4. MÓDULO DE OPERACIONES Y DESPACHO ---
elif menu == "4. Operaciones y Despacho":
    st.header("🚚 Operaciones y Despacho")
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("4.1 Despacho")
        m_sel = st.selectbox("Seleccionar Mensajero", st.session_state.db['mensajeros']['Nombre'].unique())
        guia_desp = st.text_input("Escanear Guía para Despacho")
        if guia_desp:
            if guia_desp in st.session_state.db['inventario']['Guia'].values:
                idx = st.session_state.db['inventario'][st.session_state.db['inventario']['Guia'] == guia_desp].index
                st.session_state.db['inventario'].at[idx, 'Mensajero'] = m_sel
                st.session_state.db['inventario'].at[idx, 'Estado'] = "En Ruta"
                st.success(f"Asignada a {m_sel}")

    with col2:
        st.subheader("4.3 Torre de Control")
        st.dataframe(st.session_state.db['inventario'][['Guia', 'Estado', 'Mensajero']])

# --- 6. MÓDULO DE LIQUIDACIÓN Y CAJA ---
elif menu == "6. Liquidación y Caja":
    st.header("💰 Liquidación y Caja")
    df_liq = pd.merge(st.session_state.db['inventario'], st.session_state.db['tarifario'], on=["Cliente", "Producto"], how="left")
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("6.3 Facturación Clientes", f"${df_liq['Tarifa_Venta'].sum():,.0f}")
    c2.metric("6.2 Nómina Destajo", f"${df_liq['Tarifa_Pago'].sum():,.0f}")
    c3.metric("6.1 Recaudos COD", f"${df_liq['Cobro_COD'].sum():,.0f}")
    c4.metric("6.4 Margen Enlaces", f"${(df_liq['Tarifa_Venta'].sum() - df_liq['Tarifa_Pago'].sum()):,.0f}")
    
    st.dataframe(df_liq)

# --- 7. MÓDULO DE LOGÍSTICA INVERSA ---
elif menu == "7. Logística Inversa":
    st.header("🔄 Logística Inversa y Novedades")
    nov_guia = st.text_input("Escanear Guía para Re-ingreso por Novedad")
    if nov_guia:
        st.info("Registrando novedad de retorno...")

# --- 8. PORTAL DE AUTOGESTIÓN ---
elif menu == "8. Portal de Autogestión":
    st.header("🌐 Portal del Cliente")
    st.write("Módulo para seguimiento externo de clientes.")
