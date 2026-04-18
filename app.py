import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Boolean, func, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, scoped_session
from sqlalchemy.exc import IntegrityError
from datetime import datetime
import io
import pytz # Para manejo de zonas horarias si es necesario

# --- CONFIGURACIÓN GLOBAL ---
# Configuración de la zona horaria (ajusta según tu necesidad)
# Puedes usar 'UTC' o una zona horaria específica como 'America/Bogota'
TIMEZONE = pytz.timezone('UTC') 

# --- 1. CONFIGURACIÓN DE BASE DE DATOS ---
DATABASE_URL = "sqlite:///enmilla_v16_final.db"
# 'connect_args={"check_same_thread": False}' es necesario para SQLite con Streamlit
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Configuración de la sesión para manejar múltiples peticiones en Streamlit
session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Session = scoped_session(session_factory) # scoped_session maneja sesiones por hilo/request

Base = declarative_base()

# --- 2. MODELOS DE DATOS ---
class ClientB2B(Base):
    __tablename__ = "clients_b2b"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, nullable=False)
    nit = Column(String(50), unique=True)
    # Relaciones bidireccionales
    packages = relationship("Package", back_populates="client")
    products = relationship("Product", back_populates="client")

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    client_id = Column(Integer, ForeignKey("clients_b2b.id"), index=True) # Indexar para búsquedas por cliente
    price_to_client = Column(Float, default=0.0) # Valor que cobra el cliente al destinatario final
    cost_to_courier = Column(Float, default=0.0) # Costo que paga la empresa al mensajero
    # Relación con el cliente
    client = relationship("ClientB2B", back_populates="products")

class Courier(Base):
    __tablename__ = "couriers"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    plate = Column(String(50), unique=True, nullable=False)
    is_active = Column(Boolean, default=True)
    # Relación con los paquetes que maneja
    packages = relationship("Package", back_populates="courier")

class Package(Base):
    __tablename__ = "packages"
    id = Column(Integer, primary_key=True)
    tracking_number = Column(String(100), unique=True, index=True, nullable=False)
    client_id = Column(Integer, ForeignKey("clients_b2b.id"), index=True) # Indexar para búsquedas por cliente
    courier_id = Column(Integer, ForeignKey("couriers.id"), nullable=True, index=True) # Indexar si se busca por mensajero
    product_name = Column(String(255)) # Nombre del producto (podría ser FK a Product si se requiere más detalle)
    income = Column(Float, default=0.0) # Valor total cobrado al destinatario (incluye costo de envío + valor del producto)
    expense = Column(Float, default=0.0) # Costo total para la empresa (ej. pago al mensajero)
    cash_collected = Column(Float, default=0.0) # Dinero efectivamente cobrado al destinatario
    status = Column(String(50), default="BODEGA") # Ej: BODEGA, EN RUTA, ENTREGADO, FALLIDO, DEVUELTO
    created_at = Column(DateTime, default=datetime.utcnow) # Fecha de registro inicial
    delivered_at = Column(DateTime, nullable=True) # Fecha de entrega exitosa

    # Relaciones bidireccionales
    client = relationship("ClientB2B", back_populates="packages")
    courier = relationship("Courier", back_populates="packages")
    movements = relationship("Movement", back_populates="package")

class Movement(Base):
    __tablename__ = "movements"
    id = Column(Integer, primary_key=True)
    package_id = Column(Integer, ForeignKey("packages.id"), index=True) # Indexar para búsquedas por paquete
    description = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    # Corrección de la relación: Movement pertenece a un Package
    package = relationship("Package", back_populates="movements")

# Crea las tablas en la base de datos si no existen
Base.metadata.create_all(bind=engine)

# --- 3. FUNCIONES DE APOYO ---
def to_excel(df):
    """Convierte un DataFrame de Pandas a un archivo Excel en memoria."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Reporte')
    processed_data = output.getvalue()
    return processed_data

def format_datetime(dt):
    """Formatea un objeto datetime a string con zona horaria."""
    if dt:
        # Asegúrate de que el datetime esté en la zona horaria correcta si no lo está ya
        # Si tus datetimes están en UTC y quieres mostrarlos en TIMEZONE:
        # dt_local = dt.astimezone(TIMEZONE)
        # return dt_local.strftime('%d/%m/%Y %H:%M:%S')
        # Si solo quieres mostrarlo como está (asumiendo que ya está en la zona deseada o UTC):
        return dt.strftime('%d/%m/%Y %H:%M:%S')
    return "N/A"

# --- 4. INTERFAZ PRINCIPAL ---
st.set_page_config(page_title="EnMilla ERP v16", layout="wide")
st.sidebar.title("🚚 Panel EnMilla")

# Menú de navegación
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
    tab_cli, tab_cou, tab_prod, tab_edit_cli, tab_edit_cou, tab_edit_prod = st.tabs([
        "🏢 Clientes", "🛵 Mensajeros", "📦 Productos",
        "✏️ Editar Clientes", "✏️ Editar Mensajeros", "✏️ Editar Productos"
    ])

    # --- Submódulo: Registrar Nuevos ---
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
        with st.form("
