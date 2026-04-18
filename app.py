import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from fpdf import FPDF
import io

# --- 1. CONFIGURACIÓN DE BASE DE DATOS (Requisitos 2.1 y 2.2) ---
# Se utiliza el patrón SessionLocal y la creación automática de tablas [cite: 41, 42]
DATABASE_URL = "postgresql://postgres:password@localhost:5432/enmilla_db"
engine = create_engine(DATABASE_URL, pool_size=20)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- MODELO DE DATOS (Sección 2.2 del documento) ---
class Courier(Base):
    __tablename__ = "couriers"
    id = Column(Integer, primary_key=True, index=True) [cite: 77]
    name = Column(String(255), nullable=False, index=True) [cite: 78]
    phone = Column(String(50), nullable=True) [cite: 79]
    license_plate = Column(String(50), unique=True, index=True) [cite: 81]
    is_active = Column(Boolean, default=True) [cite: 82]
    movements = relationship("Movement", back_populates="courier") [cite: 92]

class Package(Base):
    __tablename__ = "packages"
    id = Column(Integer, primary_key=True, index=True) [cite: 55]
    tracking_number = Column(String(100), unique=True, nullable=False, index=True) [cite: 56]
    sender_name = Column(String(255), index=True) [cite: 57]
    recipient_name = Column(String(255), index=True) [cite: 59]
    recipient_address = Column(Text) [cite: 60]
    status = Column(String(50), default='Recibido', index=True) [cite: 61]
    is_delivered = Column(Boolean, default=False) [cite: 64]
    movements = relationship("Movement", back_populates="package") [cite: 91]

class Movement(Base):
    __tablename__ = "movements"
    id = Column(Integer, primary_key=True, index=True) [cite: 69]
    package_id = Column(Integer, ForeignKey("packages.id"), nullable=False) [cite: 70]
    courier_id = Column(Integer, ForeignKey("couriers.id"), nullable=True) [cite: 71]
    location = Column(String(255), nullable=False) [cite: 72]
    description = Column(Text, nullable=False) [cite: 73]
    movement_time = Column(DateTime, default=datetime.utcnow) [cite: 74]
    package = relationship("Package", back_populates="movements")
    courier = relationship("Courier", back_populates="movements")

Base.metadata.create_all(bind=engine) [cite: 42]

# --- 2. INTERFAZ UNIFICADA (Módulo 3.6) ---
st.set_page_config(page_title="Enmilla ERP - Full Suite", layout="wide")

st.sidebar.title("🚚 Enmilla ERP v1.0")
menu = st.sidebar.radio("Navegación Operativa", [
    "👥 Gestión de Mensajeros",
    "📦 Recepción de Paquetes",
    "🚚 Despacho y Entrega",
    "🔍 Seguimiento 360"
]) [cite: 170]

# --- MÓDULO: GESTIÓN DE MENSAJEROS (RF 3.4) ---
if menu == "👥 Gestión de Mensajeros":
    st.header("Gestión de Mensajeros")
    
    with st.expander("Registrar Nuevo Mensajero"):
        with st.form("form_courier"):
            c_name = st.text_input("Nombre Completo*") [cite: 148]
            c_phone = st.text_input("Teléfono") [cite: 149]
            c_plate = st.text_input("Placa del Vehículo") [cite: 150]
            if st.form_submit_button("Guardar"):
                db = SessionLocal()
                new_c = Courier(name=c_name, phone=c_phone, license_plate=c_plate)
                db.add(new_c)
                db.commit()
                db.close()
                st.success("Mensajero creado exitosamente.")

    # Listado de mensajeros para selección en otros módulos [cite: 152]
    db = SessionLocal()
    active_couriers = db.query(Courier).filter(Courier.is_active == True).all()
    if active_couriers:
        st.subheader("Personal Activo")
        st.table(pd.DataFrame([{"ID": c.id, "Nombre": c.name, "Placa": c.license_plate} for c in active_couriers]))
    db.close()

# --- MÓDULO: RECEPCIÓN DE PAQUETES (RF 3.1) ---
elif menu == "📦 Recepción de Paquetes":
    st.header("Recepción Masiva en Muelle")
    with st.form("bulk_reception", clear_on_submit=True):
        t_number = st.text_input("Escanee Número de Seguimiento (Tracking)") [cite: 101]
        # Otros campos obligatorios según especificación [cite: 104, 105]
        r_name = st.text_input("Nombre del Destinatario")
        r_addr = st.text_input("Dirección de Entrega")
        
        if st.form_submit_button("Confirmar Ingreso"):
            db = SessionLocal()
            # Validación de duplicados [cite: 111]
            if db.query(Package).filter(Package.tracking_number == t_number).first():
                st.error("Error: El número de seguimiento ya existe.") [cite: 172]
            else:
                new_p = Package(tracking_number=t_number, recipient_name=r_name, recipient_address=r_addr)
                db.add(new_p)
                db.flush() # Para obtener el ID antes del commit
                # Registro de movimiento inicial automático [cite: 110]
                db.add(Movement(package_id=new_p.id, location="Recepción", description="Paquete recibido en origen"))
                db.commit()
                st.success(f"Paquete {t_number} registrado con éxito.") [cite: 172]
            db.close()

# --- MÓDULO: DESPACHO Y ENTREGA (RF 3.3) ---
elif menu == "🚚 Despacho y Entrega":
    st.header("Cargue y Salida a Ruta")
    
    db = SessionLocal()
    couriers = db.query(Courier).filter(Courier.is_active == True).all()
    c_list = {c.name: c.id for c in couriers}
    
    if not c_list:
        st.warning("Debe registrar mensajeros antes de realizar despachos.")
    else:
        selected_c_name = st.selectbox("Seleccione Mensajero para Cargue", list(c_list.keys()))
        selected_c_id = c_list[selected_c_name]
        
        with st.form("dispatch_scan", clear_on_submit=True):
            scan_track = st.text_input("Escanee Paquete para Asignar")
            if st.form_submit_button("Asignar a Mensajero"):
                pkg = db.query(Package).filter(Package.tracking_number == scan_track).first()
                if pkg:
                    pkg.status = "En Tránsito" [cite: 125]
                    # Registro de movimiento con mensajero asociado [cite: 127]
                    db.add(Movement(
                        package_id=pkg.id, 
                        courier_id=selected_c_id, 
                        location="En Ruta", 
                        description=f"Entregado a mensajero {selected_c_name}"
                    ))
                    db.commit()
                    st.success(f"Guía {scan_track} asignada correctamente.")
                else:
                    st.error("Paquete no encontrado en base de datos.")
    db.close()
