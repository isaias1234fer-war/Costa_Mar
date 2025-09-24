import streamlit as st
import pandas as pd
import mysql.connector
from mysql.connector import Error
import datetime
import time
from contextlib import contextmanager

# ================== CONFIGURACIÓN DE LA BASE DE DATOS ==================
class DatabaseManager:
    def __init__(self):
        self.config = {
            'host': 'localhost',
            'database': 'restaurante_db',
            'user': 'root',
            'password': '',  # Cambiar por tu contraseña de MySQL
            'port': 3306
        }
    
    @contextmanager
    def get_connection(self):
        connection = None
        try:
            connection = mysql.connector.connect(**self.config)
            yield connection
        except Error as e:
            st.error(f"❌ Error de conexión a la base de datos: {e}")
            st.info("💡 Asegúrate de que MySQL esté ejecutándose y las credenciales sean correctas")
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
                    st.error(f"❌ Error en consulta SQL: {e}")
                    return None
                finally:
                    cursor.close()

class SistemaRestauranteDB:
    def __init__(self):
        self.db = DatabaseManager()
        self.inicializar_base_datos()
    
    def inicializar_base_datos(self):
        """Crear tablas si no existen e insertar datos iniciales"""
        try:
            # Tabla de usuarios
            self.db.ejecutar_consulta("""
                CREATE TABLE IF NOT EXISTS usuarios (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    nombre VARCHAR(100) NOT NULL,
                    rol ENUM('admin', 'mozo', 'cliente') NOT NULL,
                    activo BOOLEAN DEFAULT TRUE,
                    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tabla de categorías
            self.db.ejecutar_consulta("""
                CREATE TABLE IF NOT EXISTS categorias (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    nombre VARCHAR(50) NOT NULL,
                    descripcion TEXT,
                    activa BOOLEAN DEFAULT TRUE
                )
            """)
            
            # Tabla de items del menú
            self.db.ejecutar_consulta("""
                CREATE TABLE IF NOT EXISTS menu_items (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    nombre VARCHAR(100) NOT NULL,
                    descripcion TEXT,
                    precio DECIMAL(10,2) NOT NULL,
                    categoria_id INT,
                    disponible BOOLEAN DEFAULT TRUE,
                    FOREIGN KEY (categoria_id) REFERENCES categorias(id)
                )
            """)
            
            # Tabla de mesas
            self.db.ejecutar_consulta("""
                CREATE TABLE IF NOT EXISTS mesas (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    numero INT UNIQUE NOT NULL,
                    capacidad INT NOT NULL,
                    ubicacion VARCHAR(50),
                    estado ENUM('disponible', 'ocupada', 'reservada') DEFAULT 'disponible'
                )
            """)
            
            # Tabla de reservas
            self.db.ejecutar_consulta("""
                CREATE TABLE IF NOT EXISTS reservas (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    cliente_nombre VARCHAR(100) NOT NULL,
                    cliente_telefono VARCHAR(20),
                    fecha_reserva DATE NOT NULL,
                    hora_reserva TIME NOT NULL,
                    numero_personas INT NOT NULL,
                    mesa_id INT,
                    estado ENUM('pendiente', 'confirmada', 'cancelada', 'completada') DEFAULT 'pendiente',
                    notas TEXT,
                    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (mesa_id) REFERENCES mesas(id)
                )
            """)
            
            # Tabla de pedidos
            self.db.ejecutar_consulta("""
                CREATE TABLE IF NOT EXISTS pedidos (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    cliente_nombre VARCHAR(100) NOT NULL,
                    tipo ENUM('local', 'llevar', 'delivery') NOT NULL,
                    estado ENUM('pendiente', 'preparando', 'listo', 'entregado', 'cancelado') DEFAULT 'pendiente',
                    total DECIMAL(10,2) DEFAULT 0,
                    mozo_id INT,
                    mesa_id INT,
                    direccion_entrega TEXT,
                    telefono_contacto VARCHAR(20),
                    notas TEXT,
                    fecha_pedido TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
            """)
            
            # Tabla de items del pedido
            self.db.ejecutar_consulta("""
                CREATE TABLE IF NOT EXISTS pedido_items (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    pedido_id INT,
                    menu_item_id INT,
                    cantidad INT NOT NULL,
                    precio_unitario DECIMAL(10,2) NOT NULL,
                    subtotal DECIMAL(10,2) NOT NULL,
                    FOREIGN KEY (pedido_id) REFERENCES pedidos(id) ON DELETE CASCADE
                )
            """)
            
            # Insertar datos iniciales
            self.insertar_datos_iniciales()
            
        except Error as e:
            st.error(f"Error al inicializar base de datos: {e}")
    
    def insertar_datos_iniciales(self):
        """Insertar datos de prueba si las tablas están vacías"""
        # Verificar si ya existen datos
        usuarios = self.db.ejecutar_consulta("SELECT COUNT(*) as count FROM usuarios", fetch=True)
        if usuarios[0]['count'] == 0:
            # Insertar usuarios
            self.db.ejecutar_consulta("""
                INSERT INTO usuarios (username, password, nombre, rol) VALUES 
                ('admin', 'admin123', 'Administrador Principal', 'admin'),
                ('mozo01', 'mozo123', 'Carlos Rodríguez', 'mozo'),
                ('mozo02', 'mozo123', 'María González', 'mozo')
            """)
        
        categorias = self.db.ejecutar_consulta("SELECT COUNT(*) as count FROM categorias", fetch=True)
        if categorias[0]['count'] == 0:
            # Insertar categorías
            self.db.ejecutar_consulta("""
                INSERT INTO categorias (nombre, descripcion) VALUES 
                ('Entradas', 'Platos para comenzar tu experiencia'),
                ('Platos Principales', 'Nuestras especialidades principales'),
                ('Bebidas', 'Bebidas refrescantes y cocteles'),
                ('Postres', 'Dulces finales para tu comida')
            """)
        
        menu_items = self.db.ejecutar_consulta("SELECT COUNT(*) as count FROM menu_items", fetch=True)
        if menu_items[0]['count'] == 0:
            # Insertar items del menú
            self.db.ejecutar_consulta("""
                INSERT INTO menu_items (nombre, descripcion, precio, categoria_id) VALUES 
                ('Ceviche Clásico', 'Pescado fresco marinado en limón', 25.00, 1),
                ('Causa Limeña', 'Papa amarilla con pollo o atún', 18.00, 1),
                ('Lomo Saltado', 'Carne salteada con cebolla y tomate', 35.00, 2),
                ('Ají de Gallina', 'Pollo deshilachado en crema de ají', 28.00, 2),
                ('Pisco Sour', 'Coctel tradicional peruano', 15.00, 3),
                ('Chicha Morada', 'Bebida de maíz morado', 8.00, 3),
                ('Mazamorra Morada', 'Postre de maíz morado con frutas', 10.00, 4),
                ('Suspiro Limeño', 'Manjar blanco con merengue', 12.00, 4)
            """)
        
        mesas = self.db.ejecutar_consulta("SELECT COUNT(*) as count FROM mesas", fetch=True)
        if mesas[0]['count'] == 0:
            # Insertar mesas
            self.db.ejecutar_consulta("""
                INSERT INTO mesas (numero, capacidad, ubicacion) VALUES 
                (1, 4, 'Interior'), (2, 2, 'Ventana'), (3, 6, 'Terraza'),
                (4, 4, 'Interior'), (5, 2, 'Ventana'), (6, 8, 'Privada')
            """)
    
    # ================== MÉTODOS DE USUARIOS ==================
    def autenticar_usuario(self, username, password):
        query = "SELECT * FROM usuarios WHERE username = %s AND password = %s AND activo = TRUE"
        usuario = self.db.ejecutar_consulta(query, (username, password), fetch=True)
        return usuario[0] if usuario else None
    
    def obtener_usuarios(self, rol=None):
        query = "SELECT * FROM usuarios WHERE activo = TRUE"
        params = []
        if rol:
            query += " AND rol = %s"
            params.append(rol)
        query += " ORDER BY nombre"
        return self.db.ejecutar_consulta(query, params, fetch=True)
    
    def crear_usuario(self, username, password, nombre, rol):
        query = "INSERT INTO usuarios (username, password, nombre, rol) VALUES (%s, %s, %s, %s)"
        return self.db.ejecutar_consulta(query, (username, password, nombre, rol))
    
    # ================== MÉTODOS DEL MENÚ ==================
    def obtener_categorias(self):
        return self.db.ejecutar_consulta("SELECT * FROM categorias WHERE activa = TRUE ORDER BY nombre", fetch=True)
    
    def obtener_menu_completo(self):
        query = """
            SELECT mi.*, c.nombre as categoria_nombre 
            FROM menu_items mi 
            JOIN categorias c ON mi.categoria_id = c.id 
            WHERE mi.disponible = TRUE 
            ORDER BY c.nombre, mi.nombre
        """
        return self.db.ejecutar_consulta(query, fetch=True)
    
    def obtener_menu_por_categoria(self, categoria_id):
        query = "SELECT * FROM menu_items WHERE categoria_id = %s AND disponible = TRUE ORDER BY nombre"
        return self.db.ejecutar_consulta(query, (categoria_id,), fetch=True)
    
    def crear_item_menu(self, nombre, descripcion, precio, categoria_id):
        query = "INSERT INTO menu_items (nombre, descripcion, precio, categoria_id) VALUES (%s, %s, %s, %s)"
        return self.db.ejecutar_consulta(query, (nombre, descripcion, precio, categoria_id))
    
    def actualizar_item_menu(self, item_id, **kwargs):
        if not kwargs:
            return False
        set_clause = ", ".join([f"{key} = %s" for key in kwargs.keys()])
        query = f"UPDATE menu_items SET {set_clause} WHERE id = %s"
        params = list(kwargs.values()) + [item_id]
        return self.db.ejecutar_consulta(query, params)
    
    # ================== MÉTODOS DE MESAS ==================
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
    
    # ================== MÉTODOS DE RESERVAS ==================
    def crear_reserva(self, cliente_nombre, telefono, fecha, hora, personas, mesa_id, notas=""):
        query = """
            INSERT INTO reservas (cliente_nombre, cliente_telefono, fecha_reserva, hora_reserva, numero_personas, mesa_id, notas)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        return self.db.ejecutar_consulta(query, (cliente_nombre, telefono, fecha, hora, personas, mesa_id, notas))
    
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
    
    # ================== MÉTODOS DE PEDIDOS ==================
    def crear_pedido(self, cliente_nombre, tipo, mozo_id=None, mesa_id=None, **kwargs):
        query = """
            INSERT INTO pedidos (cliente_nombre, tipo, mozo_id, mesa_id, direccion_entrega, telefono_contacto, notas)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        params = (cliente_nombre, tipo, mozo_id, mesa_id, 
                 kwargs.get('direccion_entrega'), kwargs.get('telefono_contacto'), kwargs.get('notas'))
        return self.db.ejecutar_consulta(query, params)
    
    def agregar_item_pedido(self, pedido_id, item_id, cantidad):
        # Obtener precio del item
        precio_query = "SELECT precio FROM menu_items WHERE id = %s"
        precio_result = self.db.ejecutar_consulta(precio_query, (item_id,), fetch=True)
        if not precio_result:
            return False
        
        precio = precio_result[0]['precio']
        subtotal = precio * cantidad
        
        query = """
            INSERT INTO pedido_items (pedido_id, menu_item_id, cantidad, precio_unitario, subtotal)
            VALUES (%s, %s, %s, %s, %s)
        """
        self.db.ejecutar_consulta(query, (pedido_id, item_id, cantidad, precio, subtotal))
        
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
            if isinstance(estado, list):
                placeholders = ', '.join(['%s'] * len(estado))
                query += f" AND p.estado IN ({placeholders})"
                params.extend(estado)
            else:
                query += " AND p.estado = %s"
                params.append(estado)
        if fecha:
            query += " AND DATE(p.fecha_pedido) = %s"
            params.append(fecha)
        query += " ORDER BY p.fecha_pedido DESC"
        return self.db.ejecutar_consulta(query, params, fetch=True)
    
    def obtener_detalle_pedido(self, pedido_id):
        query = """
            SELECT pi.*, mi.nombre as item_nombre, mi.descripcion 
            FROM pedido_items pi 
            JOIN menu_items mi ON pi.menu_item_id = mi.id 
            WHERE pi.pedido_id = %s
        """
        return self.db.ejecutar_consulta(query, (pedido_id,), fetch=True)
    
    def actualizar_estado_pedido(self, pedido_id, estado):
        query = "UPDATE pedidos SET estado = %s WHERE id = %s"
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
    
    def obtener_productos_mas_vendidos(self, fecha_inicio=None, fecha_fin=None):
        query = """
            SELECT mi.nombre, 
                   SUM(pi.cantidad) as total_vendido,
                   SUM(pi.subtotal) as total_ingresos
            FROM pedido_items pi
            JOIN pedidos p ON pi.pedido_id = p.id
            JOIN menu_items mi ON pi.menu_item_id = mi.id
            WHERE p.estado = 'entregado'
        """
        params = []
        if fecha_inicio and fecha_fin:
            query += " AND p.fecha_pedido BETWEEN %s AND %s"
            params.extend([fecha_inicio, fecha_fin])
        
        query += " GROUP BY mi.id, mi.nombre ORDER BY total_vendido DESC LIMIT 10"
        return self.db.ejecutar_consulta(query, params, fetch=True)

# ================== CONFIGURACIÓN DE STREAMLIT ==================
st.set_page_config(
    page_title="Sistema Restaurante Gourmet",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ================== INICIALIZACIÓN DEL SISTEMA ==================
@st.cache_resource
def get_sistema():
    return SistemaRestauranteDB()

sistema = get_sistema()

# ================== FUNCIONES DE LA INTERFAZ ==================
def mostrar_login():
    st.title("🍽️ Restaurante Gourmet")
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.container():
            st.subheader("🔐 Inicio de Sesión")
            
            tipo_usuario = st.selectbox(
                "Selecciona tu rol:",
                ["Cliente", "Mozo", "Administrador"]
            )
            
            with st.form("login_form"):
                if tipo_usuario == "Administrador":
                    usuario = st.text_input("👤 Usuario", value="admin")
                    password = st.text_input("🔒 Contraseña", type="password", value="admin123")
                elif tipo_usuario == "Mozo":
                    usuario = st.text_input("👤 Usuario", value="mozo01")
                    password = st.text_input("🔒 Contraseña", type="password", value="mozo123")
                else:
                    usuario = st.text_input("👤 Tu Nombre", placeholder="Ingresa tu nombre completo")
                    password = st.text_input("📞 Teléfono (opcional)", placeholder="Para confirmaciones")
                
                if st.form_submit_button("🚪 Ingresar al Sistema", use_container_width=True):
                    if usuario.strip():
                        if tipo_usuario == "Cliente":
                            st.session_state.update({
                                'logged_in': True,
                                'tipo_usuario': 'cliente',
                                'nombre': usuario,
                                'username': usuario.lower()
                            })
                            st.success(f"✅ ¡Bienvenido {usuario}!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            usuario_db = sistema.autenticar_usuario(usuario, password)
                            if usuario_db:
                                st.session_state.update({
                                    'logged_in': True,
                                    'tipo_usuario': usuario_db['rol'],
                                    'nombre': usuario_db['nombre'],
                                    'username': usuario_db['username'],
                                    'user_id': usuario_db['id']
                                })
                                st.success(f"✅ ¡Bienvenido {usuario_db['nombre']}!")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("❌ Credenciales incorrectas")
                    else:
                        st.warning("⚠️ Por favor ingresa tu nombre/usuario")

def mostrar_dashboard_admin():
    st.subheader("📊 Dashboard en Tiempo Real")
    
    # Métricas desde la base de datos
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        reservas_hoy = len(sistema.obtener_reservas(datetime.date.today()))
        st.metric("📅 Reservas Hoy", reservas_hoy)
    
    with col2:
        pedidos_activos = len(sistema.obtener_pedidos(['pendiente', 'preparando']))
        st.metric("🍽️ Pedidos Activos", pedidos_activos)
    
    with col3:
        mesas_ocupadas = len(sistema.obtener_mesas('ocupada'))
        st.metric("🪑 Mesas Ocupadas", mesas_ocupadas)
    
    with col4:
        # Ventas del día aproximadas
        pedidos_hoy = sistema.obtener_pedidos(fecha=datetime.date.today())
        ventas_hoy = sum(p['total'] for p in pedidos_hoy if p['estado'] == 'entregado')
        st.metric("💰 Ventas Hoy", f"S/. {ventas_hoy:,.2f}")
    
    # Últimas reservas
    st.subheader("📅 Últimas Reservas")
    reservas = sistema.obtener_reservas()[:5]
    if reservas:
        for reserva in reservas:
            with st.expander(f"{reserva['cliente_nombre']} - {reserva['fecha_reserva']} {reserva['hora_reserva']}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Mesa:** {reserva.get('mesa_numero', 'Por asignar')}")
                    st.write(f"**Personas:** {reserva['numero_personas']}")
                with col2:
                    st.write(f"**Estado:** {reserva['estado']}")
                    st.write(f"**Teléfono:** {reserva.get('cliente_telefono', 'N/A')}")
                
                if reserva['estado'] == 'pendiente':
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("✅ Confirmar", key=f"conf_{reserva['id']}"):
                            sistema.actualizar_estado_reserva(reserva['id'], 'confirmada')
                            st.rerun()
                    with col2:
                        if st.button("❌ Cancelar", key=f"cancel_{reserva['id']}"):
                            sistema.actualizar_estado_reserva(reserva['id'], 'cancelada')
                            st.rerun()
    else:
        st.info("📭 No hay reservas registradas")

def mostrar_gestion_menu():
    st.subheader("📋 Gestión del Menú")
    
    tab1, tab2, tab3 = st.tabs(["👀 Ver Menú", "➕ Agregar Item", "✏️ Editar Items"])
    
    with tab1:
        categorias = sistema.obtener_categorias()
        for categoria in categorias:
            st.write(f"### 🍽️ {categoria['nombre']}")
            st.caption(categoria.get('descripcion', ''))
            
            items = sistema.obtener_menu_por_categoria(categoria['id'])
            if items:
                for item in items:
                    col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
                    with col1:
                        st.write(f"**{item['nombre']}**")
                        st.caption(item['descripcion'])
                    with col2:
                        st.write(f"💰 S/. {item['precio']:.2f}")
                    with col3:
                        estado = "✅" if item['disponible'] else "❌"
                        st.write(estado)
                    with col4:
                        if st.button("Editar", key=f"edit_{item['id']}"):
                            st.session_state.editando_item = item['id']
            else:
                st.info(f"No hay items en {categoria['nombre']}")
            st.markdown("---")
    
    with tab2:
        with st.form("nuevo_item"):
            st.subheader("➕ Agregar Nuevo Item al Menú")
            
            nombre = st.text_input("Nombre del Item*")
            descripcion = st.text_area("Descripción")
            precio = st.number_input("Precio (S/.)*", min_value=0.0, step=0.5, value=20.0)
            categorias = sistema.obtener_categorias()
            categoria_id = st.selectbox(
                "Categoría*", 
                options=[c['id'] for c in categorias],
                format_func=lambda x: next((c['nombre'] for c in categorias if c['id'] == x), '')
            )
            disponible = st.checkbox("Disponible", value=True)
            
            if st.form_submit_button("Agregar Item"):
                if nombre and precio > 0:
                    resultado = sistema.crear_item_menu(nombre, descripcion, precio, categoria_id)
                    if resultado:
                        if not disponible:
                            sistema.actualizar_item_menu(resultado, disponible=False)
                        st.success("✅ Item agregado exitosamente!")
                        st.rerun()
                    else:
                        st.error("❌ Error al agregar el item")
                else:
                    st.warning("⚠️ Completa los campos obligatorios (*)")
    
    with tab3:
        if 'editando_item' in st.session_state:
            st.subheader("✏️ Editar Item del Menú")
            # Implementar edición de items
            st.info("Funcionalidad de edición en desarrollo")
            if st.button("Volver al menú"):
                del st.session_state.editando_item
                st.rerun()

def mostrar_gestion_mesas():
    st.subheader("🪑 Gestión de Mesas")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("### 📊 Estado de Mesas")
        mesas = sistema.obtener_mesas()
        for mesa in mesas:
            estado_color = "🟢" if mesa['estado'] == 'disponible' else "🔴"
            with st.container():
                col1, col2, col3 = st.columns([2, 2, 1])
                with col1:
                    st.write(f"**Mesa {mesa['numero']}**")
                    st.caption(f"Capacidad: {mesa['capacidad']} pers.")
                with col2:
                    st.write(f"Estado: {estado_color} {mesa['estado']}")
                with col3:
                    if mesa['estado'] == 'ocupada':
                        if st.button("Liberar", key=f"lib_{mesa['id']}"):
                            sistema.actualizar_estado_mesa(mesa['id'], 'disponible')
                            st.rerun()
            st.markdown("---")
    
    with col2:
        st.write("### 🔄 Acciones Rápidas")
        
        # Ocupar mesa
        with st.form("ocupar_mesa"):
            st.write("**Ocupar Mesa**")
            mesas_disponibles = sistema.obtener_mesas('disponible')
            if mesas_disponibles:
                mesa_seleccionada = st.selectbox(
                    "Seleccionar Mesa",
                    options=[m['id'] for m in mesas_disponibles],
                    format_func=lambda x: next(f"Mesa {m['numero']} ({m['capacidad']} pers.)" 
                                             for m in mesas_disponibles if m['id'] == x)
                )
                cliente_nombre = st.text_input("Nombre del Cliente*")
                
                if st.form_submit_button("Ocupar Mesa"):
                    if cliente_nombre:
                        sistema.actualizar_estado_mesa(mesa_seleccionada, 'ocupada')
                        st.success(f"✅ Mesa ocupada por {cliente_nombre}")
                        st.rerun()
                    else:
                        st.error("❌ Ingresa el nombre del cliente")
            else:
                st.info("ℹ️ No hay mesas disponibles")

def mostrar_gestion_reservas():
    st.subheader("📅 Gestión de Reservas")
    
    # Filtros
    col1, col2 = st.columns(2)
    with col1:
        filtro_fecha = st.date_input("Filtrar por fecha", datetime.date.today())
    with col2:
        filtro_estado = st.selectbox("Filtrar por estado", 
                                   ["Todas", "pendiente", "confirmada", "cancelada"])
    
    # Obtener reservas filtradas
    reservas = sistema.obtener_reservas(
        fecha=filtro_fecha if filtro_fecha else None,
        estado=filtro_estado if filtro_estado != "Todas" else None
    )
    
    if reservas:
        for reserva in reservas:
            with st.expander(f"📅 {reserva['cliente_nombre']} - {reserva['fecha_reserva']} {reserva['hora_reserva']}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Cliente:** {reserva['cliente_nombre']}")
                    st.write(f"**Teléfono:** {reserva.get('cliente_telefono', 'N/A')}")
                    st.write(f"**Fecha:** {reserva['fecha_reserva']}")
                    st.write(f"**Hora:** {reserva['hora_reserva']}")
                with col2:
                    st.write(f"**Personas:** {reserva['numero_personas']}")
                    st.write(f"**Mesa:** {reserva.get('mesa_numero', 'Por asignar')}")
                    st.write(f"**Estado:** {reserva['estado']}")
                    if reserva.get('notas'):
                        st.write(f"**Notas:** {reserva['notas']}")
                
                # Acciones según estado
                if reserva['estado'] == 'pendiente':
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button("✅ Confirmar", key=f"conf_r_{reserva['id']}"):
                            sistema.actualizar_estado_reserva(reserva['id'], 'confirmada')
                            st.rerun()
                    with col2:
                        if st.button("❌ Cancelar", key=f"cancel_r_{reserva['id']}"):
                            sistema.actualizar_estado_reserva(reserva['id'], 'cancelada')
                            st.rerun()
    else:
        st.info("📭 No hay reservas con los filtros seleccionados")

def mostrar_gestion_pedidos():
    st.subheader("🍽️ Gestión de Pedidos")
    
    # Filtros
    col1, col2 = st.columns(2)
    with col1:
        filtro_estado = st.selectbox("Estado del pedido", 
                                   ["Todos", "pendiente", "preparando", "listo", "entregado", "cancelado"])
    with col2:
        filtro_fecha = st.date_input("Fecha del pedido", datetime.date.today())
    
    # Obtener pedidos
    pedidos = sistema.obtener_pedidos(
        estado=filtro_estado if filtro_estado != "Todos" else None,
        fecha=filtro_fecha
    )
    
    if pedidos:
        for pedido in pedidos:
            estado_colores = {
                'pendiente': '🟡',
                'preparando': '🟠', 
                'listo': '🟢',
                'entregado': '🔵',
                'cancelado': '🔴'
            }
            color = estado_colores.get(pedido['estado'], '⚪')
            
            with st.expander(f"{color} Pedido #{pedido['id']} - {pedido['cliente_nombre']} - {pedido['estado']}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Cliente:** {pedido['cliente_nombre']}")
                    st.write(f"**Tipo:** {pedido['tipo']}")
                    st.write(f"**Mesa:** {pedido.get('mesa_numero', 'N/A')}")
                    st.write(f"**Fecha:** {pedido['fecha_pedido'].strftime('%d/%m/%Y %H:%M')}")
                with col2:
                    st.write(f"**Total:** S/. {pedido['total']:.2f}")
                    st.write(f"**Estado:** {pedido['estado']}")
                    st.write(f"**Mozo:** {pedido.get('mozo_nombre', 'N/A')}")
                    if pedido.get('notas'):
                        st.write(f"**Notas:** {pedido['notas']}")
                
                # Items del pedido
                items = sistema.obtener_detalle_pedido(pedido['id'])
                if items:
                    st.write("**Items:**")
                    for item in items:
                        st.write(f"- {item['item_nombre']} x{item['cantidad']} - S/. {item['subtotal']:.2f}")
                
                # Cambiar estado
                if pedido['estado'] in ['pendiente', 'preparando', 'listo']:
                    st.write("**Cambiar estado:**")
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        if pedido['estado'] == 'pendiente' and st.button("👨‍🍳 Preparando", key=f"prep_{pedido['id']}"):
                            sistema.actualizar_estado_pedido(pedido['id'], 'preparando')
                            st.rerun()
                    with col2:
                        if pedido['estado'] == 'preparando' and st.button("✅ Listo", key=f"listo_{pedido['id']}"):
                            sistema.actualizar_estado_pedido(pedido['id'], 'listo')
                            st.rerun()
                    with col3:
                        if pedido['estado'] == 'listo' and st.button("🚚 Entregado", key=f"ent_{pedido['id']}"):
                            sistema.actualizar_estado_pedido(pedido['id'], 'entregado')
                            st.rerun()
                    with col4:
                        if st.button("❌ Cancelar", key=f"cancel_p_{pedido['id']}"):
                            sistema.actualizar_estado_pedido(pedido['id'], 'cancelado')
                            st.rerun()
    else:
        st.info("📭 No hay pedidos con los filtros seleccionados")

def mostrar_nuevo_pedido():
    st.subheader("➕ Nuevo Pedido")
    
    with st.form("nuevo_pedido"):
        col1, col2 = st.columns(2)
        
        with col1:
            cliente_nombre = st.text_input("Nombre del Cliente*")
            tipo_pedido = st.selectbox("Tipo de Pedido", ["local", "llevar", "delivery"])
            telefono = st.text_input("Teléfono de Contacto")
            notas = st.text_area("Notas especiales")
        
        with col2:
            if tipo_pedido == "local":
                mesas_disponibles = sistema.obtener_mesas('disponible')
                if mesas_disponibles:
                    mesa_id = st.selectbox(
                        "Seleccionar Mesa",
                        options=[m['id'] for m in mesas_disponibles],
                        format_func=lambda x: next(f"Mesa {m['numero']} ({m['capacidad']} pers.)" 
                                                 for m in mesas_disponibles if m['id'] == x)
                    )
                else:
                    st.warning("No hay mesas disponibles")
                    mesa_id = None
            elif tipo_pedido == "delivery":
                direccion = st.text_input("Dirección de Entrega*")
            else:
                direccion = None
                mesa_id = None
        
        # Selección de items del menú
        st.write("### 🍽️ Seleccionar Items del Menú")
        categorias = sistema.obtener_categorias()
        items_seleccionados = []
        
        for categoria in categorias:
            st.write(f"#### {categoria['nombre']}")
            items = sistema.obtener_menu_por_categoria(categoria['id'])
            if items:
                for item in items:
                    col1, col2, col3 = st.columns([3, 2, 1])
                    with col1:
                        st.write(f"**{item['nombre']}**")
                        st.caption(item['descripcion'])
                    with col2:
                        st.write(f"💰 S/. {item['precio']:.2f}")
                    with col3:
                        cantidad = st.number_input(f"Cantidad", min_value=0, max_value=10, value=0, 
                                                 key=f"item_{item['id']}")
                        if cantidad > 0:
                            items_seleccionados.append({
                                'item_id': item['id'],
                                'nombre': item['nombre'],
                                'precio': item['precio'],
                                'cantidad': cantidad,
                                'subtotal': item['precio'] * cantidad
                            })
        
        if st.form_submit_button("Crear Pedido"):
            if cliente_nombre and items_seleccionados:
                if tipo_pedido == "delivery" and not direccion:
                    st.error("❌ Ingresa la dirección de entrega para delivery")
                else:
                    # Crear pedido
                    pedido_id = sistema.crear_pedido(
                        cliente_nombre=cliente_nombre,
                        tipo=tipo_pedido,
                        mozo_id=st.session_state.get('user_id'),
                        mesa_id=mesa_id if tipo_pedido == 'local' else None,
                        direccion_entrega=direccion if tipo_pedido == 'delivery' else None,
                        telefono_contacto=telefono,
                        notas=notas
                    )
                    
                    if pedido_id:
                        # Agregar items al pedido
                        for item in items_seleccionados:
                            sistema.agregar_item_pedido(pedido_id, item['item_id'], item['cantidad'])
                        
                        # Actualizar estado de mesa si es pedido local
                        if tipo_pedido == 'local' and mesa_id:
                            sistema.actualizar_estado_mesa(mesa_id, 'ocupada')
                        
                        st.success(f"✅ Pedido #{pedido_id} creado exitosamente!")
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error("❌ Error al crear el pedido")
            else:
                st.error("❌ Completa los campos obligatorios y selecciona al menos un item")

def mostrar_nueva_reserva():
    st.subheader("📅 Nueva Reserva")
    
    with st.form("nueva_reserva"):
        col1, col2 = st.columns(2)
        
        with col1:
            cliente_nombre = st.text_input("Nombre Completo*")
            telefono = st.text_input("Teléfono*")
            fecha_reserva = st.date_input("Fecha de Reserva*", min_value=datetime.date.today())
            hora_reserva = st.time_input("Hora de Reserva*", datetime.time(19, 0))
        
        with col2:
            numero_personas = st.number_input("Número de Personas*", min_value=1, max_value=20, value=2)
            
            # Mostrar mesas disponibles para la fecha y hora seleccionada
            mesas_disponibles = sistema.obtener_mesas('disponible')
            if mesas_disponibles:
                mesa_id = st.selectbox(
                    "Seleccionar Mesa*",
                    options=[m['id'] for m in mesas_disponibles],
                    format_func=lambda x: next(f"Mesa {m['numero']} ({m['capacidad']} pers.)" 
                                             for m in mesas_disponibles if m['id'] == x)
                )
            else:
                st.warning("No hay mesas disponibles para la fecha seleccionada")
                mesa_id = None
            
            notas = st.text_area("Notas especiales (alergias, celebraciones, etc.)")
        
        if st.form_submit_button("Confirmar Reserva"):
            if cliente_nombre and telefono and fecha_reserva and hora_reserva and numero_personas and mesa_id:
                resultado = sistema.crear_reserva(
                    cliente_nombre=cliente_nombre,
                    telefono=telefono,
                    fecha=fecha_reserva,
                    hora=hora_reserva,
                    personas=numero_personas,
                    mesa_id=mesa_id,
                    notas=notas
                )
                
                if resultado:
                    # Actualizar estado de la mesa
                    sistema.actualizar_estado_mesa(mesa_id, 'reservada')
                    st.success("✅ Reserva confirmada exitosamente!")
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error("❌ Error al crear la reserva")
            else:
                st.error("❌ Completa todos los campos obligatorios (*)")

def mostrar_reportes():
    st.subheader("📈 Reportes y Análisis")
    
    tab1, tab2, tab3 = st.tabs(["📊 Ventas", "🍽️ Productos Más Vendidos", "📅 Reservas"])
    
    with tab1:
        st.write("### Reporte de Ventas")
        col1, col2 = st.columns(2)
        with col1:
            fecha_inicio = st.date_input("Fecha Inicio", datetime.date.today() - datetime.timedelta(days=7))
        with col2:
            fecha_fin = st.date_input("Fecha Fin", datetime.date.today())
        
        if st.button("Generar Reporte"):
            ventas = sistema.obtener_ventas_por_fecha(fecha_inicio, fecha_fin)
            if ventas:
                df_ventas = pd.DataFrame(ventas)
                st.dataframe(df_ventas)
                
                # Gráfico de ventas
                if not df_ventas.empty:
                    st.line_chart(df_ventas.set_index('fecha')['total_ventas'])
            else:
                st.info("No hay datos de ventas para el período seleccionado")
    
    with tab2:
        st.write("### Productos Más Vendidos")
        col1, col2 = st.columns(2)
        with col1:
            fecha_inicio = st.date_input("Fecha Inicio ", datetime.date.today() - datetime.timedelta(days=30))
        with col2:
            fecha_fin = st.date_input("Fecha Fin ", datetime.date.today())
        
        if st.button("Generar Reporte "):
            productos = sistema.obtener_productos_mas_vendidos(fecha_inicio, fecha_fin)
            if productos:
                df_productos = pd.DataFrame(productos)
                st.dataframe(df_productos)
                
                # Gráfico de barras
                if not df_productos.empty:
                    st.bar_chart(df_productos.set_index('nombre')['total_vendido'])
            else:
                st.info("No hay datos de productos vendidos para el período seleccionado")
    
    with tab3:
        st.write("### Reporte de Reservas")
        fecha_reporte = st.date_input("Fecha para reporte de reservas", datetime.date.today())
        
        reservas = sistema.obtener_reservas(fecha=fecha_reporte)
        if reservas:
            st.write(f"**Total de reservas para {fecha_reporte}:** {len(reservas)}")
            
            df_reservas = pd.DataFrame(reservas)
            # Mostrar solo columnas relevantes
            if not df_reservas.empty:
                df_display = df_reservas[['cliente_nombre', 'hora_reserva', 'numero_personas', 'estado']]
                st.dataframe(df_display)
        else:
            st.info(f"No hay reservas para la fecha {fecha_reporte}")

def mostrar_interfaz_cliente():
    st.sidebar.title(f"👋 Hola, {st.session_state.nombre}")
    
    opcion = st.sidebar.selectbox(
        "Menú Cliente",
        ["🍽️ Ver Menú", "📅 Hacer Reserva", "🛒 Realizar Pedido"]
    )
    
    if opcion == "🍽️ Ver Menú":
        st.header("🍽️ Nuestro Menú")
        categorias = sistema.obtener_categorias()
        for categoria in categorias:
            st.write(f"### {categoria['nombre']}")
            st.caption(categoria.get('descripcion', ''))
            
            items = sistema.obtener_menu_por_categoria(categoria['id'])
            if items:
                cols = st.columns(2)
                for i, item in enumerate(items):
                    with cols[i % 2]:
                        with st.container():
                            st.write(f"#### {item['nombre']}")
                            st.write(item['descripcion'])
                            st.write(f"**Precio: S/. {item['precio']:.2f}**")
                            st.markdown("---")
            else:
                st.info(f"No hay items disponibles en {categoria['nombre']}")
    
    elif opcion == "📅 Hacer Reserva":
        mostrar_nueva_reserva()
    
    elif opcion == "🛒 Realizar Pedido":
        mostrar_nuevo_pedido()

def mostrar_interfaz_mozo():
    st.sidebar.title(f"👨‍💼 Mozo: {st.session_state.nombre}")
    
    opcion = st.sidebar.selectbox(
        "Menú Mozo",
        ["📊 Dashboard", "🍽️ Gestión de Pedidos", "🪑 Gestión de Mesas", "➕ Nuevo Pedido"]
    )
    
    if opcion == "📊 Dashboard":
        mostrar_dashboard_admin()  # Reutilizamos el dashboard simplificado
    
    elif opcion == "🍽️ Gestión de Pedidos":
        mostrar_gestion_pedidos()
    
    elif opcion == "🪑 Gestión de Mesas":
        mostrar_gestion_mesas()
    
    elif opcion == "➕ Nuevo Pedido":
        mostrar_nuevo_pedido()

def mostrar_interfaz_admin():
    st.sidebar.title(f"👑 Administrador: {st.session_state.nombre}")
    
    opcion = st.sidebar.selectbox(
        "Menú Administrador",
        ["📊 Dashboard", "📋 Gestión de Menú", "🪑 Gestión de Mesas", 
         "📅 Gestión de Reservas", "🍽️ Gestión de Pedidos", "📈 Reportes"]
    )
    
    if opcion == "📊 Dashboard":
        mostrar_dashboard_admin()
    
    elif opcion == "📋 Gestión de Menú":
        mostrar_gestion_menu()
    
    elif opcion == "🪑 Gestión de Mesas":
        mostrar_gestion_mesas()
    
    elif opcion == "📅 Gestión de Reservas":
        mostrar_gestion_reservas()
    
    elif opcion == "🍽️ Gestión de Pedidos":
        mostrar_gestion_pedidos()
    
    elif opcion == "📈 Reportes":
        mostrar_reportes()

# ================== APLICACIÓN PRINCIPAL ==================
def main():
    # Inicializar estado de sesión
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    
    # Mostrar interfaz según estado de login
    if not st.session_state.logged_in:
        mostrar_login()
    else:
        # Barra superior con información de usuario
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            st.title("🍽️ Sistema Restaurante Gourmet")
        with col3:
            if st.button("🚪 Cerrar Sesión"):
                st.session_state.clear()
                st.rerun()
        
        st.markdown("---")
        
        # Mostrar interfaz según tipo de usuario
        if st.session_state.tipo_usuario == 'cliente':
            mostrar_interfaz_cliente()
        elif st.session_state.tipo_usuario == 'mozo':
            mostrar_interfaz_mozo()
        elif st.session_state.tipo_usuario == 'admin':
            mostrar_interfaz_admin()

if __name__ == "__main__":
    main()