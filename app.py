# --- ACTUALIZACIÓN DEL PROCESO DE CONCILIACIÓN (MÓDULO 3.2) ---
# Copia este fragmento dentro del botón de 'Ejecutar Cruce de Datos'

if up and st.button("Ejecutar Cruce de Datos"):
    df_c = pd.read_excel(up) if up.name.endswith('xlsx') else pd.read_csv(up)
    
    # Normalizamos nombres de columnas para que coincidan con tu imagen
    # Usamos .strip() para evitar errores por espacios invisibles
    df_c.columns = [c.strip() for c in df_c.columns]
    
    for _, row in df_c.iterrows():
        g = str(row['Guia'])
        if g in st.session_state.db['inventario']['Guia'].values:
            idx = st.session_state.db['inventario'][st.session_state.db['inventario']['Guia'] == g].index
            
            # Mapeo exacto según tu imagen
            st.session_state.db['inventario'].at[idx, 'Cliente'] = row['Cliente']
            st.session_state.db['inventario'].at[idx, 'Producto'] = row['Producto']
            st.session_state.db['inventario'].at[idx, 'Destinatario'] = row['Destinatario']
            st.session_state.db['inventario'].at[idx, 'Direccion'] = row['Direccion']
            st.session_state.db['inventario'].at[idx, 'Ciudad'] = row['Ciudad']
            st.session_state.db['inventario'].at[idx, 'Cobro_COD'] = row['Cobro_COD']
            st.session_state.db['inventario'].at[idx, 'Telefono'] = row['Telefono']
            st.session_state.db['inventario'].at[idx, 'Contenido'] = row['Contenido']
            st.session_state.db['inventario'].at[idx, 'Valor_Declarado'] = row['Valor Declarado']
            st.session_state.db['inventario'].at[idx, 'Peso_Kg'] = row['Peso KG']
            
            st.session_state.db['inventario'].at[idx, 'Estado'] = "Listo para Despacho"
            
    st.success("✅ Conciliación Exitosa: Datos sincronizados con la estructura de Enlaces.")
