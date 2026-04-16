import streamlit as st
import pandas as pd
import datetime
import streamlit.components.v1 as components

# --- 1. CONFIGURACIÓN Y ESTADO (INALTERABLE) ---
st.set_page_config(page_title="Enmilla - Enlaces Logística", layout="wide", page_icon="📦")

# Aseguramos la existencia de las tablas de datos
for tabla, columnas in {
    'db_inventario': ["Fecha", "Guia", "Nombre Destinatario", "Direccion", "Cliente", "Estado"],
    'db_mensajeros': ["Nombre", "Vehiculo", "Telefono", "Fecha_Registro"],
    'db_clientes': ["Nombre_Empresa", "NIT", "Ciudad", "Contacto"],
    'db_productos': ["SKU/Referencia", "Descripcion", "Cliente_Asociado"]
}.items():
    if tabla not in st.session_state:
        st.session_state[tabla] = pd.DataFrame(columns=columnas)

if 'iteracion' not in st.session_state: st.session_state.iteracion = 0

# --- 2. SCRIPT DE ANCLAJE DE FOCO (SOLUCIÓN PISTOLA) ---
def script_foco_agresivo(placeholder_target):
    components.html(f"""
        <script>
            const forzarFoco = () => {{
                const inputs = window.parent.document.querySelectorAll('input[type="text"]');
                for (let input of inputs) {{
                    if (input.getAttribute('placeholder') === '{placeholder_target}') {{
                        if (window.parent.document.activeElement !== input) {{ input.focus(); }}
                        break;
                    }}
                }}
            }};
            forzarFoco();
            const observer = new MutationObserver(forzarFoco);
            observer.observe(window.parent.document.body, {{ childList: true, subtree: true }});
        </script>
    """, height=0)

# --- 3. ENCABEZADO CORPORATIVO ---
col_logo, col_titulo = st.columns([1, 5])
with col_logo:
    try: st.image("log fondo blancojpg.jpg", width=140)
    except: st.write("📦 **ENMILLA**")
with col_titulo:
    st.markdown("## ENMILLA")
    st.markdown("**Enlaces Soluciones Logísticas SAS** | NIT: 901.939.284-4")

tabs = st.tabs(["📊 Panel", "📥 Recepción", "🛵 Despacho", "⚙️ Administración"])

# --- TAB 1, 2 y 3: (SE MANTIENEN CON LA LÓGICA DE FOCO Y DATOS ACTUAL) ---
with tabs[0]: st.subheader("Vista General de Operación"); st.dataframe(st.session_state.db_inventario)
with tabs[1]: 
    st.subheader("Captura de Ingresos")
    guia_in = st.text_input("ESCANEE UNIDAD", key=f"in_{st.session_state.iteracion}", placeholder="CAPTURA_BODEGA")
    script_foco_agresivo("CAPTURA_BODEGA")
    if guia_in:
        # Registro rápido...
        st.session_state.iteracion += 1; st.rerun()

# --- 4. MÓDULO DE ADMINISTRACIÓN POTENCIADO ---
with tabs[3]:
    st.header("⚙️ Gestión Administrativa")
    
    # Sub-navegación interna para administración
    sub_tabs = st.tabs(["👥 Mensajeros", "🏢 Clientes", "📦 Productos", "🛠️ Herramientas de Sistema"])
    
    # --- SUB-TAB: MENSAJEROS ---
    with sub_tabs[0]:
        st.subheader("Gestión de Personal de Ruta")
        col_m1, col_m2 = st.columns([1, 2])
        with col_m1:
            with st.form("form_mensajero", clear_on_submit=True):
                m_nom = st.text_input("Nombre Completo")
                m_veh = st.selectbox("Vehículo", ["Moto", "Van", "Camión", "Bicicleta"])
                m_tel = st.text_input("Teléfono de Contacto")
                if st.form_submit_button("Registrar Mensajero"):
                    nuevo_m = pd.DataFrame([{"Nombre": m_nom, "Vehiculo": m_veh, "Telefono": m_tel, "Fecha_Registro": datetime.date.today()}])
                    st.session_state.db_mensajeros = pd.concat([st.session_state.db_mensajeros, nuevo_m], ignore_index=True)
                    st.success(f"Mensajero {m_nom} registrado.")
        with col_m2:
            st.dataframe(st.session_state.db_mensajeros, use_container_width=True)

    # --- SUB-TAB: CLIENTES ---
    with sub_tabs[1]:
        st.subheader("Maestro de Clientes")
        with st.form("form_clientes", clear_on_submit=True):
            c_col1, c_col2 = st.columns(2)
            c_nom = c_col1.text_input("Nombre Empresa")
            c_nit = c_col2.text_input("NIT / Identificación")
            c_ciu = c_col1.text_input("Ciudad Principal", value="Bogotá")
            c_con = c_col2.text_input("Persona de Contacto")
            if st.form_submit_button("Guardar Cliente"):
                nuevo_c = pd.DataFrame([{"Nombre_Empresa": c_nom, "NIT": c_nit, "Ciudad": c_ciu, "Contacto": c_con}])
                st.session_state.db_clientes = pd.concat([st.session_state.db_clientes, nuevo_c], ignore_index=True)
                st.success("Cliente vinculado satisfactoriamente.")
        st.dataframe(st.session_state.db_clientes, use_container_width=True)

    # --- SUB-TAB: PRODUCTOS ---
    with sub_tabs[2]:
        st.subheader
