import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Boolean, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import io

# --- 1. CAPA DE DATOS (PERSISTENCIA TOTAL) ---
DATABASE_URL = "sqlite:///enmilla_final_v13.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- 2. MODELOS (RECUPERADOS DESDE EL INICIO DEL CHAT) ---
class ClientB2B(Base):
    __tablename__ = "clients_b2b"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)
    nit = Column(String(50), unique=True)
    products = relationship("Product", back_populates="client")
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
    status = Column(String(50), default="BODEGA")
    created_at = Column(DateTime, default=datetime.utcnow)
    client = relationship("ClientB2B", back_populates="packages")
    courier = relationship("Courier", back_populates="packages")
    movements = relationship("Movement", back_populates="package")

class Movement(Base):
    __tablename__ = "movements"
    id = Column(Integer, primary_key=True, index=True)
    package_id = Column(Integer, ForeignKey("packages.id"))
    description = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    package = relationship("Package", back_populates="movements")

Base.metadata.create_all(bind=engine)

# --- 3. UTILIDADES DE EXPORTACIÓN ---
def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='ERP_EnMilla')
    return output.getvalue()

# --- 4. INTERFAZ DE USUARIO ---
st.set_page_config(page_title="EnMilla ERP v13.0", layout="wide")
st.sidebar.title("🚚 Operación EnMilla")
modulo = st.sidebar.radio("Módulos del Sistema:", [
    "📦 Recepción (Bodega)", 
    "🚀 Despacho (Salida)", 
    "📊 Inventario e Historial",
    "⚙️ Administración (Maestros)",
    "✏️ Corrección de Datos"
])

# --- MÓDULO 1: RECEPCIÓN ---
if modulo == "📦 Recepción (Bodega)":
    st.header("Ingreso de Guías con Scanner")
    db = SessionLocal()
    clis = db.query(ClientB2B).all()
    if clis:
        col_c, col_p = st.columns(2)
        with col_c:
            c_nom = st.selectbox("Cliente", [c.name for c in clis])
            cli_obj = db.query(ClientB2B).filter(ClientB2B.name == c_nom).first()
        with col_p:
            prods = db.query(Product).filter(Product.client_id == cli_obj.id).all()
            p_nom = st.selectbox("Producto", [p.name for p in prods] if prods else ["GENÉRICO"])

        def registrar_ingreso():
            guia = st.session_state.barcode_in.strip().upper()
            if guia:
                db_s = SessionLocal()
                if not db_s.query(Package).filter(Package.tracking_number == guia).first():
                    p = Package(tracking_number=guia, client_id=cli_obj.id, product_name=p_nom, status="BODEGA")
                    db_s.add(p); db_s.commit()
                    db_s.add(Movement(package_id=p.id, description=f"INGRESO: {p_nom}"))
                    db_s.commit()
                    st.toast(f"✅ {guia} registrado")
                else: st.error("Guía duplicada.")
                db_s.close()
                st.session_state.barcode_in = ""
        st.text_input("ESCANEE GUÍA AQUÍ", key="barcode_in", on_change=registrar_ingreso)
    db.close()

# --- MÓDULO 2: DESPACHO ---
elif modulo == "🚀 Despacho (Salida)":
    st.header("Salida a Ruta y Monitor de Carga")
    db = SessionLocal()
    mens = db.query(Courier).filter(Courier.is_active == True).all()
    
    col_s, col_m = st.columns([1, 2])
    with col_s:
        st.subheader("Escanear Salida")
        if mens:
            m_sel = st.selectbox("Mensajero", [f"{m.name} | {m.plate}" for m in mens])
            m_id = db.query(Courier).filter(Courier.name == m_sel.split(" | ")[0]).first().id

            def registrar_salida():
                guia = st.session_state.barcode_out.strip().upper()
                if guia:
                    db_d = SessionLocal()
                    p = db_d.query(Package).filter(Package.tracking_number == guia).first()
                    if p and p.status == "BODEGA":
                        p.status = "EN RUTA"; p.courier_id = m_id
                        db_d.add(Movement(package_id=p.id, description=f"DESPACHADO: {m_sel}"))
                        db_d.commit()
                        st.toast(f"🚚 {guia} despachado")
                    else: st.error("No existe o ya salió.")
                    db_d.close()
                    st.session_state.barcode_out = ""
            st.text_input("ESCANEE PARA SALIDA", key="barcode_out", on_change=registrar_salida)

    with col_m:
        st.subheader("Carga Actual por Mensajero")
        resumen = db.query(Courier.name, Courier.plate, func.count(Package.id)).join(Package).filter(Package.status == "EN RUTA").group_by(Courier.name).all()
        if resumen:
            df_r = pd.DataFrame(resumen, columns=["Mensajero", "Placa", "Guías"])
            st.table(df_r)
            st.download_button("📥 Excel de Carga", data=to_excel(df_r), file_name="hoja_de_carga.xlsx")
        else: st.info("No hay entregas activas.")
    db.close()

# --- MÓDULO 3: INVENTARIO E HISTORIAL ---
elif modulo == "📊 Inventario e Historial":
    st.header("Consulta de Stock y Trazabilidad")
    db = SessionLocal()
    t1, t2 = st.tabs(["Stock Bodega", "Rastreador de Guía"])
    
    with t1:
        inv = db.query(Package.tracking_number, ClientB2B.name, Package.product_name, Package.created_at).join(ClientB2B).filter(Package.status == "BODEGA").all()
        if inv:
            df_i = pd.DataFrame(inv, columns=["Guía", "Cliente", "Producto", "Fecha"])
            st.dataframe(df_i, use_container_width=True
