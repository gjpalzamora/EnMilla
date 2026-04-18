# admin_module.py

import streamlit as st
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime

# --- IMPORTACIONES NECESARIAS ---
try:
    from db_models import ClientB2B, Product, Courier, Base, engine, Session, format_datetime_utc, TIMEZONE, PYTZ_AVAILABLE
    from sqlalchemy import func
    DB_MODELS_IMPORTED = True
except ImportError as e:
    st.error(f"Error de importación en admin_module.py: {e}. Asegúrate de que 'db_models.py' exista y las importaciones sean correctas.")
    DB_MODELS_IMPORTED = False

# --- FUNCIONES AUXILIARES PARA CRUD (Crear, Leer, Actualizar, Eliminar) ---
# (Las funciones CRUD para ClientB2B, Product, Courier se mantienen igual que en la versión anterior)
# ... (código CRUD omitido por brevedad, pero debe estar presente) ...

# --- CRUD para ClientB2B (copiado de la versión anterior) ---
def get_clients(db: Session):
    if not DB_MODELS_IMPORTED: return []
    try:
        return db.query(ClientB2B).order_by(ClientB2B.name).all()
    except Exception as e:
        st.error(f"Error al obtener clientes: {e}")
        return []

def add_client(db: Session, name: str, nit: str):
    if not DB_MODELS_IMPORTED: return False
    try:
        now = datetime.utcnow()
        new_client = ClientB2B(name=name, nit=nit, created_at=now, updated_at=now)
        db.add(new_client)
        db.commit()
        st.success(f"Cliente '{name}' añadido correctamente.")
        return True
    except IntegrityError:
        db.rollback()
        st.error(f"Error: El cliente con nombre '{name}' o NIT '{nit}' ya existe.")
        return False
    except Exception as e:
        db.rollback()
        st.error(f"Error al añadir cliente: {e}")
        return False

def update_client(db: Session, client_id: int, name: str, nit: str):
    if not DB_MODELS_IMPORTED: return False
    try:
        client = db.query(ClientB2B).filter(ClientB2B.id == client_id).first()
        if client:
            client.name = name
            client.nit = nit
            client.updated_at = datetime.utcnow()
            db.commit()
            st.success(f"Cliente '{name}' (ID: {client_id}) actualizado correctamente.")
            return True
        else:
            st.error(f"Error: Cliente con ID {client_id} no encontrado.")
            return False
    except IntegrityError:
        db.rollback()
        st.error(f"Error: Ya existe otro cliente con nombre '{name}' o NIT '{nit}'.")
        return False
    except Exception as e:
        db.rollback()
        st.error(f"Error al actualizar cliente: {e}")
        return False

def delete_client(db: Session, client_id: int):
    if not DB_MODELS_IMPORTED: return False
    try:
        client = db.query(ClientB2B).filter(ClientB2B.id == client_id).first()
        if client:
            if client.packages or client.client_shipments:
                st.warning(f"No se puede eliminar el cliente '{client.name}' (ID: {client_id}) porque tiene paquetes o envíos asociados.")
                return False
            db.delete(client)
            db.commit()
            st.success(f"Cliente con ID {client_id} eliminado correctamente.")
            return True
        else:
            st.error(f"Error: Cliente con ID {client_id} no encontrado.")
            return False
    except Exception as e:
        db.rollback()
        st.error(f"Error al eliminar cliente: {e}")
        return False

# --- CRUD para Product (copiado de la versión anterior) ---
def get_products(db: Session, client_id: int = None):
    if not DB_MODELS_IMPORTED: return []
    try:
        query = db.query(Product, ClientB2B.name.label("client_name")).join(ClientB2B).order_by(Product.name)
        if client_id:
            query = query.filter(Product.client_id == client_id)
        results = query.all()
        products_list = []
        for product, client_name in results:
            products_list.append({
                "id": product.id, "name": product.name, "client_name": client_name,
                "client_id": product.client_id, "price_to_client": product.price_to_client,
                "cost_to_courier": product.cost_to_courier, "created_at": product.created_at,
                "updated_at": product.updated_at
            })
        return products_list
    except Exception as e:
        st.error(f"Error al obtener productos: {e}")
        return []

