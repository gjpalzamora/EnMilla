import streamlit as st
from sqlalchemy.orm import Session
from db_models import ClientB2B, Courier, Product

def display_admin_module(db: Session):
    st.header("⚙️ Panel de Administración")
    tabs = st.tabs(["Mensajeros", "Clientes B2B", "Productos"])
    
    with tabs[0]:
        st.subheader("Registro de Mensajeros")
        with st.form("form_courier"):
            name = st.text_input("Nombre Completo")
            doc_id = st.text_input("Cédula (Identificación)")
            phone = st.text_input("Teléfono")
            submitted = st.form_submit_button("Registrar Mensajero")
            if submitted and name and doc_id:
                try:
                    new_courier = Courier(name=name, document_id=doc_id, phone=phone)
                    db.add(new_courier)
                    db.commit()
                    st.success(f"Mensajero {name} registrado.")
                except Exception as e:
                    db.rollback()
                    st.error("Error: La cédula ya existe o la tabla se está sincronizando.")

        st.divider()
        st.subheader("Mensajeros Activos")
        try:
            couriers = db.query(Courier).all()
            if couriers:
                data = [{"Nombre": c.name, "Cédula": c.document_id, "Activo": c.is_active} for c in couriers]
                st.table(data)
            else:
                st.info("No hay mensajeros registrados.")
        except Exception:
            db.rollback()
            st.warning("Sincronizando base de datos... Refresca en unos segundos.")

    with tabs[1]:
        st.subheader("Clientes B2B")
        with st.form("form_client"):
            c_name = st.text_input("Nombre Empresa")
            nit = st.text_input("NIT")
            if st.form_submit_button("Guardar"):
                db.add(ClientB2B(name=c_name, nit=nit))
                db.commit()
                st.success("Cliente creado.")
