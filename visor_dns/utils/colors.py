# visor_dns/utils/colors.py
def darken_color(color, factor=0.2):
    """Oscurece un color hexadecimal"""
    color = color.lstrip('#')
    rgb = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
    rgb = tuple(max(0, int(c * (1 - factor))) for c in rgb)
    return f'#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}'

def lighten_color(color, factor=0.1):
    """Aclara un color hexadecimal"""
    color = color.lstrip('#')
    rgb = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
    rgb = tuple(min(255, int(c * (1 + factor))) for c in rgb)
    return f'#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}'