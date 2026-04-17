import streamlit as st
from database import engine, SessionLocal, Base
from models import Package, Movement, Courier
# from pdf_service import generar_pod_pdf # Activar cuando el archivo esté listo
from datetime import datetime

# Configuración inicial
st.set_page_config(page_title="EnMilla ERP", layout="wide")
Base.metadata.create_all(bind=engine)

st.sidebar.title("EnMilla ERP")
menu = st.sidebar.radio("Navegación", ["Recepción", "Seguimiento", "Despacho", "Mensajeros"])

db = SessionLocal()

if menu == "Recepción":
    st.header("📦 Registro de Paquetes")
    with st.form("reg_form"):
        t_num = st.text_input("Número de Guía*")
        dest = st.text_input("Destinatario*")
        if st.form_submit_button("Guardar"):
            if t_num and dest:
                new_p = Package(tracking_number=t_num, recipient_name=dest, status="Recibido")
                db.add(new_p)
                db.commit()
                st.success(f"Paquete {t_num} registrado.")
            else:
                st.warning("Completa los campos obligatorios.")

elif menu == "Seguimiento":
    st.header("🔍 Consultar Estado")
    search = st.text_input("Número de Guía")
    if search:
        p = db.query(Package).filter(Package.tracking_number == search).first()
        if p:
            st.info(f"Estado actual: {p.status}")
        else:
            st.error("No se encontró el paquete.")

# ... (puedes añadir el resto de módulos aquí)

db.close()
