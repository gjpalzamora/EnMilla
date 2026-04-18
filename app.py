import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Boolean, func, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, scoped_session
from datetime import datetime, timedelta
import io

# --- 1. CONFIGURACIÓN DE BASE DE DATOS ---
DATABASE_URL = "sqlite:///enmilla_v15_pro.db"
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
    client_id = Column(Integer, ForeignKey("clients_b2b.id"))
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
    client_id = Column(Integer, ForeignKey("clients_b2b.id"))
    courier_id = Column(Integer, ForeignKey("couriers.id"), nullable=True)
    product_name = Column(String(255))
    income = Column(Float, default=0.0)
    expense = Column(Float, default=0.0)
    cash_collected = Column(Float, default=0.0) # Recaudos (COD)
    status = Column(String(50), default="BODEGA") # BODEGA, EN RUTA, ENTREGADO, DEVOLUCION, REENVIO
    created_at = Column(DateTime, default=datetime.utcnow)
    delivered_at = Column(DateTime, nullable=True)
    
    client = relationship("ClientB2B", back_populates="packages")
    courier = relationship("Courier", back_populates="packages")
    movements = relationship("Movement", back_populates="package", cascade="all, delete-orphan")

class Movement(Base):
    __tablename__ = "movements"
    id = Column(Integer, primary_key=True)
    package_id = Column(Integer, ForeignKey("packages.id"))
    description = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    package = relationship("Package", back_populates="movements")

Base.metadata.create_all(bind=engine)

# --- 3. FUNCIONES DE APOYO ---
def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Reporte')
    return output.getvalue()

# --- 4. INTERFAZ PRINCIPAL ---
st.set_page_config(page_title="EnMilla ERP v15.0 Pro", layout="wide")
st.sidebar.title("🚀 EnMilla Logistics")
modulo = st.sidebar.selectbox("Menú Principal", [
    "1. Administración (Maestros)", 
    "2. Recepción y Bodega", 
    "3. Despacho y Última Milla", 
    "4. Entregas y Recaudos",
    "5. Devoluciones y Reenvíos",
    "6. Reportes y KPIs"
])

# --- MÓDULO 1: ADMINISTRACIÓN ---
if modulo == "1. Administración (Maestros)":
    st.header("Configuración de Clientes y Tarifas")
    t1, t2, t3 = st.tabs(["🏢 Clientes", "🛵 Mensajeros", "📦 Tarifario (Productos)"])
    
    with t1:
        with st.form("cli_form"):
            n = st.text_input("Nombre Empresa").upper()
            nit = st.text_input("NIT")
            if st.form_submit_button("Crear Cliente"):
                with Session() as db:
                    try:
                        db.add(ClientB2B(name=n, nit=nit)); db.commit()
                        st.success(f"Cliente {n} creado.")
                    except: st.error("Error: Ya existe.")

    with t2:
        with st.form("cou_form"):
            cn = st.text_input("Nombre Mensajero").upper()
            cp = st.text_input("Placa").upper()
            if st.form_submit_button("Registrar Mensajero"):
                with Session() as db:
                    try:
                        db.add(Courier(name=cn, plate=cp)); db.commit()
                        st.success(f"Mensajero {cn} registrado.")
                    except: st.error("Error: Placa duplicada.")

    with t3:
        with Session() as db:
            clis = db.query(ClientB2B).all()
            if clis:
                with st.form("prod_form"):
                    cli_sel = st.selectbox("Cliente", [c.name for c in clis])
                    p_name = st.text_input("Tipo de Servicio (ej: Entrega Local)").upper()
                    c1, c2 = st.columns(2)
                    inc = c1.number_input("Precio al Cliente ($)", min_value=0.0)
                    exp = c2.number_input("Costo Mensajero ($)", min_value=0.0)
                    if st.form_submit_button("Guardar Producto"):
                        c_obj = db.query(ClientB2B).filter(ClientB2B.name == cli_sel).first()
                        db.add(Product(name=p_name, client_id=c_obj.id, price_to_client=inc, cost_to_courier=exp))
                        db.commit(); st.success("Producto creado.")

