# ipython_magic_folium

IPython Magic for [`folium` maps](https://github.com/python-visualization/folium).

This extension provides magic form embedding maps in Jupyter notebooks using `folium`.

To install:

`pip install git+https://github.com/psychemedia/ipython_magic_folium.git`

To load the magic in a Jupyter notebook:

`%load_ext folium_magic`

Then call as: `%folium_map`

To guarantee working with a fresh map object, use: `%folium_new_map`

The magic currently only works as line magic.

See the `folium_magic_demo.ipynb` notebook for examples, or run using *Binder*.

[![Binder](https://mybinder.org/badge.svg)](https://mybinder.org/v2/gh/psychemedia/ipython_magic_folium/master?filepath=folium_magic_demo.ipynb)

### Create a Map or Build on an Existing Map

- No arguments - create a default map; the magic return s a `folium` map object which can be rendered if the line magic is the last item in a code cell, or assigned to a variable; if the previously executed cell output (that is, the contents of the IPython `_` variable is a `folium` map, that map will be used as the starting map).
- `-b`, `--basemap`: pass in the name of a variable whose value is set to an existing `folium` map; to override the automatic reuse of previous maps, set `-b None`.

If a map is constructed from a previous map, if a new zoom level and/or new centre location is defined, those details will be used to plot the updated map.

### Display Map

- `-l`, `--latlong`: latitude and longitude values, comma separated. If no value is provided a default location will be used;
- `-z`, `--zoom` (`default=10`): set initial zoom level;
- `-a`, `--address`: specify an address (in quotes) and the map will be created, centered on that location, and with a marker locating the address.

![](images/folium_magic_demo.png)

### Add markers

- `-m`, `--marker`: add a single marker, passed as a comma separated string with no spaces after commas; eg `52.0250,-0.7084,"My marker"`

![](images/folium_magic_demo2.png)

- `-M`,`--markers`: add multiple markers from a Python variable; pass in the name of a variable that refers to:
  - a single dict, such as `markers={'lat':52.0250, 'lng':-0.7084,'popup':'Open University, Walton Hall'}`
  - a single ordered list, such as `markers=[52.0250, -0.7084,'Open University, Walton Hall']`
  - a list of dicts, such as `markers=[{'lat':52.0250, 'lng':-0.7084,'popup':'Open University, Walton Hall'},{'lat':52.0, 'lng':-0.70,'popup':'Open University, Walton Hall'}]`
  - a list of ordered lists, such as `markers=[[52.0250, -0.7084,'Open University, Walton Hall'], [52., -0.7,'Open University, Walton Hall']]`

![](images/folium_magic_demo3.png)

 - `-C`, `--clustermarkers`: add markers to a cluster; use the same marker convention as for adding multiple markers

If no `-l` co-ordinate is set to centre the map, the co-ordinates of the single marker, or the mid-point of the multiple markers, are used instead.

### Display `geojson` / `topojson` file

- `-g`, `--geojson`: path to a geoJSON file
- `-t`, `--topojson`: path a topJSON file *(likely to be very flaky atm...)*

![](images/folium_magic_demo4.png)

If no `-l` co-ordinate is set to centre the map, the mid-point of the geojson boundary is used instead.

### Display a Choropleth Map

A choropoleth map is displayed if enough information is provided to disaplay one.

- `-g`, `--geojson`: path to a geoJSON file
- `-d`, `--data`: the data source, either in the form of a `pandas` dataframe, or the path to a csv data file
- `-c`, `--columns`: comma separated (no space after comma) column names from the data source that specify: *column to match geojson key,column containing values to display*
- `-k`, `--key`: key in geojson file to match areas with data values in data file;
- optional:
  - `-p`, `--palette`: default=`'PuBuGn'`
  - `-o`, `--opacity`: default=`0.7`

![](images/folium_magic_demo5.png)
![](images/folium_magic_demo6.png)

### Adding Additional Layers

The magic can be used to add additional features to a pre-existing map.

For example, we can pass a `folium` map object in to the magic using the `-b` / `--basemap` parameter:

```
x = %folium_map -m 52.0250,-0.7084,"My marker"
%folium_map -b x -m 52.02,-0.708,"My other marker"
```

The magic will also reuse a pre-existing map if the last item returned from a code cell execution (that is, the contents of the IPython `_` variable) is a `folium` map object. So for example, if you execute notebook cells in order, and the previous cell returned a map, using the magic in the current cell will add to that map. *You can override this behaviour by using the `-R / --reset` flag, which will force the creation of a new map.*

To guarantee using a fresh map, use `%folium_new_map` rather than `%folium_map`, or use ``%folium_map -b None`. 

## Helper Magic

The `%geo_suggester` magic provides assistance for determing what columns may be appropriate in data files, and what properties may be appropriate in geojson files, when plotting choropleth maps:

`%geo_suggester -g boundaries/iw.json`

`%geo_suggester -d data/iw_turnout.csv`

`%geo_suggester -g boundaries/iw.json -d data/iw_turnout.csv`

## Python API

I have started to pull out a Python API so we can use this outside of the magic. For example:

```python
from folium_magic.folium_tools import folium_map as fm

folium_map({"marker":'52.0250,-0.7084,"My marker"',"zoom":12})
```

The structure of the dictionary follows the argument parameter names in the magic.
