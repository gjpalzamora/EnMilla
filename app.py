import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Boolean, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import io

# --- 1. CONFIGURACIÓN DE BASE DE DATOS ---
DATABASE_URL = "sqlite:///enmilla_v11_master.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- 2. MODELOS DE DATOS (ESTRUCTURA COMPLETA RECUPERADA) ---
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
    product_name = Column(String(255)) # Conservado para reportes rápidos
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

# --- 3. FUNCIONES DE EXPORTACIÓN ---
def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='EnMilla_Report')
    return output.getvalue()

# --- 4. INTERFAZ ---
st.set_page_config(page_title="EnMilla ERP v11.0", layout="wide")
st.sidebar.title("🚚 Panel Enmilla")
modulo = st.sidebar.radio("Ir a:", [
    "1. Administración (Maestros)", 
    "2. Operaciones (Recibir)", 
    "3. Despacho y Monitor", 
    "4. Inventario y Trazabilidad",
    "5. Módulo de Edición"
])

# --- MÓDULO 1: ADMINISTRACIÓN ---
if modulo == "1. Administración (Maestros)":
    st.header("Configuración de la Operación")
    t1, t2, t3 = st.tabs(["Clientes B2B", "Mensajeros", "Productos Alfanuméricos"])
    
    with t1:
        with st.form("f_cli", clear_on_submit=True):
            n = st.text_input("Nombre Empresa").upper()
            nit = st.text_input("NIT")
            if st.form_submit_button("Guardar Cliente"):
                db = SessionLocal()
                try:
                    db.add(ClientB2B(name=n, nit=nit))
                    db.commit()
                    st.success(f"Cliente {n} registrado.")
                except: st.error("Error: NIT o Nombre ya existen.")
                db.close()

    with t2:
        with st.form("f_cou", clear_on_submit=True):
            cn = st.text_input("Nombre Mensajero").upper()
            cp = st.text_input("Placa").upper()
            if st.form_submit_button("Guardar Mensajero"):
                db = SessionLocal()
                try:
                    db.add(Courier(name=cn, plate=cp))
                    db.commit()
                    st.success(f"Mensajero {cn} creado.")
                except: st.error("Error: Placa ya existe.")
                db.close()

    with t3:
        db = SessionLocal()
        clis = db.query(ClientB2B).all()
        if clis:
            with st.form("f_prod", clear_on_submit=True):
                pn = st.text_input("Nombre Producto (Alfanumérico)").upper()
                c_sel = st.selectbox("Asociar a Cliente", [c.name for c in clis])
                if st.form_submit_button("Crear Producto"):
                    target = db.query(ClientB2B).filter(ClientB2B.name == c_sel).first()
                    db.add(Product(name=pn, client_id=target.id))
                    db.commit()
                    st.success(f"Producto {pn} enlazado a {c_sel}.")
        db.close()

# --- MÓDULO 2: OPERACIONES (RECEPCIÓN SCANNER) ---
elif modulo == "2. Operaciones (Recibir)":
    st.header("Entrada Automática (Bodega)")
    db = SessionLocal()
    clis = db.query(ClientB2B).all()
    if clis:
        c_nom = st.selectbox("Cliente", [c.name for c in clis])
        cli_obj = db.query(ClientB2B).filter(ClientB2B.name == c_nom).first()
        prods = db.query(Product).filter(Product.client_id == cli_obj.id).all()
        p_nom = st.selectbox("Producto", [p.name for p in prods] if prods else ["GENÉRICO"])

        def registrar_in():
            guia = st.session_state.barcode_in.strip().upper()
            if guia:
                db_s = SessionLocal()
                if not db_s.query(Package).filter(Package.tracking_number == guia).first():
                    p = Package(tracking_number=guia, client_id=cli_obj.id, product_name=p_nom, status="BODEGA")
                    db_s.add(p); db_s.commit()
                    db_s.add(Movement(package_id=p.id, description=f"Ingreso Bodega - Producto: {p_nom}"))
                    db_s.commit()
                    st.toast(f"✅ {guia} Recibido")
                else: st.warning("La guía ya existe.")
                db_s.close()
                st.session_state.barcode_in = ""
        st.text_input("ESCANEE AQUÍ PARA RECIBIR", key="barcode_in", on_change=registrar_in)
    db.close()

