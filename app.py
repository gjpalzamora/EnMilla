import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Boolean, func, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, scoped_session
from sqlalchemy.exc import IntegrityError
from datetime import datetime
import io

# --- 1. CONFIGURACIÓN DE BASE DE DATOS ---
DATABASE_URL = "sqlite:///enmilla_v16_final.db"
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
    client_id = Column(Integer, ForeignKey("clients_b2b.id"), index=True)
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
    client_id = Column(Integer, ForeignKey("clients_b2b.id"), index=True)
    courier_id = Column(Integer, ForeignKey("couriers.id"), nullable=True, index=True)
    product_name = Column(String(255)) # Se puede mejorar asociando a Product.id si es necesario
    income = Column(Float, default=0.0)
    expense = Column(Float, default=0.0)
    cash_collected = Column(Float, default=0.0)
    status = Column(String(50), default="BODEGA") # Ej: BODEGA, EN RUTA, ENTREGADO, FALLIDO, DEVUELTO
    created_at = Column(DateTime, default=datetime.utcnow)
    delivered_at = Column(DateTime, nullable=True)

    client = relationship("ClientB2B", back_populates="packages")
    courier = relationship("Courier", back_populates="packages")
    movements = relationship("Movement", back_populates="package")

class Movement(Base):
    __tablename__ = "movements"
    id = Column(Integer, primary_key=True)
    package_id = Column(Integer, ForeignKey("packages.id"), index=True)
    description = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    package = relationship("Package", back_populates="movements") # Corrección: Movement pertenece a un Package

Base.metadata.create_all(bind=engine)

# --- 3. FUNCIONES DE APOYO ---
def to_excel(df):
    """Convierte un DataFrame de Pandas a un archivo Excel en memoria."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Reporte')
    processed_data = output.getvalue()
    return processed_data

# --- 4. INTERFAZ PRINCIPAL ---
st.set_page_config(page_title="EnMilla ERP v16", layout="wide")
st.sidebar.title("🚚 Panel EnMilla")

modulo = st.sidebar.radio("Ir a:", [
    "1. Administración (Maestros)",
    "2. Recepción (Bodega)",
    "3. Despacho (Ruta)",
    "4. Gestión de Cobros",
    "5. Reportes"
])

# --- MÓDULO 1: ADMINISTRACIÓN (MAESTROS) ---
if modulo == "1. Administración (Maestros)":
    st.header("Gestión de Maestros")
    tab_cli, tab_cou, tab_prod = st.tabs(["🏢 Clientes", "🛵 Mensajeros", "📦 Productos"])

    with tab_cli:
        st.subheader("Registrar Nuevo Cliente B2B")
        with st.form("form_cliente", clear_on_submit=True):
            nombre_cli = st.text_input("Nombre de la Empresa").upper()
            nit_cli = st.text_input("NIT (Opcional)")

            if st.form_submit_button("Guardar Cliente"):
                if not nombre_cli:
                    st.warning("El nombre del cliente es obligatorio.")
                else:
                    with Session() as db:
                        try:
                            nuevo_cliente = ClientB2B(name=nombre_cli, nit=nit_cli)
                            db.add(nuevo_cliente)
                            db.commit()
                            st.success(f"✅ Cliente '{nombre_cli}' guardado exitosamente.")
                            st.rerun() # Refrescar la página para ver el nuevo cliente
                        except IntegrityError:
                            db.rollback()
                            st.error(f"❌ Error: El nombre '{nombre_cli}' o NIT '{nit_cli}' ya existe.")
                        except Exception as e:
                            db.rollback()
                            st.error(f"❌ Ocurrió un error inesperado: {e}")

    with tab_cou:
        st.subheader("Registrar Nuevo Mensajero")
        with st.form("form_courier", clear_on_submit=True):
            nombre_courier = st.text_input("Nombre del Mensajero").upper()
            placa_courier = st.text_input("Placa del Vehículo").upper()

            if st.form_submit_button("Guardar Mensajero"):
                if not nombre_courier or not placa_courier:
                    st.warning("El nombre y la placa del mensajero son obligatorios.")
                else:
                    with Session() as db:
                        try:
                            nuevo_courier = Courier(name=nombre_courier, plate=placa_courier)
                            db.add(nuevo_courier)
                            db.commit()
                            st.success(f"✅ Mensajero '{nombre_courier}' con placa '{placa_courier}' registrado.")
                            st.rerun() # Refrescar la página
                        except IntegrityError:
                            db.rollback()
                            st.error(f"❌ Error: La placa '{placa_courier}' ya está registrada.")
                        except Exception as e:
                            db.rollback()
                            st.error(f"❌ Ocurrió un error inesperado: {e}")

    with tab_prod:
        st.subheader("Registrar Nuevo Producto")
        with Session() as db:
            clientes_db = db.query(ClientB2B).order_by(ClientB2B.name).all()
            if not clientes_db:
                st.warning("Primero debe registrar al menos un cliente para poder agregar productos.")
            else:
                nombres_clientes = [c.name for c in clientes_db]
                with st.form("form_prod", clear_on_submit=True):
                    nombre_prod = st.text_input("Nombre del Producto").upper()
                    cliente_asociado_nombre = st.selectbox("Asociar a Cliente", nombres_clientes)
                    precio_cliente = st.number_input("Precio para el Cliente ($)", min_value=0.0, format="%.2f")
                    costo
