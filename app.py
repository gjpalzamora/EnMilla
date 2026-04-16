import streamlit as st
import pandas as pd
import datetime
import random

# --- CONFIGURACIÓN E IDENTIDAD ---
st.set_page_config(page_title="Enmilla", layout="wide")

# --- MOTOR DE DATOS (BASE DE OPERACIÓN) ---
if 'db_inventario' not in st.session_state:
    st.session_state.db_inventario = pd.DataFrame(columns=["Fecha_Ingreso", "Guia", "Nombre Destinatario", "Direcion Destino", "Telefono", "Cliente", "Estado"])
if 'db_excel_referencia' not in st.session_state:
    st.session_state.db_excel_referencia = pd.DataFrame()
if 'count_ingreso' not in st.session_state: st.session_state.count_ingreso = 0
if 'count_despacho' not in st.session_state: st.session_state.count_despacho = 0

# --- ENCABEZADO CORPORATIVO ---
col_logo, col_text = st.columns([1, 4])
with col_logo:
    try: st.image("log fondo blancojpg.jpg", width=150)
    except: st.write("📦 **ENMILLA**")
with col_text:
    st.markdown(f"<h1 style='margin:0;color:#003366;'>ENMILLA</h1><p style='margin:0;'><b>Enlaces Soluciones Logísticas SAS</b> | NIT: 901.939.284-4</p>", unsafe_allow_html=True)

tabs = st.tabs(["📊 Dashboard", "📥 Ingreso (Pistoleo)", "🛵 Despacho", "⚙️ Admin"])

# --- TAB 2: INGRESO (EL CORAZÓN DE LA BODEGA) ---
with tabs[1]:
    st.subheader("📥 Recepción de Mercancía (Pistoleo Físico)")
    
    # 1. Carga de Referencia (Opcional para traer datos)
    with st.expander("📁 Cargar Excel de Referencia (Informativo)", expanded=False):
        file = st.file_uploader("Subir base del cliente", type=['xlsx', 'csv'])
        if file:
            ref_df = pd.read_excel(file) if file.name.endswith('.xlsx') else pd.read_csv(file)
            ref_df.columns = ref_df.columns.str.strip()
            st.session_state.db_excel_referencia = ref_df
            st.success("Referencia cargada. El sistema buscará datos aquí al pistolear.")

    # 2. Área de Pistoleo de Entrada
    st.info("Pistolee cada paquete para ingresarlo al inventario real de bodega.")
    
    # El uso de una clave dinámica (count_ingreso) fuerza la limpieza del campo
    guia_ingreso = st.text_input("💥 PISTOLEE PARA ENTRADA", key=f"ingreso_{st.session_state.count_ingreso}")

    if guia_ingreso:
        g_limpia = guia_ingreso.strip()
        
        # Buscar en el Excel informativo
        ref = st.session_state.db_excel_referencia
        datos_paquete = {"Nombre Destinatario": "N/A", "Direcion Destino": "N/A", "Telefono": "N/A", "Cliente": "Externo"}
        
        if not ref.empty and 'Guia' in ref.columns:
            match_ref = ref[ref['Guia'].astype(str) == g_limpia]
            if not match_ref.empty:
                datos_paquete = {
                    "Nombre Destinatario": match_ref.iloc[0].get('Nombre Destinatario', 'N/A'),
                    "Direcion Destino": match_ref.iloc[0].get('Direcion Destino', 'N/A'),
                    "Telefono": match_ref.iloc[0].get('Telefono', 'N/A'),
                    "Cliente": "Referenciado"
                }

        # Crear registro real de inventario
        nuevo_item = pd.DataFrame([{
            "Fecha_Ingreso": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "Guia": g_limpia,
            **datos_paquete,
            "Estado": "En Bodega"
        }])
        
        st.session_state.db_inventario = pd.concat([st.session_state.db_inventario, nuevo_item], ignore_index=True).drop_duplicates(subset=['Guia'], keep='last')
        
        st.session_state.count_ingreso += 1  # Esto limpia el campo automáticamente
        st.toast(f"✅ Guía {g_limpia} ingresada a bodega.")
        st.rerun()

# --- TAB 3: DESPACHO (SALIDA A RUTA) ---
with tabs[2]:
    st.subheader("🛵 Cargue de Vehículos")
    if st.session_state.db_inventario.empty:
        st.warning("No hay mercancía en bodega. Debe pistolear los ingresos primero.")
    else:
        # Selección de mensajero (debe estar en Admin)
        mensajeros = st.session_state.get('db_mensajeros', pd.DataFrame(columns=['Nombre']))
        m_sel = st.selectbox("Mensajero", mensajeros['Nombre'] if not mensajeros.empty else ["Sin mensajeros"])
        
        guia_despacho = st.text_input("💥 PISTOLEE PARA SALIDA", key=f"despacho_{st.session_state.count_despacho}")
        
        if guia_despacho:
            g_salida = guia_despacho.strip()
            inv = st.session_state.db_inventario
            match_inv = inv[inv["Guia"].astype(str) == g_salida]
            
            if not match_inv.empty:
                # Mover a despacho y quitar de inventario
                st.session_state.db_inventario = inv[inv["Guia"].astype(str) != g_salida]
                st.session_state.count_despacho += 1
                st.toast(f"✅ Guía {g_salida} cargada a mensajero.")
                st.rerun()
            else:
                st.error(f"❌ La guía {g_salida} no ha sido ingresada a bodega todavía.")
                if st.button("Limpiar error"):
                    st.session_state.count_despacho += 1
                    st.rerun()

# --- TAB 1: DASHBOARD ---
with tabs[0]:
    c1, c2 = st.columns(2)
    c1.metric("📦 En Bodega (Físico)", len(st.session_state.db_inventario))
    c2.metric("📋 Referencia Excel", len(st.session_state.db_excel_referencia))
    st.write("### Inventario Real de Enlaces Soluciones")
    st.dataframe(st.session_state.db_inventario, use_container_width=True)

# --- TAB 4: ADMIN ---
with tabs[3]:
    if st.text_input("Clave Admin", type="password") == "1234":
        with st.form("add_m"):
            nom = st.text_input("Nuevo Mensajero")
            if st.form_submit_button("Registrar"):
                if 'db_mensajeros' not in st.session_state: st.session_state.db_mensajeros = pd.DataFrame(columns=['Nombre'])
                st.session_state.db_mensajeros = pd.concat([st.session_state.db_mensajeros, pd.DataFrame([{'Nombre': nom}])], ignore_index=True)
                st.success("Mensajero creado.")
