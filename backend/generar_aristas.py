import csv
import math
from collections import defaultdict

def calcular_distancia(lat1, lon1, lat2, lon2):
    """Haversine en kilómetros"""
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    
    a = (math.sin(dlat/2)**2 + 
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
         math.sin(dlon/2)**2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c

def generar_aristas_automaticas():
    """Genera conexiones entre nodos cercanos"""
    
    # Cargar nodos
    nodos = {}
    with open('data/nodos_juliaca.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            nodo_id = int(row['id'])
            nodos[nodo_id] = {
                'nombre': row['nombre'],
                'lat': float(row['latitud']),
                'lon': float(row['longitud']),
                'riesgo': int(row['riesgo'])
            }
    
    print(f"✅ {len(nodos)} nodos cargados")
    
    # Cargar aristas existentes
    aristas_existentes = set()
    aristas = []
    
    try:
        with open('data/aristas_juliaca.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                origen = int(row['origen'])
                destino = int(row['destino'])
                aristas_existentes.add((min(origen, destino), max(origen, destino)))
                aristas.append(row)
        print(f"✅ {len(aristas)} aristas existentes")
    except:
        print("⚠️  No hay aristas previas")
    
    # Generar nuevas conexiones
    nuevas = 0
    
    for id1 in nodos:
        for id2 in nodos:
            if id1 >= id2:
                continue
            
            # Verificar si ya existe
            if (id1, id2) in aristas_existentes:
                continue
            
            n1 = nodos[id1]
            n2 = nodos[id2]
            
            # Calcular distancia
            dist = calcular_distancia(n1['lat'], n1['lon'], n2['lat'], n2['lon'])
            
            # Solo conectar si están cerca (<= 2 km)
            if dist <= 2.0:
                riesgo_promedio = (n1['riesgo'] + n2['riesgo']) // 2
                
                aristas.append({
                    'origen': id1,
                    'destino': id2,
                    'distancia': round(dist, 3),
                    'riesgo': riesgo_promedio
                })
                
                nuevas += 1
    
    # Guardar todas las aristas
    with open('data/aristas_juliaca.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['origen', 'destino', 'distancia', 'riesgo'])
        writer.writeheader()
        writer.writerows(aristas)
    
    print(f"✅ {nuevas} nuevas aristas generadas")
    print(f"✅ Total: {len(aristas)} aristas")
    print("\n📊 CONEXIONES POR NODO:")
    
    # Contar conexiones
    conexiones = defaultdict(int)
    for arista in aristas:
        conexiones[int(arista['origen'])] += 1
        conexiones[int(arista['destino'])] += 1
    
    for nodo_id in sorted(conexiones.keys()):
        nombre = nodos[nodo_id]['nombre'][:30]
        print(f"  Nodo {nodo_id:2d}: {conexiones[nodo_id]:2d} conexiones - {nombre}")

if __name__ == "__main__":
    print("="*60)
    print("   GENERADOR DE ARISTAS AUTOMÁTICO")
    print("="*60 + "\n")
    
    generar_aristas_automaticas()
    
    print("\n✅ Proceso completado")
    print("📝 Archivo actualizado: data/aristas_juliaca.csv")