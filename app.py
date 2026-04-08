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
                df_carga['Guia'] = [f"ENM-{random.randint(100000, 999999)}" for _ in range(len(df_carga))]
                st.info("✅ Base cargada. Se han generado guías internas Enmilla.")
            else:
                # El archivo debe tener una columna 'Guia'
                if 'Guia' not in df_carga.columns:
                    st.error("❌ El archivo debe tener una columna llamada 'Guia' con el número de etiqueta del cliente.")
                    st.stop()
            
            # Guardar en el inventario global
            st.session_state.db_inventario = pd.concat([st.session_state.db_inventario, df_carga], ignore_index=True)
            st.success(f"Éxito: {len(df_carga)} registros ingresados a bodega.")
            st.dataframe(df_carga.head())
            
        except Exception as e:
            st.error(f"Error al procesar el archivo: {e}")

# --- MÓDULO: DESPACHO ---
elif rol == "Operativo" and menu == "Despacho a Ruta":
    st.header("🛵 Terminal de Salida")
    if st.session_state.db_inventario.empty:
        st.info("La bodega está vacía. Realice un ingreso de mercancía.")
    else:
        with st.form("cargue"):
            m_sel = st.selectbox("Mensajero Responsable", st.session_state.db_mensajeros["Nombre"] if not st.session_state.db_mensajeros.empty else ["Cree mensajeros"])
            guia_pistola = st.text_input("Pistolee la guía")
            if st.form_submit_button("Cargar a Vehículo"):
                if guia_pistola in st.session_state.db_inventario["Guia"].values:
                    # Movimiento de inventario a despacho
                    item = st.session_state.db_inventario[st.session_state.db_inventario["Guia"] == guia_pistola].iloc[0]
                    n_d = pd.DataFrame([{"Fecha_Salida": datetime.datetime.now().strftime("%H:%M"), "Guia": guia_pistola, "Mensajero": m_sel, "Cliente": item["Cliente"], "Estado": "En Ruta"}])
                    st.session_state.db_despacho = pd.concat([st.session_state.db_despacho, n_d], ignore_index=True)
                    st.session_state.db_inventario = st.session_state.db_inventario[st.session_state.db_inventario["Guia"] != guia_pistola]
                    st.success(f"Guía {guia_pistola} despachada.")
                else:
                    st.error("Guía no encontrada en bodega.")

# --- MÓDULOS DE ADMINISTRADOR ---
if rol == "Administrador" and password == "1234":
    if menu == "Clientes y Tarifas":
        st.subheader("Configuración de Tarifario")
        with st.form("f_tarifas", clear_on_submit=True):
            c = st.text_input("Nombre Cliente")
            p = st.text_input("Producto (Ej: Sobre, Caja, Express)")
            if st.form_submit_button("Guardar"):
                st.session_state.db_tarifario = pd.concat([st.session_state.db_tarifario, pd.DataFrame([{"Cliente": c, "Producto": p}])], ignore_index=True)
    
    elif menu == "Mensajeros":
        st.subheader("Maestro de Mensajeros")
        with st.form("f_m", clear_on_submit=True):
            n = st.text_input("Nombre")
            p = st.text_input("Placa")
            if st.form_submit_button("Vincular"):
                st.session_state.db_mensajeros = pd.concat([st.session_state.db_mensajeros, pd.DataFrame([{"Nombre": n, "Placa": p}])], ignore_index=True)

# --- VISUALIZACIÓN DE TABLAS ---
st.markdown("---")
st.subheader("📊 Control de Inventario en Tiempo Real")
st.write("**Mercancía lista en bodega:**")
st.dataframe(st.session_state.db_inventario, use_container_width=True)
