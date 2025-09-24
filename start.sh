#!/bin/bash
# Start script para Render.com

echo "=== INICIANDO SISTEMA RESTAURANTE ==="

# Ejecutar la aplicación Streamlit
# Usar 0.0.0.0 para permitir conexiones externas y puerto de Render
streamlit run app.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true