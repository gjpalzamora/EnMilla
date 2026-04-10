# --- MÓDULO 2: INGRESO A BODEGA (ESCANEADO OPTIMIZADO) ---
elif opcion == "2. Ingreso a Bodega (Escaneo)":
    st.header("📥 Recepción de Paquetes")
    
    # Input principal para el escáner
    guia_input = st.text_input("Escanee el código de barras / Ingrese Guía", key="scan")
    
    if guia_input:
        # Buscamos si la guía ya existe en el inventario para evitar duplicados
        existe = not st.session_state.db_inventario[st.session_state.db_inventario["Guia"] == guia_input].empty
        
        if existe:
            st.warning(f"La guía {guia_input} ya fue ingresada previamente.")
        else:
            # REGISTRO AUTOMÁTICO: Solo con la guía, el resto queda pendiente
            nuevo_pqt = {
                "Fecha_Ingreso": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "Guia": guia_input,
                "Destinatario": "Pendiente",  # Se llenará con la carga masiva posterior
                "Direccion": "Pendiente",     # Se llenará con la carga masiva posterior
                "Cliente": "Por Identificar", # Se llenará con la carga masiva posterior
                "Producto": "Por Definir",    # Se llenará con la carga masiva posterior
                "Cobro_COD": 0,               # Se actualizará con la base de datos
                "Estado": "En Bodega (Sin Datos)"
            }
            
            # Insertar en el dataframe
            st.session_state.db_inventario = pd.concat([st.session_state.db_inventario, pd.DataFrame([nuevo_pqt])], ignore_index=True)
            
            st.success(f"✅ Guía {guia_input} registrada. Puede continuar escaneando.")
            
            # Limpiar el input para el siguiente escaneo (opcional según comportamiento del lector)
            # st.rerun() 

    st.write("### Paquetes en Bodega")
    # Resaltamos los que no tienen datos para que sepas qué falta conciliar
    st.dataframe(st.session_state.db_inventario.style.apply(lambda x: ['background-color: #ffcccc' if val == "Pendiente" else '' for val in x], axis=1))
