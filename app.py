import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Boolean, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import io

# --- 1. CONFIGURACIÓN DE BASE DE DATOS ---
DATABASE_URL = "sqlite:///enmilla_v14_final.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- 2. MODELOS DE DATOS ---
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
    package = relationship("Movement", back_populates="movements") # Fix circular logic

Base.metadata.create_all(bind=engine)

# --- 3. FUNCIONES DE APOYO ---
def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Reporte')
    return output.getvalue()

# --- 4. INTERFAZ PRINCIPAL ---
st.set_page_config(page_title="EnMilla ERP v14.0", layout="wide")
st.sidebar.title("🚚 Panel EnMilla")
modulo = st.sidebar.radio("Ir a:", [
    "1. Administración", 
    "2. Operaciones (Recibir)", 
    "3. Despacho (Cargar)", 
    "4. Gestión de Datos (Ver/Editar)"
])

# --- MÓDULO 1: ADMINISTRACIÓN ---
if modulo == "1. Administración":
    st.header("Gestión de Maestros")
    t1, t2, t3 = st.tabs(["Clientes B2B", "Mensajeros", "Productos Alfanuméricos"])
    
    with t1:
        with st.form("form_cliente", clear_on_submit=True):
            n = st.text_input("Nombre de la Empresa").upper()
            nit = st.text_input("NIT")
            if st.form_submit_button("Registrar Cliente"):
                db = SessionLocal()
                try:
                    db.add(ClientB2B(name=n, nit=nit))
                    db.commit()
                    st.success(f"Cliente {n} guardado.")
                except: st.error("Error: El NIT o Nombre ya existen.")
                db.close()

    with t2:
        with st.form("form_courier", clear_on_submit=True):
            cn = st.text_input("Nombre del Mensajero").upper()
            cp = st.text_input("Placa del Vehículo").upper()
            if st.form_submit_button("Registrar Mensajero"):
                db = SessionLocal()
                try:
                    db.add(Courier(name=cn, plate=cp))
                    db.commit()
                    st.success(f"Mensajero {cn} registrado.")
                except: st.error("Error: La placa ya está registrada.")
                db.close()

    with t3:
        db = SessionLocal()
        clis = db.query(ClientB2B).all()
        if clis:
            with st.form("form_prod", clear_on_submit=True):
                pn = st.text_input("Nombre del Producto").upper()
                c_sel = st.selectbox("Asociar al Cliente", [c.name for c in clis])
                if st.form_submit_button("Crear Producto"):
                    target = db.query(ClientB2B).filter(ClientB2B.name == c_sel).first()
                    db.add(Product(name=pn, client_id=target.id))
                    db.commit()
                    st.success(f"Producto {pn} asignado a {c_sel}.")
        else: st.warning("Primero debe crear un cliente.")
        db.close()

# --- MÓDULO 2: OPERACIONES (RECIBIR) ---
elif modulo == "2. Operaciones (Recibir)":
    st.header("Entrada de Mercancía")
    db = SessionLocal()
    clis = db.query(ClientB2B).all()
    if clis:
        cli_n = st.selectbox("Seleccione Cliente", [c.name for c in clis])
        cli_obj = db.query(ClientB2B).filter(ClientB2B.name == cli_n).first()
        prods = db.query(Product).filter(Product.client_id == cli_obj.id).all()
        p_nom = st.selectbox("Seleccione Producto", [p.name for p in prods] if prods else ["GENÉRICO"])

        def registrar_entrada():
            guia = st.session_state.scan_in.strip().upper()
            if guia:
                db_s = SessionLocal()
                existente = db_s.query(Package).filter(Package.tracking_number == guia).first()
                if not existente:
                    p = Package(tracking_number=guia, client_id=cli_obj.id, product_name=p_nom, status="BODEGA")
                    db_s.add(p); db_s.commit()
                    db_s.add(Movement(package_id=p.id, description=f"Ingreso a Bodega - {p_nom}"))
                    db_s.commit()
                    st.toast(f"✅ Guía {guia} recibida.")
                else: st.error("Esa guía ya fue registrada anteriormente.")
                db_s.close()
                st.session_state.scan_in = ""
        st.text_input("ESCANEE TRACKING", key="scan_in", on_change=registrar_entrada)
    db.close()

