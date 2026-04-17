import streamlit as st
import sys
import os

# ESTA LÍNEA ES LA SOLUCIÓN: Agrega el directorio actual al buscador de Python
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

try:
    # Ahora el sistema encontrará 'centro' sin problemas
    from centro.database import engine, SessionLocal, Base
    from centro.models import Package, Movement, Courier
except Exception as e:
    st.error(f"Error crítico al cargar módulos: {e}")
    st.stop()

from datetime import datetime

# Configuración de la interfaz
st.set_page_config(page_title="EnMilla ERP - Logística", layout="wide")

# Crear tablas si no existen
Base.metadata.create_all(bind=engine)

st.sidebar.title("EnMilla ERP")
menu = st.sidebar.radio("Módulos", ["Recepción", "Seguimiento", "Despacho", "Mensajeros"])

db = SessionLocal()

if menu == "Recepción":
    st.header("📦 Registro de Paquetes")
    with st.form("registro"):
        t_num = st.text_input("Número de Seguimiento*")
        sender = st.text_input("Remitente")
        recipient = st.text_input("Destinatario")
        address = st.text_area("Dirección")
        if st.form_submit_button("Registrar"):
            if t_num and sender and recipient and address:
                new_pkg = Package(tracking_number=t_num, sender_name=sender, 
                                  recipient_name=recipient, recipient_address=address)
                db.add(new_pkg)
                db.commit()
                st.success(f"Paquete {t_num} registrado.")
            else:
                st.warning("Faltan datos.")

elif menu == "Seguimiento":
    st.header("🔍 Seguimiento")
    search = st.text_input("Buscar Tracking")
    if search:
        pkg = db.query(Package).filter(Package.tracking_number == search).first()
        if pkg:
            st.write(f"**Estado:** {pkg.status}")
            st.write(f"**Destinatario:** {pkg.recipient_name}")
        else:
            st.error("No encontrado.")

elif menu == "Despacho":
    st.header("🚚 Despacho")
    t_id = st.text_input("Tracking para entrega")
    if t_id:
        pkg = db.query(Package).filter(Package.tracking_number == t_id).first()
        if pkg and st.button("Marcar Entregado"):
            pkg.status = "Entregado"
            db.commit()
            st.success("Paquete Entregado.")

elif menu == "Mensajeros":
    st.header("👤 Mensajeros")
    m_name = st.text_input("Nombre del Mensajero")
    if st.button("Guardar"):
        db.add(Courier(name=m_name))
        db.commit()
        st.success("Registrado.")

db.close()
