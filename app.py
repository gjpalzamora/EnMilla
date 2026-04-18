import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

# --- 1. CONFIGURACIÓN DE BASE DE DATOS ---
DATABASE_URL = "sqlite:///enmilla_v2.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- 2. MODELOS (ORDENADOS PARA EVITAR NAMEERROR) ---

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
    recipient_name = Column(String(255))
    address = Column(Text)
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

# --- 3. INTERFAZ OPERATIVA ---
st.set_page_config(page_title="EnMilla ERP v2.0", layout="wide")
st.sidebar.title("🚚 Panel Enmilla")
modulo = st.sidebar.radio("Ir a:", [
    "1. Administración", 
    "2. Operaciones (Recibir)", 
    "3. Despacho (Cargar)", 
    "4. Gestión de Datos (Ver/Editar)"
])

# --- MÓDULO 1: ADMINISTRACIÓN ---
if modulo == "1. Administración":
    st.header("Registro de Maestros")
    t1, t2, t3 = st.tabs(["Clientes B2B", "Mensajeros", "Productos"])
    
    with t1:
        with st.form("f_cli", clear_on_submit=True):
            n = st.text_input("Nombre Empresa"); nit = st.text_input("NIT")
            if st.form_submit_button("Guardar Cliente"):
                db = SessionLocal()
                try:
                    db.add(ClientB2B(name=n, nit=nit)); db.commit()
                    st.success("Cliente creado.")
                except:
                    db.rollback(); st.error("Error: NIT o Nombre ya existen.")
                db.close()

    with t2:
        with st.form("f_cou", clear_on_submit=True):
            cn = st.text_input("Nombre Mensajero"); cp = st.text_input("Placa")
            if st.form_submit_button("Guardar Mensajero"):
                db = SessionLocal()
                try:
                    db.add(Courier(name=cn, plate=cp)); db.commit()
                    st.success("Mensajero creado.")
                except:
                    db.rollback(); st.error("Error: Placa ya existe.")
                db.close()

    with t3:
        db = SessionLocal(); clis = db.query(ClientB2B).all()
        with st.form("f_prod"):
            pn = st.text_input("Nombre Producto")
            c_sel = st.selectbox("Cliente Propietario", [c.name for c in clis])
            if st.form_submit_button("Enlazar"):
                target = db.query(ClientB2B).filter(ClientB2B.name == c_sel).first()
                db.add(Product(name=pn, client_id=target.id)); db.commit()
                st.success("Producto enlazado.")
        db.close()

# --- MÓDULO 2: OPERACIONES ---
elif modulo == "2. Operaciones (Recibir)":
    st.header("Entrada de Mercancía")
    with st.form("f_rec", clear_on_submit=True):
        track = st.text_input("ESCANEE TRACKING")
        if st.form_submit_button("INGRESAR") or track:
            db = SessionLocal()
            if not db.query(Package).filter(Package.tracking_number == track).first():
                p = Package(tracking_number=track); db.add(p); db.commit()
                db.add(Movement(package_id=p.id, location="Bodega", description="Recibido")); db.commit()
                st.toast(f"Guía {track} en bodega")
            db.close()

# --- MÓDULO 3: DESPACHO ---
elif modulo == "3. Despacho (Cargar)":
    st.header("Asignación a Mensajeros")
    db = SessionLocal(); mens = db.query(Courier).all()
    if mens:
        m_sel = st.selectbox("Mensajero", [m.name for m in mens])
        m_obj = db.query(Courier).filter(Courier.name == m_sel).first()
        with st.form("f_des", clear_on_submit=True):
            t_des = st.text_input("Escanee para salida")
            if st.form_submit_button("DESPACHAR"):
                pkg = db.query(Package).filter(Package.tracking_number == t_des).first()
                if pkg:
                    pkg.status = "En Ruta"
                    db.add(Movement(package_id=pkg.id, courier_id=m_obj.id, location="En Ruta", description="Cargado")); db.commit()
                    st.success("Despachado.")
    db.close()

# --- MÓDULO 4: GESTIÓN DE DATOS ---
elif modulo == "4. Gestión de Datos (Ver/Editar)":
    st.header("Control de Información")
    et1, et2 = st.tabs(["Listado Clientes", "Listado Mensajeros"])
