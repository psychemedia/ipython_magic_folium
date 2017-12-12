from argparse import ArgumentParser
import shlex
from csv import reader
import os.path
from IPython.core.magic import (
    magics_class, line_magic, line_cell_magic, Magics)
from IPython.core.display import Image, HTML


import folium

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
        default_latlong = False

        #If we have several markers, guess the lat long
        if args.markers is not None:
            _markers = self.shell.user_ns[args.markers]
            if isinstance(_markers,dict):
                _markers = [_markers]
            elif isinstance(_markers,list):
                if isinstance(_markers[0],list) or isinstance(_markers[0],dict):
                    pass
                else:
                    _markers = [_markers]
            else: _markers = []
            
            markers = []
            extrema={'lat':[],'long':[]}
            for _marker in _markers:
                marker = {'popup':None}
                if isinstance(_marker,dict):
                    if 'latlng' in _marker:
                        marker['latlong'] = [float(x) for x in _marker[latlng].split(',')]
                    elif 'lat' in _marker and 'lng' in _marker:
                        marker['latlong'] = [_marker['lat'], _marker['lng']]
                    else: continue
                    if 'popup' in _marker:
                        marker['popup'] = _marker['popup']
                    markers.append(marker)
                elif isinstance(_marker,list) and len(_marker)>2:
                    marker['latlong'] = [float(x) for x in _marker[:2]]
                    if len(_marker)>2:
                        marker['popup'] = str(_marker[2])
                    markers.append(marker)
                else: continue
                extrema['lat'].append(marker['latlong'][0])
                extrema['long'].append(marker['latlong'][1])
            maxlat=max(extrema['lat'])
            maxlon=max(extrema['long'])
            minlat=min(extrema['lat'])
            minlon=min(extrema['long'])
            latlong = [(maxlat+minlat)/2,(maxlon+minlon/2)]
        else: markers=[]
                
                
        #If we have a single marker, use that as a guess for latlong
        if args.marker is not None:
            #'52.0250,-0.7084,"sds sdsd"'
            marker = [i for i in reader([args.marker])][0]
            latlong = [float(x) for x in marker[:2]]
        
        if args.latlong is not None: 
            latlong = [float(x) for x in args.latlong.split(',')]
        elif args.geojson is not None:
            if os.path.isfile(args.geojson):
                from fiona import open as fi_open
                with fi_open(args.geojson) as fi:
                    latlong = [(fi.bounds[1]+fi.bounds[3])/2,
                               (fi.bounds[0]+fi.bounds[2])/2]
        if latlong is None:
            latlong = DEFAULT_LAT_LONG
            default_latlong = True
        
        if args.basemap is not None \
            and args.basemap in self.shell.user_ns and type(self.shell.user_ns[args.basemap])== folium.folium.Map:
            m = self.shell.user_ns[args.basemap]
        elif args.basemap is None \
            and '_' in self.shell.user_ns and type(self.shell.user_ns['_'])== folium.folium.Map:
            m = self.shell.user_ns['_']
            if not default_latlong:
                m.location = latlong
            if args.zoom is not None: m.zoom_start=args.zoom
        else:
            m = folium.Map(location=latlong, zoom_start=args.zoom)
        
        
        if args.marker is not None:
            if len(marker)==3:
                folium.Marker(latlong,popup=str(marker[2])).add_to(m)
            else:
                folium.Marker(latlong).add_to(m)

        for marker in markers:
            folium.Marker(marker['latlong'],popup=marker['popup']).add_to(m)
                
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
        
    @line_magic
    def folium_new_map(self,line):
        ''' Map arguments '''
        return self.folium_map( '-b None {}'.format(line) )
        
def load_ipython_extension(ipython):
    ipython.register_magics(FoliumMagic)
    
ip = get_ipython()
ip.register_magics(FoliumMagic)