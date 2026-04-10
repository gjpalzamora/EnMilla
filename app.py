import streamlit as st
import pandas as pd
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA Y ESTILO CORPORATIVO ---
st.set_page_config(page_title="Enlaces - Soluciones Logísticas", layout="wide", page_icon="📦")

# Inyectamos CSS para usar los colores de tu logo (Azul Petróleo y Naranja)
st.markdown("""
    <style>
    .main { background-color: #f5f5f5; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; border-left: 5px solid #f37021; }
    div[data-testid="stSidebarNav"] { background-color: #006064; }
    h1, h2, h3 { color: #006064; }
    .stButton>button { background-color: #f37021; color: white; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

# --- INICIALIZACIÓN DE BASES DE DATOS (STATE) ---
if 'db_mensajeros' not in st.session_state:
    st.session_state.db_mensajeros = pd.DataFrame(columns=["Nombre", "Placa", "Telefono", "Zona"])

if 'db_tarifario' not in st.session_state:
    # Matriz Dual: Venta (lo que cobras) vs Pago (lo que pagas al mensajero)
    st.session_state.db_tarifario = pd.DataFrame(columns=["Cliente", "Producto", "Tarifa_Venta", "Tarifa_Pago"])

if 'db_inventario' not in st.session_state:
    st.session_state.db_inventario = pd.DataFrame(columns=[
        "Fecha_Ingreso", "Guia", "Destinatario", "Direccion", "Cliente", "Producto", "Cobro_COD", "Estado"
    ])

# --- BARRA LATERAL CON LOGO ---
with st.sidebar:
    # Aquí puedes poner la URL de tu imagen o el nombre del archivo si está en la misma carpeta
    st.image("https://imgur.com", use_column_width=True) # Reemplazar con el path de tu imagen
    st.markdown("<h2 style='text-align: center; color: white;'>ENLACES</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #f37021;'>Soluciones Logísticas</p>", unsafe_allow_html=True)
    st.markdown("---")
    opcion = st.radio("Módulos del Sistema:", [
        "1. Configuración de Tarifas", 
        "2. Recepción (Ingreso a Ciegas)", 
        "3. Carga Masiva y Conciliación",
        "4. Despacho y Operaciones",
        "5. Liquidación y Caja"
    ])
    st.markdown("---")
    st.caption("Powered by Enlaces Tech v1.6")

# --- MÓDULO 1: CONFIGURACIÓN DE TARIFAS ---
if opcion == "1. Configuración de Tarifas":
    st.header("⚙️ Matriz de Tarifas: Enlaces Logística")
    st.subheader("Define la rentabilidad por cliente y tipo de producto")
    
    with st.form("form_tarifas"):
        col1, col2 = st.columns(2)
        with col1:
            cliente = st.text_input("Nombre del Cliente Corporativo")
            t_venta = st.number_input("Tarifa de Venta (Cobro al Cliente)", min_value=0)
        with col2:
            producto = st.text_input("Tipo de Producto (ej: Sobre, Caja)")
            t_pago = st.number_input("Tarifa de Pago (Destajo Mensajero)", min_value=0)
        
        if st.form_submit_button("Guardar Configuración"):
            nueva_tarifa = {"Cliente": cliente, "Producto": producto, "Tarifa_Venta": t_venta, "Tarifa_Pago": t_pago}
            st.session_state.db_tarifario = pd.concat([st.session_state.db_tarifario, pd.DataFrame([nueva_tarifa])], ignore_index=True)
            st.success(f"Tarifa registrada para {cliente}")

    st.write("### Portafolio de Tarifas Actual")
    st.dataframe(st.session_state.db_tarifario, use_container_width=True)

# --- MÓDULO 2: RECEPCIÓN (INGRESO A CIEGAS) ---
elif opcion == "2. Recepción (Ingreso a Ciegas)":
    st.header("📥 Recepción Rápida (Inbound)")
    st.info("Escanee las guías físicas. El sistema las marcará como pendientes de datos.")
    
    guia_input = st.text_input("FOCO DE ESCÁNER (Escanee ahora):", key="scanner_input")
    
    if guia_input:
        if guia_input in st.session_state.db_inventario["Guia"].values:
            st.warning(f"La guía {guia_input} ya está en bodega.")
        else:
            nuevo_pqt = {
                "Fecha_Ingreso": datetime.now().strftime("%d/%m/%Y %H:%M"),
                "Guia": guia_input,
                "Destinatario": "PENDIENTE", 
                "Direccion": "PENDIENTE",
                "Cliente": "PENDIENTE",
                "Producto": "PENDIENTE",
                "Cobro_COD": 0,
                "Estado": "En Bodega (Físico)"
            }
            st.session_state.db_inventario = pd.concat([st.session_state.db_inventario, pd.DataFrame([nuevo_pqt])], ignore_index=True)
            st.success(f"✅ Guía {guia_input} recibida correctamente.")

    st.write("### Inventario en Bodega Enlaces")
    st.dataframe(st.session_state.db_inventario, use_container_width=True)

# --- MÓDULO 3: CARGA MASIVA Y CONCILIACIÓN ---
elif opcion == "3. Carga Masiva y Conciliación":
    st.header("📂 Carga de Datos de Clientes")
    archivo = st.file_uploader("Sube el archivo Excel/CSV enviado por el cliente", type=["xlsx", "csv"])
    
    if archivo:
        df_cliente = pd.read_excel(archivo) if archivo.name.endswith('xlsx') else pd.read_csv(archivo)
        st.write("Datos detectados en el archivo:")
        st.dataframe(df_cliente.head())
        
        if st.button("Ejecutar Conciliación de Guías"):
            for index, row in df_cliente.iterrows():
                guia_c = str(row['Guia'])
                if guia_c in st.session_state.db_inventario["Guia"].values:
                    idx = st.session_state.db_inventario[st.session_state.db_inventario["Guia"] == guia_c].index
                    st.session_state.db_inventario.at[idx, "Destinatario"] = row['Destinatario']
                    st.session_state.db_inventario.at[idx, "Direccion"] = row['Direccion']
                    st.session_state.db_inventario.at[idx, "Cliente"] = row['Cliente']
                    st.session_state.db_inventario.at[idx, "Producto"] = row['Producto']
                    st.session_state.db_inventario.at[idx, "Cobro_COD"] = row['Cobro_COD']
                    st.session_state.db_inventario.at[idx, "Estado"] = "Listo para Despacho"
            st.success("✅ Datos conciliados. Paquetes listos para salida.")

# --- MÓDULO 5: LIQUIDACIÓN Y CAJA (COLORES CORPORATIVOS) ---
elif opcion == "5. Liquidación y Caja":
    st.header("💰 Liquidación de Servicios - Enlaces")
    
    if st.session_state.db_inventario.empty:
        st.warning("Sin datos para liquidar.")
    else:
        df_liq = pd.merge(st.session_state.db_inventario, st.session_state.db_tarifario, on=["Cliente", "Producto"], how="left")
        
        c1, c2, c3 = st.columns(3)
        c1.metric("A FACTURAR (Ventas)", f"${df_liq['Tarifa_Venta'].sum():,.0f}")
        c2.metric("A PAGAR (Mensajeros)", f"${df_liq['Tarifa_Pago'].sum():,.0f}")
        c3.metric("RECAUDOS COD", f"${df_liq['Cobro_COD'].sum():,.0f}")
        
        st.write("### Reporte Detallado")
        st.dataframe(df_liq, use_container_width=True)
