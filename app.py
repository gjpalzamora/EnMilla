import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

# --- CONFIGURACIÓN BASE DE DATOS ---
DATABASE_URL = "sqlite:///enmilla_final.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- MODELOS (MÓDULO 1) ---
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

# --- INTERFAZ ---
st.set_page_config(page_title="EnMilla ERP v1.1", layout="wide")
st.sidebar.title("🚚 Operaciones Enmilla")
modulo = st.sidebar.radio("Navegación", [
    "1. Administración (Crear)",
    "2. Operaciones (Recibir)",
    "3. Despacho (Cargar)",
    "4. Gestión de Datos (Ver/Editar)"
])

# --- MÓDULO 4: GESTIÓN DE DATOS (VER Y EDITAR) ---
if modulo == "4. Gestión de Datos (Ver/Editar)":
    st.header("Visualización y Edición de Maestros")
    edit_tab1, edit_tab2 = st.tabs(["Clientes B2B", "Mensajeros"])

    with edit_tab1:
        db = SessionLocal()
        clientes = db.query(ClientB2B).all()
        if clientes:
            df_cli = pd.DataFrame([{"ID": c.id, "Nombre": c.name, "NIT": c.nit} for c in clientes])
            st.dataframe(df_cli, use_container_width=True)
            
            st.subheader("Editar Cliente")
            cli_to_edit = st.selectbox("Seleccione cliente para modificar", [c.name for c in clientes])
            target_cli = db.query(ClientB2B).filter(ClientB2B.name == cli_to_edit).first()
            
            with st.form("edit_cli_form"):
                new_n = st.text_input("Nuevo Nombre", value=target_cli.name)
                new_nit = st.text_input("Nuevo NIT", value=target_cli.nit)
                if st.form_submit_button("Actualizar Cliente"):
                    try:
                        target_cli.name = new_n
                        target_cli.nit = new_nit
                        db.commit()
                        st.success("Información de cliente actualizada.")
                        st.rerun()
                    except Exception as e:
                        db.rollback()
                        st.error("No se pudo actualizar. Pos
