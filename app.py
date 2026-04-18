# --- 2. MODELOS DE DATOS ---
# (Mantener ClientB2B, Product, Courier, Package, Movement como están o con ajustes menores)

# --- NUEVOS MODELOS PARA ENLACES 360 ---

class ClientShipment(Base):
    __tablename__ = "client_shipments"
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey("clients_b2b.id"), index=True, nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), index=True, nullable=True) # Opcional, si el envío es de un producto específico
    client_tracking_number = Column(String(100), unique=True, index=True, nullable=False) # Guía del cliente original
    internal_tracking_number = Column(String(100), unique=True, index=True, nullable=True) # Guía interna generada por Enlace (si aplica)
    quantity_total = Column(Integer, nullable=False, default=1)
    quantity_available = Column(Integer, nullable=False, default=1) # Stock disponible para crear paquetes individuales
    status = Column(String(50), default="PRE-ALERTA") # Ej: PRE-ALERTA, EN BODEGA, STOCK AGOTADO
    received_at = Column(DateTime, default=datetime.utcnow) # Fecha de recepción física
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    client = relationship("ClientB2B", back_populates="client_shipments")
    product = relationship("Product", back_populates="client_shipments")
    packages = relationship("Package", back_populates="client_shipment") # Paquetes individuales creados desde este envío

class Package(Base): # Modificaciones al Package existente
    __tablename__ = "packages"
    id = Column(Integer, primary_key=True)
    internal_tracking_number = Column(String(100), unique=True, index=True, nullable=False)
    client_shipment_id = Column(Integer, ForeignKey("client_shipments.id"), index=True, nullable=True) # FK al envío original
    client_id = Column(Integer, ForeignKey("clients_b2b.id"), index=True) # Cliente B2B final (si no viene de client_shipment)
    courier_id = Column(Integer, ForeignKey("couriers.id"), nullable=True, index=True)
    recipient_name = Column(String(255), nullable=False)
    recipient_address = Column(Text, nullable=False)
    sender_name = Column(String(255)) # Podría ser el nombre del cliente B2B o Enlace
    status = Column(String(50), default="PENDIENTE DE ENVÍO") # Ej: PENDIENTE DE ENVÍO, EN RUTA, ENTREGADO, NOVEDAD, DEVUELTO
    created_at = Column(DateTime, default=datetime.utcnow)
    delivered_at = Column(DateTime, nullable=True)
    is_delivered = Column(Boolean, default=False)
    delivery_proof_url = Column(String(512), nullable=True) # URL del POD
    cod_amount = Column(Float, default=0.0) # Monto a cobrar contra entrega
    cod_paid = Column(Boolean, default=False) # Si el COD ya fue pagado
    route_id = Column(Integer, ForeignKey("routes.id"), index=True, nullable=True) # FK a la ruta asignada

    client_shipment = relationship("ClientShipment", back_populates="packages")
    client = relationship("ClientB2B", back_populates="packages") # Si el paquete no viene de client_shipment
    courier = relationship("Courier", back_populates="packages")
    movements = relationship("Movement", back_populates="package")
    route = relationship("Route", back_populates="packages")

class Route(Base): # Para agrupar paquetes en una ruta de mensajero
    __tablename__ = "routes"
    id = Column(Integer, primary_key=True)
    courier_id = Column(Integer, ForeignKey("couriers.id"), index=True, nullable=False)
    route_number = Column(String(50), unique=True, index=True, nullable=False) # Ej: RUTA-20231027-001
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    status = Column(String(50), default="PENDIENTE") # Ej: PENDIENTE, EN CURSO, CERRADA, CANCELADA
    total_cod_collected = Column(Float, default=0.0) # Suma de COD recaudado en esta ruta

    courier = relationship("Courier", back_populates="routes")
    packages = relationship("Package", back_populates="route")
    cod_records = relationship("CODRecord", back_populates="route")

class CODRecord(Base): # Para registrar los cobros contra entrega
    __tablename__ = "cod_records"
    id = Column(Integer, primary_key=True)
    package_id = Column(Integer, ForeignKey("packages.id"), index=True, nullable=False)
    route_id = Column(Integer, ForeignKey("routes.id"), index=True, nullable=False)
    courier_id = Column(Integer, ForeignKey("couriers.id"), index=True, nullable=False)
    amount = Column(Float, nullable=False)
    payment_method = Column(String(50)) # Ej: EFECTIVO, DATA-">fono", TRANSFERENCIA
    status = Column(String(50), default="PENDIENTE") # Ej: PENDIENTE, LIQUIDADO, DISCREPANCIA
    recorded_at = Column(DateTime, default=datetime.utcnow) # Momento en que se registra el COD
    liquidated_at = Column(DateTime, nullable=True) # Momento en que se liquida

    package = relationship("Package", back_populates="cod_records")
    route = relationship("Route", back_populates="cod_records")
    courier = relationship("Courier") # Relación simple, no necesita back_populates si no se usa

class RegexMap(Base): # Para patrones de validación
    __tablename__ = "regex_map"
    id = Column(Integer, primary_key=True)
    pattern_name = Column(String(100), unique=True, index=True, nullable=False)
    regex_pattern = Column(Text, nullable=False)
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

# --- Añadir relaciones a modelos existentes ---
# ClientB2B
ClientB2B.client_shipments = relationship("ClientShipment", back_populates="client")
ClientB2B.routes = relationship("Route", back_populates="client") # Si un cliente B2B puede tener rutas asociadas (menos común)

# Product
Product.client_shipments = relationship("ClientShipment", back_populates="product")

# Courier
Courier.routes = relationship("Route", back_populates="courier")

# Package (ya tiene las relaciones añadidas arriba)

# ClientShipment (ya tiene las relaciones añadidas arriba)

# Route (ya tiene las relaciones añadidas arriba)

# Movement (ya tiene la relación añadida arriba)

# CODRecord (ya tiene las relaciones añadidas arriba)

# FileStorage (ya tiene la relación añadida arriba)

# --- Crear tablas ---
# Base.metadata.create_all(bind=engine) # Usar migraciones en producción
