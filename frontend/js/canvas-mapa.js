const API_URL = 'http://localhost:5000';

// Variables globales
let canvas, ctx;
let nodos = {};
let aristasCompletas = [];
let nodosVisibles = [];
let aristasVisibles = [];
let rutaActual = [];

// Vista/transformación
let offsetX = 0, offsetY = 0;
let escala = 1.0;
let isDragging = false;
let lastX = 0, lastY = 0;

// Selección
let idOrigen = null;
let idDestino = null;

// Límites geográficos
let minLat, maxLat, minLon, maxLon;

// OPTIMIZACIÓN: Límites de viewport actual
let viewportBounds = { minLat: 0, maxLat: 0, minLon: 0, maxLon: 0 };

// Colores
function getColorRiesgo(riesgo) {
    if (riesgo < 40) return '#2ecc71';
    if (riesgo < 60) return '#f39c12';
    if (riesgo < 75) return '#e67e22';
    return '#e74c3c';
}

// Conversión geo → canvas
function geoToCanvas(lat, lon) {
    const rangoLat = maxLat - minLat;
    const rangoLon = maxLon - minLon;
    
    const x_norm = (lon - minLon) / rangoLon;
    const y_norm = (maxLat - lat) / rangoLat;
    
    const margen = 50;
    const anchoUtil = canvas.width - 2 * margen;
    const altoUtil = canvas.height - 2 * margen;
    
    const x = margen + x_norm * anchoUtil;
    const y = margen + y_norm * altoUtil;
    
    return {
        x: (x - canvas.width / 2) * escala + canvas.width / 2 + offsetX,
        y: (y - canvas.height / 2) * escala + canvas.height / 2 + offsetY
    };
}

// Canvas → geo (para clicks)
function canvasToGeo(canvasX, canvasY) {
    const margen = 50;
    const anchoUtil = canvas.width - 2 * margen;
    const altoUtil = canvas.height - 2 * margen;
    
    const x = ((canvasX - offsetX - canvas.width / 2) / escala) + canvas.width / 2;
    const y = ((canvasY - offsetY - canvas.height / 2) / escala) + canvas.height / 2;
    
    const x_norm = (x - margen) / anchoUtil;
    const y_norm = (y - margen) / altoUtil;
    
    const lon = minLon + x_norm * (maxLon - minLon);
    const lat = maxLat - y_norm * (maxLat - minLat);
    
    return { lat, lon };
}

// NUEVO: Calcular viewport actual
function calcularViewportBounds() {
    // Obtener las 4 esquinas del canvas
    const topLeft = canvasToGeo(0, 0);
    const topRight = canvasToGeo(canvas.width, 0);
    const bottomLeft = canvasToGeo(0, canvas.height);
    const bottomRight = canvasToGeo(canvas.width, canvas.height);
    
    // Encontrar los límites
    const lats = [topLeft.lat, topRight.lat, bottomLeft.lat, bottomRight.lat];
    const lons = [topLeft.lon, topRight.lon, bottomLeft.lon, bottomRight.lon];
    
    return {
        minLat: Math.min(...lats),
        maxLat: Math.max(...lats),
        minLon: Math.min(...lons),
        maxLon: Math.max(...lons)
    };
}

// NUEVO: Filtrar elementos visibles en el viewport
function filtrarElementosVisibles() {
    viewportBounds = calcularViewportBounds();
    
    // Filtrar nodos visibles
    nodosVisibles = [];
    for (const id in nodos) {
        const nodo = nodos[id];
        if (nodo.lat >= viewportBounds.minLat && nodo.lat <= viewportBounds.maxLat &&
            nodo.lon >= viewportBounds.minLon && nodo.lon <= viewportBounds.maxLon) {
            nodosVisibles.push({ id, ...nodo });
        }
    }
    
    // Filtrar aristas visibles (ambos extremos en viewport)
    aristasVisibles = [];
    for (const arista of aristasCompletas) {
        const origenVisible = 
            arista.origen.lat >= viewportBounds.minLat && 
            arista.origen.lat <= viewportBounds.maxLat &&
            arista.origen.lon >= viewportBounds.minLon && 
            arista.origen.lon <= viewportBounds.maxLon;
            
        const destinoVisible = 
            arista.destino.lat >= viewportBounds.minLat && 
            arista.destino.lat <= viewportBounds.maxLat &&
            arista.destino.lon >= viewportBounds.minLon && 
            arista.destino.lon <= viewportBounds.maxLon;
        
        if (origenVisible || destinoVisible) {
            aristasVisibles.push(arista);
        }
    }
    
    // Limitar cantidad según zoom para mejor rendimiento
    const maxNodos = escala > 2 ? 5000 : escala > 1.5 ? 3000 : 2000;
    const maxAristas = escala > 2 ? 8000 : escala > 1.5 ? 5000 : 3000;
    
    if (nodosVisibles.length > maxNodos) {
        const step = Math.ceil(nodosVisibles.length / maxNodos);
        nodosVisibles = nodosVisibles.filter((_, i) => i % step === 0);
    }
    
    if (aristasVisibles.length > maxAristas) {
        const step = Math.ceil(aristasVisibles.length / maxAristas);
        aristasVisibles = aristasVisibles.filter((_, i) => i % step === 0);
    }
    
    console.log(`📊 Visibles: ${nodosVisibles.length} nodos, ${aristasVisibles.length} aristas`);
}

