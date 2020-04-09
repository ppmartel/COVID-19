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
# Country populations
##################################################

df_pop = pd.read_csv('Countries.csv', encoding='utf-8', index_col='Country')

##################################################
# Check whether the data already exists on disk
##################################################

if os.path.exists('COVID-19_WHO_Cases.csv'):
    print("Database exists - Reading it")

    df_cases = pd.read_csv('COVID-19_WHO_Cases.csv', encoding='utf-8', index_col='Country')
    df_deaths = pd.read_csv('COVID-19_WHO_Deaths.csv', encoding='utf-8', index_col='Country')

    first_dt = datetime.strptime('2020-02-03',"%Y-%m-%d")
    start_dt = datetime.strptime(df_cases.columns.values[-1],'%Y-%m-%d') + timedelta(1)
    start_rep = 14 + int ((start_dt - first_dt).days)
else:
    print("Database does not exist - Building it")

    ##################################################
    # Hard-code first data
    ##################################################
    
    df_cases = df_pop.copy()
    df_deaths = df_pop.copy()

    start_dt = datetime.strptime('2020-02-03',"%Y-%m-%d")
    start_rep = 14

##################################################
# Update data if needed
##################################################

end_dt = datetime.now() - timedelta(1)

for dt in range(int ((end_dt - start_dt).days)+1):
    new_date = start_dt + timedelta(dt)
    new_rep = start_rep + dt
    if new_rep >= 24:
        who_file = new_date.strftime("%Y%m%d")+"-sitrep-"+str(new_rep)+"-covid-19.pdf"
    else:
        who_file = new_date.strftime("%Y%m%d")+"-sitrep-"+str(new_rep)+"-ncov.pdf"
        
    new_date = new_date.strftime("%Y-%m-%d")
    print("Adding "+new_date+" to database")

    file = "WHO/"+who_file

    ##################################################
    # Download file from WHO if not on disk
    ##################################################

    if not os.path.exists(file):
        print("File missing - Downloading "+file)
        response = requests.get("https://www.who.int/docs/default-source/coronaviruse/situation-reports/"+who_file)
        if response.status_code >= 400:
            print("Does not exist")
            sys.exit()
        else:
            with open(file, 'wb') as f:
                f.write(response.content)

    ##################################################
    # Get World statistics
    ##################################################

    tab_who = tabula.read_pdf(file, pages="all", silent=True, pandas_options={'header': None})

    if len(tab_who) > 0:
        df_who = pd.concat(tab_who)
        cols = list(i for i in range(7,len(df_who.columns),1))
        df_who.drop(df_who.columns[cols], axis=1, inplace = True)
        df_who.replace(to_replace = '\s*\(.*\)', value = '', regex = True, inplace = True)
        df_who.replace(to_replace = '\s*\[.*\]', value = '', regex = True, inplace = True)

        if new_rep >= 42:
            # Format for reports 42+
            df_who.drop(df_who.columns[[2,4,5,6]], axis=1, inplace = True)
        elif new_rep >= 39:
            # Format for reports 39-41, fewer columns than the rest
            cols = list(i for i in range(3,len(df_who.columns),1))
            df_who.drop(df_who.columns[cols], axis=1, inplace = True)
        elif new_rep == 38:
            # Format for reports 38
            tab_who[2].drop(tab_who[2].columns[[2,3,4]], axis=1, inplace = True)
            tab_who[3].drop(tab_who[3].columns[[2,3,4,5]], axis=1, inplace = True)
            df_who = pd.concat(tab_who)
            df_who.replace(to_replace = '\s*\(.*\)', value = '', regex = True, inplace = True)
            df_who.replace(to_replace = '\s*\[.*\]', value = '', regex = True, inplace = True)
        elif new_rep == 31:
            # Special format for report 31, as Cases get merged into the country
            df_who = tab_who[1]
            df_who.replace(to_replace = '\s*\(.*\)', value = '', regex = True, inplace = True)
            df_who = df_who[df_who.columns[0]].str.rsplit(' ', 1, expand = True)
            df_who[2] = tab_who[1][4]
        elif new_rep >= 30:
            # Format for reports 30 and 32-37
            df_who.drop(df_who.columns[[2,3,4]], axis=1, inplace = True)
        elif new_rep >= 25:
            # Format for reports 25-29
            df_who.drop(df_who.columns[[1,3,4,5]], axis=1, inplace = True)
        elif new_rep >= 23:
            # Format for reports 23-24
            df_who.drop(df_who.columns[[0,3,4]], axis=1, inplace = True)
        elif new_rep == 17:
            # Format for reports 17
            df_who.drop(df_who.columns[[1,3,4,5]], axis=1, inplace = True)
        elif new_rep >= 14:
            # Format for reports 14-16 and 18-22
            df_who.drop(df_who.columns[[0,3]], axis=1, inplace = True)
        else:
            print("Not programmed to extract this report")
            sys.exit()

        df_who.replace(to_replace = '\s\d*$', value = '', regex = True, inplace = True)
        df_who = df_who[pd.to_numeric(df_who[df_who.columns[1]], errors='coerce').notnull()]
        df_who = df_who[pd.to_numeric(df_who[df_who.columns[2]], errors='coerce').notnull()]
        df_who.dropna(inplace = True)
        df_who.reset_index(drop = True, inplace = True)
        #df_who.drop(df_who.index[0], inplace = True)
            
        df_who.rename(columns = {df_who.columns[0]:'Country',df_who.columns[1]:'Cases',df_who.columns[2]:'Deaths'}, inplace=True)
        df_who['Country'] = df_who['Country'].astype(str)
        df_who['Cases'] = df_who['Cases'].astype(int)
        df_who['Deaths'] = df_who['Deaths'].astype(int)
        
        df_who['Country'] = df_who['Country'].str.replace('’','\'')
        df_who['Country'] = df_who['Country'].str.replace('\r',' ')
        df_who['Country'] = df_who['Country'].str.replace('\W*$','')
        df_who['Country'] = df_who['Country'].str.replace('^the ','')
        df_who['Country'] = df_who['Country'].str.replace('^The ','')
        df_who['Country'] = df_who['Country'].str.replace('Syria.*','Syria')
        df_who['Country'] = df_who['Country'].str.replace('.*Tanzania','Tanzania')
        df_who['Country'] = df_who['Country'].str.replace('occupied Palestinian territory','Palestine')
        df_who['Country'] = df_who['Country'].str.replace('^Kingdom','United Kingdom')
        df_who['Country'] = df_who['Country'].str.replace('^Congo','Republic of the Congo')
        df_who['Country'] = df_who['Country'].str.replace('Viet Nam','Vietnam')
        df_who['Country'] = df_who['Country'].str.replace(' of America','')
        df_who['Country'] = df_who['Country'].str.replace('Holy See','Vatican City')
        df_who['Country'] = df_who['Country'].str.replace('conveyance','Diamond Princess')
        df_who.replace(to_replace = 'Serbia.*', value = 'Serbia', regex = True, inplace = True)

        df_who.set_index('Country', inplace = True)
        df_who.to_csv('WHO/'+new_date+'.csv', index = True, encoding='utf-8')

        df_cases[new_date] = df_who['Cases']
        df_deaths[new_date] = df_who['Deaths']
        
