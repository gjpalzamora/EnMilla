import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

# --- 1. CONFIGURACIÓN DE BASE DE DATOS ---
DATABASE_URL = "sqlite:///enmilla_v5_final.db"
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
    status = Column(String(50), default="BODEGA")
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
st.set_page_config(page_title="EnMilla ERP v5.0", layout="wide")
st.sidebar.title("🚚 Panel Enmilla")
modulo = st.sidebar.radio("Ir a:", [
    "1. Administración", 
    "2. Operaciones (Recibir)", 
    "3. Despacho (Cargar)", 
    "4. Edición de Datos"
])

# --- MÓDULO 1: ADMINISTRACIÓN (CREACIÓN) ---
if modulo == "1. Administración":
    st.header("Maestros de Operación")
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
                pn = st.text_input("Nombre Producto (Alfanumérico)").upper()
                c_sel = st.selectbox("Asociar a Cliente", [c.name for c in clis])
                if st.form_submit_button("Enlazar Producto"):
                    target = db.query(ClientB2B).filter(ClientB2B.name == c_sel).first()
                    db.add(Product(name=pn, client_id=target.id))
                    db.commit()
                    st.success(f"Producto {pn} enlazado.")
        else:
            st.info("Cree un cliente primero.")
        db.close()

# --- MÓDULO 2: OPERACIONES (RECEPCIÓN AUTO) ---
elif modulo == "2. Operaciones (Recibir)":
    st.header("Entrada Automática (Muelle)")
    db = SessionLocal()
    clis = db.query(ClientB2B).all()
    if clis:
        c_nom = st.selectbox("Cliente", [c.name for c in clis])
        cli_obj = db.query(ClientB2B).filter(ClientB2B.name == c_nom).first()
        prods = db.query(Product).filter(Product.client_id == cli_obj.id).all()
        p_nom = st.selectbox("Producto", [p.name for p in prods] if prods else ["GENÉRICO"])

        def registrar():
            guia = st.session_state.barcode_in.strip().upper()
            if guia:
                db_s = SessionLocal()
                if not db_s.query(Package).filter(Package.tracking_number == guia).first():
                    p = Package(tracking_number=guia, client_id=cli_obj.id)
                    db_s.add(p); db_s.commit()
                    db_s.add(Movement(package_id=p.id, location="BODEGA", description=f"Ingreso {p_nom}"))
                    db_s.commit()
                    st.toast(f"✅ {guia} Recibido")
                else:
                    st.warning(f"Guía {guia} ya existe.")
                db_s.close()
                st.session_state.barcode_in = ""

        st.text_input("ESCANEE AQUÍ", key="barcode_in", on_change=registrar)
    db.close()

# --- MÓDULO 3: DESPACHO ---
elif modulo == "3. Despacho (Cargar)":
    st.header("Salida a Ruta")
    db = SessionLocal()
    mens = db.query(Courier).all()
    if mens:
        m_sel = st.selectbox("Mensajero", [m.name for m in mens])
        m_obj = db.query(Courier).filter(Courier.name == m_sel).first()

        def despachar():
            g = st.session_state.barcode_out.strip().upper()
            if g:
                db_d = SessionLocal()
                pkg = db_d.query(Package).filter(Package.tracking_number == g).first()
                if pkg:
                    pkg.status = "EN RUTA"
                    db_d.add(Movement(package_id=pkg.id, courier_id=m_obj.id, location="EN RUTA", description=f"Asignado a {m_sel}"))
                    db_d.commit()
                    st.toast(f"🚚 {g} en ruta")
                else:
                    st.error("Guía no encontrada.")
                db_d.close()
                st.session_state.barcode_out = ""

        st.text_input("ESCANEE PARA SALIDA", key="barcode_out", on_change=despachar)
    db.close()

# --- MÓDULO 4: EDICIÓN DE DATOS ---
elif modulo == "4. Edición de Datos":
    st.header("Corrección y Edición de Maestros")
    db = SessionLocal()
    
    edit_tipo = st.selectbox("¿Qué desea corregir?", ["Productos", "Clientes", "Mensajeros"])
    
    if edit_tipo == "Productos":
        prods = db.query(Product).all()
        if prods:
            p_to_edit = st.selectbox("Seleccione Producto", [f"{p.id} - {p.name}" for p in prods])
            p_id = int(p_to_edit.split(" - ")[0])
            p_obj = db.query(Product).get(p_id)
            
            with st.form("edit_p"):
                new_name = st.text_input("Nuevo nombre (Mayúsculas Auto)", value=p_obj.name).upper()
                if st.form_submit_button("Actualizar Producto"):
                    p_obj.name = new_name
                    db.commit()
                    st.success("Producto actualizado.")
                    st.rerun()

    elif edit_tipo == "Clientes":
        clis = db.query(ClientB2B).all()
        if clis:
            c_to_edit = st.selectbox("Seleccione Cliente", [c.name for c in clis])
            c_obj = db.query(ClientB2B).filter(ClientB2B.name == c_to_edit).first()
            with st.form("edit_c"):
                new_n = st.text_input("Nuevo Nombre", value=c_obj.name).upper()
                new_nit = st.text_input("Nuevo NIT", value=c_obj.nit)
                if st.form_submit_button("Actualizar Cliente"):
                    c_obj.name = new_n
                    c_obj.nit = new_nit
                    db.commit()
                    st.success("Cliente actualizado.")
                    st.rerun()

    db.close()