// Buscar nodo más cercano
function buscarNodoCercano(lat, lon, radioMax = 0.005) {
    let mejorNodo = null;
    let minDist = Infinity;
    
    // Buscar solo en nodos visibles
    for (const nodo of nodosVisibles) {
        const dist = Math.sqrt(
            Math.pow(nodo.lat - lat, 2) + 
            Math.pow(nodo.lon - lon, 2)
        );
        
        if (dist < minDist && dist < radioMax) {
            minDist = dist;
            mejorNodo = nodo.id;
        }
    }
    
    return mejorNodo;
}

// Cargar datos
async function cargarDatos() {
    try {
        // Cargar nodos
        const respNodos = await fetch(`${API_URL}/api/nodos`);
        const dataNodos = await respNodos.json();
        
        if (dataNodos.success) {
            nodos = dataNodos.nodos;
            console.log(`✅ ${Object.keys(nodos).length} nodos cargados`);
            
            // Calcular límites
            const lats = Object.values(nodos).map(n => n.lat);
            const lons = Object.values(nodos).map(n => n.lon);
            
            minLat = Math.min(...lats);
            maxLat = Math.max(...lats);
            minLon = Math.min(...lons);
            maxLon = Math.max(...lons);
            
            console.log(`📍 Límites: lat[${minLat.toFixed(4)}, ${maxLat.toFixed(4)}] lon[${minLon.toFixed(4)}, ${maxLon.toFixed(4)}]`);
            
            // Poblar selectores con búsqueda inteligente
            const selectOrigen = document.getElementById('selectOrigen');
            const selectDestino = document.getElementById('selectDestino');
            
            selectOrigen.innerHTML = '<option value="">-- Busca o selecciona --</option>';
            selectDestino.innerHTML = '<option value="">-- Busca o selecciona --</option>';
            
            // Obtener nodos únicos por nombre (eliminar duplicados)
            const nodosUnicos = {};
            for (const id in nodos) {
                const nodo = nodos[id];
                const nombreLimpio = nodo.nombre.replace(/\s*#\d+$/, ''); // Quitar números
                
                if (!nodosUnicos[nombreLimpio] || 
                    Object.keys(nodos[id]).length > Object.keys(nodosUnicos[nombreLimpio]).length) {
                    nodosUnicos[nombreLimpio] = { id, ...nodo };
                }
            }
            
            // Ordenar alfabéticamente
            const nodosOrdenados = Object.values(nodosUnicos)
                .sort((a, b) => a.nombre.localeCompare(b.nombre))
                .slice(0, 200); // Limitar a 200 para mejor rendimiento
            
            nodosOrdenados.forEach(nodo => {
                const riesgoLabel = nodo.riesgo < 40 ? '🟢' : nodo.riesgo < 60 ? '🟡' : nodo.riesgo < 75 ? '🟠' : '🔴';
                const option = `<option value="${nodo.id}">${riesgoLabel} ${nodo.nombre}</option>`;
                selectOrigen.innerHTML += option;
                selectDestino.innerHTML += option;
            });
            
            // Habilitar búsqueda en selectores (opcional pero útil)
            [selectOrigen, selectDestino].forEach(select => {
                select.addEventListener('focus', function() {
                    this.size = 8; // Mostrar lista
                });
                select.addEventListener('blur', function() {
                    this.size = 1;
                });
            });
            
            document.getElementById('btnCalcular').disabled = false;
        }
        
        // Cargar aristas
        const respAristas = await fetch(`${API_URL}/api/aristas`);
        const dataAristas = await respAristas.json();
        
        if (dataAristas.success) {
            aristasCompletas = dataAristas.aristas;
            console.log(`✅ ${aristasCompletas.length} aristas cargadas`);
        }
        
        document.getElementById('loading').style.display = 'none';
        
        // Filtrar y dibujar
        filtrarElementosVisibles();
        dibujar();
        
    } catch (error) {
        console.error('❌ Error:', error);
        alert('Error: Asegúrate que el servidor Python esté corriendo en localhost:5000');
    }
}

// Dibujar mapa (OPTIMIZADO)
function dibujar() {
    ctx.fillStyle = '#1a1a2e';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    
    // Dibujar solo aristas visibles
    ctx.lineWidth = 1.5 * Math.min(escala, 2); // Limitar grosor
    
    for (const arista of aristasVisibles) {
        const p1 = geoToCanvas(arista.origen.lat, arista.origen.lon);
        const p2 = geoToCanvas(arista.destino.lat, arista.destino.lon);
        
        // Culling: no dibujar si está fuera del canvas
        if ((p1.x < -10 && p2.x < -10) || (p1.x > canvas.width + 10 && p2.x > canvas.width + 10) ||
            (p1.y < -10 && p2.y < -10) || (p1.y > canvas.height + 10 && p2.y > canvas.height + 10)) {
            continue;
        }
        
        ctx.strokeStyle = getColorRiesgo(arista.riesgo);
        ctx.globalAlpha = 0.6;
        
        ctx.beginPath();
        ctx.moveTo(p1.x, p1.y);
        ctx.lineTo(p2.x, p2.y);
        ctx.stroke();
    }
    
    ctx.globalAlpha = 1.0;
    
    // Dibujar ruta si existe
    if (rutaActual.length >= 2) {
        ctx.strokeStyle = '#00ff88';
        ctx.lineWidth = 4 * escala;
        ctx.lineCap = 'round';
        ctx.shadowBlur = 10;
        ctx.shadowColor = '#00ff88';
        
        ctx.beginPath();
        const p0 = geoToCanvas(nodos[rutaActual[0]].lat, nodos[rutaActual[0]].lon);
        ctx.moveTo(p0.x, p0.y);
        
        for (let i = 1; i < rutaActual.length; i++) {
            const p = geoToCanvas(nodos[rutaActual[i]].lat, nodos[rutaActual[i]].lon);
            ctx.lineTo(p.x, p.y);
        }
        
        ctx.stroke();
        ctx.shadowBlur = 0;
    }
    
    // Dibujar solo nodos visibles
    const radioBase = Math.max(2, 3 * Math.min(escala, 2));
    
    for (const nodo of nodosVisibles) {
        const p = geoToCanvas(nodo.lat, nodo.lon);
        
        // Culling
        if (p.x < -20 || p.x > canvas.width + 20 || p.y < -20 || p.y > canvas.height + 20) {
            continue;
        }
        
        let radio = radioBase;
        let color = getColorRiesgo(nodo.riesgo);
        
        // Resaltar origen/destino
        if (nodo.id == idOrigen) {
            radio = radioBase * 2;
            color = '#00ffff';
            ctx.shadowBlur = 15;
            ctx.shadowColor = '#00ffff';
        } else if (nodo.id == idDestino) {
            radio = radioBase * 2;
            color = '#ff00ff';
            ctx.shadowBlur = 15;
            ctx.shadowColor = '#ff00ff';
        }
        
        ctx.fillStyle = color;
        ctx.strokeStyle = 'white';
        ctx.lineWidth = 1.5;
        
        ctx.beginPath();
        ctx.arc(p.x, p.y, radio, 0, Math.PI * 2);
        ctx.fill();
        ctx.stroke();
        
        ctx.shadowBlur = 0;
    }
    
    // Título
    ctx.fillStyle = 'white';
    ctx.font = '16px Arial';
    ctx.fillText('JULIACA CENTRO - Dataset Real', 10, 25);
    ctx.font = '12px Arial';
    ctx.fillStyle = '#95e1d3';
    ctx.fillText(`${nodosVisibles.length}/${Object.keys(nodos).length} nodos | ${aristasVisibles.length}/${aristasCompletas.length} calles | Zoom: ${escala.toFixed(1)}x`, 10, 45);
}

// Calcular ruta
async function calcularRuta() {
    const origen = document.getElementById('selectOrigen').value;
    const destino = document.getElementById('selectDestino').value;
    
    if (!origen || !destino) {
        alert('Selecciona origen y destino');
        return;
    }
    
    if (origen === destino) {
        alert('Origen y destino deben ser diferentes');
        return;
    }
    
    idOrigen = parseInt(origen);
    idDestino = parseInt(destino);
    
    // Mostrar loading
    document.getElementById('loading').style.display = 'block';
    
    try {
        const response = await fetch(`${API_URL}/api/ruta`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ origen, destino })
        });
        
        const data = await response.json();
        
        if (data.success) {
            const ruta = data.ruta;
            rutaActual = ruta.camino;
            
            mostrarInfoRuta(ruta);
            dibujar();
        } else {
            alert('No se encontró ruta');
        }
    } catch (error) {
        alert('Error al calcular ruta');
    } finally {
        document.getElementById('loading').style.display = 'none';
    }
}

