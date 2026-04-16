import streamlit as st
import pandas as pd
import datetime
import re
import io
from fpdf import FPDF
import streamlit.components.v1 as components

# --- 1. CONFIGURACIÓN DE SEGURIDAD Y ESTADO ---
st.set_page_config(page_title="Enmilla ERP v1.1", layout="wide", page_icon="📦")

def robust_init():
    """Inicialización profunda para prevenir errores de 'KeyError'"""
    config = {
        'db_inventario': ["Fecha_Ingreso", "Guia", "Cliente", "Estado", "Ubicacion", "Peso"],
        'db_mensajeros': ["Nombre", "Cedula", "Vehiculo", "Activo"],
        'db_clientes': ["Nombre", "NIT", "Regex_Pattern"],
        'db_log_movimientos': ["Timestamp", "Guia", "De_Estado", "A_Estado", "Responsable"]
    }
    for tabla, columnas in config.items():
        if tabla not in st.session_state:
            st.session_state[tabla] = pd.DataFrame(columns=columnas)
    
    if 'scan_count' not in st.session_state:
        st.session_state.scan_count = 0

robust_init()

# --- 2. MOTOR LOGÍSTICO (REGLAS DE NEGOCIO) ---

def registrar_movimiento(guia, de_est, a_est, responsable):
    """Auditoría obligatoria de cada cambio de estado"""
    nuevo_log = pd.DataFrame([{
        "Timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Guia": guia,
        "De_Estado": de_est,
        "A_Estado": a_est,
        "Responsable": responsable
    }])
    st.session_state.db_log_movimientos = pd.concat([st.session_state.db_log_movimientos, nuevo_log], ignore_index=True)

def motor_identificacion(guia):
    """Regex dinámico para identificación 3PL"""
    for _, cli in st.session_state.db_clientes.iterrows():
        try:
            if re.match(cli['Regex_Pattern'], guia, re.IGNORECASE):
                return cli['Nombre']
        except: continue
    return "DESCONOCIDO"

def inyectar_foco_perpetuo(placeholder_id):
    """Script para que la pistola siempre tenga donde escribir"""
    components.html(f"""
        <script>
            function setFocus() {{
                const inputs = window.parent.document.querySelectorAll('input[type="text"]');
                for (let i of inputs) {{
                    if (i.getAttribute('placeholder') === '{placeholder_id}') {{
                        if (window.parent.document.activeElement !== i) i.focus();
                        break;
                    }}
                }}
            }}
            setInterval(setFocus, 400);
        </script>
    """, height=0)

# --- 3. DISEÑO DE PLANILLA LEGAL (PDF MEDIA CARTA) ---

class PlanillaLegal(FPDF):
    def header(self):
        # Datos según User Summary
        self.set_font('Arial', 'B', 11)
        self.cell(0, 7, 'ENLACES SOLUCIONES LOGÍSTICAS SAS', ln=True, align='C')
        self.set_font('Arial', '', 8)
        self.cell(0, 4, 'NIT: 901.939.284-4 | San Martin, Bogotá', ln=True, align='C')
        self.ln(5)

def crear_acta_entrega(mensajero, placa, guias):
    pdf = PlanillaLegal(format=(140, 216)) # Formato Media Carta
    pdf.add_page()
    pdf.set_font('Arial', 'B', 9)
    pdf.cell(0, 6, f"PLANILLA N°: {datetime.datetime.now().strftime('%m%d%H%M')}", ln=True)
    pdf.cell(0, 6, f"RESPONSABLE: {mensajero} | PLACA: {placa}", ln=True)
    pdf.ln(3)
    
    # Tabla con bordes reforzados
    pdf.set_fill_color(230, 240, 255)
    pdf.cell(10, 7, '#', 1, 0, 'C', True)
    pdf.cell(50, 7, 'Guía de Transporte', 1, 0, 'C', True)
    pdf.cell(60, 7, 'Firma / Novedad', 1, 1, 'C', True)
    
    pdf.set_font('Arial', '', 8)
    for i, g in enumerate(guias, 1):
        pdf.cell(10, 7, str(i), 1)
        pdf.cell(50, 7, str(g), 1)
        pdf.cell(60, 7, '', 1, 1)
    
    pdf.ln(8)
    pdf.set_font('Arial', 'I', 7)
    pdf.multi_cell(0, 4, "Nota: El mensajero declara recibir la mercancía en buen estado y se compromete a la entrega efectiva.")
    return pdf.output(dest='S').encode('latin-1')

# --- 4. INTERFAZ OPERATIVA ---

st.title("📦 ENMILLA ERP v1.1")
menu = st.tabs(["📉 Monitor", "📥 Ingreso (Pistola)", "🛵 Despacho (Ruta)", "⚙️ Config"])

# TAB INGRESO: Blindado contra duplicados
with menu[1]:
    st
