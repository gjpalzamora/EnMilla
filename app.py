import streamlit as st
import pandas as pd
from sqlalchemy.orm import Session
from db_models import engine, get_db, create_tables, Package, Courier
from logica_operativa import procesar_escaneo
from admin_module import display_admin_module

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="EnMilla Logistics", layout="wide")

def play_sound(sound_type):
    audio_url = "https://www.soundjay.com/buttons/sounds/button-37.mp3" if sound_type == "OK" else "https://www.soundjay.com/buttons/sounds/button-10.mp3"
    st.components.v1.html(f'<audio autoplay><source src="{audio_url}"></audio>', height=0)

# --- INICIALIZACIÓN ---
try:
    db = next(get_db())
    create_tables() # MEJORA: Crea las tablas automáticamente
except Exception as e:
    st.error("Error de conexión a la base de datos.")
    st.stop()

st.sidebar.title("📦 EnMilla")
modulo = st.sidebar.radio("Módulos:", ["Administración", "Recepción", "Despacho", "Reportes"])

if modulo == "Administración":
    display_admin_module(db)

elif modulo == "Recepción":
    st.header("📥 Recepción de Paquetes")
    guia = st.text_input("Escanear Guía:", key="recep_scan")
    if guia:
        res = procesar_escaneo(db, guia, "Admin", "INGRESO")
        if res["status"] == "OK":
            st.success(res["message"])
            play_sound("OK")
        else:
            st.error(res["message"])
            play_sound("FAIL")

elif modulo == "Despacho":
    st.header("🚚 Salida a Ruta")
    couriers = db.query(Courier).all()
    c_dict = {c.name: c.id for c in couriers}
    sel_c = st.selectbox("Mensajero:", options=list(c_dict.keys()))
    guia_d = st.text_input("Escanear para despacho:", key="desp_scan")
    if guia_d and sel_c:
        res = procesar_escaneo(db, guia_d, "Admin", "DESPACHO", mensajero_id=c_dict[sel_c])
        if res["status"] == "OK":
            st.success("Asignado correctamente")
            play_sound("OK")
        else:
            st.warning(res["message"])
            play_sound("FAIL")

# --- CIERRE LIMPIO ---
if 'db' in locals():
    db.close()
