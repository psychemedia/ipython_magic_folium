"""ipython-folium-magic"""
#__version__ = '0.0.3'

from .folium_magic import FoliumMagic

def load_ipython_extension(ipython):
    ipython.register_magics(FoliumMagic)