// Mostrar info
function mostrarInfoRuta(ruta) {
    const infoDiv = document.getElementById('info');
    
    let html = `
        <div class="stat">
            <span>📏 Distancia:</span>
            <strong>${ruta.distancia_total.toFixed(2)} km</strong>
        </div>
        <div class="stat">
            <span>⚖️ Riesgo:</span>
            <strong>${ruta.riesgo_promedio.toFixed(1)}/100</strong>
        </div>
        <div class="stat">
            <span>📍 Nodos:</span>
            <strong>${ruta.nodos.length}</strong>
        </div>
        <div style="margin-top: 10px; font-size: 10px; max-height: 150px; overflow-y: auto;">
            <strong style="color: #00ff88;">Recorrido:</strong><br>
    `;
    
    ruta.nodos.slice(0, 20).forEach((nodo, i) => {
        html += `${i + 1}. ${nodo.nombre}<br>`;
    });
    
    if (ruta.nodos.length > 20) {
        html += `... y ${ruta.nodos.length - 20} nodos más`;
    }
    
    html += '</div>';
    infoDiv.innerHTML = html;
}

// Limpiar
function limpiar() {
    idOrigen = null;
    idDestino = null;
    rutaActual = [];
    document.getElementById('selectOrigen').value = '';
    document.getElementById('selectDestino').value = '';
    document.getElementById('info').innerHTML = `
        <p style="color: #95e1d3; text-align: center; padding: 15px; font-size: 11px;">
            Selecciona origen y destino<br>
            o haz click en el mapa
        </p>
    `;
    dibujar();
}

