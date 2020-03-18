import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
from matplotlib import cm
import shapely.geometry as sgeom

import cartopy.crs as ccrs
import cartopy.io.shapereader as shpreader

reds = cm.get_cmap('Reds', 8)

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
#ax.background_patch.set_visible(False)
#ax.outline_patch.set_visible(False)

ax.set_title('My First Map')

colors = []
for c in range(16):
    colors.append(reds(c/16))

ax.add_geometries(
    de_shapes,
    ccrs.PlateCarree(),
    facecolor=colors, edgecolor='black')

plt.savefig("MAP_DE.png")
