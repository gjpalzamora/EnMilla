import pandas as pd
from datetime import datetime
# Importamos la conexión de Streamlit a Google Sheets
from streamlit_gsheets import GSheetsConnection
import streamlit as st

def conectar_db():
    # Establece la conexión usando el ID de su Spreadsheet
    conn = st.connection("gsheets", type=GSheetsConnection)
    return conn

def obtener_datos(nombre_pestana):
    """Trae la información de las tablas: Mensajeros, Ingresos o Logs"""
    conn = conectar_db()
    # Leemos la pestaña específica de su base de datos
    df = conn.read(worksheet=nombre_pestana)
    return df

def registrar_fila(nombre_pestana, lista_datos):
    """Registra un nuevo pistoleo (Ingreso o Despacho)"""
    conn = conectar_db()
    # Traemos los datos actuales
    df_actual = conn.read(worksheet=nombre_pestana)
    
    # Creamos la nueva fila con la estructura del Plan Maestro
    nueva_fila = pd.DataFrame([lista_datos], columns=df_actual.columns)
    
    # Concatenamos y actualizamos la base de datos en la nube
    df_final = pd.concat([df_actual, nueva_fila], ignore_index=True)
    conn.update(worksheet=nombre_pestana, data=df_final)
