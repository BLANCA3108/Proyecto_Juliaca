import heapq
import csv

class GrafoDijkstra:
    def __init__(self):
        self.nodos = {}
        self.grafo = {}
    
    def cargar_desde_csv(self):
        """Carga nodos y aristas desde CSV"""
        # Cargar nodos
        with open('data/nodos_juliaca.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                nodo_id = int(row['id'])
                self.nodos[nodo_id] = {
                    'nombre': row['nombre'],
                    'lat': float(row['latitud']),
                    'lon': float(row['longitud']),
                    'riesgo': int(row['riesgo'])
                }
                self.grafo[nodo_id] = []
        
        print(f"✅ {len(self.nodos)} nodos cargados")
        
        # Cargar aristas
        with open('data/aristas_juliaca.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                origen = int(row['origen'])
                destino = int(row['destino'])
                distancia = float(row['distancia'])
                riesgo = int(row['riesgo'])
                
                # Peso combinado: distancia + riesgo
                peso = distancia + (riesgo * 0.1)
                
                self.grafo[origen].append((destino, peso))
                self.grafo[destino].append((origen, peso))  # Bidireccional
        
        print(f"✅ Grafo construido")
    
    def calcular_ruta(self, origen, destino):
        """Dijkstra: encuentra la ruta más segura"""
        if origen not in self.grafo or destino not in self.grafo:
            return None
        
        distancias = {nodo: float('inf') for nodo in self.nodos}
        distancias[origen] = 0
        padres = {nodo: None for nodo in self.nodos}
        
        cola = [(0, origen)]
        visitados = set()
        
        while cola:
            dist_actual, nodo_actual = heapq.heappop(cola)
            
            if nodo_actual in visitados:
                continue
            
            visitados.add(nodo_actual)
            
            if nodo_actual == destino:
                break
            
            for vecino, peso in self.grafo[nodo_actual]:
                distancia = dist_actual + peso
                
                if distancia < distancias[vecino]:
                    distancias[vecino] = distancia
                    padres[vecino] = nodo_actual
                    heapq.heappush(cola, (distancia, vecino))
        
        # Reconstruir camino
        camino = []
        nodo = destino
        while nodo is not None:
            camino.append(nodo)
            nodo = padres[nodo]
        
        camino.reverse()
        
        if camino[0] != origen:
            return None
        
        # Calcular métricas
        riesgo_total = sum(self.nodos[n]['riesgo'] for n in camino)
        riesgo_promedio = riesgo_total / len(camino)
        
        return {
            'camino': camino,
            'nodos': [self.nodos[n] for n in camino],
            'distancia_total': distancias[destino],
            'riesgo_promedio': riesgo_promedio
        }

# Prueba rápida
if __name__ == "__main__":
    grafo = GrafoDijkstra()
    grafo.cargar_desde_csv()
    
    # Prueba: Plaza de Armas (1) → Terminal (2)
    ruta = grafo.calcular_ruta(1, 2)
    
    if ruta:
        print("\n✅ RUTA ENCONTRADA:")
        for i, nodo in enumerate(ruta['nodos'], 1):
            print(f"  {i}. {nodo['nombre']} (Riesgo: {nodo['riesgo']})")
        print(f"\n  Distancia ponderada: {ruta['distancia_total']:.2f}")
        print(f"  Riesgo promedio: {ruta['riesgo_promedio']:.1f}/100")
    else:
        print("❌ No se encontró ruta")