// Zoom con recálculo de visibles
function zoomIn() {
    escala *= 1.2;
    filtrarElementosVisibles();
    dibujar();
}

function zoomOut() {
    escala /= 1.2;
    if (escala < 0.5) escala = 0.5;
    filtrarElementosVisibles();
    dibujar();
}

function resetVista() {
    escala = 1.0;
    offsetX = 0;
    offsetY = 0;
    filtrarElementosVisibles();
    dibujar();
}

// Eventos del canvas
canvas = document.getElementById('canvas');
ctx = canvas.getContext('2d');

function ajustarCanvas() {
    const container = document.getElementById('mapa-container');
    canvas.width = container.clientWidth;
    canvas.height = container.clientHeight;
    filtrarElementosVisibles();
    dibujar();
}

// Mouse
let dragStartTime = 0;

canvas.addEventListener('mousedown', (e) => {
    isDragging = true;
    dragStartTime = Date.now();
    lastX = e.offsetX;
    lastY = e.offsetY;
});

canvas.addEventListener('mousemove', (e) => {
    if (isDragging) {
        offsetX += e.offsetX - lastX;
        offsetY += e.offsetY - lastY;
        lastX = e.offsetX;
        lastY = e.offsetY;
        dibujar(); // Dibujar mientras arrastra (sin recalcular)
    }
});

canvas.addEventListener('mouseup', (e) => {
    const dragDuration = Date.now() - dragStartTime;
    
    if (dragDuration < 200) {
        // Fue un click, no un drag
        const geo = canvasToGeo(e.offsetX, e.offsetY);
        const nodo = buscarNodoCercano(geo.lat, geo.lon);
        
        if (nodo) {
            if (!idOrigen) {
                idOrigen = parseInt(nodo);
                document.getElementById('selectOrigen').value = nodo;
            } else if (!idDestino && nodo != idOrigen) {
                idDestino = parseInt(nodo);
                document.getElementById('selectDestino').value = nodo;
                calcularRuta();
            } else {
                idOrigen = parseInt(nodo);
                idDestino = null;
                rutaActual = [];
                document.getElementById('selectOrigen').value = nodo;
                document.getElementById('selectDestino').value = '';
            }
            dibujar();
        }
    } else {
        // Fue un drag, recalcular elementos visibles
        filtrarElementosVisibles();
        dibujar();
    }
    
    isDragging = false;
});

// Zoom con rueda del mouse
canvas.addEventListener('wheel', (e) => {
    e.preventDefault();
    
    if (e.deltaY < 0) {
        escala *= 1.1;
    } else {
        escala /= 1.1;
        if (escala < 0.5) escala = 0.5;
    }
    
    filtrarElementosVisibles();
    dibujar();
});

// Botones
document.getElementById('btnCalcular').addEventListener('click', calcularRuta);
document.getElementById('btnLimpiar').addEventListener('click', limpiar);

// Inicializar
window.addEventListener('load', () => {
    ajustarCanvas();
    cargarDatos();
});

window.addEventListener('resize', ajustarCanvas);