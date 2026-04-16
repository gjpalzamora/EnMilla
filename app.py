import streamlit as st
import pandas as pd
import datetime
import random

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Enmilla", layout="wide", page_icon="📦")

# --- MOTOR DE DATOS ---
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
    # Clave para resetear el input del scanner
    if 'input_key' not in st.session_state:
        st.session_state.input_key = 0

init_db()

# --- ENCABEZADO ---
col_logo, col_text = st.columns([1, 4])
with col_logo:
    try: st.image("log fondo blancojpg.jpg", width=150)
    except: st.write("📦 **ENMILLA**")

with col_text:
    st.markdown(f"""
        <h1 style="margin:0; color:#003366;">ENMILLA</h1>
        <p style="margin:0; font-weight:bold;">Enlaces Soluciones Logísticas SAS | NIT: 901.939.284-4</p>
        """, unsafe_allow_html=True)

st.markdown("---")
tabs = st.tabs(["📊 Tablero", "📥 Ingreso", "🛵 Cargue", "⚙️ Admin"])

# --- TAB 3: CARGUE (PISTOLEO CONTINUO OPTIMIZADO) ---
with tabs[2]:
    if st.session_state.db_mensajeros.empty:
        st.warning("⚠️ Registre mensajeros en Admin antes de despachar.")
    elif st.session_state.db_inventario.empty:
        st.info("La bodega está vacía. Cargue una base de datos para empezar.")
    else:
        st.subheader("🛵 Despacho a Mensajero")
        m_sel = st.selectbox("Mensajero Responsable", st.session_state.db_mensajeros["Nombre"])
        
        # PROPOSITIVO: Usamos st.session_state.input_key para forzar la limpieza del campo
        guia_scan = st.text_input(
            "💥 ESCANEE GUÍA (EL CAMPO SE LIMPIARÁ SOLO)", 
            key=f"scanner_{st.session_state.input_key}"
        )
        
        if guia_scan:
            inv = st.session_state.db_inventario
            # Buscamos la guía ignorando espacios accidentales
            match = inv[inv["Guia"].astype(str).str.strip() == guia_scan.strip()]
            
            if not match.empty:
                idx = match.index[0]
                # Registrar el movimiento
                n_desp = pd.DataFrame([{
                    "Fecha_Salida": datetime.datetime.now().strftime("%H:%M"),
                    "Guia": guia_scan, 
                    "Mensajero": m_sel, 
                    "Nombre Destinatario": match.loc[idx, "Nombre Destinatario"],
                    "Cliente": match.loc[idx, "Cliente"], 
                    "Estado": "En Ruta"
                }])
                
                # Actualizar estados
                st.session_state.db_despacho = pd.concat([st.session_state.db_despacho, n_desp], ignore_index=True)
                st.session_state.db_inventario = inv.drop(idx)
                
                # INCREMENTAR KEY PARA LIMPIAR EL INPUT
                st.session_state.input_key += 1
                
                st.toast(f"✅ Guía {guia_scan} cargada correctamente.")
                st.rerun() # Reinicia la app para que el cursor vuelva al campo limpio
            else:
                st.error(f"❌ La guía {guia_scan} NO está en bodega. Verifique el ingreso.")
                # Si falla, también limpiamos para no bloquear la operación
                if st.button("Limpiar para reintentar"):
                    st.session_state.input_key += 1
                    st.rerun()

# --- LAS DEMÁS PESTAÑAS SE MANTIENEN IGUAL (ADMIN, INGRESO, TABLERO) ---
with tabs[1]: # INGRESO
    if not st.session_state.db_tarifario.empty:
        col1, col2 = st.columns(2)
        cli = col1.selectbox("Cliente", st.session_state.db_tarifario["Cliente"].unique())
        prod = col2.selectbox("Producto", st.session_state.db_tarifario[st.session_state.db_tarifario["Cliente"] == cli]["Producto"])
        archivo = st.file_uploader("Subir base", type=['xlsx', 'csv'])
        if archivo and st.button("🚀 Cargar Base"):
            df_in = pd.read_excel(archivo) if archivo.name.endswith('.xlsx') else pd.read_csv(archivo)
            df_in['Cliente'], df_in['Producto'], df_in['Estado'] = cli, prod, "En Bodega"
            st.session_state.db_inventario = pd.concat([st.session_state.db_inventario, df_in], ignore_index=True).drop_duplicates(subset=['Guia'])
            st.success("Base cargada.")

with tabs[3]: # ADMIN
    if st.text_input("Acceso Admin", type="password") == "1234":
        c_a, c_b = st.columns(2)
        with c_a:
            with st.form("a"):
                nc = st.text_input("Nombre Empresa"); np = st.text_input("Producto")
                if st.form_submit_button("Añadir Cliente"):
                    st.session_state.db_tarifario = pd.concat([st.session_state.db_tarifario, pd.DataFrame([{"Cliente": nc, "Producto": np}])], ignore_index=True)
        with c_b:
            with st.form("b"):
                nm = st.text_input("Nombre"); pl = st.text_input("Placa")
                if st.form_submit_button("Añadir Mensajero"):
                    st.session_state.db_mensajeros = pd.concat([st.session_state.db_mensajeros, pd.DataFrame([{"Nombre": nm, "Placa": pl}])], ignore_index=True)

with tabs[0]: # TABLERO
    st.metric("Stock en Bodega", len(st.session_state.db_inventario))
    st.dataframe(st.session_state.db_inventario, use_container_width=True)

st.markdown("---")
st.subheader("🚚 Registro de Salidas")
st.dataframe(st.session_state.db_despacho, use_container_width=True)