# --- MÓDULO 3: DESPACHO Y MONITOR ---
elif modulo == "3. Despacho y Monitor":
    st.header("Salida a Ruta y Monitor de Mensajeros")
    db = SessionLocal()
    mens = db.query(Courier).filter(Courier.is_active == True).all()
    
    c1, c2 = st.columns([1, 2])
    with c1:
        st.subheader("Cargar Guías")
        if mens:
            m_sel = st.selectbox("Mensajero", [f"{m.name} | {m.plate}" for m in mens])
            m_id = db.query(Courier).filter(Courier.name == m_sel.split(" | ")[0]).first().id

            def registrar_out():
                guia = st.session_state.barcode_out.strip().upper()
                if guia:
                    db_d = SessionLocal()
                    p = db_d.query(Package).filter(Package.tracking_number == guia).first()
                    if p:
                        p.status = "EN RUTA"
                        p.courier_id = m_id
                        db_d.add(Movement(package_id=p.id, description=f"Despachado - Mensajero: {m_sel}"))
                        db_d.commit()
                        st.toast(f"🚚 {guia} Cargada")
                    else: st.error("Guía no encontrada en bodega.")
                    db_d.close()
                    st.session_state.barcode_out = ""
            st.text_input("ESCANEE PARA DESPACHO", key="barcode_out", on_change=registrar_out)

    with c2:
        st.subheader("Estado de Carga Actual")
        carga = db.query(Courier.name, Courier.plate, func.count(Package.id)).join(Package).filter(Package.status == "EN RUTA").group_by(Courier.name).all()
        if carga:
            df_carga = pd.DataFrame(carga, columns=["Mensajero", "Placa", "Cant. Guías"])
            st.table(df_carga)
            st.download_button("📥 Reporte Excel Carga", data=to_excel(df_carga), file_name="carga_actual.xlsx")
        else: st.info("Sin rutas activas.")
    db.close()

# --- MÓDULO 4: INVENTARIO Y TRAZABILIDAD ---
elif modulo == "4. Inventario y Trazabilidad":
    st.header("Consultas e Inventario")
    db = SessionLocal()
    t_inv, t_track = st.tabs(["Inventario Bodega", "Trazabilidad de Guía"])
    
    with t_inv:
        inv = db.query(Package.tracking_number, ClientB2B.name, Package.product_name, Package.created_at).join(ClientB2B).filter(Package.status == "BODEGA").all()
        if inv:
            df_inv = pd.DataFrame(inv, columns=["Guía", "Cliente", "Producto", "Ingreso"])
            st.dataframe(df_inv, use_container_width=True)
            st.download_button("📥 Bajar Inventario", data=to_excel(df_inv), file_name="inventario.xlsx")

    with t_track:
        busqueda = st.text_input("Rastrear Guía:").upper()
        if busqueda:
            p = db.query(Package).filter(Package.tracking_number == busqueda).first()
            if p:
                st.info(f"Estado Actual: **{p.status}**")
                st.write(f"**Cliente:** {p.client.name} | **Producto:** {p.product_name}")
                if p.courier: st.write(f"**Mensajero:** {p.courier.name}")
                st.write("---")
                movs = db.query(Movement).filter(Movement.package_id == p.id).order_by(Movement.timestamp.desc()).all()
                for m in movs:
                    st.write(f"🕒 {m.timestamp.strftime('%d/%m/%Y %H:%M')} - {m.description}")
            else: st.error("No existe.")
    db.close()

# --- MÓDULO 5: EDICIÓN COMPLETA ---
elif modulo == "5. Edición de Maestros":
    st.header("Módulo de Correcciones")
    db = SessionLocal()
    edit_tipo = st.radio("Editar:", ["Productos", "Clientes", "Mensajeros"])
    
    if edit_tipo == "Productos":
        prods = db.query(Product).all()
        if prods:
            p_sel = st.selectbox("Producto", [f"{p.id} | {p.name}" for p in prods])
            p_obj = db.query(Product).get(int(p_sel.split(" | ")[0]))
            with st.form("e_p"):
                new_n = st.text_input("Nombre", value=p_obj.name).upper()
                if st.form_submit_button("Actualizar"):
                    p_obj.name = new_n; db.commit(); st.success("Listo"); st.rerun()

    elif edit_tipo == "Clientes":
        clis = db.query(ClientB2B).all()
        if clis:
            c_sel = st.selectbox("Cliente", [c.name for c in clis])
            c_obj = db.query(ClientB2B).filter(ClientB2B.name == c_sel).first()
            with st.form("e_c"):
                new_n = st.text_input("Nombre", value=c_obj.name).upper()
                new_nit = st.text_input("NIT", value=c_obj.nit)
                if st.form_submit_button("Actualizar"):
                    c_obj.name = new_n; c_obj.nit = new_nit; db.commit(); st.rerun()

    elif edit_tipo == "Mensajeros":
        mens = db.query(Courier).all()
        if mens:
            m_sel = st.selectbox("Mensajero", [m.name for m in mens])
            m_obj = db.query(Courier).filter(Courier.name == m_sel).first()
            with st.form("e_m"):
                new_n = st.text_input("Nombre", value=m_obj.name).upper()
                new_p = st.text_input("Placa", value=m_obj.plate).upper()
                act = st.checkbox("Activo", value=m_obj.is_active)
                if st.form_submit_button("Actualizar"):
                    m_obj.name = new_n; m_obj.plate = new_p; m_obj.is_active = act; db.commit(); st.rerun()
    db.close()
