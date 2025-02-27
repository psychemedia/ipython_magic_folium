import os
from pandas import read_csv, DataFrame
from fiona import open as fi_open
from numpy import number
import folium
from csv import reader
import os.path
import geocoder
from folium.plugins import MarkerCluster
from types import SimpleNamespace
def _set(obj, key, value):
    if isinstance(obj, dict):
        # For dictionaries, set the key-value pair
        obj[key] = value
    elif hasattr(obj, key):
        # For objects, use setattr to set the attribute
        setattr(obj, key, value)
    else:
        # For objects that don't have the attribute, add it dynamically
        setattr(obj, key, value)

def get(obj, key, default=None):
    if isinstance(obj, dict):
        # For dictionaries, use the .get() method
        return obj.get(key, default)
    elif hasattr(obj, key):
        # For objects, use getattr to get the attribute
        return getattr(obj, key, default)
    return default  # Return the default value if it's neither a dict nor an object with the attribute


DEFAULT_LAT_LONG = [52.0250, -0.7084]

def get_data(df):
    _df = df
    if _df is not None:
        if os.path.isfile(_df):
            data = read_csv(_df)
        else:
            return DataFrame()
        return data
    return DataFrame()

def check_geojson(geojson):
    _geojson = geojson
    geo_json_check = False
    if _geojson is not None and os.path.isfile(_geojson):
        with fi_open(_geojson) as fi:
            geo_json_check = (fi.meta['driver'] == 'GeoJSON')
    return geo_json_check


def check_topojson(topojson):
    _topojson = topojson
    check_topojson = check_geojson( _topojson)
    if check_topojson:
        import json
        with open(_topojson) as r:
            j=json.load(r)
            check_topojson = ('type' in j) and (j['type'] == 'Topology')
    return check_topojson

def check_everything(data, fi, cols=None):
    guess_data_col = {}
    # Assume that the geojson keys are strings
    if cols is None:
        cols = data.select_dtypes(object).columns
    if cols is None:
        return None, 0
    for datacol in cols:
        guess_key, score = get_match_geo_property_with_data_col(
            fi, data, datacol
        )
        guess_data_col[(datacol, guess_key)] = score
    return guess_data_col


def get_schema_property_values(fi):
    props = {k: set() for k in fi.meta["schema"]["properties"].keys()}
    # Find the unique vals for each geojson property
    for k, v in fi.items():
        for k2 in v["properties"]:
            props[k2].add(v["properties"][k2])
    return props

def get_match_geo_property_with_data_col(fi, _data, _datacol):
    # Get the values in the data key column
    vals = set(_data[_datacol].unique())
    # Find what property keys are in the geojson
    props = get_schema_property_values(fi)
    # See which geojson property overlaps best with data keys
    matcher = {}
    for k in props:
        matches = props[k].intersection(vals)
        matcher[k] = len(matches)
    # https://stackoverflow.com/a/280156/454773
    _guesskey = max(matcher, key=matcher.get)
    guesskey = "feature.properties.{}".format(_guesskey)
    return guesskey, matcher[_guesskey]

def get_match_data_col_with_geo_property(fi, fi_key, _data):
    # Get the values in the geo-property column
    props = set()
    for k, v in fi.items():
        if "properties" in v and fi_key in v["properties"]:
            props.add(v["properties"][fi_key])
    # Find the unique vals for each data col
    datakeys = _data.select_dtypes(object).columns
    # See which geojson property overlaps best with data keys
    matcher = {}
    for k in datakeys:
        matches = props.intersection(set(_data[k].unique()))
        matcher[k] = len(matches)
    # https://stackoverflow.com/a/280156/454773
    guesskey = max(matcher, key=matcher.get)
    return guesskey, matcher[guesskey]

def guess_everything(self, data, fi, cols=None):
    guess_data_col = self._check_everything(data, fi, cols=cols)
    return max(guess_data_col, key=guess_data_col.get)

def marker_groups(markers):
    """Handle marker groups."""
    _markers=markers
    if isinstance(_markers,dict):
        _markers = [_markers]
    elif isinstance(_markers,list):
        if isinstance(_markers[0],list) or isinstance(_markers[0],dict):
            pass
        else:
            _markers = [_markers]
    else:
        _markers = []

    markers = []
    extrema={'lat':[],'long':[]}
    for _marker in _markers:
        marker = {'popup':None}
        if isinstance(_marker,dict):
            if 'latlng' in _marker:
                marker['latlong'] = [float(x) for x in _marker['latlng'].split(',')]
            elif 'lat' in _marker and 'lng' in _marker:
                marker['latlong'] = [_marker['lat'], _marker['lng']]
            else:
                continue
            if 'popup' in _marker:
                marker['popup'] = _marker['popup']
            markers.append(marker)
        elif isinstance(_marker,list) and len(_marker)>2:
            marker['latlong'] = [float(x) for x in _marker[:2]]
            if len(_marker)>2:
                marker['popup'] = str(_marker[2])
            markers.append(marker)
        else:
            continue
        extrema['lat'].append(marker['latlong'][0])
        extrema['long'].append(marker['latlong'][1])
    maxlat=max(extrema['lat'])
    maxlon=max(extrema['long'])
    minlat=min(extrema['lat'])
    minlon=min(extrema['long'])
    latlong = [(maxlat+minlat)/2,(maxlon+minlon/2)]
    return markers, latlong, maxlat, maxlon, minlat, minlon


