from datetime import timedelta, date, datetime
import cartopy.crs as ccrs
import cartopy.io.shapereader as shpreader
from matplotlib import cm
import matplotlib.pyplot as plt
import numpy as np
import os
import pandas as pd
import sys
import requests
import tabula

##################################################
# Check whether the data already exists on disk
##################################################

if os.path.exists('COVID-19_RKI_WW.csv'):
    print("Databases exist - Reading them")

    df_rki_ww_old = pd.read_csv('COVID-19_RKI_WW.csv', encoding='utf-8')
    df_rki_de_old = pd.read_csv('COVID-19_RKI_DE.csv', encoding='utf-8')

    df_rki_ww_all = [df_rki_ww_old]
    df_rki_de_all = [df_rki_de_old]

    start_dt = datetime.strptime(df_rki_ww_old['Date'].max(),'%Y-%m-%d') + timedelta(1)
else:
    print("Databases do not exist - Building them")

    ##################################################
    # Hard-code 2020-03-03 data
    ##################################################
    
    rki_ww_303 = {'Date' : '2020-03-03',
                  'Region' : ['Deutschland','Europa','China','Weltweit'],
                  'Cases' : [196,3367,80304,92138],
                  'Deaths' : [0,84,2946,3134]
    }
    df_rki_ww_303 = pd.DataFrame(rki_ww_303, columns = ['Date','Region','Cases','Deaths'])
    
    rki_de_303 = {'Date' : '2020-03-03',
                  'State' : ['Baden-Württemberg','Bayern','Berlin','Brandenburg','Bremen','Hamburg','Hessen','Mecklenburg-Vorpommern','Niedersachsen','Nordrhein-Westfalen','Rheinland-Pfalz','Saarland','Sachsen','Sachsen-Anhalt','Schleswig-Holstein','Thüringen'],
                  'Cases' : [28,37,3,1,2,2,12,0,2,103,2,0,1,0,2,1]
    }
    df_rki_de_303 = pd.DataFrame(rki_de_303, columns = ['Date','State','Cases'])
    
    ##################################################
    # Hard-code 2020-03-04 data
    ##################################################
    
    rki_ww_304 = {'Date' : '2020-03-04',
                  'Region' : ['Deutschland','Europa','China','Weltweit'],
                  'Cases' : [262,3483,80423,94150],
                  'Deaths' : [0,85,2984,3219]
    }
    df_rki_ww_304 = pd.DataFrame(rki_ww_304, columns = ['Date','Region','Cases','Deaths'])
    
    rki_de_304 = {'Date' : '2020-03-04',
                  'State' : ['Baden-Württemberg','Bayern','Berlin','Brandenburg','Bremen','Hamburg','Hessen','Mecklenburg-Vorpommern','Niedersachsen','Nordrhein-Westfalen','Rheinland-Pfalz','Saarland','Sachsen','Sachsen-Anhalt','Schleswig-Holstein','Thüringen'],
                  'Cases' : [50,48,7,1,3,3,12,4,7,115,7,1,1,0,2,1]
    }
    df_rki_de_304 = pd.DataFrame(rki_de_304, columns = ['Date','State','Cases'])

    df_rki_ww_all = [df_rki_ww_303,df_rki_ww_304]
    df_rki_de_all = [df_rki_de_303,df_rki_de_304]

    start_dt = datetime.strptime('2020-03-04',"%Y-%m-%d") + timedelta(1)

##################################################
# Update data if needed
##################################################

end_dt = datetime.now() - timedelta(1)

