import streamlit as st
from db_models import get_db, create_tables, Courier
from logica_operativa import procesar_escaneo
from admin_module import display_admin_module

st.set_page_config(page_title="EnMilla v2.0", layout="wide")

# Identidad Corporativa
st.sidebar.image("https://raw.githubusercontent.com/gjpalzamora/enmilla/main/log%20fondo%20blancojpg.jpg", use_container_width=True)
st.sidebar.title("EnMilla")
st.sidebar.info("**Enlaces Soluciones Logísticas SAS**\n\nNIT: 901.939.284-4\n\nBogotá, Colombia")

try:
    db = next(get_db())
    create_tables()
except Exception as e:
    st.error("Error al inicializar la base de datos.")
    st.stop()

menu = st.sidebar.radio("Menú:", ["Administración", "Recepción (Ingreso)", "Despacho (Salida)"])

if menu == "Administración":
    display_admin_module(db)
elif menu == "Recepción (Ingreso)":
    st.title("📥 Ingreso")
    with st.form("in", clear_on_submit=True):
        g = st.text_input("Guía:")
        if st.form_submit_button("Registrar"):
            res = procesar_escaneo(db, g, "Op", "INGRESO")
            st.success(res["message"]) if res["status"] == "OK" else st.error(res["message"])
elif menu == "Despacho (Salida)":
    st.title("🚚 Salida")
    m = db.query(Courier).all()
    if m:
        m_map = {i.name: i.id for i in m}
        sel = st.selectbox("Mensajero:", list(m_map.keys()))
        with st.form("out", clear_on_submit=True):
            go = st.text_input("Guía:")
            if st.form_submit_button("Enviar"):
                res = procesar_escaneo(db, go, "Ad", "DESPACHO", m_map[sel])
                st.success(res["message"]) if res["status"] == "OK" else st.warning(res["message"])

db.close()
