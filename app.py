import streamlit as st
from database import engine, SessionLocal, Base
from models import Package, Courier
from datetime import datetime

# CONFIGURACIÓN SEGÚN RF3.6 (Interfaz de Usuario)
st.set_page_config(page_title="Enmilla ERP - Logística", layout="wide", page_icon="🚚")

# Inicialización de BD (Requisito 2.1)
Base.metadata.create_all(bind=engine)

st.title("🚚 Enmilla ERP")
st.caption("Sistema de Gestión Logística - Enlace Soluciones Logísticas SAS")

# Menú Lateral (RF3.6.1)
menu = st.sidebar.radio("Navegación", ["Recepción", "Seguimiento", "Despacho", "Mensajeros"])

db = SessionLocal()

# --- RF3.1: MÓDULO DE RECEPCIÓN ---
if menu == "Recepción":
    st.header("📦 Registro de Paquetes")
    with st.form("registro_paquete", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            tracking = st.text_input("Número de Seguimiento (Único)*") # RF3.1.1
            remitente = st.text_input("Nombre del Remitente*")
        with col2:
            destinatario = st.text_input("Nombre del Destinatario*")
            direccion = st.text_input("Dirección de Entrega*")
        
        if st.form_submit_button("Registrar Ingreso"):
            # Validación de Duplicados (RF3.1.2)
            existe = db.query(Package).filter(Package.tracking_number == tracking).first()
            if existe:
                st.error(f"Error: El número de seguimiento {tracking} ya existe.")
            elif tracking and destinatario:
                nuevo = Package(
                    tracking_number=tracking,
                    sender_name=remitente,
                    recipient_name=destinatario,
                    recipient_address=direccion,
                    status="Recibido" # Estado Inicial RF3.1.1
                )
                db.add(nuevo)
                db.commit()
                st.success("✅ Paquete registrado con éxito.")
            else:
                st.warning("Por favor complete los campos obligatorios.")

# --- RF3.2: MÓDULO DE SEGUIMIENTO ---
elif menu == "Seguimiento":
    st.header("🔍 Seguimiento de Paquetes")
    busqueda = st.text_input("Buscar por Tracking Number")
    if busqueda:
        p = db.query(Package).filter(Package.tracking_number == busqueda).first()
        if p:
            st.info(f"**Estado:** {p.status}")
            st.write(f"**Remitente:** {p.sender_name}")
            st.write(f"**Destinatario:** {p.recipient_name}")
            st.write(f"**Dirección:** {p.recipient_address}")
            st.write(f"**Fecha Ingreso:** {p.created_at.strftime('%Y-%m-%d %H:%M')}")
        else:
            st.error("No se encontró el paquete.")

# --- RF3.3: MÓDULO DE DESPACHO (Control de Estados) ---
elif menu == "Despacho":
    st.header("🚚 Gestión de Salidas")
    pendientes = db.query(Package).filter(Package.status != "Entregado").all()
    if pendientes:
        seleccion = st.selectbox("Paquete a gestionar", [p.tracking_number for p in pendientes])
        nuevo_estado = st.selectbox("Actualizar Estado", ["En Tránsito", "Entregado", "Incidencia"])
        
        if st.button("Actualizar Movimiento"):
            pkg = db.query(Package).filter(Package.tracking_number == seleccion).first()
            pkg.status = nuevo_estado
            if nuevo_estado == "Entregado":
                pkg.is_delivered = True # RF3.3.2
            db.commit()
            st.success(f"Estado actualizado a {nuevo_estado}")
            st.rerun()
    else:
        st.write("No hay paquetes pendientes de entrega.")

db.close()
