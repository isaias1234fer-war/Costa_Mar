import datetime

def formatear_fecha(fecha):
    """Formatear fecha para mostrar"""
    return fecha.strftime("%d/%m/%Y %H:%M")

def calcular_total_pedido(items):
    """Calcular total de un pedido"""
    return sum(item['precio'] * item['cantidad'] for item in items)

def obtener_estado_color(estado):
    """Obtener color según estado"""
    colores = {
        'pendiente': '🟡',
        'preparando': '🟠', 
        'completado': '🟢',
        'cancelado': '🔴'
    }
    return colores.get(estado, '⚪')