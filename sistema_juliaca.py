
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import sqlite3
import math
from collections import defaultdict
import heapq
from datetime import datetime
import random

# ============================================
# ESTRUCTURAS DE DATOS
# ============================================

class NodoArbol:
    def __init__(self, zona_id, nombre, riesgo):
        self.zona_id = zona_id
        self.nombre = nombre
        self.riesgo = riesgo
        self.izq = None
        self.der = None

class ArbolRiesgo:
    def __init__(self):
        self.raiz = None
    
    def insertar(self, zona_id, nombre, riesgo):
        if not self.raiz:
            self.raiz = NodoArbol(zona_id, nombre, riesgo)
        else:
            self._insertar_recursivo(self.raiz, zona_id, nombre, riesgo)
    
    def _insertar_recursivo(self, nodo, zona_id, nombre, riesgo):
        if riesgo < nodo.riesgo:
            if nodo.izq is None:
                nodo.izq = NodoArbol(zona_id, nombre, riesgo)
            else:
                self._insertar_recursivo(nodo.izq, zona_id, nombre, riesgo)
        else:
            if nodo.der is None:
                nodo.der = NodoArbol(zona_id, nombre, riesgo)
            else:
                self._insertar_recursivo(nodo.der, zona_id, nombre, riesgo)
    
    def buscar_por_rango(self, min_riesgo, max_riesgo):
        resultado = []
        self._buscar_rango_recursivo(self.raiz, min_riesgo, max_riesgo, resultado)
        return resultado
    
    def _buscar_rango_recursivo(self, nodo, min_r, max_r, resultado):
        if not nodo:
            return
        if min_r <= nodo.riesgo <= max_r:
            resultado.append((nodo.zona_id, nodo.nombre, nodo.riesgo))
        if min_r < nodo.riesgo:
            self._buscar_rango_recursivo(nodo.izq, min_r, max_r, resultado)
        if max_r > nodo.riesgo:
            self._buscar_rango_recursivo(nodo.der, min_r, max_r, resultado)

class MatrizDispersa:
    def __init__(self):
        self.datos = defaultdict(lambda: defaultdict(int))
    
    def agregar(self, zona, hora, cantidad=1):
        self.datos[zona][hora] += cantidad
    
    def obtener(self, zona, hora):
        return self.datos[zona].get(hora, 0)
    
    def horas_peligrosas(self, zona, umbral=2):
        if zona not in self.datos:
            return []
        return [(h, c) for h, c in self.datos[zona].items() if c >= umbral]

class GrafoRutas:
    def __init__(self):
        self.grafo = defaultdict(list)
        self.nodos = {}
    
    def agregar_nodo(self, id_nodo, nombre, x, y, riesgo):
        self.nodos[id_nodo] = {
            'nombre': nombre,
            'x': x,
            'y': y,
            'riesgo': riesgo
        }
    
    def agregar_arista(self, origen, destino, riesgo):
        if origen in self.nodos and destino in self.nodos:
            x1, y1 = self.nodos[origen]['x'], self.nodos[origen]['y']
            x2, y2 = self.nodos[destino]['x'], self.nodos[destino]['y']
            distancia = math.sqrt((x2-x1)**2 + (y2-y1)**2)
            peso = distancia + (riesgo * 5)
            self.grafo[origen].append((destino, peso, riesgo))
            self.grafo[destino].append((origen, peso, riesgo))
    
    def dijkstra(self, inicio, fin):
        if inicio not in self.nodos or fin not in self.nodos:
            return None, float('inf')
        
        distancias = {nodo: float('inf') for nodo in self.nodos}
        distancias[inicio] = 0
        padres = {nodo: None for nodo in self.nodos}
        visitados = set()
        pq = [(0, inicio)]
        
        while pq:
            dist_actual, nodo_actual = heapq.heappop(pq)
            if nodo_actual in visitados:
                continue
            visitados.add(nodo_actual)
            if nodo_actual == fin:
                break
            
            for vecino, peso, _ in self.grafo[nodo_actual]:
                distancia = dist_actual + peso
                if distancia < distancias[vecino]:
                    distancias[vecino] = distancia
                    padres[vecino] = nodo_actual
                    heapq.heappush(pq, (distancia, vecino))
        
        camino = []
        nodo = fin
        while nodo is not None:
            camino.append(nodo)
            nodo = padres[nodo]
        camino.reverse()
        
        if not camino or camino[0] != inicio:
            return None, float('inf')
        
        return camino, distancias[fin]

# ============================================
# SISTEMA PRINCIPAL
# ============================================

