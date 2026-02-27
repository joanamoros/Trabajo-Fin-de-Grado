import os
import re
import csv
from datetime import datetime

# --- Configuración de rutas ---
BASE_DIR = "/media/sf_tfg_shared"
STATS_SRC_DIR = os.path.join(BASE_DIR, "named_stats")
CACHEVIEWER_DIR = os.path.join(BASE_DIR, "cacheviewer")
REALTIME_CSV = os.path.join(CACHEVIEWER_DIR, "stats_real.csv")

# Archivo para guardar la última posición leída
LAST_POSITION_FILE = os.path.join(CACHEVIEWER_DIR, ".last_position")

os.makedirs(CACHEVIEWER_DIR, exist_ok=True)

def get_last_position():
    """Obtiene la última posición leída del archivo"""
    try:
        if os.path.exists(LAST_POSITION_FILE):
            with open(LAST_POSITION_FILE, 'r') as f:
                return int(f.read().strip())
    except:
        pass
    return 0

def save_last_position(position):
    """Guarda la última posición leída"""
    try:
        with open(LAST_POSITION_FILE, 'w') as f:
            f.write(str(position))
    except:
        pass

def parse_latest_stats(stats_file):
    """Parsea solo las estadísticas MÁS RECIENTES del archivo"""
    stats_data = {}
    try:
        last_position = get_last_position()
        
        with open(stats_file, 'r', encoding='utf-8') as f:
            # Ir a la última posición leída
            f.seek(last_position)
            content = f.read()
            
            # Actualizar posición
            save_last_position(f.tell())
        
        if not content.strip():
            print("[INFO] No hay datos nuevos en el archivo")
            return {}
        
        # Buscar el ÚLTIMO bloque de estadísticas
        dump_markers = list(re.finditer(r'\+\+\+ Statistics Dump \+\+\+', content))
        
        if not dump_markers:
            print("[WARN] No se encontraron marcadores de estadísticas")
            return {}
        
        # Tomar desde el ÚLTIMO marcador
        last_dump_start = dump_markers[-1].start()
        latest_content = content[last_dump_start:]
        
        # Timestamp actual
        stats_data['Timestamp'] = datetime.now().strftime("%d/%m/%Y")
        stats_data['Hora'] = datetime.now().strftime("%H:%M:%S")
        stats_data['Archivo'] = os.path.basename(stats_file)
        
        # --- Incoming Queries A ---
        incoming_match = re.search(r'\+\+ Incoming Queries \+\+\s*\n\s*(\d+)\s+A', latest_content)
        if incoming_match:
            stats_data['incoming_queries_A'] = incoming_match.group(1).strip()
        else:
            stats_data['incoming_queries_A'] = "0"
        
        # --- Cache Statistics (default view) ---
        cache_section = re.search(r'\+\+ Cache Statistics \+\+\s*\[View: default\](.*?)(?:\n\[View:|--- Statistics)', latest_content, re.S | re.I)
        
        if cache_section:
            cache_content = cache_section.group(1)
            
            # cache hits
            hits_match = re.search(r'(\d+)\s+cache hits(?:\s|$)', cache_content)
            stats_data['cache_hits'] = hits_match.group(1) if hits_match else "0"
            
            # cache misses
            misses_match = re.search(r'(\d+)\s+cache misses(?:\s|$)', cache_content)
            stats_data['cache_misses'] = misses_match.group(1) if misses_match else "0"
            
            # cache hits (from query)
            hits_query_match = re.search(r'(\d+)\s+cache hits \(from query\)', cache_content)
            stats_data['cache_hits_from_query'] = hits_query_match.group(1) if hits_query_match else "0"
            
            # cache misses (from query)
            misses_query_match = re.search(r'(\d+)\s+cache misses \(from query\)', cache_content)
            stats_data['cache_misses_from_query'] = misses_query_match.group(1) if misses_query_match else "0"
        else:
            # Buscar alternativas si no encuentra la sección completa
            hits_match = re.search(r'(\d+)\s+cache hits', latest_content)
            stats_data['cache_hits'] = hits_match.group(1) if hits_match else "0"
            
            misses_match = re.search(r'(\d+)\s+cache misses', latest_content)
            stats_data['cache_misses'] = misses_match.group(1) if misses_match else "0"
            
            hits_query_match = re.search(r'(\d+)\s+cache hits \(from query\)', latest_content)
            stats_data['cache_hits_from_query'] = hits_query_match.group(1) if hits_query_match else "0"
            
            misses_query_match = re.search(r'(\d+)\s+cache misses \(from query\)', latest_content)
            stats_data['cache_misses_from_query'] = misses_query_match.group(1) if misses_query_match else "0"
        
        # Validar que tenemos datos
        total_hits = int(stats_data.get('cache_hits', 0))
        total_misses = int(stats_data.get('cache_misses', 0))
        
        if total_hits == 0 and total_misses == 0:
            print("[WARN] No se encontraron estadísticas válidas en el bloque más reciente")
            return {}
        
        return stats_data
        
    except Exception as e:
        print(f"[ERROR] Procesando {stats_file}: {e}")
        import traceback
        traceback.print_exc()
        return {}

