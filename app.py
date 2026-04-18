# app.py

import streamlit as st
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime
import io
import os

# --- CONFIGURACIÓN DE LA BASE DE DATOS Y MODELOS ---
# Importamos todo lo necesario de db_models.py.
# Si db_models.py está en la misma carpeta, la importación es directa.
try:
    from db_models import (
        ClientB2B, Product, Courier, Base, engine, Session, 
        format_datetime_utc, TIMEZONE, PYTZ_AVAILABLE, get_db, create_tables
    )
    # Importamos la función principal del módulo de administración
    from admin_module import display_admin_module
    
    # Bandera para indicar si las importaciones fueron exitosas
    MODULES_IMPORTED = True
    st.success("Módulos 'db_models.py' y 'admin_module.py' importados correctamente.")
except ImportError as e:
    st.error(f"Error de importación: {e}. Asegúrate de que 'db_models.py' y 'admin_module.py' estén en la misma carpeta que 'app.py' y que sus nombres sean correctos.")
    MODULES_IMPORTED = False
except Exception as e:
    st.error(f"Ocurrió un error inesperado al importar módulos: {e}")
    MODULES_IMPORTED = False

# --- CONFIGURACIÓN INICIAL DE STREAMLIT ---
st.set_page_config(page_title="EnMilla - Backoffice", layout="wide")

# --- INICIALIZACIÓN DE LA BASE DE DATOS Y SESIÓN ---
# Solo procedemos si las importaciones fueron exitosas
db_session_generator = None
db_session = None
if MODULES_IMPORTED:
    try:
        # Obtenemos el generador de sesiones
        db_session_generator = get_db() 
        # Obtenemos la sesión actual
        db_session = next(db_session_generator) 
        st.success("Conexión a la base de datos lista.")
    except Exception as e:
        st.error(f"Error al obtener la sesión de la base de datos: {e}")
        MODULES_IMPORTED = False # Si falla la conexión a la BD, tampoco podemos continuar

# --- LLAMADA A LA CREACIÓN DE TABLAS (SOLO PARA DESARROLLO INICIAL) ---
# Descomenta esta línea SOLO la primera vez que ejecutes la app o hagas cambios en los modelos.
# ¡En producción, usa migraciones (Alembic)!
# if MODULES_IMPORTED:
#     try:
#         # Llama a la función definida en db_models.py para crear las tablas
#         create_tables() 
#         st.success("Tablas de base de datos verificadas/creadas.")
#     except Exception as e:
#         st.error(f"Error al intentar crear tablas: {e}")
#         MODULES_IMPORTED = False # Si falla la creación de tablas, tampoco podemos continuar

# --- BARRA LATERAL DE NAVEGACIÓN ---
st.sidebar.title("EnMilla")

# Definimos las opciones del menú principal
menu_options = ["Administración", "Recepción", "Gestión Paquetes", "Despacho y Rutas", "Gestión COD", "Reportes"]
modulo = st.sidebar.radio("Módulos:", menu_options)

# --- LÓGICA DE NAVEGACIÓN Y CARGA DE MÓDULOS ---

# Solo procedemos si las importaciones y la BD están listas
if MODULES_IMPORTED and db_session:
    if modulo == "Administración":
        # Llamamos a la función que muestra la interfaz del módulo de administración
        display_admin_module(db_session)
        
    elif modulo == "Recepción":
        st.header("Módulo de Recepción")
        st.info("Funcionalidad de Recepción (en desarrollo).")
        # Aquí llamarías a la función display_reception_module(db_session) cuando la crees
        
    elif modulo == "Gestión Paquetes":
        st.header("Módulo de Gestión de Paquetes")
        st.info("Funcionalidad de Gestión de Paquetes (en desarrollo).")
        # Aquí llamarías a la función display_package_management_module(db_session)
        
    elif modulo == "Despacho y Rutas":
        st.header("Módulo de Despacho y Rutas")
        st.info("Funcionalidad de Despacho y Rutas (en desarrollo).")
        # Aquí llamarías a la función display_dispatch_module(db_session)
        
    elif modulo == "Gestión COD":
        st.header("Módulo de Gestión de Cobros (COD)")
        st.info("Funcionalidad de Gestión de COD (en desarrollo).")
        # Aquí llamarías a la función display_cod_module(db_session)
        
    elif modulo == "Reportes":
        st.header("Módulo de Reportes")
        st.info("Funcionalidad de Reportes (en desarrollo).")
        # Aquí llamarías a la función display_reports_module(db_session)

else:
    # Si hubo errores de importación o conexión, mostramos un mensaje general
    st.error("La aplicación no puede iniciarse correctamente debido a errores de importación o conexión a la base de datos. Por favor, revisa los mensajes de error anteriores.")

# --- CIERRE DE LA SESIÓN DE BASE DE DATOS ---
# Asegurarse de que la sesión se cierre si se llegó a abrir
if db_session:
    try:
        db_session.close()
    except Exception as e:
        st.error(f"Error al cerrar la sesión de base de datos: {e}")
