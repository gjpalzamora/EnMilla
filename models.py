# db_models.py

import os
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Boolean, func, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, scoped_session
from sqlalchemy.exc import IntegrityError
from datetime import datetime
import io
import pytz # Asegúrate de tener pytz instalado: pip install pytz

# --- Configuración de Zona Horaria ---
# Usamos UTC como zona horaria estándar.
try:
    TIMEZONE = pytz.timezone('UTC')
    PYTZ_AVAILABLE = True
except ImportError:
    TIMEZONE = None # Si pytz no está, usaremos datetime.utcnow directamente.
    PYTZ_AVAILABLE = False
    print("Advertencia: La librería 'pytz' no está instalada. Las fechas se manejarán en UTC. Instala con: pip install pytz")

# --- Configuración de la Base de Datos (PostgreSQL) ---
# Es CRUCIAL usar variables de entorno para la URL de la base de datos en producción.
# Ejemplo de DATABASE_URL para PostgreSQL:
# "postgresql://USUARIO:CONTRASENA@HOST:PUERTO/NOMBRE_BD"
# Ejemplo: "postgresql://enlace_user:mi_contrasena@localhost:5432/enlaces360_db"

# Intenta obtener la URL de la base de datos de las variables de entorno.
# Si no está disponible (ej: en desarrollo local), usa un valor por defecto (¡DEBES CAMBIARLO!).
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://enlace_user:mi_contrasena@localhost:5432/enlaces360_db")

# Crea el engine de SQLAlchemy para PostgreSQL.
# 'echo=True' es útil para ver las consultas SQL generadas durante el desarrollo.
engine = create_engine(DATABASE_URL, echo=False) 

# Configuración de la sesión para manejar múltiples peticiones.
# scoped_session es importante para aplicaciones web.
session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Session = scoped_session(session_factory)

# Declaración base para los modelos
Base = declarative_base()

# --- Función para obtener una sesión de base de datos ---
def get_db():
    """Proporciona una sesión de base de datos."""
    db = Session()
    try:
        yield db
    finally:
        db.close()

# --- Función para formatear fechas a UTC ---
def format_datetime_utc(dt):
    """Formatea un objeto datetime a string en formato UTC."""
    if dt:
        if dt.tzinfo is None:
            # Si no tiene zona horaria, asumimos que es UTC o la localizamos si pytz está disponible
            dt_utc = TIMEZONE.localize(dt) if TIMEZONE else dt
        else:
            # Si tiene zona horaria, la convertimos a UTC
            dt_utc = dt.astimezone(TIMEZONE) if TIMEZONE else dt.astimezone(datetime.timezone.utc)
        
        return dt_utc.strftime('%Y-%m-%d %H:%M:%S UTC') # Formato estándar
    return "N/A"

# --- Función para crear tablas (usar migraciones en producción) ---
def create_tables():
    """Crea todas las tablas definidas en los modelos si no existen."""
    try:
        # Base.metadata.create_all(bind=engine) 
        # ¡ADVERTENCIA! create_all() es útil para desarrollo, pero en producción se recomienda usar
        # herramientas de migración como Alembic para gestionar cambios en el esquema de BD de forma segura.
        print("Tablas creadas o ya existentes (si se usa create_all).")
    except Exception as e:
        print(f"Error al intentar crear tablas: {e}")

# --- Autenticación de la conexión (opcional, para verificar que la BD está accesible) ---
try:
    connection = engine.connect()
    print("Conexión a la base de datos PostgreSQL establecida correctamente.")
    connection.close()
except Exception as e:
    print(f"Error al conectar a la base de datos: {e}")
    print("Por favor, verifica que PostgreSQL esté corriendo y que la variable de entorno DATABASE_URL esté configurada correctamente.")

# --- Definición de Modelos de Datos ---

