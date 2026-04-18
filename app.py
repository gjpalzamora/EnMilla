import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Boolean, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

# --- CONFIGURACIÓN DE NÚCLEO ---
DATABASE_URL = "sqlite:///enmilla_master_v11.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- MODELOS (PERSISTENCIA DE DATOS) ---
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
    fee_client = Column(Float, default=0.0)  # Lo que paga el cliente
    fee_courier = Column(Float, default=0.0) # Lo que se paga al mensajero
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
    status = Column(String(50), default="BODEGA")
    last_update = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    client = relationship("ClientB2B", back_populates="packages")
    courier = relationship("Courier", back_populates="packages")

Base.metadata.create_all(bind=engine)

# --- INTERFAZ ---
st.set_page_config(page_title="EnMilla ERP v11.0", layout="wide")
st.sidebar.title("🚚 Gestión Logística")
modulo = st.sidebar.radio("Navegación:", [
    "1. Administración", 
    "2. Recepción Bodega", 
    "3. Despacho & Monitor", 
    "4. Edición de Datos"
])

# --- MODULO 1: ADMINISTRACIÓN ---
if modulo == "1. Administración":
    st.header("Registro de Maestros")
    t1, t2, t3 = st.tabs(["Clientes", "Mensajeros", "Productos"])
    db = SessionLocal()
    
    with t1:
        with st.form("f_cli", clear_on_submit=True):
            n = st.text_input("Nombre Empresa").upper()
            nit = st.text_input("NIT")
            if st.form_submit_button("Guardar Cliente"):
                try:
                    db.add(ClientB2B(name=n, nit=nit)); db.commit()
                    st.success(f"Cliente {n} registrado.")
                except: st.error("Error: NIT o Nombre duplicado.")
    
    with t2:
        with st.form("f_cou", clear_on_submit=True):
            cn = st.text_input("Nombre Mensajero").upper()
            cp = st.text_input("Placa").upper()
            if st.form_submit_button("Guardar Mensajero"):
                try:
                    db.add(Courier(name=cn, plate=cp)); db.commit()
                    st.success(f"Mensajero {cn} registrado.")
                except: st.error("Error: Placa duplicada.")

    with t3:
        clis = db.query(ClientB2B).all()
        if clis:
            with st.form("f_prod", clear_on_submit=True):
                st.subheader("Nuevo Producto con Tarifas")
                pn = st.text_input("Nombre del Producto/Servicio").upper()
                c_sel = st.selectbox("Asociar a Cliente", [c.name for c in clis])
                col_f1, col_f2 = st.columns(2)
                f_cli = col_f1.number_input("Tarifa Cliente (Ingreso)", min_value=0.0, step=100.0)
                f_cou = col_f2.number_input("Tarifa Mensajero (Costo)", min_value=0.0, step=100.0)
                
                if st.form_submit_button("Crear Producto"):
                    target = db.query(ClientB2B).filter(ClientB2B.name == c_sel).first()
                    new_p = Product(name=pn, fee_client=f_cli, fee_courier=f_cou, client_id=target.id)
                    db.add(new_p); db.commit()
                    st.success(f"Producto {pn} creado para {c_sel}.")
        else:
            st.warning("Debe crear un cliente antes de registrar productos.")
    db.close()

# --- MODULO 2: RECEPCIÓN BODEGA (CONSERVA LÓGICA ANTERIOR) ---
elif modulo == "2. Recepción Bodega":
    st.header("Ingreso de Mercancía")
    db = SessionLocal()
    clis = db.query(ClientB2B).all()
    if clis:
        c_sel = st.selectbox("Cliente Remitente", [c.name for c in clis])
        cli = db.query(ClientB2B).filter(ClientB2B.name == c_sel).first()
        def reg():
            g = st.session_state.b_in.strip().upper()
            if g:
                if not db.query(Package).filter(Package.tracking_number == g).first():
                    db.add(Package(tracking_number=g, client_id=cli.id)); db.commit()
                    st.toast(f"✅ {g} en bodega")
                else: st.warning(f"La guía {g} ya existe.")
                st.session_state.b_in = ""
        st.text_input("ESCÁNER BODEGA", key="b_in", on_change=reg)
    db.close()

