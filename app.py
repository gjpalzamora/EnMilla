import streamlit as st
from database import engine, SessionLocal, Base
from models import Package, Courier
from datetime import datetime

# 1. CONFIGURACIÓN E INTERFAZ
st.set_page_config(page_title="EnMilla ERP - Logística", layout="wide", page_icon="🚚")

# Asegurar que las tablas existan en la base de datos
Base.metadata.create_all(bind=engine)

# Estilo personalizado para el título
st.markdown("# 🚚 EnMilla ERP")
st.markdown("### Sistema de Gestión Logística - Enlaces Soluciones Logística SAS")
st.sidebar.header("Control de Operaciones")

# 2. NAVEGACIÓN
menu = st.sidebar.radio("Módulos", ["Recepción", "Seguimiento", "Despacho", "Mensajeros"])

db = SessionLocal()

# --- MÓDULO 1: RECEPCIÓN ---
if menu == "Recepción":
    st.header("📦 Recepción de Mercancía")
    with st.form("form_recepcion", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            tracking = st.text_input("Número de Guía (Tracking)*")
            destinatario = st.text_input("Nombre del Cliente/Destinatario*")
        with col2:
            direccion = st.text_input("Dirección de Entrega*")
            notas = st.text_area("Observaciones del paquete")
        
        if st.form_submit_button("Registrar Ingreso"):
            if tracking and destinatario:
                nuevo_pkg = Package(
                    tracking_number=tracking, 
                    recipient_name=destinatario,
                    recipient_address=direccion,
                    status="En Bodega"
                )
                db.add(nuevo_pkg)
                db.commit()
                st.success(f"✅ Paquete {tracking} ingresado al inventario.")
            else:
                st.error("Error: Los campos con * son obligatorios.")

# --- MÓDULO 2: SEGUIMIENTO ---
elif menu == "Seguimiento":
    st.header("🔍 Rastreo de Envíos")
    guia_busqueda = st.text_input("Ingrese número de guía para consultar")
    if guia_buscada:
        res = db.query(Package).filter(Package.tracking_number == guia_buscada).first()
        if res:
            st.info(f"**Estado Actual:** {res.status}")
            st.write(f"**Destinatario:** {res.recipient_name}")
            st.write(f"**Dirección:** {res.recipient_address}")
            st.write(f"**Fecha de Ingreso:** {res.created_at.strftime('%d/%m/%Y %H:%M')}")
        else:
            st.warning("No se encontró ninguna guía coincidente.")

# --- MÓDULO 3: DESPACHO ---
elif menu == "Despacho":
    st.header("🚚 Gestión de Salidas y Última Milla")
    p_pendientes = db.query(Package).filter(Package.status == "En Bodega").all()
    
    if p_pendientes:
        guias_lista = [p.tracking_number for p in p_pendientes]
        guia_a_despachar = st.selectbox("Seleccione Guía para Despacho", guias_lista)
        
        if st.button("Marcar como En Ruta"):
            pkg = db.query(Package).filter(Package.tracking_number == guia_a_despachar).first()
            pkg.status = "En Ruta"
            db.commit()
            st.success(f"Guía {guia_a_despachar} asignada a despacho.")
            st.rerun()
    else:
        st.write("No hay paquetes pendientes por despachar.")

# --- MÓDULO 4: MENSAJEROS ---
elif menu == "Mensajeros":
    st.header("👤 Administración de Personal")
    # Lógica para registrar y ver mensajeros (en desarrollo)
    st.info("Este módulo permite la gestión de la flota de última milla.")

db.close()