class ClientB2B(Base):
    __tablename__ = "clients_b2b"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, nullable=False)
    nit = Column(String(50), unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    client_shipments = relationship("ClientShipment", back_populates="client")
    packages = relationship("Package", back_populates="client") # Paquetes no asociados a un envío específico
    products = relationship("Product", back_populates="client")

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    client_id = Column(Integer, ForeignKey("clients_b2b.id"), index=True)
    price_to_client = Column(Float, default=0.0) 
    cost_to_courier = Column(Float, default=0.0) 
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    client = relationship("ClientB2B", back_populates="products")
    client_shipments = relationship("ClientShipment", back_populates="product")

class Courier(Base):
    __tablename__ = "couriers"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    phone = Column(String(50), nullable=True)
    plate = Column(String(50), unique=True, nullable=True) # Placa es opcional pero única si se proporciona
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    packages = relationship("Package", back_populates="courier")
    routes = relationship("Route", back_populates="courier")
    movements = relationship("Movement", back_populates="courier") 

class ClientShipment(Base): # Envío original del cliente B2B
    __tablename__ = "client_shipments"
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey("clients_b2b.id"), index=True, nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), index=True, nullable=True)
    client_tracking_number = Column(String(100), unique=True, index=True, nullable=False) # Guía del cliente original
    internal_tracking_number = Column(String(100), unique=True, index=True, nullable=True) # Guía interna generada por Enlace
    quantity_total = Column(Integer, nullable=False, default=1)
    quantity_available = Column(Integer, nullable=False, default=1) # Stock disponible para crear paquetes individuales
    status = Column(String(50), default="PRE-ALERTA", index=True) # Ej: PRE-ALERTA, EN BODEGA, STOCK AGOTADO
    received_at = Column(DateTime, nullable=True) # Fecha de recepción física (si aplica)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    client = relationship("ClientB2B", back_populates="client_shipments")
    product = relationship("Product", back_populates="client_shipments")
    packages = relationship("Package", back_populates="client_shipment") # Paquetes individuales creados desde este envío

class Package(Base):
    __tablename__ = "packages"
    id = Column(Integer, primary_key=True)
    internal_tracking_number = Column(String(100), unique=True, index=True, nullable=False)
    client_shipment_id = Column(Integer, ForeignKey("client_shipments.id"), index=True, nullable=True)
    client_id = Column(Integer, ForeignKey("clients_b2b.id"), index=True, nullable=True) # Cliente B2B final (si no viene de client_shipment)
    courier_id = Column(Integer, ForeignKey("couriers.id"), nullable=True, index=True)
    route_id = Column(Integer, ForeignKey("routes.id"), index=True, nullable=True) # FK a la ruta asignada

    # Datos del destinatario y envío
    recipient_name = Column(String(255), nullable=False)
    recipient_address = Column(Text, nullable=False)
    sender_name = Column(String(255)) # Puede ser el cliente B2B o Enlace
    
    # Estados y Trazabilidad
    status = Column(String(50), default="PENDIENTE DE ENVÍO", index=True) # Ej: PENDIENTE DE ENVÍO, EN RUTA, ENTREGADO, NOVEDAD, DEVUELTO
    is_delivered = Column(Boolean, default=False, index=True)
    delivered_at = Column(DateTime, nullable=True)
    
    # COD (Cobro Contra Entrega)
    cod_amount = Column(Float, default=0.0) # Monto a cobrar contra entrega
    cod_paid = Column(Boolean, default=False, index=True) # Si el COD ya fue pagado
    
    # POD (Comprobante de Entrega)
    delivery_proof_url = Column(String(512), nullable=True) # URL del POD

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    # Relaciones
    client_shipment = relationship("ClientShipment", back_populates="packages")
    client = relationship("ClientB2B", back_populates="packages")
    courier = relationship("Courier", back_populates="packages")
    route = relationship("Route", back_populates="packages")
    movements = relationship("Movement", back_populates="package")
    cod_records = relationship("CODRecord", back_populates="package") # Registros COD asociados a este paquete
    attachments = relationship("FileStorage", back_populates="package") # Archivos adjuntos (PODs, fotos)

