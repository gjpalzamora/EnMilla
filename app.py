import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

# --- 1. CONFIGURACIÓN DE BASE DE DATOS ---
DATABASE_URL = "sqlite:///enmilla_v4_final.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- 2. MODELOS DE DATOS ---
class ClientB2B(Base):
    __tablename__ = "clients_b2b"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True)
    nit = Column(String(50), unique=True)
    products = relationship("Product", back_populates="client")
    packages = relationship("Package", back_populates="client")

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    client_id = Column(Integer, ForeignKey("clients_b2b.id"))
    client = relationship("ClientB2B", back_populates="products")

class Courier(Base):
    __tablename__ = "couriers"
    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    plate = Column(String(50), unique=True)
    is_active = Column(Boolean, default=True)
    movements = relationship("Movement", back_populates="courier")

class Package(Base):
    __tablename__ = "packages"
    id = Column(Integer, primary_key=True)
    tracking_number = Column(String(100), unique=True)
    client_id = Column(Integer, ForeignKey("clients_b2b.id"))
    status = Column(String(50), default="En Bodega")
    client = relationship("ClientB2B", back_populates="packages")
    movements = relationship("Movement", back_populates="package")

class Movement(Base):
    __tablename__ = "movements"
    id = Column(Integer, primary_key=True)
    package_id = Column(Integer, ForeignKey("packages.id"))
    courier_id = Column(Integer, ForeignKey("couriers.id"), nullable=True)
    location = Column(String(255))
    description = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    package = relationship("Package", back_populates="movements")
    courier = relationship("Courier", back_populates="movements")

Base.metadata.create_all(bind=engine)

# --- 3. INTERFAZ ---
st.set_page_config(page_title="EnMilla ERP v4.0", layout="wide")
st.sidebar.title("🚚 Panel Enmilla")
modulo = st.sidebar.radio("Ir a:", ["1. Administración", "2. Operaciones (Recibir)", "3. Despacho (Cargar)", "4. Edición y Gestión"])

# --- MÓDULO 1: ADMINISTRACIÓN ---
if modulo == "1. Administración":
    st.header("Creación de Maestros")
    t1, t2, t3 = st.tabs(["Clientes B2B", "Mensajeros", "Productos"])
    
    with t1:
        with st.form("f_cli", clear_on_submit=True):
            n = st.text_input("Nombre Empresa").upper()
            nit = st.text_input("NIT")
            if st.form_submit_button("Guardar Cliente"):
                db = SessionLocal()
                try:
                    db.add(ClientB2B(name=n, nit=nit))
                    db.commit()
                    st.success(f"Cliente {n} registrado.")
                except:
                    st.error("Error: NIT o Nombre ya existen.")
                db.close()

    with t2:
        with st.form("f_cou", clear_on_submit=True):
            cn = st.text_input("Nombre Mensajero").upper()
            cp = st.text_input("Placa").upper()
            if st.form_submit_button("Guardar Mensajero"):
                db = SessionLocal()
                try:
                    db.add(Courier(name=cn, plate=cp))
                    db.commit()
                    st.success("Mensajero creado.")
                except:
                    st.error("Error: Placa duplicada.")
                db.close()

    with t3:
        db = SessionLocal()
        clis = db.query(ClientB2B).all()
        if clis:
            with st.form("f_prod", clear_on_submit=True):
                pn = st.text_input("Nombre del Producto (Alfanumérico)").upper()
                c_sel = st.selectbox("Asociar a Cliente", [c.name for c in clis])
                if st.form_submit_button("Enlazar Producto"):
                    target = db.query(ClientB2B).filter(ClientB2B.name == c_sel).first()
                    db.add(Product(name=pn, client_id=target.id))
                    db.commit()
                    st.success(f"Producto {pn} enlazado.")
        db.close()

# --- MÓDULO 2: OPERACIONES (RECEPCIÓN AUTO) ---
elif modulo == "2. Operaciones (Recibir)":
    st.header("Entrada Automática")
    db = SessionLocal()
    clis = db.query(ClientB2B).all()
    if clis
