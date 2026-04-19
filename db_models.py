import os
from sqlalchemy import create_engine, Column, Integer, String, Boolean, ForeignKey, DateTime, text
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
from sqlalchemy.sql import func

DATABASE_URL = os.environ.get("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
if not DATABASE_URL:
    DATABASE_URL = "sqlite:///./enmilla_v2.db"

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class ClientB2B(Base):
    __tablename__ = "clients_b2b"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)
    nit = Column(String(50), unique=True)
    products = relationship("Product", back_populates="client", cascade="all, delete-orphan")
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
    document_id = Column(String(50), unique=True, nullable=False)
    phone = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True)
    packages = relationship("Package", back_populates="courier")

class Package(Base):
    __tablename__ = "packages"
    id = Column(Integer, primary_key=True, index=True)
    tracking_number = Column(String(100), unique=True, index=True, nullable=False)
    status = Column(String(50), default="PRE-CARGADO")
    client_id = Column(Integer, ForeignKey("clients_b2b.id"), nullable=True)
    courier_id = Column(Integer, ForeignKey("couriers.id"), nullable=True)
    client = relationship("ClientB2B", back_populates="packages")
    courier = relationship("Courier", back_populates="packages")

class PackageLog(Base):
    __tablename__ = "package_logs"
    id = Column(Integer, primary_key=True)
    package_id = Column(Integer, ForeignKey("packages.id"))
    action = Column(String(100))
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

def create_tables():
    # Creamos las tablas si no existen
    Base.metadata.create_all(bind=engine)
    
    # ATAR CABO SUELTO: Forzar actualización de columnas para SQLite
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE couriers ADD COLUMN phone VARCHAR(50)"))
            conn.commit()
        except Exception:
            pass # Si ya existe, no falla

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