def geosuggester(args, data):
    _data=data

    items = {"strcols": [], "numcols": [], "props": [], "jntcols": []}
    if _data is not None:

        items["strcols"] = _data.select_dtypes(object)
        items["numcols"] = _data.select_dtypes(number).columns.tolist()
        print("Data - numeric cols: {}".format(", ".join(items["numcols"])))
        strvals = [
            "{} ({})".format(p, sorted(list(items["strcols"][p]))[:3] + ["..."])
            for p in items["strcols"]
        ]
        print("Data - object cols: {}".format(", ".join(strvals)))

    if check_geojson(get(args,'geojson')):

        with fi_open(get(args,'geojson')) as fi:
            items["props"] = get_schema_property_values(fi)
            matches = check_everything(_data, fi, items["strcols"])
        items["jntcols"] = {m: matches[m] for m in matches if matches[m] > 0}
        propvals = [
            "{} ({})".format(p, sorted(list(items["props"][p]))[:3] + ["..."])
            for p in items["props"]
        ]
        print("Geojson - properties cols: {}".format(", ".join(propvals)))
        if _data is not None:
            matchlabels = [
                "{} ({})".format(k, items["jntcols"][k]) for k in items["jntcols"]
            ]
            print(
                "Possible matches between data and geojson: {}".format(
                    ", ".join(matchlabels)
                )
            )
    return items

def folium_map(args, m=None, data=None):

    # We should do a stronger cast and cast list/dict to df if we can?
    data = DataFrame() if data is None else data

    latlong = None
    default_latlong = False

    if get(args,'zoom') is None:
        _set(args,'zoom', 5)

    # If we have several markers, guess the lat long
    if get(args,'clustermarkers') is not None:
        clustermarkers, latlong, maxlat, maxlon, minlat, minlon = marker_groups(get(args,'clustermarkers'))

    if get(args,'markers') is not None:
        markers, latlong, maxlat, maxlon, minlat, minlon = marker_groups(get(args,'markers'))
    else:
        markers = []

    # If we have a single marker, use that as a guess for latlong
    if get(args,'marker') is not None:
        #'52.0250,-0.7084,"sds sdsd"'
        marker = [i for i in reader([get(args,'marker')])][0]
        latlong = [float(x) for x in marker[:2]]

    if get(args,'latlong') is not None: 
        latlong = [float(x) for x in get(args,'latlong').split(',')]
    elif get(args,'address') is not None:
        latlong = geocoder.osm(get(args,'address')).latlng
        address_latlong = latlong
    elif get(args,'geojson') is not None:
        if os.path.isfile(get(args,'geojson')):
            with fi_open(get(args,'geojson')) as fi:
                latlong = [(fi.bounds[1]+fi.bounds[3])/2,
                               (fi.bounds[0]+fi.bounds[2])/2]

    if latlong is None:
        latlong = DEFAULT_LAT_LONG
        default_latlong = True

    if m is None:
        m = folium.Map(location=latlong, zoom_start=get(args,'zoom'))

    # Choropleth or boundary
    if check_geojson(get(args,'geojson')):
        columns = (
            None if get(args,'columns') is None else [c for c in reader([get(args,'columns')])][0]
        )
        # Check we have some legitimate data

        if not data.empty:
            with fi_open(get(args,'geojson')) as fi:
                if columns is not None and get(args,'key') is None:
                    if len(columns) == 2:
                        datakeycolumn = columns[0]
                    # Can we match a key to the dataset?
                    # Look for opportunities to match data col with geojson keys
                    if (len(columns) == 2) and (datakeycolumn in data.columns):
                        _kv, dummyscore = get_match_geo_property_with_data_col(
                            fi, data, datakeycolumn
                        )
                        set(args,'key', _kv)
                    elif len(columns) == 1:
                        # See if we can guess match key for data and geojson
                        datakeycolumn, _kv = guess_everything(data, fi)
                        set(args,'key', _kv)
                        if datakeycolumn:
                            columns = [datakeycolumn]+columns
                        # We also assume that a single colname is the value
                        # ...but what if it's the key? Test for this?
                elif columns is not None and len(columns)==1 and get(args,'key') is not None:
                    # See if we can guess match key for data and geojson
                    datakeycolumn, dummyscore = get_match_data_col_with_geo_property(fi, get(args,'key'), data)
                    columns = [datakeycolumn]+columns
                elif get(args,'columns') is None and get(args,'key') is not None:
                    # See if we can guess the get(args,'key')
                    # We also need to guess a value datacol
                    datakeycol, dummyscore = get_match_data_col_with_geo_property(fi, get(args,'key'), data)
                    # TO BE CONTINUED

            if not data.empty and columns is not None and get(args,'key') is not None:
                m.choropleth(geo_data=get(args,'geojson'),
                                 data=data,
                                 columns=columns,
                                 key_on=get(args,'key'),
                                 fill_color=get(args,'palette'), fill_opacity=get(args,'opacity')
                                )
        else:
            # Just plot the boundary
            #
            folium.GeoJson( get(args,'geojson'), name='geojson' ).add_to(m)

    if check_topojson(get(args,'topojson')):
        with open( get(args,'topojson') ) as tf:
            m.choropleth(tf,topojson='objects.collection', smooth_factor=0.5)

    if get(args,'marker') is not None:
        if len(marker)==3:
            folium.Marker(latlong,popup=str(marker[2])).add_to(m)
        else:
            folium.Marker(latlong).add_to(m)

    if get(args,'address') is not None:
        folium.Marker(address_latlong,popup=str(get(args,'address'))).add_to(m)

    for marker in markers:
        folium.Marker(marker['latlong'],popup=marker['popup']).add_to(m)

    if get(args,'clustermarkers') is not None:
        marker_cluster = MarkerCluster().add_to(m)
        for marker in clustermarkers:
            folium.Marker(marker['latlong'] ,popup=marker['popup']).add_to(marker_cluster)

    return m
