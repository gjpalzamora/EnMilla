import streamlit as st
import pandas as pd
import datetime
import re
from fpdf import FPDF
import streamlit.components.v1 as components

# --- 1. CONFIGURACIÓN INICIAL (EVITA PANTALLAS EN BLANCO) ---
st.set_page_config(page_title="Enmilla ERP v1.2", layout="wide")

def inicializar_datos():
    tablas = {
        'db_inventario': ["Fecha", "Guia", "Cliente", "Estado"],
        'db_mensajeros': ["Nombre", "Vehiculo"],
        'db_clientes': ["Nombre", "Regex"]
    }
    for tabla, columnas in tablas.items():
        if tabla not in st.session_state:
            st.session_state[tabla] = pd.DataFrame(columns=columnas)
    if 'key_pistola' not in st.session_state:
        st.session_state.key_pistola = 0

inicializar_datos()

# --- 2. MOTOR LOGÍSTICO (CORRECCIÓN DE ERRORES) ---

def motor_regex(guia):
    """Identifica cliente. Si no hay clientes configurados, devuelve 'Pendiente'"""
    if st.session_state.db_clientes.empty:
        return "CLIENTE NO CONFIGURADO"
    for _, fila in st.session_state.db_clientes.iterrows():
        try:
            if re.match(fila['Regex'], guia, re.IGNORECASE):
                return fila['Nombre']
        except: continue
    return "DESCONOCIDO"

def inyectar_foco_corregido(placeholder_id):
    """
    CORRECCIÓN CRÍTICA: Se eliminó la dependencia de variables externas 
    dentro del string de JS para evitar el error de la imagen anterior.
    """
    components.html(f"""
        <script>
            const forzarFoco = () => {{
                const docs = window.parent.document;
                const inputs = docs.querySelectorAll('input[type="text"]');
                for (let x of inputs) {{
                    if (x.getAttribute('placeholder') === '{placeholder_id}') {{
                        if (docs.activeElement !== x) x.focus();
                        break;
                    }}
                }}
            }};
            setInterval(forzarFoco, 500);
        </script>
    """, height=0)

# --- 3. GENERADOR DE PDF (MEDIA CARTA - 140x216mm) ---

def generar_planilla_pdf(mensajero, guias):
    pdf = FPDF(format=(140, 216))
    pdf.add_page()
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "ENLACES SOLUCIONES LOGISTICAS SAS", ln=True, align='C')
    pdf.set_font("Arial", size=9)
    pdf.cell(0, 5, f"Planilla de Despacho - {datetime.datetime.now().strftime('%Y-%m-%d')}", ln=True, align='C')
    pdf.ln(5)
    pdf.cell(0, 8, f"Responsable: {mensajero}", ln=True)
    pdf.ln(2)
    
    # Encabezados
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(10, 8, "#", 1, 0, 'C', True)
    pdf.cell(50, 8, "Guia / Tracking", 1, 0, 'C', True)
    pdf.cell(60, 8, "Firma Recibido", 1, 1, 'C', True)
    
    for i, g in enumerate(guias, 1):
        pdf.cell(10, 8, str(i), 1)
        pdf.cell(50, 8, str(g), 1)
        pdf.cell(60, 8, "", 1, 1)
    
    return pdf.output(dest='S').encode('latin-1')

# --- 4. INTERFAZ OPERATIVA ---

st.title("📦 ENMILLA ERP - Control Logístico")
tabs = st.tabs(["📥 Recepción", "🛵 Despacho", "⚙️ Configuración"])

with tabs[0]: # RECEPCIÓN
    st.subheader("Ingreso de Mercancía (Pistola)")
    # El placeholder debe coincidir EXACTAMENTE con el del script JS
    input_guia = st.text_input("ESCANEAR", placeholder="SCAN_INPUT", key=f"p_{st.session_state.key_pistola}")
    inyectar_foco_corregido("SCAN_INPUT")
    
    if input_guia:
        guia = input_guia.strip().upper()
        if guia in st.session_state.db_inventario['Guia'].values:
            st.error(f"La guía {guia} ya fue ingresada.")
        else:
            cli = motor_regex(guia)
            nuevo = pd.DataFrame([{"Fecha": datetime.datetime.now(), "Guia": guia, "Cliente": cli, "Estado": "BODEGA"}])
            st.session_state.db_inventario = pd.concat([st.session_state.db_inventario, nuevo], ignore_index=True)
            st.session_state.key_pistola += 1
            st.toast(f"Registrado: {cli}")
            st.rerun()

with tabs[1]: # DESPACHO
    st.subheader("Salida a Ruta")
    if st.session_state.db_mensajeros.empty:
        st.warning("Debe registrar mensajeros en Configuración.")
    else:
        mensajero = st.selectbox("Seleccione Mensajero", st.session_state.db_mensajeros['Nombre'])
        guias_bodega = st.session_state.db_inventario[st.session_state.db_inventario['Estado'] == "BODEGA"]['Guia']
        seleccion = st.multiselect("Guías para despacho", guias_bodega)
        
        if st.button("Generar Planilla y Despachar"):
            if seleccion:
                pdf_data = generar_planilla_pdf(mensajero, seleccion)
                st.download_button("Descargar Planilla PDF", pdf_data, f"Ruta_{mensajero}.pdf")
                st.session_state.db_inventario.loc[st.session_state.db_inventario['Guia'].isin(seleccion), 'Estado'] = "DESPACHADO"
                st.success("Despacho procesado exitosamente.")
            else:
                st.error("Seleccione al menos una guía.")

with tabs[2]: # CONFIG
    st.subheader("Configuración Maestra")
    c1, c2 = st.columns(2)
    with c1:
        with st.form("f_mens", clear_on_submit=True):
            st.write("Registrar Mensajero")
            n = st.text_input("Nombre"); v = st.text_input("Placa")
            if st.form_submit_button("Guardar"):
                st.session_state.db_mensajeros = pd.concat([st.session_state.db_mensajeros, pd.DataFrame([{"Nombre": n, "Vehiculo": v}])], ignore_index=True)
                st.rerun()
    with c2:
        with st.form("f_cli", clear_on_submit=True):
            st.write("Configurar Cliente Regex")
            cn = st.text_input("Nombre Cliente (Ej: Amazon)"); cr = st.text_input("Regex (Ej: ^AMZ)")
            if st.form_submit_button("Añadir"):
                st.session_state.db_clientes = pd
