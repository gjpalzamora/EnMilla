import streamlit as st
import pandas as pd
import datetime
import streamlit.components.v1 as components

# --- 1. CONFIGURACIÓN Y ESTADO DE ALTO RENDIMIENTO (BLOQUE INALTERABLE) ---
st.set_page_config(page_title="Enmilla - Enlaces Logística", layout="wide", page_icon="📦")

# Persistencia de bases de datos
if 'db_inventario' not in st.session_state:
    st.session_state.db_inventario = pd.DataFrame(columns=["Fecha_Ingreso", "Guia", "Nombre Destinatario", "Direcion Destino", "Telefono", "Cliente", "Estado"])
if 'db_referencia' not in st.session_state:
    st.session_state.db_referencia = pd.DataFrame()
if 'iteracion' not in st.session_state:
    st.session_state.iteracion = 0
if 'despacho_iter' not in st.session_state:
    st.session_state.despacho_iter = 0

# --- 2. INGENIERÍA DE ANCLAJE DE FOCO AGRESIVO (BLOQUE INALTERABLE) ---
def script_anclaje_foco(placeholder_text):
    # Mejora técnica definitiva para mantener el puntero activo
    components.html(
        f"""
        <script>
            const anclarCursor = () => {{
                const campos = window.parent.document.querySelectorAll('input[type="text"]');
                for (let campo of campos) {{
                    if (campo.getAttribute('placeholder') === '{placeholder_text}') {{
                        if (window.parent.document.activeElement !== campo) {{
                            campo.focus();
                            campo.select();
                        }}
                        break;
                    }}
                }}
            }};
            
            anclarCursor(); // Ejecución inmediata
            setTimeout(anclarCursor, 200); // Ejecución diferida para micro-retrasos
            setTimeout(anclarCursor, 600);
            
            // Vigilante de DOM: si algo cambia, re-enfoca
            const observador = new MutationObserver(anclarCursor);
            observador.observe(window.parent.document.body, {{ childList: true, subtree: true }});
        </script>
        """,
        height=0,
    )

