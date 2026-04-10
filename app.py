import streamlit as st
import pandas as pd
from datetime import datetime

# --- 0. CONFIGURACIÓN E IDENTIDAD CORPORATIVA ---
st.set_page_config(page_title="Enlaces - Soluciones Logísticas", layout="wide", page_icon="📦")

# Estilo Enlaces
st.markdown("""
    <style>
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; border-left: 5px solid #f37021; box-shadow: 2px 2px 5px rgba(0,0,0,0.05); }
    h1, h2, h3 { color: #006064; }
    .stButton>button { background-color: #f37021; color: white; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- INICIALIZACIÓN DE BASES DE DATOS ---
if 'db' not in st.session_state:
    st.session_state.db = {
        'clientes': pd.DataFrame(columns=["NIT", "Nombre"]),
        'tarifario': pd.DataFrame(columns=["Cliente", "Producto", "Tarifa_Venta", "Tarifa_Pago"]),
        'mensajeros': pd.DataFrame(columns=["Nombre", "Placa"]),
        'inventario': pd.DataFrame(columns=[
            "Guia", "Fecha_In", "Cliente", "Producto", "Destinatario", "Direccion", 
            "Ciudad", "Cobro_COD", "Telefono", "Contenido", "Valor Declarado", "Peso KG", "Estado", "Mensajero"
        ])
    }

# --- BARRA LATERAL (MENÚ DE 8 MÓDULOS) ---
with st.sidebar:
    st.markdown("<h1 style='text-align: center; color: white;'>ENLACES</h1>", unsafe_allow_html=True)
    st.markdown("---")
    menu = st.selectbox("MENÚ PRINCIPAL", [
        "1. Administración",
        "2. Admisión e Ingesta",
        "3. Recepción y Bodega (WMS)",
        "4. Operaciones y Despacho",
        "5. App Móvil (Operación)",
        "6. Liquidación y Caja",
        "7. Logística Inversa",
        "8. Portal de Autogestión"
    ])
    st.markdown("---")
    st.caption("v2.5 - Enlaces Soluciones Logísticas")

# --- LÓGICA DE MÓDULOS (IF / ELIF ESTRUCTURADO) ---

if menu == "1. Administración":
    st.header("⚙️ Configuración Administrativa")
    with st.expander("Registrar Clientes y Tarifas"):
        with st.form("f_adm"):
            c1, c2 = st.columns(2)
            cli = c1.text_input("Cliente")
            prod = c2.selectbox("Producto", ["Sobre", "Paquete", "Carga"])
            t_v = c1.number_input("Tarifa Venta", min_value=0)
            t_p = c2.number_input("Tarifa Pago", min_value=0)
            if st.form_submit_button("Guardar Configuración"):
                new_t = {"Cliente": cli, "Producto": prod, "Tarifa_Venta": t_v, "Tarifa_Pago": t_p}
                st.session_state.db['tarifario'] = pd.concat([st.session_state.db['tarifario'], pd.DataFrame([new_t])], ignore_index=True)
                st.success("Guardado.")

elif menu == "3. Recepción y Bodega (WMS)":
    st.header("📦 Gestión de Bodega")
    
    st.subheader("3.1 Ingreso a Ciegas")
    g_scan = st.text_input("ESCÁNER: Leer Guía", placeholder="Escanea aquí...")
    if g_scan:
        if g_scan not in st.session_state.db['inventario']['Guia'].values:
            nuevo = {"Guia": g_scan, "Fecha_In": datetime.now(), "Estado": "En Bodega (Físico)"}
            st.session_state.db['inventario'] = pd.concat([st.session_state.db['inventario'], pd.DataFrame([nuevo])], ignore_index=True)
            st.success(f"Guía {g_scan} registrada físicamente.")
        else:
            st.warning("Esa guía ya fue escaneada.")

    st.markdown("---")
    st.subheader("3.2 Conciliador Masivo")
    up = st.file_uploader("1. Subir Excel del Cliente", type=["xlsx", "csv"])
    
    if up is not None:
        st.info("Archivo listo. Presione el botón para procesar.")
        if st.button("🚀 TRANSMITIR Y CONCILIAR DATOS"):
            df_c = pd.read_excel(up) if up.name.endswith('xlsx') else pd.read_csv(up)
            df_c.columns = [c.strip() for c in df_c.columns]
            
            count = 0
            for _, row in df_c.iterrows():
                g = str(row['Guia'])
                if g in st.session_state.db['inventario']['Guia'].values:
                    idx = st.session_state.db['inventario'][st.session_state.db['inventario']['Guia'] == g].index
                    st.session_state.db['inventario'].at[idx, 'Cliente'] = row.get('Cliente', '')
                    st.session_state.db['inventario'].at[idx, 'Producto'] = row.get('Producto', '')
                    st.session_state.db['inventario'].at[idx, 'Destinatario'] = row.get('Destinatario', '')
                    st.session_state.db['inventario'].at[idx, 'Direccion'] = row.get('Direccion', '')
                    st.session_state.db['inventario'].at[idx, 'Ciudad'] = row.get('Ciudad', '')
                    st.session_state.db['inventario'].at[idx, 'Cobro_COD'] = row.get('Cobro_COD', 0)
                    st.session_state.db['inventario'].at[idx, 'Telefono'] = row.get('Telefono', '')
                    st.session_state.db['inventario'].at[idx, 'Contenido'] = row.get('Contenido', '')
                    st.session_state.db['inventario'].at[idx, 'Valor Declarado'] = row.get('Valor Declarado', 0)
                    st.session_state.db['inventario'].at[idx, 'Peso KG'] = row.get('Peso KG', 0)
                    st.session_state.db['inventario'].at[idx, 'Estado'] = "Listo para Despacho"
                    count += 1
            st.success(f"✅ Transmisión terminada. {count} guías conciliadas.")

    st.write("### Inventario en tiempo real")
    st.dataframe(st.session_state.db['inventario'], use_container_width=True)

elif menu == "6. Liquidación y Caja":
    st.header("💰 Liquidación")
    df_liq = pd.merge(st.session_state.db['inventario'], st.session_state.db['tarifario'], on=["Cliente", "Producto"], how="left")
    st.dataframe(df_liq)

else:
    st.info(f"El módulo '{menu}' está en desarrollo o seleccionado.")
