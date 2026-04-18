import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Boolean, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, scoped_session
from datetime import datetime
import io

# --- 1. CONFIGURACIÓN DE BASE DE DATOS ---
DATABASE_URL = "sqlite:///enmilla_v14_final.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Session = scoped_session(session_factory)
Base = declarative_base()

# --- 2. MODELOS DE DATOS ---
class ClientB2B(Base):
    __tablename__ = "clients_b2b"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)
    nit = Column(String(50), unique=True)
    packages = relationship("Package", back_populates="client")

class Courier(Base):
    __tablename__ = "couriers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    plate = Column(String(50), unique=True, nullable=False)
    is_active = Column(Boolean, default=True)
    packages = relationship("Package", back_populates="courier")

class Package(Base):
    __tablename__ = "packages"
    id = Column(Integer, primary_key=True, index=True)
    tracking_number = Column(String(100), unique=True, index=True, nullable=False)
    client_id = Column(Integer, ForeignKey("clients_b2b.id"))
    courier_id = Column(Integer, ForeignKey("couriers.id"), nullable=True)
    product_name = Column(String(255))
    status = Column(String(50), default="BODEGA") # BODEGA, EN RUTA, ENTREGADO, NOVEDAD
    created_at = Column(DateTime, default=datetime.utcnow)
    
    client = relationship("ClientB2B", back_populates="packages")
    courier = relationship("Courier", back_populates="packages")
    # CORRECCIÓN: Relación corregida para evitar lógica circular
    movements = relationship("Movement", back_populates="package", cascade="all, delete-orphan")

class Movement(Base):
    __tablename__ = "movements"
    id = Column(Integer, primary_key=True, index=True)
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
st.set_page_config(page_title="EnMilla ERP v14.1", layout="wide")
st.sidebar.title("🚚 Panel EnMilla")
modulo = st.sidebar.radio("Ir a:", [
    "1. Administración", 
    "2. Operaciones (Recibir)", 
    "3. Despacho (Cargar)", 
    "4. Gestión de Datos"
])

# --- MÓDULO 1: ADMINISTRACIÓN ---
if modulo == "1. Administración":
    st.header("Gestión de Maestros")
    t1, t2 = st.tabs(["Clientes B2B", "Mensajeros"])
    
    with t1:
        with st.form("form_cliente", clear_on_submit=True):
            n = st.text_input("Nombre de la Empresa (Asociado)").upper()
            nit = st.text_input("NIT")
            if st.form_submit_button("Registrar Cliente"):
                with Session() as db:
                    try:
                        db.add(ClientB2B(name=n, nit=nit))
                        db.commit()
                        st.success(f"Cliente {n} guardado.")
                    except: st.error("Error: El NIT o Nombre ya existen.")

    with t2:
        with st.form("form_courier", clear_on_submit=True):
            cn = st.text_input("Nombre del Mensajero").upper()
            cp = st.text_input("Placa del Vehículo").upper()
            if st.form_submit_button("Registrar Mensajero"):
                with Session() as db:
                    try:
                        db.add(Courier(name=cn, plate=cp))
                        db.commit()
                        st.success(f"Mensajero {cn} registrado.")
                    except: st.error("Error: La placa ya está registrada.")

# --- MÓDULO 2: OPERACIONES (RECIBIR) ---
elif modulo == "2. Operaciones (Recibir)":
    st.header("Entrada de Mercancía")
    with Session() as db:
        clis = db.query(ClientB2B).all()
        if clis:
            cli_n = st.selectbox("Seleccione Cliente", [c.name for c in clis])
            cli_obj = db.query(ClientB2B).filter(ClientB2B.name == cli_n).first()
            p_nom = st.text_input("Descripción del Producto (Ej: Almohadilla, Paquete)").upper()

            def registrar_entrada():
                guia = st.session_state.scan_in.strip().upper()
                if guia:
                    with Session() as db_s:
                        existente = db_s.query(Package).filter(Package.tracking_number == guia).first()
                        if not existente:
                            p = Package(tracking_number=guia, client_id=cli_obj.id, product_name=p_nom, status="BODEGA")
                            db_s.add(p)
                            db_s.flush() # Para obtener el ID antes del commit
                            db_s.add(Movement(package_id=p.id, description=f"Ingreso a Bodega - Cliente: {cli_n}"))
                            db_s.commit()
                            st.toast(f"✅ Guía {guia} recibida.")
                        else: st.error(f"La guía {guia} ya existe con estado {existente.status}.")
                    st.session_state.scan_in = ""

            st.text_input("ESCANEE TRACKING", key="scan_in", on_change=registrar_entrada)
        else: st.warning("Debe crear un cliente primero.")

# --- MÓDULO 3: DESPACHO (CARGAR) ---
elif modulo == "3. Despacho (Cargar)":
    st.header("Salida a Ruta")
    with Session() as db:
        mens = db.query(Courier).filter(Courier.is_active == True).all()
        col1, col2 = st.columns([1, 2])
        
        with col1:
            if mens:
                m_sel = st.selectbox("Mensajero de Salida", [f"{m.name} ({m.plate})" for m in mens])
                m_id = db.query(Courier).filter(Courier.plate == m_sel.split("(")[1].replace(")", "")).first().id

                def registrar_salida():
                    guia = st.session_state.scan_out.strip().upper()
                    if guia:
                        with Session() as db_d:
                            p = db_d.query(Package).filter(Package.tracking_number == guia).first()
                            if p and p.status == "BODEGA":
                                p.status = "EN RUTA"
                                p.courier_id = m_id
                                db_d.add(Movement(package_id=p.id, description=f"Despachado en ruta con {m_sel}"))
                                db_d.commit()
                                st.toast(f"🚚 Guía {guia} cargada.")
                            else: st.error("Guía no disponible para despacho.")
                        st.session_state.scan_out = ""

                st.text_input("ESCANEE PARA DESPACHO", key="scan_out", on_change=registrar_salida)

        with col2:
            st.subheader("Carga Actual por Mensajero")
            carga = db.query(Courier.name, func.count(Package.id)).join(Package).filter(Package.status == "EN RUTA").group_by(Courier.name).all()
            if carga:
                st.table(pd.DataFrame(carga, columns=["Mensajero", "Paquetes en Mano"]))

# --- MÓDULO 4: GESTIÓN DE DATOS ---
elif modulo == "4. Gestión de Datos":
    st.header("Consultas y Reportes")
    with Session() as db:
        tab1, tab2 = st.tabs(["Inventario en Bodega", "Trazabilidad Total"])
        
        with tab1:
            inv = db.query(Package.tracking_number, ClientB2B.name, Package.product_name, Package.created_at)\
                    .join(ClientB2B).filter(Package.status == "BODEGA").all()
            if inv:
                df_i = pd.DataFrame(inv, columns=["Tracking", "Cliente", "Producto", "Fecha"])
                st.dataframe(df_i, use_container_width=True)
                st.download_button("📥 Excel Inventario", data=to_excel(df_i), file_name="stock_bodega.xlsx")

        with tab2:
            search = st.text_input("Rastrear Guía:").upper()
            if search:
                p = db.query(Package).filter(Package.tracking_number == search).first()
                if p:
                    st.info(f"**Estado Actual:** {p.status} | **Cliente:** {p.client.name}")
                    hist = db.query(Movement).filter(Movement.package_id == p.id).order_by(Movement.timestamp.desc()).all()
                    for m in hist: st.write(f"🕒 {m.timestamp.strftime('%d/%m/%Y %H:%M')} - {m.description}")
                else: st.error("Guía no encontrada.")
