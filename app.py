import streamlit as st
import pandas as pd
import datetime
import random
import streamlit.components.v1 as components

# --- CONFIGURACIÓN E IDENTIDAD ---
st.set_page_config(page_title="Enmilla", layout="wide")

# --- MOTOR DE DATOS ---
if 'db_inventario' not in st.session_state:
    st.session_state.db_inventario = pd.DataFrame(columns=["Fecha_Ingreso", "Guia", "Nombre Destinatario", "Direcion Destino", "Telefono", "Cliente", "Producto", "Estado"])
if 'db_despacho' not in st.session_state:
    st.session_state.db_despacho = pd.DataFrame(columns=["Fecha_Salida", "Guia", "Mensajero", "Nombre Destinatario", "Cliente", "Estado"])
if 'scan_key' not in st.session_state:
    st.session_state.scan_key = 0

# --- INTERFAZ ---
col_logo, col_text = st.columns([1, 4])
with col_logo:
    try: st.image("log fondo blancojpg.jpg", width=150)
    except: st.write("📦 **ENMILLA**")
with col_text:
    st.markdown(f"<h1>ENMILLA</h1><p><b>Enlaces Soluciones Logísticas SAS</b> | NIT: 901.939.284-4</p>", unsafe_allow_html=True)

tabs = st.tabs(["📊 Tablero", "📥 Ingreso", "🛵 Cargue", "⚙️ Admin"])

# --- TAB 3: CARGUE (CON AUTO-FOCO Y LIMPIEZA) ---
with tabs[2]:
    st.subheader("🛵 Despacho a Mensajero")
    
    if st.session_state.get('db_mensajeros') is None or st.session_state.db_mensajeros.empty:
        st.warning("⚠️ Registre mensajeros en Admin.")
    else:
        m_sel = st.selectbox("Mensajero Responsable", st.session_state.db_mensajeros["Nombre"])
        
        # Este es el truco del 'scan_key': al cambiar el número, el input se destruye y renace vacío
        guia_scan = st.text_input(
            "💥 ESCANEE AQUÍ (PROCESAMIENTO AUTOMÁTICO)", 
            key=f"input_{st.session_state.scan_key}",
            placeholder="Esperando lectura de pistola..."
        )

        # INYECCIÓN DE AUTO-FOCO: Esto obliga al cursor a entrar al cuadro de texto solo
        components.html(
            f"""
            <script>
                var input = window.parent.document.querySelectorAll('input[type="text"]');
                for (var i = 0; i < input.length; i++) {{
                    if (input[i].getAttribute('aria-label') == '💥 ESCANEE AQUÍ (PROCESAMIENTO AUTOMÁTICO)') {{
                        input[i].focus();
                        input[i].select();
                    }}
                }}
            </script>
            """,
            height=0,
        )

        if guia_scan:
            inv = st.session_state.db_inventario
            # Limpiamos espacios por si la pistola manda un ENTER o TAB
            guia_limpia = guia_scan.strip()
            match = inv[inv["Guia"].astype(str) == guia_limpia]
            
            if not match.empty:
                idx = match.index[0]
                # Registrar salida
                n_salida = pd.DataFrame([{
                    "Fecha_Salida": datetime.datetime.now().strftime("%H:%M"),
                    "Guia": guia_limpia, "Mensajero": m_sel, 
                    "Nombre Destinatario": match.loc[idx, "Nombre Destinatario"], 
                    "Cliente": match.loc[idx, "Cliente"], "Estado": "En Ruta"
                }])
                st.session_state.db_despacho = pd.concat([st.session_state.db_despacho, n_salida], ignore_index=True)
                st.session_state.db_inventario = inv.drop(idx)
                
                # CAMBIO CLAVE: Cambiamos la 'key' para que el input se limpie solo
                st.session_state.scan_key += 1
                st.toast(f"✅ Guía {guia_limpia} cargada.")
                st.rerun()
            else:
                st.error(f"❌ La guía {guia_limpia} no está en bodega.")
                # Si falla, damos opción de limpiar para seguir pistoleando
                if st.button("Limpiar campo para reintentar"):
                    st.session_state.scan_key += 1
                    st.rerun()

# --- EL RESTO DEL CÓDIGO
