import streamlit as st
import pandas as pd
import datetime
import streamlit.components.v1 as components

# --- 1. CONFIGURACIÓN DE ALTO RENDIMIENTO (INALTERABLE) ---
st.set_page_config(page_title="Enmilla - Enlaces Logística", layout="wide", page_icon="📦")

# Inicialización de bases de datos en Session State para persistencia total
bases_de_datos = {
    'db_inventario': ["Fecha_Ingreso", "Guia", "Nombre Destinatario", "Direcion Destino", "Telefono", "Cliente", "Estado"],
    'db_mensajeros': ["Nombre", "ID", "Vehiculo", "Fecha_Registro"],
    'db_clientes': ["Nombre_Empresa", "NIT", "Contacto", "Ciudad"],
    'db_despachos': ["Fecha_Salida", "Guia", "Mensajero", "Estado"]
}

for tabla, columnas in bases_de_datos.items():
    if tabla not in st.session_state:
        st.session_state[tabla] = pd.DataFrame(columns=columnas)

if 'db_referencia' not in st.session_state:
    st.session_state.db_referencia = pd.DataFrame()
if 'iteracion' not in st.session_state:
    st.session_state.iteracion = 0

# --- 2. INGENIERÍA DE ANCLAJE DE FOCO (SOLUCIÓN PUNTERO) ---
def script_foco_agresivo(placeholder_target):
    # Esta mejora técnica asegura que el cursor no se pierda tras el escaneo
    components.html(f"""
        <script>
            const forzarFoco = () => {{
                const inputs = window.parent.document.querySelectorAll('input[type="text"]');
                for (let input of inputs) {{
                    if (input.getAttribute('placeholder') === '{placeholder_target}') {{
                        if (window.parent.document.activeElement !== input) {{
                            input.focus();
                        }}
                        break;
                    }}
                }}
            }};
            forzarFoco();
            setTimeout(forzarFoco, 300);
            const observer = new MutationObserver(forzarFoco);
            observer.observe(window.parent.document.body, {{ childList: true, subtree: true }});
        </script>
    """, height=0)

# --- 3. DISEÑO VISUAL Y ENCABEZADO CORPORATIVO ---
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: white; border-radius: 10px; border: 1px solid #e0e0e0; padding: 15px; }
    h2 { color: #003366; }
    </style>
    """, unsafe_allow_html=True)

col_logo, col_titulo = st.columns([1, 5])
with col_logo:
    try: st.image("log fondo blancojpg.jpg", width=140)
    except: st.write("📦 **ENMILLA**")
with col_titulo:
    st.markdown("## ENMILLA")
    st.markdown("**Enlaces Soluciones Logísticas SAS** | NIT: 901.939.284-4")

# --- 4. NAVEGACIÓN POR MÓDULOS (RESTAURADOS) ---
tabs = st.tabs(["📊 Tablero", "📥 Ingreso (Pistoleo)", "🛵 Despacho", "👥 Clientes", "🏃 Mensajeros", "⚙️ Admin"])

# --- TAB: TABLERO (ESTADÍSTICAS REALES) ---
with tabs[0]:
    st.subheader("Panel de Control Operativo")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("En Bodega", len(st.session_state.db_inventario))
    m2.metric("Despachados", len(st.session_state.db_despachos))
    m3.metric("Mensajeros Activos", len(st.session_state.db_mensajeros))
    m4.metric("Clientes Registrados", len(st.session_state.db_clientes))
    
    st.write("### Inventario Actual en Bodega")
    st.dataframe(st.session_state.db_inventario, use_container_width=True)

# --- TAB: INGRESO (RECEPCIÓN TÉCNICA) ---
with tabs[1]:
    st.subheader("Recepción de Mercancía (Pistoleo Físico)")
    with st.expander("📂 Cargar Excel de Referencia (Informativo)"):
        up_file = st.file_uploader("Subir base", type=['xlsx', 'csv'], key="up_rec")
        if up_file:
            st.session_state.db_referencia = pd.read_excel(up_file) if up_file.name.endswith('.xlsx') else pd.read_csv(up_file)
            st.success("Referencia cargada.")

    # Campo de captura con limpieza automática
    guia_scan = st.text_input(
        "PISTOLEE PARA ENTRADA", 
        key=f"in_{st.session_state.iteracion}",
        placeholder="ESCANEE UNIDAD AQUÍ"
    )
    script_foco_agresivo("ESCANEE UNIDAD AQUÍ")

    if guia_scan:
        g_id = guia_scan.strip()
        ref = st.session_state.db_referencia
        datos = {"Nombre Destinatario": "EXTERNO", "Direcion Destino": "PENDIENTE", "Telefono": "N/A", "Cliente": "EXTERNO"}
        
        # Cruce con manifiesto
        if not ref.empty and 'Guia' in ref.columns:
            match = ref[ref['Guia'].astype(str).str.strip() == g_id]
            if not match.empty:
                datos = {
                    "Nombre Destinatario": match.iloc[0].get('Nombre Destinatario', 'N/A'),
                    "Direcion Destino": match.iloc[0].get('Direcion Destino', 'N/A'),
                    "Telefono": match.iloc[0].get('Telefono', 'N/A'),
                    "Cliente": "REFERENCIADO"
                }

        nuevo_reg = pd.DataFrame([{"Fecha_Ingreso": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "Guia": g_id, **datos, "Estado": "BODEGA"}])
        st.session_state.db_inventario = pd.concat([st.session_state.db_inventario, nuevo_reg], ignore_index=True).drop_duplicates('Guia', keep='last')
        
        st.session_state.iteracion += 1
        st.toast(f"✅ Guía {g_id} registrada")
        st.rerun()

# --- TAB: DESPACHO ---
with tabs[2]:
    st.subheader("Cargue de Vehículos y Salida")
    if not st.session_state.db_mensajeros.empty:
        mensajero_sel = st.selectbox("Seleccionar Mensajero", st.session_state.db_mensajeros['Nombre'])
        guia_out = st.text_input("PISTOLEE PARA SALIDA", key=f"out_{st.session_state.iteracion}", placeholder="SALIDA A RUTA")
        script_foco_agresivo("SALIDA A RUTA")
        
        if guia_out:
            g_out_id = guia_out.strip()
            # Lógica: Mover de inventario a despachos
            if g_out_id in st.session_state.db_inventario['Guia'].values:
                nuevo_desp = pd.DataFrame([{"Fecha_Salida": datetime.datetime.now(), "Guia": g_out_id, "Mensajero": mensajero_sel, "Estado": "EN RUTA"}])
                st.session_state.db_despachos = pd.concat([st.session_state.db_despachos, nuevo_desp], ignore_index=True)
                st.session_state.db_inventario = st.session_state.db_inventario[st.session_state.db_inventario['Guia'] != g_out_id]
                st.session_state.iteracion += 1
                st.success(f"Guía {g_out_id} asignada a {mensajero_sel}")
                st.rerun()
            else:
                st.error("Error: La guía no se encuentra en bodega.")
    else:
        st.warning("Debe registrar mensajeros en la pestaña correspondiente.")

# --- TAB: CLIENTES (RESTAURADO) ---
with tabs[3]:
    st.subheader("Gestión de Clientes")
    with st.form("form_clientes"):
        c_nom = st.text_input("Nombre   
