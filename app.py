# app.py

import streamlit as st
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime
import io
import os

# --- IMPORTACIONES DE MÓDULOS ---
try:
    from db_models import (
        ClientB2B, Product, Courier, Base, engine, Session, 
        format_datetime_utc, TIMEZONE, PYTZ_AVAILABLE, get_db, create_tables
    )
    from admin_module import display_admin_module
    MODULES_IMPORTED = True
    st.success("Módulos 'db_models.py' y 'admin_module.py' importados correctamente.")
except ImportError as e:
    st.error(f"Error de importación: {e}. Asegúrate de que 'db_models.py' y 'admin_module.py' estén en la misma carpeta que 'app.py' y que sus nombres sean correctos.")
    MODULES_IMPORTED = False

# --- CONFIGURACIÓN INICIAL DE STREAMLIT ---
# CORRECCIÓN: Cambiado el título de la página y el título de la barra lateral a "EnMilla"
st.set_page_config(page_title="EnMilla - Backoffice", layout="wide")

# --- INICIALIZACIÓN DE LA BASE DE DATOS Y SESIÓN ---
db_session_generator = None
db_session = None
if MODULES_IMPORTED:
    try:
        db_session_generator = get_db() 
        db_session = next(db_session_generator) 
        st.success("Conexión a la base de datos lista.")
    except Exception as e:
        st.error(f"Error al obtener la sesión de la base de datos: {e}")
        MODULES_IMPORTED = False

# --- LLAMADA A LA CREACIÓN DE TABLAS (SOLO PARA DESARROLLO INICIAL) ---
# if MODULES_IMPORTED:
#     try:
#         create_tables()
#         st.success("Tablas de base de datos verificadas/creadas.")
#     except Exception as e:
#         st.error(f"Error al intentar crear tablas: {e}")
#         MODULES_IMPORTED = False

# --- BARRA LATERAL DE NAVEGACIÓN ---
# CORRECCIÓN: Cambiado el título de la barra lateral a "EnMilla"
st.sidebar.title("EnMilla")

# Definimos las opciones del menú principal
menu_options = ["Administración", "Recepción", "Gestión Paquetes", "Despacho y Rutas", "Gestión COD", "Reportes"]
modulo = st.sidebar.radio("Módulos:", menu_options)

# --- LÓGICA DE NAVEGACIÓN Y CARGA DE MÓDULOS ---

if MODULES_IMPORTED and db_session:
    if modulo == "Administración":
        display_admin_module(db_session)
        
    elif modulo == "Recepción":
        st.header("Módulo de Recepción")
        st.info("Funcionalidad de Recepción (en desarrollo).")
        
    elif modulo == "Gestión Paquetes":
        st.header("Módulo de Gestión de Paquetes")
        st.info("Funcionalidad de Gestión de Paquetes (en desarrollo).")
        
    elif modulo == "Despacho y Rutas":
        st.header("Módulo de Despacho y Rutas")
        st.info("Funcionalidad de Despacho y Rutas (en desarrollo).")
        
    elif modulo == "Gestión COD":
        st.header("Módulo de Gestión de Cobros (COD)")
        st.info("Funcionalidad de Gestión de COD (en desarrollo).")
        
    elif modulo == "Reportes":
        st.header("Módulo de Reportes")
        st.info("Funcionalidad de Reportes (en desarrollo).")

else:
    st.error("La aplicación no puede iniciarse correctamente debido a errores de importación o conexión a la base de datos.")

# --- CIERRE DE LA SESIÓN DE BASE DE DATOS ---
if db_session:
    try:
        db_session.close()
    except Exception as e:
        st.error(f"Error al cerrar la sesión de base de datos: {e}")
