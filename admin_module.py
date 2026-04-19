import streamlit as st
from sqlalchemy.orm import Session
from db_models import ClientB2B, Courier, Product

def display_admin_module(db: Session):
    st.header("⚙️ Panel de Administración")
    tabs = st.tabs(["Mensajeros", "Clientes B2B", "Productos"])
    
    with tabs[0]:
        st.subheader("Registro de Mensajeros")
        with st.form("form_courier", clear_on_submit=True):
            name = st.text_input("Nombre Completo")
            doc_id = st.text_input("Cédula (Identificación)")
            phone = st.text_input("Teléfono")
            submitted = st.form_submit_button("Registrar Mensajero")
            if submitted:
                if name and doc_id:
                    try:
                        new_courier = Courier(name=name, document_id=doc_id, phone=phone)
                        db.add(new_courier)
                        db.commit()
                        st.success(f"Mensajero {name} registrado con éxito.")
                    except Exception as e:
                        db.rollback()
                        st.error(f"Error al registrar: Cédula duplicada o error de red.")
                else:
                    st.warning("Nombre y Cédula son campos obligatorios.")

        st.divider()
        st.subheader("Mensajeros Activos")
        try:
            couriers = db.query(Courier).all()
            if couriers:
                data = [{"Nombre": c.name, "Cédula": c.document_id, "Teléfono": c.phone, "Activo": c.is_active} for c in couriers]
                st.table(data)
            else:
                st.info("No hay mensajeros registrados aún.")
        except Exception as e:
            db.rollback()
            st.warning("Cargando lista de mensajeros...")

    with tabs[1]:
        st.subheader("Gestión de Clientes B2B")
        with st.form("form_client", clear_on_submit=True):
            c_name = st.text_input("Nombre de la Empresa")
            nit = st.text_input("NIT")
            if st.form_submit_button("Guardar Cliente"):
                if c_name:
                    try:
                        db.add(ClientB2B(name=c_name, nit=nit))
                        db.commit()
                        st.success(f"Cliente {c_name} creado.")
                    except:
                        db.rollback()
                        st.error("Error al crear cliente.")
                else:
                    st.warning("El nombre es obligatorio.")
