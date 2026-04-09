import streamlit as st
import pandas as pd
import datetime
import random

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Enmilla - Enlaces Logística", layout="wide")

# --- INICIALIZACIÓN DE BASES DE DATOS ---
if 'db_mensajeros' not in st.session_state:
    st.session_state.db_mensajeros = pd.DataFrame(columns=["Nombre", "Placa"])
if 'db_tarifario' not in st.session_state:
    st.session_state.db_tarifario = pd.DataFrame(columns=["Cliente", "Producto"])
if 'db_inventario' not in st.session_state:
    st.session_state.db_inventario = pd.DataFrame(columns=[
        "Fecha_Ingreso", "Guia", "Nombre Destinatario", "Direcion Destino", "Telefono", "Cliente", "Producto", "Estado"
    ])
if 'db_despacho' not in st.session_state:
    st.session_state.db_despacho = pd.DataFrame(columns=["Fecha_Salida", "Guia", "Mensajero", "Nombre Destinatario", "Estado"])

# --- BARRA LATERAL ---
with st.sidebar:
    st.title("📦 ENMILLA OPS")
    st.markdown("**Enlaces Soluciones Logística SAS**")
    st.caption("NIT: 901.939.284-4")
    st.markdown("---")
    rol = st.radio("Acceso", ["Operativo", "Administrador"])
    
    if rol == "Administrador":
        password = st.text_input("Clave Admin", type="password")
        menu = st.selectbox("Maestros", ["Clientes y Tarifas", "Mensajeros"])
    else:
        menu = st.selectbox("Operación", ["1. Ingreso a Bodega (Cargar Base)", "2. Despacho (Salida a Ruta)"])

# --- ENCABEZADO ---
st.markdown(f"""
    <div style="background-color:#003366;padding:15px;border-radius:10px;text-align:center;border-bottom: 5px solid #f1c40f;">
        <h1 style="color:white;margin:0;">SISTEMA LOGÍSTICO ENMILLA</h1>
        <p style="color:white;margin:5px;">Propiedad de: Enlaces Soluciones Logística SAS | Bogotá D.C.</p>
    </div><br>
    """, unsafe_allow_html=True)

# --- MÓDULO: INGRESO A BODEGA ---
if rol == "Operativo" and menu == "1. Ingreso a Bodega (Cargar Base)":
    st.header("📥 Recepción y Carga de Base")
    
    if st.session_state.db_tarifario.empty:
        st.warning("⚠️ Primero el Administrador debe crear un Cliente y Producto.")
    else:
        c1, c2 = st.columns(2)
        cliente_sel = c1.selectbox("¿De qué cliente es la mercancía?", st.session_state.db_tarifario["Cliente"].unique())
        prods = st.session_state.db_tarifario[st.session_state.db_tarifario["Cliente"] == cliente_sel]["Producto"]
        producto_sel = c2.selectbox("Seleccione el Producto", prods)

        tipo_op = st.radio("Tipo de Operación", ["Cliente Externo (Ya trae Guía)", "Mensajería Propia (Generar Guía Interna)"])
        
        archivo = st.file_uploader("Subir Excel del Cliente", type=['xlsx', 'xls', 'csv'])
        
        if archivo and st.button("🚀 Procesar e Ingresar a Bodega"):
            try:
                # Lectura flexible para Excel o CSV
                if archivo.name.endswith(('.xlsx', '.xls')):
                    df_excel = pd.read_excel(archivo, engine='openpyxl')
                else:
                    df_excel = pd.read_csv(archivo)
                
                # Limpiar nombres de columnas (quitar espacios)
                df_excel.columns = df_excel.columns.str.strip()
                
                # Columnas que detectamos en tu archivo
                cols_requeridas = ["Nombre Destinatario", "Direcion Destino", "Telefono"]
                
                if all(col in df_excel.columns for col in cols_requeridas):
                    df_excel['Fecha_Ingreso'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                    df_excel['Cliente'] = cliente_sel
                    df_excel['Producto'] = producto_sel
                    df_excel['Estado'] = "En Bodega"
                    
                    if tipo_op == "Mensajería Propia (Generar Guía Interna)":
                        df_excel['Guia'] = [f"ENM-{random.randint(100000, 999999)}" for _ in range(len(df_excel))]
                    else:
                        if 'Guia' not in df_excel.columns:
                            st.error("❌ El archivo no tiene la columna 'Guia' necesaria para este modo.")
                            st.stop()
                    
                    # Consolidar solo las columnas necesarias
                    columnas_finales = ["Fecha_Ingreso", "Guia", "Nombre Destinatario", "Direcion Destino", "Telefono", "Cliente", "Producto", "Estado"]
                    df_final = df_excel[columnas_finales]
                    
                    st.session_state.db_inventario = pd.concat([st.session_state.db_inventario, df_final], ignore_index=True)
