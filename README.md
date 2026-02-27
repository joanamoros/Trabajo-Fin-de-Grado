# DNS Cache Viewer – Trabajo Fin de Grado

Este repositorio contiene el código desarrollado para el Trabajo Fin de Grado cuyo objetivo es el análisis y visualización de la caché DNS interna del servidor **BIND9**, a partir de los ficheros de estadísticas y volcados de caché generados por el propio servidor.

El proyecto ha sido desarrollado y validado en un **entorno controlado** basado en una máquina virtual Linux, con **BIND 9.18.33 compilado desde código fuente**.

---

## Estructura del proyecto

```
visor_dns/
│
├── utils/
│   ├── __pycache__/
│   ├── __init__.py
│   └── colors.py
│
├── viewer/
│   ├── __pycache__/
│   ├── __init__.py
│   ├── cache_view.py
│   ├── dns_viewer.py
│   ├── hits_misses_view.py
│   ├── stats_view.py
│   ├── tempCodeRunnerFile.py
│   └── ui_setup.py
│
└── main.py
```

---

## Directorios necesarios (máquina virtual)

```bash
BASE_DIR="/media/sf_tfg_shared"
STATS_SRC="/media/sf_tfg_shared/named_stats"
DUMP_SRC="/media/sf_tfg_shared/named_dumps"
```

- `named.stats` se guardará en `named_stats/`
- `named_dump.db` se guardará en `named_dumps/`

---

## Snapshots de caché

Los snapshots (capturas instantáneas de caché) se almacenan en:

```
(...)/cacheviewer/cache_snapshots
```

---

## Pruebas desde una máquina externa

Usar:
- `dnsperf_cubo.sh`
- `dnsperf_gui.py`

---

## Gestión del servidor BIND9

```bash
sudo /usr/local/sbin/named -f -d 1 -c /usr/local/etc/named.conf
sudo /usr/local/sbin/rndc <comando>
```

---

## Instalación de BIND9

```bash
sudo apt update
sudo apt install build-essential libssl-dev libcap-dev libxml2-dev libuv1-dev libnghttp2-dev pkg-config make -y
```

```bash
wget https://downloads.isc.org/isc/bind9/9.18.33/bind-9.18.33.tar.xz
tar -xf bind-9.18.33.tar.xz
cd bind-9.18.33
./configure --prefix=/usr/local --sysconfdir=/usr/local/etc
sudo make -j$(nproc)
sudo make install
```

---

## Limitaciones

- Probado solo en máquina virtual Linux
- Requiere BIND9 compilado desde código fuente
- Rutas y permisos específicos

---

## Autor

Joan Amoros Ramírez
