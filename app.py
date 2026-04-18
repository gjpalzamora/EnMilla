import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Boolean, func, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, scoped_session
from datetime import datetime
import io

# --- 1. CONFIGURACIÓN DE BASE DE DATOS ---
DATABASE_URL = "sqlite:///enmilla_v14_final.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Session = scoped_session(session_factory)
Base = declarative_base()

# --- 2. MODELOS DE DATOS ---
class ClientB2B(Base):
    __tablename__ = "clients_b2b"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)
    nit = Column(String(50), unique=True)
    packages = relationship("Package", back_populates="client")
    products = relationship("Product", back_populates="client")

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    client_id = Column(Integer, ForeignKey("clients_b2b.id"))
    price_to_client = Column(Float, default=0.0)
    cost_to_courier = Column(Float, default=0.0)
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
    income = Column(Float, default=0.0)
    expense = Column(Float, default=0.0)
    # CORRECCIÓN DE PARÉNTESIS AQUÍ:
    status = Column(String(50), default="BODEGA")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    client = relationship("ClientB2B", back_populates="packages")
    courier = relationship("Courier", back_populates="packages")
    movements = relationship("Movement", back_populates="package", cascade="all, delete-orphan")

class Movement(Base):
    __tablename__ = "movements"
    id = Column(Integer, primary_key=True, index=True)
    package_id = Column(Integer, ForeignKey("packages.id"))
    description = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    package = relationship("Package", back_populates="movements")

Base.metadata.create_all(bind=engine)

# --- 3. FUNCIONES DE APOYO ---
def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Reporte')
    return output.getvalue()

# --- 4. INTERFAZ PRINCIPAL ---
st.set_page_config(page_title="EnMilla ERP v14.5", layout="wide")
st.sidebar.title("🚚 Panel EnMilla")
modulo = st.sidebar.radio("Ir a:", [
    "1. Administración", 
    "2. Operaciones (Recibir)", 
    "3. Despacho (Cargar)", 
    "4. Gestión de Datos"
])

# --- MÓDULO 1: ADMINISTRACIÓN ---
if modulo == "1. Administración":
    st.header("Gestión de Maestros")
    t1, t2, t3 = st.tabs(["🏢 Clientes B2B", "🛵 Mensajeros", "📦 Crear Producto"])
    
    with t1:
        with st.form("form_cliente", clear_on_submit=True):
            n = st.text_input("Nombre de la Empresa").upper()
            nit = st.text_input("NIT")
            if st.form_submit_button("Registrar Cliente"):
                with Session() as db:
                    try:
                        db.add(ClientB2B(name=n, nit=nit))
                        db.commit()
                        st.success(f"✅ Cliente {n} guardado.")
                    except:
                        db.rollback()
                        st.error("❌ Error: El NIT o Nombre ya existen.")

    with t2:
        with st.form("form_courier", clear_on_submit=True):
            cn = st.text_input("Nombre del Mensajero").upper()
            cp = st.text_input("Placa del Vehículo").upper()
            if st.form_submit_button("Registrar Mensajero"):
                with Session() as db:
                    try:
                        db.add(Courier(name=cn, plate=cp))
                        db.commit()
                        st.success(f"✅ Mensajero {cn} registrado.")
                    except:
                        db.rollback()
                        st.error("❌ Error: La placa ya está registrada.")

    with t3:
        with Session() as db:
            clis = db.query(ClientB2B).all()
            if clis:
                with st.form("form_producto", clear_on_submit=True):
                    cli_sel = st.selectbox("Asociar a Cliente", [c.name for c in clis])
                    p_name = st.text_input("Nombre del Producto/Servicio").upper()
                    col_a, col_b = st.columns(2)
                    p_client = col_a.number_input("Precio Cobrado al Cliente ($)", min_value=0.0, step=100.0)
                    p_courier = col_b.number_input("Pago al Mensajero ($)", min_value=0.0, step=100.0)
                    
                    if st.form_submit_button("Guardar Producto"):
                        try:
                            target_cli = db.query(ClientB2B).filter(ClientB2B.name == cli_sel).first()
                            db.add(Product(name=p_name, client_id=target_cli.id, price_to_client=p_client, cost_to_courier=p_courier))
                            db.commit()
                            st.success(f"✅ Producto '{p_name}' creado.")
                        except:
                            db.rollback()
                            st.error("❌ Error al guardar producto.")
            else: st.warning("Cree un cliente primero.")

# --- MÓDULO 2: OPERACIONES (RECIBIR) ---
elif modulo == "2. Operaciones (Recibir)":
    st.header("Entrada de Mercancía")
    with Session() as db:
        clis = db.query(ClientB2B).all()
        if clis:
            cli_n = st.selectbox("Seleccione Cliente", [c.name for c in clis])
            cli_obj = db.query(ClientB2B).filter(ClientB2B.name == cli_n).first()
            
            prods = db.query(Product).filter(Product.client_id == cli_obj.id).all()
            if prods:
                p_sel = st.selectbox("Tipo de Producto", [p.name for p in prods])
                p_obj = db.query(Product).filter(Product.name == p_sel, Product.client_id == cli_obj.id).first()
                st.info(f"Cobro: ${p_obj.price_to_client:,.
