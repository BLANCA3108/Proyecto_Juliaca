import csv
import re
from collections import defaultdict

def convertir_a_wkt(tipo_geom, coords_str):
    """Convierte coordinates CSV a formato WKT"""
    if not coords_str or not tipo_geom:
        return None
    
    # Separar las coordenadas por comas
    coords_list = coords_str.split(',')
    
    # Agrupar de 2 en 2 (lon, lat)
    puntos = []
    for i in range(0, len(coords_list)-1, 2):
        try:
            lon = coords_list[i].strip()
            lat = coords_list[i+1].strip()
            puntos.append(f"{lon} {lat}")
        except:
            pass
    
    if not puntos:
        return None
    
    # Crear WKT según tipo
    if tipo_geom == "LineString":
        return f"LINESTRING({', '.join(puntos)})"
    elif tipo_geom == "Polygon":
        return f"POLYGON(({', '.join(puntos)}))"
    
    return None

def extraer_coordenadas_wkt(wkt):
    """Extrae todas las coordenadas de un LINESTRING"""
    match = re.search(r'LINESTRING\s*\((.*?)\)', wkt)
    if not match:
        return []
    
    coords_str = match.group(1)
    puntos = []
    
    for coord in coords_str.split(','):
        coord = coord.strip()
        if coord:
            partes = coord.split()
            if len(partes) >= 2:
                try:
                    lon = float(partes[0])
                    lat = float(partes[1])
                    puntos.append((lat, lon))
                except:
                    pass
    
    return puntos

def procesar_mapa_juliaca():
    """Procesa mapaJ.csv y genera nodos y aristas"""
    
    print("="*60)
    print("   PROCESADOR DE GEOMETRÍAS WKT")
    print("="*60 + "\n")
    
    # Mapas para nodos únicos
    coord_a_id = {}
    nodos = {}
    aristas = []
    siguiente_id = 0
    
    # Leer CSV
    with open('data/mapaJ.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        linea_num = 0
        procesadas = 0
        
        for row in reader:
            linea_num += 1
            
            # CORRECCIÓN: Obtener tipo y coordenadas de columnas separadas
            tipo_geom = row.get('geometry', '').strip()
            coords_raw = row.get('coordinates', '').strip()
            
            # Convertir a WKT válido
            geom_wkt = convertir_a_wkt(tipo_geom, coords_raw)
            
            if not geom_wkt or 'LINESTRING' not in geom_wkt:
                continue
            
            # Extraer info de la vía
            nombre = row.get('name', row.get('bridge:name', 'Sin nombre'))
            tipo_via = row.get('highway', 'unknown')
            
            # Calcular riesgo según tipo de vía
            riesgos_tipo = {
                'motorway': 70, 'trunk': 65, 'primary': 60,
                'secondary': 50, 'tertiary': 45, 'residential': 35,
                'service': 30, 'footway': 25, 'path': 40,
                'pedestrian': 20
            }
            riesgo_base = riesgos_tipo.get(tipo_via, 45)
            
            # Extraer coordenadas
            coords = extraer_coordenadas_wkt(geom_wkt)
            
            if len(coords) < 2:
                continue
            
            procesadas += 1
            
            # Procesar cada segmento
            for i in range(len(coords) - 1):
                lat1, lon1 = coords[i]
                lat2, lon2 = coords[i + 1]
                
                # Redondear para agrupar nodos cercanos
                lat1_r = round(lat1, 6)
                lon1_r = round(lon1, 6)
                lat2_r = round(lat2, 6)
                lon2_r = round(lon2, 6)
                
                # Obtener o crear IDs de nodos
                if (lat1_r, lon1_r) not in coord_a_id:
                    coord_a_id[(lat1_r, lon1_r)] = siguiente_id
                    # Nombre mejorado con nombre de calle
                    nombre_nodo = f"{nombre}" if nombre != 'Sin nombre' else f"Intersección {siguiente_id}"
                    nodos[siguiente_id] = {
                        'id': siguiente_id,
                        'lat': lat1,
                        'lon': lon1,
                        'nombre': nombre_nodo,
                        'riesgo': riesgo_base,
                        'tipo_via': tipo_via
                    }
                    siguiente_id += 1
                
                if (lat2_r, lon2_r) not in coord_a_id:
                    coord_a_id[(lat2_r, lon2_r)] = siguiente_id
                    nombre_nodo = f"{nombre}" if nombre != 'Sin nombre' else f"Intersección {siguiente_id}"
                    nodos[siguiente_id] = {
                        'id': siguiente_id,
                        'lat': lat2,
                        'lon': lon2,
                        'nombre': nombre_nodo,
                        'riesgo': riesgo_base,
                        'tipo_via': tipo_via
                    }
                    siguiente_id += 1
                
                id1 = coord_a_id[(lat1_r, lon1_r)]
                id2 = coord_a_id[(lat2_r, lon2_r)]
                
                # Calcular distancia (Haversine)
                import math
                R = 6371000  # Radio de la Tierra en metros
                
                lat1_rad = math.radians(lat1)
                lat2_rad = math.radians(lat2)
                dlat = math.radians(lat2 - lat1)
                dlon = math.radians(lon2 - lon1)
                
                a = (math.sin(dlat/2)**2 + 
                     math.cos(lat1_rad) * math.cos(lat2_rad) * 
                     math.sin(dlon/2)**2)
                c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
                distancia = R * c / 1000  # En kilómetros
                
                # Agregar arista
                aristas.append({
                    'origen': id1,
                    'destino': id2,
                    'distancia': round(distancia, 3),
                    'riesgo': riesgo_base,
                    'nombre': nombre
                })
            
            if linea_num % 100 == 0:
                print(f"📖 Procesadas {linea_num} líneas... ({procesadas} válidas)")
    
    print(f"\n✅ Procesamiento completado")
    print(f"   Líneas leídas: {linea_num}")
    print(f"   Líneas válidas: {procesadas}")
    print(f"   Nodos generados: {len(nodos)}")
    print(f"   Aristas generadas: {len(aristas)}")
    
    # Guardar nodos
    with open('data/nodos_juliaca.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['id', 'nombre', 'latitud', 'longitud', 'riesgo', 'tipo'])
        writer.writeheader()
        
        for nodo in nodos.values():
            writer.writerow({
                'id': nodo['id'],
                'nombre': nodo['nombre'],
                'latitud': nodo['lat'],
                'longitud': nodo['lon'],
                'riesgo': nodo['riesgo'],
                'tipo': 'interseccion'
            })
    
    print(f"\n✅ Guardado: data/nodos_juliaca.csv")
    
    # Guardar aristas
    with open('data/aristas_juliaca.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['origen', 'destino', 'distancia', 'riesgo', 'nombre'])
        writer.writeheader()
        writer.writerows(aristas)
    
    print(f"✅ Guardado: data/aristas_juliaca.csv")
    
    # Estadísticas
    print("\n📊 ESTADÍSTICAS:")
    print(f"   Total nodos: {len(nodos)}")
    print(f"   Total aristas: {len(aristas)}")
    
    # Contar conexiones por nodo
    conexiones = defaultdict(int)
    for arista in aristas:
        conexiones[arista['origen']] += 1
        conexiones[arista['destino']] += 1
    
    print(f"   Nodos conectados: {len(conexiones)}")
    print(f"   Nodos aislados: {len(nodos) - len(conexiones)}")
    
    if conexiones:
        max_conex = max(conexiones.values())
        print(f"   Máximo de conexiones: {max_conex}")

if __name__ == "__main__":
    procesar_mapa_juliaca()