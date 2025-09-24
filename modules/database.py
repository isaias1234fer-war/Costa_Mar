import mysql.connector
from mysql.connector import Error
import streamlit as st
from contextlib import contextmanager
import datetime

class DatabaseManager:
    def __init__(self):
        self.config = {
            'host': 'localhost',
            'database': 'restaurante_db',
            'user': 'root',
            'password': '',
            'port': 3306
        }
    
    @contextmanager
    def get_connection(self):
        connection = None
        try:
            connection = mysql.connector.connect(**self.config)
            yield connection
        except Error as e:
            st.error(f"Error de conexión a la base de datos: {e}")
        finally:
            if connection and connection.is_connected():
                connection.close()
    
    def ejecutar_consulta(self, query, params=None, fetch=False):
        with self.get_connection() as connection:
            if connection:
                cursor = connection.cursor(dictionary=True)
                try:
                    cursor.execute(query, params or ())
                    if fetch:
                        if query.strip().upper().startswith('SELECT'):
                            result = cursor.fetchall()
                        else:
                            connection.commit()
                            result = cursor.lastrowid
                    else:
                        connection.commit()
                        result = cursor.rowcount
                    return result
                except Error as e:
                    st.error(f"Error en consulta: {e}")
                    return None
                finally:
                    cursor.close()

