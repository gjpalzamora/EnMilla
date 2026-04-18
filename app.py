import streamlit as st
from database import engine, SessionLocal, Base
from models import Package, Client, ClientShipment
import uuid

# Configuración Profesional
st.set_page_config(page_title="Enmilla ERP - Logística", layout="wide")
Base.metadata.create_all(bind=engine)
db = SessionLocal()

st.title("🚚 Enmilla ERP - Gestión Estratégica")

menu = st.sidebar.selectbox("Módulo Operativo", 
    ["Gestión de Clientes", "Recepción (Escaneo Rápido)", "Distribución", "Seguimiento"])

# --- RF5.1: GESTIÓN DE CLIENTES ---
if menu == "Gestión de Clientes":
    st.header("🏢 Registro de Clientes Corporativos")
    with st.form("nuevo_cliente"):
        nombre = st.text_input("Nombre de la Empresa/Cliente*")
        email = st.text_input("Correo Electrónico")
        if st.form_submit_button("Registrar Cliente"):
            if nombre:
                nuevo_c = Client(name=nombre, email=email)
                db.add(nuevo_c)
                db.commit()
                st.success(f"Cliente {nombre} creado.")

# --- RF5.3: ESCANEO RÁPIDO EN BODEGA ---
elif menu == "Recepción (Escaneo Rápido)":
    st.header("⚡ Ingreso Masivo a Bodega")
    st.info("Compatible con lectores de código de barras (Enter automático)")
    
    # Campo de enfoque automático para el lector
    scan_input = st.text_input("Escanee Código de Guía (Cliente o Interna)", key="scanner", help="El lector debe enviar 'Enter' al final")
    
    if scan_input:
        # Lógica de búsqueda y actualización automática
        pkg = db.query(Package).filter(Package.internal_tracking_number == scan_input).first()
        if pkg:
            pkg.status = "Ingresado a Bodega"
            db.commit()
            st.success(f"📦 Paquete {scan_input} actualizado a: Ingresado a Bodega")
        else:
            st.error("❌ Código no reconocido en el sistema.")

# --- RF5.2: DISTRIBUCIÓN (Crear Paquetes desde Envío de Cliente) ---
elif menu == "Distribución":
    st.header("⛟ Distribución de Envíos de Clientes")
    envios_disponibles = db.query(ClientShipment).filter(ClientShipment.quantity_available > 0).all()
    
    if envios_disponibles:
        opciones = {f"{e.client.name} - {e.client_tracking_number} (Disp: {e.quantity_available})": e.id for e in envios_disponibles}
        seleccion = st.selectbox("Seleccione envío del cliente para distribuir", opciones.keys())
        
        with st.form("distribuir"):
            dest = st.text_input("Nombre Destinatario Final*")
            dir_dest = st.text_input("Dirección de Entrega*")
            if st.form_submit_button("Generar Paquete y Etiqueta"):
                envio_id = opciones[seleccion]
                envio = db.query(ClientShipment).get(envio_id)
                
                # RF5.2.1: Crear paquete y decrementar inventario
                nueva_guia = f"ENM-{uuid.uuid4().hex[:8].upper()}"
                nuevo_p = Package(
                    internal_tracking_number=nueva_guia,
                    client_shipment_id=envio.id,
                    recipient_name=dest,
                    recipient_address=dir_dest,
                    status="Listo para Despacho"
                )
                envio.quantity_available -= 1
                db.add(nuevo_p)
                db.commit()
                st.success(f"✅ Paquete creado. Guía Interna: {nueva_guia}")
                st.info("🖨️ Generando etiqueta PDF... (RF5.2.2)")
    else:
        st.write("No hay bultos de clientes pendientes de distribuir.")

db.close()
