import os
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
from sqlalchemy.sql import func

# --- Configuración del Motor ---
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://enlace_user:mi_contrasena@localhost:5432/enlaces360_db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- 1. CLIENTES (Dueños de la mercancía: Temu, Shein, etc.) ---
class ClientB2B(Base):
    __tablename__ = "clients_b2b"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True, index=True)
    nit = Column(String(50), nullable=False, unique=True)
    
    packages = relationship("Package", back_populates="client")

# --- 2. MENSAJEROS (Recurso Humano en terreno) ---
class Courier(Base):
    __tablename__ = "couriers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    document_id = Column(String(50), nullable=False, unique=True, index=True) # Cédula
    phone = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True)
    
    packages = relationship("Package", back_populates="courier")
    logs = relationship("PackageLog", back_populates="courier")

# --- 3. PAQUETES (El Inventario Físico) ---
class Package(Base):
    __tablename__ = "packages"
    id = Column(Integer, primary_key=True, index=True)
    tracking_number = Column(String(100), unique=True, index=True, nullable=False) # Guía del cliente
    
    # Información de contacto para validación en terreno
    recipient_name = Column(String(255))
    address = Column(String(500))
    phone = Column(String(100))
    
    # Estados lógicos: 'PRE-CARGADO', 'EN_BODEGA', 'EN_REPARTO', 'ENTREGADO', 'DEVUELTO_CLIENTE'
    status = Column(String(50), default="PRE-CARGADO")
    
    # Contador de intentos de entrega
    delivery_attempts = Column(Integer, default=0)
    
    client_id = Column(Integer, ForeignKey("clients_b2b.id"))
    courier_id = Column(Integer, ForeignKey("couriers.id"), nullable=True) # Quién lo tiene actualmente
    
    client = relationship("ClientB2B", back_populates="packages")
    courier = relationship("Courier", back_populates="packages")
    logs = relationship("PackageLog", back_populates="package")

# --- 4. TRAZABILIDAD (La Hoja de Vida / Logs) ---
class PackageLog(Base):
    __tablename__ = "package_logs"
    id = Column(Integer, primary_key=True)
    package_id = Column(Integer, ForeignKey("packages.id"))
    
    # Acción realizada: 'INGRESO_BODEGA', 'CARGUE_MENSAJERO', 'INTENTO_FALLIDO', 'ENTREGADO', 'AUDITORIA_BODEGA'
    action = Column(String(100))
    
    # Actores involucrados
    courier_id = Column(Integer, ForeignKey("couriers.id"), nullable=True) # Mensajero asignado
    operator_id = Column(String(100)) # Quién pistoleó en bodega
    
    # Observación para las causales (Ausente, Cerrado, etc.)
    observation = Column(String(500), nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    package = relationship("Package", back_populates="logs")
    courier = relationship("Courier", back_populates="logs")

# --- 5. USUARIOS DEL SISTEMA (Operarios de Bodega) ---
class SystemUser(Base):
    __tablename__ = "system_users"
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False) # Para seguridad individual
    full_name = Column(String(255))

# --- Inicialización ---
def create_all_tables():
    Base.metadata.create_all(bind=engine)
