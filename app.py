import streamlit as st
from core.database import engine, SessionLocal, Base
from core.models import Package, Movement, Courier
from centro.pdf_service import generar_pod_pdf  # Asegúrate de que el nombre de la carpeta sea core o centro
from datetime import datetime

# Ejecuta la creación automática del esquema al inicio [cite: 42]
Base.metadata.create_all(bind=engine)

st.set_page_config(page_title="Enmilla ERP - Logística", layout="wide")

# Menú lateral para navegación [cite: 170]
st.sidebar.title("Enmilla ERP")
menu = st.sidebar.radio("Módulos", ["Recepción", "Seguimiento", "Despacho", "Mensajeros"])

db = SessionLocal()

# --- MÓDULO DE RECEPCIÓN [cite: 95] ---
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
                st.warning("Por favor complete los campos obligatorios.")

# --- MÓDULO DE SEGUIMIENTO [cite: 113] ---
elif menu == "Seguimiento":
    st.header("🔍 Seguimiento de Paquetes")
    search = st.text_input("Buscar por Tracking Number")
    
    if search:
        pkg = db.query(Package).filter(Package.tracking_number == search).first()
        if pkg:
            st.subheader(f"Detalles del Paquete: {pkg.tracking_number}")
            st.write(f"**Estado Actual:** {pkg.status}")
            st.write(f"**Destinatario:** {pkg.recipient_name}")
            st.write(f"**Dirección:** {pkg.recipient_address}")
            
            # Mostrar historial de movimientos [cite: 118, 119]
            st.write("---")
            st.write("**Historial de Movimientos:**")
            for mov in pkg.movements:
                st.write(f"- {mov.movement_time.strftime('%Y-%m-%d %H:%M')}: {mov.description} ({mov.location})")
        else:
            st.error("Paquete no encontrado.")

# --- MÓDULO DE DESPACHO Y ENTREGA [cite: 122] ---
elif menu == "Despacho":
    st.header("🚚 Gestión de Despacho y Entrega")
    t_num = st.text_input("Ingrese Tracking Number para gestionar")
    
    if t_num:
        pkg = db.query(Package).filter(Package.tracking_number == t_num).first()
        if pkg:
            st.info(f"Estado Actual: {pkg.status}")
            
            couriers = db.query(Courier).filter(Courier.is_active == True).all()
            c_options = {c.name: c.id for c in couriers}
            sel_courier = st.selectbox("Asignar Mensajero", options=list(c_options.keys()))
            
            nuevo_estado = st.selectbox("Cambiar Estado a:", ["En Tránsito", "Entregado", "Incidencia"])
            
            if st.button("Actualizar Estado"):
                # RF3.3.2. Marcar como entregado [cite: 128, 131]
                if nuevo_estado == "Entregado":
                    pkg.is_delivered = True
                    pkg.status = "Entregado"
                else:
                    pkg.status = nuevo_estado
                
                # Registrar movimiento [cite: 126]
                nuevo_mov = Movement(
                    package_id=pkg.id,
                    location="Punto de Operación",
                    description=f"Estado actualizado a {nuevo_estado} con mensajero {sel_courier}"
                )
                db.add(nuevo_mov)
                db.commit()
                st.success(f"Estado actualizado a {nuevo_estado}")
                
                # Generar POD si es entregado [cite: 138, 143]
                if nuevo_estado == "Entregado":
                    pdf_data = generar_pod_pdf(pkg, sel_courier)
                    st.download_button(
                        label="📥 Descargar Comprobante POD (PDF)",
                        data=pdf_data,
                        file_name=f"POD_{pkg.tracking_number}.pdf",
                        mime="application/pdf"
                    )
        else:
            st.error("Paquete no encontrado.")

# --- MÓDULO DE MENSAJEROS [cite: 145] ---
elif menu == "Mensajeros":
    st.header("👤 Gestión de Mensajeros")
    with st.expander("Registrar Nuevo Mensajero"):
        m_name = st.text_input("Nombre Completo*")
        m_plate = st.text_input("Placa del Vehículo")
        if st.button("Guardar Mensajero"):
            new_courier = Courier(name=m_name, license_plate=m_plate)
            db.add(new_courier)
            db.commit()
            st.success("Mensajero registrado.")

    st.subheader("Lista de Mensajeros Activos")
    couriers = db.query(Courier).filter(Courier.is_active == True).all()
    for c in couriers:
        st.text(f"ID: {c.id} | {c.name} - Placa: {c.license_plate}")

db.close()