def add_product(db: Session, name: str, client_id: int, price_to_client: float, cost_to_courier: float):
    if not DB_MODELS_IMPORTED: return False
    try:
        now = datetime.utcnow()
        new_product = Product(name=name, client_id=client_id, price_to_client=price_to_client, 
                              cost_to_courier=cost_to_courier, created_at=now, updated_at=now)
        db.add(new_product)
        db.commit()
        st.success(f"Producto '{name}' añadido correctamente.")
        return True
    except IntegrityError:
        db.rollback()
        st.error(f"Error: El producto con nombre '{name}' ya existe para este cliente.")
        return False
    except Exception as e:
        db.rollback()
        st.error(f"Error al añadir producto: {e}")
        return False

def update_product(db: Session, product_id: int, name: str, client_id: int, price_to_client: float, cost_to_courier: float):
    if not DB_MODELS_IMPORTED: return False
    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        if product:
            product.name = name
            product.client_id = client_id
            product.price_to_client = price_to_client
            product.cost_to_courier = cost_to_courier
            product.updated_at = datetime.utcnow()
            db.commit()
            st.success(f"Producto '{name}' (ID: {product_id}) actualizado correctamente.")
            return True
        else:
            st.error(f"Error: Producto con ID {product_id} no encontrado.")
            return False
    except IntegrityError:
        db.rollback()
        st.error(f"Error: Ya existe otro producto con nombre '{name}' para este cliente.")
        return False
    except Exception as e:
        db.rollback()
        st.error(f"Error al actualizar producto: {e}")
        return False

def delete_product(db: Session, product_id: int):
    if not DB_MODELS_IMPORTED: return False
    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        if product:
            if product.client_shipments:
                st.warning(f"No se puede eliminar el producto '{product.name}' (ID: {product_id}) porque tiene envíos asociados.")
                return False
            db.delete(product)
            db.commit()
            st.success(f"Producto con ID {product_id} eliminado correctamente.")
            return True
        else:
            st.error(f"Error: Producto con ID {product_id} no encontrado.")
            return False
    except Exception as e:
        db.rollback()
        st.error(f"Error al eliminar producto: {e}")
        return False

# --- CRUD para Courier (copiado de la versión anterior) ---
def get_couriers(db: Session, active_only: bool = False):
    if not DB_MODELS_IMPORTED: return []
    try:
        query = db.query(Courier)
        if active_only:
            query = query.filter(Courier.is_active == True)
        return query.order_by(Courier.name).all()
    except Exception as e:
        st.error(f"Error al obtener mensajeros: {e}")
        return []

def add_courier(db: Session, name: str, phone: str, plate: str):
    if not DB_MODELS_IMPORTED: return False
    try:
        now = datetime.utcnow()
        if plate:
            existing_courier = db.query(Courier).filter(Courier.plate == plate).first()
            if existing_courier:
                st.error(f"Error: Ya existe un mensajero con la placa '{plate}'.")
                return False
        new_courier = Courier(name=name, phone=phone, plate=plate, is_active=True, created_at=now, updated_at=now)
        db.add(new_courier)
        db.commit()
        st.success(f"Mensajero '{name}' añadido correctamente.")
        return True
    except IntegrityError:
        db.rollback()
        st.error(f"Error: Ya existe un mensajero con el nombre '{name}'.")
        return False
    except Exception as e:
        db.rollback()
        st.error(f"Error al añadir mensajero: {e}")
        return False

def update_courier(db: Session, courier_id: int, name: str, phone: str, plate: str, is_active: bool):
    if not DB_MODELS_IMPORTED: return False
    try:
        courier = db.query(Courier).filter(Courier.id == courier_id).first()
        if courier:
            if plate and plate != courier.plate:
                existing_courier = db.query(Courier).filter(Courier.plate == plate, Courier.id != courier_id).first()
                if existing_courier:
                    st.error(f"Error: Ya existe otro mensajero con la placa '{plate}'.")
                    return False
            courier.name = name
            courier.phone = phone
            courier.plate = plate
            courier.is_active = is_active
            courier.updated_at = datetime.utcnow()
            db.commit()
            st.success(f"Mensajero '{name}' (ID: {courier_id}) actualizado correctamente.")
            return True
        else:
            st.error(f"Error: Mensajero con ID {courier_id} no encontrado.")
            return False
    except IntegrityError:
        db.rollback()
        st.error(f"Error: Ya existe otro mensajero con el nombre '{name}'.")
        return False
    except Exception as e:
        db.rollback()
        st.error(f"Error al actualizar mensajero: {e}")
        return False