# --- MÓDULO 3: DESPACHO (CARGAR) ---
elif modulo == "3. Despacho (Cargar)":
    st.header("Salida a Ruta")
    db = SessionLocal()
    mens = db.query(Courier).filter(Courier.is_active == True).all()
    
    col1, col2 = st.columns([1, 2])
    with col1:
        if mens:
            m_sel = st.selectbox("Mensajero de Salida", [f"{m.name} ({m.plate})" for m in mens])
            m_id = db.query(Courier).filter(Courier.name == m_sel.split(" (")[0]).first().id

            def registrar_salida():
                guia = st.session_state.scan_out.strip().upper()
                if guia:
                    db_d = SessionLocal()
                    p = db_d.query(Package).filter(Package.tracking_number == guia).first()
                    if p and p.status == "BODEGA":
                        p.status = "EN RUTA"; p.courier_id = m_id
                        db_d.add(Movement(package_id=p.id, description=f"Despachado con {m_sel}"))
                        db_d.commit()
                        st.toast(f"🚚 Guía {guia} cargada.")
                    else: st.error("Guía no encontrada o ya está fuera de bodega.")
                    db_d.close()
                    st.session_state.scan_out = ""
            st.text_input("ESCANEE PARA DESPACHO", key="scan_out", on_change=registrar_salida)

    with col2:
        st.subheader("Monitor de Carga Actual")
        carga = db.query(Courier.name, Courier.plate, func.count(Package.id)).join(Package).filter(Package.status == "EN RUTA").group_by(Courier.name).all()
        if carga:
            df_c = pd.DataFrame(carga, columns=["Nombre", "Placa", "Paquetes"])
            st.table(df_c)
            st.download_button("📥 Excel Carga", data=to_excel(df_c), file_name="hoja_ruta.xlsx")
    db.close()

# --- MÓDULO 4: GESTIÓN DE DATOS ---
elif modulo == "4. Gestión de Datos (Ver/Editar)":
    st.header("Consultas y Correcciones")
    db = SessionLocal()
    tab1, tab2, tab3 = st.tabs(["Inventario", "Trazabilidad", "Editar Maestros"])
    
    with tab1:
        inv = db.query(Package.tracking_number, ClientB2B.name, Package.product_name, Package.created_at).join(ClientB2B).filter(Package.status == "BODEGA").all()
        if inv:
            df_i = pd.DataFrame(inv, columns=["Tracking", "Cliente", "Producto", "Fecha Ingreso"])
            st.dataframe(df_i, use_container_width=True)
            st.download_button("📥 Bajar Inventario", data=to_excel(df_i), file_name="stock.xlsx")

    with tab2:
        search = st.text_input("Rastrear Guía:").upper()
        if search:
            p = db.query(Package).filter(Package.tracking_number == search).first()
            if p:
                st.write(f"**Estado:** {p.status} | **Producto:** {p.product_name}")
                hist = db.query(Movement).filter(Movement.package_id == p.id).order_by(Movement.timestamp.desc()).all()
                for m in hist: st.write(f"🕒 {m.timestamp.strftime('%d/%m/%Y %H:%M')} - {m.description}")
            else: st.error("Guía inexistente.")

    with tab3:
        tipo = st.radio("¿Qué desea corregir?", ["Productos", "Clientes", "Mensajeros"])
        if tipo == "Productos":
            prods = db.query(Product).all()
            if prods:
                p_id = st.selectbox("Seleccione Producto", [f"{p.id} | {p.name}" for p in prods])
                p_obj = db.query(Product).get(int(p_id.split(" | ")[0]))
                with st.form("edit_p"):
                    new_n = st.text_input("Nuevo Nombre", value=p_obj.name).upper()
                    if st.form_submit_button("Actualizar"):
                        p_obj.name = new_n; db.commit(); st.success("Actualizado"); st.rerun()
        # Se pueden añadir secciones similares para Clientes y Mensajeros aquí.
    db.close()
