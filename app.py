import streamlit as st
import pandas as pd
import datetime
import random

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Enmilla - Enlaces Logística", layout="wide")

# --- INICIALIZACIÓN DE BASES DE DATOS ---
if 'db_mensajeros' not in st.session_state:
    st.session_state.db_mensajeros = pd.DataFrame(columns=["ID", "Nombre", "Placa"])
if 'db_tarifario' not in st.session_state:
    st.session_state.db_tarifario = pd.DataFrame(columns=["Cliente", "Producto", "Cobro_Cli", "Pago_Mens"])
if 'db_inventario' not in st.session_state:
    st.session_state.db_inventario = pd.DataFrame(columns=["Fecha_Ingreso", "Guia", "Cliente", "Producto", "Destinatario", "Estado"])
if 'db_despacho' not in st.session_state:
    st.session_state.db_despacho = pd.DataFrame(columns=["Fecha_Salida", "Guia", "Mensajero", "Cliente", "Estado"])

# --- BARRA LATERAL ---
with st.sidebar:
    st.title("📦 ENMILLA OPS")
    st.markdown("**Enlaces Soluciones Logística SAS**")
    st.caption("NIT: 901.939.284-4")
    st.markdown("---")
    rol = st.radio("Acceso", ["Operativo", "Administrador"])
    
    if rol == "Administrador":
        password = st.text_input("Contraseña Admin", type="password")
        menu = st.selectbox("Maestros", ["Clientes y Tarifas", "Mensajeros"])
    else:
        menu = st.selectbox("Operación", ["Ingreso a Bodega", "Despacho a Ruta"])

# --- ENCABEZADO ---
st.markdown(f"""
    <div style="background-color:#003366;padding:15px;border-radius:10px;text-align:center;border-bottom: 5px solid #f1c40f;">
        <h1 style="color:white;margin:0;">SISTEMA LOGÍSTICO ENMILLA</h1>
        <p style="color:white;margin:5px;">Operación: Bogotá D.C. | Barrios Unidos</p>
    </div><br>
    """, unsafe_allow_html=True)

# --- MÓDULO: INGRESO A BODEGA ---
if rol == "Operativo" and menu == "Ingreso a Bodega":
    st.header("📥 Recepción de Mercancía")
    
    # 1. Identificación del Cliente y Producto
    col1, col2 = st.columns(2)
    if not st.session_state.db_tarifario.empty:
        lista_clientes = st.session_state.db_tarifario["Cliente"].unique()
        cliente_sel = col1.selectbox("¿De qué cliente es la mercancía?", lista_clientes)
        lista_prods = st.session_state.db_tarifario[st.session_state.db_tarifario["Cliente"] == cliente_sel]["Producto"]
        producto_sel = col2.selectbox("Seleccione el Producto/Servicio", lista_prods)
    else:
        st.warning("⚠️ El Administrador debe configurar Clientes y Productos primero.")
        st.stop()

    tipo_cliente = st.radio("Tipo de Operación", ["Mensajería Propia (Generar Guías)", "Cliente Externo (Guías ya impresas)"])
    
    st.markdown("---")
    
    # 2. Carga de Base de Datos
    archivo = st.file_uploader(f"Subir base de datos de {cliente_sel}", type=['xlsx', 'csv'])
    
    if archivo and st.button("Procesar Ingreso a Bodega"):
        try:
            df_carga = pd.read_excel(archivo) if archivo.name.endswith('.xlsx') else pd.read_csv(archivo)
            
            # Limpieza y preparación
            df_carga['Fecha_Ingreso'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            df_carga['Cliente'] = cliente_sel
            df_carga['Producto'] = producto_sel
            df_carga['Estado'] = "En Bodega"
            
            if tipo_cliente == "Mensajería Propia (Generar Guías)":
                # Generamos consecutivo interno para cada fila
                df_carga['
