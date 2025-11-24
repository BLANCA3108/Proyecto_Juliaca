"""
CARGADOR DE DATOS OSM - JULIACA
Procesa archivos .osm de OpenStreetMap y extrae información relevante
"""

import xml.etree.ElementTree as ET
import sqlite3
import math
from collections import defaultdict

class CargadorOSM:
    def __init__(self, archivo_osm, db_name='juliaca_seguridad.db'):
        self.archivo_osm = archivo_osm
        self.db_name = db_name
        self.nodos = {}
        self.vias = []
        self.zonas_importantes = []
        
    def calcular_distancia(self, lat1, lon1, lat2, lon2):
        """Calcula distancia en metros entre dos puntos (Haversine)"""
        R = 6371000  # Radio de la Tierra en metros
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_lat/2) ** 2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * 
             math.sin(delta_lon/2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c
    
    def cargar_osm(self):
        """Lee y parsea el archivo OSM"""
        print(f"\n📖 Leyendo archivo {self.archivo_osm}...")
        
        try:
            tree = ET.parse(self.archivo_osm)
            root = tree.getroot()
            
            # Extraer nodos
            for node in root.findall('node'):
                node_id = int(node.get('id'))
                lat = float(node.get('lat'))
                lon = float(node.get('lon'))
                
                tags = {}
                for tag in node.findall('tag'):
                    tags[tag.get('k')] = tag.get('v')
                
                self.nodos[node_id] = {
                    'lat': lat,
                    'lon': lon,
                    'tags': tags
                }
                
                # Identificar zonas importantes
                if 'name' in tags or 'amenity' in tags or 'highway' in tags:
                    self.zonas_importantes.append({
                        'id': node_id,
                        'nombre': tags.get('name', f'Nodo_{node_id}'),
                        'lat': lat,
                        'lon': lon,
                        'tipo': tags.get('amenity', tags.get('highway', 'unknown')),
                        'tags': tags
                    })
            
            print(f"✅ {len(self.nodos)} nodos cargados")
            print(f"✅ {len(self.zonas_importantes)} zonas importantes identificadas")
            
            # Extraer vías (ways)
            for way in root.findall('way'):
                way_id = int(way.get('id'))
                nodos_way = []
                tags_way = {}
                
                for nd in way.findall('nd'):
                    nodos_way.append(int(nd.get('ref')))
                
                for tag in way.findall('tag'):
                    tags_way[tag.get('k')] = tag.get('v')
                
                if 'highway' in tags_way:  # Solo vías importantes
                    self.vias.append({
                        'id': way_id,
                        'nodos': nodos_way,
                        'nombre': tags_way.get('name', f'Via_{way_id}'),
                        'tipo': tags_way.get('highway'),
                        'tags': tags_way
                    })
            
            print(f"✅ {len(self.vias)} vías cargadas")
            return True
            
        except FileNotFoundError:
            print(f"❌ Error: No se encontró el archivo {self.archivo_osm}")
            print("   Descarga el archivo desde:")
            print("   https://www.openstreetmap.org/export")
            print("   Busca 'Juliaca, Peru' y exporta el área")
            return False
        except Exception as e:
            print(f"❌ Error al procesar OSM: {e}")
            return False
    
    def integrar_a_bd(self):
        """Integra datos OSM con la base de datos existente"""
        print("\n🔄 Integrando datos OSM con la base de datos...")
        
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            # Agregar zonas importantes que no estén en la BD
            cursor.execute('SELECT MAX(id) FROM zonas')
            max_id = cursor.fetchone()[0] or 20
            
            nuevas_zonas = 0
            for zona in self.zonas_importantes[:20]:  # Limitar a 20 adicionales
                # Verificar si ya existe cerca
                cursor.execute('''
                    SELECT id FROM zonas 
                    WHERE ABS(lat - ?) < 0.001 AND ABS(lon - ?) < 0.001
                ''', (zona['lat'], zona['lon']))
                
                if not cursor.fetchone():
                    max_id += 1
                    riesgo = 40  # Riesgo base para zonas OSM
                    
                    cursor.execute('''
                        INSERT INTO zonas (id, nombre, lat, lon, riesgo_general, tipo_zona, descripcion)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (max_id, zona['nombre'], zona['lat'], zona['lon'], 
                          riesgo, zona['tipo'], 'Zona desde OSM'))
                    
                    nuevas_zonas += 1
            
            # Crear rutas desde las vías
            nuevas_rutas = 0
            cursor.execute('SELECT id, lat, lon FROM zonas')
            zonas_db = cursor.fetchall()
            
            for via in self.vias[:50]:  # Limitar procesamiento
                if len(via['nodos']) < 2:
                    continue
                
                # Tomar primer y último nodo
                nodo_inicio = via['nodos'][0]
                nodo_fin = via['nodos'][-1]
                
                if nodo_inicio not in self.nodos or nodo_fin not in self.nodos:
                    continue
                
                # Buscar zonas cercanas a estos nodos
                lat1, lon1 = self.nodos[nodo_inicio]['lat'], self.nodos[nodo_inicio]['lon']
                lat2, lon2 = self.nodos[nodo_fin]['lat'], self.nodos[nodo_fin]['lon']
                
                zona_origen = None
                zona_destino = None
                
                for z_id, z_lat, z_lon in zonas_db:
                    if not zona_origen and abs(z_lat - lat1) < 0.005 and abs(z_lon - lon1) < 0.005:
                        zona_origen = z_id
                    if not zona_destino and abs(z_lat - lat2) < 0.005 and abs(z_lon - lon2) < 0.005:
                        zona_destino = z_id
                
                if zona_origen and zona_destino and zona_origen != zona_destino:
                    distancia = self.calcular_distancia(lat1, lon1, lat2, lon2)
                    tiempo = int(distancia / 15)  # Aprox 15 m/min
                    riesgo_via = self.calcular_riesgo_via(via['tipo'])
                    
                    # Verificar si la ruta ya existe
                    cursor.execute('''
                        SELECT id FROM rutas 
                        WHERE origen_id = ? AND destino_id = ?
                    ''', (zona_origen, zona_destino))
                    
                    if not cursor.fetchone():
                        cursor.execute('''
                            INSERT INTO rutas (origen_id, destino_id, distancia, 
                                             tiempo_estimado, nivel_riesgo)
                            VALUES (?, ?, ?, ?, ?)
                        ''', (zona_origen, zona_destino, distancia/1000, tiempo, riesgo_via))
                        nuevas_rutas += 1
            
            conn.commit()
            print(f"✅ {nuevas_zonas} nuevas zonas agregadas")
            print(f"✅ {nuevas_rutas} nuevas rutas creadas")
            conn.close()
            
        except Exception as e:
            print(f"❌ Error al integrar datos: {e}")
    
    def calcular_riesgo_via(self, tipo_via):
        """Calcula nivel de riesgo según tipo de vía"""
        riesgos = {
            'motorway': 70,
            'trunk': 65,
            'primary': 60,
            'secondary': 50,
            'tertiary': 45,
            'residential': 35,
            'service': 30,
            'footway': 25,
            'path': 40
        }
        return riesgos.get(tipo_via, 45)
    
    def generar_reporte(self):
        """Genera reporte de datos cargados"""
        print("\n" + "="*50)
        print("📊 REPORTE DE DATOS OSM")
        print("="*50)
        
        print(f"\n📍 Total de nodos: {len(self.nodos)}")
        print(f"🛣️  Total de vías: {len(self.vias)}")
        print(f"⭐ Zonas importantes: {len(self.zonas_importantes)}")
        
        # Tipos de zonas
        tipos = defaultdict(int)
        for zona in self.zonas_importantes:
            tipos[zona['tipo']] += 1
        
        print("\n📌 Tipos de zonas identificadas:")
        for tipo, cantidad in sorted(tipos.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"   • {tipo}: {cantidad}")
        
        # Tipos de vías
        tipos_via = defaultdict(int)
        for via in self.vias:
            tipos_via[via['tipo']] += 1
        
        print("\n🛣️  Tipos de vías:")
        for tipo, cantidad in sorted(tipos_via.items(), key=lambda x: x[1], reverse=True):
            print(f"   • {tipo}: {cantidad}")
        
        print("="*50 + "\n")

# ============================================
# SCRIPT PRINCIPAL
# ============================================

if __name__ == "__main__":
    print("="*60)
    print("   CARGADOR DE DATOS OPENSTREETMAP - JULIACA")
    print("="*60)
    
    # Intentar cargar archivo OSM
    archivos_posibles = ['juliaca.osm', 'export.osm', 'map.osm']
    archivo_encontrado = None
    
    for archivo in archivos_posibles:
        try:
            with open(archivo):
                archivo_encontrado = archivo
                break
        except FileNotFoundError:
            continue
    
    if not archivo_encontrado:
        print("\n⚠️  No se encontró archivo OSM")
        print("\nPara obtener el archivo:")
        print("1. Ve a: https://www.openstreetmap.org/")
        print("2. Busca: 'Juliaca, Peru'")
        print("3. Click en 'Exportar' (arriba)")
        print("4. Selecciona el área y descarga")
        print("5. Guarda como 'juliaca.osm' en esta carpeta\n")
        
        print("Continuando sin datos OSM (usando solo datos simulados)...")
        input("\nPresiona ENTER para continuar...")
    else:
        cargador = CargadorOSM(archivo_encontrado)
        
        if cargador.cargar_osm():
            cargador.generar_reporte()
            cargador.integrar_a_bd()
            print("\n✅ ¡Integración OSM completada!")
        
        input("\nPresiona ENTER para continuar...")