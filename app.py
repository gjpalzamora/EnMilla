import streamlit as st
from centro.database import engine, SessionLocal, Base
from centro.models import Package, Movement, Courier
from centro.pdf_service import generar_pod_pdf 
from datetime import datetime

# Ejecuta la creación automática del esquema al inicio
Base.metadata.create_all(bind=engine)

st.set_page_config(page_title="Enmilla ERP - Logística", layout="wide")

# Menú lateral para navegación
st.sidebar.title("Enmilla ERP")
menu = st.sidebar.radio("Módulos", ["Recepción", "Seguimiento", "Despacho", "Mensajeros"])

db = SessionLocal()

# --- MÓDULO DE RECEPCIÓN ---
if menu == "Recepción":
    st.header("📦 Registro de Paquetes")
    with st.form("registro_paquete"):
        t_number = st.text_input("Número de Seguimiento (Único)*")
        sender = st.text_input("Nombre del Remitente*")
        recipient = st.text_input("Nombre del Destinatario*")
        address = st.text_area("Dirección del Destinatario*")
        
        if st.form_submit_button("Registrar"):
            if t_number and sender and recipient and address:
                exists = db.query(Package).filter(Package.tracking_number == t_number).first()
                if exists:
                    st.error("Error: El número de seguimiento ya existe.")
                else:
                    new_pkg = Package(
                        tracking_number=t_number,
                        sender_name=sender,
                        recipient_name=recipient,
                        recipient_address=address,
                        status='Recibido'
                    )
                    db.add(new_pkg)
                    db.commit()
                    st.success(f"Paquete {t_number} registrado con éxito.")
            else:
                st.warning("Por favor complete todos los campos obligatorios.")

# --- MÓDULO DE SEGUIMIENTO ---
elif menu == "Seguimiento":
    st.header("🔍 Seguimiento de Paquetes")
    search_id = st.text_input("Ingrese Número de Seguimiento")
    if search_id:
        pkg = db.query(Package).filter(Package.tracking_number == search_id).first()
        if pkg:
            st.write(f"**Estado Actual:** {pkg.status}")
            st.write(f"**Destinatario:** {pkg.recipient_name}")
            st.write(f"**Dirección:** {pkg.recipient_address}")
            
            st.subheader("Historial de Movimientos")
            for mov in pkg.movements:
                st.write(f"{mov.movement_time.strftime('%Y-%m-%d %H:%M')} - {mov.location}: {mov.description}")
        else:
            st.error("Paquete no encontrado.")

# --- MÓDULO DE DESPACHO ---
elif menu == "Despacho":
    st.header("🚚 Gestión de Despacho y POD")
    track_num = st.text_input("Número de Seguimiento para Entrega")
    if track_num:
        pkg = db.query(Package).filter(Package.tracking_number == track_num).first()
        if pkg:
            st.info(f"Paquete seleccionado: {pkg.tracking_number}")
            if st.button("Marcar como Entregado y Generar POD"):
                pkg.status = "Entregado"
                pkg.is_delivered = True
                db.commit()
                # Aquí se llamaría a generar_pod_pdf(pkg)
                st.success("Paquete entregado. Comprobante (POD) generado.")
        else:
            st.error("Paquete no encontrado.")

# --- MÓDULO DE MENSAJEROS ---
elif menu == "Mensajeros":
    st.header("👤 Gestión de Mensajeros")
    with st.form("nuevo_mensajero"):
        m_name = st.text_input("Nombre Completo*")
        m_plate = st.text_input("Placa del Vehículo")
        if st.form_submit_button("Registrar Mensajero"):
            if m_name:
                new_courier = Courier(name=m_name, license_plate=m_plate)
                db.add(new_courier)
                db.commit()
                st.success(f"Mensajero {m_name} registrado.")
            else:
                st.error("El nombre es obligatorio.")

db.close()
