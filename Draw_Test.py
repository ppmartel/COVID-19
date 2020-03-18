import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.pyplot as plt


def main():
    fig = plt.figure()
    #ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())
    #ax.set_extent([5, 15, 47, 57], crs=ccrs.PlateCarree())
    ax = fig.add_subplot(1, 1, 1, projection=ccrs.EuroPP())
    ax.set_extent([200000, 1000000, 5200000, 6200000], crs=ccrs.EuroPP())

    ax.add_feature(cfeature.LAND)
    ax.add_feature(cfeature.OCEAN)
    ax.add_feature(cfeature.COASTLINE)
    ax.add_feature(cfeature.BORDERS, linestyle=':')
    ax.add_feature(cfeature.LAKES, alpha=0.5)
    ax.add_feature(cfeature.RIVERS)

    plt.savefig("MAP_Test.png")


if __name__ == '__main__':
    main()
