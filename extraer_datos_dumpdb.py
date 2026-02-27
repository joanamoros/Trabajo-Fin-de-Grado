import os
import csv
import glob

def exact_format_parser(input_path, output_path=None):
    """
    Parser específico para el formato exacto del archivo .db
    """
    if output_path is None:
        filename = os.path.basename(input_path)
        output_path = f"{filename.replace('.db', '.csv')}"
    
    records = []  # Lista para manejar cada IP individualmente
    
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            if line == '; answer':
                i += 1
                if i >= len(lines):
                    break
                    
                # Procesar bloque de answer
                current_domain = None
                
                while i < len(lines):
                    line = lines[i].strip()
                    
                    # Si encontramos otra sección, terminar este bloque
                    if line.startswith(';') and line != '; answer':
                        break
                    
                    # Procesar línea de registro
                    if line and not line.startswith(';'):
                        parts = line.split()
                        
                        # Verificar si es un registro A válido
                        if len(parts) >= 4 and 'A' in parts:
                            # Encontrar la posición de 'A'
                            a_pos = parts.index('A')
                            
                            if a_pos >= 2:  # Debe haber dominio y TTL antes
                                domain = parts[0].rstrip('.')
                                ttl = parts[a_pos - 1]
                                ip = parts[a_pos + 1]
                                
                                current_domain = domain
                                
                                # Añadir a la lista
                                records.append({
                                    'Domain': domain,
                                    'IP_Addresses': ip,
                                    'TTLs': ttl
                                })
                        
                        # Procesar líneas de continuación (solo TTL A IP)
                        elif len(parts) == 3 and parts[1] == 'A' and current_domain:
                            ttl = parts[0]
                            ip = parts[2]
                            
                            # Añadir con dominio vacío para continuación
                            records.append({
                                'Domain': '',  # Vacío para IPs adicionales del mismo dominio
                                'IP_Addresses': ip,
                                'TTLs': ttl
                            })
                    
                    i += 1
            else:
                i += 1
        
        # GUARDAR EN CSV
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Domain', 'IP_Addresses', 'TTLs'])
            
            for record in records:
                writer.writerow([
                    record['Domain'],
                    record['IP_Addresses'],
                    record['TTLs']
                ])
        
        print(f"Procesado: {os.path.basename(input_path)}")
        print(f"  Registros: {len(records)}")
        print(f"  CSV: {output_path}")
        
        # Mostrar estadísticas
        unique_domains = len(set(r['Domain'] for r in records if r['Domain']))
        total_ips = len(records)
        print(f"  Dominios únicos: {unique_domains}")
        print(f"  Total de IPs: {total_ips}")
        
        return records
        
    except Exception as e:
        print(f"ERROR procesando {input_path}: {str(e)}")
        return []

def process_all_files():
    """
    Procesa los archivos .db en la carpeta named_dumps
    """
    # Ruta de los archivos .db
    db_files = glob.glob('/media/sf_tfg_shared/named_dumps/named_dump*.db')
    
    if not db_files:
        print("No se encontraron archivos named_dump_*.db")
        return
    
    print(f"Encontrados {len(db_files)} archivos .db")
    
    total_records = 0
    total_domains = 0
    
    for db_file in db_files:
        print(f"\n" + "="*50)
        # Aquí se deja output_path directo a cache_real.csv
        output_csv = '/media/sf_tfg_shared/cacheviewer/cache_real.csv'
        records = exact_format_parser(db_file, output_csv)
        
        if records:
            total_records += len(records)
            unique_domains = len(set(r['Domain'] for r in records if r['Domain']))
            total_domains += unique_domains
    
    # Resumen final
    if total_records > 0:
        print(f"\n" + "="*50)
        print("RESUMEN FINAL")
        print("="*50)
        print(f"Total archivos procesados: {len(db_files)}")
        print(f"Total registros extraídos: {total_records}")
        print(f"Total dominios únicos: {total_domains}")


# Ejecutar el procesamiento
if __name__ == "__main__":
    print("Extracción de datos DNS desde archivos .db")
    print("=" * 50)
    
    process_all_files()
    print("\nProceso completado!")