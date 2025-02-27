from argparse import ArgumentParser
import shlex

from IPython.core.magic import (
    magics_class, line_magic, line_cell_magic, Magics)
# from IPython.core.display import Image, HTML

import folium

from .folium_tools import marker_groups, get_data, geosuggester, folium_map

DEFAULT_LAT_LONG = [52.0250,-0.7084]

@magics_class
class FoliumMagic(Magics):
    def __init__(self, shell, cache_display_data=False):
        super(FoliumMagic, self).__init__(shell)
        self.cache_display_data = cache_display_data

    @line_magic
    def folium_map(self,line):
        ''' Map arguments '''
        parser = ArgumentParser()
        parser.add_argument('-b', '--basemap', default=None)
        parser.add_argument('-l', '--latlong', default=None)
        parser.add_argument('-m', '--marker', default=None)
        parser.add_argument('-g', '--geojson', default=None)
        parser.add_argument('-t', '--topojson', default=None)
        # For markers, pass in a list of dicts: [{'lat':x,'lng':y,'latlng''x,y',popup:'txt'}]
        # or a list of lists [ [lat, lng,'popup txt']
        parser.add_argument('-M','--markers',default=None)
        parser.add_argument('-C','--clustermarkers',default=None)
        parser.add_argument('-z', '--zoom', default=10 )
        parser.add_argument('-d','--data',default=None)
        parser.add_argument('-c','--columns',default=None)
        parser.add_argument('-k','--key',default=None)
        parser.add_argument('-p','--palette',default='PuBuGn')
        parser.add_argument('-o','--opacity',default=0.7)
        parser.add_argument('-a','--address',default=None)
        parser.add_argument('-R','--reset', action='store_true', help='Reset map')
        args = parser.parse_args(shlex.split(line))

        if (
            args.basemap is not None
            and args.basemap in self.shell.user_ns
            and type(self.shell.user_ns[args.basemap]) == folium.folium.Map
        ):
            m = self.shell.user_ns[args.basemap]
        elif (
            args.basemap is None
            and "_" in self.shell.user_ns
            and type(self.shell.user_ns["_"]) == folium.folium.Map
            and not args.reset
        ):
            m = self.shell.user_ns["_"]
        else:
            m = folium.Map()
        data = get_data(args.data)

        if args.markers in self.shell.user_ns:
            args.markers = self.shell.user_ns[args.markers]
        if args.clustermarkers in self.shell.user_ns:
            args.clustermarkers = self.shell.user_ns[args.clustermarkers]
        return folium_map(args, m, data)

    def _marker_groups(self,_markers):

        markers, latlong, maxlat, maxlon, minlat, minlon = marker_groups(_markers)
        return markers, latlong, maxlat, maxlon, minlat, minlon

    def _get_data(self, _df):
        if _df in self.shell.user_ns:
            return self.shell.user_ns[_df]
        else:
            return get_data(_df)

    @line_magic
    def folium_new_map(self,line):
        ''' Map arguments '''
        return self.folium_map( '-b None {}'.format(line) )

    @line_magic
    def geo_suggester(self,line):
        ''' Provide suggestions about data and shapefile properties '''
        parser = ArgumentParser()
        parser.add_argument('-g','--geojson',default=None)
        parser.add_argument('-d','--data',default=None)
        args = parser.parse_args(shlex.split(line))

        _data = self._get_data(args.data)
        return geosuggester(args, _data)

def load_ipython_extension(ipython):
    ipython.register_magics(FoliumMagic)

#ip = get_ipython()
#ip.register_magics(FoliumMagic)
