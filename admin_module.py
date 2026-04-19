import streamlit as st
import pandas as pd
from sqlalchemy.orm import Session
from db_models import ClientB2B, Courier, Product

def display_admin_module(db: Session):
    st.header("⚙️ Administración EnMilla")
    t_reg, t_db = st.tabs(["📝 Registro", "📋 Base de Datos"])

    with t_reg:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Mensajero")
            with st.form("f_courier", clear_on_submit=True):
                n = st.text_input("Nombre")
                c = st.text_input("Cédula")
                p = st.text_input("Teléfono")
                if st.form_submit_button("Guardar"):
                    db.add(Courier(name=n, document_id=c, phone=p))
                    db.commit()
                    st.success("Mensajero creado.")
        
        with col2:
            st.subheader("Cliente")
            with st.form("f_client", clear_on_submit=True):
                cn = st.text_input("Empresa")
                nit = st.text_input("NIT")
                if st.form_submit_button("Crear"):
                    db.add(ClientB2B(name=cn, nit=nit))
                    db.commit()
                    st.success("Cliente creado.")

        st.divider()
        st.subheader("Producto")
        clientes = db.query(ClientB2B).all()
        if clientes:
            c_map = {cli.name: cli.id for cli in clientes}
            with st.form("f_prod", clear_on_submit=True):
                pn = st.text_input("Producto")
                cl = st.selectbox("Asignar a:", options=list(c_map.keys()))
                if st.form_submit_button("Vincular"):
                    db.add(Product(name=pn, client_id=c_map[cl]))
                    db.commit()
                    st.success("Vinculado.")

    with t_db:
        ver = st.radio("Tabla:", ["Mensajeros", "Clientes", "Productos"], horizontal=True)
        try:
            if ver == "Mensajeros":
                items = db.query(Courier).all()
                if items: st.table(pd.DataFrame([{"ID": i.id, "Nombre": i.name, "Cédula": i.document_id, "Tel": i.phone} for i in items]))
            elif ver == "Clientes":
                items = db.query(ClientB2B).all()
                if items: st.table(pd.DataFrame([{"ID": i.id, "Empresa": i.name, "NIT": i.nit} for i in items]))
            elif ver == "Productos":
                items = db.query(Product).all()
                if items: st.table(pd.DataFrame([{"ID": i.id, "Producto": i.name, "Dueño": i.client.name} for i in items]))
        except Exception:
            st.warning("Actualizando estructura... Intente de nuevo en un momento.")
