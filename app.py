import streamlit as st
import pandas as pd
import datetime
import re
from fpdf import FPDF
import streamlit.components.v1 as components

# --- 1. CONFIGURACIÓN Y ESTADO DE SESIÓN ---
st.set_page_config(page_title="Enmilla ERP", layout="wide", page_icon="📦")

# Bases de datos temporales (En producción conectar a PostgreSQL)
for key, cols in {
    'db_inventario': ["Fecha", "Guia", "Cliente", "Estado"],
    'db_mensajeros': ["Nombre", "Vehiculo", "ID"],
    'db_clientes': ["Nombre", "Regex", "NIT"]
}.items():
    if key not in st.session_state:
        st.session_state[key] = pd.DataFrame(columns=cols)

if 'iteracion' not in st.session_state:
    st.session_state.iteracion = 0

# --- 2. MOTOR DE INTELIGENCIA LOGÍSTICA ---

def identificar_cliente(guia):
    """Identifica el cliente basado en patrones de texto (Regex)"""
    for _, row in st.session_state.db_clientes.iterrows():
        if re.match(row['Regex'], guia):
            return row['Nombre']
    return "Cliente Genérico / Desconocido"

def script_foco_pistola(placeholder):
    """Mantiene el cursor activo para escaneo continuo sin usar el mouse"""
    components.html(f"""
        <script>
            const focusInput = () => {{
                const inputs = window.parent.document.querySelectorAll('input[type="text"]');
                for (let i of inputs) {{
                    if (i.getAttribute('placeholder') === '{placeholder}') {{
                        if (window.parent.document.activeElement !== i) i.focus();
                        break;
                    }}
                }}
            }};
            focusInput();
            const obs = new MutationObserver(focusInput);
            obs.observe(window.parent.document.body, {{childList: true, subtree: true}});
        </script>
    """, height=0)

# --- 3. GENERADOR DE PDF (MEDIA CARTA) ---

class PlanillaPDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 8, 'ENMILLA - ENLACES SOLUCIONES LOGÍSTICAS SAS', ln=True, align='C')
        self.set_font('Arial', '', 8)
        self.cell(0, 4, 'NIT: 901.939.284-4 | Planilla de Despacho 3PL', ln=True, align='C')
        self.ln(5)

def generar_pdf(mensajero, guias):
    pdf = PlanillaPDF(format=(140, 216)) # Media Carta
    pdf.add_page()
    pdf.set_font('Arial', 'B', 9)
    pdf.cell(0, 6, f"MENSAJERO: {mensajero} | FECHA: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=True)
    pdf.ln(4)
    # Tabla
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(10, 7, "#", 1, 0, 'C', True)
    pdf.cell(50, 7, "Número de Guía", 1, 0, 'C', True)
    pdf.cell(60, 7, "Firma de Recibido", 1, 1, 'C', True)
    pdf.set_font('Arial', '', 8)
    for i, g in enumerate(guias, 1):
        pdf.cell(10, 7, str(i), 1)
        pdf.cell(50, 7, g, 1)
        pdf.cell(60, 7, "", 1, 1)
    return pdf.output(dest='S').encode('latin-1')

# --- 4. INTERFAZ DE USUARIO ---

st.title("📦 Sistema Enmilla ERP")
tabs = st.tabs(["📊 Dashboard", "📥 Recepción (Ingreso)", "🛵 Despacho (Salida)", "⚙️ Administración"])

# MODULO: RECEPCIÓN
with tabs[1]:
    st.subheader("Ingreso de Mercancía por Escaneo")
    guia_in = st.text_input("ESCANEAR UNIDAD", placeholder="INPUT_BODEGA", key=f"in_{st.session_state.iteracion}")
    script_foco_pistola("INPUT_BODEGA")
    
    if guia_in:
        cliente = identificar_cliente(guia_in)
        nuevo = pd.DataFrame([{"Fecha": datetime.datetime.now(), "Guia": guia_in, "Cliente": cliente, "Estado": "BODEGA"}])
        st.session_state.db_inventario = pd.concat([st.session_state.db_inventario, nuevo], ignore_index=True)
        st.session_state.iteracion += 1
        st.toast(f"✅ Registrada: {guia_in} ({cliente})")
        st.rerun()

# MODULO: DESPACHO
with tabs[2]:
    st.subheader("Asignación a Mensajeros")
