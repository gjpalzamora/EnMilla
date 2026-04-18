import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

# --- 1. CONFIGURACIÓN DE BASE DE DATOS ---
DATABASE_URL = "sqlite:///enmilla_final_v3.db"
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

# --- 3. INTERFAZ STREAMLIT ---
st.set_page_config(page_title="EnMilla ERP v3.0", layout="wide")
st.sidebar.title("🚚 Panel Enmilla")
modulo = st.sidebar.radio("Ir a:", ["1. Administración", "2. Operaciones (Recibir)", "3. Despacho (Cargar)", "4. Gestión de Datos"])

# --- MÓDULO 1: ADMINISTRACIÓN ---
if modulo == "1. Administración":
    st.header("Gestión de Maestros")
    t1, t2, t3 = st.tabs(["Clientes B2B", "Mensajeros", "Productos"])
    
    with t1:
        with st.form("f_cli", clear_on_submit=True):
            n = st.text_input("Nombre Empresa"); nit = st.text_input("NIT")
            if st.form_submit_button("Guardar Cliente"):
                db = SessionLocal()
                try:
                    db.add(ClientB2B(name=n, nit=nit)); db.commit()
                    st.success(f"Cliente {n} creado.")
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
        if clis:
            with st.form("f_prod", clear_on_submit=True):
                pn = st.text_input("Nombre del Producto")
                c_sel = st.selectbox("Asociar a Cliente", [c.name for c in clis])
                if st.form_submit_button("Enlazar Producto"):
                    target = db.query(ClientB2B).filter(ClientB2B.name == c_sel).first()
                    db.add(Product(name=pn, client_id=target.id)); db.commit()
                    st.success(f"Producto {pn} enlazado a {c_sel}")
        else: st.warning("Cree un cliente primero.")
        db.close()

# --- MÓDULO 2: OPERACIONES (RECEPCIÓN AUTOMÁTICA) ---
elif modulo == "2. Operaciones (Recibir)":
    st.header("Entrada Automática (Muelle)")
    db = SessionLocal()
    clientes = db.query(ClientB2B).all()
    
    if not clientes:
        st.warning("Debe crear un cliente en Administración.")
    else:
        c1, c2 = st.columns(2)
        with c1:
            c_nom = st.selectbox("Cliente B2B", [c.name for c in clientes])
            cli_obj = db.query(ClientB2B).filter(ClientB2B.name == c_nom).first()
        with c2:
            prods = db.query(Product).filter(Product.client_id == cli_obj.id).all()
            p_nom = st.selectbox("Producto", [p.name for p in prods] if prods else ["Genérico"])

        def procesar_escaneo():
            guia = st.session_state.barcode.strip()
            if guia:
                db_sub = SessionLocal()
                if not db_sub.query(Package).filter(Package.tracking_number == guia).first():
                    p = Package(tracking_number=guia, client_id=cli_obj.id)
                    db_sub.add(p); db_sub.commit()
                    db_sub.add(Movement(package_id=p.id, location="Bodega", description=f"Recibido - {p_nom}")); db_sub.commit()
                    st.toast(f"✅ {guia} Recibido", icon="📦")
                else: st.warning(f"Guía {guia} ya existe.")
                db_sub.close()
                st.session_state.barcode = ""

        st.text_input("ESCANEE AQUÍ (Automático)", key="barcode", on_change=procesar_escaneo)

# --- MÓDULO 3: DESPACHO ---
elif modulo == "3. Despacho (Cargar)":
    st.header("Salida a Ruta")
    db = SessionLocal(); mens = db.query(Courier).filter(Courier.is_active==True).all()
    if mens:
        m_sel = st.selectbox("Seleccione Mensajero", [m.name for m in mens])
        m_obj = db.query(Courier).filter(Courier.name == m_sel).first()
        
        def procesar_despacho():
            g_des = st.session_state.barcode_out.strip()
            if g_des:
                db_d = SessionLocal()
                pkg = db_d.query(Package).filter(Package.tracking_number == g_des).first()
                if pkg:
                    pkg.status = "En Ruta"
                    db_d.add(Movement(package_id=pkg.
