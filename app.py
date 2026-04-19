import streamlit as st
import pandas as pd
from sqlalchemy.orm import Session
from datetime import datetime
import os

# --- IMPORTACIONES DINÁMICAS ---
try:
    # Traemos los modelos y la sesión
    from db_models import (
        ClientB2B, Product, Courier, Package, PackageLog,
        engine, get_db, create_tables
    )
    # Traemos la lógica operativa (El cerebro de los escaneos)
    from logica_operativa import procesar_escaneo
    # Módulo administrativo
    from admin_module import display_admin_module
    
    MODULES_IMPORTED = True
except ImportError as e:
    st.error(f"Error de importación crítico: {e}")
    MODULES_IMPORTED = False

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="EnMilla - Sistema de Inventario", layout="wide")

# --- FUNCIÓN DE AUDIO (ALERTAS SONORAS) ---
def play_sound(sound_type):
    """Reproduce sonidos según el resultado del escaneo"""
    # Sonido corto para éxito, frecuencia alta para error
    if sound_type == "BEEP_CORTO":
        audio_url = "https://www.soundjay.com/buttons/sounds/button-37.mp3"
    else: # ALERTA_CRITICA
        audio_url = "https://www.soundjay.com/buttons/sounds/button-10.mp3"
    
    st.components.v1.html(
        f"""<audio autoplay><source src="{audio_url}" type="audio/mpeg"></audio>""",
        height=0,
    )

# --- INICIALIZACIÓN DE BASE DE DATOS ---
if MODULES_IMPORTED:
    db = next(get_db())
    # Descomenta la siguiente línea una sola vez si necesitas crear las tablas nuevas
    # create_tables()
else:
    st.stop()

# --- NAVEGACIÓN LATERAL ---
st.sidebar.title("📦 EnMilla Logistics")
menu_options = ["Administración", "Recepción", "Despacho y Rutas", "Reportes"]
modulo = st.sidebar.radio("Ir a:", menu_options)

# --- MÓDULO DE RECEPCIÓN (BODEGA INBOUND) ---
if modulo == "Recepción":
    st.header("📥 Entrada a Bodega")
    st.write("Escanee los paquetes para confirmar su ingreso físico.")
    
    with st.container():
        # Campo de escaneo - El cursor vuelve aquí automáticamente
        guia = st.text_input("Escanear Guía (Pistola de barras):", key="scan_recepcion")
        
        if guia:
            # Llamamos a nuestra lógica centralizada
            res = procesar_escaneo(db, guia, operario_id="Admin_EnMilla", modo="INGRESO")
            
            if res["status"] == "OK":
                st.success(res["message"])
                play_sound("BEEP_CORTO")
            else:
                st.error(res["message"])
                play_sound("ALERTA_CRITICA")

# --- MÓDULO DE DESPACHO (BODEGA OUTBOUND) ---
elif modulo == "Despacho y Rutas":
    st.header("🚚 Salida a Reparto")
    
    # 1. Seleccionar Mensajero
    couriers = db.query(Courier).filter(Courier.is_active == True).all()
    c_options = {f"{c.name} ({c.document_id})": c.id for c in couriers}
    sel_courier = st.selectbox("Seleccione el mensajero responsable:", options=list(c_options.keys()))
    
    if sel_courier:
        guia_despacho = st.text_input("Escanear paquete para asignar:", key="scan_despacho")
        
        if guia_despacho:
            # Validamos con la lógica operativa (No sale si no entró)
            res = procesar_escaneo(
                db, guia_despacho, 
                operario_id="Admin_EnMilla", 
                modo="DESPACHO", 
                mensajero_id=c_options[sel_courier]
            )
            
            if res["status"] == "OK":
                st.success(res["message"])
                play_sound("BEEP_CORTO")
            else:
                st.warning(res["message"]) # Esto saldrá si el paquete no registra ingreso
                play_sound("ALERTA_CRITICA")

# --- MÓDULO ADMINISTRATIVO ---
elif modulo == "Administración":
    display_admin_module(db)

# --- MÓDULO DE REPORTES ---
elif modulo == "Reportes":
    st.header("📊 Trazabilidad y Auditoría")
    st.info("Consulte la hoja de vida de cualquier guía.")
    
    search_guia = st.text_input("Buscar historial de guía:")
    if search_guia:
        pkg = db.query(Package).filter(Package.tracking_number == search_guia).first()
        if pkg:
            st.subheader(f"Estado Actual: {pkg.status}")
            # Mostrar los LOGS (La hoja de vida)
            logs = [{"Fecha": l.timestamp, "Acción": l.action, "Nota": l.observation} for l in pkg.logs]
            st.table(pd.DataFrame(logs))
        else:
            st.error("Guía no encontrada.")

# --- CIERRE ---
db.close()
