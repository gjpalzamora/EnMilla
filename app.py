import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Boolean, func, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, scoped_session
from datetime import datetime
import io

# --- 1. CONFIGURACIÓN DE BASE DE DATOS ---
DATABASE_URL = "sqlite:///enmilla_v15_final.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Session = scoped_session(session_factory)
Base = declarative_base()

# --- 2. MODELOS DE DATOS ---
class ClientB2B(Base):
    __tablename__ = "clients_b2b"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, nullable=False)
    nit = Column(String(50), unique=True)
    packages = relationship("Package", back_populates="client")
    products = relationship("Product", back_populates="client")

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    client_id = Column(Integer, ForeignKey("clients_b2b.id"))
    price_to_client = Column(Float, default=0.0)
    cost_to_courier = Column(Float, default=0.0)
    client = relationship("ClientB2B", back_populates="products")

class Courier(Base):
    __tablename__ = "couriers"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    plate = Column(String(50), unique=True, nullable=False)
    is_active = Column(Boolean, default=True)
    packages = relationship("Package", back_populates="courier")

class Package(Base):
    __tablename__ = "packages"
    id = Column(Integer, primary_key=True)
    tracking_number = Column(String(100), unique=True, index=True, nullable=False)
    client_id = Column(Integer, ForeignKey("clients_b2b.id"))
    courier_id = Column(Integer, ForeignKey("couriers.id"), nullable=True)
    product_name = Column(String(255))
    income = Column(Float, default=0.0)
    expense = Column(Float, default=0.0)
    cash_collected = Column(Float, default=0.0)
    status = Column(String(50), default="BODEGA")
    created_at = Column(DateTime, default=datetime.utcnow)
    delivered_at = Column(DateTime, nullable=True)
    
    client = relationship("ClientB2B", back_populates="packages")
    courier = relationship("Courier", back_populates="packages")
    movements = relationship("Movement", back_populates="package", cascade="all, delete-orphan")

class Movement(Base):
    __tablename__ = "movements"
    id = Column(Integer, primary_key=True)
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
st.set_page_config(page_title="EnMilla ERP v15.1", layout="wide")
st.sidebar.title("🚚 Panel EnMilla")
modulo = st.sidebar.radio("Ir a:", [
    "1. Administración", 
    "2. Recepción (Bodega)", 
    "3. Despacho (Ruta)", 
    "4. Entregas y Recaudos",
    "5. Novedades",
    "6. Reportes"
])

# --- MÓDULO 1: ADMINISTRACIÓN ---
if modulo == "1. Administración":
    st.header("Gestión de Maestros")
    t1, t2, t3 = st.tabs(["🏢 Clientes", "🛵 Mensajeros", "📦 Productos"])
    
    with t1:
        with st.form("f_cli", clear_on_submit=True):
            n = st.text_input("Nombre Empresa").upper()
            nit = st.text_input("NIT")
            if st.form_submit_button("Crear Cliente"):
                with Session() as db:
                    try:
                        db.add(ClientB2B(name=n, nit=nit))
                        db.commit()
                        st.success("✅ Guardado")
                    except Exception as e:
                        db.rollback()
                        st.error(f"❌ Error: {e}")

    with t2:
        with st.form("f_cou", clear_on_submit=True):
            cn = st.text_input("Nombre Mensajero").upper()
            cp = st.text_input("Placa").upper()
            if st.form_submit_button("Registrar Mensajero"):
                with Session() as db:
                    try:
                        db.add(Courier(name=cn, plate=cp))
                        db.commit()
                        st.success("✅ Registrado")
                    except Exception as e:
                        db.rollback()
                        st.error(f"❌ Error: {e}")

    with t3:
        # ESTA ES LA FUNCIÓN QUE PEDISTE: CREAR PRODUCTO
        with Session() as db:
            clis = db.query(ClientB2B).all()
            if clis:
                with st.form("f_prod", clear_on_submit=True):
                    c_sel = st.selectbox("Asociar a Cliente", [c.name for c in clis])
                    p_n = st.text_input("Nombre del Servicio (Ej: Express)").upper()
                    c1, c2 = st.columns(2)
                    p_c = c1.number_input("Cobro al Cliente ($)", min_value=0.0)
                    p_m = c2.number_input("Pago al Mensajero ($)", min_value=0.0)
                    if st.form_submit_button("Guardar Producto"):
                        target = db.query(ClientB2B).filter(ClientB2B.name == c_sel).first()
                        db.add(Product(name=p_n, client_id=target.id, price_to_client=p_c, cost_to_courier=p_m))
                        db.commit()
                        st.success(f"✅ Producto '{p_n}' creado para {c_sel}")
            else:
                st.warning("Primero debe crear un cliente en la pestaña de al lado.")

# --- MÓDULO 2: RECEPCIÓN ---
elif modulo == "2. Recepción (Bodega)":
    st.header("Entrada de Mercancía")
    with Session() as db:
        clis = db.query(ClientB2B).all()
        if clis:
            c_name = st.
