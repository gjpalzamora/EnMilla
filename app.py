import streamlit as st
from db_models import get_db, create_tables, Courier
from logica_operativa import procesar_escaneo
from admin_module import display_admin_module

# Configuración EnMilla
st.set_page_config(page_title="EnMilla - Enlaces Soluciones Logísticas", layout="wide")

# Encabezado de Empresa
st.sidebar.image("https://raw.githubusercontent.com/gjpalzamora/enmilla/main/log%20fondo%20blancojpg.jpg", width=200)
st.sidebar.markdown("### **Enlaces Soluciones Logísticas SAS**")
st.sidebar.markdown("**NIT:** 901.939.284-4")
st.sidebar.markdown("**Sede:** Bogotá, Colombia")

try:
    db = next(get_db())
    create_tables()
except Exception as e:
    st.error("Error al conectar con la base de datos.")
    st.stop()

menu = st.sidebar.radio("Menú Principal:", ["Administración", "Recepción (Ingreso)", "Despacho (Salida)"])

if menu == "Administración":
    display_admin_module(db)

elif menu == "Recepción (Ingreso)":
    st.title("📥 Recepción EnMilla")
    with st.form("scan_form", clear_on_submit=True):
        guia = st.text_input("ESCANEAR GUÍA:")
        if st.form_submit_button("Procesar"):
            res = procesar_escaneo(db, guia, "Admin", "INGRESO")
            if res["status"] == "OK": st.success(res["message"])
            else: st.error(res["message"])

elif menu == "Despacho (Salida)":
    st.title("🚚 Despacho y Rutas")
    mensajeros = db.query(Courier).all()
    if mensajeros:
        m_map = {m.name: m.id for m in mensajeros}
        sel_m = st.selectbox("Mensajero:", options=list(m_map.keys()))
        with st.form("out_form", clear_on_submit=True):
            guia_out = st.text_input("GUÍA PARA RUTA:")
            if st.form_submit_button("Despachar"):
                res = procesar_escaneo(db, guia_out, "Admin", "DESPACHO", mensajero_id=m_map[sel_m])
                if res["status"] == "OK": st.success(res["message"])
                else: st.warning(res["message"])
    else:
        st.warning("Debe registrar mensajeros en Administración.")

db.close()
