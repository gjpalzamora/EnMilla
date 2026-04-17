import streamlit as st
import sys
import os

# FORZAR RUTA: Esto resuelve el error 'No module named database'
sys.path.append(os.path.join(os.path.dirname(__file__), 'centro'))

try:
    from database import engine, SessionLocal, Base
    from models import Package, Courier
except ImportError as e:
    st.error(f"Error Técnico: No se encontraron los archivos en la carpeta 'centro'. Detalle: {e}")
    st.stop()

# Configuración de EnMilla ERP
st.set_page_config(page_title="EnMilla ERP - Logística", layout="wide")

# Crear tablas si no existen
Base.metadata.create_all(bind=engine)

st.title("🚚 EnMilla ERP")
st.sidebar.header("Control de Operaciones")
menu = st.sidebar.radio("Módulos", ["Recepción", "Seguimiento", "Despacho"])

db = SessionLocal()

if menu == "Recepción":
    st.subheader("📦 Registro de Mercancía")
    with st.form("registro"):
        guia = st.text_input("Número de Guía*")
        cliente = st.text_input("Destinatario*")
        if st.form_submit_button("Registrar"):
            if guia and cliente:
                nuevo = Package(tracking_number=guia, recipient_name=cliente)
                db.add(nuevo)
                db.commit()
                st.success(f"Guía {guia} registrada en sistema.")
            else:
                st.warning("Datos incompletos.")

elif menu == "Seguimiento":
    st.subheader("🔍 Localización de Guías")
    busqueda = st.text_input("Ingrese Guía")
    if busqueda:
        res = db.query(Package).filter(Package.tracking_number == busqueda).first()
        if res:
            st.info(f"Estado: {res.status} | Cliente: {res.recipient_name}")
        else:
            st.error("Guía no encontrada.")

db.close()
