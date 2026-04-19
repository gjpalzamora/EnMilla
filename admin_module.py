import streamlit as st
import pandas as pd
from sqlalchemy.orm import Session
from db_models import ClientB2B, Courier, Product

def display_admin_module(db: Session):
    st.header("⚙️ Configuración EnMilla")
    tabs = st.tabs(["Mensajeros", "Clientes B2B", "Productos", "🗂️ Gestión de Datos"])

    with tabs[0]:
        st.subheader("Registrar Mensajero")
        with st.form("f_courier", clear_on_submit=True):
            n = st.text_input("Nombre Completo")
            c = st.text_input("Cédula")
            p = st.text_input("Teléfono")
            if st.form_submit_button("Guardar"):
                if n and c:
                    db.add(Courier(name=n, document_id=c, phone=p))
                    db.commit()
                    st.success(f"Mensajero {n} registrado.")

    with tabs[1]:
        st.subheader("Registrar Cliente Corporativo")
        with st.form("f_client", clear_on_submit=True):
            cn = st.text_input("Nombre de Empresa")
            nit = st.text_input("NIT")
            if st.form_submit_button("Registrar Cliente"):
                db.add(ClientB2B(name=cn, nit=nit))
                db.commit()
                st.success("Cliente guardado.")

    with tabs[2]:
        st.subheader("Asignar Productos")
        clientes = db.query(ClientB2B).all()
        if clientes:
            cli_map = {cli.name: cli.id for cli in clientes}
            with st.form("f_prod", clear_on_submit=True):
                pn = st.text_input("Nombre del Producto")
                sel_cli = st.selectbox("Asociar a Cliente:", options=list(cli_map.keys()))
                if st.form_submit_button("Guardar Producto"):
                    db.add(Product(name=pn, client_id=cli_map[sel_cli]))
                    db.commit()
                    st.success("Producto registrado.")

    with tabs[3]:
        st.subheader("Auditoría de Registros")
        tipo = st.radio("Ver tabla de:", ["Mensajeros", "Clientes", "Productos"], horizontal=True)
        if tipo == "Mensajeros":
            data = db.query(Courier).all()
            if data:
                st.dataframe(pd.DataFrame([{"ID": m.id, "Nombre": m.name, "ID": m.document_id} for m in data]), use_container_width=True)
        elif tipo == "Clientes":
            data = db.query(ClientB2B).all()
            if data:
                st.dataframe(pd.DataFrame([{"ID": c.id, "Empresa": c.name, "NIT": c.nit} for c in data]), use_container_width=True)
        elif tipo == "Productos":
            data = db.query(Product).all()
            if data:
                st.dataframe(pd.DataFrame([{"ID": p.id, "Producto": p.name, "Dueño": p.client.name} for p in data]), use_container_width=True)
