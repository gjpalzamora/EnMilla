import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Boolean, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

# --- 1. CONFIGURACIÓN ---
DATABASE_URL = "sqlite:///enmilla_v8_final.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- 2. MODELOS ---
class ClientB2B(Base):
    __tablename__ = "clients_b2b"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True)
    nit = Column(String(50))
    packages = relationship("Package", back_populates="client")

class Courier(Base):
    __tablename__ = "couriers"
    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    plate = Column(String(50), unique=True)
    is_active = Column(Boolean, default=True)
    packages = relationship("Package", back_populates="courier")

class Package(Base):
    __tablename__ = "packages"
    id = Column(Integer, primary_key=True)
    tracking_number = Column(String(100), unique=True)
    client_id = Column(Integer, ForeignKey("clients_b2b.id"))
    courier_id = Column(Integer, ForeignKey("couriers.id"), nullable=True)
    status = Column(String(50), default="BODEGA")
    last_update = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    client = relationship("ClientB2B", back_populates="packages")
    courier = relationship("Courier", back_populates="packages")

Base.metadata.create_all(bind=engine)

# --- 3. INTERFAZ ---
st.set_page_config(page_title="EnMilla ERP v8.0", layout="wide")
st.sidebar.title("🚚 Panel Enmilla")
modulo = st.sidebar.radio("Ir a:", ["1. Administración", "2. Operaciones (Recibir)", "3. Despacho y Monitoreo", "4. Edición de Maestros"])

# --- MÓDULO 3: DESPACHO Y MONITOREO (EL QUE SOLICITASTE) ---
if modulo == "3. Despacho y Monitoreo":
    st.header("Gestión de Salida y Carga de Mensajeros")
    db = SessionLocal()
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Registrar Salida")
        mens = db.query(Courier).filter(Courier.is_active == True).all()
        if mens:
            m_sel = st.selectbox("Seleccione Mensajero para cargar", [f"{m.name} | {m.plate}" for m in mens])
            m_id = int(db.query(Courier).filter(Courier.name == m_sel.split(" | ")[0]).first().id)

            def procesar_despacho():
                g = st.session_state.guia_despacho.strip().upper()
                if g:
                    pkg = db.query(Package).filter(Package.tracking_number == g).first()
                    if pkg:
                        pkg.status = "EN RUTA"
                        pkg.courier_id = m_id
                        db.commit()
                        st.toast(f"🚚 Guía {g} cargada a {m_sel.split(' | ')[0]}")
                    else:
                        st.error(f"La guía {g} no existe en bodega.")
                    st.session_state.guia_despacho = ""

            st.text_input("ESCANEE GUÍA PARA DESPACHAR", key="guia_despacho", on_change=procesar_despacho)
        else:
            st.warning("No hay mensajeros activos creados.")

    with col2:
        st.subheader("📦 ¿Qué lleva cada mensajero?")
        # Consulta para ver el resumen de carga
        carga = db.query(Courier.name, func.count(Package.id)).join(Package).filter(Package.status == "EN RUTA").group_by(Courier.name).all()
        
        if carga:
            df_resumen = pd.DataFrame(carga, columns=["Mensajero", "Total Guías"])
            st.table(df_resumen)
            
            with st.expander("Ver detalle por guía"):
                detalles = db.query(Package.tracking_number, Courier.name, Package.last_update).join(Courier).filter(Package.status == "EN RUTA").all()
                df_detalles = pd.DataFrame(detalles, columns=["Número de Guía", "Mensajero", "Hora Despacho"])
                st.dataframe(df_detalles, use_container_width=True)
        else:
            st.info("No hay paquetes en ruta actualmente.")
    db.close()

# --- MÓDULO 1: ADMINISTRACIÓN (RESUMIDO PARA FUNCIONAR) ---
elif modulo == "1. Administración":
    st.header("Configuración de Maestros")
    t1, t2 = st.tabs(["Clientes", "Mensajeros"])
    with t1:
        with st.form("f1", clear_on_submit=True):
            n = st.text_input("Nombre Cliente").upper()
            if st.form_submit_button("Guardar"):
                db = SessionLocal(); db.add(ClientB2B(name=n)); db.commit(); db.close()
                st.success("Cliente Creado")
    with t2:
        with st.form("f2", clear_on_submit=True):
            cn = st.text_input("Nombre Mensajero").upper()
            cp = st.text_input("Placa").upper()
            if st.form_submit_button("Guardar"):
                db = SessionLocal(); db.add(Courier(name=cn, plate=cp)); db.commit(); db.close()
                st.success("Mensajero Creado")

# --- MÓDULO 2: RECEPCIÓN ---
elif modulo == "2. Operaciones (Recibir)":
    st.header("Entrada de Mercancía")
    db = SessionLocal()
    clis = db.query(ClientB2B).all()
    if clis:
        c_sel = st.selectbox("Cliente", [c.name for c in clis])
        c_id = db.query(ClientB2B).filter(ClientB2B.name == c_sel).first().id
        
        def recibir():
            g = st.session_state.guia_in.strip().upper()
            if g:
                if not db.query(Package).filter(Package.tracking_number == g).first():
                    db.add(Package(tracking_number=g, client_id=c_id, status="BODEGA"))
                    db.commit()
                    st.toast(f"✅ Recibida: {g}")
                st.session_state.guia_in = ""
        
        st.text_input("ESCANEE TRACKING", key="guia_in", on_change=recibir)
    db.close()

# --- MÓDULO 4: EDICIÓN ---
elif modulo == "4. Edición de Maestros":
    st.header("Corrección de Datos")
    db = SessionLocal()
    modo = st.radio("Editar:", ["Mensajeros", "Clientes"])
    if modo == "Mensajeros":
        m_list = db.query(Courier).all()
        if m_list:
            m_sel = st.selectbox("Elegir Mensajero", [m.name for m in m_list])
            m_obj = db.query(Courier).filter(Courier.name == m_sel).first()
            with st.form("ed_m"):
                new_n = st.text_input("Nombre", value=m_obj.name).upper()
                new_p = st.text_input("Placa", value=m_obj.plate).upper()
                if st.form_submit_button("Actualizar"):
                    m_obj.name = new_n; m_obj.plate = new_p; db.commit(); st.rerun()
    db.close()
