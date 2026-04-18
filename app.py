import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

# --- 1. CONFIGURACIÓN DE BASE DE DATOS ---
DATABASE_URL = "sqlite:///enmilla_final.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- 2. MODELOS DE DATOS ---
class ClientB2B(Base):
    __tablename__ = "clients_b2b"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)
    nit = Column(String(50), unique=True)
    products = relationship("Product", back_populates="client")
    packages = relationship("Package", back_populates="client")

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    client_id = Column(Integer, ForeignKey("clients_b2b.id"))
    client = relationship("ClientB2B", back_populates="products")

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
    client_id = Column(Integer, ForeignKey("clients_b2b.id"), nullable=True)
    status = Column(String(50), default="En Bodega")
    client = relationship("ClientB2B", back_populates="packages")
    movements = relationship("Movement", back_populates="package")

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

Base.metadata.create_all(bind=engine)

# --- 3. INTERFAZ ---
st.set_page_config(page_title="EnMilla ERP", layout="wide")
st.sidebar.title("🚚 Panel Enmilla")
modulo = st.sidebar.radio("Ir a:", [
    "1. Administración", 
    "2. Operaciones (Recibir)", 
    "3. Despacho (Cargar)", 
    "4. Gestión de Datos"
])

# --- MÓDULO 1: ADMINISTRACIÓN ---
if modulo == "1. Administración":
    st.header("Administración de Maestros")
    t1, t2, t3 = st.tabs(["Clientes B2B", "Mensajeros", "Productos"])
    
    with t1:
        with st.form("f_cli", clear_on_submit=True):
            n = st.text_input("Nombre Empresa")
            nit = st.text_input("NIT")
            if st.form_submit_button("Guardar Cliente"):
                db = SessionLocal()
                try:
                    db.add(ClientB2B(name=n, nit=nit))
                    db.commit()
                    st.success(f"Cliente {n} registrado.")
                except:
                    db.rollback()
                    st.error("Error: El NIT o Nombre ya existen.")
                db.close()

    with t2:
        with st.form("f_cou", clear_on_submit=True):
            cn = st.text_input("Nombre Mensajero")
            cp = st.text_input("Placa Vehículo")
            if st.form_submit_button("Guardar Mensajero"):
                db = SessionLocal()
                try:
                    db.add(Courier(name=cn, plate=cp))
                    db.commit()
                    st.success(f"Mensajero {cn} registrado.")
                except:
                    db.rollback()
                    st.error("Error: La placa ya está registrada.")
                db.close()

    with t3:
        db = SessionLocal()
        clis = db.query(ClientB2B).all()
        if clis:
            with st.form("f_prod", clear_on_submit=True):
                pn = st.text_input("Nombre del Producto")
                c_sel = st.selectbox("Asociar a Cliente", [c.name for c in clis])
                if st.form_submit_button("Enlazar Producto"):
                    target = db.query(ClientB2B).filter(ClientB2B.name == c_sel).first()
                    db.add(Product(name=pn, client_id=target.id))
                    db.commit()
                    st.success("Producto enlazado correctamente.")
        else:
            st.info("Debe crear un cliente primero para agregar productos.")
        db.close()

# --- MÓDULO 2: OPERACIONES (RECEPCIÓN AUTOMÁTICA) ---
elif modulo == "2. Operaciones (Recibir)":
    st.header("Entrada de Mercancía (Scanner Mode)")
    db = SessionLocal()
    clis = db.query(ClientB2B).all()
    
    if not clis:
        st.warning("⚠️ No hay clientes. Vaya a Administración.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            c_nom = st.selectbox("Cliente", [c.name for c in clis])
            cli_obj = db.query(ClientB2B).filter(ClientB2B.name == c_nom).first()
        with col2:
            prods = db.query(Product).filter(Product.client_id == cli_obj.id).all()
            p_nom = st.selectbox("Producto", [p.name for p in prods] if prods else ["General"])

        def registrar_entrada():
            g = st.session_state.barcode_in.strip()
            if g:
                db_s = SessionLocal()
                if not db_s.query(Package).filter(Package.tracking_number == g).first():
                    nuevo_p = Package(tracking_number=g, client_id=cli_obj.id)
                    db_s.add(nuevo_p); db_s.commit()
                    db_s.add(Movement(package_id=nuevo_p.id, location="Bodega", description=f"Ingreso: {p_nom}"))
                    db_s.commit()
                    st.toast(f"✅ Guía {g} recibida", icon="📦")
                else:
                    st.warning(f"Guía {g} ya está en sistema.")
                db_s.close()
                st.session_state.barcode_in = ""

        st.text_input("ESCANEE GUÍA AQUÍ", key="barcode_in", on_change=registrar_entrada)
    db.close()

# --- MÓDULO 3: DESPACHO (CARGAR A RUTA) ---
elif modulo == "3. Despacho (Cargar)":
    st.header("Salida a Ruta (Cargue de Vehículos)")
    db = SessionLocal()
    mensajeros = db.query(Courier).filter(Courier.is_active == True).all()
    
    if not mensajeros:
        st.warning("
