import streamlit as st
import pandas as pd
from sqlalchemy.orm import Session
from db_models import ClientB2B, Courier, Product

def display_admin_module(db: Session):
    st.header("⚙️ Configuración Maestra")
    tabs = st.tabs(["Mensajeros", "Clientes", "Productos", "🗂️ Base de Datos"])

    with tabs[0]: # Mensajeros
        with st.form("add_courier", clear_on_submit=True):
            n = st.text_input("Nombre Completo")
            c = st.text_input("Cédula")
            p = st.text_input("Teléfono")
            if st.form_submit_button("Registrar"):
                db.add(Courier(name=n, document_id=c, phone=p))
                db.commit()
                st.success(f"Mensajero {n} registrado.")

    with tabs[1]: # Clientes
        with st.form("add_client", clear_on_submit=True):
            cn = st.text_input("Empresa")
            nit = st.text_input("NIT")
            if st.form_submit_button("Crear Cliente"):
                db.add(ClientB2B(name=cn, nit=nit))
                db.commit()
                st.success("Cliente guardado.")

    with tabs[2]: # Productos
        clientes = db.query(ClientB2B).all()
        if not clientes:
            st.warning("Cree un cliente primero.")
        else:
            cli_map = {cli.name: cli.id for cli in clientes}
            with st.form("add_product", clear_on_submit=True):
                pn = st.text_input("Nombre del Producto (ej: Sobre, Caja)")
                target_cli = st.selectbox("Asignar a:", options=list(cli_map.keys()))
                if st.form_submit_button("Vincular Producto"):
                    db.add(Product(name=pn, client_id=cli_map[target_cli]))
                    db.commit()
                    st.success("Producto vinculado.")

    with tabs[3]: # Visualización y Eliminación
        st.subheader("Control de Registros")
        sub_tab = st.selectbox("Ver tabla de:", ["Mensajeros", "Clientes", "Productos"])
        
        if sub_tab == "Mensajeros":
            items = db.query(Courier).all()
            if items:
                df = pd.DataFrame([{"ID": i.id, "Nombre": i.name, "Documento": i.document_id} for i in items])
                st.table(df)
                to_del = st.number_input("ID a eliminar", min_value=0, step=1)
                if st.button("Eliminar Mensajero"):
                    item = db.query(Courier).get(to_del)
                    if item:
                        db.delete(item)
                        db.commit()
                        st.rerun()

        elif sub_tab == "Clientes":
            items = db.query(ClientB2B).all()
            if items:
                df = pd.DataFrame([{"ID": i.id, "Empresa": i.name, "NIT": i.nit} for i in items])
                st.table(df)
                # Lógica similar para eliminar...
