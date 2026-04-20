import gspread
from oauth2client.service_account import ServiceAccountCredentials
import streamlit as st

def conectar_hoja():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    # Usamos el nombre exacto que pusimos en los Secrets
    creds_dict = st.secrets["gcp_service_account"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    # Verifique que su hoja en Drive se llame exactamente así
    return client.open("EnMilla_DB")

def obtener_datos(pestaña):
    try:
        sheet = conectar_hoja().worksheet(pestaña)
        return sheet.get_all_records()
    except:
        return []

def registrar_fila(pestaña, fila):
    try:
        sheet = conectar_hoja().worksheet(pestaña)
        sheet.append_row(fila)
        return True
    except:
        return False
