import sqlite3
from datetime import datetime

class BaseDatos:
    def __init__(self, nombre_db="db/batalla_naval.db"):
        """Inicializa la conexión a la base de datos y crea las tablas si no existen."""
        try:
            self.conexion = sqlite3.connect(nombre_db)
            self.cursor = self.conexion.cursor()
            self.crear_tablas()
        except sqlite3.Error as e:
            print(f"Error al conectar con la base de datos: {e}")

    def crear_tablas(self):
        """Crea las tablas necesarias para almacenar los resultados."""
        try:
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS jugadores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL,
                    puntuacion INTEGER NOT NULL,
                    disparos_usados INTEGER NOT NULL,
                    fecha TEXT NOT NULL
                )
            ''')
            self.conexion.commit()
        except sqlite3.Error as e:
            print(f"Error al crear las tablas: {e}")

    def guardar_resultados(self, nombre, puntuacion, disparos_usados):
        """Guarda un resultado en la tabla 'jugadores'."""
        try:
            fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.cursor.execute('''
                INSERT INTO jugadores (nombre, puntuacion, disparos_usados, fecha)
                VALUES (?, ?, ?, ?)
            ''', (nombre, puntuacion, disparos_usados, fecha_actual))
            self.conexion.commit()
        except sqlite3.Error as e:
            print(f"Error al guardar los resultados: {e}")

    def obtener_mejores_resultados(self, limite=3):
        """Obtiene los mejores resultados basados en una métrica de eficiencia."""
        try:
            self.cursor.execute('''
                SELECT nombre, puntuacion, disparos_usados, fecha,
                    CAST(puntuacion AS FLOAT) / disparos_usados AS eficiencia
                FROM jugadores
                ORDER BY eficiencia DESC
                LIMIT ?
            ''', (limite,))
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error al obtener los mejores resultados: {e}")
            return []

    def cerrar_conexion(self):
        """Cierra la conexión a la base de datos."""
        try:
            if self.conexion:
                self.conexion.close()
        except sqlite3.Error as e:
            print(f"Error al cerrar la conexión: {e}")
