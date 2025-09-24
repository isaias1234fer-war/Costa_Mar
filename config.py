import streamlit as st

# Configuración de la base de datos
DB_CONFIG = {
    'host': 'localhost',
    'database': 'restaurante_db', 
    'user': 'root',
    'password': '',  # Cambiar por tu contraseña de MySQL
    'port': 3306
}

# Configuración de la aplicación
APP_CONFIG = {
    'nombre_restaurante': 'Restaurante Gourmet',
    'moneda': 'S/.',
    'impuesto': 0.18,  # 18% IGV
    'horario_apertura': '12:00',
    'horario_cierre': '23:00'
}

@st.cache_resource
def get_db_config():
    return DB_CONFIG

def get_app_config():
    return APP_CONFIG