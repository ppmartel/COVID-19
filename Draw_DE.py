import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import shapely.geometry as sgeom

import cartopy.crs as ccrs
import cartopy.io.shapereader as shpreader

fig = plt.figure()
ax = fig.add_axes([0, 0, 1, 1], projection=ccrs.EuroPP())

#ax.set_extent([5, 15, 47, 57], ccrs.PlateCarree())
ax.set_extent([200000, 1000000, 5200000, 6200000], crs=ccrs.EuroPP())

de_reader = shpreader.Reader('GADM/gadm36_DEU_1.shp')
de_states = list(de_reader.records())
de_shapes = list(de_reader.geometries())
print(de_states[0].attributes['GID_1']+" - "+de_states[0].attributes['NAME_1'])

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

colors = ['black','red','orange','yellow','green','cyan','blue','magenta','black','red','orange','yellow','green','cyan','blue','magenta']

ax.add_geometries(
    de_shapes,
    ccrs.PlateCarree(),
    facecolor=colors, edgecolor='black')

#ax.add_geometries(
#    de_shapes,
#    ccrs.PlateCarree(),
#    styler=colorize_state)

plt.savefig("MAP_DE.png")
