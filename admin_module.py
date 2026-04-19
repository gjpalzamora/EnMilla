import streamlit as st
import pandas as pd
from sqlalchemy.orm import Session
from db_models import ClientB2B, Courier, Product, Package

def display_admin_module(db: Session):
    st.header("⚙️ Panel de Administración")
    tabs = st.tabs(["Mensajeros", "Clientes B2B", "📦 Carga Masiva"])
    
    with tabs[0]:
        st.subheader("Registro de Mensajeros")
        with st.form("form_courier", clear_on_submit=True):
            name = st.text_input("Nombre Completo")
            doc_id = st.text_input("Cédula")
            phone = st.text_input("Teléfono")
            if st.form_submit_button("Registrar"):
                if name and doc_id:
                    try:
                        db.add(Courier(name=name, document_id=doc_id, phone=phone))
                        db.commit()
                        st.success(f"Mensajero {name} registrado.")
                    except:
                        db.rollback()
                        st.error("Error: Cédula duplicada.")

    with tabs[1]:
        st.subheader("Clientes B2B")
        with st.form("form_client", clear_on_submit=True):
            c_name = st.text_input("Nombre Empresa")
            nit = st.text_input("NIT")
            if st.form_submit_button("Guardar"):
                db.add(ClientB2B(name=c_name, nit=nit))
                db.commit()
                st.success("Cliente creado.")

    with tabs[2]:
        st.subheader("Importar Guías desde Excel")
        clients = db.query(ClientB2B).all()
        if not clients:
            st.warning("Cree un cliente primero.")
        else:
            client_map = {c.name: c.id for c in clients}
            selected_client = st.selectbox("Asignar carga a:", options=list(client_map.keys()))
            
            uploaded_file = st.file_uploader("Subir Excel (.xlsx)", type=["xlsx"])
            if uploaded_file:
                df = pd.read_excel(uploaded_file)
                st.write("Vista previa de los datos:")
                st.dataframe(df.head(5))
                
                # Mapeo de columnas (puedes ajustar los nombres según tu archivo real)
                col_guia = st.selectbox("Columna de Guía/Tracking:", df.columns)
                col_nombre = st.selectbox("Columna de Destinatario:", df.columns)
                
                if st.button("🚀 Procesar e Importar"):
                    count = 0
                    errors = 0
                    for index, row in df.iterrows():
                        try:
                            # Evitamos duplicados
                            exists = db.query(Package).filter(Package.tracking_number == str(row[col_guia])).first()
                            if not exists:
                                new_pkg = Package(
                                    tracking_number=str(row[col_guia]),
                                    recipient_name=str(row[col_nombre]),
                                    client_id=client_map[selected_client],
                                    status="PRE-CARGADO"
                                )
                                db.add(new_pkg)
                                count += 1
                        except:
                            errors += 1
                    db.commit()
                    st.success(f"Importación terminada: {count} guías nuevas cargadas. {errors} errores.")
