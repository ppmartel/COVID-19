import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import shapely.geometry as sgeom

import cartopy.crs as ccrs
import cartopy.io.shapereader as shpreader

fig = plt.figure()
ax = fig.add_axes([0, 0, 1, 1], projection=ccrs.LambertConformal())

ax.set_extent([-125, -66.5, 20, 50], ccrs.Geodetic())

shapename = 'admin_1_states_provinces_lakes_shp'
#states_shp = shpreader.natural_earth(resolution='10m',
states_shp = shpreader.natural_earth(resolution='110m',
                                     category='cultural', name=shapename)

# to get the effect of having just the states without a map "background"
# turn off the outline and background patches
ax.background_patch.set_visible(False)
ax.outline_patch.set_visible(False)

ax.set_title('My First Map')

def colorize_state(geometry):
    facecolor = (0.9375, 0.9375, 0.859375)
    #if geometry.intersects(track):
    #    facecolor = 'red'
    #elif geometry.intersects(track_buffer):
    #    facecolor = '#FF7E00'
    return {'facecolor': facecolor, 'edgecolor': 'black'}

ax.add_geometries(
    shpreader.Reader(states_shp).geometries(),
    ccrs.PlateCarree(),
    styler=colorize_state)

plt.savefig("MAP_US.png")
