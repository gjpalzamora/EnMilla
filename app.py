import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Boolean, func, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, scoped_session
from sqlalchemy.exc import IntegrityError
from datetime import datetime
import io

# Intenta importar pytz. Si no está, maneja el error o informa al usuario.
try:
    import pytz
    TIMEZONE = pytz.timezone('UTC') # Configuración de la zona horaria (ajusta según tu necesidad)
    PYTZ_AVAILABLE = True
except ImportError:
    st.warning("La librería 'pytz' no está instalada. Las fechas se mostrarán en UTC. Instálala con: pip install pytz")
    # Define una fecha ficticia o usa datetime.utcnow directamente si pytz no está disponible
    TIMEZONE = None 
    PYTZ_AVAILABLE = False

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
        # Si pytz está disponible y la zona horaria está configurada
        if PYTZ_AVAILABLE and TIMEZONE:
            try:
                # Intenta convertir a la zona horaria configurada si el datetime no tiene zona
                if dt.tzinfo is None:
                    dt_local = TIMEZONE.localize(dt)
                else:
                    dt_local = dt.astimezone(TIMEZONE)
                return dt_local.strftime('%d/%m/%Y %H:%M:%S')
            except Exception as e:
                st.error(f"Error al formatear fecha con zona horaria: {e}")
                # Si hay error, muestra la fecha sin zona horaria
                return dt.strftime('%d/%m/%Y %H:%M:%S')
        else:
            # Si pytz no está disponible o no se configuró, muestra la fecha como está (probablemente UTC)
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
    # Se han añadido pestañas para edición dentro del mismo módulo de administración
    # Corrección: Se eliminaron los emojis de las cadenas de texto de las pestañas para evitar errores de sintaxis.
    tab_cli, tab_cou, tab_prod, tab_edit_cli, tab_edit_cou, tab_edit_prod = st.tabs([
        "Clientes", "Mensajeros", "Productos",
        "
