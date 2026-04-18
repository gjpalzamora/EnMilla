import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Boolean, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

# --- CONFIGURACIÓN DE NÚCLEO ---
DATABASE_URL = "sqlite:///enmilla_master_v12.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- MODELOS ---
class ClientB2B(Base):
    __tablename__ = "clients_b2b"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)
    nit = Column(String(50), unique=True)
    packages = relationship("Package", back_populates="client")

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    fee_client = Column(Float, default=0.0)
    fee_courier = Column(Float, default=0.0)
    client_id = Column(Integer, ForeignKey("clients_b2b.id"))

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
    status = Column(String(50), default="BODEGA")
    last_update = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    client = relationship("ClientB2B", back_populates="packages")
    courier = relationship("Courier", back_populates="packages")

Base.metadata.create_all(bind=engine)

# --- INTERFAZ ---
st.set_page_config(page_title="EnMilla ERP v12.0", layout="wide")
st.sidebar.title("🚚 Gestión Logística")
modulo = st.sidebar.radio("Navegación:", [
    "1. Administración", 
    "2. Recepción Bodega", 
    "3. Despacho & Monitor", 
    "4. Edición de Datos",
    "5. Base de Datos (Reportes)"
])

# --- MODULO 1 AL 4 (CONSERVADOS INTEGRAMENTE) ---
db = SessionLocal()

if modulo == "1. Administración":
    st.header("Registro de Maestros")
    t1, t2, t3 = st.tabs(["Clientes", "Mensajeros", "Productos"])
    with t1:
        with st.form("f_cli", clear_on_submit=True):
            n = st.text_input("Nombre Empresa").upper()
            nit = st.text_input("NIT")
            if st.form_submit_button("Guardar Cliente"):
                try: db.add(ClientB2B(name=n, nit=nit)); db.commit(); st.success("Registrado")
                except: st.error("Duplicado")
    with t2:
        with st.form("f_cou", clear_on_submit=True):
            cn = st.text_input("Nombre Mensajero").upper(); cp = st.text_input("Placa").upper()
            if st.form_submit_button("Guardar Mensajero"):
                try: db.add(Courier(name=cn, plate=cp)); db.commit(); st.success("Registrado")
                except: st.error("Placa duplicada")
    with t3:
        clis = db.query(ClientB2B).all()
        if clis:
            with st.form("f_prod", clear_on_submit=True):
                pn = st.text_input("Nombre Producto").upper()
                c_sel = st.selectbox("Cliente", [c.name for c in clis])
                f_cli = st.number_input("Tarifa Cliente", min_value=0.0)
                f_cou = st.number_input("Tarifa Mensajero", min_value=0.0)
                if st.form_submit_button("Crear Producto"):
                    target = db.query(ClientB2B).filter(ClientB2B.name == c_sel).first()
                    db.add(Product(name=pn, fee_client=f_cli, fee_courier=f_cou, client_id=target.id)); db.commit(); st.success("Creado")

elif modulo == "2. Recepción Bodega":
    st.header("Ingreso de Mercancía")
    clis = db.query(ClientB2B).all()
    if clis:
        c_sel = st.selectbox("Cliente", [c.name for c in clis])
        cli = db.query(ClientB2B).filter(ClientB2B.name == c_sel).first()
        def reg():
            g = st.session_state.b_in.strip().upper()
            if g:
                if not db.query(Package).filter(Package.tracking_number == g).first():
                    db.add(Package(tracking_number=g, client_id=cli.id)); db.commit(); st.toast(f"✅ {g}")
                st.session_state.b_in = ""
        st.text_input("ESCÁNER BODEGA", key="b_in", on_change=reg)

elif modulo == "3. Despacho & Monitor":
    st.header("Salida a Ruta")
    mens = db.query(Courier).filter(Courier.is_active == True).all()
    col1, col2 = st.columns([1, 2])
    with col1:
        if mens:
            m_sel = st.selectbox("Mensajero", [f"{m.name} ({m.plate})" for m in mens])
            m_obj = db.query(Courier).filter(Courier.name == m_sel.split(" (")[0]).first()
            def desp():
                g = st.session_state.b_out.strip().upper()
                if g:
                    pkg = db.query(Package).filter(Package.tracking_number == g).first()
                    if pkg:
                        pkg.status = "EN RUTA"; pkg.courier_id = m_obj.id; db.commit(); st.toast(f"🚚 {g}")
                    st.session_state.b_out = ""
            st.text_input("ESCÁNER DESPACHO", key="b_out", on_change=desp)
    with col2:
        carga = db.query(Courier.name, func.count(Package.id)).join(Package).filter(Package.status == "EN RUTA").group_by(Courier.name).all()
        if carga: st.table(pd.DataFrame(carga, columns=["Mensajero", "Total"]))

elif modulo == "4. Edición de Datos":
    st.header("Corrección de Maestros")
    op = st.radio("Editar:", ["Clientes", "Mensajeros", "Productos"])
    if op == "Clientes":
        items = db.query(ClientB2B).all()
        if items:
            sel = st.selectbox("Cliente", [i.name for i in items])
            obj = db.query(ClientB2B).filter(ClientB2B.name == sel).first()
            with st.form("e_c"):
                n = st.text_input("Nombre", value=obj.name).upper()
                if st.form_submit_button("Actualizar"): obj.name = n; db.commit(); st.rerun()

# --- NUEVO MODULO 5: VISUALIZACIÓN DE BASE DE DATOS ---
elif modulo == "5. Base de Datos (Reportes)":
    st.header("Consulta General de Inventario")
    
    # Buscador Global
    search = st.text_input("🔍 Buscar guía específica:").upper()
    if search:
        res = db.query(Package).filter(Package.tracking_number.contains(search)).all()
        if res:
            st.dataframe(pd.DataFrame([{
                "Guía": p.tracking_number, 
                "Estado": p.status, 
                "Cliente": p.client.name, 
                "Mensajero": p.courier.name if p.courier else "N/A",
                "Último Movimiento": p.last_update.strftime("%Y-%m-%d %H:%M")
            } for p in res]))
        else: st.warning("No se encontró esa guía.")

    st.divider()
    
    tab_bodega, tab_ruta = st.tabs(["📦 En Bodega", "🚚 En Ruta"])
    
    with tab_bodega:
        st.subheader("Paquetes listos para despacho")
        bodega_data = db.query(Package).filter(Package.status == "BODEGA").all()
        if bodega_data:
            df_b = pd.DataFrame([{
                "Guía": p.tracking_number, 
                "Cliente": p.client.name, 
                "Fecha Ingreso": p.last_update.strftime("%Y-%m-%d %H:%M")
            } for p in bodega_data])
            st.dataframe(df_b, use_container_width=True)
        else: st.info("La bodega está vacía.")

    with tab_ruta:
        st.subheader("Control de entregas activas")
        ruta_data = db.query(Package).filter(Package.status == "EN RUTA").all()
        if ruta_data:
            df_r = pd.DataFrame([{
                "Guía": p.tracking_number, 
                "Mensajero": p.courier.name, 
                "Placa": p.courier.plate,
                "Cliente": p.client.name,
                "Hora Salida": p.last_update.strftime("%H:%M:%S")
            } for p in ruta_data])
            st.dataframe(df_r, use_container_width=True)
        else: st.info("No hay nada en ruta.")

db.close()
