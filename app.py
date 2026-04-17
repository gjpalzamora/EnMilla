import streamlit as st
import sys
import os

# 1. REFERENCIA MÉDICA AL PATH: Esto obliga a Python a mirar dentro de 'centro'
sys.path.append(os.path.join(os.path.dirname(__file__), 'centro'))

try:
    # 2. IMPORTACIÓN DIRECTA: Ahora que 'centro' está en el path, importamos los nombres de los archivos
    from database import engine, SessionLocal, Base
    from models import Package, Movement, Courier
except ImportError as e:
    st.error(f"Error de Dr. en Python: No se hallaron los archivos en 'centro'. Detalle: {e}")
    st.stop()

# --- CONFIGURACIÓN DE LOGÍSTICA EXPERTA ---
st.set_page_config(page_title="EnMilla ERP - Enlaces Soluciones Logísticas", layout="wide")

# Inicializar Base de Datos
Base.metadata.create_all(bind=engine)

st.title("🚚 EnMilla ERP")
st.sidebar.header("Panel de Control")
menu = st.sidebar.radio("Operaciones", ["Recepción", "Despacho", "Inventario"])

db = SessionLocal()

if menu == "Recepción":
    st.subheader("📦 Registro Masivo de Guías")
    # Aquí va tu lógica de ingreso de carga...
    st.info("Módulo listo para procesar ingresos de última milla.")

db.close()
