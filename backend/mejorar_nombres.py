import csv
from collections import defaultdict

def mejorar_nombres_nodos():
    """
    Mejora los nombres de nodos agregando información de calles cercanas
    """
    
    print("🔧 Mejorando nombres de nodos...")
    
    # Cargar nodos actuales
    nodos = {}
    with open('data/nodos_juliaca.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            nodos[int(row['id'])] = row
    
    # Cargar aristas con nombres
    aristas_por_nodo = defaultdict(list)
    with open('data/aristas_juliaca.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            origen = int(row['origen'])
            destino = int(row['destino'])
            nombre = row.get('nombre', 'Sin nombre')
            
            if nombre != 'Sin nombre':
                aristas_por_nodo[origen].append(nombre)
                aristas_por_nodo[destino].append(nombre)
    
    # Mejorar nombres
    nodos_mejorados = []
    ubicaciones_importantes = defaultdict(int)
    
    for nodo_id, nodo_info in nodos.items():
        calles = aristas_por_nodo.get(nodo_id, [])
        
        if calles:
            # Obtener la calle más común
            contador_calles = defaultdict(int)
            for calle in calles:
                contador_calles[calle] += 1
            
            calle_principal = max(contador_calles.items(), key=lambda x: x[1])[0]
            
            # Limpiar nombre
            calle_principal = calle_principal.replace('Avenida', 'Av.').replace('Jirón', 'Jr.')
            
            # Crear nombre único
            ubicaciones_importantes[calle_principal] += 1
            numero = ubicaciones_importantes[calle_principal]
            
            if len(calles) > 1 and len(set(calles)) > 1:
                # Es una intersección
                calles_unicas = list(set(calles))[:2]
                calles_limpias = [c.replace('Avenida', 'Av.').replace('Jirón', 'Jr.') for c in calles_unicas]
                nombre_final = f"{calles_limpias[0]} ∩ {calles_limpias[1]}"
            else:
                # Es un punto en una calle
                nombre_final = f"{calle_principal} #{numero}"
        else:
            # Sin nombre, usar coordenadas
            lat = float(nodo_info['latitud'])
            lon = float(nodo_info['longitud'])
            nombre_final = f"Punto ({lat:.4f}, {lon:.4f})"
        
        nodos_mejorados.append({
            'id': nodo_id,
            'nombre': nombre_final,
            'latitud': nodo_info['latitud'],
            'longitud': nodo_info['longitud'],
            'riesgo': nodo_info['riesgo'],
            'tipo': nodo_info['tipo']
        })
    
    # Guardar nodos mejorados
    with open('data/nodos_juliaca.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['id', 'nombre', 'latitud', 'longitud', 'riesgo', 'tipo'])
        writer.writeheader()
        writer.writerows(nodos_mejorados)
    
    print(f"✅ {len(nodos_mejorados)} nodos actualizados con nombres mejorados")
    
    # Mostrar ejemplos
    print("\n📝 Ejemplos de nombres:")
    for i, nodo in enumerate(nodos_mejorados[:10]):
        print(f"   {nodo['nombre']}")

if __name__ == "__main__":
    mejorar_nombres_nodos()