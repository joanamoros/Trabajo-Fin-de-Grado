# visor_dns/main.py
import tkinter as tk
from viewer.dns_viewer import DNSViewer

if __name__ == "__main__":
    root = tk.Tk()
    app = DNSViewer(root)
    root.mainloop()


