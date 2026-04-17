import streamlit as st
import sys
import os

# Configuración de rutas para detectar la carpeta 'centro'
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

try:
    # Estas son las importaciones que fallaban en la línea 9
    from centro.database import engine, SessionLocal, Base
    from centro.models import Package, Movement, Courier
except Exception as e:
    st.error(f"Error crítico al cargar módulos: {e}")
    st.stop()

from datetime import datetime

# Configuración de interfaz según el Documento de Especificaciones [cite: 294, 433]
st.set_page_config(page_title="Enmilla ERP - Logística", layout="wide")

# Inicialización de la base de datos [cite: 305]
Base.metadata.create_all(bind=engine)

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
                st.warning("Complete los campos obligatorios.")

# --- MÓDULO DE SEGUIMIENTO [cite: 376] ---
elif menu == "Seguimiento":
    st.header("🔍 Seguimiento de Paquetes")
    search_id = st.text_input("Ingrese Número de Seguimiento")
    if search_id:
        pkg = db.query(Package).filter(Package.tracking_number == search_id).first()
        if pkg:
            st.write(f"**Estado:** {pkg.status}")
            st.write(f"**Destinatario:** {pkg.recipient_name}")
            st.subheader("Historial")
            for mov in pkg.movements:
                st.write(f"{mov.movement_time.strftime('%Y-%m-%d')} - {mov.location}")
        else:
            st.error("Paquete no encontrado.")

# --- MÓDULO DE DESPACHO [cite: 385] ---
elif menu == "Despacho":
    st.header("🚚 Gestión de Despacho")
    track_num = st.text_input("Número de Seguimiento para Entrega")
    if track_num:
        pkg = db.query(Package).filter(Package.tracking_number == track_num).first()
        if pkg:
            if st.button("Marcar como Entregado"):
                pkg.status = "Entregado"
                pkg.is_delivered = True
                db.commit()
                st.success("Estado actualizado a Entregado.")
        else:
            st.error("Paquete no encontrado.")

# --- MÓDULO DE MENSAJEROS [cite: 408] ---
elif menu == "Mensajeros":
    st.header("👤 Gestión de Mensajeros")
    with st.form("nuevo_mensajero"):
        m_name = st.text_input("Nombre Completo*")
        if st.form_submit_button("Registrar"):
            if m_name:
                db.add(Courier(name=m_name))
                db.commit()
                st.success(f"Mensajero {m_name} registrado.")

db.close()
