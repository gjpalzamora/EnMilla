import streamlit as st
import pandas as pd
import datetime
import re
import os
from fpdf import FPDF
import streamlit.components.v1 as components

# --- 1. CONFIGURACIÓN DE SEGURIDAD Y PERSISTENCIA ---
st.set_page_config(page_title="Enmilla ERP v1.0", layout="wide", page_icon="📦")

# Inicialización robusta para evitar "KeyError" o pantallas en blanco
def inicializar_sistema():
    tablas = {
        'db_inventario': ["Fecha_Ingreso", "Guia", "Cliente", "Estado", "Ubicacion"],
        'db_mensajeros': ["Nombre", "Cedula", "Vehiculo", "Activo"],
        'db_clientes': ["Nombre", "NIT", "Regex_Pattern"],
        'db_despachos': ["Fecha_Salida", "Guia", "Mensajero", "Planilla_ID"]
    }
    for tabla, columnas in tablas.items():
        if tabla not in st.session_state:
            st.session_state[tabla] = pd.DataFrame(columns=columnas)
    
    if 'iteracion' not in st.session_state:
        st.session_state.iteracion = 0

inicializar_sistema()

# --- 2. MOTOR DE IDENTIFICACIÓN Y LÓGICA DE ESTADOS ---

def identificar_cliente_automático(guia):
    """Busca coincidencias Regex en la base de clientes"""
    if st.session_state.db_clientes.empty:
        return "SIN_CLIENTE_CONFIGURADO"
    
    for _, cliente in st.session_state.db_clientes.iterrows():
        try:
            if re.match(cliente['Regex_Pattern'], guia):
                return cliente['Nombre']
        except Exception:
            continue
    return "CLIENTE_DESCONOCIDO"

def inyectar_foco_pistola(target_placeholder):
    """Garantiza que el cursor nunca se pierda (indispensable en bodega)"""
    components.html(f"""
        <script>
            const mantenerFoco = () => {{
                const inputs = window.parent.document.querySelectorAll('input[type="text"]');
                for (let i of inputs) {{
                    if (i.getAttribute('placeholder') === '{target_placeholder}') {{
                        if (window.parent.document.activeElement !== i) i.focus();
                        break;
                    }}
                }}
            }};
            setInterval(mantenerFoco, 500);
        </script>
    """, height=0)

# --- 3. GENERADOR DE PLANILLAS PDF (MEDIA CARTA PROFESIONAL) ---

class PlanillaEnmilla(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 8, 'ENMILLA - ENLACES SOLUCIONES LOGÍSTICAS SAS', ln=True, align='C')
        self.set_font('Arial', '', 8)
        self.cell(0, 4, 'NIT: 901.939.284-4 | Operador Logístico 3PL', ln=True, align='C')
        self.ln(5)

def generar_pdf_despacho(mensajero, vehiculo, guias_lista):
    pdf = PlanillaEnmilla(format=(140, 216)) # Media Carta
    pdf.add_page()
    pdf.set_font('Arial', 'B', 9)
    pdf.cell(0, 6, f"PLANILLA: {datetime.datetime.now().strftime('%Y%m%d-%H%M')}", ln=True)
    pdf.cell(0, 6, f"MENSAJERO: {mensajero} | VEHÍCULO: {vehiculo}", ln=True)
    pdf.ln(4)
    
    # Tabla de Guías
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font('Arial', 'B', 8)
    pdf.cell(10, 7, '#', 1, 0, 'C', True)
    pdf.cell(50, 7, 'Guía / Tracking', 1, 0, 'C', True)
    pdf.cell(60, 7, 'Observación / Firma', 1, 1, 'C', True)
    
    pdf.set_font('Arial', '', 8)
    for i, g in enumerate(guias_lista, 1):
        pdf.cell(10, 7, str(i), 1)
        pdf.cell(50, 7, str(g), 1)
        pdf.cell(60, 7, '________________________', 1, 1)
    
    pdf.ln(10)
    pdf.set_font('Arial', 'I', 7)
    pdf.multi_cell(0, 4, "Declaro recibir las unidades anteriores en perfecto estado para su distribución.")
    return pdf.output(dest='S').encode('latin-1')

# --- 4. INTERFAZ Y FLUJO DE TRABAJO ---

st.markdown(f"### 📦 ENMILLA ERP | Gestión 3PL")
tabs = st.tabs(["📊 Dashboard", "📥 Recepción", "🛵 Despacho", "⚙️ Admin"])

# MÓDULO RECEPCIÓN: Control de Duplicados e Identificación
with tabs[1]:
    st.subheader("Captura de Ingresos")
    input_scan = st.text_input("ESCANEE GUÍA", placeholder="SCAN_RECEPCION", key=f"rec_{st.session_state.iteracion}")
    inyectar_foco_pistola("SCAN_RECEPCION")
    
    if input_scan:
        guia_limpia = input_scan.strip()
        # Validación de duplicados (Error común en bodega)
        if guia_limpia in st.session_state.db_inventario['Guia'].values:
            st.error(f"⚠️ ERROR: La guía {guia_limpia} ya fue ingresada previamente.")
        else:
            cliente = identificar_cliente_automático(guia_limpia)
            nuevo_p = pd.DataFrame([{
                "Fecha_Ingreso": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                "Guia": guia_limpia,
                "Cliente": cliente,
                "Estado": "BODEGA",
                "Ubicacion": "BODEGA_PPAL"
            }])
            st.session_state.db_inventario = pd.concat([st.session_state.db_inventario, nuevo_p], ignore_index=True)
            st.toast(f"✅ Ingreso Exitoso: {cliente}")
            st.session_state.iteracion += 1
            st.rerun()

# MÓDULO DESPACHO: Vinculación de Custodia
with tabs[2]:
    st
