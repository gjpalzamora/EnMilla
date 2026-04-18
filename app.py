import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

# --- 1. CONFIGURACIÓN DE BASE DE DATOS ---
DATABASE_URL = "sqlite:///enmilla_final.db" # Cambiar a PostgreSQL en producción
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- 2. MODELOS DE DATOS (MÓDULO 1: ADMINISTRACIÓN) ---

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

# --- MODELOS DE OPERACIONES (MÓDULO 2) ---

class Package(Base):
    __tablename__ = "packages"
    id = Column(Integer, primary_key=True, index=True)
    tracking_number = Column(String(100), unique=True, index=True)
    client_id = Column(Integer, ForeignKey("clients_b2b.id"), nullable=True) # B2B
    recipient_name = Column(String(255)) # B2C
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

# --- 3. INTERFAZ DE USUARIO ---
st.set_page_config(page_title="EnMilla ERP v1.0", layout="wide")
st.sidebar.title("🚚 Panel de Control")
modulo = st.sidebar.selectbox("Seleccione Módulo", [
    "1. Administración (Maestros)",
    "2. Operaciones (Recepción/Conciliación)",
    "3. Despacho (Cargue a Ruta)"
])

# --- LÓGICA MÓDULO 1: ADMINISTRACIÓN ---
if modulo == "1. Administración (Maestros)":
    st.header("Gestión de Clientes, Mensajeros y Productos")
    tab1, tab2, tab3 = st.tabs(["Clientes B2B", "Mensajeros", "Productos"])
    
    with tab1:
        with st.form("new_client"):
            n = st.text_input("Nombre Empresa"); nit = st.text_input("NIT")
            if st.form_submit_button("Guardar"):
                db = SessionLocal(); db.add(ClientB2B(name=n, nit=nit)); db.commit(); db.close()
                st.success("Cliente Creado")

    with tab2:
        with st.form("new_courier"):
            cn = st.text_input("Nombre Mensajero"); cp = st.text_input("Placa")
            if st.form_submit_button("Registrar"):
                db = SessionLocal(); db.add(Courier(name=cn, plate=cp)); db.commit(); db.close()
                st.success("Mensajero Registrado")

    with tab3:
        db = SessionLocal(); clients = db.query(ClientB2B).all()
        with st.form("new_prod"):
            pn = st.text_input("Nombre del Producto")
            cid = st.selectbox("Cliente Propietario", [c.name for c in clients])
            if st.form_submit_button("Enlazar Producto"):
                target = db.query(ClientB2B).filter(ClientB2B.name == cid).first()
                db.add(Product(name=pn, client_id=target.id)); db.commit()
                st.success(f"Producto {pn} enlazado a {cid}")
        db.close()

# --- LÓGICA MÓDULO 2: OPERACIONES ---
elif modulo == "2. Operaciones (Recepción/Conciliación)":
    st.header("Recepción y Vinculación B2B/B2C")
    sub_tab1, sub_tab2 = st.tabs(["Recepción Masiva", "Carga de Manifiesto (Excel)"])
    
    with sub_tab1:
        with st.form("recepcion", clear_on_submit=True):
            t = st.text_input("ESCANEE TRACKING (Ingreso a Bodega)")
            if st.form_submit_button("REGISTRAR") or t:
                db = SessionLocal()
                if not db.query(Package).filter(Package.tracking_number == t).first():
                    p = Package(tracking_number=t)
                    db.add(p); db.commit()
                    db.add(Movement(package_id=p.id, location="Bodega", description="Ingreso Masivo"))
                    db.commit(); st.toast(f"Guía {t} en bodega")
                db.close()

    with sub_tab2:
        st.info("Suba el Excel para unir Trackings con Clientes B2C")
        db = SessionLocal(); clients = db.query(ClientB2B).all()
        c_sel = st.selectbox("Seleccione Cliente Origen (B2B)", [c.name for c in clients])
        file = st.file_uploader("Archivo CSV")
        if file and st.button("Procesar"):
            df = pd.read_csv(file) # Columnas: tracking, destinatario, direccion
            client_obj = db.query(ClientB2B).filter(ClientB2B.name == c_sel).first()
            for _, row in df.iterrows():
                pkg = db.query(Package).filter(Package.tracking_number == str(row['tracking'])).first()
                if pkg:
                    pkg.client_id = client_obj.id; pkg.recipient_name = row['destinatario']; pkg.address = row['direccion']
            db.commit(); st.success("Datos Conciliados")
        db.close()

# --- LÓGICA MÓDULO 3: DESPACHO ---
elif modulo == "3. Despacho (Cargue a Ruta)":
    st.header("Salida de Mensajeros")
    db = SessionLocal(); couriers = db.query(Courier).filter(Courier.is_active == True).all()
    if couriers:
        m_sel = st.selectbox("Seleccione Mensajero", [c.name for c in couriers])
        m_obj = db.query(Courier).filter(Courier.name == m_sel).first()
        with st.form("cargue", clear_on_submit=True):
            t_salida = st.text_input("Escanee para Despacho")
            if st.form_submit_button("ASIGNAR A RUTA"):
                pkg = db.query(Package).filter(Package.tracking_number == t_salida).first()
                if pkg:
                    pkg.status = "En Ruta"
                    db.add(Movement(package_id=pkg.id, courier_id=m_obj.id, location="En Ruta", description=f"Cargado por {m_sel}"))
                    db.commit(); st.success(f"Guía {t_salida} asignada")
    db.close()
