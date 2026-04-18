# --- REEMPLAZA EL MÓDULO 2 EN TU CÓDIGO CON ESTA VERSIÓN ---

elif modulo == "2. Operaciones (Recibir)":
    st.header("Entrada de Mercancía Automática")
    
    db = SessionLocal()
    clientes = db.query(ClientB2B).all()
    
    if not clientes:
        st.warning("⚠️ Primero debe crear un Cliente B2B en el Módulo de Administración.")
    else:
        # Fila superior: Selección de contexto
        col1, col2 = st.columns(2)
        with col1:
            c_nom = st.selectbox("Seleccione Cliente B2B", [c.name for c in clientes])
            cliente_obj = db.query(ClientB2B).filter(ClientB2B.name == c_nom).first()
        with col2:
            prods_cliente = db.query(Product).filter(Product.client_id == cliente_obj.id).all()
            p_nom = st.selectbox("Seleccione Producto", [p.name for p in prods_cliente] if prods_cliente else ["Sin productos"])

        st.divider()
        
        # Campo de entrada automática
        # El parámetro on_change permite que apenas el escáner mande la señal, se ejecute la lógica
        if "input_guia" not in st.session_state:
            st.session_state.input_guia = ""

        def procesar_guia():
            guia = st.session_state.guia_escaneada.strip()
            if guia:
                db_op = SessionLocal()
                # Verificar si ya existe
                existe = db_op.query(Package).filter(Package.tracking_number == guia).first()
                if not existe:
                    try:
                        # Crear paquete con cliente y producto ya vinculados
                        nuevo_pkg = Package(
                            tracking_number=guia,
                            client_id=cliente_obj.id,
                            status="En Bodega"
                        )
                        db_op.add(nuevo_pkg)
                        db_op.commit()
                        
                        # Registrar el movimiento inicial
                        mov = Movement(
                            package_id=nuevo_pkg.id,
                            location="Bodega Barrios Unidos",
                            description=f"Ingreso automático - Cliente: {c_nom} - Prod: {p_nom}"
                        )
                        db_op.add(mov)
                        db_op.commit()
                        st.toast(f"✅ Guía {guia} recibida correctamente", icon="📦")
                    except Exception as e:
                        db_op.rollback()
                        st.error(f"Error al ingresar: {e}")
                else:
                    st.warning(f"⚠️ La guía {guia} ya fue ingresada anteriormente.")
                db_op.close()
                # Limpiar el campo para la siguiente lectura
                st.session_state.guia_escaneada = ""

        st.subheader("Escanee ahora")
        st.text_input(
            "Enfoque el escáner aquí y procese las guías:",
            key="guia_escaneada",
            on_change=procesar_guia,
            help="El sistema procesará la guía automáticamente al terminar de escanear."
        )
        
        st.info("💡 Consejo: El operario solo debe seleccionar el cliente y producto una vez por lote de carga.")
    
    db.close()
