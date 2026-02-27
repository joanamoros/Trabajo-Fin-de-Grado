# visor_dns/viewer/dns_viewer.py
import tkinter as tk
from tkinter import filedialog, messagebox
import os

# Importar mixins
from viewer.ui_setup import UISupport
from viewer.stats_view import StatsView
from viewer.cache_view import CacheView
from viewer.hits_misses_view import HitsMissesView

class DNSViewer(UISupport, StatsView, CacheView, HitsMissesView):
    """Clase principal del visor DNS que hereda de todos los mixins"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("DNS Cache Viewer")
        self.root.geometry("700x500")
        
        # Variables para almacenar archivos
        self.estadisticas_file = None
        self.cache_files = []
        
        self.setup_ui()