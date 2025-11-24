import sqlite3
import csv

def exportar_a_csv():
    """Exporta zonas y rutas de SQLite a CSV"""
    conn = sqlite3.connect('data/juliaca_seguridad.db')
    cursor = conn.cursor()
    
    # Exportar NODOS
    print("📊 Exportando nodos...")
    cursor.execute('SELECT id, nombre, lat, lon, riesgo_general, tipo_zona FROM zonas')
    
    with open('data/nodos_juliaca.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['id', 'nombre', 'latitud', 'longitud', 'riesgo', 'tipo'])
        writer.writerows(cursor.fetchall())
    
    print("✅ nodos_juliaca.csv generado")
    
    # Exportar ARISTAS (rutas)
    print("📊 Exportando aristas...")
    cursor.execute('SELECT origen_id, destino_id, distancia, nivel_riesgo FROM rutas')
    
    with open('data/aristas_juliaca.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['origen', 'destino', 'distancia', 'riesgo'])
        writer.writerows(cursor.fetchall())
    
    print("✅ aristas_juliaca.csv generado")
    
    conn.close()
    print("\n✅ EXPORTACIÓN COMPLETA")

if __name__ == "__main__":
    exportar_a_csv()