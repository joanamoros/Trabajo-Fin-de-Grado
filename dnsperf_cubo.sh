#!/bin/bash
# ============================================================================
# dnsperf_cubo.sh - Ejecución de dnsperf con segmentos y QPS variable
# ============================================================================
# Uso: ./dnsperf_cubo.sh <server> <segments> <segment_durations> 
#                        <qps_list> <queries_file>
# ============================================================================

echo "=== DNSPERF CONFIGURACIÓN CON SEGMENTOS ==="

# Validar número de parámetros
if [ $# -lt 5 ]; then
    echo "ERROR: Se requieren 5 parámetros"
    echo "Uso: $0 <server> <segments> <segment_durations> <qps_list> <queries_file>"
    echo "Ejemplo: $0 192.168.1.155 3 \"30,60,30\" \"100,500,100\" queries.txt"
    exit 1
fi

# Asignar parámetros
SERVER="$1"
SEGMENTS="$2"
SEGMENT_DURATIONS_STR="$3"
QPS_LIST_STR="$4"
QUERIES_FILE="$5"

# Convertir listas en arrays
IFS=',' read -ra DURATIONS <<< "$SEGMENT_DURATIONS_STR"
IFS=',' read -ra QPS_VALUES <<< "$QPS_LIST_STR"

# Validar que coincida el número de segmentos
if [ ${#DURATIONS[@]} -ne $SEGMENTS ] || [ ${#QPS_VALUES[@]} -ne $SEGMENTS ]; then
    echo "ERROR: Número de duraciones o QPS no coincide con segmentos"
    echo "Segmentos: $SEGMENTS"
    echo "Duraciones: ${#DURATIONS[@]}"
    echo "QPS: ${#QPS_VALUES[@]}"
    exit 1
fi

# Mostrar configuración
echo "---------------------------------------------"
echo "[CONFIGURACIÓN]"
echo "  Servidor:          $SERVER"
echo "  Segmentos:         $SEGMENTS"
echo "  Archivo queries:   $QUERIES_FILE"
echo "---------------------------------------------"
echo "  Segmento | Duración | QPS"
echo "---------------------------------------------"

TOTAL_DURATION=0
for i in $(seq 0 $(($SEGMENTS-1))); do
    echo "  $(($i+1))        | ${DURATIONS[$i]}s      | ${QPS_VALUES[$i]}"
    TOTAL_DURATION=$((TOTAL_DURATION + ${DURATIONS[$i]}))
done
echo "---------------------------------------------"
echo "  Duración total: $TOTAL_DURATION segundos"
echo "---------------------------------------------"
echo

# Verificar que existe el archivo de queries
if [ ! -f "$QUERIES_FILE" ]; then
    echo "ERROR: El archivo de queries '$QUERIES_FILE' no existe"
    exit 1
fi

# Verificar que dnsperf está instalado
if ! command -v dnsperf &> /dev/null; then
    echo "ERROR: dnsperf no está instalado o no está en el PATH"
    echo "Instala con: sudo apt-get install dnsperf"
    exit 1
fi

# Validar que todos los QPS sean mayores que 0
for i in $(seq 0 $(($SEGMENTS-1))); do
    if [ "${QPS_VALUES[$i]}" = "0" ] || [ "${QPS_VALUES[$i]}" -le "0" ]; then
        echo "ERROR: QPS del segmento $(($i+1)) debe ser mayor que 0"
        exit 1
    fi
done

# ============================================================
# NO HACER FLUSH AQUÍ - SE HACE EN real_time_export.sh EN LA MV
# ============================================================
echo "=== NOTA IMPORTANTE ==="
echo "El flush de caché se ejecutará en la MV (real_time_export.sh)"
# echo "Esperando 2 segundos para sincronización con MV..."
# sleep 2
echo

# ============================================================
# INICIAR PRUEBA DNSperf
# ============================================================
echo "=== INICIANDO PRUEBA DNSPERF ==="
echo "[$(date '+%H:%M:%S')] Iniciando prueba DNS..."

EXIT_CODE=0
START_TIME=$(date +%s)

# Ejecutar cada segmento
for i in $(seq 0 $(($SEGMENTS-1))); do
    DURATION=${DURATIONS[$i]}
    QPS=${QPS_VALUES[$i]}
    
    echo "---------------------------------------------"
    echo "SEGMENTO $(($i+1))/$SEGMENTS"
    echo "Duración: $DURATION segundos"
    echo "QPS: $QPS"
    echo "---------------------------------------------"
    
    # Ejecutar dnsperf con -S (estadísticas cada segundo) y -Q (siempre límite de QPS)
    CMD="dnsperf -s $SERVER -d \"$QUERIES_FILE\" -l $DURATION -Q $QPS -S 1 -q 1000 -t 5"
    echo "Comando: $CMD"
    echo
    
    SEGMENT_START=$(date +%s)
    eval $CMD
    SEGMENT_EXIT=$?
    SEGMENT_END=$(date +%s)
    
    if [ $SEGMENT_EXIT -ne 0 ]; then
        EXIT_CODE=$SEGMENT_EXIT
        echo "Segmento $(($i+1)) finalizado con código: $SEGMENT_EXIT"
    else
        echo "Segmento $(($i+1)) completado en $((SEGMENT_END - SEGMENT_START))s"
    fi
    
    # NO ejecutar flush entre segmentos
    # Actualizar duración total transcurrida
    TOTAL_DURATION=$((TOTAL_DURATION - DURATION))
    
    # Esperar entre segmentos si no es el último
    if [ $i -lt $(($SEGMENTS-1)) ]; then
        echo "⏳ Preparando siguiente segmento..."
        sleep 2
    fi
done

END_TIME=$(date +%s)
TOTAL_TIME=$((END_TIME - START_TIME))

# Mostrar resultados finales
echo "============================================="
if [ $EXIT_CODE -eq 0 ]; then
    echo "PRUEBA COMPLETADA EXITOSAMENTE"
else
    echo "PRUEBA FINALIZADA CON CÓDIGO DE SALIDA: $EXIT_CODE"
fi

echo "   Tiempo total: $TOTAL_TIME segundos"
echo "   Servidor: $SERVER"
echo "   Segmentos ejecutados: $SEGMENTS"
echo "   Flush ejecutado al inicio: sudo /usr/local/sbin/rndc flush"
echo "============================================="

exit $EXIT_CODE