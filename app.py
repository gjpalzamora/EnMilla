import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

# --- 1. CONFIGURACIÓN DE BASE DE DATOS ---
# Usamos un nombre de archivo nuevo para asegurar una base limpia
DATABASE_URL = "sqlite:///enmilla_v7_final.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- 2. MODELOS DE DATOS (CORREGIDOS) ---
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
    plate = Column(String(50), unique=True, nullable=False)
    is_active = Column(Boolean, default=True)
    movements = relationship("Movement", back_populates="courier")

class Package(Base):
    __tablename__ = "packages"
    id = Column(Integer, primary_key=True, index=True)
    tracking_number = Column(String(100), unique=True, index=True, nullable=False)
    client_id = Column(Integer, ForeignKey("clients_b2b.id"), nullable=True)
    status = Column(String(50), default="BODEGA")
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
st.set_page_config(page_title="EnMilla ERP v7.0", layout="wide")
st.sidebar.title("🚚 Panel Enmilla")
modulo = st.sidebar.radio("Ir a:", [
    "1. Administración (Crear)", 
    "2. Operaciones (Recibir)", 
    "3. Despacho (Cargar)", 
    "4. Edición de Maestros"
])

# --- MÓDULO 1: ADMINISTRACIÓN ---
if modulo == "1. Administración (Crear)":
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
                except Exception:
                    st.error("Error: El NIT o Nombre ya existen.")
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
                    st.success(f"Mensajero {cn} creado.")
                except Exception:
                    st.error("Error: La placa ya está registrada.")
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
            st.info("Debe crear un cliente antes de agregar productos.")
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
                existe = db_s.query(Package).filter(Package.tracking_number == guia).first()
                if not existe:
                    p = Package(tracking_number=guia, client_id=cli_obj.id)
                    db_s.add(p); db_s.commit()
                    db_s.add(Movement(package_id=p.id, location="BODEGA", description=f"Ingreso: {p_nom}"))
                    db_s.commit()
                    st.toast(f"✅ {guia} Recibido", icon="📦")
                else:
                    st.warning(f"La guía {guia} ya está en bodega.")
                db_s.close()
                st.session_state.barcode_in = ""

        st.text_input("ESCANEE GUÍA AQUÍ", key="barcode_in", on_change=registrar)
    else:
        st.warning("Cree clientes en Administración.")
    db.close()

# --- MÓDULO 3: DESPACHO ---
elif modulo == "3. Despacho (Cargar)":
    st.header("Salida a Ruta")
    db = SessionLocal()
    mens = db.query(Courier).filter(Courier.is_active == True).all()
    if mens:
        m_sel = st.selectbox("Seleccione Mensajero", [f"{m.name} ({m.plate})" for m in mens])
        m_name_only = m_sel.split(" (")[0]
        m_obj = db.query(Courier).filter(Courier.name == m_name_only).first()

        def despachar():
            g = st.session_state.barcode_out.strip().upper()
            if g:
                db_d = SessionLocal()
                pkg = db_d.query(Package).filter(Package.tracking_number == g).first()
                if pkg:
                    pkg.status = "EN RUTA"
                    db_d.add(Movement(package_id=pkg.id, courier_id=m_obj.id, location="EN RUTA", description=f"Cargado a {m_obj.name}"))
                    db_d.commit()
                    st.toast(f"🚚 {g} Despachado", icon="🚀")
                else:
                    st.error(f"La guía {g} no existe.")
                db_d.close()
                st.session_state.barcode_out = ""

        st.text_input("ESCANEE PARA SALIDA", key="barcode_out", on_change=despachar)
    else:
        st.warning("Cree mensajeros en Administración.")
    db.close()

# --- MÓDULO 4: EDICIÓN COMPLETA ---
elif modulo == "4. Edición de Maestros":
    st.header("Gestión y Corrección de Datos")
    db = SessionLocal()
    
    op = st.selectbox("¿Qué desea corregir?", ["Productos", "Clientes", "Mensajeros"])
    
    if op == "Productos":
        prods = db.query(Product).all()
        if prods:
            p_sel = st.selectbox("Producto a editar", [f"{p.id} | {p.name}" for p in prods])
            p_id = int(p_sel.split(" | ")[0])
            p_obj = db.query(Product).get(p_id)
            with st.form("ed_p"):
                new_n = st.text_input("Nombre Producto", value=p_obj.name).upper()
                if st.form_submit_button("Actualizar Producto"):
                    p_obj.name = new_n
                    db.commit(); st.success("Actualizado"); st.rerun()

    elif op == "Clientes":
        clis = db.query(ClientB2B).all()
        if clis:
            c_sel = st.selectbox("Cliente a editar", [c.name for c in clis])
            c_obj = db.query(ClientB2B).filter(ClientB2B.name == c_sel).first()
            with st.form("ed_c"):
                new_n = st.text_input("Nombre Empresa", value=c_obj.name).upper()
                new_nit = st.text_input("NIT", value=c_obj.nit)
                if st.form_submit_button("Actualizar Cliente"):
                    c_obj.name = new_n; c_obj.nit = new_nit
                    db.commit(); st.success("Actualizado"); st.rerun()

    elif op == "Mensajeros":
        mens = db.query(Courier).all()
        if mens:
            m_sel = st.selectbox("Mensajero a editar", [m.name for m in mens])
            m_obj = db.query(Courier).filter(Courier.name == m_sel).first()
            with st.form("ed_m"):
                new_n = st.text_input("Nombre", value=m_obj.name).upper()
                new_p = st.text_input("Placa", value=m_obj.plate).upper()
                act = st.checkbox("Activo", value=m_obj.is_active)
                if st.form_submit_button("Actualizar Mensajero"):
                    m_obj.name = new_n; m_obj.plate = new_p; m_obj.is_active = act
                    db.commit(); st.success("Actualizado"); st.rerun()
    db.close()
