import os
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Boolean, Float
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
from sqlalchemy.sql import func

# Configuración de Conexión
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://enlace_user:mi_contrasena@localhost:5432/enlaces360_db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- MODELOS ---

class ClientB2B(Base):
    __tablename__ = "clients_b2b"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)
    nit = Column(String(50), unique=True)
    packages = relationship("Package", back_populates="client")

# Mantenemos 'Product' para evitar el error de importación que ves en pantalla
class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    client_id = Column(Integer, ForeignKey("clients_b2b.id"))
    price_to_client = Column(Float, default=0.0)
    cost_to_courier = Column(Float, default=0.0)

class Courier(Base):
    __tablename__ = "couriers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    document_id = Column(String(50), unique=True, nullable=False) # Cédula
    phone = Column(String(50))
    is_active = Column(Boolean, default=True)
    packages = relationship("Package", back_populates="courier")

class Package(Base):
    __tablename__ = "packages"
    id = Column(Integer, primary_key=True, index=True)
    tracking_number = Column(String(100), unique=True, index=True, nullable=False)
    
    # Datos de contacto
    recipient_name = Column(String(255))
    address = Column(String(500))
    phone = Column(String(100))
    
    # Estados: 'PRE-CARGADO', 'EN_BODEGA', 'EN_REPARTO', 'ENTREGADO', 'DEVUELTO'
    status = Column(String(50), default="PRE-CARGADO")
    delivery_attempts = Column(Integer, default=0)
    
    client_id = Column(Integer, ForeignKey("clients_b2b.id"))
    courier_id = Column(Integer, ForeignKey("couriers.id"), nullable=True)
    
    client = relationship("ClientB2B", back_populates="packages")
    courier = relationship("Courier", back_populates="packages")
    logs = relationship("PackageLog", back_populates="package")

class PackageLog(Base):
    __tablename__ = "package_logs"
    id = Column(Integer, primary_key=True)
    package_id = Column(Integer, ForeignKey("packages.id"))
    action = Column(String(100)) # INGRESO, SALIDA, FALLIDO, AUDITORIA
    courier_id = Column(Integer, ForeignKey("couriers.id"), nullable=True)
    operator_id = Column(String(100)) 
    observation = Column(String(500))
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    package = relationship("Package", back_populates="logs")

# --- UTILIDADES ---

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    Base.metadata.create_all(bind=engine)
