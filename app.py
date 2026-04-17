import streamlit as st
import sys
import os

# Fuerza al sistema a reconocer la carpeta 'centro'
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

try:
    from centro.database import engine, SessionLocal, Base
    from centro.models import Package, Movement, Courier
    # from centro.pdf_service import generar_pod_pdf # Descomentar cuando el archivo esté listo
except ModuleNotFoundError as e:
    st.error(f"Error de configuración: No se pudo encontrar el módulo. {e}")
    st.info("Asegúrate de que la carpeta se llame 'centro' y contenga un archivo __init__.py vacío.")
    st.stop()

from datetime import datetime

# Configuración de la página según especificaciones [cite: 436, 461]
st.set_page_config(page_title="Enmilla ERP - Logística", layout="wide")

# Creación automática de tablas al inicio [cite: 305]
Base.metadata.create_all(bind=engine)

# Menú lateral de navegación [cite: 433]
st.sidebar.title("Enmilla ERP")
menu = st.sidebar.radio("Módulos", ["Recepción", "Seguimiento", "Despacho", "Mensajeros"])

db = SessionLocal()

# --- MÓDULO DE RECEPCIÓN [cite: 358] ---
if menu == "Recepción":
    st.header("📦 Registro de Paquetes")
    with st.form("registro_paquete"):
        t_number = st.text_input("Número de Seguimiento (Único)*")
        sender = st.text_input("Nombre del Remitente*")
        recipient = st.text_input("Nombre del Destinatario*")
        address = st.text_area("Dirección del Destinatario*")
        
        if st.form_submit_button("Registrar"):
            if t_number and sender and recipient and address:
                # Validación de duplicados [cite: 374]
                exists = db.query(Package).filter(Package.tracking_number == t_number).first()
                if exists:
                    st.error("Error: El número de seguimiento ya existe.")
                else:
                    new_pkg = Package(
                        tracking_number=t_number,
                        sender_name=sender,
                        recipient_name=recipient,
                        recipient_address=address,
                        status='Recibido' # Estado inicial por defecto [cite: 371]
                    )
                    db.add(new_pkg)
                    db.commit()
                    st.success(f"Paquete {t_number} registrado con éxito.")
            else:
                st.warning("Por favor complete todos los campos obligatorios.")

# --- MÓDULO DE SEGUIMIENTO [cite: 376] ---
elif menu == "Seguimiento":
    st.header("🔍 Seguimiento de Paquetes")
    search_id = st.text_input("Ingrese Número de Seguimiento")
    if search_id:
        pkg = db.query(Package).filter(Package.tracking_number == search_id).first()
        if pkg:
            st.write(f"**Estado Actual:** {pkg.status} [cite: 384]")
            st.write(f"**Destinatario:** {pkg.recipient_name}")
            st.write(f"**Dirección:** {pkg.recipient_address}")
            
            st.subheader("Historial de Movimientos [cite: 381]")
            for mov in pkg.movements:
                st.write(f"{mov.movement_time.strftime('%Y-%m-%d %H:%M')} - {mov.location}: {mov.description}")
        else:
            st.error("Paquete no encontrado.")

# --- MÓDULO DE DESPACHO [cite: 385] ---
elif menu == "Despacho":
    st.header("🚚 Gestión de Despacho y Entrega")
    track_num = st.text_input("Número de Seguimiento para Entrega")
    if track_num:
        pkg = db.query(Package).filter(Package.tracking_number == track_num).first()
        if pkg:
            st.info(f"Paquete seleccionado: {pkg.tracking_number}")
            if st.button("Marcar como Entregado [cite: 391]"):
                pkg.status = "Entregado"
                pkg.is_delivered = True # Actualiza bandera booleana [cite: 394]
                db.commit()
                st.success("Paquete entregado con éxito.")
        else:
            st.error("Paquete no encontrado.")

# --- MÓDULO DE MENSAJEROS [cite: 408] ---
elif menu == "Mensajeros":
    st.header("👤 Gestión de Mensajeros")
    with st.form("nuevo_mensajero"):
        m_name = st.text_input("Nombre Completo* [cite: 411]")
        m_plate = st.text_input("Placa del Vehículo [cite: 413]")
        if st.form_submit_button("Registrar Mensajero"):
            if m_name:
                new_courier = Courier(name=m_name, license_plate=m_plate)
                db.add(new_courier)
                db.commit()
                st.success(f"Mensajero {m_name} registrado.")
            else:
                st.error("El nombre es obligatorio.")

db.close()
