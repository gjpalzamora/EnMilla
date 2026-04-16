import streamlit as st
import pandas as pd
import datetime
import random

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Enmilla Pro - Enlaces Logística", layout="wide")

# --- INICIALIZACIÓN DE BASES DE DATOS ---
for db in ['db_mensajeros', 'db_tarifario', 'db_inventario', 'db_despacho']:
    if db not in st.session_state:
        if db == 'db_inventario':
            st.session_state[db] = pd.DataFrame(columns=["Fecha_Ingreso", "Guia", "Nombre Destinatario", "Direcion Destino", "Telefono", "Cliente", "Producto", "Estado"])
        elif db == 'db_despacho':
            st.session_state[db] = pd.DataFrame(columns=["Fecha_Salida", "Guia", "Mensajero", "Nombre Destinatario", "Cliente", "Estado"])
        else:
            st.session_state[db] = pd.DataFrame()

# --- ESTILO CSS PERSONALIZADO ---
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .header-box { background-color: #003366; padding: 20px; border-radius: 10px; color: white; text-align: center; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- ENCABEZADO Y NAVEGACIÓN (ESTRUCTURA NUEVA) ---
st.markdown('<div class="header-box"><h1>📦 SISTEMA LOGÍSTICO ENMILLA PRO</h1><p>Enlaces Soluciones Logística SAS | NIT: 901.939.284-4</p></div>', unsafe_allow_html=True)

menu_principal = st.tabs(["🏠 Dashboard", "📥 Ingreso a Bodega", "🛵 Despacho (Cargue)", "⚙️ Configuración Admin"])

# --- TAB 1: DASHBOARD (MÉTRICAS) ---
with menu_principal[0]:
    st.subheader("Estado de la Operación - Hoy")
    c1, c2, c3 = st.columns(3)
    c1.metric("En Bodega", len(st.session_state.db_inventario))
    c2.metric("En Ruta", len(st.session_state.db_despacho))
    c3.metric("Entregados", "0") # Placeholder para futuro estado

# --- TAB 2: INGRESO A BODEGA (RECEPCIÓN) ---
with menu_principal[1]:
    st.header("📥 Recepción de Mercancía")
    
    if st.session_state.db_tarifario.empty:
        st.warning("⚠️ Configure Clientes en la pestaña de Configuración primero.")
    else:
        col_a, col_b = st.columns(2)
        cliente_sel = col_a.selectbox("Cliente Remitente", st.session_state.db_tarifario["Cliente"].unique(), key="ing_cli")
        prods = st.session_state.db_tarifario[st.session_state.db_tarifario["Cliente"] == cliente_sel]["Producto"]
        producto_sel = col_b.selectbox("Tipo de Producto", prods, key="ing_prod")
        
        tipo_op = st.radio("Método de Ingreso", ["Cliente Externo (Usa Guía del Excel)", "Mensajería Propia (Generar Guía ENM)"], horizontal=True)
        
        archivo = st.file_uploader("Subir base de datos (Excel/CSV)", type=['xlsx', 'xls', 'csv'])
        
        if archivo and st.button("🚀 Cargar a Bodega"):
            try:
                df = pd.read_excel(archivo, engine='openpyxl') if archivo.name.endswith(('.xlsx', '.xls')) else pd.read_csv(archivo)
                df.columns = df.columns.str.strip()
                
                # Validación de columnas según tu archivo real
                cols_req = ["Nombre Destinatario", "Direcion Destino", "Telefono"]
                if all(c in df.columns for c in cols_req):
                    df['Fecha_Ingreso'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                    df['Cliente'] = cliente_sel
                    df['Producto'] = producto_sel
                    df['Estado'] = "En Bodega"
                    
                    if tipo_op == "Mensajería Propia (Generar Guía ENM)":
                        df['Guia'] = [f"ENM-{random.randint(100000, 999999)}" for _ in range(len(df))]
                    
                    st.session_state.db_inventario = pd.concat([st.session_state.db_inventario, df[["Fecha_Ingreso", "Guia", "Nombre Destinatario", "Direcion Destino", "Telefono", "Cliente", "Producto", "Estado"]]], ignore_index=True)
                    st.success(f"✅ Cargadas {len(df)} unidades exitosamente.")
                else:
                    st.error(f"❌ Columnas faltantes. El archivo debe tener: {cols_req}")
            except Exception as e:
                st.error(f"Error: {e}")

# --- TAB 3: DESPACHO (CARGUE A VEHÍCULO) ---
with menu_principal[2]:
    st.header("🛵 Despacho y Cargue de Vehículos")
    if st.session_state.db_inventario.empty:
        st.info("No hay paquetes disponibles en bodega para despacho.")
    else:
        col_m, col_p = st.columns(2)
        if not st.session_state.db_mensajeros.empty:
            m_sel = col_m.selectbox("Mensajero", st.session_state.db_mensajeros["Nombre"])
            # Campo de pistoleo continuo
            guia_scan = st.text_input("💥 PISTOLEE CÓDIGO DE GUÍA AQUÍ", key="scanner_input")
            
            if guia_scan:
                match = st.session_state.db_inventario[st.session_state.db_inventario["Guia"] == guia_scan]
                if not match.empty:
                    idx = match.index[0]
                    # Mover a despacho
                    n_d = pd.DataFrame([{
                        "Fecha_Salida": datetime.datetime.now().strftime("%H:%M"),
                        "Guia": guia_scan, "Mensajero": m_sel, "Nombre Destinatario": match.loc[idx, "Nombre Destinatario"],
                        "Cliente": match.loc[idx, "Cliente"], "Estado": "En Ruta"
                    }])
                    st.session_state.db_despacho = pd.concat([st.session_state.db_despacho, n_d], ignore_index=True)
                    st.session_state.db_inventario = st.session_state.db_inventario.drop(idx)
                    st.toast(f"✅ {guia_scan} asignada a {m_sel}")
                else:
                    st.error("Guía no encontrada en Bodega.")
        else:
            st.warning("Cree mensajeros en la pestaña de Configuración.")

# --- TAB 4: CONFIGURACIÓN (ADMIN) ---
with menu_principal[3]:
    st.header("⚙️ Configuración del Sistema")
    pw = st.text_input("Clave de Administrador", type="password")
    if pw == "1234":
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Maestro Clientes")
            with st.form("f_cli", clear_on_submit=True):
                nc = st.text_input("Nombre Cliente")
                np = st.text_input("Producto")
                if st.form_submit_button("Guardar"):
                    st.session_state.db_tarifario = pd.concat([st.session_state.db_tarifario, pd.DataFrame([{"Cliente": nc, "Producto": np}])], ignore_index=True)
        with c2:
            st.subheader("Maestro Mensajeros")
            with st.form("f_men", clear_on_submit=True):
                nm = st.text_input("Nombre")
                pl = st.text_input("Placa")
                if st.form_submit_button("Vincular"):
                    st.session_state.db_mensajeros = pd.concat([st.session_state.db_mensajeros, pd.DataFrame([{"Nombre": nm, "Placa": pl}])], ignore_index=True)

# --- VISUALIZACIÓN DE TABLA DE CONTROL (PIE DE PÁGINA) ---
st.markdown("---")
st.subheader("📋 Inventario Actual en Bodega")
st.dataframe(st.session_state.db_inventario, use_container_width=True)
