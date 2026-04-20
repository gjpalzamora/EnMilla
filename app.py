import streamlit as st
import pandas as pd
from datetime import datetime
import base64
# Importación de sus funciones de base de datos
from database import obtener_datos, registrar_fila

# --- CONFIGURACIÓN Y ESTILOS ---
st.set_page_config(page_title="EnMilla v2.0 - Enlaces Soluciones Logísticas", layout="wide")

# Función maestra para evitar que las guías se vuelvan notación científica
def formatear_guia(texto):
    if not texto: return ""
    return str(texto).strip().split('.')[0]

# Sistema de alertas sonoras
def emitir_sonido(tipo):
    sonido_ok = "https://www.soundjay.com/buttons/button-3.mp3"
    sonido_error = "https://www.soundjay.com/buttons/button-10.mp3"
    url = sonido_ok if tipo == "exito" else sonido_error
    audio_html = f'<audio autoplay style="display:none;"><source src="{url}" type="audio/mp3"></audio>'
    st.components.v1.html(audio_html, height=0)

# --- NAVEGACIÓN LATERAL ---
st.sidebar.title("📦 EnMilla v2.0")
st.sidebar.caption("NIT: 901.939.284-4")
menu = st.sidebar.radio("Módulos:", [
    "👥 Administración", 
    "📥 Recepción (Bodega)", 
    "🚚 Despacho (Cargue)", 
    "📊 Trazabilidad"
])

# --- MÓDULO 1: ADMINISTRACIÓN ---
if menu == "👥 Administración":
    st.header("⚙️ Configuración de Maestros")
    t1, t2 = st.tabs(["Mensajeros", "Clientes/Productos"])
    
    with t1:
        with st.form("f_mensajeros", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            n = c1.text_input("Nombre:")
            cc = c2.text_input("Cédula:")
            p = c3.text_input("Placa:")
            if st.form_submit_button("Registrar"):
                registrar_fila("Maestro_Mensajeros", [n, cc, p.upper()])
                st.success("Mensajero guardado.")

    with t2:
        with st.form("f_clientes", clear_on_submit=True):
            cl = st.text_input("Cliente:")
            pr = st.text_input("Producto:")
            if st.form_submit_button("Vincular"):
                registrar_fila("Clientes_Productos", [cl, pr])
                st.success("Producto vinculado.")

# --- MÓDULO 2: RECEPCIÓN ---
elif menu == "📥 Recepción (Bodega)":
    st.header("📥 Ingreso Automatizado")
    c_df = pd.DataFrame(obtener_datos("Clientes_Productos"))
    if not c_df.empty:
        cli = st.selectbox("Cliente:", c_df['Cliente'].unique())
        pro = st.selectbox("Producto:", c_df[c_df['Cliente'] == cli]['Producto'])
    else:
        st.error("Primero cree Clientes en Administración.")
        st.stop()

    def ingreso_auto():
        g_raw = st.session_state.ingreso_pisto
        if g_raw:
            g_f = formatear_guia(g_raw)
            ahora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            # El prefijo "'" asegura que Google Sheets lo trate como TEXTO
            registrar_fila("Inventario_Bodega", [f"'{g_f}", cli, pro, ahora])
            emitir_sonido("exito")
            st.toast(f"✅ Registrada: {g_f}")
            st.session_state.ingreso_pisto = ""

    st.text_input("ESCANEE AQUÍ:", key="ingreso_pisto", on_change=ingreso_auto)

# --- MÓDULO 3: DESPACHO (EL ESCUDO) ---
elif menu == "🚚 Despacho (Cargue)":
    st.header("🚚 Salida a Ruta")
    m_df = pd.DataFrame(obtener_datos("Maestro_Mensajeros"))
    if not m_df.empty:
        m_sel = st.selectbox("Mensajero:", m_df['Nombre'])
        p_sel = m_df[m_df['Nombre'] == m_sel]['Placa'].values[0]
        st.info(f"Placa: {p_sel}")
    else:
        st.error("No hay mensajeros registrados.")
        st.stop()

    def despacho_auto():
        g_raw = st.session_state.despacho_pisto
        if g_raw:
            g_f = formatear_guia(g_raw)
            inv = pd.DataFrame(obtener_datos("Inventario_Bodega"))
            # Limpiamos para comparar guías largas sin errores
            guias_ok = inv['Guia'].astype(str).str.replace("'", "").values if not inv.empty else []

            if g_f in guias_ok:
                ahora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                registrar_fila("Despachos", [f"'{g_f}", m_sel, p_sel, ahora, "REPARTO"])
                emitir_sonido("exito")
                st.toast(f"🚀 Despachada: {g_f}")
            else:
                emitir_sonido("error")
                st.error("❌ ERROR: Guía sin ingreso previo en bodega.")
            st.session_state.despacho_pisto = ""

    st.text_input("PISTOLEE PARA SALIDA:", key="despacho_pisto", on_change=despacho_auto)

# --- MÓDULO 4: TRAZABILIDAD ---
elif menu == "📊 Trazabilidad":
    st.header("📊 Trazabilidad Total")
    st.subheader("Inventario actual en Barrios Unidos")
    st.dataframe(pd.DataFrame(obtener_datos("Inventario_Bodega")), use_container_width=True)
