import streamlit as st
import pandas as pd
import datetime
import streamlit.components.v1 as components

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Enmilla", layout="wide")

# --- PERSISTENCIA DE DATOS ---
if 'db_inventario' not in st.session_state:
    st.session_state.db_inventario = pd.DataFrame(columns=["Fecha_Ingreso", "Guia", "Nombre Destinatario", "Direcion Destino", "Telefono", "Cliente", "Estado"])
if 'db_referencia' not in st.session_state:
    st.session_state.db_referencia = pd.DataFrame()
if 'iteracion' not in st.session_state:
    st.session_state.iteracion = 0

# --- COMPONENTE DE FOCO AUTOMÁTICO (SOLUCIÓN TÉCNICA) ---
def forzar_foco():
    components.html(
        f"""
        <script>
            var inputs = window.parent.document.querySelectorAll('input[type="text"]');
            // Buscamos el campo específico de captura
            for (var i = 0; i < inputs.length; i++) {{
                inputs[i].focus();
            }}
        </script>
        """,
        height=0,
    )

# --- ENCABEZADO CORPORATIVO ---
col_logo, col_info = st.columns([1, 4])
with col_logo:
    try: st.image("log fondo blancojpg.jpg", width=120)
    except: st.write("📦 **ENMILLA**")
with col_info:
    st.markdown(f"<h2>ENMILLA</h2><p><b>Enlaces Soluciones Logísticas SAS</b> | NIT: 901.939.284-4</p>", unsafe_allow_html=True)

tabs = st.tabs(["📊 Dashboard", "📥 Recepción de Mercancía", "🛵 Despacho a Ruta", "⚙️ Configuración"])

# --- MÓDULO: RECEPCIÓN DE MERCANCÍA (CONTROL DE INGRESO) ---
with tabs[1]:
    st.subheader("Control de Ingreso por Escaneo")
    
    # Carga de base informativa (Opcional)
    with st.expander("📂 Cargar Manifiesto de Referencia", expanded=False):
        uploaded_file = st.file_uploader("Subir base de datos", type=['xlsx', 'csv'])
        if uploaded_file:
            df_ref = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('.xlsx') else pd.read_csv(uploaded_file)
            df_ref.columns = df_ref.columns.str.strip()
            st.session_state.db_referencia = df_ref
            st.success("Referencia cargada exitosamente.")

    # CAMPO DE CAPTURA CON FOCO AUTOMÁTICO
    # Usamos una clave dinámica para limpiar el campo tras cada lectura
    guia_leida = st.text_input(
        "LECTURA DE GUÍA (ESCANEADO CONTINUO)", 
        key=f"input_recepcion_{st.session_state.iteracion}",
        placeholder="A la espera de captura..."
    )

    # Inyectamos el foco después de renderizar el input
    forzar_foco()

    if guia_leida:
        g_id = guia_leida.strip()
        
        # Lógica Propositiva: Cruce con referencia o creación de registro nuevo
        ref = st.session_state.db_referencia
        datos = {"Nombre Destinatario": "PENDIENTE", "Direcion Destino": "PENDIENTE", "Telefono": "N/A", "Cliente": "EXTERNO"}
        
        if not ref.empty and 'Guia' in ref.columns:
            match = ref[ref['Guia'].astype(str) == g_id]
            if not match.empty:
                datos = {
                    "Nombre Destinatario": match.iloc[0].get('Nombre Destinatario', 'PENDIENTE'),
                    "Direcion Destino": match.iloc[0].get('Direcion Destino', 'PENDIENTE'),
                    "Telefono": match.iloc[0].get('Telefono', 'N/A'),
                    "Cliente": "REFERENCIADO"
                }

        # Actualización de Inventario Físico
        nuevo_registro = pd.DataFrame([{
            "Fecha_Ingreso": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "Guia": g_id,
            **datos,
            "Estado": "BODEGA"
        }])
        
        st.session_state.db_inventario = pd.concat([st.session_state.db_inventario, nuevo_registro], ignore_index=True).drop_duplicates(subset=['Guia'], keep='last')
        
        # Incremento de iteración para limpiar el campo y re-enfocar
        st.session_state.iteracion += 1
        st.toast(f"✅ Guía {g_id} ingresada correctamente.")
        st.rerun()

# --- MÓDULO: DASHBOARD (VISUALIZACIÓN DE INVENTARIO) ---
with tabs[0]:
    st.write("### Inventario Físico en Tiempo Real")
    st.metric("Total Unidades en Bodega", len(st.session_state.db_inventario))
    st.dataframe(st.session_state.db_inventario, use_container_width=True)
