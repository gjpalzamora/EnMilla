# db_models.py

import os
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float, Boolean, ForeignKey
from sqlalchemy.orm import sessionmaker, Session as SQLASession # Renombramos para evitar conflicto con st.Session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import pytz # Necesario para manejo de zonas horarias

# --- Configuración de la Base de Datos ---
# Intenta obtener la URL de la base de datos de una variable de entorno.
# Si no existe, usa una URL de conexión local por defecto.
# ¡IMPORTANTE! Reemplaza los detalles de la conexión local si son diferentes.
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://enlace_user:mi_contrasena@localhost:5432/enlaces360_db")

# Crear el motor de la base de datos
try:
    engine = create_engine(DATABASE_URL)
    Base = declarative_base()
    # Crear una fábrica de sesiones
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
except Exception as e:
    # Manejar error si la conexión falla al iniciar
    print(f"Error al crear el motor de la base de datos: {e}")
    # Podrías querer lanzar una excepción o establecer variables a None para indicar fallo
    engine = None
    Base = None
    SessionLocal = None

# --- Función para obtener sesión de BD ---
def get_db():
    """Generador para obtener una sesión de base de datos."""
    if SessionLocal is None:
        print("Error: SessionLocal no está inicializado. La conexión a la BD falló.")
        return None # O lanzar una excepción
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Función para crear tablas (solo para desarrollo inicial) ---
def create_tables():
    """Crea todas las tablas definidas en los modelos si no existen."""
    if Base is None or engine is None:
        print("Error: Base o engine no están inicializados. No se pueden crear tablas.")
        return
    try:
        Base.metadata.create_all(bind=engine)
        print("Tablas de base de datos verificadas/creadas.")
    except Exception as e:
        print(f"Error al crear tablas: {e}")

# --- Manejo de Zona Horaria ---
# Define la zona horaria a usar. 'UTC' es una buena práctica para el almacenamiento.
# Si necesitas una zona horaria específica para mostrar, puedes usar pytz.
TIMEZONE = pytz.timezone('UTC')
PYTZ_AVAILABLE = True # Bandera para indicar si pytz está disponible

def format_datetime_utc(dt):
    """Formatea un datetime a string UTC o local si es necesario."""
    if dt is None:
        return ""
    try:
        # Si el datetime ya tiene timezone info (es aware)
        if dt.tzinfo is not None and dt.tzinfo.utcoffset(dt) is not None:
            # Convertir a UTC si no lo está ya
            dt_utc = dt.astimezone(TIMEZONE)
        else:
            # Si es naive, asumir que está en UTC (o la zona horaria por defecto)
            dt_utc = TIMEZONE.localize(dt)
            
        # Formato común: YYYY-MM-DD HH:MM:SS UTC
        return dt_utc.strftime('%Y-%m-%d %H:%M:%S') + " UTC"
    except Exception as e:
        print(f"Error al formatear fecha {dt}: {e}")
        return str(dt) # Devolver la representación string si falla el formato


# --- Definición de Modelos SQLAlchemy ---

# --- Modelo ClientB2B ---
class ClientB2B(Base):
    __tablename__ = "clients_b2b"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True, index=True)
    nit = Column(String(50), nullable=False, unique=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relaciones (si las hubiera, ej: paquetes, envíos)
    packages = relationship("Package", back_populates="client") # Asumiendo que Package existe
    client_shipments = relationship("ClientShipment", back_populates="client") # Asumiendo que ClientShipment existe

    def __repr__(self):
        return f"<ClientB2B(id={self.id}, name='{self.name}', nit='{self.nit}')>"

# --- Modelo Product ---
class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    client_id = Column(Integer, ForeignKey("clients_b2b.id"), nullable=False)
    price_to_client = Column(Float, nullable=False)
    cost_to_courier = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relaciones
    client = relationship("ClientB2B", back_populates="products")
    client_shipments = relationship("ClientShipment", back_populates="product") # Asumiendo que ClientShipment existe

    # Constraint para asegurar que el nombre del producto sea único por cliente
    __table_args__ = (UniqueConstraint('name', 'client_id', name='_name_client_uc'),)

    def __repr__(self):
        return f"<Product(id={self.id}, name='{self.name}', client_id={self.client_id})>"

# --- Modelo Courier (Mensajero) ---
class Courier(Base):
    __tablename__ = "couriers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True, index=True)
    phone = Column(String(50), nullable=True)
    plate = Column(String(20), nullable=True, unique=True, index=True) # Placa del vehículo
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relaciones
    packages = relationship("Package", back_populates="courier") # Asumiendo que Package existe
    routes = relationship("Route", back_populates="courier") # Asumiendo que Route existe

    def __repr__(self):
        return f"<Courier(id={self.id}, name='{self.name}', plate='{self.plate}', is_active={self.is_active})>"

# --- Modelos Adicionales (Ejemplos - ¡Asegúrate de tenerlos si los necesitas!) ---
# Si no los tienes definidos en tu archivo 'base de datos.py' o 'modelos.py',
# deberás definirlos aquí o adaptar las relaciones anteriores.

# Ejemplo de Modelo Package (si lo usas)
class Package(Base):
    __tablename__ = "packages"
    id = Column(Integer, primary_key=True, index=True)
    tracking_number = Column(String(100), unique=True, index=True)
    client_id = Column(Integer, ForeignKey("clients_b2b.id"), nullable=False)
    courier_id = Column(Integer, ForeignKey("couriers.id"), nullable=True) # Puede ser null si aún no se asigna mensajero
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True) # Puede ser null si no es un producto específico
    #
