import os
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
from sqlalchemy.sql import func
import pytz

# --- Configuración de la Base de Datos ---
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://enlace_user:mi_contrasena@localhost:5432/enlaces360_db")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- Modelo ClientB2B (Tus clientes: Temu, Shein, etc.) ---
class ClientB2B(Base):
    __tablename__ = "clients_b2b"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True, index=True)
    nit = Column(String(50), nullable=False, unique=True)
    
    packages = relationship("Package", back_populates="client")

# --- Modelo Courier (Mensajeros) ---
class Courier(Base):
    __tablename__ = "couriers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    # Ajuste: Identificación como llave única para evitar duplicados
    document_id = Column(String(50), nullable=False, unique=True, index=True) 
    phone = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True)
    
    packages = relationship("Package", back_populates="courier")
    logs = relationship("PackageLog", back_populates="courier")

# --- Modelo Package (El Corazón del Sistema) ---
class Package(Base):
    __tablename__ = "packages"
    id = Column(Integer, primary_key=True, index=True)
    # La guía externa es nuestra referencia principal
    tracking_number = Column(String(100), unique=True, index=True, nullable=False)
    
    # Datos de contacto (lo que pides para validar en terreno)
    recipient_name = Column(String(255))
    address = Column(String(500))
    phone = Column(String(100))
    
    # Estado Actual: 'BODEGA', 'EN_REPARTO', 'ENTREGADO', 'DEVOLUCION_CLIENTE'
    status = Column(String(50), default="PRE-CARGADO")
    
    # Contador de intentos (Máximo 3 según tu regla)
    delivery_attempts = Column(Integer, default=0)
    
    client_id = Column(Integer, ForeignKey("clients_b2b.id"))
    courier_id = Column(Integer, ForeignKey("couriers.id"), nullable=True)
    
    client = relationship("ClientB2B", back_populates="packages")
    courier = relationship("Courier", back_populates="packages")
    logs = relationship("PackageLog", back_populates="package")

# --- Modelo PackageLog (LA HOJA DE VIDA / TRAZABILIDAD) ---
# Aquí se graba CADA movimiento para el reporte que le das al cliente
class PackageLog(Base):
    __tablename__ = "package_logs"
    id = Column(Integer, primary_key=True)
    package_id = Column(Integer, ForeignKey("packages.id"))
    
    # Qué pasó: 'INGRESO_BODEGA', 'ASIGNADO_A_MENSAJERO', 'INTENTO_FALLIDO', etc.
    action = Column(String(100)) 
    
    # Quién lo tenía (Mensajero) y qué operario hizo el escaneo
    courier_id = Column(Integer, ForeignKey("couriers.id"), nullable=True)
    operator_id = Column(String(100)) # ID del operario que escaneó
    
    observation = Column(String(500)) # Aquí guardamos las "Causales" (Cerrado, Ausente)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    package = relationship("Package", back_populates="logs")
    courier = relationship("Courier", back_populates="logs")

# --- Función de Utilidad para el Cuadre de Inventario ---
def create_tables():
    Base.metadata.create_all(bind=engine)
