from datetime import timedelta, date, datetime
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

first_dt = datetime.strptime('2020-01-21',"%Y-%m-%d")
first_rep = 1

if os.path.exists('COVID-19_WHO_Cases.csv'):
    print("Database exists - Reading it")

    df_cases = pd.read_csv('COVID-19_WHO_Cases.csv', encoding='utf-8', index_col='Country')
    df_deaths = pd.read_csv('COVID-19_WHO_Deaths.csv', encoding='utf-8', index_col='Country')

    start_dt = datetime.strptime(df_cases.columns.values[-1],'%Y-%m-%d') + timedelta(1)
    start_rep = first_rep + int ((start_dt - first_dt).days)
else:
    print("Database does not exist - Building it")

    ##################################################
    # Hard-code first data
    ##################################################
    
    df_cases = df_pop.copy()
    df_deaths = df_pop.copy()

    start_dt = datetime.strptime('2020-02-03',"%Y-%m-%d")
    start_rep = 14
    
end_dt = datetime.now() - timedelta(1)
end_rep = first_rep + int ((end_dt - first_dt).days)

##################################################
# Update data if needed
##################################################

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
        cases_tot = pd.to_numeric(df_who[df_who[0] == "Grand total"][1].replace(' ', '', regex = True).values[0])
        deaths_tot = pd.to_numeric(df_who[df_who[0] == "Grand total"][3].replace(' ', '', regex = True).values[0])

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
            
        df_who.rename(columns = {df_who.columns[0]:'Country',df_who.columns[1]:'Cases',df_who.columns[2]:'Deaths'},
            inplace=True)
        df_who['Country'] = df_who['Country'].astype(str)
        df_who['Cases'] = df_who['Cases'].astype(int)
        df_who['Deaths'] = df_who['Deaths'].astype(int)
        
        df_who['Country'] = df_who['Country'].str.replace('’','\'')
        df_who['Country'] = df_who['Country'].str.replace('\r',' ')
        df_who['Country'] = df_who['Country'].str.replace('\W*$','')
        df_who['Country'] = df_who['Country'].str.replace('^Bahamas','The Bahamas')
        df_who['Country'] = df_who['Country'].str.replace('Bonaire, Sint Eustatius and Saba',
                                                          'Caribbean Netherlands')
        df_who['Country'] = df_who['Country'].str.replace('Brunei Darussalam','Brunei')
        df_who['Country'] = df_who['Country'].str.replace('^Congo','Republic of the Congo')
        df_who['Country'] = df_who['Country'].str.replace('.*Ivoire','Ivory Coast')
        df_who['Country'] = df_who['Country'].str.replace('Holy See','Vatican')
        df_who['Country'] = df_who['Country'].str.replace('Eswatini', 'eSwatini')
        df_who['Country'] = df_who['Country'].str.replace('^Lao.*', 'Laos')
        df_who['Country'] = df_who['Country'].str.replace('occupied Palestinian territory','Palestine')
        df_who['Country'] = df_who['Country'].str.replace('.*Mariana.*','Northern Mariana Islands')
        df_who['Country'] = df_who['Country'].str.replace('Republic of Korea', 'South Korea')
        df_who['Country'] = df_who['Country'].str.replace('Republic of Moldova', 'Moldova')
        df_who['Country'] = df_who['Country'].str.replace('Russian Federation', 'Russia')
        df_who['Country'] = df_who['Country'].str.replace('Saint Barthélemy','Saint Barthelemy')
        df_who['Country'] = df_who['Country'].str.replace('Serbi.*','Republic of Serbia')
        df_who['Country'] = df_who['Country'].str.replace('Syrian Arab Republic','Syria')
        df_who['Country'] = df_who['Country'].str.replace('Timor-Leste','East Timor')
        df_who['Country'] = df_who['Country'].str.replace('The United','United')
        df_who['Country'] = df_who['Country'].str.replace('^Kingdom','United Kingdom')
        df_who['Country'] = df_who['Country'].str.replace('Viet Nam','Vietnam')        
        df_who['Country'] = df_who['Country'].str.replace('.*conveyance.*','Diamond Princess')

        df_who.set_index('Country', inplace = True)
        df_who.to_csv('WHO/'+new_date+'.csv', index = True, encoding='utf-8')

        df_who.fillna(0, inplace = True)

        df_cases[new_date] = df_who['Cases']
        df_deaths[new_date] = df_who['Deaths']

        if df_cases[new_date].sum() != cases_tot:
            print('Total cases do not match up (Table = '+str(cases_tot)+', Sum = '+str(df_cases[new_date].sum()))
        if df_deaths[new_date].sum() != deaths_tot:
            print('Total deaths do not match up (Table = '+str(deaths_tot)+', Sum = '+str(df_deaths[new_date].sum()))
        
end_dt = end_dt.strftime("%Y-%m-%d")

##################################################
# Save data
##################################################

df_cases.to_csv('COVID-19_WHO_Cases.csv', index = True, encoding='utf-8')
df_deaths.to_csv('COVID-19_WHO_Deaths.csv', index = True, encoding='utf-8')
