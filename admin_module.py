import streamlit as st
from sqlalchemy.orm import Session
from db_models import ClientB2B, Courier, Product

def display_admin_module(db: Session):
    st.header("⚙️ Panel de Administración")
    
    tabs = st.tabs(["Mensajeros", "Clientes B2B", "Productos"])
    
    # --- GESTIÓN DE MENSAJEROS ---
    with tabs[0]:
        st.subheader("Registro de Mensajeros")
        with st.form("form_courier"):
            name = st.text_input("Nombre Completo")
            doc_id = st.text_input("Cédula (Identificación)")
            phone = st.text_input("Teléfono")
            submitted = st.form_submit_button("Registrar Mensajero")
            
            if submitted:
                if name and doc_id:
                    new_courier = Courier(name=name, document_id=doc_id, phone=phone)
                    try:
                        db.add(new_courier)
                        db.commit()
                        st.success(f"Mensajero {name} registrado con éxito.")
                    except Exception as e:
                        db.rollback()
                        st.error(f"Error: La cédula ya existe o hubo un fallo: {e}")
                else:
                    st.warning("Nombre y Cédula son obligatorios.")

        st.divider()
        st.subheader("Mensajeros Activos")
        couriers = db.query(Courier).all()
        if couriers:
            data = [{"Nombre": c.name, "Cédula": c.document_id, "Teléfono": c.phone, "Activo": c.is_active} for c in couriers]
            st.table(data)

    # --- GESTIÓN DE CLIENTES ---
    with tabs[1]:
        st.subheader("Registro de Clientes (Dueños de Carga)")
        with st.form("form_client"):
            c_name = st.text_input("Nombre de la Empresa (Ej: Temu)")
            nit = st.text_input("NIT")
            c_submitted = st.form_submit_button("Registrar Cliente")
            
            if c_submitted:
                if c_name:
                    new_client = ClientB2B(name=c_name, nit=nit)
                    db.add(new_client)
                    db.commit()
                    st.success(f"Cliente {c_name} creado.")
                else:
                    st.warning("El nombre es obligatorio.")

    # --- GESTIÓN DE PRODUCTOS ---
    with tabs[2]:
        st.subheader("Configuración de Productos/Servicios")
        clients = db.query(ClientB2B).all()
        if clients:
            with st.form("form_product"):
                p_name = st.text_input("Nombre del Servicio (Ej: Entrega Local)")
                client_id = st.selectbox("Cliente", options=[c.id for c in clients], format_func=lambda x: next(c.name for c in clients if c.id == x))
                price = st.number_input("Precio al Cliente", min_value=0.0)
                cost = st.number_input("Costo Mensajero", min_value=0.0)
                p_submitted = st.form_submit_button("Guardar Producto")
                
                if p_submitted:
                    new_prod = Product(name=p_name, client_id=client_id, price_to_client=price, cost_to_courier=cost)
                    db.add(new_prod)
                    db.commit()
                    st.success("Producto configurado.")
        else:
            st.info("Primero registre un cliente en la pestaña anterior.")
