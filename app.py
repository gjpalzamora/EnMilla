import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Boolean, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

# --- 1. CONFIGURACIÓN DE BASE DE DATOS ---
DATABASE_URL = "sqlite:///enmilla_master_v9.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- 2. MODELOS DE DATOS (RESTAURADOS Y COMPLETOS) ---
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
    packages = relationship("Package", back_populates="courier")

class Package(Base):
    __tablename__ = "packages"
    id = Column(Integer, primary_key=True, index=True)
    tracking_number = Column(String(100), unique=True, index=True, nullable=False)
    client_id = Column(Integer, ForeignKey("clients_b2b.id"))
    courier_id = Column(Integer, ForeignKey("couriers.id"), nullable=True)
    product_name = Column(String(255))
    status = Column(String(50), default="BODEGA")
    last_update = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    client = relationship("ClientB2B", back_populates="packages")
    courier = relationship("Courier", back_populates="packages")

class Movement(Base):
    __tablename__ = "movements"
    id = Column(Integer, primary_key=True, index=True)
    package_id = Column(Integer, ForeignKey("packages.id"))
    description = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

# --- 3. INTERFAZ ---
st.set_page_config(page_title="EnMilla ERP v9.0", layout="wide")
st.sidebar.title("🚚 Panel Enmilla")
modulo = st.sidebar.radio("Ir a:", [
    "1. Administración (Crear)", 
    "2. Operaciones (Recibir)", 
    "3. Despacho y Monitoreo", 
    "4. Edición de Maestros"
])

# --- MÓDULO 1: ADMINISTRACIÓN ---
if modulo == "1. Administración (Crear)":
    st.header("Gestión de Maestros")
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
                except: st.error("Error: NIT o Nombre ya existen.")
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
                except: st.error("Error: Placa duplicada.")
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
        db.close()

# --- MÓDULO 2: OPERACIONES (RECEPCIÓN AUTOMÁTICA) ---
elif modulo == "2. Operaciones (Recibir)":
    st.header("Entrada de Mercancía (Scanner Mode)")
    db = SessionLocal()
    clis = db.query(ClientB2B).all()
    if clis:
        col_c, col_p = st.columns(2)
        with col_c:
            c_nom = st.selectbox("Cliente", [c.name for c in clis])
            cli_obj = db.query(ClientB2B).filter(ClientB2B.name == c_nom).first()
        with col_p:
            prods = db.query(Product).filter(Product.client_id == cli_obj.id).all()
            p_nom = st.selectbox("Producto", [p.name for p in prods] if prods else ["GENÉRICO"])

        def registrar_in():
            guia = st.session_state.barcode_in.strip().upper()
            if guia:
                db_s = SessionLocal()
                if not db_s.query(Package).filter(Package.tracking_number == guia).first():
                    p = Package(tracking_number=guia, client_id=cli_obj.id, product_name=p_nom, status="BODEGA")
                    db_s.add(p); db_s.commit()
                    db_s.add(Movement(package_id=p.id, description=f"Ingreso Bodega - {p_nom}"))
                    db_s.commit()
                    st.toast(f"✅ {guia} Recibido")
                db_s.close()
                st.session_state.barcode_in = ""

        st.text_input("ESCANEE AQUÍ", key="barcode_in", on_change=registrar_in)
    db.close()

# --- MÓDULO 3: DESPACHO Y MONITOREO ---
elif modulo == "3. Despacho y Monitoreo":
    st.header("Salida a Ruta y Control de Carga")
    db = SessionLocal()
    mens = db.query(Courier).filter(Courier.is_active == True).all()
    
    col_scan, col_monitor = st.columns([1, 2])
    
    with col_scan:
        st.subheader("Escanear Salida")
        if mens:
            m_sel = st.selectbox("Mensajero", [f"{m.name} | {m.plate}" for m in mens])
            m_id = db.query(Courier).filter(Courier.name == m_sel.split(" | ")[0]).first().id

            def registrar_out():
                guia = st.session_state.barcode_out.strip().upper()
                if guia:
                    db_d = SessionLocal()
                    p = db_d.query(Package).filter(Package.tracking_number == guia).first()
                    if p:
                        p.status = "EN RUTA"
                        p.courier_id = m_id
                        db_d.add(Movement(package_id=p.id, description=f"Despachado con {m_sel}"))
                        db_d.commit()
                        st.toast(f"🚚 {guia} en Ruta")
                    else: st.error("Guía no encontrada.")
                    db_d.close()
                    st.session_state.barcode_out = ""
            st.text_input("ESCANEE PARA DESPACHO", key="barcode_out", on_change=registrar_out)

    with col_monitor:
        st.subheader("Estado de Carga")
        carga = db.query(Courier.name, func.count(Package.id)).join(Package).filter(Package.status == "EN RUTA").group_by(Courier.name).all()
        if carga:
            st.table(pd.DataFrame(carga, columns=["Mensajero", "Paquetes en Ruta"]))
            with st.expander("Ver Detalle por Guía"):
                det = db.query(Package.tracking_number, Courier.name, Package.product_name).join(Courier).filter(Package.status == "EN RUTA").all()
                st.dataframe(pd.DataFrame(det, columns=["Guía", "Mensajero", "Producto"]), use_container_width=True)
        else: st.info("No hay entregas en curso.")
    db.close()

# --- MÓDULO 4: EDICIÓN DE MAESTROS ---
elif modulo == "4. Edición de Maestros":
    st.header("Módulo de Correcciones")
    db = SessionLocal()
    tipo = st.radio("Editar:", ["Productos", "Clientes", "Mensajeros"])
    
    if tipo == "Productos":
        prods = db.query(Product).all()
        if prods:
            p_sel = st.selectbox("Seleccione Producto", [f"{p.id} | {p.name}" for p in prods])
            p_obj = db.query(Product).get(int(p_sel.split(" | ")[0]))
            with st.form("ed_p"):
                new_n = st.text_input("Nuevo nombre", value=p_obj.name).upper()
                if st.form_submit_button("Actualizar"):
                    p_obj.name = new_n; db.commit(); st.success("Actualizado"); st.rerun()

    elif tipo == "Clientes":
        clis = db.query(ClientB2B).all()
        if clis:
            c_sel = st.selectbox("Seleccione Cliente", [c.name for c in clis])
            c_obj = db.query(ClientB2B).filter(ClientB2B.name == c_sel).first()
            with st.form("ed_c"):
                new_n = st.text_input("Nombre Empresa", value=c_obj.name).upper()
                new_nit = st.text_input("NIT", value=c_obj.nit)
                if st.form_submit_button("Actualizar"):
                    c_obj.name = new_n; c_obj.nit = new_nit; db.commit(); st.success("Actualizado"); st.rerun()

    elif tipo == "Mensajeros":
        mens = db.query(Courier).all()
        if mens:
            m_sel = st.selectbox("Seleccione Mensajero", [m.name for m in mens])
            m_obj = db.query(Courier).filter(Courier.name == m_sel).first()
            with st.form("ed_m"):
                new_n = st.text_input("Nombre", value=m_obj.name).upper()
                new_p = st.text_input("Placa", value=m_obj.plate).upper()
                act = st.checkbox("Activo", value=m_obj.is_active)
                if st.form_submit_button("Actualizar"):
                    m_obj.name = new_n; m_obj.plate = new_p; m_obj.is_active = act; db.commit(); st.success("Actualizado"); st.rerun()
    db.close()
