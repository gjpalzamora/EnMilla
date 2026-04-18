import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from fpdf import FPDF
import io

# --- CONFIGURACIÓN DE BASE DE DATOS (ACID COMPLIANT) --- [cite: 34, 36]
# Sustituir con tus credenciales de PostgreSQL en producción [cite: 188]
DATABASE_URL = "postgresql://user:password@localhost:5432/enmilla_db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine) # [cite: 41]
Base = declarative_base()

# --- MODELO DE DATOS (MODELO 360) --- [cite: 49, 50, 51]
class Package(Base): # [cite: 52]
    __tablename__ = "packages"
    id = Column(Integer, primary_key=True, index=True) # [cite: 55]
    tracking_number = Column(String(100), unique=True, nullable=False, index=True) # [cite: 56]
    sender_name = Column(String(255), nullable=True) # [cite: 57]
    recipient_name = Column(String(255), nullable=True) # [cite: 59]
    recipient_address = Column(Text, nullable=True) # [cite: 60]
    status = Column(String(50), default="Recibido") # [cite: 61, 108]
    is_delivered = Column(Boolean, default=False) # [cite: 64]
    created_at = Column(DateTime, default=datetime.utcnow) # [cite: 62]
    movements = relationship("Movement", back_populates="package") # [cite: 91]

class Movement(Base): # [cite: 66]
    __tablename__ = "movements"
    id = Column(Integer, primary_key=True, index=True) # [cite: 69]
    package_id = Column(Integer, ForeignKey("packages.id"), nullable=False) # [cite: 70]
    location = Column(String(255), nullable=False) # [cite: 72]
    description = Column(Text, nullable=False) # [cite: 73]
    movement_time = Column(DateTime, default=datetime.utcnow) # [cite: 74]
    package = relationship("Package", back_populates="movements") # [cite: 91]

# Crear tablas automáticamente al inicio [cite: 42, 236]
Base.metadata.create_all(bind=engine)

# --- LÓGICA DE NEGOCIO Y POD --- [cite: 14, 135]
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'COMPROBANTE DE ENTREGA (POD) - Enlace Soluciones', 0, 1, 'C') # [cite: 2, 260]

# --- INTERFAZ STREAMLIT --- [cite: 31, 33]
st.set_page_config(page_title="EnMilla ERP", layout="wide")

# Inicializar sesión para escaneo ciego de contingencia
if 'bulk_scans' not in st.session_state:
    st.session_state.bulk_scans = []

st.sidebar.title("🚚 Operaciones EnMilla")
modulo = st.sidebar.radio("Navegación", [
    "📦 Recepción Masiva (Contingencia)", 
    "🚚 Gestión de Despacho", 
    "🔍 Rastreo 360",
    "📊 Carga de Manifiestos (Conciliación)"
]) # [cite: 170]

# --- MÓDULO 1: RECEPCIÓN MASIVA (ESCENARIO 10 PM) ---
if modulo == "📦 Recepción Masiva (Contingencia)":
    st.header("⚡ Recepción de Contingencia (Modo Ciego)")
    st.warning("Mercancía en muelle sin base de datos. Ingrese solo el tracking.") # 
    
    with st.form("form_scan", clear_on_submit=True):
        tracking = st.text_input("ESCANEE CÓDIGO DE BARRAS", key="scanner")
        if st.form_submit_button("REGISTRAR INGRESO"):
            db = SessionLocal()
            # RF3.1.2: Evitar duplicados [cite: 111, 112]
            exists = db.query(Package).filter(Package.tracking_number == tracking).first()
            if not exists:
                new_pkg = Package(tracking_number=tracking, status="Recibido") # 
                db.add(new_pkg)
                db.commit()
                # Movimiento inicial automático 
                new_move = Movement(package_id=new_pkg.id, location="Bodega Bogotá", description="Ingreso masivo nocturno")
                db.add(new_move)
                db.commit()
                st.session_state.bulk_scans.append(tracking)
                st.toast(f"✅ Registrado: {tracking}")
            else:
                st.error("Error: Guía ya existe en sistema.") # [cite: 172]
            db.close()

    st.subheader("Paquetes en esta descarga")
    st.write(st.session_state.bulk_scans)

# --- MÓDULO 2: GESTIÓN DE DESPACHO Y POD --- [cite: 122, 135]
elif modulo == "🚚 Gestión de Despacho":
    st.header("Gestión de Salidas y POD")
    track_to_deliver = st.text_input("Ingrese Guía para Entrega")
    receptor = st.text_input("Nombre de quien recibe")
    
    if st.button("Finalizar Entrega y Generar PDF"): # 
        db = SessionLocal()
        pkg = db.query(Package).filter(Package.tracking_number == track_to_deliver).first()
        if pkg:
            pkg.status = "Entregado" # [cite: 131]
            pkg.is_delivered = True # [cite: 131]
            db.add(Movement(package_id=pkg.id, location="Dirección Destino", description=f"Recibido por: {receptor}"))
            db.commit()
            
            # Generación de PDF Real [cite: 47, 143]
            pdf = PDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            pdf.cell(200, 10, txt=f"Guía: {pkg.tracking_number}", ln=1)
            pdf.cell(200, 10, txt=f"Destinatario: {pkg.recipient_name or 'N/A'}", ln=2)
            pdf.cell(200, 10, txt=f"Recibido por: {receptor}", ln=3)
            
            output = io.BytesIO()
            pdf.output(output)
            st.download_button("📥 Descargar POD PDF", data=output.getvalue(), file_name=f"POD_{track_to_deliver}.pdf")
            st.success("Entrega registrada correctamente.")
        db.close()

# --- MÓDULO 3: CONCILIACIÓN (CARGA DE EXCEL) --- 
elif modulo == "📊 Carga de Manifiestos (Conciliación)":
    st.header("Sincronización de Base de Datos Cliente")
    uploaded_file = st.file_uploader("Suba el archivo del cliente (CSV/Excel)")
    if uploaded_file:
        df = pd.read_csv(uploaded_file) # Supongamos CSV para este ejemplo
        if st.button("Cruzar Datos y Actualizar Guías"):
            db = SessionLocal()
            count = 0
            for index, row in df.iterrows():
                pkg = db.query(Package).filter(Package.tracking_number == str(row['tracking'])).first()
                if pkg:
                    # Inyectamos los datos que faltaban del escaneo ciego
                    pkg.sender_name = row['remitente']
                    pkg.recipient_name = row['destinatario']
                    pkg.recipient_address = row['direccion']
                    count += 1
            db.commit()
            db.close()
            st.success(f"Se actualizaron {count} registros con la información del cliente.")
