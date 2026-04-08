import streamlit as st
import pandas as pd
import datetime

# --- CONFIGURACIÓN LEGAL Y DE MARCA ---
st.set_page_config(page_title="Enmilla - Enlaces Logística", layout="wide")

# --- INICIALIZACIÓN DE BASES DE DATOS (Persistencia de Sesión) ---
if 'db_mensajeros' not in st.session_state:
    st.session_state.db_mensajeros = pd.DataFrame(columns=["ID", "Nombre", "Placa", "Telefono"])

if 'db_tarifario' not in st.session_state:
    st.session_state.db_tarifario = pd.DataFrame(columns=["Cliente", "Producto", "Cobro_Cli", "Pago_Mens"])

if 'db_despacho' not in st.session_state:
    st.session_state.db_despacho = pd.DataFrame(columns=["Fecha", "Guia", "Cliente", "Producto", "Mensajero", "Estado"])

# --- BARRA LATERAL (IDENTIDAD CORPORATIVA) ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2312/2312214.png", width=100)
    st.title("ENMILLA OPS")
    st.markdown("**Enlaces Soluciones Logística SAS**")
    st.caption("NIT: 901.939.284-4")
    st.markdown("---")
    
    rol = st.radio("Nivel de Acceso", ["Operativo", "Administrador"])
    
    if rol == "Administrador":
        password = st.text_input("Contraseña de Admin", type="password")
        menu = st.selectbox("Gestión de Maestros", ["Configuración de Clientes", "Liquidación y Reportes"])
    else:
        menu = st.selectbox("Operación Diaria", ["Despacho (Modo Pistola)", "Registro de Mensajeros"])

# --- ENCABEZADO INSTITUCIONAL ---
st.markdown(f"""
    <div style="background-color:#003366;padding:15px;border-radius:10px;text-align:center;border-bottom: 5px solid #f1c40f;">
        <h1 style="color:white;margin:0;">SISTEMA LOGÍSTICO ENMILLA</h1>
        <p style="color:white;margin:5px;"><b>Propiedad de:</b> Enlaces Soluciones Logística SAS | NIT: 901.939.284-4 | Bogotá D.C.</p>
    </div><br>
    """, unsafe_allow_html=True)

# --- 1. MÓDULO: REGISTRO DE MENSAJEROS (Disponible para Operarios) ---
if menu == "Registro de Mensajeros" or (rol == "Administrador" and password == "1234"):
    st.header("👤 Maestro de Mensajeros")
    with st.form("form_mens", clear_on_submit=True):
        c1, c2 = st.columns(2)
        nombre_m = c1.text_input("Nombre Completo del Mensajero")
        cedula_m = c2.text_input("Cédula / ID")
        placa_m = c1.text_input("Placa del Vehículo")
        tel_m = c2.text_input("Teléfono de Contacto")
        if st.form_submit_button("Registrar Mensajero"):
            if nombre_m and cedula_m:
                nuevo_m = pd.DataFrame([{"ID": cedula_m, "Nombre": nombre_m, "Placa": placa_m, "Telefono": tel_m}])
                st.session_state.db_mensajeros = pd.concat([st.session_state.db_mensajeros, nuevo_m], ignore_index=True)
                st.success(f"Mensajero {nombre_m} vinculado a la flota.")
            else:
                st.error("Nombre y Cédula son obligatorios.")

# --- 2. MÓDULO: CONFIGURACIÓN DE CLIENTES (Solo Admin) ---
if rol == "Administrador" and password == "1234":
    if menu == "Configuración de Clientes":
        st.header("🏢 Tarifario Multiproducto")
        with st.form("form_tarifas", clear_on_submit=True):
            cliente = st.text_input("Nombre de la Empresa Cliente")
            producto = st.text_input("Tipo de Producto / Servicio (Ej: Sobre, Caja, Express)")
            col_a, col_b = st.columns(2)
            c_cliente = col_a.number_input("Tarifa Cobro Cliente ($)", min_value=0, step=500)
            p_mensajero = col_b.number_input("Tarifa Pago Mensajero ($)", min_value=0, step=500)
            if st.form_submit_button("Guardar Configuración"):
                if cliente and producto:
                    nueva_t = pd.DataFrame([{"Cliente": cliente, "Producto": producto, "Cobro_Cli": c_cliente, "Pago_Mens": p_mensajero}])
                    st.session_state.db_tarifario = pd.concat([st.session_state.db_tarifario, nueva_t], ignore_index=True)
                    st.success(f"Tarifa {producto} para {cliente} guardada.")

    elif menu == "Liquidación y Reportes":
        st.header("💰 Panel de Control y Liquidación")
        st.write("### Tarifas Activas")
        st.dataframe(st.session_state.db_tarifario, use_container_width=True)

# --- 3. MÓDULO: DESPACHO PROFESIONAL (MODO PISTOLA) ---
elif rol == "Operativo" and menu == "Despacho (Modo Pistola)":
    st.header("🛵 Terminal de Salida a Ruta")
    
    if st.session_state.db_mensajeros.empty or st.session_state.db_tarifario.empty:
        st.warning("⚠️ El sistema requiere que existan Mensajeros y Tarifas de Clientes configuradas.")
    else:
        # Selección de cabecera (se mantiene fija para el pistoleo)
        col_m, col_c, col_p = st.columns(3)
        mensajero_sel = col_m.selectbox("Asignar a Mensajero:", st.session_state.db_mensajeros["Nombre"])
        cliente_lista = st.session_state.db_tarifario["Cliente"].unique()
        cliente_sel = col_c.selectbox("Cliente Remitente:", cliente_lista)
        
        prods_filtrados = st.session_state.db_tarifario[st.session_state.db_tarifario["Cliente"] == cliente_sel]["Producto"]
        producto_sel = col_p.selectbox("Tipo de Envío:", prods_filtrados)
        
        st.markdown("---")
        # El campo de "Pistoleo"
        guia_scan = st.text_input("💥 PISTOLEE CÓDIGO DE GUÍA AQUÍ", key="scanner", help="El cursor debe estar aquí para usar la pistola.")

        if guia_scan:
            ahora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            despacho_actual = pd.DataFrame([{
                "Fecha": ahora,
                "Guia": guia_scan,
                "Cliente": cliente_sel,
                "Producto": producto_sel,
                "Mensajero": mensajero_sel,
                "Estado": "En Ruta / Despachado"
            }])
            st.session_state.db_despacho = pd.concat([st.session_state.db_despacho, despacho_actual], ignore_index=True)
            st.toast(f"📦 Guía {guia_scan} asignada a {mensajero_sel}", icon="✅")

# --- TABLA DE MOVIMIENTOS (SIEMPRE AL FINAL) ---
st.markdown("---")
st.subheader("📋 Registro de Operaciones en Tiempo Real")
if not st.session_state.db_despacho.empty:
    st.dataframe(st.session_state.db_despacho.tail(20), use_container_width=True)
    
    # Resumen de carga por mensajero
    st.write("### Guías cargadas por mensajero hoy:")
    resumen = st.session_state.db_despacho.groupby("Mensajero").size().reset_index(name='Total Guías')
    st.table(resumen)
else:
    st.info("No hay despachos registrados aún. Inicie el pistoleo de guías.")

if rol == "Administrador" and password != "" and password != "1234":
    st.sidebar.error("Clave incorrecta")
