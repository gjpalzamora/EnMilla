import streamlit as st
import sys
import os

# Agrega la ruta actual al path de Python para encontrar la carpeta 'centro'
actual_path = os.path.dirname(os.path.abspath(__file__))
if actual_path not in sys.path:
    sys.path.append(actual_path)

try:
    # Importación directa desde el paquete 'centro'
    from centro.database import engine, SessionLocal, Base
    from centro.models import Package, Movement, Courier
except Exception as e:
    st.error(f"Error crítico de configuración: {e}")
    st.info("Verifica que la carpeta 'centro' contenga el archivo __init__.py vacío.")
    st.stop()

# Inicialización de base de datos y configuración
Base.metadata.create_all(bind=engine)
st.set_page_config(page_title="EnMilla ERP", layout="wide")

st.sidebar.title("EnMilla ERP")
menu = st.sidebar.radio("Navegación", ["Recepción", "Seguimiento", "Despacho", "Mensajeros"])

db = SessionLocal()

# --- LÓGICA DE MÓDULOS ---
if menu == "Recepción":
    st.header("📦 Registro de Paquetes")
    with st.form("reg_form"):
        t_num = st.text_input("Guía / Tracking*")
        dest = st.text_input("Destinatario*")
        if st.form_submit_button("Guardar"):
            if t_num and dest:
                new_p = Package(tracking_number=t_num, recipient_name=dest, status="Recibido")
                db.add(new_p)
                db.commit()
                st.success("Registrado correctamente.")
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

db.close()