# --- MÓDULO 2: RECEPCIÓN Y BODEGA ---
elif modulo == "2. Recepción y Bodega":
    st.header("Ingreso de Mercancía")
    with Session() as db:
        clis = db.query(ClientB2B).all()
        if clis:
            c_name = st.selectbox("Seleccione Cliente", [c.name for c in clis])
            c_obj = db.query(ClientB2B).filter(ClientB2B.name == c_name).first()
            prods = db.query(Product).filter(Product.client_id == c_obj.id).all()
            
            if prods:
                p_sel = st.selectbox("Servicio", [p.name for p in prods])
                p_obj = db.query(Product).filter(Product.name == p_sel, Product.client_id == c_obj.id).first()
                st.info(f"Configuración: Cobro ${p_obj.price_to_client} | Pago Mens. ${p_obj.cost_to_courier}")

                def scan_in():
                    guia = st.session_state.scan_in.strip().upper()
                    if guia:
                        with Session() as dbs:
                            if not dbs.query(Package).filter(Package.tracking_number == guia).first():
                                pack = Package(tracking_number=guia, client_id=c_obj.id, product_name=p_obj.name, income=p_obj.price_to_client, expense=p_obj.cost_to_courier, status="BODEGA")
                                dbs.add(pack); dbs.flush()
                                dbs.add(Movement(package_id=pack.id, description="Ingreso a bodega"))
                                dbs.commit(); st.toast("Recibido.")
                            else: st.error("Duplicado.")
                        st.session_state.scan_in = ""

                st.text_input("Escanear Guía", key="scan_in", on_change=scan_in)
            else: st.warning("Cliente sin servicios configurados.")

# --- MÓDULO 4: ENTREGAS Y RECAUDOS ---
elif modulo == "4. Entregas y Recaudos":
    st.header("Confirmación de Entrega y Recaudo (COD)")
    guia = st.text_input("Escanear Guía Entregada").upper()
    if guia:
        with Session() as db:
            p = db.query(Package).filter(Package.tracking_number == guia).first()
            if p and p.status == "EN RUTA":
                with st.form("entrega_form"):
                    st.write(f"**Guía:** {p.tracking_number} | **Mensajero:** {p.courier.name}")
                    cod = st.number_input("Valor Recaudado (Efectivo)", min_value=0.0)
                    if st.form_submit_button("Confirmar Entrega"):
                        p.status = "ENTREGADO"
                        p.cash_collected = cod
                        p.delivered_at = datetime.utcnow()
                        db.add(Movement(package_id=p.id, description=f"ENTREGADO - Recaudo: ${cod}"))
                        db.commit(); st.success("Entrega registrada.")
            else: st.error("Guía no está en ruta o no existe.")

# --- MÓDULO 5: DEVOLUCIONES Y REENVÍOS ---
elif modulo == "5. Devoluciones y Reenvíos":
    st.header("Gestión de Novedades")
    guia = st.text_input("Escanear Guía con Novedad").upper()
    if guia:
        with Session() as db:
            p = db.query(Package).filter(Package.tracking_number == guia).first()
            if p:
                tipo = st.radio("Acción:", ["DEVOLUCIÓN A BODEGA (Fallo)", "REENVÍO (Nueva Ruta)", "RETORNO A CLIENTE"])
                obs = st.text_area("Motivo de la novedad")
                if st.form_submit_button("Procesar Novedad"):
                    if "DEVOLUCIÓN" in tipo: p.status = "DEVOLUCION"
                    elif "REENVÍO" in tipo: p.status = "BODEGA" # Vuelve a bodega para ser re-despachado
                    elif "RETORNO" in tipo: p.status = "RETORNADO_CLIENTE"
                    
                    db.add(Movement(package_id=p.id, description=f"NOVEDAD: {tipo} - Obs
