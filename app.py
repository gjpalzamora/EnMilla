import streamlit as st
from db_models import get_db, create_tables, Courier
from logica_operativa import procesar_escaneo
from admin_module import display_admin_module

st.set_page_config(page_title="EnMilla Logistics", layout="wide", page_icon="📦")

# Inicialización
try:
    db = next(get_db())
    create_tables()
except Exception as e:
    st.error(f"❌ Error crítico de base de datos: {e}")
    st.stop()

st.sidebar.title("EnMilla v2.0")
modulo = st.sidebar.radio("Ir a:", ["Administración", "Recepción (Ingreso)", "Despacho (Salida)"])

if modulo == "Administración":
    display_admin_module(db)

elif modulo == "Recepción (Ingreso)":
    st.header("📥 Recepción de Mercancía")
    guia = st.text_input("Escanee el código de barras:", placeholder="Esperando escaneo...", key="scan_in")
    if guia:
        res = procesar_escaneo(db, guia, "Admin", "INGRESO")
        if res["status"] == "OK":
            st.success(f"✅ {res['message']}")
            # Aquí se puede agregar st.balloons() o un sonido si lo deseas
        else:
            st.error(f"❌ {res['message']}")

elif modulo == "Despacho (Salida)":
    st.header("🚚 Salida a Ruta")
    couriers = db.query(Courier).filter(Courier.is_active == True).all()
    if couriers:
        c_dict = {c.name: c.id for c in couriers}
        sel_c = st.selectbox("Seleccione Mensajero:", options=list(c_dict.keys()))
        guia_d = st.text_input("Escanee guía para despacho:", key="scan_out")
        if guia_d:
            res = procesar_escaneo(db, guia_d, "Admin", "DESPACHO", mensajero_id=c_dict[sel_c])
            if res["status"] == "OK":
                st.success(f"🚀 {res['message']} a {sel_c}")
            else:
                st.warning(f"⚠️ {res['message']}")
    else:
        st.warning("No hay mensajeros activos en el sistema.")

db.close()
