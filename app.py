import streamlit as st
import pandas as pd
from datetime import datetime

# --- CONFIGURACIÓN DE SEGURIDAD ---
st.set_page_config(page_title="EnMilla v2.0", layout="wide")

# Función para limpiar y formatear guías (Evita notación científica)
def formatear_guia(texto):
    if not texto: return ""
    return str(texto).strip().split('.')[0] # Elimina decimales y espacios

st.title("📦 Sistema EnMilla v2.0")
st.sidebar.header("Control de Operaciones")

menu = st.sidebar.radio("Seleccione Módulo:", [
    "1. Configuración (Clientes/Prod)", 
    "2. Recepción en Bodega", 
    "3. Cargue a Mensajeros", 
    "4. Trazabilidad y Reportes"
])

# --- MÓDULO 1: CONFIGURACIÓN ---
if menu == "1. Configuración (Clientes/Prod)":
    st.header("🏢 Gestión de Clientes y Productos")
    with st.form("form_clientes"):
        nuevo_cliente = st.text_input("Nombre del Cliente (ej. Integra)")
        nuevo_producto = st.text_input("Nombre del Producto (ej. Paquete Estandar)")
        if st.form_submit_button("Registrar Producto"):
            # Lógica para guardar en pestaña 'Clientes_Productos'
            st.success(f"Producto '{nuevo_producto}' asignado a {nuevo_cliente}")

# --- MÓDULO 2: RECEPCIÓN EN BODEGA ---
elif menu == "2. Recepción en Bodega":
    st.header("📥 Ingreso de Mercancía")
    
    # Cargar clientes para el selectbox
    cliente_sel = st.selectbox("Seleccione Cliente:", ["Integra", "Temu", "Shein"])
    producto_sel = st.selectbox("Seleccione Producto:", ["Estandar", "Express", "Devolución"])

    with st.form("form_ingreso", clear_on_submit=True):
        # El input de guía se trata siempre como texto
        guia_raw = st.text_input("ESCANEAR GUÍA:", key="input_ingreso")
        if st.form_submit_button("Confirmar Ingreso"):
            guia_limpia = formatear_guia(guia_raw)
            ahora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            # REGISTRO: Aquí se envía a la pestaña 'Inventario_Bodega'
            st.success(f"✅ Guía {guia_limpia} ingresada correctamente a {cliente_sel}")

# --- MÓDULO 3: CARGUE A MENSAJEROS (EL ESCUDO) ---
elif menu == "3. Cargue a Mensajeros":
    st.header("🚚 Despacho y Asignación")
    
    # Selección de Mensajero y Placa Automática
    mensajeros_data = {"Nombre": ["Juan Perez", "Carlos Ruiz"], "Placa": ["XYZ-123", "ABC-456"]}
    df_m = pd.DataFrame(mensajeros_data)
    
    m_sel = st.selectbox("Mensajero:", df_m['Nombre'])
    placa_auto = df_m[df_m['Nombre'] == m_sel]['Placa'].values[0]
    st.warning(f"Vehículo Asignado: {placa_auto}")

    guia_despacho_raw = st.text_input("ESCANEAR PARA DESPACHO:")
    
    if st.button("Validar y Despachar"):
        guia_despacho = formatear_guia(guia_despacho_raw)
        
        # --- LÓGICA DE ESCUDO ---
        # 1. Buscar en 'Inventario_Bodega'
        # if guia_despacho in inventario_fisico:
        if guia_despacho != "": # Simulación de validación
            st.success(f"🚀 Despacho Autorizado: Guía {guia_despacho} -> {m_sel} ({placa_auto})")
            # Registrar en pestaña 'Despachos' y actualizar estado
        else:
            st.error("❌ ERROR CRÍTICO: El paquete no registra ingreso previo en bodega.")

# --- MÓDULO 4: TRAZABILIDAD ---
elif menu == "4. Trazabilidad y Reportes":
    st.header("📊 Trazabilidad Total")
    # Cruce de tablas para mostrar la "Vida del Paquete"
    st.info("Aquí podrá ver quién recibió el paquete, a qué producto pertenece y qué mensajero lo lleva.")
