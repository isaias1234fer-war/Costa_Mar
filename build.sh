#!/bin/bash
# Build script para Render.com

echo "=== INSTALANDO SISTEMA RESTAURANTE ==="

# Instalar dependencias de Python
pip install -r requirements.txt

# Verificar instalación
echo "=== VERIFICACIÓN ==="
python --version
pip list