class SistemaJuliaca:
    def __init__(self, root):
        self.root = root
        self.root.title(" Sistema de Seguridad Vial - Juliaca")
        self.root.geometry("1400x900")
        self.root.configure(bg='#0a0e27')
        
        # Conectar BD
        self.db_name = 'juliaca_seguridad.db'
        self.conn = None
        self.conectar_db()
        
        # Estructuras de datos
        self.arbol_riesgo = ArbolRiesgo()
        self.matriz_dispersa = MatrizDispersa()
        self.grafo = GrafoRutas()
        
        # Variables de mapa
        self.zoom = 1.0
        self.offset_x = 0
        self.offset_y = 0
        self.dragging = False
        self.last_x = 0
        self.last_y = 0
        self.zonas_posiciones = {}
        
        # Cargar datos
        self.cargar_estructuras()
        self.crear_interfaz()
    
    def conectar_db(self):
        try:
            self.conn = sqlite3.connect(self.db_name)
            print("✅ Conectado a BD")
        except Exception as e:
            print(f"❌ Error BD: {e}")
    
    def cargar_estructuras(self):
        if not self.conn:
            return
        
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM zonas')
        zonas = cursor.fetchall()
        
        # Crear layout del mapa (posiciones simplificadas)
        self.crear_layout_mapa(zonas)
        
        for zona in zonas:
            zona_id = zona[0]
            self.arbol_riesgo.insertar(zona_id, zona[1], zona[4])
            
            # Agregar al grafo con posiciones simplificadas
            if zona_id in self.zonas_posiciones:
                pos = self.zonas_posiciones[zona_id]
                self.grafo.agregar_nodo(zona_id, zona[1], pos['x'], pos['y'], zona[4])
        
        # Cargar matriz dispersa
        cursor.execute('SELECT zona_id, hora FROM incidentes')
        for zona_id, hora in cursor.fetchall():
            self.matriz_dispersa.agregar(zona_id, hora)
        
        # Crear conexiones del grafo
        self.crear_conexiones_grafo()
        
        print("✅ Estructuras cargadas")
    
    def crear_layout_mapa(self, zonas):
        """Crea un layout circular/radial de las zonas"""
        # Centro del mapa
        centro_x = 400
        centro_y = 300
        
        # Zonas principales en el centro (Plaza, Terminal, Mercados)
        zonas_centro = [1, 2, 3, 4, 10]  # IDs de zonas centrales
        
        # Posicionar zonas
        for i, zona in enumerate(zonas):
            zona_id = zona[0]
            
            if zona_id in zonas_centro:
                # Zonas del centro en un círculo pequeño
                angulo = (2 * math.pi * zonas_centro.index(zona_id)) / len(zonas_centro)
                radio = 80
                x = centro_x + radio * math.cos(angulo)
                y = centro_y + radio * math.sin(angulo)
            else:
                # Otras zonas en círculo grande
                idx = i - len(zonas_centro)
                total_externas = len(zonas) - len(zonas_centro)
                angulo = (2 * math.pi * idx) / total_externas
                radio = 200
                x = centro_x + radio * math.cos(angulo)
                y = centro_y + radio * math.sin(angulo)
            
            self.zonas_posiciones[zona_id] = {'x': x, 'y': y}
    
    def crear_conexiones_grafo(self):
        """Crea conexiones entre zonas cercanas"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM rutas')
        rutas = cursor.fetchall()
        
        for ruta in rutas:
            self.grafo.agregar_arista(ruta[1], ruta[2], ruta[5])
        
        # Agregar conexiones adicionales automáticas (zonas cercanas)
        zonas_ids = list(self.zonas_posiciones.keys())
        for i, zona1 in enumerate(zonas_ids):
            for zona2 in zonas_ids[i+1:]:
                pos1 = self.zonas_posiciones[zona1]
                pos2 = self.zonas_posiciones[zona2]
                dist = math.sqrt((pos1['x']-pos2['x'])**2 + (pos1['y']-pos2['y'])**2)
                
                # Conectar si están cerca (distancia < 150)
                if dist < 150:
                    cursor.execute('SELECT riesgo_general FROM zonas WHERE id = ?', (zona1,))
                    riesgo1 = cursor.fetchone()[0]
                    cursor.execute('SELECT riesgo_general FROM zonas WHERE id = ?', (zona2,))
                    riesgo2 = cursor.fetchone()[0]
                    riesgo_promedio = (riesgo1 + riesgo2) / 2
                    self.grafo.agregar_arista(zona1, zona2, int(riesgo_promedio))
    
    def crear_interfaz(self):
        # Título
        frame_titulo = tk.Frame(self.root, bg='#0a0e27')
        frame_titulo.pack(fill='x', pady=10)
        
        tk.Label(frame_titulo, text=" SISTEMA DE RIESGO DE ALERTA TEMPRANA - JULIACA",
                font=('Arial', 22, 'bold'), bg='#0a0e27', fg='#00ff88').pack()
        
        tk.Label(frame_titulo, text="JULIACA CENTRO",
                font=('Arial', 11), bg='#0a0e27', fg='#88ccff').pack()
        
        # Frame principal
        frame_principal = tk.Frame(self.root, bg='#0a0e27')
        frame_principal.pack(fill='both', expand=True, padx=15, pady=5)
        
        # PANEL IZQUIERDO
        panel_izq = tk.Frame(frame_principal, bg='#16213e', relief='ridge', bd=3, width=350)
        panel_izq.pack(side='left', fill='both', padx=(0, 10))
        panel_izq.pack_propagate(False)
        
        tk.Label(panel_izq, text="🎛️ PANEL DE CONTROL", font=('Arial', 14, 'bold'),
                bg='#16213e', fg='#ffffff').pack(pady=10)
        
        # Búsqueda
        frame_buscar = tk.LabelFrame(panel_izq, text="🔍 Buscar Zona", 
                                     font=('Arial', 11, 'bold'),
                                     bg='#16213e', fg='#00ff88', bd=2)
        frame_buscar.pack(pady=10, padx=10, fill='x')
        
        self.combo_zonas = ttk.Combobox(frame_buscar, font=('Arial', 10), state='readonly')
        if self.conn:
            cursor = self.conn.cursor()
            cursor.execute('SELECT id, nombre FROM zonas ORDER BY nombre')
            zonas = cursor.fetchall()
            self.combo_zonas['values'] = [f"{z[0]:02d} - {z[1]}" for z in zonas]
        self.combo_zonas.pack(pady=8, padx=8, fill='x')
        
        tk.Button(frame_buscar, text="📍 Analizar Zona", command=self.analizar_zona,
                 bg='#0f4c75', fg='white', font=('Arial', 10, 'bold'),
                 cursor='hand2', relief='raised', bd=3).pack(pady=5, padx=8, fill='x')
        
        # Información
        frame_info = tk.LabelFrame(panel_izq, text="ℹ️ Información de Zona",
                                   font=('Arial', 11, 'bold'),
                                   bg='#16213e', fg='#00ff88', bd=2)
        frame_info.pack(pady=10, padx=10, fill='both', expand=True)
        
        self.texto_info = scrolledtext.ScrolledText(frame_info, height=15,
                                                    font=('Consolas', 9),
                                                    bg='#0a0a0a', fg='#00ff00',
                                                    wrap='word', relief='sunken', bd=2)
        self.texto_info.pack(pady=8, padx=8, fill='both', expand=True)
        
        # Botones
        frame_botones = tk.Frame(panel_izq, bg='#16213e')
        frame_botones.pack(pady=10, padx=10, fill='x')
        
        tk.Button(frame_botones, text="🛣️ Ruta Segura", command=self.calcular_ruta_segura,
                 bg='#27ae60', fg='white', font=('Arial', 9, 'bold')).pack(fill='x', pady=3)
        
        tk.Button(frame_botones, text="📊 Estadísticas", command=self.mostrar_estadisticas,
                 bg='#2980b9', fg='white', font=('Arial', 9, 'bold')).pack(fill='x', pady=3)
        
        tk.Button(frame_botones, text="⚠️ Zonas Críticas", command=self.mostrar_zonas_criticas,
                 bg='#c0392b', fg='white', font=('Arial', 9, 'bold')).pack(fill='x', pady=3)
        
        tk.Button(frame_botones, text="🔄 Recargar Mapa", command=self.dibujar_mapa,
                 bg='#8e44ad', fg='white', font=('Arial', 9, 'bold')).pack(fill='x', pady=3)
        
        # PANEL DERECHO - MAPA
        panel_der = tk.Frame(frame_principal, bg='#16213e', relief='ridge', bd=3)
        panel_der.pack(side='right', fill='both', expand=True)
        
        tk.Label(panel_der, text="🗺️ MAPA DE JULIACA (Representación Simplificada)",
                font=('Arial', 14, 'bold'), bg='#16213e', fg='#ffffff').pack(pady=8)
        
        tk.Label(panel_der, text="✅ Mapa generado con datos de la base de datos",
                font=('Arial', 10), bg='#16213e', fg='#ffd700').pack()
        
        # Canvas
        self.canvas = tk.Canvas(panel_der, bg='#1a1a2e', highlightthickness=0, cursor='hand2')
        self.canvas.pack(pady=10, padx=10, fill='both', expand=True)
        
        # Eventos mouse
        self.canvas.bind('<ButtonPress-1>', self.mouse_press)
        self.canvas.bind('<ButtonRelease-1>', self.mouse_release)
        self.canvas.bind('<B1-Motion>', self.mouse_drag)
        self.canvas.bind('<MouseWheel>', self.mouse_wheel)
        
        # Controles
        frame_controles = tk.Frame(panel_der, bg='#16213e')
        frame_controles.pack(pady=5)
        
        tk.Label(frame_controles, text="Controles:", font=('Arial', 10, 'bold'),
                bg='#16213e', fg='#ffffff').pack(side='left', padx=5)
        
        tk.Button(frame_controles, text="🔍 Zoom +", command=lambda: self.zoom_mapa(0.2),
                 bg='#34495e', fg='white', font=('Arial', 9)).pack(side='left', padx=2)
        
        tk.Button(frame_controles, text="🔍 Zoom -", command=lambda: self.zoom_mapa(-0.2),
                 bg='#34495e', fg='white', font=('Arial', 9)).pack(side='left', padx=2)
        
        tk.Button(frame_controles, text="↺ Reset", command=self.reset_vista,
                 bg='#34495e', fg='white', font=('Arial', 9)).pack(side='left', padx=2)
        
        # Dibujar mapa inicial
        self.root.after(200, self.dibujar_mapa)
    
    def dibujar_mapa(self):
        """Dibuja el mapa simplificado con líneas"""
        self.canvas.delete('all')
        w = self.canvas.winfo_width() or 800
        h = self.canvas.winfo_height() or 600
        
        # Centro del canvas
        center_x = w / 2
        center_y = h / 2
        
        # Dibujar título
        self.canvas.create_text(center_x, 30, text="MAPA DE RIESGO",
                               fill='white', font=('Arial', 18, 'bold'))
        
        # Dibujar leyenda
        self.dibujar_leyenda(w, h)
        
        # Dibujar conexiones (aristas del grafo)
        for origen_id in self.grafo.grafo:
            if origen_id not in self.zonas_posiciones:
                continue
            
            pos1 = self.zonas_posiciones[origen_id]
            x1 = center_x + (pos1['x'] - 400) * self.zoom + self.offset_x
            y1 = center_y + (pos1['y'] - 300) * self.zoom + self.offset_y
            
            for destino_id, _, riesgo in self.grafo.grafo[origen_id]:
                if destino_id not in self.zonas_posiciones:
                    continue
                
                # Evitar duplicados (solo dibujar si origen < destino)
                if origen_id >= destino_id:
                    continue
                
                pos2 = self.zonas_posiciones[destino_id]
                x2 = center_x + (pos2['x'] - 400) * self.zoom + self.offset_x
                y2 = center_y + (pos2['y'] - 300) * self.zoom + self.offset_y
                
                color = self.obtener_color_riesgo(riesgo)
                grosor = max(2, int(3 * self.zoom))
                
                self.canvas.create_line(x1, y1, x2, y2,
                                       fill=color, width=grosor, tags='calle')
        
        # Dibujar zonas (nodos)
        if self.conn:
            cursor = self.conn.cursor()
            cursor.execute('SELECT * FROM zonas')
            zonas = cursor.fetchall()
            
            for zona in zonas:
                zona_id = zona[0]
                if zona_id not in self.zonas_posiciones:
                    continue
                
                pos = self.zonas_posiciones[zona_id]
                x = center_x + (pos['x'] - 400) * self.zoom + self.offset_x
                y = center_y + (pos['y'] - 300) * self.zoom + self.offset_y
                
                riesgo = zona[4]
                color = self.obtener_color_riesgo(riesgo)
                radio = max(8, int(12 * self.zoom))
                
                # Círculo de zona
                circulo = self.canvas.create_oval(x-radio, y-radio, x+radio, y+radio,
                                                 fill=color, outline='white', width=3,
                                                 tags=f'zona_{zona_id}')
                
                # Nombre de zona
                if self.zoom > 0.7:
                    nombre = zona[1]
                    if len(nombre) > 20:
                        nombre = nombre[:17] + '...'
                    
                    self.canvas.create_text(x, y-radio-15, text=nombre,
                                           fill='white', font=('Arial', int(8*self.zoom), 'bold'),
                                           tags=f'label_{zona_id}')
                
                # Bind click
                self.canvas.tag_bind(f'zona_{zona_id}', '<Button-1>',
                                    lambda e, z=zona: self.click_zona(z))
    
    def dibujar_leyenda(self, w, h):
        """Dibuja la leyenda en el mapa"""
        x_base = 20
        y_base = 70
        
        # Fondo de leyenda
        self.canvas.create_rectangle(x_base, y_base, x_base+220, y_base+180,
                                     fill='#0a0a0a', outline='white', width=2)
        
        self.canvas.create_text(x_base+110, y_base+15, text="NIVELES DE RIESGO",
                               fill='white', font=('Arial', 11, 'bold'))
        
        niveles = [
            ("🟢 Bajo (0-40)", '#2ecc71'),
            ("🟡 Medio (40-60)", '#f39c12'),
            ("🟠 Alto (60-75)", '#e67e22'),
            ("🔴 Crítico (75+)", '#e74c3c')
        ]
        
        y_offset = y_base + 40
        for texto, color in niveles:
            self.canvas.create_oval(x_base+15, y_offset, x_base+25, y_offset+10,
                                   fill=color, outline='white', width=2)
            self.canvas.create_text(x_base+40, y_offset+5, text=texto,
                                   fill='white', font=('Arial', 10), anchor='w')
            y_offset += 30
    
    def obtener_color_riesgo(self, riesgo):
        if riesgo < 40:
            return '#2ecc71'
        elif riesgo < 60:
            return '#f39c12'
        elif riesgo < 75:
            return '#e67e22'
        else:
            return '#e74c3c'
    
    def analizar_zona(self):
        seleccion = self.combo_zonas.get()
        if not seleccion:
            messagebox.showwarning("Advertencia", "Seleccione una zona")
            return
        
        zona_id = int(seleccion.split(' - ')[0])
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM zonas WHERE id = ?', (zona_id,))
        zona = cursor.fetchone()
        
        if not zona:
            return
        
        self.texto_info.delete('1.0', 'end')
        
        # Información
        self.insertar_texto(f"{'='*45}\n", 'titulo')
        self.insertar_texto(f"ZONA: {zona[1]}\n", 'titulo')
        self.insertar_texto(f"{'='*45}\n\n", 'titulo')
        
        riesgo = zona[4]
        nivel = ("BAJO" if riesgo < 40 else "MEDIO" if riesgo < 60 
                else "ALTO" if riesgo < 75 else "CRÍTICO")
        self.insertar_texto(f"🚨 NIVEL DE RIESGO: {nivel} ({riesgo}/100)\n\n", 'riesgo')
        
        self.insertar_texto(f"📍 Tipo: {zona[5].upper()}\n", 'info')
        if zona[7]:
            self.insertar_texto(f"👥 Población: {zona[7]:,}\n", 'info')
        self.insertar_texto(f"\n{zona[6]}\n\n", 'desc')
        
        # Horas peligrosas
        horas = self.matriz_dispersa.horas_peligrosas(zona_id, umbral=2)
        if horas:
            self.insertar_texto("⏰ HORAS DE MAYOR RIESGO:\n", 'subtitulo')
            for hora, cantidad in sorted(horas, key=lambda x: x[1], reverse=True)[:5]:
                self.insertar_texto(f"   • {hora:02d}:00 hrs - {cantidad} incidentes\n", 'dato')
            self.insertar_texto('\n')
        
        # Incidentes
        cursor.execute('SELECT * FROM incidentes WHERE zona_id = ?', (zona_id,))
        incidentes = cursor.fetchall()
        
        if incidentes:
            self.insertar_texto(f"📋 INCIDENTES REGISTRADOS: {len(incidentes)}\n", 'subtitulo')
            tipos = {}
            for inc in incidentes:
                tipo = inc[2].upper()
                tipos[tipo] = tipos.get(tipo, 0) + 1
            
            for tipo, cant in sorted(tipos.items(), key=lambda x: x[1], reverse=True):
                emoji = {"ROBO": "🔫", "HURTO": "👜", "ACCIDENTE": "🚗", 
                        "TRATA": "⚠️", "TRAFICO": "🚦"}.get(tipo, "•")
                self.insertar_texto(f"   {emoji} {tipo}: {cant} casos\n", 'dato')
            self.insertar_texto('\n')
        
        # Recomendaciones
        self.insertar_texto("💡 RECOMENDACIONES:\n", 'subtitulo')
        self.insertar_texto("• Mantenerse en zonas iluminadas\n", 'recom')
        self.insertar_texto("• Evitar mostrar objetos de valor\n", 'recom')
        self.insertar_texto("• Transitar en grupo durante la noche\n", 'recom')
        self.insertar_texto("• Reportar actividades sospechosas al 105\n", 'recom')
        
        self.aplicar_estilos_texto()
        self.resaltar_zona_mapa(zona_id)
    
    def insertar_texto(self, texto, tag='normal'):
        self.texto_info.insert('end', texto, tag)
    
    def aplicar_estilos_texto(self):
        self.texto_info.tag_config('titulo', foreground='#00ff88', font=('Consolas', 10, 'bold'))
        self.texto_info.tag_config('subtitulo', foreground='#3498db', font=('Consolas', 9, 'bold'))
        self.texto_info.tag_config('riesgo', foreground='#e74c3c', font=('Consolas', 9, 'bold'))
        self.texto_info.tag_config('info', foreground='#f39c12')
        self.texto_info.tag_config('desc', foreground='#95e1d3')
        self.texto_info.tag_config('dato', foreground='#95e1d3')
        self.texto_info.tag_config('recom', foreground='#a8e6cf')
    
    def resaltar_zona_mapa(self, zona_id):
        self.canvas.delete('resaltado')
        
        if zona_id in self.zonas_posiciones:
            w = self.canvas.winfo_width()
            h = self.canvas.winfo_height()
            center_x = w / 2
            center_y = h / 2
            
            pos = self.zonas_posiciones[zona_id]
            x = center_x + (pos['x'] - 400) * self.zoom + self.offset_x
            y = center_y + (pos['y'] - 300) * self.zoom + self.offset_y
            radio = max(20, int(25 * self.zoom))
            
            self.canvas.create_oval(x-radio, y-radio, x+radio, y+radio,
                                   outline='#00ff88', width=4, tags='resaltado')
    
    def click_zona(self, zona):
        self.combo_zonas.set(f"{zona[0]:02d} - {zona[1]}")
        self.analizar_zona()
    
    def calcular_ruta_segura(self):
        ventana = tk.Toplevel(self.root)
        ventana.title("🛣️ Calcular Ruta Segura")
        ventana.geometry("550x500")
        ventana.configure(bg='#0a0e27')
        
        tk.Label(ventana, text="🛣️ CALCULADOR DE RUTA SEGURA",
                font=('Arial', 16, 'bold'), bg='#0a0e27', fg='#00ff88').pack(pady=15)
        
        frame_seleccion = tk.Frame(ventana, bg='#16213e', relief='ridge', bd=2)
        frame_seleccion.pack(pady=10, padx=20, fill='both')
        
        tk.Label(frame_seleccion, text="📍 ORIGEN:", bg='#16213e', fg='white',
                font=('Arial', 11, 'bold')).pack(pady=(10,5))
        combo_origen = ttk.Combobox(frame_seleccion, font=('Arial', 10), state='readonly')
        combo_origen['values'] = self.combo_zonas['values']
        combo_origen.pack(pady=5, padx=10, fill='x')
        
        tk.Label(frame_seleccion, text="🎯 DESTINO:", bg='#16213e', fg='white',
                font=('Arial', 11, 'bold')).pack(pady=(10,5))
        combo_destino = ttk.Combobox(frame_seleccion, font=('Arial', 10), state='readonly')
        combo_destino['values'] = self.combo_zonas['values']
        combo_destino.pack(pady=5, padx=10, fill='x')
        
        tk.Label(frame_seleccion, text="📊 RESULTADO:", bg='#16213e', fg='white',
                font=('Arial', 11, 'bold')).pack(pady=(15,5))
        
        texto_resultado = scrolledtext.ScrolledText(frame_seleccion, height=12,
                                                    font=('Consolas', 9),
                                                    bg='#0a0a0a', fg='#00ff00', wrap='word')
        texto_resultado.pack(pady=5, padx=10, fill='both', expand=True)
        
        def calcular():
            if not combo_origen.get() or not combo_destino.get():
                messagebox.showwarning("Advertencia", "Selecciona origen y destino")
                return
            
            origen_id = int(combo_origen.get().split(' - ')[0])
            destino_id = int(combo_destino.get().split(' - ')[0])
            
            if origen_id == destino_id:
                messagebox.showinfo("Info", "Origen y destino son iguales")
                return
            
            camino, distancia_total = self.grafo.dijkstra(origen_id, destino_id)
            
            texto_resultado.delete('1.0', 'end')
            
            if camino and len(camino) > 1:
                texto_resultado.insert('end', "="*50 + "\n", 'titulo')
                texto_resultado.insert('end', "✅ RUTA SEGURA ENCONTRADA\n", 'titulo')
                texto_resultado.insert('end', "="*50 + "\n\n", 'titulo')
                
                texto_resultado.insert('end', f"📏 Distancia ponderada: {distancia_total:.1f}\n", 'info')
                texto_resultado.insert('end', f"📍 Paradas: {len(camino)}\n\n", 'info')
                
                texto_resultado.insert('end', "🗺️ RECORRIDO:\n", 'subtitulo')
                texto_resultado.insert('end', "-"*50 + "\n\n", 'subtitulo')
                
                riesgo_promedio = 0
                for i, nodo_id in enumerate(camino, 1):
                    nombre = self.grafo.nodos[nodo_id]['nombre']
                    riesgo = self.grafo.nodos[nodo_id]['riesgo']
                    riesgo_promedio += riesgo
                    
                    emoji = "🟢" if riesgo < 40 else "🟡" if riesgo < 60 else "🟠" if riesgo < 75 else "🔴"
                    
                    texto_resultado.insert('end', f"{i}. {emoji} {nombre}\n", 'dato')
                    texto_resultado.insert('end', f"   Nivel de riesgo: {riesgo}/100\n\n", 'dato')
                
                riesgo_promedio /= len(camino)
                texto_resultado.insert('end', "\n" + "="*50 + "\n", 'titulo')
                texto_resultado.insert('end', f"⚖️ RIESGO PROMEDIO: {riesgo_promedio:.1f}/100\n", 'riesgo')
                
                if riesgo_promedio < 40:
                    texto_resultado.insert('end', "\n✅ Ruta SEGURA\n", 'seguro')
                elif riesgo_promedio < 60:
                    texto_resultado.insert('end', "\n⚠️ Ruta MODERADA\n", 'advertencia')
                else:
                    texto_resultado.insert('end', "\n🚨 Ruta PELIGROSA\n", 'peligro')
                
                # Dibujar ruta en el mapa principal
                self.dibujar_ruta_en_mapa(camino)
                
            else:
                texto_resultado.insert('end', "="*50 + "\n", 'titulo')
                texto_resultado.insert('end', "❌ NO SE ENCONTRÓ RUTA\n", 'error')
                texto_resultado.insert('end', "="*50 + "\n\n", 'titulo')
                texto_resultado.insert('end', "Las zonas no están conectadas.\n", 'info')
            
            texto_resultado.tag_config('titulo', foreground='#00ff88', font=('Consolas', 10, 'bold'))
            texto_resultado.tag_config('subtitulo', foreground='#3498db', font=('Consolas', 9, 'bold'))
            texto_resultado.tag_config('info', foreground='#f39c12')
            texto_resultado.tag_config('dato', foreground='#95e1d3')
            texto_resultado.tag_config('riesgo', foreground='#e74c3c', font=('Consolas', 10, 'bold'))
            texto_resultado.tag_config('seguro', foreground='#2ecc71', font=('Consolas', 10, 'bold'))
            texto_resultado.tag_config('advertencia', foreground='#f39c12', font=('Consolas', 10, 'bold'))
            texto_resultado.tag_config('peligro', foreground='#e74c3c', font=('Consolas', 10, 'bold'))
            texto_resultado.tag_config('error', foreground='#ff6b6b', font=('Consolas', 10, 'bold'))
        
        tk.Button(ventana, text="🚀 CALCULAR RUTA", command=calcular,
                 bg='#27ae60', fg='white', font=('Arial', 12, 'bold'),
                 cursor='hand2', relief='raised', bd=3).pack(pady=15)
    
    def dibujar_ruta_en_mapa(self, camino):
        """Dibuja la ruta calculada en el mapa principal"""
        self.canvas.delete('ruta_calculada')
        
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        center_x = w / 2
        center_y = h / 2
        
        for i in range(len(camino) - 1):
            zona1_id = camino[i]
            zona2_id = camino[i + 1]
            
            if zona1_id in self.zonas_posiciones and zona2_id in self.zonas_posiciones:
                pos1 = self.zonas_posiciones[zona1_id]
                pos2 = self.zonas_posiciones[zona2_id]
                
                x1 = center_x + (pos1['x'] - 400) * self.zoom + self.offset_x
                y1 = center_y + (pos1['y'] - 300) * self.zoom + self.offset_y
                x2 = center_x + (pos2['x'] - 400) * self.zoom + self.offset_x
                y2 = center_y + (pos2['y'] - 300) * self.zoom + self.offset_y
                
                self.canvas.create_line(x1, y1, x2, y2,
                                       fill='#00ff88', width=5,
                                       arrow=tk.LAST, tags='ruta_calculada')
    
    def mostrar_estadisticas(self):
        ventana = tk.Toplevel(self.root)
        ventana.title("📊 Estadísticas Generales")
        ventana.geometry("700x600")
        ventana.configure(bg='#0a0e27')
        
        tk.Label(ventana, text="📊 ESTADÍSTICAS DEL SISTEMA",
                font=('Arial', 18, 'bold'), bg='#0a0e27', fg='#00ff88').pack(pady=15)
        
        texto = scrolledtext.ScrolledText(ventana, font=('Consolas', 10),
                                         bg='#0a0a0a', fg='#00ff00', wrap='word')
        texto.pack(pady=10, padx=20, fill='both', expand=True)
        
        texto.insert('end', "="*60 + "\n", 'titulo')
        texto.insert('end', "ANÁLISIS DE RIESGO POR ZONAS\n", 'titulo')
        texto.insert('end', "="*60 + "\n\n", 'titulo')
        
        zonas_bajo = self.arbol_riesgo.buscar_por_rango(0, 40)
        zonas_medio = self.arbol_riesgo.buscar_por_rango(40, 60)
        zonas_alto = self.arbol_riesgo.buscar_por_rango(60, 75)
        zonas_critico = self.arbol_riesgo.buscar_por_rango(75, 100)
        
        texto.insert('end', f"🟢 RIESGO BAJO (0-40): {len(zonas_bajo)} zonas\n", 'bajo')
        for z in zonas_bajo[:5]:
            texto.insert('end', f"   • {z[1]}: {z[2]}/100\n", 'dato')
        if len(zonas_bajo) > 5:
            texto.insert('end', f"   ... y {len(zonas_bajo)-5} más\n", 'dato')
        texto.insert('end', '\n')
        
        texto.insert('end', f"🟡 RIESGO MEDIO (40-60): {len(zonas_medio)} zonas\n", 'medio')
        for z in zonas_medio[:5]:
            texto.insert('end', f"   • {z[1]}: {z[2]}/100\n", 'dato')
        if len(zonas_medio) > 5:
            texto.insert('end', f"   ... y {len(zonas_medio)-5} más\n", 'dato')
        texto.insert('end', '\n')
        
        texto.insert('end', f"🟠 RIESGO ALTO (60-75): {len(zonas_alto)} zonas\n", 'alto')
        for z in zonas_alto:
            texto.insert('end', f"   • {z[1]}: {z[2]}/100\n", 'dato')
        texto.insert('end', '\n')
        
        texto.insert('end', f"🔴 RIESGO CRÍTICO (75+): {len(zonas_critico)} zonas\n", 'critico')
        for z in zonas_critico:
            texto.insert('end', f"   • {z[1]}: {z[2]}/100\n", 'dato')
        texto.insert('end', '\n')
        
        cursor = self.conn.cursor()
        cursor.execute('SELECT tipo, COUNT(*) as total FROM incidentes GROUP BY tipo ORDER BY total DESC')
        incidentes_tipo = cursor.fetchall()
        
        texto.insert('end', "\n" + "="*60 + "\n", 'titulo')
        texto.insert('end', "INCIDENTES POR TIPO\n", 'titulo')
        texto.insert('end', "="*60 + "\n\n", 'titulo')
        
        total_inc = sum(i[1] for i in incidentes_tipo)
        for tipo, cantidad in incidentes_tipo:
            porcentaje = (cantidad / total_inc) * 100
            emoji = {"robo": "🔫", "hurto": "👜", "accidente": "🚗", 
                    "trata": "⚠️", "trafico": "🚦", "violencia": "👊"}.get(tipo, "•")
            texto.insert('end', f"{emoji} {tipo.upper()}: {cantidad} ({porcentaje:.1f}%)\n", 'stat')
        
        cursor.execute('''
            SELECT hora, COUNT(*) as total 
            FROM incidentes 
            GROUP BY hora 
            ORDER BY total DESC 
            LIMIT 5
        ''')
        horas_top = cursor.fetchall()
        
        texto.insert('end', "\n" + "="*60 + "\n", 'titulo')
        texto.insert('end', "HORARIOS MÁS PELIGROSOS\n", 'titulo')
        texto.insert('end', "="*60 + "\n\n", 'titulo')
        
        for hora, cantidad in horas_top:
            texto.insert('end', f"🕐 {hora:02d}:00 hrs → {cantidad} incidentes\n", 'hora')
        
        texto.tag_config('titulo', foreground='#00ff88', font=('Consolas', 11, 'bold'))
        texto.tag_config('bajo', foreground='#2ecc71', font=('Consolas', 10, 'bold'))
        texto.tag_config('medio', foreground='#f39c12', font=('Consolas', 10, 'bold'))
        texto.tag_config('alto', foreground='#e67e22', font=('Consolas', 10, 'bold'))
        texto.tag_config('critico', foreground='#e74c3c', font=('Consolas', 10, 'bold'))
        texto.tag_config('stat', foreground='#3498db')
        texto.tag_config('hora', foreground='#9b59b6')
        texto.tag_config('dato', foreground='#95e1d3')
    
    def mostrar_zonas_criticas(self):
        zonas_criticas = self.arbol_riesgo.buscar_por_rango(70, 100)
        
        if not zonas_criticas:
            messagebox.showinfo("Información", "No hay zonas críticas")
            return
        
        ventana = tk.Toplevel(self.root)
        ventana.title("⚠️ Zonas Críticas")
        ventana.geometry("600x500")
        ventana.configure(bg='#0a0e27')
        
        tk.Label(ventana, text="🚨 ZONAS DE ALTO RIESGO 🚨",
                font=('Arial', 18, 'bold'), bg='#0a0e27', fg='#e74c3c').pack(pady=15)
        
        texto = scrolledtext.ScrolledText(ventana, font=('Consolas', 10),
                                         bg='#0a0a0a', fg='#ff6b6b', wrap='word')
        texto.pack(pady=10, padx=20, fill='both', expand=True)
        
        texto.insert('end', "ATENCIÓN: Estas zonas requieren precaución extrema\n", 'titulo')
        texto.insert('end', "="*55 + "\n\n", 'titulo')
        
        for i, zona in enumerate(sorted(zonas_criticas, key=lambda x: x[2], reverse=True), 1):
            texto.insert('end', f"{i}. {zona[1]}\n", 'zona')
            texto.insert('end', f"   🔴 Nivel de riesgo: {zona[2]}/100\n", 'riesgo')
            
            cursor = self.conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM incidentes WHERE zona_id = ?', (zona[0],))
            num_inc = cursor.fetchone()[0]
            
            if num_inc > 0:
                texto.insert('end', f"   📋 Incidentes: {num_inc}\n", 'info')
            
            horas = self.matriz_dispersa.horas_peligrosas(zona[0], umbral=1)
            if horas:
                horas_str = ', '.join([f"{h[0]:02d}:00" for h in sorted(horas)[:3]])
                texto.insert('end', f"   ⏰ Horarios críticos: {horas_str}\n", 'info')
            
            texto.insert('end', '\n')
        
        texto.insert('end', "\n" + "="*55 + "\n", 'titulo')
        texto.insert('end', "⚠️ RECOMENDACIONES:\n\n", 'titulo')
        texto.insert('end', "• Evitar estas zonas en horarios nocturnos\n", 'recom')
        texto.insert('end', "• Transitar en grupo o vehículo\n", 'recom')
        texto.insert('end', "• No mostrar objetos de valor\n", 'recom')
        texto.insert('end', "• Reportar al 105\n", 'recom')
        
        texto.tag_config('titulo', foreground='#ff6b6b', font=('Consolas', 11, 'bold'))
        texto.tag_config('zona', foreground='#ffffff', font=('Consolas', 10, 'bold'))
        texto.tag_config('riesgo', foreground='#e74c3c', font=('Consolas', 10, 'bold'))
        texto.tag_config('info', foreground='#f39c12')
        texto.tag_config('recom', foreground='#a8e6cf')
    
    def mouse_press(self, event):
        self.dragging = True
        self.last_x = event.x
        self.last_y = event.y
    
    def mouse_release(self, event):
        self.dragging = False
    
    def mouse_drag(self, event):
        if self.dragging:
            dx = event.x - self.last_x
            dy = event.y - self.last_y
            self.offset_x += dx
            self.offset_y += dy
            self.last_x = event.x
            self.last_y = event.y
            self.dibujar_mapa()
    
    def mouse_wheel(self, event):
        if event.delta > 0:
            self.zoom_mapa(0.1)
        else:
            self.zoom_mapa(-0.1)
    
    def zoom_mapa(self, delta):
        nuevo_zoom = self.zoom + delta
        if 0.3 <= nuevo_zoom <= 3.0:
            self.zoom = nuevo_zoom
            self.dibujar_mapa()
    
    def reset_vista(self):
        self.zoom = 1.0
        self.offset_x = 0
        self.offset_y = 0
        self.dibujar_mapa()
    
    def __del__(self):
        if self.conn:
            self.conn.close()

# ============================================
# EJECUCIÓN
# ============================================

if __name__ == "__main__":
    print("="*70)
    print("   SISTEMA DE SEGURIDAD VIAL - JULIACA")
    print("   Mapa Simplificado con Datos Reales")
    print("="*70)
    print()
    
    import os
    if not os.path.exists('juliaca_seguridad.db'):
        print("⚠️  Base de datos no encontrada.")
        print("📝 Ejecuta primero: python base_datos.py")
        print()
    
    print("🚀 Iniciando aplicación...")
    print()
    
    root = tk.Tk()
    app = SistemaJuliaca(root)
    root.mainloop()