import streamlit as st
import pandas as pd
import datetime
import random

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Enmilla", layout="wide")

# --- MOTOR DE DATOS (PERSISTENCIA TOTAL) ---
def init_db(name, cols):
    if name not in st.session_state:
        st.session_state[name] = pd.DataFrame(columns=cols)

init_db('db_mensajeros', ["Nombre", "Placa"])
init_db('db_tarifario', ["Cliente", "Producto"])
init_db('db_inventario', ["Fecha_Ingreso", "Guia", "Nombre Destinatario", "Direcion Destino", "Telefono", "Cliente", "Producto", "Estado"])
init_db('db_despacho', ["Fecha_Salida", "Guia", "Mensajero", "Nombre Destinatario", "Cliente", "Estado"])

# --- INTERFAZ CORPORATIVA ---
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #e9ecef; border-radius: 5px 5px 0 0; padding: 10px 20px;
    }
    .stTabs [aria-selected="true"] { background-color: #003366 !important; color: white !important; }
    </style>
    """, unsafe_allow_html=True)

# Encabezado con Identidad Corporativa
col_logo, col_text = st.columns([1, 4])
with col_logo:
    # Aquí cargamos el logo que subiste
    st.image("log fondo blancojpg.jpg", width=150)
with col_text:
    st.markdown(f"""
        <div style="text-align: left;">
            <h1 style="margin:0; color:#003366;">ENMILLA</h1>
            <p style="margin:0; font-weight:bold;">Enlaces Soluciones Logísticas SAS</p>
            <p style="margin:0;">NIT: 901.939.284-4</p>
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")

tabs = st.tabs(["📊 Tablero de Control", "📥 Ingreso a Bodega", "🛵 Cargue y Despacho", "⚙️ Administración"])

# --- 1. TABLERO DE CONTROL ---
with tabs[0]:
    c1, c2, c3 = st.columns(3)
    c1.metric("Paquetes en Bodega", len(st.session_state.db_inventario))
    c2.metric("En Ruta de Entrega", len(st.session_state.db_despacho))
    c3.metric("Total Movimientos", len(st.session_state.db_inventario) + len(st.session_state.db_despacho))
    
    st.subheader("📋 Inventario Disponible")
    st.dataframe(st.session_state.db_inventario, use_container_width=True)

# --- 2. INGRESO A BODEGA ---
with tabs[1]:
    if st.session_state.db_tarifario.empty:
        st.warning("⚠️ Acceda a Administración para configurar Clientes y Productos.")
    else:
        with st.expander("Configuración de Carga", expanded=True):
            col1, col2 = st.columns(2)
            cli_sel = col1.selectbox("Seleccione Cliente", st.session_state.db_tarifario["Cliente"].unique())
            prod_sel = col2.selectbox("Seleccione Producto", st.session_state.db_tarifario[st.session_state.db_tarifario["Cliente"] == cli_sel]["Producto"])
            
            tipo_ingreso = st.radio("Método", ["Masivo (Excel/CSV)", "Manual (Unitario)"], horizontal=True)

        if tipo_ingreso == "Masivo (Excel/CSV)":
            gen_interna = st.checkbox("Generar guías automáticas de Enmilla")
            archivo = st.file_uploader("Subir base de datos del cliente", type=['xlsx', 'csv'])
            if archivo and st.button("🚀 Ejecutar Ingreso Masivo"):
                try:
                    df = pd.read_excel(archivo) if archivo.name.endswith('.xlsx') else pd.read_csv(archivo)
                    df.columns = df.columns.str.strip()
                    
                    df['Fecha_Ingreso'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                    df['Cliente'], df['Producto'], df['Estado'] = cli_sel, prod_sel, "En Bodega"
                    
                    if gen_interna:
                        df['Guia'] = [f"ENM-{random.randint(100000, 999999)}" for _ in range(len(df))]
                    
                    # Evitar duplicados por Guía
                    st.session_state.db_inventario = pd.concat([st.session_state.db_inventario, df], ignore_index=True).drop_duplicates(subset=['Guia'], keep='last')
                    st.success(f"Se han ingresado {len(df)} registros a la bodega.")
                except Exception as e:
                    st.error(f"Error en el archivo: {e}")
        else:
            with st.form("registro_manual"):
                g_man = st.text_input("Guía del paquete (Vacio para generar interna)")
                d_man = st.text_input("Nombre del Destinatario")
                dir_man = st.text_input("Dirección de Destino")
                tel_man = st.text_input("Teléfono")
                if st.form_submit_button("Registrar en Bodega"):
                    final_guia = g_man if g_man else f"ENM-{random.randint(100000, 999999)}"
                    n_reg = pd.DataFrame([{"Fecha_Ingreso": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "Guia": final_guia, "Nombre Destinatario": d_man, "Direcion Destino": dir_man, "Telefono": tel_man, "Cliente": cli_sel, "Producto": prod_sel, "Estado": "En Bodega"}])
                    st.session_state.db_inventario = pd.concat([st.session_state.db_inventario, n_reg], ignore_index=True)
                    st.success(f"Guía {final_guia} ingresada.")

# --- 3. CARGUE Y DESPACHO (FLUJO PISTOLA) ---
with tabs[2]:
    st.subheader("🛵 Despacho a Mensajero (Pistoleo)")
    if st.session_state.db_mensajeros.empty:
        st.info("Debe registrar mensajeros en el panel de Administración.")
    elif st.session_state.db_inventario.empty:
        st.info("No hay paquetes en bodega para despachar.")
    else:
        col_m, col_v = st.columns(2)
        m_resp = col_m.selectbox("Mensajero Responsable", st.session_state.db_mensajeros["Nombre"])
        
        # Foco para escaneo continuo
        scan_input = st.text_input("💥 ESCANEE GUÍA PARA CARGUE", key="pistola")
        
        if scan_input:
            match = st.session_state.db_inventario[st.session_state.db_inventario["Guia"] == scan_input]
            if not match.empty:
                idx = match.index[0]
                # Registrar Salida
                n_salida = pd.DataFrame([{
                    "Fecha_Salida": datetime.datetime.now().strftime("%H:%M"),
                    "Guia": scan_input, "Mensajero": m_resp, 
                    "Nombre Destinatario": match.loc[idx, "Nombre Destinatario"], 
                    "Cliente": match.loc[idx, "Cliente"], "Estado": "En Ruta"
                }])
                st.session_state.db_despacho = pd.concat([st.session_state.db_despacho, n_salida], ignore_index=True)
                # Remover de inventario
                st.session_state.db_inventario = st.session_state.db_inventario.drop(idx)
                st.toast(f"✅ Guía {scan_input} cargada a vehículo.")
                # Auto-limpieza del input para el siguiente escaneo
                st.rerun()
            else:
                st.error("❌ LA GUÍA NO EXISTE EN BODEGA. Verifique el ingreso previo.")

# --- 4. ADMINISTRACIÓN ---
with tabs[3]:
    st.header("⚙️ Panel Administrativo")
    if st.text_input("Ingrese Clave de Acceso", type="password") == "1234":
        c_adm1, c_adm2 = st.columns(2)
        with c_adm1:
            st.write("### Gestión de Clientes")
            with st.form("admin_cli"):
                nc = st.text_input("Nombre de Empresa Cliente")
                pc = st.text_input("Nombre del Producto/Servicio")
                if st.form_submit_button("Crear Cliente"):
                    nuevo_cli = pd.DataFrame([{"Cliente": nc, "Producto": pc}])
                    st.session_state.db_tarifario = pd.concat([st.session_state.db_tarifario, nuevo_cli], ignore_index=True)
        with c_adm2:
            st.write("### Gestión de Mensajeros")
            with st.form("admin_men"):
                nm = st.text_input("Nombre del Mensajero")
                pm = st.text_input("Placa del Vehículo")
                if st.form_submit_button("Registrar Mensajero"):
                    nuevo_men = pd.DataFrame([{"Nombre": nm, "Placa": pm}])
                    st.session_state.db_mensajeros = pd.concat([st.session_state.db_mensajeros, nuevo_men], ignore_index=True)

# --- REPORTE DE SALIDAS (FOOTER) ---
st.markdown("---")
st.subheader("🚚 Registro de Despachos (Ruta)")
st.dataframe(st.session_state.db_despacho, use_container_width=True)