# --- MODULO 3: DESPACHO & MONITOR (CONSERVA VISIBILIDAD SOLICITADA) ---
elif modulo == "3. Despacho & Monitor":
    st.header("Salida a Ruta y Monitor de Carga")
    db = SessionLocal()
    mens = db.query(Courier).filter(Courier.is_active == True).all()
    col1, col2 = st.columns([1, 2])
    with col1:
        if mens:
            m_sel = st.selectbox("Mensajero de Turno", [f"{m.name} ({m.plate})" for m in mens])
            m_obj = db.query(Courier).filter(Courier.name == m_sel.split(" (")[0]).first()
            def desp():
                g = st.session_state.b_out.strip().upper()
                if g:
                    pkg = db.query(Package).filter(Package.tracking_number == g).first()
                    if pkg:
                        pkg.status = "EN RUTA"; pkg.courier_id = m_obj.id; db.commit()
                        st.toast(f"🚚 {g} asignado a {m_obj.name}")
                    else: st.error("La guía no ha sido recibida en bodega.")
                    st.session_state.b_out = ""
            st.text_input("ESCÁNER DESPACHO", key="b_out", on_change=desp)
    with col2:
        st.subheader("📦 Estado de Carga Actual")
        carga = db.query(Courier.name, func.count(Package.id)).join(Package).filter(Package.status == "EN RUTA").group_by(Courier.name).all()
        if carga:
            st.table(pd.DataFrame(carga, columns=["Mensajero", "Total Guías"]))
            with st.expander("Ver detalle por número de guía"):
                det = db.query(Package.tracking_number, Courier.name).join(Courier).filter(Package.status == "EN RUTA").all()
                st.dataframe(pd.DataFrame(det, columns=["Guía", "Mensajero"]), use_container_width=True)
        else: st.info("No hay entregas en curso.")
    db.close()

# --- MODULO 4: EDICIÓN DE DATOS ---
elif modulo == "4. Edición de Datos":
    st.header("Corrección y Edición de Maestros")
    db = SessionLocal()
    op = st.radio("¿Qué desea corregir?", ["Clientes", "Mensajeros", "Productos"])
    
    if op == "Clientes":
        items = db.query(ClientB2B).all()
        if items:
            sel = st.selectbox("Seleccione Cliente", [i.name for i in items])
            obj = db.query(ClientB2B).filter(ClientB2B.name == sel).first()
            with st.form("e_c"):
                n = st.text_input("Nombre", value=obj.name).upper()
                nit = st.text_input("NIT", value=obj.nit)
                if st.form_submit_button("Actualizar Cliente"):
                    obj.name = n; obj.nit = nit; db.commit(); st.rerun()
    
    elif op == "Mensajeros":
        items = db.query(Courier).all()
        if items:
            sel = st.selectbox("Seleccione Mensajero", [i.name for i in items])
            obj = db.query(Courier).filter(Courier.name == sel).first()
            with st.form("e_m"):
                n = st.text_input("Nombre", value=obj.name).upper()
                p = st.text_input("Placa", value=obj.plate).upper()
                act = st.checkbox("Activo", value=obj.is_active)
                if st.form_submit_button("Actualizar Mensajero"):
                    obj.name = n; obj.plate = p; obj.is_active = act; db.commit(); st.rerun()

    elif op == "Productos":
        items = db.query(Product).all()
        if items:
            sel = st.selectbox("Seleccione Producto", [f"{p.id} | {p.name}" for p in items])
            p_id = int(sel.split(" | ")[0])
            obj = db.query(Product).get(p_id)
            with st.form("e_p"):
                n = st.text_input("Nombre", value=obj.name).upper()
                f1 = st.number_input("Tarifa Cliente", value=obj.fee_client)
                f2 = st.number_input("Tarifa Mensajero", value=obj.fee_courier)
                if st.form_submit_button("Actualizar Producto"):
                    obj.name = n; obj.fee_client = f1; obj.fee_courier = f2; db.commit(); st.rerun()
    db.close()
