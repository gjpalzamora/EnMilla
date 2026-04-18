import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Boolean, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

# --- CONFIGURACIÓN DE NÚCLEO ---
DATABASE_URL = "sqlite:///enmilla_master_v10.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- MODELOS (PROHIBIDO ELIMINAR PKs) ---
class ClientB2B(Base):
    __tablename__ = "clients_b2b"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)
    nit = Column(String(50), unique=True)
    packages = relationship("Package", back_populates="client")

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    client_id = Column(Integer, ForeignKey("clients_b2b.id"))

class Courier(Base):
    __tablename__ = "couriers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    plate = Column(String(50), unique=True, nullable=False)
    is_active = Column(Boolean, default=True)
    packages = relationship("Package", back_populates="courier")

class Package(Base):
    __tablename__ = "packages"
    id = Column(Integer, primary_key=True, index=True)
    tracking_number = Column(String(100), unique=True, index=True, nullable=False)
    client_id = Column(Integer, ForeignKey("clients_b2b.id"))
    courier_id = Column(Integer, ForeignKey("couriers.id"), nullable=True)
    status = Column(String(50), default="BODEGA")
    last_update = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    client = relationship("ClientB2B", back_populates="packages")
    courier = relationship("Courier", back_populates="packages")

Base.metadata.create_all(bind=engine)

# --- INTERFAZ ---
st.set_page_config(page_title="EnMilla ERP v10.0", layout="wide")
st.sidebar.title("🚚 Gestión Logística")
modulo = st.sidebar.radio("Navegación:", [
    "1. Administración", 
    "2. Recepción Bodega", 
    "3. Despacho & Monitor", 
    "4. Edición de Datos"
])

# --- MODULO 1: ADMINISTRACIÓN ---
if modulo == "1. Administración":
    st.header("Registro de Maestros")
    t1, t2, t3 = st.tabs(["Clientes", "Mensajeros", "Productos"])
    db = SessionLocal()
    with t1:
        with st.form("f_cli", clear_on_submit=True):
            n = st.text_input("Nombre Empresa").upper()
            nit = st.text_input("NIT")
            if st.form_submit_button("Guardar"):
                try:
                    db.add(ClientB2B(name=n, nit=nit)); db.commit()
                    st.success("Registrado.")
                except: st.error("Duplicado.")
    with t2:
        with st.form("f_cou", clear_on_submit=True):
            cn = st.text_input("Nombre Mensajero").upper()
            cp = st.text_input("Placa").upper()
            if st.form_submit_button("Guardar"):
                try:
                    db.add(Courier(name=cn, plate=cp)); db.commit()
                    st.success("Registrado.")
                except: st.error("Placa duplicada.")
    db.close()

# --- MODULO 2: RECEPCIÓN ---
elif modulo == "2. Recepción Bodega":
    st.header("Ingreso Alfanumérico")
    db = SessionLocal()
    clis = db.query(ClientB2B).all()
    if clis:
        c_sel = st.selectbox("Cliente", [c.name for c in clis])
        cli = db.query(ClientB2B).filter(ClientB2B.name == c_sel).first()
        def reg():
            g = st.session_state.b_in.strip().upper()
            if g:
                if not db.query(Package).filter(Package.tracking_number == g).first():
                    db.add(Package(tracking_number=g, client_id=cli.id)); db.commit()
                    st.toast(f"✅ {g} en bodega")
                st.session_state.b_in = ""
        st.text_input("ESCÁNER BODEGA", key="b_in", on_change=reg)
    db.close()

# --- MODULO 3: DESPACHO & MONITOR ---
elif modulo == "3. Despacho & Monitor":
    st.header("Control de Salidas")
    db = SessionLocal()
    mens = db.query(Courier).filter(Courier.is_active == True).all()
    col1, col2 = st.columns([1, 2])
    with col1:
        if mens:
            m_sel = st.selectbox("Mensajero", [f"{m.name} ({m.plate})" for m in mens])
            m_obj = db.query(Courier).filter(Courier.name == m_sel.split(" (")[0]).first()
            def desp():
                g = st.session_state.b_out.strip().upper()
                if g:
                    pkg = db.query(Package).filter(Package.tracking_number == g).first()
                    if pkg:
                        pkg.status = "EN RUTA"; pkg.courier_id = m_obj.id; db.commit()
                        st.toast(f"🚚 {g} -> {m_obj.name}")
                    else: st.error("No existe.")
                    st.session_state.b_out = ""
            st.text_input("ESCÁNER DESPACHO", key="b_out", on_change=desp)
    with col2:
        carga = db.query(Courier.name, func.count(Package.id)).join(Package).filter(Package.status == "EN RUTA").group_by(Courier.name).all()
        if carga:
            st.table(pd.DataFrame(carga, columns=["Mensajero", "Guías"]))
            with st.expander("Ver detalle de guías"):
                det = db.query(Package.tracking_number, Courier.name).join(Courier).filter(Package.status == "EN RUTA").all()
                st.dataframe(pd.DataFrame(det, columns=["Guía", "Lleva"]), use_container_width=True)
    db.close()

# --- MODULO 4: EDICIÓN COMPLETA ---
elif modulo == "4. Edición de Datos":
    st.header("Corrección de Errores")
    db = SessionLocal()
    op = st.radio("Editar:", ["Clientes", "Mensajeros"])
    if op == "Clientes":
        items = db.query(ClientB2B).all()
        if items:
            sel = st.selectbox("Elegir:", [i.name for i in items])
            obj = db.query(ClientB2B).filter(ClientB2B.name == sel).first()
            with st.form("e_c"):
                n = st.text_input("Nombre", value=obj.name).upper()
                nit = st.text_input("NIT", value=obj.nit)
                if st.form_submit_button("Actualizar"):
                    obj.name = n; obj.nit = nit; db.commit(); st.rerun()
    elif op == "Mensajeros":
        items = db.query(Courier).all()
        if items:
            sel = st.selectbox("Elegir:", [i.name for i in items])
            obj = db.query(Courier).filter(Courier.name == sel).first()
            with st.form("e_m"):
                n = st.text_input("Nombre", value=obj.name).upper()
                p = st.text_input("Placa", value=obj.plate).upper()
                if st.form_submit_button("Actualizar"):
                    obj.name = n; obj.plate = p; db.commit(); st.rerun()
    db.close()