def delete_courier(db: Session, courier_id: int):
    if not DB_MODELS_IMPORTED: return False
    try:
        courier = db.query(Courier).filter(Courier.id == courier_id).first()
        if courier:
            if courier.packages or courier.routes:
                st.warning(f"No se puede eliminar el mensajero '{courier.name}' (ID: {courier_id}) porque tiene paquetes o rutas asociadas.")
                return False
            db.delete(courier)
            db.commit()
            st.success(f"Mensajero con ID {courier_id} eliminado correctamente.")
            return True
        else:
            st.error(f"Error: Mensajero con ID {courier_id} no encontrado.")
            return False
    except Exception as e:
        db.rollback()
        st.error(f"Error al eliminar mensajero: {e}")
        return False


# --- Interfaz de Usuario para el Módulo de Administración ---
def display_admin_module(db: Session):
    """Muestra la interfaz de Streamlit para la gestión de maestros."""
    if not DB_MODELS_IMPORTED:
        st.error("No se puede mostrar el módulo de administración debido a errores de importación de modelos.")
        return

    # --- TÍTULO PRINCIPAL DEL MÓDULO ---
    # Se elimina el sub-nombre y se usa solo "Administración"
    st.header("Administración")
    
    # --- PESTAÑAS DENTRO DEL MÓDULO ---
    # Se eliminan los sub-nombres de las pestañas
    tab1, tab2, tab3 = st.tabs([
        "Clientes B2B", "Productos", "Mensajeros"
    ])

    # --- Pestaña: Clientes B2B ---
    with tab1:
        st.subheader("Gestión de Clientes B2B")
        
        with st.expander("Añadir Nuevo Cliente B2B"):
            with st.form("add_client_form", clear_on_submit=True):
                client_name = st.text_input("Nombre del Cliente:")
                client_nit = st.text_input("NIT:")
                submitted = st.form_submit_button("Guardar Cliente")
                if submitted:
                    if client_name and client_nit:
                        add_client(db, client_name, client_nit)
                    else:
                        st.warning("Por favor, ingrese el nombre y NIT del cliente.")

        st.divider()
        
        st.subheader("Listado de Clientes B2B")
        clients = get_clients(db)
        if clients:
            df_clients = pd.DataFrame([{
                "ID": c.id, "Nombre": c.name, "NIT": c.nit,
                "Creado": format_datetime_utc(c.created_at), "Actualizado": format_datetime_utc(c.updated_at),
                "Acciones": None
            } for c in clients])
            
            st.dataframe(df_clients, use_container_width=True)

            st.subheader("Acciones sobre Clientes")
            client_to_edit_id = st.selectbox("Selecciona un cliente para editar o eliminar:", 
                                             options=[c.id for c in clients], 
                                             format_func=lambda x: f"{next(c.name for c in clients if c.id == x)} (ID: {x})",
                                             key="select_client_action")

            if client_to_edit_id:
                client_to_edit = db.query(ClientB2B).filter(ClientB2B.id == client_to_edit_id).first()
                if client_to_edit:
                    col1, col2 = st.columns(2)
                    with col1:
                        with st.expander(f"Editar Cliente: {client_to_edit.name}"):
                            with st.form(f"edit_client_form_{client_to_edit.id}", clear_on_submit=True):
                                edit_name = st.text_input("Nombre del Cliente:", value=client_to_edit.name)
                                edit_nit = st.text_input("NIT:", value=client_to_edit.nit)
                                submitted_edit = st.form_submit_button("Actualizar Cliente")
                                if submitted_edit:
                                    if edit_name and edit_nit:
                                        update_client(db, client_to_edit.id, edit_name, edit_nit)
                                    else:
                                        st.warning("Por favor, ingrese el nombre y NIT.")
                    with col2:
                        with st.expander(f"Eliminar Cliente: {client_to_edit.name}"):
                            st.warning(f"¿Está seguro que desea eliminar al cliente '{client_to_edit.name}' (ID: {client_to_edit.id})?")
                            if st.button("Confirmar Eliminación", key=f"confirm_delete_client_{client_to_edit.id}"):
                                delete_client(db, client_to_edit.id)
                                st.rerun() # Recargar para actualizar la lista
        else:
            st.info("No hay clientes B2B registrados aún.")

    # --- Pestaña: Productos ---
    with tab2:
        st.subheader("Gestión de Productos")
        
        # Obtener lista de clientes para el selectbox
        clients_for_product = get_clients(db)
        client_options = {c.}
