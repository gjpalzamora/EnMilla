import streamlit as st
import pandas as pd
import datetime
import streamlit.components.v1 as components

# --- CONFIGURACIÓN DE ALTO RENDIMIENTO ---
st.set_page_config(page_title="Enmilla", layout="wide")

# --- PERSISTENCIA DE DATOS (ARQUITECTURA DE ESTADO) ---
if 'db_inventario' not in st.session_state:
    st.session_state.db_inventario = pd.DataFrame(columns=["Fecha_Ingreso", "Guia", "Nombre Destinatario", "Direcion Destino", "Telefono", "Cliente", "Estado"])
if 'db_referencia' not in st.session_state:
    st.session_state.db_referencia = pd.DataFrame()
if 'iteracion' not in st.session_state:
    st.session_state.iteracion = 0

# --- INGENIERÍA DE FOCO AUTOMÁTICO (SCRIPT DE ANCLAJE PERPETUO) ---
def script_foco_perpetuo():
    # JavaScript avanzado: Usa un observador de mutaciones para asegurar el foco 
    # incluso si hay micro-retrasos en el renderizado del navegador.
    components.html(
        """
        <script>
            const anclarCursor = () => {
                const campos = window.parent.document.querySelectorAll('input[type="text"]');
                for (let campo of campos) {
                    if (campo.getAttribute('placeholder') === 'CAPTURA ACTIVA - ESCANEE UNIDAD') {
                        if (window.parent.document.activeElement !== campo) {
                            campo.focus();
                            campo.select();
                        }
                        break;
                    }
                }
            };
            
            // Ejecución multietapa para garantizar efectividad
            anclarCursor();
            setTimeout(anclarCursor, 100);
            setTimeout(anclarCursor, 300);
            setTimeout(anclarCursor, 700);
            
            // Vigilante de DOM: si el sistema cambia, re-enfoca
            const observador = new MutationObserver(anclarCursor);
            observador.observe(window.parent.document.body, { childList: true, subtree: true });
        </script>
        """,
        height=0,
    )

# --- IDENTIDAD CORPORATIVA ---
col_logo, col_info = st.columns([1, 4])
with col_logo:
    try: st.image("log fondo blancojpg.jpg", width=120)
    except: st.write("📦 **ENMILLA**")
with col_info:
    st.markdown(f"<h2>ENMILLA</h2><p><b>Enlaces Soluciones Logísticas SAS</b> | NIT: 901.939.284-4</p>", unsafe_allow_html=True)

tabs = st.tabs(["📊 Dashboard de Inventario", "📥 Recepción Técnica", "🛵 Despacho a Ruta", "⚙️ Configuración"])

# --- MÓDULO: RECEPCIÓN TÉCNICA (CONTROL DE INGRESO FÍSICO) ---
with tabs[1]:
    st.subheader("Control de Ingreso por Escaneo de Radiofrecuencia")
    
    with st.expander("📂 Cargar Manifiesto Informativo (Opcional)", expanded=False):
        up = st.file_uploader("Subir base de datos de referencia", type=['xlsx', 'csv'], key="up_recepcion")
        if up:
            df_temp = pd.read_excel(up) if up.name.endswith('.xlsx') else pd.read_csv(up)
            df_temp.columns = df_temp.columns.str.strip()
            st.session_state.db_referencia = df_temp
            st.success("Manifiesto vinculado correctamente.")

    # CAMPO DE CAPTURA AUTOMATIZADO
    # La clave dinámica 'iteracion' fuerza la limpieza total del buffer tras cada lectura
    guia_capturada = st.text_input(
        "ENTRADA DE UNIDAD", 
        key=f"scan_ingreso_{st.session_state.iteracion}",
        placeholder="CAPTURA ACTIVA - ESCANEE UNIDAD"
    )

    # Inyectamos el anclaje de cursor
    script_foco_perpetuo()

    if guia_capturada:
        g_id = guia_capturada.strip()
        
        # Validación y Cruce de Datos
        ref = st.session_state.db_referencia
        # Datos por defecto si no existe en el Excel
        info_paquete = {"Nombre Destinatario": "EXTERNO / NO PRE-CARGADO", "Direcion Destino": "VERIFICAR MANUAL", "Telefono": "N/A", "Cliente": "EXTERNO"}
        
        if not ref.empty and 'Guia' in ref.columns:
            # Buscamos coincidencia exacta ignorando espacios y tipos de datos
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
        
        # Concatenación y eliminación de duplicados (prevalece el último escaneo)
        st.session_state.db_inventario = pd.concat([st.session_state.db_inventario, nuevo_item], ignore_index=True).drop_duplicates(subset=['Guia'], keep='last')
        
        # Reinicio de ciclo operativo
        st.session_state.iteracion += 1
        st.toast(f"✅ UNIDAD REGISTRADA: {g_id}")
        st.rerun()

# --- MÓDULO: DASHBOARD (VISIBILIDAD OPERATIVA) ---
with tabs[0]:
    st.write("### Inventario Físico en Tiempo Real (Bogotá - Barrios Unidos)")
    st.metric("Unidades Disponibles en Bodega", len(st.session_state.db_inventario))
    st.dataframe(st.session_state.db_inventario, use_container_width=True)
