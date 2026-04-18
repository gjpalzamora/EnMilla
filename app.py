# app.py

import streamlit as st
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime
import io
import os # Necesario para leer variables de entorno

# --- IMPORTACIONES DE MÓDULOS ---
# Asegúrate de que estos archivos estén en la misma carpeta o en una subcarpeta accesible
# Si db_models.py está en una subcarpeta 'src', la importación sería: from src.db_models import ...
try:
    from db_models import ClientB2B, Product, Courier, Base, engine, Session, format_datetime_utc, TIMEZONE, PYTZ_AVAILABLE, get_db, create_tables # Importamos todo de db_models
    from admin_module import display_admin_module, get_clients # Importamos la función del módulo de administración
    MODULES_IMPORTED = True
except ImportError as e:
    st.error(f"Error de importación: {e}. Asegúrate de que 'db_models.py' y 'admin_module.py' estén en el lugar correcto y las importaciones sean correctas.")
    MODULES_IMPORTED = False

# --- CONFIGURACIÓN INICIAL DE STREAMLIT ---
st.set_page_config(page_title="Enlaces 360 - Backoffice", layout="wide")

# --- INICIALIZACIÓN DE LA BASE DE DATOS Y SESIÓN ---
# Usamos la función get_db() que definimos en db_models.py
# La sesión se maneja dentro de cada módulo o función que la necesite.

# --- LLAMADA A LA CREACIÓN DE TABLAS (SOLO PARA DESARROLLO INICIAL) ---
# ¡ADVERTENCIA! Descomenta esta línea SOLO la primera vez que ejecutes la app
# o cuando hagas cambios en los modelos. En producción, usa migraciones (Alembic).
# if MODULES_IMPORTED:
#     create_tables() # Llama a la función definida en db_models.py

# --- BARRA LATERAL DE NAVEGACIÓN ---
st.sidebar.title("🔗 Enlaces 360")

# Definimos las opciones del menú principal
menu_options = ["Administración", "Recepción", "Gestión Paquetes", "Despacho y Rutas", "Gestión COD", "Reportes"]
modulo = st.sidebar.radio("Módulos:", menu_options)

# --- LÓGICA DE NAVEGACIÓN Y CARGA DE MÓDULOS ---

# Obtener una sesión de base de datos para usarla en los módulos
db_session_generator = get_db() # Esto nos da un generador para la sesión
db_session = next(db_session_generator) # Obtenemos la sesión actual

if MODULES_IMPORTED:
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
    st.error("La aplicación no puede continuar debido a errores de importación.")

# --- CIERRE DE LA SESIÓN DE BASE DE DATOS ---
# Es importante cerrar la sesión al final de la ejecución del script de Streamlit
# para liberar recursos.
if db_session:
    db_session.close()

# --- CORRECCIÓN DEL ERROR DE SINTAXIS (EJEMPLO) ---
# El error que viste '{' was never closed' ocurría en una línea como esta:
# client_options = {c.id: c.name for c in clients} # ¡Esta es la línea correcta!
# Si tu código original tenía algo como:
# client_options = {c.id: c.name for c in clients # ¡Faltaba el '}' al final!
# O si era una definición de diccionario mal formada.
# La corrección se realiza dentro de las funciones de cada módulo (ej: en admin_module.py)
# donde se necesiten crear diccionarios o listas.
# En este archivo app.py, la navegación es la principal lógica.
