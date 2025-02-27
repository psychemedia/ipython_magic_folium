from setuptools import setup

setup(name='ipython_magic_folium',
      version='0.0.4',
	install_requires=['folium','fiona', 'geocoder', 'branca'],
      packages=['folium_magic']
)