##################################################
# Save and plot data
##################################################

df_cases.to_csv('COVID-19_WHO_Cases.csv', index = True, encoding='utf-8')
df_deaths.to_csv('COVID-19_WHO_Deaths.csv', index = True, encoding='utf-8')

df_cases.fillna(0, inplace = True)
df_deaths.fillna(0, inplace = True)

df_germany = df_cases.drop(['Continental Region','Statistical Region','Population'], axis=1).loc['Germany']
print(df_germany)
df_germany.plot(figsize=(15,7),legend=True)
#df_cases.set_index('Date', inplace=True)
#df_cases.groupby('Country')['Cases'].plot(figsize=(15,7),legend=True)
plt.savefig("COVID-19_WHO.png")

plt.clf()
#sys.exit()

##################################################
# Plot world map
##################################################

end_dt = end_dt.strftime("%Y-%m-%d")

reds = cm.get_cmap('Reds', 8)

fig = plt.figure(figsize=(13,8))
ax = fig.add_axes([0, 0, 1, 1], projection=ccrs.Robinson())

shapename = 'admin_0_countries'
#shapename = 'admin_0_sovereignty'
shapefile = shpreader.natural_earth(resolution='10m', category='cultural', name=shapename)
reader = shpreader.Reader(shapefile)
countries = list(reader.records())

# to get the effect of having just the states without a map "background"
# turn off the outline and background patches
#ax.background_patch.set_visible(False)
#ax.outline_patch.set_visible(False)

cases_max = max(df_cases.loc[:,end_dt])
print("Max = "+str(cases_max))
colors = []
shapes = []
for n in range(len(countries)):
    country = countries[n].attributes['NAME_LONG']
    if country == 'eSwatini': country = 'Eswatini'
    elif country == 'The Gambia': country = 'Gambia'
    elif country == 'Lao PDR': country = 'Laos'
    elif country == 'Dem. Rep. Korea': country = 'North Korea'
    elif country == 'Moldova': country = 'Republic of Moldova'
    elif country == 'Macedonia': country = 'North Macedonia'
    elif country == 'Czech Republic': country = 'Czechia'
    if country in df_cases.index:
        cases = df_cases.loc[country,end_dt]
        pop = df_cases.loc[country,'Population']
        print("{0:3d} - {1:35s}: Pop = {2:10.0f} - Cases = {3:5.0f} ({4:.2f} per thousand)".format(n, country, pop, cases, 1000*cases/pop))
        colors.append(reds(1000*cases/pop))
    else:
        print("{0:3d} - {1:35s}".format(n, country))
        colors.append(reds(0))
    shapes.append(countries[n].geometry)
    ax.add_geometries([shapes[n]], ccrs.PlateCarree(), facecolor=colors[n], edgecolor='black')
    
ax.set_title('COVID-19 Cases (WHO)')

plt.savefig("MAP_WHO.png")