for dt in range(int ((end_dt - start_dt).days)+1):
    new_date = start_dt + timedelta(dt)
    new_date = new_date.strftime("%Y-%m-%d")
    print("Adding "+new_date+" to database")

    file = "RKI/"+new_date+"-de.pdf"

    ##################################################
    # Download file from RKI if not on disk
    ##################################################

    if not os.path.exists(file):
        print("File missing - Downloading")
        response = requests.get("https://www.rki.de/DE/Content/InfAZ/N/Neuartiges_Coronavirus/Situationsberichte/"+new_date+"-de.pdf?__blob=publicationFile")
        if response.status_code >= 400:
            print("Does not exist")
            sys.exit()
        else:
            with open(file, 'wb') as f:
                f.write(response.content)
    
    ##################################################
    # Get World statistics
    ##################################################

    tab_rki_ww = tabula.read_pdf(file, pages="1", silent=True, pandas_options={'header': None})

    #tabula.read_pdf("RKI/2020-03-10-de.pdf", pages="1", stream=True, guess=False)
    if len(tab_rki_ww) > 0:
        df_rki_ww_new = tab_rki_ww[0]
        
        if len(df_rki_ww_new.columns) > 4:
            df_rki_ww_new.drop(df_rki_ww_new.columns[0], axis=1, inplace=True)
        
        df_rki_ww_new.drop(df_rki_ww_new.columns[3], axis=1, inplace=True)
        df_rki_ww_new.rename(columns = {df_rki_ww_new.columns[0]:'Region',df_rki_ww_new.columns[1]:'Cases',df_rki_ww_new.columns[2]:'Deaths'}, inplace=True)
        df_rki_ww_new.dropna(inplace = True)
        df_rki_ww_new.replace(to_replace = 'Europa (einschl. D)', value = 'Europa', inplace = True)
        df_rki_ww_new.replace(to_replace = '.', value = '', inplace = True)
        df_rki_ww_new.reset_index(drop = True, inplace = True)

        df_rki_ww_new['Cases'] = df_rki_ww_new['Cases'].astype(str)
        df_rki_ww_new['Cases'] = [x.replace('.','') for x in df_rki_ww_new['Cases']]
        df_rki_ww_new['Cases'] = df_rki_ww_new['Cases'].astype(int)
        df_rki_ww_new['Deaths'] = df_rki_ww_new['Deaths'].astype(str)
        df_rki_ww_new['Deaths'] = [x.replace('.','') for x in df_rki_ww_new['Deaths']]
        df_rki_ww_new['Deaths'] = df_rki_ww_new['Deaths'].astype(int)
        df_rki_ww_new.insert(0, column='Date', value=new_date)

        df_rki_ww_all.append(df_rki_ww_new)

    ##################################################
    # Get Germany statistics
    ##################################################

    tab_rki_de = tabula.read_pdf(file, pages="2", silent=True, pandas_options={'header': None})

    if len(tab_rki_de) > 0:
        df_rki_de_new = tab_rki_de[0]

        if len(df_rki_de_new.columns) < 3:
            df_rki_de_new.dropna(inplace = True)
            df_rki_de_new = df_rki_de_new[df_rki_de_new.columns[0]].str.split(' ', 1, expand = True)
        else:
            cols = list(i for i in range(2,len(df_rki_de_new.columns),1))
            df_rki_de_new.drop(df_rki_de_new.columns[cols], axis=1, inplace=True)
        df_rki_de_new.rename(columns = {df_rki_de_new.columns[0]:'State',df_rki_de_new.columns[1]:'Cases'}, inplace=True)
        df_rki_de_new.dropna(inplace = True)

        df_rki_de_new = df_rki_de_new[df_rki_de_new['State'] != 'Bundesland']
        df_rki_de_new = df_rki_de_new[df_rki_de_new['State'] != 'Gesamt']
        df_rki_de_new.sort_values(by = 'State', ascending = True, inplace = True)
        df_rki_de_new.reset_index(drop = True, inplace = True)
        df_rki_de_new['Cases'] = df_rki_de_new['Cases'].astype(str)
        df_rki_de_new['Cases'] = [x.replace('.','') for x in df_rki_de_new['Cases']]
        df_rki_de_new['Cases'] = df_rki_de_new['Cases'].astype(int)
        df_rki_de_new.insert(0, column='Date', value=new_date)

        df_rki_de_all.append(df_rki_de_new)

##################################################
# Save and plot data
##################################################

df_rki_ww = pd.concat(df_rki_ww_all)
df_rki_ww.to_csv('COVID-19_RKI_WW.csv', index = False, encoding='utf-8')
df_rki_ww.set_index('Date', inplace=True)
df_rki_ww.groupby('Region')['Cases'].plot(figsize=(15,7),legend=True)
plt.savefig("COVID-19_RKI_WW.png")

plt.clf()

df_rki_de = pd.concat(df_rki_de_all)
df_rki_de.to_csv('COVID-19_RKI_DE.csv', index = False, encoding='utf-8')
df_rki_de.set_index('Date', inplace=True)
df_rki_de.groupby(['State'])['Cases'].plot(figsize=(15,7),legend=True)
plt.savefig("COVID-19_RKI_DE.png")

plt.clf()

##################################################
# Plot map of Germany
##################################################

end_dt = end_dt.strftime("%Y-%m-%d")

reds = cm.get_cmap('Reds', 8)

fig = plt.figure()
ax = fig.add_axes([0, 0, 1, 1], projection=ccrs.EuroPP())
ax.set_extent([200000, 1000000, 5200000, 6200000], crs=ccrs.EuroPP())

# to get the effect of having just the states without a map "background"
# turn off the outline and background patches
ax.background_patch.set_visible(False)
ax.outline_patch.set_visible(False)

de_reader = shpreader.Reader('GADM/gadm36_DEU_1.shp')
de_states = list(de_reader.records())

cases_max = max(df_rki_de.loc[:,'Cases'])
print("Max = "+str(cases_max))
colors = []
de_shapes = []
for n in range(len(de_states)):
    cases_state = df_rki_de[df_rki_de['State'] == de_states[n].attributes['NAME_1']].loc[end_dt,'Cases']
    print(str(n)+" - "+de_states[n].attributes['NAME_1']+" = "+str(cases_state))
    colors.append(reds(cases_state/cases_max))
    de_shapes.append(de_states[n].geometry)
    ax.add_geometries([de_states[n].geometry], ccrs.PlateCarree(), facecolor=reds(cases_state/cases_max), edgecolor='black')

ax.set_title('My First Map')

plt.savefig("MAP_DE.png")
