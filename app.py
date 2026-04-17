elif menu == "Despacho":
    st.header("🚚 Gestión de Despacho y Entrega")
    
    # Buscador de paquete para despachar
    t_num = st.text_input("Ingrese Tracking Number para gestionar")
    if t_num:
        pkg = db.query(Package).filter(Package.tracking_number == t_num).first()
        if pkg:
            st.info(f"Estado Actual: {pkg.status}")
            
            # Selección de Mensajero y Nuevo Estado [cite: 125, 127]
            couriers = db.query(Courier).filter(Courier.is_active == True).all()
            c_options = {c.name: c.id for c in couriers}
            sel_courier = st.selectbox("Asignar Mensajero", options=list(c_options.keys()))
            
            nuevo_estado = st.selectbox("Cambiar Estado a:", ["En Tránsito", "Entregado", "Incidencia"])
            
            if st.button("Actualizar Estado"):
                # RF3.3.2. Marcar como entregado [cite: 129, 131]
                if nuevo_estado == "Entregado":
                    pkg.is_delivered = True
                    pkg.status = "Entregado"
                else:
                    pkg.status = nuevo_estado
                
                # Registrar el movimiento [cite: 126, 133]
                nuevo_mov = Movement(
                    package_id=pkg.id,
                    location="Punto de Entrega",
                    description=f"Estado cambiado a {nuevo_estado} con mensajero {sel_courier}"
                )
                db.add(nuevo_mov)
                db.commit()
                st.success(f"Estado actualizado a {nuevo_estado}")
                
                # Generación de POD si es entregado [cite: 138]
                if nuevo_estado == "Entregado":
                    pdf_data = generar_pod_pdf(pkg, sel_courier)
                    st.download_button(
                        label="📥 Descargar Comprobante POD (PDF)",
                        data=pdf_data,
                        file_name=f"POD_{pkg.tracking_number}.pdf",
                        mime="application/pdf"
                    )
        else:
            st.error("Paquete no encontrado.")