class RestauranteDB:
    def __init__(self):
        self.db = DatabaseManager()
    
    # ================== USUARIOS ==================
    def autenticar_usuario(self, username, password):
        query = "SELECT * FROM usuarios WHERE username = %s AND password = %s AND activo = TRUE"
        usuario = self.db.ejecutar_consulta(query, (username, password), fetch=True)
        return usuario[0] if usuario else None
    
    def obtener_usuario_por_id(self, user_id):
        query = "SELECT * FROM usuarios WHERE id = %s"
        return self.db.ejecutar_consulta(query, (user_id,), fetch=True)
    
    # ================== MENÚ ==================
    def obtener_categorias(self):
        query = "SELECT * FROM categorias WHERE activa = TRUE ORDER BY nombre"
        return self.db.ejecutar_consulta(query, fetch=True)
    
    def obtener_menu_items(self, categoria_id=None, disponibles=True):
        query = """
            SELECT mi.*, c.nombre as categoria_nombre 
            FROM menu_items mi 
            JOIN categorias c ON mi.categoria_id = c.id 
            WHERE mi.disponible = %s
        """
        params = [disponibles]
        
        if categoria_id:
            query += " AND mi.categoria_id = %s"
            params.append(categoria_id)
        
        query += " ORDER BY c.nombre, mi.nombre"
        return self.db.ejecutar_consulta(query, params, fetch=True)
    
    def agregar_item_menu(self, nombre, descripcion, precio, categoria_id, disponible=True):
        query = """
            INSERT INTO menu_items (nombre, descripcion, precio, categoria_id, disponible) 
            VALUES (%s, %s, %s, %s, %s)
        """
        return self.db.ejecutar_consulta(query, (nombre, descripcion, precio, categoria_id, disponible))
    
    def actualizar_item_menu(self, item_id, **kwargs):
        if not kwargs:
            return False
        
        set_clause = ", ".join([f"{key} = %s" for key in kwargs.keys()])
        query = f"UPDATE menu_items SET {set_clause} WHERE id = %s"
        params = list(kwargs.values()) + [item_id]
        
        return self.db.ejecutar_consulta(query, params)
    
    # ================== MESAS ==================
    def obtener_mesas(self, estado=None):
        query = "SELECT * FROM mesas WHERE 1=1"
        params = []
        
        if estado:
            query += " AND estado = %s"
            params.append(estado)
        
        query += " ORDER BY numero"
        return self.db.ejecutar_consulta(query, params, fetch=True)
    
    def actualizar_estado_mesa(self, mesa_id, estado):
        query = "UPDATE mesas SET estado = %s WHERE id = %s"
        return self.db.ejecutar_consulta(query, (estado, mesa_id))
    
    # ================== RESERVAS ==================
    def crear_reserva(self, cliente_nombre, cliente_telefono, fecha_reserva, hora_reserva, 
                     numero_personas, mesa_id, notas=""):
        query = """
            INSERT INTO reservas 
            (cliente_nombre, cliente_telefono, fecha_reserva, hora_reserva, numero_personas, mesa_id, notas) 
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        params = (cliente_nombre, cliente_telefono, fecha_reserva, hora_reserva, 
                 numero_personas, mesa_id, notas)
        
        return self.db.ejecutar_consulta(query, params)
    
    def obtener_reservas(self, fecha=None, estado=None):
        query = """
            SELECT r.*, m.numero as mesa_numero 
            FROM reservas r 
            LEFT JOIN mesas m ON r.mesa_id = m.id 
            WHERE 1=1
        """
        params = []
        
        if fecha:
            query += " AND r.fecha_reserva = %s"
            params.append(fecha)
        
        if estado:
            query += " AND r.estado = %s"
            params.append(estado)
        
        query += " ORDER BY r.fecha_reserva DESC, r.hora_reserva DESC"
        return self.db.ejecutar_consulta(query, params, fetch=True)
    
    def actualizar_estado_reserva(self, reserva_id, estado):
        query = "UPDATE reservas SET estado = %s WHERE id = %s"
        return self.db.ejecutar_consulta(query, (estado, reserva_id))
    
    # ================== PEDIDOS ==================
    def crear_pedido(self, cliente_nombre, tipo, mozo_id=None, mesa_id=None, 
                    direccion_entrega=None, telefono_contacto=None, notas=None):
        query = """
            INSERT INTO pedidos 
            (cliente_nombre, tipo, mozo_id, mesa_id, direccion_entrega, telefono_contacto, notas, total) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, 0)
        """
        params = (cliente_nombre, tipo, mozo_id, mesa_id, direccion_entrega, telefono_contacto, notas)
        
        pedido_id = self.db.ejecutar_consulta(query, params)
        return pedido_id
    
    def agregar_item_pedido(self, pedido_id, menu_item_id, cantidad):
        # Obtener precio del item
        precio_query = "SELECT precio FROM menu_items WHERE id = %s"
        precio_result = self.db.ejecutar_consulta(precio_query, (menu_item_id,), fetch=True)
        
        if not precio_result:
            return False
        
        precio = precio_result[0]['precio']
        subtotal = precio * cantidad
        
        query = """
            INSERT INTO pedido_items (pedido_id, menu_item_id, cantidad, precio_unitario, subtotal) 
            VALUES (%s, %s, %s, %s, %s)
        """
        self.db.ejecutar_consulta(query, (pedido_id, menu_item_id, cantidad, precio, subtotal))
        
        # Actualizar total del pedido
        self.actualizar_total_pedido(pedido_id)
        return True
    
    def actualizar_total_pedido(self, pedido_id):
        query = """
            UPDATE pedidos SET total = (
                SELECT COALESCE(SUM(subtotal), 0) FROM pedido_items WHERE pedido_id = %s
            ) WHERE id = %s
        """
        return self.db.ejecutar_consulta(query, (pedido_id, pedido_id))
    
    def obtener_pedidos(self, estado=None, fecha=None):
        query = """
            SELECT p.*, u.nombre as mozo_nombre, m.numero as mesa_numero 
            FROM pedidos p 
            LEFT JOIN usuarios u ON p.mozo_id = u.id 
            LEFT JOIN mesas m ON p.mesa_id = m.id 
            WHERE 1=1
        """
        params = []
        
        if estado:
            query += " AND p.estado = %s"
            params.append(estado)
        
        if fecha:
            query += " AND DATE(p.fecha_pedido) = %s"
            params.append(fecha)
        
        query += " ORDER BY p.fecha_pedido DESC"
        return self.db.ejecutar_consulta(query, params, fetch=True)
    
    def obtener_items_pedido(self, pedido_id):
        query = """
            SELECT pi.*, mi.nombre as item_nombre 
            FROM pedido_items pi 
            JOIN menu_items mi ON pi.menu_item_id = mi.id 
            WHERE pi.pedido_id = %s
        """
        return self.db.ejecutar_consulta(query, (pedido_id,), fetch=True)
    
    def actualizar_estado_pedido(self, pedido_id, estado):
        query = "UPDATE pedidos SET estado = %s, fecha_actualizacion = NOW() WHERE id = %s"
        return self.db.ejecutar_consulta(query, (estado, pedido_id))
    
    # ================== REPORTES ==================
    def obtener_ventas_por_fecha(self, fecha_inicio, fecha_fin):
        query = """
            SELECT DATE(fecha_pedido) as fecha, 
                   COUNT(*) as total_pedidos,
                   SUM(total) as total_ventas,
                   AVG(total) as promedio_venta
            FROM pedidos 
            WHERE estado = 'entregado' 
            AND fecha_pedido BETWEEN %s AND %s
            GROUP BY DATE(fecha_pedido)
            ORDER BY fecha
        """
        return self.db.ejecutar_consulta(query, (fecha_inicio, fecha_fin), fetch=True)
    
    def obtener_productos_mas_vendidos(self, fecha_inicio, fecha_fin):
        query = """
            SELECT mi.nombre, 
                   SUM(pi.cantidad) as total_vendido,
                   SUM(pi.subtotal) as total_ingresos
            FROM pedido_items pi
            JOIN pedidos p ON pi.pedido_id = p.id
            JOIN menu_items mi ON pi.menu_item_id = mi.id
            WHERE p.estado = 'entregado'
            AND p.fecha_pedido BETWEEN %s AND %s
            GROUP BY mi.id, mi.nombre
            ORDER BY total_vendido DESC
            LIMIT 10
        """
        return self.db.ejecutar_consulta(query, (fecha_inicio, fecha_fin), fetch=True)