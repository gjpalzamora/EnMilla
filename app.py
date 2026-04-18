import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

# --- 1. ARQUITECTURA DE BASE DE DATOS (PostgreSQL / SQLAlchemy) ---
# RF2.1: Implementación de Patrón SessionLocal y Base
DATABASE_URL = "postgresql://postgres:password@localhost:5432/enmilla_db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Tablas Requeridas (RF2.2)
class Courier(Base):
    __tablename__ = "couriers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    phone = Column(String(50), nullable=True)
    license_plate = Column(String(50), unique=True, index=True)
    is_active = Column(Boolean, default=True)
    movements = relationship("Movement", back_populates="courier")

class Package(Base):
    __tablename__ = "packages"
    id = Column(Integer, primary_key=True, index=True)
    tracking_number = Column(String(100), unique=True, nullable=False, index=True)
    status = Column(String(50), default='Recibido', index=True)
    recipient_name = Column(String(255), nullable=True)
    recipient_address = Column(Text, nullable=True)
    movements = relationship("Movement", back_populates="package")

class Movement(Base):
    __tablename__ = "movements"
    id = Column(Integer, primary_key=True, index=True)
    package_id = Column(Integer, ForeignKey("packages.id"), nullable=False)
    courier_id = Column(Integer, ForeignKey("couriers.id"), nullable=True)
    location = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    movement_time = Column(DateTime, default=datetime.utcnow)
    package = relationship("Package", back_populates="movements")
    courier = relationship("Courier", back_populates="movements")

# RF2.1: Creación automática del esquema
Base.metadata.create_all(bind=engine)

# --- 2. INTERFAZ DE USUARIO (Streamlit) ---
st.set_page_config(page_title="Enmilla ERP - Operación Completa", layout="wide")

# RF3.6.1: Menú Lateral de Navegación
st.sidebar.title("🚚 Enmilla ERP v1.0")
modulo = st.sidebar.radio("Módulos", [
    "👥 Gestión de Mensajeros",
    "📦 Recepción Masiva",
    "🚚 Despacho a Ruta (Cargue)",
    "📊 Auditoría y Rastreo"
])

# --- MÓDULO: GESTIÓN DE MENSAJEROS (RF3.4) ---
if modulo == "👥 Gestión de Mensajeros":
    st.header("Administración de Personal de Entrega")
    
    # RF3.4.1: Registrar Nuevo Mensajero
    with st.expander("➕ Registrar Nuevo Mensajero"):
        with st.form("new_courier"):
            name = st.text_input("Nombre Completo (Obligatorio)")
            phone = st.text_input("Teléfono")
            plate = st.text_input("Placa del Vehículo")
            if st.form_submit_button("Guardar Mensajero"):
                db = SessionLocal()
                new_c = Courier(name=name, phone=phone, license_plate=plate)
                db.add(new_c)
                db.commit()
                db.close()
                st.success(f"Mensajero {name} registrado.")

    # RF3.4.2: Listar Mensajeros
    st.subheader("Mensajeros Activos")
    db = SessionLocal()
    couriers = db.query(Courier).filter(Courier.is_active == True).all()
    if couriers:
        df_c = pd.DataFrame([{"ID": c.id, "Nombre": c.name, "Placa": c.license_plate} for c in couriers])
        st.table(df_c)
    db.close()

# --- MÓDULO: RECEPCIÓN MASIVA (RF3.1) ---
elif modulo == "📦 Recepción Masiva":
    st.header("Ingreso Nocturno de Mercancía") # Escenario 10 PM
    with st.form("bulk_scan", clear_on_submit=True):
        t_input = st.text_input("ESCANEE GUÍA")
        if st.form_submit_button("Registrar Ingreso") or t_input:
            db = SessionLocal()
            # RF3.1.2: Validación de Duplicados
            if not db.query(Package).filter(Package.tracking_number == t_input).first():
                pkg = Package(tracking_number=t_input, status="Recibido")
                db.add(pkg)
                db.commit()
                # Registro de movimiento inicial
                db.add(Movement(package_id=pkg.id, location="Bodega Bogotá", description="Ingreso a base"))
                db.commit()
                st.toast(f"Paquete {t_input} en bodega")
            db.close()

# --- MÓDULO: DESPACHO A RUTA (RF3.3) ---
elif modulo == "🚚 Despacho a Ruta (Cargue)":
    st.header("Asignación de Carga y Despacho")
    
    db = SessionLocal()
    active_couriers = db.query(Courier).filter(Courier.is_active == True).all()
    
    if not active_couriers:
        st.error("No hay mensajeros registrados. Vaya al módulo de Mensajeros primero.")
    else:
        # Selección del Mensajero para el cargue
        c_options = {c.name: c.id for c in active_couriers}
        sel_courier_name = st.selectbox("Seleccione Mensajero para Despacho", list(c_options.keys()))
        sel_courier_id = c_options[sel_courier_name]
        
        # Escaneo masivo para asignar a este mensajero
        with st.form("dispatch_form", clear_on_submit=True):
            track_dispatch = st.text_input("Escanee guías para asignar a este mensajero")
            if st.form_submit_button("Asignar a Ruta") or track_dispatch:
                pkg = db.query(Package).filter(Package.tracking_number == track_dispatch).first()
                if pkg:
                    pkg.status = "En Tránsito"
                    # Registrar movimiento con el courier_id seleccionado
                    new_move = Movement(
                        package_id=pkg.id, 
                        courier_id=sel_courier_id, 
                        location="En Ruta", 
                        description=f"Despachado con {sel_courier_name}"
                    )
                    db.add(new_move)
                    db.commit()
                    st.success(f"Guía {track_dispatch} asignada a {sel_courier_name}")
                else:
                    st.error("La guía no existe en bodega.")
    db.close()
