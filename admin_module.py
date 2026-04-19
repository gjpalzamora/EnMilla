import streamlit as st
import pandas as pd
from sqlalchemy.orm import Session
from db_models import ClientB2B, Courier, Product

def display_admin_module(db: Session):
    st.header("⚙️ Configuración EnMilla")
    t1, t2 = st.tabs(["📝 Registro", "📋 Ver Datos"])

    with t1:
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Mensajeros")
            with st.form("f_courier", clear_on_submit=True):
                nom = st.text_input("Nombre")
                ced = st.text_input("Cédula")
                tel = st.text_input("Celular")
                if st.form_submit_button("Registrar"):
                    if nom and ced:
                        db.add(Courier(name=nom, document_id=ced, phone=tel))
                        db.commit()
                        st.success(f"Registrado: {nom}")
        with c2:
            st.subheader("Clientes")
            with st.form("f_client", clear_on_submit=True):
                emp = st.text_input("Empresa")
                nit = st.text_input("NIT")
                if st.form_submit_button("Crear"):
                    db.add(ClientB2B(name=emp, nit=nit))
                    db.commit()
                    st.success("Cliente Creado")

    with t2:
        ver = st.radio("Mostrar:", ["Mensajeros", "Clientes", "Productos"], horizontal=True)
        try:
            if ver == "Mensajeros":
                res = db.query(Courier).all()
                if res: st.dataframe(pd.DataFrame([{"ID": r.id, "Nombre": r.name, "ID": r.document_id, "Tel": r.phone} for r in res]))
            elif ver == "Clientes":
                res = db.query(ClientB2B).all()
                if res: st.dataframe(pd.DataFrame([{"ID": r.id, "Empresa": r.name, "NIT": r.nit} for r in res]))
            elif ver == "Productos":
                res = db.query(Product).all()
                if res: st.dataframe(pd.DataFrame([{"ID": r.id, "Producto": r.name, "Dueño": r.client.name} for r in res]))
        except Exception:
            st.error("Error al leer la base de datos. Por favor, reinicie la aplicación.")
