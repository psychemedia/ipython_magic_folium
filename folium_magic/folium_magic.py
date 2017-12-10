from argparse import ArgumentParser
import shlex
from csv import reader
import os.path
from IPython.core.magic import (
    magics_class, line_magic, line_cell_magic, Magics)
from IPython.core.display import Image, HTML


import folium


@magics_class
class FoliumMagic(Magics):
    def __init__(self, shell, cache_display_data=False):
        super(FoliumMagic, self).__init__(shell)
        self.cache_display_data = cache_display_data

    @line_magic
    def folium_map(self,line, cell=''):
        ''' Map arguments '''
        parser = ArgumentParser()
        parser.add_argument('-l', '--latlong', default=None)
        parser.add_argument('-m', '--marker', default=None)
        parser.add_argument('-g', '--geojson', default=None)
        #For markers, pass in a list of dicts: [{'lat':x,'lng':y,'latlng''x,y',popup:'txt'}]
        #or a list of lists [ [lat, lng,'popup txt']
        parser.add_argument('-M','--markers',default=None)
        parser.add_argument('-z', '--zoom', default=10 )
        parser.add_argument('-d','--data',default=None)
        parser.add_argument('-c','--columns',default=None)
        parser.add_argument('-k','--key',default=None)
        parser.add_argument('-p','--palette',default='PuBuGn')
        parser.add_argument('-o','--opacity',default=0.7)
        args = parser.parse_args(shlex.split(line))

        latlong = None
        if args.latlong is not None: 
            latlong = [float(x) for x in args.latlong.split(',')]
        elif args.geojson is not None:
            if os.path.isfile(args.geojson):
                from fiona import open as fi_open
                with fi_open(args.geojson) as fi:
                    latlong = [(fi.bounds[1]+fi.bounds[3])/2,
                               (fi.bounds[0]+fi.bounds[2])/2]
        if latlong is None: latlong=[52.0250,-0.7084]
        
        m=folium.Map(location=latlong, zoom_start=args.zoom)
        
        if args.marker is not None:
            #'52.0250,-0.7084,"sds sdsd"'
            marker = [i for i in reader([args.marker])][0]
            if len(marker)==3:
                latlong = [float(x) for x in marker[:2]]
                folium.Marker(latlong,popup=str(marker[2])).add_to(m)
        
        if args.markers is not None:
            markers = self.shell.user_ns[args.markers]
            if isinstance(markers,dict):
                markers = [markers]
            elif isinstance(markers,list):
                if isinstance(markers[0],list) or isinstance(markers[0],dict):
                    pass
                else:
                    markers = [markers]
            else: markers = []
                
            for marker in markers:
                popup = None
                if isinstance(marker,dict):
                    if 'latlng' in marker:
                        latlong = [float(x) for x in marker[latlng].split(',')]
                    elif 'lat' in marker and 'lng' in marker:
                        latlong = [marker['lat'], marker['lng']]
                    else: continue
                    if 'popup' in marker:
                        popup = marker['popup']
                elif isinstance(marker,list) and len(marker)>2:
                    latlong = [float(x) for x in  marker[:2]]
                    if len(marker)>2:
                        popup=str(marker[2])
                else: continue

                folium.Marker(latlong,popup=popup).add_to(m)
                
        if args.geojson is not None:
            if os.path.isfile(args.geojson):
                folium.GeoJson( args.geojson, name='geojson' ).add_to(m)
                
        #Choropleth
        if args.geojson is not None and args.data is not None and args.columns is not None and args.key is not None:
            if os.path.isfile(args.data):
                from pandas import read_csv
                data = read_csv(args.data)
            else:
                data = self.shell.user_ns[args.data]
            if os.path.isfile(args.geojson):
                m.choropleth(geo_data=args.geojson,
                             data=data,
                             columns=[c for c in reader([args.columns])][0],
                             key_on=args.key,
                             fill_color=args.palette, fill_opacity=args.opacity
                            )
            
        return m
        
def load_ipython_extension(ipython):
    ipython.register_magics(FoliumMagic)
    
ip = get_ipython()
ip.register_magics(FoliumMagic)