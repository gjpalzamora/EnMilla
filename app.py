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
                    st.success(f"✅ ¡Éxito! {len(df_final)} guías de {cliente_sel} ingresadas a bodega.")
                else:
                    st.error(f"❌ Columnas no coinciden. Se esperan: {cols_requeridas}")
            except Exception as e:
                st.error(f"Error técnico: {e}")

# --- MÓDULO: DESPACHO ---
elif rol == "Operativo" and menu == "2. Despacho (Salida a Ruta)":
    st.header("🛵 Terminal de Despacho")
    if st.session_state.db_inventario.empty:
        st.info("La bodega está vacía. Cargue una base primero.")
    else:
        m_sel = st.selectbox("Mensajero Responsable", st.session_state.db_mensajeros["Nombre"] if not st.session_state.db_mensajeros.empty else ["No hay mensajeros"])
        guia_pistola = st.text_input("💥 PISTOLEE LA GUÍA AQUÍ")
        
        if guia_pistola:
            # Buscar en el inventario cargado
            match = st.session_state.db_inventario[st.session_state.db_inventario["Guia"] == guia_pistola]
            
            if not match.empty:
                idx = match.index[0]
                info = match.loc[idx]
                
                # Registrar salida
                n_desp = pd.DataFrame([{
                    "Fecha_Salida": datetime.datetime.now().strftime("%H:%M"),
                    "Guia": guia_pistola,
                    "Mensajero": m_sel,
                    "Nombre Destinatario": info["Nombre Destinatario"],
                    "Estado": "En Ruta"
                }])
                st.session_state.db_despacho = pd.concat([st.session_state.db_despacho, n_desp], ignore_index=True)
                
                # Eliminar de bodega (se resta del inventario disponible)
                st.session_state.db_inventario = st.session_state.db_inventario.drop(idx)
                st.toast(f"✅ Guía {guia_pistola} despachada.")
            else:
                st.error("Guía no encontrada en el inventario de bodega.")

# --- ADMINISTRACIÓN ---
if rol == "Administrador" and password == "1234":
    if menu == "Clientes y Tarifas":
        with st.form("fc"):
            c = st.text_input("Nombre Cliente")
            p = st.text_input("Producto/Servicio")
            if st.form_submit_button("Registrar"):
                st.session_state.db_tarifario = pd.concat([st.session_state.db_tarifario, pd.DataFrame([{"Cliente": c, "Producto": p}])], ignore_index=True)
    elif menu == "Mensajeros":
        with st.form("fm"):
            n = st.text_input("Nombre")
            p = st.text_input("Placa")
            if st.form_submit_button("Vincular"):
                st.session_state.db_mensajeros = pd.concat([st.session_state.db_mensajeros, pd.DataFrame([{"Nombre": n, "Placa": p}])], ignore_index=True)

# --- MONITOR ---
st.markdown("---")
st.subheader("📋 Inventario Actual en Bodega")
st.dataframe(st.session_state.db_inventario, use_container_width=True)