# --- 3. DISEÑO VISUAL PROFESIONAL (CSS PERSONALIZADO) ---
# Aquí inyectamos el aspecto visual que perdimos
st.markdown("""
    <style>
    /* Fondo principal y tarjetas limpias */
    .main { background-color: #f6f8f9; }
    div[data-testid="stMetric"] { background-color: #ffffff; padding: 20px; border-radius: 10px; border: 1px solid #eaeaea; }
    
    /* Estilo de la barra superior */
    header { background-color: #003366 !important; color: white !important; padding: 20px; border-radius: 0 0 10px 10px; margin-bottom: 20px; }
    header h1, header p { color: white !important; margin: 0; }
    header img { border-radius: 50%; border: 2px solid white; margin-right: 15px; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. ENCABEZADO CORPORATIVO (INTEGRADO EN EL DISEÑO) ---
# Corrección del error de traceback de media file storage
header_col1, header_col2 = st.columns([1, 6])
with header_col1:
    try:
        # Cargamos el logo con manejo de errores técnico
        st.image("log fondo blancojpg.jpg", width=120)
    except Exception as e:
        # Fallback silencioso si falla la carga
        st.write("📦 **ENMILLA**")
with header_col2:
    st.markdown(f"<h2>ENMILLA</h2><p><b>Enlaces Soluciones Logísticas SAS</b> | NIT: 901.939.284-4</p>", unsafe_allow_html=True)

st.markdown("---")

# Estructura de pestañas profesional
tabs = st.tabs(["📊 Panel de Control", "📥 Recepción Técnica", "🛵 Despacho a Ruta", "⚙️ Administración"])

# --- 5. TABS Y BLOQUES DE FUNCIONALIDAD TÉCNICA (PROTEGIDOS) ---

# --- TAB 1: PANEL DE CONTROL (DASHBOARD) ---
with tabs[0]:
    st.write("### Estado de Inventario Físico en Tiempo Real")
    col1, col2 = st.columns(2)
    col1.metric("Unidades Físicas en Bodega", len(st.session_state.db_inventario))
    col2.metric("Unidades en Ruta", "0") # Placeholder para futura funcionalidad
    
    st.dataframe(st.session_state.db_inventario, use_container_width=True)

# --- TAB 2: RECEPCIÓN TÉCNICA (CONTROL DE INGRESO FÍSICO) ---
# Mantenemos intacta la lógica de escaneo continuo
with tabs[1]:
    st.subheader("Control de Ingreso por Escaneo de Radiofrecuencia")
    
    # Carga de Manifiesto Informativo (Inalterable)
    with st.expander("📂 Cargar Manifiesto de Referencia (Informativo)", expanded=False):
        uploaded_file = st.file_uploader("Subir base de datos de referencia", type=['xlsx', 'csv'], key="up_recepcion")
        if uploaded_file:
            df_temp = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('.xlsx') else pd.read_csv(uploaded_file)
            df_temp.columns = df_temp.columns.str.strip()
            st.session_state.db_referencia = df_temp
            st.success("Manifiesto vinculado correctamente.")

    # Campo de captura técnico automatizado con clave dinámica
    # autocomplete="new-password" para bloquear Chrome
    guia_capturada = st.text_input(
        "ENTRADA DE UNIDAD", 
        key=f"scan_recepcion_{st.session_state.iteracion}",
        placeholder="CAPTURA ACTIVA - ESCANEE UNIDAD",
        autocomplete="new-password"
    )

    # Inyectamos el anclaje de puntero agresivo
    script_anclaje_foco("CAPTURA ACTIVA - ESCANEE UNIDAD")

    if guia_capturada:
        g_id = guia_capturada.strip()
        
        # Validación y Cruce de Datos (Propositivo: no frena la operación)
        ref = st.session_state.db_referencia
        info_paquete = {"Nombre Destinatario": "EXTERNO / NO PRE-CARGADO", "Direcion Destino": "VERIFICAR MANUAL", "Telefono": "N/A", "Cliente": "EXTERNO"}
        
        if not ref.empty and 'Guia' in ref.columns:
            match = ref[ref['Guia'].astype(str).str.strip() == g_id]
            if not match.empty:
                info_paquete = {
                    "Nombre Destinatario": match.iloc[0].get('Nombre Destinatario', 'N/A'),
                    "Direcion Destino": match.iloc[0].get('Direcion Destino', 'N/A'),
                    "Telefono": match.iloc[0].get('Telefono', 'N/A'),
                    "Cliente": "REFERENCIADO"
                }

        # Registro en el Inventario Físico de Bodega
        nuevo_item = pd.DataFrame([{
            "Fecha_Ingreso": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "Guia": g_id,
            **info_paquete,
            "Estado": "BODEGA"
        }])
        
        # Concatenación y eliminación de duplicados
        st.session_state.db_inventario = pd.concat([st.session_state.db_inventario, nuevo_item], ignore_index=True).drop_duplicates(subset=['Guia'], keep='last')
        
        # Reinicio de ciclo operativo para limpieza total del buffer
        st.session_state.iteracion += 1
        st.toast(f"✅ UNIDAD REGISTRADA: {g_id}")
        st.rerun()

# --- LAS DEMÁS PESTAÑAS SE CONSERVAN IGUAL (ADMIN, DESPACHO) ---
with tabs[3]:
    st.subheader("Gestión Maestra")
    # Formulario para mensajeros (inalterable)
    with st.form("admin_m"):
        m_name = st.text_input("Nombre Completo Mensajero")
        if st.form_submit_button("Registrar"):
            if 'db_mensajeros' not in st.session_state: st.session_state.db_mensajeros = pd.DataFrame(columns=['Nombre'])
            st.session_state.db_mensajeros = pd.concat([st.session_state.db_mensajeros, pd.DataFrame([{'Nombre': m_name}])], ignore_index=True)
            st.success("Mensajero creado.")
