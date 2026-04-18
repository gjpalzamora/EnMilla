from fpdf import FPDF
from datetime import datetime

def generar_pod_pdf(package_data, courier_name):
    pdf = FPDF()
    pdf.add_page()
    
    # Encabezado
    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, txt="Comprobante de Entrega (POD)", ln=True, align='C')
    pdf.ln(10)
    
    # Información del Paquete [cite: 140]
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Guía: {package_data.tracking_number}", ln=True)
    pdf.cell(200, 10, txt=f"Remitente: {package_data.sender_name}", ln=True)
    pdf.cell(200, 10, txt=f"Destinatario: {package_data.recipient_name}", ln=True)
    pdf.cell(200, 10, txt=f"Dirección: {package_data.recipient_address}", ln=True)
    
    # Detalles de la Entrega [cite: 141]
    pdf.ln(5)
    pdf.cell(200, 10, txt=f"Fecha de Entrega: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=True)
    pdf.cell(200, 10, txt=f"Entregado por: {courier_name}", ln=True)
    
    # Espacio para firma [cite: 142]
    pdf.ln(20)
    pdf.cell(200, 10, txt="__________________________", ln=True)
    pdf.cell(200, 10, txt="Firma del Receptor", ln=True)
    
    return pdf.output(dest='S').encode('latin-1')
