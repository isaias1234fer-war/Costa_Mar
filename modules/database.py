import mysql.connector
from mysql.connector import Error
import streamlit as st
import os
from contextlib import contextmanager

class DatabaseManager:
    def __init__(self):
        # Configuración para Render (usar variables de entorno)
        self.config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'database': os.getenv('DB_NAME', 'restaurante_db'),
            'user': os.getenv('DB_USER', 'root'),
            'password': os.getenv('DB_PASSWORD', ''),
            'port': int(os.getenv('DB_PORT', '3306')),
            'charset': 'utf8mb4',
            'connect_timeout': 10  # Timeout de conexión
        }
        
        # Mostrar info de conexión (solo en desarrollo)
        if os.getenv('APP_ENV') == 'development':
            st.sidebar.info(f"Conectando a: {self.config['host']}:{self.config['port']}")
    
    @contextmanager
    def get_connection(self):
        """Context manager corregido para MySQL"""
        connection = None
        try:
            connection = mysql.connector.connect(**self.config)
            if connection.is_connected():
                yield connection
            else:
                raise RuntimeError("No se pudo conectar a la base de datos")
        except Error as e:
            st.error(f"❌ Error de conexión MySQL: {e}")
            # Mostrar información de ayuda
            st.info("💡 Verifica que:")
            st.info("1. La base de datos MySQL esté ejecutándose")
            st.info("2. Las credenciales sean correctas")
            st.info("3. El host sea accesible desde Render")
            raise  # Re-lanzar la excepción
        finally:
            if connection and connection.is_connected():
                connection.close()
    
    def ejecutar_consulta(self, query, params=None, fetch=False):
        """Método seguro para ejecutar consultas"""
        try:
            with self.get_connection() as connection:
                cursor = connection.cursor(dictionary=True)
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
                
                cursor.close()
                return result
                
        except Exception as e:
            st.error(f"❌ Error en consulta SQL: {e}")
            return None

class RestauranteDB:
    def __init__(self):
        self.db = DatabaseManager()
        # No inicializar automáticamente para evitar errores en inicio
        if 'db_initialized' not in st.session_state:
            self.inicializar_base_datos()
            st.session_state.db_initialized = True
    
    def inicializar_base_datos(self):
        """Inicializar base de datos con manejo de errores"""
        try:
            st.info("🔄 Inicializando base de datos...")
            
            # Tabla de usuarios
            self.db.ejecutar_consulta("""
                CREATE TABLE IF NOT EXISTS usuarios (
                    id INT AUTO_INCREMENT PRIMARY KEY,
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
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    nombre VARCHAR(50) NOT NULL,
                    descripcion TEXT,
                    activa BOOLEAN DEFAULT TRUE
                )
            """)
            
            # Tabla de items del menú
            self.db.ejecutar_consulta("""
                CREATE TABLE IF NOT EXISTS menu_items (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    nombre VARCHAR(100) NOT NULL,
                    descripcion TEXT,
                    precio DECIMAL(10,2) NOT NULL,
                    categoria_id INT,
                    disponible BOOLEAN DEFAULT TRUE,
                    FOREIGN KEY (categoria_id) REFERENCES categorias(id)
                )
            """)
            
            # Insertar datos iniciales
            self.insertar_datos_iniciales()
            
            st.success("✅ Base de datos inicializada correctamente")
            
        except Exception as e:
            st.error(f"❌ Error inicializando base de datos: {e}")
            # Continuar aunque falle la inicialización
    
    def insertar_datos_iniciales(self):
        """Insertar datos de ejemplo de forma segura"""
        try:
            # Usuarios por defecto
            usuarios = [
                ('admin', 'admin123', 'Administrador Principal', 'admin'),
                ('mozo01', 'mozo123', 'Carlos Rodríguez', 'mozo')
            ]
            
            for usuario in usuarios:
                self.db.ejecutar_consulta("""
                    INSERT IGNORE INTO usuarios (username, password, nombre, rol) 
                    VALUES (%s, %s, %s, %s)
                """, usuario)
            
            # Categorías
            categorias = [
                ('Entradas', 'Platos para comenzar'),
                ('Platos Principales', 'Nuestras especialidades'),
                ('Bebidas', 'Bebidas y cocteles')
            ]
            
            for categoria in categorias:
                self.db.ejecutar_consulta("""
                    INSERT IGNORE INTO categorias (nombre, descripcion) 
                    VALUES (%s, %s)
                """, categoria)
            
            # Items del menú
            menu_items = [
                ('Ceviche Clásico', 'Pescado fresco marinado en limón', 25.00, 1),
                ('Lomo Saltado', 'Carne salteada con cebolla y tomate', 35.00, 2),
                ('Pisco Sour', 'Coctel tradicional peruano', 15.00, 3)
            ]
            
            for item in menu_items:
                self.db.ejecutar_consulta("""
                    INSERT IGNORE INTO menu_items (nombre, descripcion, precio, categoria_id) 
                    VALUES (%s, %s, %s, %s)
                """, item)
                
        except Exception as e:
            st.warning(f"⚠️ Algunos datos iniciales no pudieron insertarse: {e}")
    
    # ================== MÉTODOS DE CONSULTA ==================
    
    def autenticar_usuario(self, username, password):
        """Autenticar usuario con manejo de errores"""
        try:
            resultado = self.db.ejecutar_consulta(
                "SELECT * FROM usuarios WHERE username = %s AND password = %s AND activo = TRUE",
                (username, password), 
                fetch=True
            )
            return resultado[0] if resultado else None
        except:
            return None
    
    def obtener_menu_completo(self):
        """Obtener menú con manejo de errores"""
        try:
            return self.db.ejecutar_consulta("""
                SELECT mi.*, c.nombre as categoria_nombre 
                FROM menu_items mi 
                JOIN categorias c ON mi.categoria_id = c.id 
                WHERE mi.disponible = TRUE 
                ORDER BY c.nombre, mi.nombre
            """, fetch=True) or []
        except:
            return []
    
    def obtener_mesas(self):
        """Obtener mesas con valores por defecto"""
        try:
            return self.db.ejecutar_consulta(
                "SELECT * FROM mesas ORDER BY numero", 
                fetch=True
            ) or []
        except:
            # Retornar mesas por defecto si hay error
            return [
                {'id': 1, 'numero': 1, 'capacidad': 4, 'estado': 'disponible'},
                {'id': 2, 'numero': 2, 'capacidad': 2, 'estado': 'disponible'}
            ]
