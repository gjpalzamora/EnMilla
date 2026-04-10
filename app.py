import streamlit as st
import pandas as pd
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="EnMilla - Logística 360", layout="wide")

# --- INICIALIZACIÓN DE BASES DE DATOS (STATE) ---
if 'db_mensajeros' not in st.session_state:
    st.session_state.db_mensajeros = pd.DataFrame(columns=["Nombre", "Placa", "Telefono"])

if 'db_tarifario' not in st.session_state:
    # Añadimos Venta y Pago (Destajo)
    st.session_state.db_tarifario = pd.DataFrame(columns=["Cliente", "Producto", "Tarifa_Venta", "Tarifa_Pago"])

if 'db_inventario' not in st.session_state:
    st.session_state.db_inventario = pd.DataFrame(columns=[
        "Fecha_Ingreso", "Guia", "Destinatario", "Direccion", "Cliente", "Producto", "Cobro_COD", "Estado"
    ])

if 'db_despacho' not in st.session_state:
    st.session_state.db_despacho = pd.DataFrame(columns=["Fecha_Salida", "Guia", "Mensajero", "Estado"])

# --- BARRA LATERAL (MENÚ) ---
with st.sidebar:
    st.title("📦 ENMILLA OPS")
    opcion = st.radio("Ir a:", [
        "1. Configuración Tarifas", 
        "2. Ingreso a Bodega (Escaneo)", 
        "3. Despacho a Ruta", 
        "4. Liquidación y Caja"
    ])

# --- MÓDULO 1: CONFIGURACIÓN DE TARIFAS ---
if opcion == "1. Configuración Tarifas":
    st.header("⚙️ Configuración de Clientes y Tarifas")
    
    with st.form("form_tarifas"):
        col1, col2 = st.columns(2)
        cliente = col1.text_input("Nombre del Cliente")
        producto = col2.text_input("Tipo de Producto (ej. Sobre, Caja)")
        t_venta = col1.number_input("Tarifa de Venta (Lo que cobras)", min_value=0)
        t_pago = col2.number_input("Tarifa de Pago (Destajo Mensajero)", min_value=0)
        
        if st.form_submit_button("Guardar Tarifa"):
            nueva_tarifa = {"Cliente": cliente, "Producto": producto, "Tarifa_Venta": t_venta, "Tarifa_Pago": t_pago}
            st.session_state.db_tarifario = pd.concat([st.session_state.db_tarifario, pd.DataFrame([nueva_tarifa])], ignore_index=True)
            st.success("Tarifa guardada")

    st.write("### Tarifario Actual")
    st.table(st.session_state.db_tarifario)

# --- MÓDULO 2: INGRESO A BODEGA (ESCANEADO) ---
elif opcion == "2. Ingreso a Bodega (Escaneo)":
    st.header("📥 Recepción de Paquetes")
    
    # Simulación de escáner
    guia_input = st.text_input("Escanee el código de barras / Ingrese Guía", key="scan")
    
    if guia_input:
        with st.expander("Detalles del Paquete Escaneado", expanded=True):
            col1, col2 = st.columns(2)
            cliente_sel = col1.selectbox("Cliente", st.session_state.db_tarifario["Cliente"].unique() if not st.session_state.db_tarifario.empty else ["Sin Clientes"])
            prod_sel = col2.selectbox("Producto", st.session_state.db_tarifario[st.session_state.db_tarifario["Cliente"] == cliente_sel]["Producto"] if not st.session_state.db_tarifario.empty else ["Sin Productos"])
            destinatario = col1.text_input("Nombre Destinatario")
            direccion = col2.text_input("Dirección de Entrega")
            cobro = st.number_input("Monto a Cobrar (COD) - 0 si es prepagado", min_value=0)
            
            if st.button("Confirmar Ingreso a Bodega"):
                nuevo_pqt = {
                    "Fecha_Ingreso": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "Guia": guia_input,
                    "Destinatario": destinatario,
                    "Direccion": direccion,
                    "Cliente": cliente_sel,
                    "Producto": prod_sel,
                    "Cobro_COD": cobro,
                    "Estado": "En Bodega"
                }
                st.session_state.db_inventario = pd.concat([st.session_state.db_inventario, pd.DataFrame([nuevo_pqt])], ignore_index=True)
                st.success(f"Guía {guia_input} ingresada correctamente")

    st.write("### Paquetes en Bodega")
    st.dataframe(st.session_state.db_inventario)

# --- MÓDULO 4: LIQUIDACIÓN Y CAJA (EL ALGORITMO) ---
elif opcion == "4. Liquidación y Caja":
    st.header("💰 Liquidación de Cuentas")
    
    if st.session_state.db_inventario.empty:
        st.warning("No hay datos para liquidar.")
    else:
        # Unimos inventario con tarifario para calcular dinero
        df_final = pd.merge(
            st.session_state.db_inventario, 
            st.session_state.db_tarifario, 
            on=["Cliente", "Producto"], 
            how="left"
        )
        
        col1, col2, col3 = st.columns(3)
        total_venta = df_final["Tarifa_Venta"].sum()
        total_pago = df_final["Tarifa_Pago"].sum()
        total_recaudo = df_final["Cobro_COD"].sum()
        
        col1.metric("A Facturar (Ventas)", f"${total_venta:,.0f}")
        col2.metric("A Pagar (Destajo)", f"${total_pago:,.0f}")
        col3.metric("Recaudos (COD)", f"${total_recaudo:,.0f}")
        
        st.write("### Detalle de Rentabilidad")
        df_final["Margen"] = df_final["Tarifa_Venta"] - df_final["Tarifa_Pago"]
        st.dataframe(df_final[["Guia", "Cliente", "Tarifa_Venta", "Tarifa_Pago", "Margen", "Cobro_COD"]])
        
        st.info(f"Ganancia Bruta Estimada: ${df_final['Margen'].sum():,.0f}")
