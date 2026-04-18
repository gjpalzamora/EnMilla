import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import io

# --- 1. MOTOR DE BASE DE DATOS (ARQUITECTURA 360) ---
# Cambia 'sqlite:///enmilla.db' por tu URL de PostgreSQL cuando estés listo
DATABASE_URL = "sqlite:///enmilla.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- MODELOS (RELACIONES COMPLETAS PARA EVITAR NameError) ---
class Movement(Base):
    __tablename__ = "movements"
    id = Column(Integer, primary_key=True, index=True)
    package_id = Column(Integer, ForeignKey("packages.id"))
    courier_id = Column(Integer, ForeignKey("couriers.id"), nullable=True)
    location = Column(String(255))
    description = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    package = relationship("Package", back_populates="movements")
    courier = relationship("Courier", back_populates="movements")

class Courier(Base):
    __tablename__ = "couriers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    plate = Column(String(50), unique=True)
    is_active = Column(Boolean, default=True)
    movements = relationship("Movement", back_populates="courier")

class Package(Base):
    __tablename__ = "packages"
    id = Column(Integer, primary_key=True, index=True)
    tracking_number = Column(String(100), unique=True, index=True)
    recipient_name = Column(String(255), nullable=True)
    address = Column(Text, nullable=True)
    status = Column(String(50), default="Recibido")
    movements = relationship("Movement", back_populates="package")

# Creación de tablas
Base.metadata.create_all(bind=engine)

# --- 2. INTERFAZ DE USUARIO (OPERACIÓN ENLACE SOLUCIONES) ---
st.set_page_config(page_title="Enmilla ERP v1.0", layout="wide")

st.sidebar.title("🚚 Enmilla ERP")
menu = st.sidebar.radio("Navegación Operativa", [
    "👥 Gestión de Mensajeros", 
    "📦 Recepción Masiva (10 PM)", 
    "🚛 Cargue y Despacho", 
    "🔍 Rastreo 360"
])

# --- MÓDULO: GESTIÓN DE MENSAJEROS ---
if menu == "👥 Gestión de Mensajeros":
    st.header("Administración de Mensajeros")
    with st.form("nuevo_mensajero"):
        n = st.text_input("Nombre del Mensajero")
        p = st.text_input("Placa del Vehículo")
        if st.form_submit_button("Registrar Mensajero"):
            db = SessionLocal()
            db.add(Courier(name=n, plate=p))
            db.commit()
            db.close()
            st.success(f"Mensajero {n} registrado.")

# --- MÓDULO: RECEPCIÓN MASIVA (CONTINGENCIA) ---
elif menu == "📦 Recepción Masiva (10 PM)":
    st.header("Recepción de Contingencia")
    st.info("Escaneo rápido para descarga de camión.")
    with st.form("scan_form", clear_on_submit=True):
        track = st.text_input("ESCANEE AQUÍ")
        if st.form_submit_button("INGRESAR") or track:
            db = SessionLocal()
            if not db.query(Package).filter(Package.tracking_number == track).first():
                p = Package(tracking_number=track)
                db.add(p)
                db.commit()
                db.add(Movement(package_id=p.id, location="Bodega", description="Ingreso masivo"))
                db.commit()
                st.toast(f"Paquete {track} registrado.")
            db.close()

# --- MÓDULO: CARGUE Y DESPACHO (ASIGNACIÓN REAL) ---
elif menu == "🚛 Cargue y Despacho":
    st.header("Asignación de Rutas")
    db = SessionLocal()
    mensajeros = db.query(Courier).filter(Courier.is_active == True).all()
    
    if not mensajeros:
        st.warning("No hay mensajeros creados. Ve al módulo de Mensajeros.")
    else:
        opciones_m = {m.name: m.id for m in mensajeros}
        m_seleccionado = st.selectbox("Seleccione Mensajero para Cargue", list(opciones_m.keys()))
        
        with st.form("form_cargue", clear_on_submit=True):
            guia = st.text_input("Escanee Guía para Cargar al Vehículo")
            if st.form_submit_button("ASIGNAR"):
                pkg = db.query(Package).filter(Package.tracking_number == guia).first()
                if pkg:
                    pkg.status = "En Tránsito"
                    db.add(Movement(
                        package_id=pkg.id, 
                        courier_id=opciones_m[m_seleccionado],
                        location="En Ruta",
                        description=f"Cargado en vehículo de {m_seleccionado}"
                    ))
                    db.commit()
                    st.success(f"Guía {guia} asignada a {m_seleccionado}")
                else:
                    st.error("La guía no existe en sistema.")
    db.close()
