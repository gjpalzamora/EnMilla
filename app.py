import streamlit as st
from database import engine, SessionLocal, Base
from models import Package, Movement, Courier
from datetime import datetime

# Configuración inicial de la página
st.set_page_config(page_title="EnMilla ERP", layout="wide")

# Creación automática de las tablas en la base de datos
Base.metadata.create_all(bind=engine)

st.sidebar.title("EnMilla ERP")
menu = st.sidebar.radio("Navegación", ["Recepción", "Seguimiento", "Despacho", "Mensajeros"])

db = SessionLocal()

# --- MÓDULO DE RECEPCIÓN ---
if menu == "Recepción":
    st.header("📦 Registro de Paquetes")
    with st.form("reg_form"):
        t_num = st.text_input("Número de Guía (Tracking)*")
        dest = st.text_input("Nombre del Destinatario*")
        addr = st.text_area("Dirección de Entrega*")
        if st.form_submit_button("Registrar Paquete"):
            if t_num and dest and addr:
                new_p = Package(tracking_number=t_num, recipient_name=dest, 
                                recipient_address=addr, status="Recibido")
                db.add(new_p)
                db.commit()
                st.success(f"Paquete {t_num} registrado con éxito.")
            else:
                st.warning("Por favor, complete los campos obligatorios.")

# --- MÓDULO DE SEGUIMIENTO ---
elif menu == "Seguimiento":
    st.header("🔍 Consultar Estado")
    search = st.text_input("Ingrese el Número de Guía")
    if search:
        p = db.query(Package).filter(Package.tracking_number == search).first()
        if p:
            st.info(f"Estado actual: {p.status}")
            st.write(f"Destinatario: {p.recipient_name}")
            st.write(f"Dirección: {p.recipient_address}")
        else:
            st.error("No se encontró ningún paquete con ese número.")

# --- MÓDULO DE DESPACHO ---
elif menu == "Despacho":
    st.header("🚚 Gestión de Despacho")
    t_id = st.text_input("Tracking para marcar como entregado")
    if t_id:
        p = db.query(Package).filter(Package.tracking_number == t_id).first()
        if p and st.button("Confirmar Entrega"):
            p.status = "Entregado"
            db.commit()
            st.success("El paquete ha sido marcado como Entregado.")

db.close()
