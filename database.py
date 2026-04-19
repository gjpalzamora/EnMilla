import gspread
from oauth2client.service_account import ServiceAccountCredentials
import streamlit as st

def conectar_hoja():
    # Definimos los permisos
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    # Cargamos las credenciales desde los Secrets de Streamlit por seguridad
    # Esto evita que sus claves queden expuestas en GitHub
    creds_dict = st.secrets["gcp_service_account"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    
    client = gspread.authorize(creds)
    # Debe crear una hoja en su Google Drive llamada EXACTAMENTE: EnMilla_DB
    return client.open("EnMilla_DB")

def obtener_datos(pestaña):
    sheet = conectar_hoja().worksheet(pestaña)
    return sheet.get_all_records()

def registrar_fila(pestaña, fila):
    sheet = conectar_hoja().worksheet(pestaña)
    sheet.append_row(fila)
