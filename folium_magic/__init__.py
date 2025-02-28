"""ipython-folium-magic"""
# __version__ = '0.0.6'

from .folium_tools import folium_map, geosuggester

try:
    from .folium_magic import FoliumMagic

    def load_ipython_extension(ipython):
        ipython.register_magics(FoliumMagic)
except:
    print("IPython magics not supported.")