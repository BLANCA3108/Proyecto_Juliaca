from flask import Flask, jsonify, request
from flask_cors import CORS
from dijkstra import GrafoDijkstra
import json

app = Flask(__name__)
CORS(app)  # Permite que JavaScript se conecte

# Cargar grafo al iniciar
print("🔄 Cargando grafo...")
grafo = GrafoDijkstra()
grafo.cargar_desde_csv()
print("✅ API lista\n")

@app.route('/api/nodos', methods=['GET'])
def obtener_nodos():
    """Devuelve todos los nodos"""
    return jsonify({
        'success': True,
        'nodos': grafo.nodos
    })

@app.route('/api/ruta', methods=['POST'])
def calcular_ruta():
    """Calcula ruta entre dos puntos"""
    data = request.get_json()
    origen = int(data.get('origen'))
    destino = int(data.get('destino'))
    
    print(f"📍 Calculando ruta: {origen} → {destino}")
    
    resultado = grafo.calcular_ruta(origen, destino)
    
    if resultado:
        return jsonify({
            'success': True,
            'ruta': resultado
        })
    else:
        return jsonify({
            'success': False,
            'error': 'No se encontró ruta'
        }), 404

@app.route('/api/test', methods=['GET'])
def test():
    """Endpoint de prueba"""
    return jsonify({
        'success': True,
        'message': 'API funcionando correctamente',
        'total_nodos': len(grafo.nodos)
    })

@app.route('/api/aristas', methods=['GET'])
def obtener_aristas():
    """Devuelve todas las aristas para dibujar en canvas"""
    import csv
    
    aristas = []
    
    with open('data/aristas_juliaca.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            origen_id = int(row['origen'])
            destino_id = int(row['destino'])
            
            if origen_id in grafo.nodos and destino_id in grafo.nodos:
                aristas.append({
                    'origen': {
                        'id': origen_id,
                        'lat': grafo.nodos[origen_id]['lat'],
                        'lon': grafo.nodos[origen_id]['lon']
                    },
                    'destino': {
                        'id': destino_id,
                        'lat': grafo.nodos[destino_id]['lat'],
                        'lon': grafo.nodos[destino_id]['lon']
                    },
                    'riesgo': int(row['riesgo'])
                })
    
    return jsonify({
        'success': True,
        'aristas': aristas,
        'total': len(aristas)
    })
if __name__ == '__main__':
    print("="*50)
    print("🚀 API HEATMAP JULIACA")
    print("="*50)
    print("📡 Servidor corriendo en: http://localhost:5000")
    print("🔗 Prueba: http://localhost:5000/api/test")
    print("="*50 + "\n")
    
    app.run(debug=True, port=5000)