class Movement(Base):
    __tablename__ = "movements"
    id = Column(Integer, primary_key=True)
    package_id = Column(Integer, ForeignKey("packages.id"), index=True, nullable=False)
    courier_id = Column(Integer, ForeignKey("couriers.id"), index=True, nullable=True) # Mensajero asociado al movimiento
    route_id = Column(Integer, ForeignKey("routes.id"), index=True, nullable=True) # Ruta asociada al movimiento
    
    location = Column(String(255), nullable=False) # Ej: 'BODEGA', 'DIRECCION_DESTINATARIO', 'RUTA_X'
    description = Column(Text, nullable=False) # Ej: 'Paquete recibido', 'En tránsito', 'Entregado'
    movement_time = Column(DateTime, default=datetime.utcnow)
    
    package = relationship("Package", back_populates="movements")
    courier = relationship("Courier", back_populates="movements")
    route = relationship("Route", back_populates="movements")

class Route(Base): # Ruta de entrega para un mensajero
    __tablename__ = "routes"
    id = Column(Integer, primary_key=True)
    courier_id = Column(Integer, ForeignKey("couriers.id"), index=True, nullable=False)
    route_number = Column(String(50), unique=True, index=True, nullable=False) # Ej: RUTA-20231027-001
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    status = Column(String(50), default="PENDIENTE", index=True) # Ej: PENDIENTE, EN CURSO, CERRADA, CANCELADA
    total_cod_collected = Column(Float, default=0.0) # Suma de COD recaudado en esta ruta
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    courier = relationship("Courier", back_populates="routes")
    packages = relationship("Package", back_populates="route") # Paquetes asignados a esta ruta
    cod_records = relationship("CODRecord", back_populates="route") # Registros COD de esta ruta
    movements = relationship("Movement", back_populates="route") # Movimientos asociados a esta ruta

class CODRecord(Base): # Registro de Cobro Contra Entrega
    __tablename__ = "cod_records"
    id = Column(Integer, primary_key=True)
    package_id = Column(Integer, ForeignKey("packages.id"), index=True, nullable=False)
    route_id = Column(Integer, ForeignKey("routes.id"), index=True, nullable=False)
    courier_id = Column(Integer, ForeignKey("couriers.id"), index=True, nullable=False)
    amount = Column(Float, nullable=False) # Monto cobrado
    payment_method = Column(String(50)) # Ej: EFECTIVO, DATA-">fono", TRANSFERENCIA
    status = Column(String(50), default="PENDIENTE", index=True) # Ej: PENDIENTE, LIQUIDADO, DISCREPANCIA
    recorded_at = Column(DateTime, default=datetime.utcnow) # Momento en que se registra el COD
    liquidated_at = Column(DateTime, nullable=True) # Momento en que se liquida

    package = relationship("Package", back_populates="cod_records")
    route = relationship("Route", back_populates="cod_records")
    courier = relationship("Courier") # Relación simple

class RegexMap(Base): # Para patrones de validación
    __tablename__ = "regex_map"
    id = Column(Integer, primary_key=True)
    pattern_name = Column(String(100), unique=True, index=True, nullable=False) # Ej: 'VALID_POSTAL_CODE_SPAIN'
    regex_pattern = Column(Text, nullable=False) # Ej: '^[0-9]{5}$'
    description = Column(Text)

class FileStorage(Base): # Para metadatos de archivos subidos (PODs, firmas, etc.)
    __tablename__ = "file_storage"
    id = Column(Integer, primary_key=True)
    package_id = Column(Integer, ForeignKey("packages.id"), index=True, nullable=True)
    file_type = Column(String(50)) # Ej: 'POD_PDF', 'SIGNATURE', 'PHOTO_DELIVERY'
    url = Column(String(512), nullable=False) # URL del archivo (S3, GCS, local)
    original_name = Column(String(255))
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    package = relationship("Package", back_populates="attachments")

# --- Definición de Relaciones Adicionales (si faltan) ---
# Asegurarse de que todas las relaciones bidireccionales estén completas.
# Ejemplo: ClientB2B tiene 'client_shipments' y ClientShipment tiene 'client'.
# Si no se definen explícitamente con 'relationship', SQLAlchemy puede inferirlas,
# pero es mejor ser explícito para claridad.

# --- Crear tablas (solo para desarrollo inicial) ---
# En producción, se usarán migraciones (ej: Alembic).
# Descomenta la siguiente línea para crear las tablas la primera vez que ejecutes el script.
# create_tables() 