def process_current_stats_file():
    """Procesa solo las estadísticas NUEVAS del archivo"""
    stats_file = os.path.join(STATS_SRC_DIR, "named.stats")
    
    if not os.path.isfile(stats_file):
        print(f"[WARN] {stats_file} no encontrado")
        return
    
    # Verificar si el archivo ha sido truncado (reiniciado)
    current_size = os.path.getsize(stats_file)
    last_position = get_last_position()
    
    if current_size < last_position:
        print("[INFO] Archivo ha sido truncado, reiniciando lectura...")
        save_last_position(0)
        last_position = 0
    
    stats_data = parse_latest_stats(stats_file)
    
    if not stats_data:
        print("[INFO] No se extrajeron datos nuevos")
        return
    
    # Verificar que tenemos datos válidos
    try:
        hits = int(stats_data.get('cache_hits', 0))
        misses = int(stats_data.get('cache_misses', 0))
        
        if hits == 0 and misses == 0:
            print("[INFO] Datos extraídos son todos ceros, posiblemente no hay datos nuevos")
            return
    except:
        pass
    
    # Añadir columnas adicionales
    final_data = {
        'Timestamp': stats_data.get('Timestamp', ''),
        'Hora': stats_data.get('Hora', ''),
        'Archivo': stats_data.get('Archivo', ''),
        'cache_hits': stats_data.get('cache_hits', "0"),
        'cache_hits_from_query': stats_data.get('cache_hits_from_query', "0"),
        'cache_misses': stats_data.get('cache_misses', "0"),
        'cache_misses_from_query': stats_data.get('cache_misses_from_query', "0"),
        'incoming_queries_A': stats_data.get('incoming_queries_A', "0")
    }
    
    # Append al CSV
    file_exists = os.path.isfile(REALTIME_CSV)
    
    try:
        with open(REALTIME_CSV, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=list(final_data.keys()))
            if not file_exists:
                writer.writeheader()
            writer.writerow(final_data)
        
        print(f" CSV actualizado: {REALTIME_CSV}")
        print(f"   Cache Hits: {final_data['cache_hits']}")
        print(f"   Cache Misses: {final_data['cache_misses']}")
        print(f"   Incoming Queries A: {final_data['incoming_queries_A']}")
        
    except Exception as e:
        print(f"[ERROR] Escribiendo CSV: {e}")

def process_stats_with_reset():
    """Procesa estadísticas, reseteando si es un nuevo ciclo"""
    stats_file = os.path.join(STATS_SRC_DIR, "named.stats")
    
    if not os.path.isfile(stats_file):
        print(f"[WARN] {stats_file} no encontrado")
        return
    
    # Leer todo el archivo
    with open(stats_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Encontrar TODOS los bloques de estadísticas
    stats_blocks = re.findall(r'\+\+\+ Statistics Dump \+\+\+.*?(?=\+\+\+ Statistics Dump \+\+\+|--- Statistics Dump ---|$)', content, re.S)
    
    if not stats_blocks:
        print("[WARN] No se encontraron bloques de estadísticas")
        return
    
    # Procesar solo el ÚLTIMO bloque
    latest_block = stats_blocks[-1]
    
    stats_data = {}
    stats_data['Timestamp'] = datetime.now().strftime("%d/%m/%Y")
    stats_data['Hora'] = datetime.now().strftime("%H:%M:%S")
    stats_data['Archivo'] = os.path.basename(stats_file)
    
    # Parsear el último bloque
    incoming_match = re.search(r'\+\+ Incoming Queries \+\+\s*\n\s*(\d+)\s+A', latest_block)
    stats_data['incoming_queries_A'] = incoming_match.group(1) if incoming_match else "0"
    
    # Cache Statistics
    cache_hits_match = re.search(r'(\d+)\s+cache hits(?:\s|$)', latest_block)
    stats_data['cache_hits'] = cache_hits_match.group(1) if cache_hits_match else "0"
    
    cache_misses_match = re.search(r'(\d+)\s+cache misses(?:\s|$)', latest_block)
    stats_data['cache_misses'] = cache_misses_match.group(1) if cache_misses_match else "0"
    
    cache_hits_query_match = re.search(r'(\d+)\s+cache hits \(from query\)', latest_block)
    stats_data['cache_hits_from_query'] = cache_hits_query_match.group(1) if cache_hits_query_match else "0"
    
    cache_misses_query_match = re.search(r'(\d+)\s+cache misses \(from query\)', latest_block)
    stats_data['cache_misses_from_query'] = cache_misses_query_match.group(1) if cache_misses_query_match else "0"
    
    # Validar
    hits = int(stats_data.get('cache_hits', 0))
    misses = int(stats_data.get('cache_misses', 0))
    
    if hits == 0 and misses == 0:
        print("[WARN] No se encontraron estadísticas válidas en el último bloque")
        return
    
    # Guardar en CSV
    final_data = {
        'Timestamp': stats_data.get('Timestamp', ''),
        'Hora': stats_data.get('Hora', ''),
        'Archivo': stats_data.get('Archivo', ''),
        'cache_hits': stats_data.get('cache_hits', "0"),
        'cache_hits_from_query': stats_data.get('cache_hits_from_query', "0"),
        'cache_misses': stats_data.get('cache_misses', "0"),
        'cache_misses_from_query': stats_data.get('cache_misses_from_query', "0"),
        'incoming_queries_A': stats_data.get('incoming_queries_A', "0")
    }
    
    file_exists = os.path.isfile(REALTIME_CSV)
    with open(REALTIME_CSV, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(final_data.keys()))
        if not file_exists:
            writer.writeheader()
        writer.writerow(final_data)
    
    print(f" Último bloque procesado y guardado")
    print(f"   Hits: {final_data['cache_hits']}")
    print(f"   Misses: {final_data['cache_misses']}")

if __name__ == "__main__":
    # Usar el método con reset (más robusto)
    process_stats_with_reset()