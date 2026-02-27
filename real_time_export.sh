#!/bin/bash
# real_time_export.sh 

STATS_SRC="/media/sf_tfg_shared/named_stats/named.stats"
DUMP_SRC="/media/sf_tfg_shared/named_dumps/named_dump.db"
BASE_DIR="/media/sf_tfg_shared"
OUT_DIR="/media/sf_tfg_shared/cacheviewer"
SNAPSHOTS_DIR="$OUT_DIR/cache_snapshots"
PYTHON_SCRIPTS_DIR="$BASE_DIR"

# Obtener tiempo total 
TOTAL_TIME=${1:-0}  

# Crear directorios 
mkdir -p "$OUT_DIR"
mkdir -p "$SNAPSHOTS_DIR"
mkdir -p "$(dirname "$STATS_SRC")"
mkdir -p "$(dirname "$DUMP_SRC")"

echo "[INFO] ========================================="
echo "[INFO] Generador en tiempo real sincronizado"
echo "[INFO] Tiempo total configurado: ${TOTAL_TIME}s (0=infinito)"
echo "[INFO] Directorio base: $BASE_DIR"
echo "[INFO] Snapshots: $SNAPSHOTS_DIR"
echo "[INFO] ========================================="

# Limpieza inicial de archivos
echo "[INFO] Limpiando archivos anteriores..."
rm -f "$STATS_SRC"
rm -f "$DUMP_SRC"
rm -f "$SNAPSHOTS_DIR"/*.csv
rm -f "$OUT_DIR/stats_real.csv"
rm -f "$OUT_DIR/cache_real.csv"

# Inicializar contadores
ITERATION=0
SNAPSHOT_COUNTER=0
START_TIME=$(date +%s)

# Calcular tiempo restante
get_remaining_time() {
    if [ $TOTAL_TIME -eq 0 ]; then
        echo "infinito"
    else
        CURRENT_TIME=$(date +%s)
        ELAPSED=$((CURRENT_TIME - START_TIME))
        REMAINING=$((TOTAL_TIME - ELAPSED))
        echo "${REMAINING}s"
    fi
}

# Limpiar la caché
echo "[INFO] Limpiando caché inicial..."
sudo /usr/local/sbin/rndc flush


# Bucle principal (sincronizado)
while true; do
    if [ $TOTAL_TIME -gt 0 ]; then
        CURRENT_TIME=$(date +%s)
        ELAPSED=$((CURRENT_TIME - START_TIME))
       
        if [ $ELAPSED -ge $TOTAL_TIME ]; then
            echo "[INFO] Tiempo total alcanzado. Finalizando..."
            break
        fi
    fi
   
    ITERATION=$((ITERATION + 1))
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    REMAINING=$(get_remaining_time)
   
    echo ""
    echo "[INFO] [$TIMESTAMP] Iteración #$ITERATION (Tiempo restante: $REMAINING)"
   
    # 1) Ejecutar estadísticas
    echo "[INFO]   Ejecutando rndc stats..."
    sudo /usr/local/sbin/rndc stats
   
    # 2) Ejecutar dumpdb
    echo "[INFO]   Ejecutando rndc dumpdb -cache..."
    sudo /usr/local/sbin/rndc dumpdb -cache
   
    # Verificar archivos
    if [ ! -f "$STATS_SRC" ] || [ ! -f "$DUMP_SRC" ]; then
        echo "[WARN]   Archivos no encontrados, omitiendo..."
        continue
    fi
   
    # 3) Procesar estadísticas
    echo "[INFO]   Procesando estadísticas..."
    if python3 "$PYTHON_SCRIPTS_DIR/extraer_datos_stats.py"; then
        echo "[OK]     stats_real.csv actualizado"
    fi
   
    # 4) Procesar dump y crear snapshot
    echo "[INFO]   Procesando volcado de caché..."
    SNAPSHOT_FILE="$SNAPSHOTS_DIR/cache_snapshot_${TIMESTAMP}.csv"
   
    if python3 "$PYTHON_SCRIPTS_DIR/extraer_datos_dumpdb.py"; then
        CACHE_REAL_FILE="$OUT_DIR/cache_real.csv"
        if [ -f "$CACHE_REAL_FILE" ]; then
            cp "$CACHE_REAL_FILE" "$SNAPSHOT_FILE"
            SNAPSHOT_COUNTER=$((SNAPSHOT_COUNTER + 1))
            echo "[OK]     Snapshot #$SNAPSHOT_COUNTER creado"
        fi
    fi
   
    sleep 1  # Intervalo entre iteraciones
done

echo ""
echo "[INFO] ========================================="
echo "[INFO] Exportación finalizada"
echo "[INFO] Iteraciones totales: $ITERATION"
echo "[INFO] Snapshots generados: $SNAPSHOT_COUNTER"
echo "[INFO] ========================================="
