import streamlit as st
from core.database import engine, SessionLocal, Base
from core.models import Package, Movement, Courier
from datetime import datetime

# Ejecuta la creación automática del esquema al inicio [cite: 42]
Base.metadata.create_all(bind=engine)

st.set_page_config(page_title="Enmilla ERP - Logística", layout="wide")

# Menú lateral claro para navegación intuitiva [cite: 170]
st.sidebar.title("Enmilla ERP")
menu = st.sidebar.radio("Módulos", ["Recepción", "Seguimiento", "Despacho", "Mensajeros"])

db = SessionLocal()

# --- MÓDULO DE RECEPCIÓN [cite: 95] ---
if menu == "Recepción":
    st.header("📦 Registro de Paquetes")
    with st.form("registro_paquete"):
        t_number = st.text_input("Número de Seguimiento (Único)*") [cite: 101]
        sender = st.text_input("Nombre del Remitente*") [cite: 102]
        recipient = st.text_input("Nombre del Destinatario*") [cite: 104]
        address = st.text_area("Dirección del Destinatario*") [cite: 105]
        
        if st.form_submit_button("Registrar"):
            if t_number and sender and recipient and address:
                # RF3.1.2. Validación de duplicados [cite: 112]
                exists = db.query(Package).filter(Package.tracking_number == t_number).first()
                if exists:
                    st.error("Error: El número de seguimiento ya existe.") [cite: 172]
                else:
                    new_pkg = Package(
                        tracking_number=t_number,
                        sender_name=sender,
                        recipient_name=recipient,
                        recipient_address=address,
                        status='Recibido' # Status inicial [cite: 108]
                    )
                    db.add(new_pkg)
                    db.commit()
                    st.success(f"Paquete {t_number} registrado con éxito.") [cite: 172]
            else:
                st.warning("Por favor complete los campos obligatorios.")

# --- MÓDULO DE SEGUIMIENTO [cite: 113] ---
elif menu == "Seguimiento":
    st.header("🔍 Seguimiento de Paquetes")
    search = st.text_input("Buscar por Tracking Number") [cite: 116]
    
    if search:
        pkg = db.query(Package).filter(Package.tracking_number == search).first()
        if pkg:
            st.subheader(f"Detalles del Paquete: {pkg.tracking_number}")
            st.write(f"**Estado Actual:** {pkg.status}") [cite: 121]
            st.write(f"**Destinatario:** {pkg.recipient_name}")
            st.write(f"**Dirección:** {pkg.recipient_address}")
        else:
            st.error("Paquete no encontrado.")

# --- MÓDULO DE MENSAJEROS [cite: 145] ---
elif menu == "Mensajeros":
    st.header("👤 Gestión de Mensajeros")
    with st.expander("Registrar Nuevo Mensajero"):
        m_name = st.text_input("Nombre Completo*") [cite: 148]
        m_plate = st.text_input("Placa del Vehículo") [cite: 150]
        if st.button("Guardar Mensajero"):
            new_courier = Courier(name=m_name, license_plate=m_plate)
            db.add(new_courier)
            db.commit()
            st.success("Mensajero registrado.")

    st.subheader("Lista de Mensajeros Activos") [cite: 153, 155]
    couriers = db.query(Courier).filter(Courier.is_active == True).all()
    for c in couriers:
        st.text(f"ID: {c.id} | {c.name} - Placa: {c.license_plate}")

db.close()
