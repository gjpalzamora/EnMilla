import streamlit as st
import pandas as pd
import datetime
import random

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Enmilla", layout="wide", page_icon="📦")

# --- MOTOR DE DATOS (INICIALIZACIÓN CON COLUMNAS FIJAS) ---
def init_db():
    if 'db_mensajeros' not in st.session_state:
        st.session_state.db_mensajeros = pd.DataFrame(columns=["Nombre", "Placa"])
    if 'db_tarifario' not in st.session_state:
        st.session_state.db_tarifario = pd.DataFrame(columns=["Cliente", "Producto"])
    if 'db_inventario' not in st.session_state:
        st.session_state.db_inventario = pd.DataFrame(columns=[
            "Fecha_Ingreso", "Guia", "Nombre Destinatario", "Direcion Destino", "Telefono", "Cliente", "Producto", "Estado"
        ])
    if 'db_despacho' not in st.session_state:
        st.session_state.db_despacho = pd.DataFrame(columns=[
            "Fecha_Salida", "Guia", "Mensajero", "Nombre Destinatario", "Cliente", "Estado"
        ])

init_db()

# --- ESTILOS ---
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: white; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# --- ENCABEZADO CORPORATIVO ---
col_logo, col_text = st.columns([1, 4])
with col_logo:
    try:
        st.image("log fondo blancojpg.jpg", width=150)
    except:
        st.write("📦 **ENMILLA**")

with col_text:
    st.markdown(f"""
        <h1 style="margin:0; color:#003366;">ENMILLA</h1>
        <p style="margin:0; font-weight:bold;">Enlaces Soluciones Logísticas SAS | NIT: 901.939.284-4</p>
        """, unsafe_allow_html=True)

st.markdown("---")

tabs = st.tabs(["📊 Tablero", "📥 Ingreso", "🛵 Cargue", "⚙️ Admin"])

# --- 1. TABLERO DE CONTROL ---
with tabs[0]:
    c1, c2, c3 = st.columns(3)
    c1.metric("En Bodega", len(st.session_state.db_inventario))
    c2.metric("En Ruta", len(st.session_state.db_despacho))
    c3.metric("Total Hoy", len(st.session_state.db_inventario) + len(st.session_state.db_despacho))
    
    st.subheader("📦 Stock Actual")
    st.dataframe(st.session_state.db_inventario, use_container_width=True)

# --- 2. INGRESO A BODEGA ---
with tabs[1]:
    if st.session_state.db_tarifario.empty:
        st.info("💡 Diríjase a 'Admin' para crear su primer Cliente.")
    else:
        with st.container():
            col1, col2 = st.columns(2)
            cli = col1.selectbox("Cliente", st.session_state.db_tarifario["Cliente"].unique())
            prod = col2.selectbox("Producto", st.session_state.db_tarifario[st.session_state.db_tarifario["Cliente"] == cli]["Producto"])
            
            op = st.radio("Modo de Ingreso", ["Masivo (Archivo)", "Manual"], horizontal=True)

            if op == "Masivo (Archivo)":
                gen = st.checkbox("Generar guías internas Enmilla")
                archivo = st.file_uploader("Subir base", type=['xlsx', 'csv'])
                if archivo and st.button("🚀 Cargar Base"):
                    try:
                        df_in = pd.read_excel(archivo, engine='openpyxl') if archivo.name.endswith('.xlsx') else pd.read_csv(archivo)
                        df_in.columns = df_in.columns.str.strip()
                        
                        # Mapeo de seguridad para que coincida con tu archivo
                        df_in['Fecha_Ingreso'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                        df_in['Cliente'], df_in['Producto'], df_in['Estado'] = cli, prod, "En Bodega"
                        
                        if gen:
                            df_in['Guia'] = [f"ENM-{random.randint(100000, 999999)}" for _ in range(len(df_in))]
                        
                        # Solo tomamos las columnas que nuestra base soporta
                        cols_validas = [c for c in st.session_state.db_inventario.columns if c in df_in.columns]
                        st.session_state.db_inventario = pd.concat([st.session_state.db_inventario, df_in[cols_validas]], ignore_index=True).drop_duplicates(subset=['Guia'])
                        st.success("✅ Carga masiva completada.")
                    except Exception as e:
                        st.error(f"Error: Verifique que el archivo tenga las columnas correctas. ({e})")
            else:
                with st.form("manual"):
                    g = st.text_input("Guía")
                    d = st.text_input("Destinatario")
                    dir = st.text_input("Dirección")
                    if st.form_submit_button("Registrar"):
                        nueva_g = g if g else f"ENM-{random.randint(1000, 9999)}"
                        fila = pd.DataFrame([{"Fecha_Ingreso": datetime.datetime.now().strftime("%H:%M"), "Guia": nueva_g, "Nombre Destinatario": d, "Direcion Destino": dir, "Cliente": cli, "Producto": prod, "Estado": "En Bodega"}])
                        st.session_state.db_inventario = pd.concat([st.session_state.db_inventario, fila], ignore_index=True)
                        st.success("Registrado.")

# --- 3. CARGUE (PISTOLEO) ---
with tabs[2]:
    if st.session_state.db_mensajeros.empty:
        st.warning("⚠️ Registre mensajeros en Admin.")
    elif st.session_state.db_inventario.empty:
        st.info("La bodega está vacía.")
    else:
        m_sel = st.selectbox("Mensajero", st.session_state.db_mensajeros["Nombre"])
        guia_scan = st.text_input("💥 PISTOLEE AQUÍ", key="pistola_input")
        
        if guia_scan:
            inv = st.session_state.db_inventario
            match = inv[inv["Guia"] == guia_scan]
            
            if not match.empty:
                idx = match.index[0]
                # Extraer datos de forma segura
                nombre_dest = match.loc[idx, "Nombre Destinatario"] if "Nombre Destinatario" in match.columns else "N/A"
                
                n_desp = pd.DataFrame([{
                    "Fecha_Salida": datetime.datetime.now().strftime("%H:%M"),
                    "Guia": guia_scan, "Mensajero": m_sel, 
                    "Nombre Destinatario": nombre_dest,
                    "Cliente": match.loc[idx, "Cliente"], "Estado": "En Ruta"
                }])
                st.session_state.db_despacho = pd.concat([st.session_state.db_despacho, n_desp], ignore_index=True)
                st.session_state.db_inventario = inv.drop(idx)
                st.toast(f"✅ Guía {guia_scan} despachada.")
                st.rerun()
            else:
                st.error("Guía no encontrada en bodega.")

# --- 4. ADMIN ---
with tabs[3]:
    if st.text_input("Acceso Admin", type="password") == "1234":
        c_a, c_b = st.columns(2)
        with c_a:
            with st.form("a"):
                st.write("### Nuevo Cliente")
                nc = st.text_input("Nombre Empresa")
                np = st.text_input("Producto")
                if st.form_submit_button("Añadir"):
                    st.session_state.db_tarifario = pd.concat([st.session_state.db_tarifario, pd.DataFrame([{"Cliente": nc, "Producto": np}])], ignore_index=True)
        with c_b:
            with st.form("b"):
                st.write("### Nuevo Mensajero")
                nm = st.text_input("Nombre")
                pl = st.text_input("Placa")
                if st.form_submit_button("Añadir"):
                    st.session_state.db_mensajeros = pd.concat([st.session_state.db_mensajeros, pd.DataFrame([{"Nombre": nm, "Placa": pl}])], ignore_index=True)

st.markdown("---")
st.subheader("🚚 Despachos Realizados")
st.dataframe(st.session_state.db_despacho, use_container_width=True)
