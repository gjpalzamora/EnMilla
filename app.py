import streamlit as st
import pandas as pd
from datetime import datetime
import base64
# Se asume que database.py tiene las funciones: obtener_datos y registrar_fila
from database import obtener_datos, registrar_fila

# --- 1. CONFIGURACIÓN Y UTILIDADES ---
st.set_page_config(page_title="EnMilla v2.0 - Gestión Integral", layout="wide")

def formatear_guia(texto):
    if not texto: return ""
    return str(texto).strip().split('.')[0]

def emitir_sonido(tipo):
    # Sonidos de confirmación y error
    sonido_ok = "https://www.soundjay.com/buttons/button-3.mp3"
    sonido_error = "https://www.soundjay.com/buttons/button-10.mp3"
    url = sonido_ok if tipo == "exito" else sonido_error
    audio_html = f'<audio autoplay style="display:none;"><source src="{url}" type="audio/mp3"></audio>'
    st.components.v1.html(audio_html, height=0)

# --- 2. NAVEGACIÓN ---
st.sidebar.title("📦 EnMilla v2.0")
st.sidebar.caption("Enlaces Soluciones Logísticas S.A.S.")
menu = st.sidebar.radio("Seleccione Módulo:", [
    "👥 Administración (Mensajeros/Clientes/Prod)", 
    "📥 Recepción (Ingreso Bodega)", 
    "🚚 Despacho (Cargue Mensajero)", 
    "📊 Trazabilidad y Reportes"
])

# --- 3. MÓDULOS DEL APLICATIVO ---

# MÓDULO 1: ADMINISTRACIÓN (Mensajeros, Clientes y Productos)
if menu == "👥 Administración (Mensajeros/Clientes/Prod)":
    st.header("⚙️ Configuración del Sistema")
    
    tab1, tab2 = st.tabs(["Registro de Mensajeros", "Registro de Clientes y Productos"])
    
    with tab1:
        st.subheader("Alta de Mensajeros y Flota")
        with st.form("form_mensajeros", clear_on_submit=True):
            col1, col2, col3 = st.columns(3)
            nombre_m = col1.text_input("Nombre Completo:")
            cedula_m = col2.text_input("Cédula:")
            placa_m = col3.text_input("Placa del Vehículo:")
            
            if st.form_submit_button("Registrar Mensajero"):
                if nombre_m and placa_m:
                    registrar_fila("Maestro_Mensajeros", [nombre_m, cedula_m, placa_m.upper()])
                    st.success(f"✅ Mensajero {nombre_m} vinculado a placa {placa_m.upper()}")
                else:
                    st.error("Nombre y Placa son obligatorios.")

    with tab2:
        st.subheader("Estructura de Clientes y sus Productos")
        st.info("Un cliente puede tener múltiples productos (ej. Integra -> Express, Integra -> Estandar)")
        with st.form("form_clientes", clear_on_submit=True):
            col1, col2 = st.columns(2)
            cliente_nombre = col1.text_input("Nombre del Cliente (ej. Integra):")
            producto_nombre = col2.text_input("Nombre del Producto (ej. Paquete Estandar):")
            
            if st.form_submit_button("Guardar Cliente/Producto"):
                if cliente_nombre and producto_nombre:
                    # Guardamos la relación Cliente-Producto
                    registrar_fila("Clientes_Productos", [cliente_nombre, producto_nombre])
                    st.success(f"✅ Vinculado: {producto_nombre} al cliente {cliente_nombre}")
                else:
                    st.error("Debe ingresar tanto el Cliente como el Producto.")

# MÓDULO 2: RECEPCIÓN (INGRESO CON FILTRO DE PRODUCTO)
elif menu == "📥 Recepción (Ingreso Bodega)":
    st.header("📥 Recepción Automatizada")
    
    # Carga de datos de configuración
    c_df = pd.DataFrame(obtener_datos("Clientes_Productos"))
    
    if not c_df.empty:
        col_c, col_p = st.columns(2)
        cliente_opt = col_c.selectbox("Seleccione Cliente:", c_df['Cliente'].unique())
        # Filtrado dinámico: Solo muestra productos del cliente seleccionado
        productos_filtrados = c_df[c_df['Cliente'] == cliente_opt]['Producto'].unique()
        prod_opt = col_p.selectbox("Seleccione Producto:", productos_filtrados)
    else:
        st.warning("⚠️ Primero debe configurar Clientes y Productos en el módulo de Administración.")
        st.stop()

    def procesar_ingreso():
        guia_raw = st.session_state.input_ingreso
        if guia_raw:
            guia_final = formatear_guia(guia_raw)
            ahora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            # Forzamos texto con comilla para evitar notación científica en guías largas
            registrar_fila("Inventario_Bodega", [f"'{guia_final}", cliente_opt, prod_opt, ahora])
            emitir_sonido("exito")
            st.toast(f"✅ Ingresada: {guia_final}")
            st.session_state.input_ingreso = ""

    st.text_input("ESCANEE GUÍA PARA INGRESO:", key="input_ingreso", on_change=procesar_ingreso)

# MÓDULO 3: DESPACHO (EL ESCUDO DE SEGURIDAD)
elif menu == "🚚 Despacho (Cargue Mensajero)":
    st.header("🚚 Cargue a Mensajeros")
    
    m_df = pd.DataFrame(obtener_datos("Maestro_Mensajeros"))
    if not m_df.empty:
        mensajero_sel = st.selectbox("Seleccione Mensajero Responsable:", m_df['Nombre'])
        placa_vinculada = m_df[m_df['Nombre'] == mensajero_sel]['Placa'].values[0]
        st.info(f"Vehículo vinculado: **{placa_vinculada}**")
    else:
        st.warning("⚠️ No hay mensajeros registrados en el sistema.")
        st.stop()

    def procesar_despacho():
        guia_raw = st.session_state.input_despacho
        if guia_raw:
            guia_final = formatear_guia(guia_raw)
            
            # --- EL ESCUDO: VALIDACIÓN DE INVENTARIO ---
            inv_bodega = pd.DataFrame(obtener_datos("Inventario_Bodega"))
            # Limpiamos prefijos para la comparación técnica
            guias_en_bodega = inv_bodega['Guia'].astype(str).str.replace("'", "").values if not inv_bodega.empty else []

            if guia_final in guias_en_bodega:
                ahora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                # Registro con trazabilidad completa
                registrar_fila("Despachos", [f"'{guia_final}", mensajero_sel, placa_vinculada, ahora, "EN REPARTO"])
                emitir_sonido("exito")
                st.toast(f"🚀 Despacho Autorizado: {guia_final}")
            else:
                emitir_sonido("error")
                st.error(f"❌ ERROR: La guía {guia_final} NO registra ingreso físico previo en bodega.")
            
            st.session_state.input_despacho = ""

    st.text_input("PISTOLEE PARA DESPACHO:", key="input_despacho", on_change=procesar_despacho)

# MÓDULO 4: TRAZABILIDAD
elif menu == "📊 Trazabilidad y Reportes":
    st.header("📊 Trazabilidad de Operación")
    tab_inv, tab_desp = st.tabs(["Inventario en Bodega", "Historial de Despachos"])
    
    with tab_inv:
        st.subheader("Paquetes actualmente en sede Barrios Unidos")
        df_inv = pd.DataFrame(obtener_datos("Inventario_Bodega"))
        st.dataframe(df_inv, use_container_width=True)

    with tab_desp:
        st.subheader("Registro de Salidas a Ruta")
        df_desp = pd.DataFrame(obtener_datos("Despachos"))
        st.dataframe(df_desp, use_container_width=True)
