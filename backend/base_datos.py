"""
SISTEMA DE BASE DE DATOS - JULIACA
Maneja toda la información de zonas, incidentes y estadísticas
"""

import sqlite3
import csv
from datetime import datetime, timedelta
import random
import os

class BaseDatosJuliaca:
    def __init__(self, nombre_db='juliaca_seguridad.db'):
        """Inicializa la conexión a la base de datos"""
        self.nombre_db = nombre_db
        self.conn = None
        self.conectar()
        self.crear_tablas()
    
    def conectar(self):
        """Establece conexión con SQLite"""
        try:
            self.conn = sqlite3.connect(self.nombre_db)
            print(f"✅ Conexión exitosa a {self.nombre_db}")
        except sqlite3.Error as e:
            print(f"❌ Error al conectar: {e}")
    
    def crear_tablas(self):
        """Crea las tablas necesarias si no existen"""
        cursor = self.conn.cursor()
        
        # Tabla de Zonas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS zonas (
                id INTEGER PRIMARY KEY,
                nombre TEXT NOT NULL,
                lat REAL NOT NULL,
                lon REAL NOT NULL,
                riesgo_general INTEGER DEFAULT 30,
                tipo_zona TEXT,
                descripcion TEXT,
                poblacion INTEGER,
                ultima_actualizacion TEXT
            )
        ''')
        
        # Tabla de Incidentes
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS incidentes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                zona_id INTEGER,
                tipo TEXT NOT NULL,
                subtipo TEXT,
                hora INTEGER,
                dia_semana INTEGER,
                descripcion TEXT,
                fecha TEXT,
                gravedad INTEGER,
                FOREIGN KEY (zona_id) REFERENCES zonas(id)
            )
        ''')
        
        # Tabla de Zonas Rojas (Trata de personas)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS zonas_rojas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                zona_id INTEGER,
                nivel_riesgo TEXT,
                horario_critico_inicio INTEGER,
                horario_critico_fin INTEGER,
                descripcion_riesgo TEXT,
                medidas_seguridad TEXT,
                FOREIGN KEY (zona_id) REFERENCES zonas(id)
            )
        ''')
        
        # Tabla de Rutas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rutas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                origen_id INTEGER,
                destino_id INTEGER,
                distancia REAL,
                tiempo_estimado INTEGER,
                nivel_riesgo INTEGER,
                FOREIGN KEY (origen_id) REFERENCES zonas(id),
                FOREIGN KEY (destino_id) REFERENCES zonas(id)
            )
        ''')
        
        # Tabla de Reportes de Usuarios (para futuro)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reportes_usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                zona_id INTEGER,
                tipo_reporte TEXT,
                descripcion TEXT,
                fecha_hora TEXT,
                verificado INTEGER DEFAULT 0,
                FOREIGN KEY (zona_id) REFERENCES zonas(id)
            )
        ''')
        
        self.conn.commit()
        print("✅ Tablas creadas/verificadas correctamente")
    
    def cargar_datos_juliaca(self):
        """Carga datos reales y simulados de Juliaca"""
        cursor = self.conn.cursor()
        
        # Verificar si ya hay datos
        cursor.execute('SELECT COUNT(*) FROM zonas')
        if cursor.fetchone()[0] > 0:
            print("ℹ️  Ya existen datos en la base de datos")
            respuesta = input("¿Deseas recargar los datos? (s/n): ")
            if respuesta.lower() != 's':
                return
            # Limpiar tablas
            cursor.execute('DELETE FROM incidentes')
            cursor.execute('DELETE FROM zonas_rojas')
            cursor.execute('DELETE FROM rutas')
            cursor.execute('DELETE FROM zonas')
        
        print("\n📊 Cargando datos de Juliaca...")
        
        # ZONAS REALES DE JULIACA (basadas en OpenStreetMap)
        zonas_juliaca = [
            # Centro
            (1, "Plaza de Armas", -15.5000, -70.1333, 45, "centro_historico", 
             "Centro neurálgico de Juliaca", 5000, datetime.now().isoformat()),
            
            (2, "Terminal Terrestre", -15.4800, -70.1200, 75, "transporte",
             "Principal terminal de buses interprovinciales", 8000, datetime.now().isoformat()),
            
            (3, "Mercado Santa Bárbara", -15.4950, -70.1280, 65, "comercio",
             "Mercado principal de abastos", 12000, datetime.now().isoformat()),
            
            (4, "Mercado Túpac Amaru", -15.4920, -70.1300, 68, "comercio",
             "Mercado de productos andinos", 9000, datetime.now().isoformat()),
            
            # Educación
            (5, "Universidad Andina Néstor Cáceres Velásquez", -15.4700, -70.1400, 30, "educacion",
             "Principal universidad de la región", 15000, datetime.now().isoformat()),
            
            (6, "Universidad Peruana Unión", -15.4650, -70.1450, 28, "educacion",
             "Campus universitario", 8000, datetime.now().isoformat()),
            
            # Carreteras
            (7, "Salida a Puno", -15.5200, -70.1150, 80, "carretera",
             "Carretera Juliaca-Puno, zona de asaltos", 3000, datetime.now().isoformat()),
            
            (8, "Salida a Arequipa", -15.4600, -70.1100, 75, "carretera",
             "Vía principal hacia Arequipa", 4000, datetime.now().isoformat()),
            
            # Industrial/Comercial
            (9, "Zona Industrial", -15.4600, -70.1500, 55, "industrial",
             "Área de fábricas y almacenes", 6000, datetime.now().isoformat()),
            
            (10, "Centro Comercial Real Plaza", -15.4850, -70.1320, 40, "comercio",
             "Principal centro comercial", 10000, datetime.now().isoformat()),
            
            # Zonas Residenciales
            (11, "Barrio Chilla", -15.4900, -70.1250, 50, "residencial",
             "Barrio residencial", 7000, datetime.now().isoformat()),
            
            (12, "Barrio San José", -15.4880, -70.1380, 48, "residencial",
             "Zona residencial", 6500, datetime.now().isoformat()),
            
            (13, "Urbanización San Santiago", -15.4750, -70.1350, 35, "residencial",
             "Urbanización moderna", 5000, datetime.now().isoformat()),
            
            # Zonas Críticas/Rojas
            (14, "Jr. Mariano Núñez (Zona Roja)", -15.4980, -70.1310, 85, "zona_roja",
             "Zona de prostitución, alto riesgo de trata", 2000, datetime.now().isoformat()),
            
            (15, "Jr. San Román (Zona Roja)", -15.4990, -70.1290, 82, "zona_roja",
             "Zona de bares y prostíbulos", 1800, datetime.now().isoformat()),
            
            # Transporte
            (16, "Av. Circunvalación Norte", -15.4850, -70.1350, 60, "avenida",
             "Avenida principal con alto tráfico", 8000, datetime.now().isoformat()),
            
            (17, "Av. Huancané", -15.4920, -70.1330, 58, "avenida",
             "Avenida comercial", 7500, datetime.now().isoformat()),
            
            # Otros
            (18, "Aeropuerto Inca Manco Cápac", -15.4670, -70.1580, 35, "aeropuerto",
             "Aeropuerto internacional", 5000, datetime.now().isoformat()),
            
            (19, "Estadio Guillermo Briceño", -15.4880, -70.1270, 45, "deportivo",
             "Estadio municipal", 4000, datetime.now().isoformat()),
            
            (20, "Hospital Carlos Monge Medrano", -15.4910, -70.1340, 42, "salud",
             "Principal hospital de Juliaca", 6000, datetime.now().isoformat())
        ]
        
        cursor.executemany('''
            INSERT INTO zonas (id, nombre, lat, lon, riesgo_general, tipo_zona, 
                             descripcion, poblacion, ultima_actualizacion)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', zonas_juliaca)
        
        print(f"✅ {len(zonas_juliaca)} zonas cargadas")
        
        # INCIDENTES SIMULADOS (basados en patrones reales)
        print("📋 Generando incidentes...")
        
        tipos_incidentes = {
            'robo': ['asalto_mano_armada', 'robo_celular', 'robo_cartera', 'asalto_bus'],
            'hurto': ['carterista', 'robo_tienda', 'hurto_vehiculo'],
            'accidente': ['choque', 'atropello', 'volcadura'],
            'trata': ['captacion', 'explotacion', 'intento_secuestro'],
            'trafico': ['congestion', 'accidente_menor'],
            'violencia': ['agresion', 'riña', 'violencia_familiar']
        }
        
        incidentes = []
        fecha_base = datetime.now() - timedelta(days=90)  # Últimos 3 meses
        
        # Generar incidentes por zona según su nivel de riesgo
        for zona in zonas_juliaca:
            zona_id = zona[0]
            riesgo = zona[4]
            tipo_zona = zona[5]
            
            # Más incidentes en zonas de mayor riesgo
            num_incidentes = int((riesgo / 10) * random.uniform(0.8, 1.5))
            
            for _ in range(num_incidentes):
                # Tipo de incidente según zona
                if tipo_zona == 'zona_roja':
                    tipo = random.choice(['trata', 'robo', 'violencia'])
                elif tipo_zona == 'transporte':
                    tipo = random.choice(['robo', 'hurto', 'accidente'])
                elif tipo_zona == 'comercio':
                    tipo = random.choice(['hurto', 'robo'])
                elif tipo_zona == 'carretera':
                    tipo = random.choice(['robo', 'accidente'])
                else:
                    tipo = random.choice(list(tipos_incidentes.keys()))
                
                subtipo = random.choice(tipos_incidentes[tipo])
                
                # Hora del incidente (más incidentes en noche)
                if tipo in ['robo', 'trata', 'violencia']:
                    hora = random.choices(
                        range(24),
                        weights=[2]*6 + [1]*6 + [1]*6 + [5]*6  # Más en la noche
                    )[0]
                else:
                    hora = random.randint(0, 23)
                
                dia_semana = random.randint(0, 6)
                gravedad = random.randint(1, 10)
                
                fecha = fecha_base + timedelta(days=random.randint(0, 90))
                
                descripcion = f"{subtipo.replace('_', ' ').title()} en {zona[1]}"
                
                incidentes.append((
                    zona_id, tipo, subtipo, hora, dia_semana,
                    descripcion, fecha.isoformat(), gravedad
                ))
        
        cursor.executemany('''
            INSERT INTO incidentes (zona_id, tipo, subtipo, hora, dia_semana,
                                   descripcion, fecha, gravedad)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', incidentes)
        
        print(f"✅ {len(incidentes)} incidentes generados")
        
        # ZONAS ROJAS - Información detallada
        zonas_rojas_data = [
            (14, "CRITICO", 20, 4, 
             "Alta concentración de prostíbulos, riesgo de trata y explotación sexual. Presencia de mafias.",
             "Evitar transitar solo/a. Llamar al 105 ante actividad sospechosa. No aceptar bebidas de desconocidos."),
            
            (15, "ALTO", 21, 5,
             "Zona de bares clandestinos, riesgo de captación para trata. Menores en situación de riesgo.",
             "Transitar en grupo. Evitar horarios nocturnos. Denunciar presencia de menores.")
        ]
        
        cursor.executemany('''
            INSERT INTO zonas_rojas (zona_id, nivel_riesgo, horario_critico_inicio,
                                    horario_critico_fin, descripcion_riesgo, medidas_seguridad)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', zonas_rojas_data)
        
        print(f"✅ {len(zonas_rojas_data)} zonas rojas registradas")
        
        # RUTAS - Conexiones entre zonas
        print("🛣️  Generando rutas...")
        rutas = [
            (1, 2, 2.5, 10, 60),   # Plaza - Terminal
            (1, 3, 1.2, 5, 55),    # Plaza - Mercado Santa Bárbara
            (1, 10, 1.5, 7, 45),   # Plaza - Real Plaza
            (2, 7, 3.0, 12, 75),   # Terminal - Salida Puno
            (3, 4, 0.8, 4, 60),    # Mercado Santa Bárbara - Túpac Amaru
            (5, 6, 2.0, 8, 25),    # UANCV - UPeU
            (10, 16, 1.0, 5, 50),  # Real Plaza - Circunvalación
            (14, 15, 0.5, 3, 85),  # Zona Roja - Zona Roja
            (18, 8, 5.0, 15, 40),  # Aeropuerto - Salida Arequipa
        ]
        
        cursor.executemany('''
            INSERT INTO rutas (origen_id, destino_id, distancia, tiempo_estimado, nivel_riesgo)
            VALUES (?, ?, ?, ?, ?)
        ''', rutas)
        
        print(f"✅ {len(rutas)} rutas creadas")
        
        self.conn.commit()
        print("\n✅ ¡Base de datos cargada completamente!")
        self.mostrar_resumen()
    
    def mostrar_resumen(self):
        """Muestra un resumen de los datos en la BD"""
        cursor = self.conn.cursor()
        
        print("\n" + "="*50)
        print("📊 RESUMEN DE LA BASE DE DATOS")
        print("="*50)
        
        cursor.execute('SELECT COUNT(*) FROM zonas')
        print(f"🗺️  Zonas registradas: {cursor.fetchone()[0]}")
        
        cursor.execute('SELECT COUNT(*) FROM incidentes')
        print(f"📋 Incidentes registrados: {cursor.fetchone()[0]}")
        
        cursor.execute('SELECT COUNT(*) FROM zonas_rojas')
        print(f"🔴 Zonas rojas: {cursor.fetchone()[0]}")
        
        cursor.execute('SELECT COUNT(*) FROM rutas')
        print(f"🛣️  Rutas mapeadas: {cursor.fetchone()[0]}")
        
        # Top 5 zonas más peligrosas
        cursor.execute('''
            SELECT z.nombre, z.riesgo_general, COUNT(i.id) as incidentes
            FROM zonas z
            LEFT JOIN incidentes i ON z.id = i.zona_id
            GROUP BY z.id
            ORDER BY z.riesgo_general DESC
            LIMIT 5
        ''')
        
        print("\n⚠️  TOP 5 ZONAS MÁS PELIGROSAS:")
        for i, (nombre, riesgo, inc) in enumerate(cursor.fetchall(), 1):
            print(f"   {i}. {nombre}: Riesgo {riesgo}/100 ({inc} incidentes)")
        
        print("="*50 + "\n")
    
    def exportar_csv(self, tabla, archivo):
        """Exporta una tabla a CSV"""
        cursor = self.conn.cursor()
        cursor.execute(f'SELECT * FROM {tabla}')
        
        with open(archivo, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([desc[0] for desc in cursor.description])
            writer.writerows(cursor.fetchall())
        
        print(f"✅ Tabla '{tabla}' exportada a {archivo}")
    
    def cerrar(self):
        """Cierra la conexión"""
        if self.conn:
            self.conn.close()
            print("✅ Conexión cerrada")

# ============================================
# SCRIPT PRINCIPAL PARA CREAR LA BD
# ============================================

if __name__ == "__main__":
    print("="*60)
    print("   SISTEMA DE BASE DE DATOS - JULIACA")
    print("   Proyecto de Seguridad Ciudadana")
    print("="*60 + "\n")
    
    # Crear base de datos
    db = BaseDatosJuliaca()
    
    # Cargar datos
    db.cargar_datos_juliaca()
    
    # Exportar datos (opcional)
    print("\n¿Deseas exportar los datos a CSV? (s/n): ", end="")
    if input().lower() == 's':
        db.exportar_csv('zonas', 'zonas_juliaca.csv')
        db.exportar_csv('incidentes', 'incidentes_juliaca.csv')
    
    db.cerrar()
    
    print("\n✅ ¡Proceso completado!")
    print("📁 Archivo generado: juliaca_seguridad.db")
    input("\nPresiona ENTER para salir...")