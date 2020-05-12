from bokeh.io import curdoc, output_file, show
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, GeoJSONDataSource, LinearColorMapper, LogColorMapper, ColorBar
from bokeh.models import Div, HoverTool, RadioButtonGroup, Button, DateSlider, Span, Toggle
from bokeh.models import DatetimeTickFormatter, PrintfTickFormatter, BasicTicker, LogTicker, CustomJSHover
from bokeh.models import DataTable, TableColumn
from bokeh.palettes import brewer, Category20_16
from bokeh.layouts import row, column
from datetime import timedelta, date, datetime
import geopandas as gpd
import json
import pandas as pd

##################################################
# Get the JHU data from the web
##################################################

draw_sub_unit = ['Greenland', 'French Southern and Antarctic Lands', 'New Caledonia', 'Falkland Islands', 'Puerto Rico']

first_dt = datetime.strptime('2020-01-22',"%Y-%m-%d")

def get_jhu(location):
    df = pd.read_csv(location, encoding='utf-8', error_bad_lines=False)
    
    df['Province/State'] = df['Province/State'].str.replace('Bonaire, Sint Eustatius and Saba','Caribbean Netherlands')
    df['Province/State'] = df['Province/State'].str.replace('Curacao','Curaçao')
    df['Province/State'] = df['Province/State'].str.replace('St Martin','Saint Martin')
    df['Province/State'] = df['Province/State'].str.replace('\s*\(.*\)','')
    
    for i, index_this in enumerate(df.index[df['Province/State'].notnull()].tolist()):
        country = df.iloc[index_this,1]
        if country != 'Australia' and country != 'Canada' and country != 'China' and df.iloc[index_this,0] in draw_sub_unit:
            df.iloc[index_this,1] = df.iloc[index_this,0]
            
    df.drop(df.columns[[0,2,3]], axis=1, inplace=True)
    df.rename(columns = {df.columns[0]:'Country'}, inplace=True)
    
    df['Country'] = df['Country'].str.replace('Burma','Myanmar')
    df['Country'] = df['Country'].str.replace('Bahamas','The Bahamas')
    df['Country'] = df['Country'].str.replace('Congo \(Brazzaville\)','Republic of the Congo')
    df['Country'] = df['Country'].str.replace('Congo \(Kinshasa\)','Democratic Republic of the Congo')
    df['Country'] = df['Country'].str.replace('.*Ivoire','Ivory Coast')
    df['Country'] = df['Country'].str.replace('Eswatini', 'eSwatini')
    df['Country'] = df['Country'].str.replace('Holy See','Vatican')
    df['Country'] = df['Country'].str.replace('Korea, South', 'South Korea')
    df['Country'] = df['Country'].str.replace('Reunion','Réunion')
    df['Country'] = df['Country'].str.replace('Sao Tome and Principe','São Tomé and Príncipe')
    df['Country'] = df['Country'].str.replace('Serbia','Republic of Serbia')
    df['Country'] = df['Country'].str.replace('Taiwan\*','Taiwan')
    df['Country'] = df['Country'].str.replace('Tanzania','United Republic of Tanzania')
    df['Country'] = df['Country'].str.replace('Timor-Leste','East Timor')
    df['Country'] = df['Country'].str.replace('US','United States of America')
    df['Country'] = df['Country'].str.replace('West Bank and Gaza','Palestine')
    
    df = df.groupby('Country').sum()
    
    df.columns = pd.to_datetime(df.columns).tolist()

    return df

df_cases_tot = get_jhu('COVID-19_JHU_Cases.csv')
df_deaths_tot = get_jhu('COVID-19_JHU_Deaths.csv')

#df_cases_tot = get_jhu('https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv')
#df_deaths_tot = get_jhu('https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_global.csv')

last_dt = df_cases_tot.columns[-1]
prev_dt = (last_dt - timedelta(1))
show_dt = last_dt

# Make a copy within which the day to day changes are calculated
# Probably a better way to do this, but this works for now
df_cases_new = df_cases_tot.copy()
df_deaths_new = df_deaths_tot.copy()
new_dt = last_dt
while new_dt > first_dt:
    df_cases_new[new_dt] = (df_cases_new[new_dt] - df_cases_new[(new_dt - timedelta(1))])
    df_deaths_new[new_dt] = (df_deaths_new[new_dt] - df_deaths_new[(new_dt - timedelta(1))])
    new_dt = (new_dt - timedelta(1))
df_cases_new[first_dt] = 0
df_deaths_new[first_dt] = 0

##################################################
# Plot world map using geopandas
##################################################

geofile = 'ne_110m_admin_0_countries.shp'

df_geo = gpd.read_file(geofile)[['ADMIN', 'ADM0_A3', 'geometry']]
df_geo.columns = ['Country','Code','geometry']

# 2019 update of Macedonia to North Macedonia
df_geo['Country'] = df_geo['Country'].str.replace('Macedonia','North Macedonia')

# Specific for JHU, includes Puerto Rico as part of US
df_geo['Country'] = df_geo['Country'].str.replace('Puerto Rico','United States of America')

# Remove Antarctica
df_geo.drop([159], inplace = True)
#df_geo.drop([239], inplace = True)

df_countries = pd.read_csv('Countries.csv', encoding='utf-8')[['Country', 'Population']]
df_geo = df_geo.merge(df_countries, left_on = 'Country', right_on = 'Country', how = 'left')

# Fix multipolygon rendering (though now selecting a polygon does not select the other parts)
df_geo = df_geo.explode()
df_geo.reset_index(inplace = True)

# Merge cases and deaths with map
df_cases_map = df_geo.merge(df_cases_tot, left_on = 'Country', right_on = 'Country', how = 'left')
df_deaths_map = df_geo.merge(df_deaths_tot, left_on = 'Country', right_on = 'Country', how = 'left')

df_cases_map.fillna(0, inplace = True)
df_deaths_map.fillna(0, inplace = True)

# Build results map
df_map = df_geo.copy()
df_map['Cases_Tot_Abs'] = df_cases_map[show_dt]
df_map['Cases_New_Abs'] = df_cases_map[show_dt]-df_cases_map[prev_dt]
df_map['Cases_Tot_Rel'] = 1000*df_map['Cases_Tot_Abs']/df_map['Population']
df_map['Cases_New_Rel'] = 1000*df_map['Cases_New_Abs']/df_map['Population']
df_map['Deaths_Tot_Abs'] = df_deaths_map[show_dt]
df_map['Deaths_New_Abs'] = df_deaths_map[show_dt]-df_deaths_map[prev_dt]
df_map['Deaths_Tot_Rel'] = 1000*df_map['Deaths_Tot_Abs']/df_map['Population']
df_map['Deaths_New_Rel'] = 1000*df_map['Deaths_New_Abs']/df_map['Population']
df_map['Selected'] = df_map['Cases_Tot_Abs']

#Convert to json for plotting
df_map_json = json.loads(df_map.to_json())
json_map = json.dumps(df_map_json)
source_map = GeoJSONDataSource(geojson = json_map)

df_cases_tot = df_cases_tot.T
df_cases_tot.reset_index(inplace = True)
df_cases_tot.rename(columns = {df_cases_tot.columns[0]:'Date'}, inplace=True)
df_cases_tot['World'] = df_cases_tot.apply(lambda row: row[1 : -1].sum(),axis=1)
df_cases_tot['ToolTipDate'] = df_cases_tot.Date.map(lambda x: x.strftime("%b %d"))

df_cases_new = df_cases_new.T
df_cases_new.reset_index(inplace = True)
df_cases_new.rename(columns = {df_cases_new.columns[0]:'Date'}, inplace=True)
df_cases_new['World'] = df_cases_new.apply(lambda row: row[1 : -1].sum(),axis=1)
df_cases_new['ToolTipDate'] = df_cases_new.Date.map(lambda x: x.strftime("%b %d"))

df_deaths_tot = df_deaths_tot.T
df_deaths_tot.reset_index(inplace = True)
df_deaths_tot.rename(columns = {df_deaths_tot.columns[0]:'Date'}, inplace=True)
df_deaths_tot['World'] = df_deaths_tot.apply(lambda row: row[1 : -1].sum(),axis=1)
df_deaths_tot['ToolTipDate'] = df_deaths_tot.Date.map(lambda x: x.strftime("%b %d"))

df_deaths_new = df_deaths_new.T
df_deaths_new.reset_index(inplace = True)
df_deaths_new.rename(columns = {df_deaths_new.columns[0]:'Date'}, inplace=True)
df_deaths_new['World'] = df_deaths_new.apply(lambda row: row[1 : -1].sum(),axis=1)
df_deaths_new['ToolTipDate'] = df_deaths_new.Date.map(lambda x: x.strftime("%b %d"))

df_grp = df_cases_tot[['Date', 'ToolTipDate']].copy()
df_grp['Country'] = 'World'
df_grp['Population'] = 7776350000
df_grp['Cases_Tot_Abs'] = df_cases_tot['World']
df_grp['Cases_New_Abs'] = df_cases_new['World']
df_grp['Cases_Tot_Rel'] = df_cases_tot['World']/7776350
df_grp['Cases_New_Rel'] = df_cases_new['World']/7776350
df_grp['Deaths_Tot_Abs'] = df_deaths_tot['World']
df_grp['Deaths_New_Abs'] = df_deaths_new['World']
df_grp['Deaths_Tot_Rel'] = df_deaths_tot['World']/7776350
df_grp['Deaths_New_Rel'] = df_deaths_new['World']/7776350
df_grp['Selected'] = df_grp['Cases_Tot_Abs']
df_grp['Color'] = Category20_16[0]
df_grp = df_grp.sort_values(['Country', 'Date'])
source_grp = ColumnDataSource(df_grp)

sum_population = df_grp[df_grp['Date'] == show_dt]['Population'].sum()
sum_cases_tot_abs = df_grp[df_grp['Date'] == show_dt]['Cases_Tot_Abs'].sum()
sum_cases_new_abs = df_grp[df_grp['Date'] == show_dt]['Cases_New_Abs'].sum()
sum_cases_tot_rel = 1000*sum_cases_tot_abs/sum_population
sum_cases_new_rel = 1000*sum_cases_new_abs/sum_population
sum_deaths_tot_abs = df_grp[df_grp['Date'] == show_dt]['Deaths_Tot_Abs'].sum()
sum_deaths_new_abs = df_grp[df_grp['Date'] == show_dt]['Deaths_New_Abs'].sum()
sum_deaths_tot_rel = 1000*sum_deaths_tot_abs/sum_population
sum_deaths_new_rel = 1000*sum_deaths_new_abs/sum_population

#Define a sequential multi-hue color palette.
palette = brewer['YlGnBu'][9]

#Reverse color order so that dark blue is highest obesity.
palette = palette[::-1]

custom=CustomJSHover(code="""
                     if (value==0) {
                         return ""
                     }
                     var modified;
                     var SI_SYMBOL = ["", "k", "M", "B", "T"];
                     modified = 1000/value;
                     
                     // what tier? (determines SI symbol)
                     var tier = Math.log10(modified) / 3 | 0;
                     
                     // if zero, we don't need a suffix
                     if(tier == 0) return "(1/" + modified.toFixed(0) + " Ppl)";
                     
                     // get suffix and determine scale
                     var suffix = SI_SYMBOL[tier];
                     var scale = Math.pow(10, tier * 3);
                     
                     // scale the number
                     var scaled = modified / scale;
                     
                     // format number and add suffix
                     return "(1/" + scaled.toFixed(1) + suffix + " Ppl)";
                     """)

hover = HoverTool(tooltips= [('Date','@ToolTipDate'),
                             ('Country/region','@Country'), ('Population','@Population'),
                             ('Cases','@Cases_Tot_Abs @Cases_Tot_Rel{custom}')],
                  formatters={'@Cases_Tot_Rel' : custom}, mode = 'vline')

def my_format(num):
    if num == 0:
        return '0'
    num = float('{:.3g}'.format(1000/num))
    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        num /= 1000.0
    return '1/{}{} Ppl'.format('{:f}'.format(num).rstrip('0').rstrip('.'), ['', 'k', 'M', 'B', 'T'][magnitude])

# Make the map
def make_map():
    #Create figure object.
    p = figure(title = 'Map of COVID-19 '+plot_title[sel_var]+' (WHO)', plot_height = 550 , plot_width = 950, 
                     x_range=(-180, 180), y_range=(-65, 90), toolbar_location = 'above',
                     tools = 'pan, wheel_zoom, box_zoom, reset, tap', sizing_mode="scale_width")
    p.xgrid.grid_line_color = None
    p.ygrid.grid_line_color = None
    
    # Choose linear or logarithmic color mapper
    if lin_map.active:
        mapper = LinearColorMapper(palette = palette, low = 0, high = plot_max[sel_var])
        color_bar = ColorBar(color_mapper = mapper, label_standoff = 8, height = 20, #width = 500, 
                             border_line_color = None, location = (0,0), orientation = 'horizontal', 
                             ticker = BasicTicker(), major_label_overrides = tick_lin[sel_var])
    else:
        mapper = LogColorMapper(palette = palette, low = plot_min[sel_var], high = plot_max[sel_var])
        color_bar = ColorBar(color_mapper = mapper, label_standoff = 8, height = 20, #width = 500, 
                             border_line_color = None, location = (0,0), orientation = 'horizontal', 
                             ticker = LogTicker(), major_label_overrides = tick_log[sel_var])
    
    #Add patch renderer to figure. 
    ren_map = p.patches('xs', 'ys', source = source_map, line_color = 'black', line_width = 0.25,
                        fill_color = {'field' : 'Selected', 'transform' : mapper}, fill_alpha = 1)

    #Specify figure layout.
    p.add_layout(color_bar, 'below')
    
    #Add hover tool
    p.add_tools(HoverTool(tooltips = [('Country/region','@Country'), ('Population','@Population'), 
                                      ('Tot Cases','@Cases_Tot_Abs @Cases_Tot_Rel{custom}'),
                                      ('New Cases','@Cases_New_Abs @Cases_New_Rel{custom}'),
                                      ('Tot Deaths','@Deaths_Tot_Abs @Deaths_Tot_Rel{custom}'),
                                      ('New Deaths','@Deaths_New_Abs @Deaths_New_Rel{custom}')],
                          formatters={'@Cases_Tot_Rel' : custom, '@Cases_New_Rel' : custom,
                                      '@Deaths_Tot_Rel' : custom, '@Deaths_New_Rel' : custom}))
    return p

# Make linear plot
def make_lin():
    #Create figure object.
    p = figure(title = 'Lin. Plot of COVID-19 '+plot_title[sel_var]+' (WHO)', toolbar_location = 'above',
               plot_height = 250, plot_width = 500, x_axis_type = 'datetime', 
               tools = 'pan, wheel_zoom, box_zoom, reset', sizing_mode="scale_width")

    # Format your x-axis as datetime.
    p.xaxis[0].formatter = DatetimeTickFormatter(days='%b %d')
    p.yaxis[0].formatter = PrintfTickFormatter(format='%.1e')

    p.circle(x = 'Date', y = 'Selected', source=source_grp, fill_color = 'Color', line_color = 'Color', 
             legend_field = 'Country')

    p.legend.location = "top_left"
    p.legend.click_policy="mute"

    p.add_layout(dt_span)

    # Add your tooltips
    p.add_tools(hover)
    return p

# Make logarithmic plot
def make_log():
    #Create figure object.
    p = figure(title = 'Log. Plot of COVID-19 '+plot_title[sel_var]+' (WHO)',toolbar_location = 'above',
               plot_height = 250, plot_width = 500, x_axis_type = 'datetime', y_axis_type = 'log', 
               tools = 'pan, wheel_zoom, box_zoom, reset', sizing_mode="scale_width")

    # Format your x-axis as datetime.
    p.xaxis[0].formatter = DatetimeTickFormatter(days='%b %d')

    p.circle(x = 'Date', y = 'Selected', source=source_grp, fill_color = 'Color', line_color = 'Color', 
             legend_field = 'Country')

    p.legend.location = "top_left"
    p.legend.click_policy="mute"

    p.add_layout(dt_span)
    
    # Add your tooltips
    p.add_tools(hover)
    return p
    
# Define the callback function: update_map
def update_map(attr, old, new):
    global show_dt
    show_dt = pd.to_datetime(slider.value_as_date)
    if slider.value_as_datetime > first_dt:
        prev_dt = (pd.to_datetime(slider.value_as_date) - timedelta(1))
    else:
        prev_dt = show_dt
    dt_span.update(location=slider.value_as_date)

    sum_population = df_grp[df_grp['Date'] == show_dt]['Population'].sum()
    sum_cases_tot_abs = df_grp[df_grp['Date'] == show_dt]['Cases_Tot_Abs'].sum()
    sum_cases_new_abs = df_grp[df_grp['Date'] == show_dt]['Cases_New_Abs'].sum()
    sum_cases_tot_rel = 1000*sum_cases_tot_abs/sum_population
    sum_cases_new_rel = 1000*sum_cases_new_abs/sum_population
    sum_deaths_tot_abs = df_grp[df_grp['Date'] == show_dt]['Deaths_Tot_Abs'].sum()
    sum_deaths_new_abs = df_grp[df_grp['Date'] == show_dt]['Deaths_New_Abs'].sum()
    sum_deaths_tot_rel = 1000*sum_deaths_tot_abs/sum_population
    sum_deaths_new_rel = 1000*sum_deaths_new_abs/sum_population
    
    source_out.data = dict(stat=['Tot Cases', 'New Cases', 'Tot Deaths', 'New Deaths'],
                           vabs=[sum_cases_tot_abs, sum_cases_new_abs, sum_deaths_tot_abs, sum_deaths_new_abs],
                           vrel=[my_format(sum_cases_tot_rel), my_format(sum_cases_new_rel),
                                 my_format(sum_deaths_tot_rel), my_format(sum_deaths_new_rel)])
    
    df_map['Cases_Tot_Abs'] = df_cases_map[show_dt]
    df_map['Cases_New_Abs'] = df_cases_map[show_dt]-df_cases_map[prev_dt]
    df_map['Cases_Tot_Rel'] = 1000*df_map['Cases_Tot_Abs']/df_map['Population']
    df_map['Cases_New_Rel'] = 1000*df_map['Cases_New_Abs']/df_map['Population']
    df_map['Deaths_Tot_Abs'] = df_deaths_map[show_dt]
    df_map['Deaths_New_Abs'] = df_deaths_map[show_dt]-df_deaths_map[prev_dt]
    df_map['Deaths_Tot_Rel'] = 1000*df_map['Deaths_Tot_Abs']/df_map['Population']
    df_map['Deaths_New_Rel'] = 1000*df_map['Deaths_New_Abs']/df_map['Population']
    df_map['Selected'] = df_map[plot_var[sel_var]]

    df_map_json = json.loads(df_map.to_json())
    json_map = json.dumps(df_map_json)
    source_map.geojson = json_map

# Define the callback function: update_plot
def update_plot(attr, old, new):
    global df_grp
    try:
        selected_index = source_map.selected.indices[0]
        old_list = source_map.selected.indices
        old_list.sort()
        new_list = []
        for i,  selected_index in enumerate(source_map.selected.indices):
            new_list = new_list + list(df_cases_map['Country'][df_cases_map['Country'] == df_cases_map.iloc[selected_index]['Country']].index)

        new_list = list(set(new_list))
        new_list.sort()
        if new_list != old_list:
            source_map.selected.update(indices = new_list)
            return
        
        df_grp = pd.DataFrame(columns=['Date', 'ToolTipDate', 'Country', 'Population', 'Selected', 'Color',
                                       'Cases_Tot_Abs', 'Cases_New_Abs', 'Cases_Tot_Rel', 'Cases_New_Rel',
                                       'Deaths_Tot_Abs', 'Deaths_New_Abs', 'Deaths_Tot_Rel', 'Deaths_New_Rel'])

        color_index = 0
        prev_country = 'World'
        for i, selected_index in enumerate(source_map.selected.indices):
            selected_country = df_cases_map.iloc[selected_index]['Country']
            if selected_country != prev_country:
                prev_country = selected_country
                pop_country = df_cases_map.iloc[selected_index]['Population']
                df_sel = df_cases_tot[['Date', 'ToolTipDate']].copy()
                df_sel['Country'] = selected_country
                df_sel['Population'] = pop_country
                df_sel['Cases_Tot_Abs'] = df_cases_tot[selected_country]
                df_sel['Cases_New_Abs'] = df_cases_new[selected_country]
                df_sel['Cases_Tot_Rel'] = 1000*df_cases_tot[selected_country]/pop_country
                df_sel['Cases_New_Rel'] = 1000*df_cases_new[selected_country]/pop_country
                df_sel['Deaths_Tot_Abs'] = df_deaths_tot[selected_country]
                df_sel['Deaths_New_Abs'] = df_deaths_new[selected_country]
                df_sel['Deaths_Tot_Rel'] = 1000*df_deaths_tot[selected_country]/pop_country
                df_sel['Deaths_New_Rel'] = 1000*df_deaths_new[selected_country]/pop_country
                df_sel['Selected'] = df_sel[plot_var[sel_var]]
                df_sel['Color'] = Category20_16[color_index]
                color_index = color_index + 1
                df_grp = df_grp.append(df_sel, ignore_index=True)
                        
        df_grp = df_grp.sort_values(['Country', 'Date'])
        source_grp.data = df_grp

    except IndexError:
        df_grp = df_cases_tot[['Date', 'ToolTipDate']].copy()
        df_grp['Country'] = 'World'
        df_grp['Population'] = 7776350000
        df_grp['Cases_Tot_Abs'] = df_cases_tot['World']
        df_grp['Cases_New_Abs'] = df_cases_new['World']
        df_grp['Cases_Tot_Rel'] = df_cases_tot['World']/7776350
        df_grp['Cases_New_Rel'] = df_cases_new['World']/7776350
        df_grp['Deaths_Tot_Abs'] = df_deaths_tot['World']
        df_grp['Deaths_New_Abs'] = df_deaths_new['World']
        df_grp['Deaths_Tot_Rel'] = df_deaths_tot['World']/7776350
        df_grp['Deaths_New_Rel'] = df_deaths_new['World']/7776350
        df_grp['Selected'] = df_grp[plot_var[sel_var]]
        df_grp['Color'] = Category20_16[0]
        df_grp = df_grp.sort_values(['Country', 'Date'])
        source_grp.data = df_grp

    sum_population = df_grp[df_grp['Date'] == show_dt]['Population'].sum()
    sum_cases_tot_abs = df_grp[df_grp['Date'] == show_dt]['Cases_Tot_Abs'].sum()
    sum_cases_new_abs = df_grp[df_grp['Date'] == show_dt]['Cases_New_Abs'].sum()
    sum_cases_tot_rel = 1000*sum_cases_tot_abs/sum_population
    sum_cases_new_rel = 1000*sum_cases_new_abs/sum_population
    sum_deaths_tot_abs = df_grp[df_grp['Date'] == show_dt]['Deaths_Tot_Abs'].sum()
    sum_deaths_new_abs = df_grp[df_grp['Date'] == show_dt]['Deaths_New_Abs'].sum()
    sum_deaths_tot_rel = 1000*sum_deaths_tot_abs/sum_population
    sum_deaths_new_rel = 1000*sum_deaths_tot_abs/sum_population
    
    source_out.data = dict(stat=['Tot Cases', 'New Cases', 'Tot Deaths', 'New Deaths'],
                           vabs=[sum_cases_tot_abs, sum_cases_new_abs, sum_deaths_tot_abs, sum_deaths_new_abs],
                           vrel=[my_format(sum_cases_tot_rel), my_format(sum_cases_new_rel),
                                 my_format(sum_deaths_tot_rel), my_format(sum_deaths_new_rel)])
    
def change_var(attr, old, new):
    curdoc().clear()
    
    global sel_var
    sel_var = int(str(rb_cases_deaths.active)+str(rb_abs_rel.active)+str(rb_tot_new.active), 2)
    
    df_map['Selected'] = df_map[plot_var[sel_var]]
    df_map_json = json.loads(df_map.to_json())
    json_map = json.dumps(df_map_json)
    source_map.geojson = json_map
    
    df_grp['Selected'] = df_grp[plot_var[sel_var]]
    source_grp.data = df_grp

    if rb_cases_deaths.active and rb_tot_new.active:
        hover.tooltips = [('Date','@ToolTipDate'), ('Country/region','@Country'), ('Population','@Population'),
                          ('New Deaths','@Deaths_New_Abs @Deaths_New_Rel{custom}')]
        hover.formatters = {'@Deaths_New_Rel' : custom}

    elif rb_cases_deaths.active:
        hover.tooltips = [('Date','@ToolTipDate'), ('Country/region','@Country'), ('Population','@Population'),
                          ('Tot Deaths','@Deaths_Tot_Abs @Deaths_Tot_Rel{custom}')]
        hover.formatters = {'@Deaths_Tot_Rel' : custom}
    elif rb_tot_new.active:
        hover.tooltips = [('Date','@ToolTipDate'), ('Country/region','@Country'), ('Population','@Population'),
                          ('New Cases','@Cases_New_Abs @Cases_New_Rel{custom}')]
        hover.formatters = {'@Cases_New_Rel' : custom}
    else:
        hover.tooltips = [('Date','@ToolTipDate'), ('Country/region','@Country'), ('Population','@Population'),
                          ('Tot Cases','@Cases_Tot_Abs @Cases_Tot_Rel{custom}')]
        hover.formatters = {'@Cases_Tot_Rel' : custom}

    curdoc().add_root(row(column(make_map(), row(column(heading, row(button, lin_map, sizing_mode="stretch_width"), sizing_mode="stretch_width"), column(rb_cases_deaths, rb_tot_new, rb_abs_rel, sizing_mode="stretch_width")), slider, table_out, sizing_mode="scale_width"), column(make_lin(), make_log(), sizing_mode="scale_width"), sizing_mode="stretch_both"))

def animate_update():
    global show_dt
    slider.value = slider.value_as_date + timedelta(1)
    show_dt = pd.to_datetime(slider.value_as_date)
    if last_dt == pd.to_datetime(slider.value_as_date):
        animate()

callback_id = None

def animate():
    global callback_id
    if button.label == '► Play':
        slider.on_change('value', update_map)
        if last_dt.date() == slider.value_as_date:
            slider.value = first_dt
        button.label = '❚❚ Pause'
        callback_id = curdoc().add_periodic_callback(animate_update, 1)
    else:
        slider.remove_on_change('value', update_map)
        button.label = '► Play'
        curdoc().remove_periodic_callback(callback_id)

# Make a selection of what to plot
plot_title = ['Tot Cases', 'New Cases', 'Tot Cases/1k Ppl', 'New Cases/1k Ppl',
              'Tot Deaths', 'New Deaths', 'Tot Deaths/1k Ppl', 'New Deaths/1k Ppl']
plot_var = ['Cases_Tot_Abs', 'Cases_New_Abs', 'Cases_Tot_Rel', 'Cases_New_Rel',
            'Deaths_Tot_Abs', 'Deaths_New_Abs', 'Deaths_Tot_Rel', 'Deaths_New_Rel']
plot_min = [1, 1, 0.0005, 0.0005, 1, 1, 0.0005, 0.00001]
plot_max = [max(df_map[plot_var[0]]), max(df_map[plot_var[1]]), max(df_map[plot_var[2]]),
            max(df_map[plot_var[3]]), max(df_map[plot_var[4]]), max(df_map[plot_var[5]]),
            max(df_map[plot_var[6]]), max(df_map[plot_var[7]])]
tick_lin = [{'0':'0', '50000':'50k', '100000':'100k', '150000':'150k', '200000':'200k', '250000':'250k',
             '300000':'300k', '350000':'350k', '400000':'400k', '500000':'500k'},
            {'0':'0', '50000':'50k', '100000':'100k', '150000':'150k', '200000':'200k', '250000':'250k',
             '300000':'300k', '350000':'350k', '400000':'400k', '500000':'500k'},
            {'0.5':'1/2000', '1':'1/1000', '1.5':'1/666', '2':'1/500', '2.5':'1/400', '3':'1/333',
             '3.5':'1/286', '4':'1/250', '4.5':'1/222', '5':'1/200'},
            {'0.5':'1/2000', '1':'1/1000', '1.5':'1/666', '2':'1/500', '2.5':'1/400', '3':'1/333',
             '3.5':'1/286', '4':'1/250', '4.5':'1/222', '5':'1/200'},
            {'0':'0', '50000':'50k', '100000':'100k', '150000':'150k', '200000':'200k', '250000':'250k',
             '300000':'300k', '350000':'350k', '400000':'400k', '500000':'500k'},
            {'0':'0', '50000':'50k', '100000':'100k', '150000':'150k', '200000':'200k', '250000':'250k',
             '300000':'300k', '350000':'350k', '400000':'400k', '500000':'500k'},
            {'0.5':'1/2000', '1':'1/1000', '1.5':'1/666', '2':'1/500', '2.5':'1/400', '3':'1/333',
             '3.5':'1/286', '4':'1/250', '4.5':'1/222', '5':'1/200'},
            {'0.5':'1/2000', '1':'1/1000', '1.5':'1/666', '2':'1/500', '2.5':'1/400', '3':'1/333',
             '3.5':'1/286', '4':'1/250', '4.5':'1/222', '5':'1/200'}]
tick_log = [{'1':'1', '10':'10', '100':'100', '1000':'1k', '10000':'10k', '100000':'100k', '1000000':'1M'},
            {'1':'1', '10':'10', '100':'100', '1000':'1k', '10000':'10k', '100000':'100k', '1000000':'1M'},
            {'0.00001':'1/100M', '0.0001':'1/10M', '0.001':'1/1M', '0.01':'1/100k', '0.1':'1/10k',
             '1':'1/1k', '10':'1/100', '100':'1/10'},
            {'0.00001':'1/100M', '0.0001':'1/10M', '0.001':'1/1M', '0.01':'1/100k', '0.1':'1/10k',
             '1':'1/1k', '10':'1/100', '100':'1/10'},
            {'1':'1', '10':'10', '100':'100', '1000':'1k', '10000':'10k', '100000':'100k', '1000000':'1M'},
            {'1':'1', '10':'10', '100':'100', '1000':'1k', '10000':'10k', '100000':'100k', '1000000':'1M'},
            {'0.00001':'1/100M', '0.0001':'1/10M', '0.001':'1/1M', '0.01':'1/100k', '0.1':'1/10k',
             '1':'1/1k', '10':'1/100', '100':'1/10'},
            {'0.00001':'1/100M', '0.0001':'1/10M', '0.001':'1/1M', '0.01':'1/100k', '0.1':'1/10k',
             '1':'1/1k', '10':'1/100', '100':'1/10'}]
             
# heading fills available width
heading = Div(text='Worldwide COVID-19 Statistics - <a href="https://www.who.int/emergencies/diseases/novel-coronavirus-2019/situation-reports" target="_blank">WHO</a></br>Click on countries (multiple with shift)</br>Created by Phil Martel - <a href="https://github.com/ppmartel/COVID-19" target="_blank">GitHub Repository</a>',
              style={'background-color':'#c8cfd6', 'outline':'black solid thin', 'text-align':'center'},
              height=70, align="center", sizing_mode="stretch_width")

# Make a toggle to cycle through the dates
button = Button(label='► Play', height = 30)
button.on_click(animate)

# Make a toggle for changing the map to linear
lin_map = Toggle(label = 'Linear Map', active = False, height = 30)
lin_map.on_change('active', change_var)

rb_cases_deaths = RadioButtonGroup(labels=['Cases', 'Deaths'], active=0, height = 30)
rb_cases_deaths.on_change('active', change_var)

rb_abs_rel = RadioButtonGroup(labels=['Per Region', 'Per 1k Ppl'], active=0, height = 30)
rb_abs_rel.on_change('active', change_var)

rb_tot_new = RadioButtonGroup(labels=['Total', 'New'], active=0, height = 30)
rb_tot_new.on_change('active', change_var)

sel_var = int(str(rb_cases_deaths.active)+str(rb_abs_rel.active)+str(rb_tot_new.active), 2)

# Make a selection of the date to plot
slider = DateSlider(title = 'Date', start = first_dt, end = last_dt, step = 1, value = last_dt,
                    height = 20, margin = (20, 50, 20, 50), sizing_mode="stretch_width")
slider.on_change('value_throttled', update_map)

# Make a span to show current date in plots
dt_span = Span(location=slider.value_as_date, dimension='height', line_color='red', line_dash='solid',
               line_width=2)

# Update timeseries plots based on selection
source_map.selected.on_change('indices', update_plot)

# Make a set of labels to show some totals on the map
data_out = dict(stat=['Tot Cases', 'New Cases', 'Tot Deaths', 'New Deaths'],
                vabs=[sum_cases_tot_abs, sum_cases_new_abs, sum_deaths_tot_abs, sum_deaths_new_abs],
                vrel=[my_format(sum_cases_tot_rel), my_format(sum_cases_new_rel),
                      my_format(sum_deaths_tot_rel), my_format(sum_deaths_new_rel)])
source_out = ColumnDataSource(data_out)
columns_out = [TableColumn(field='stat', title="Statistic"),
               TableColumn(field='vabs', title="Per Region"),
               TableColumn(field='vrel', title="Per Capita")]
table_out = DataTable(source=source_out, columns=columns_out, height=125, width=100, sizing_mode="stretch_width")

# Make a column layout of widgets and plots
curdoc().add_root(row(column(make_map(), row(column(heading, row(button, lin_map, sizing_mode="stretch_width"), sizing_mode="stretch_width"), column(rb_cases_deaths, rb_tot_new, rb_abs_rel, sizing_mode="stretch_width")), slider, table_out, sizing_mode="scale_width"), column(make_lin(), make_log(), sizing_mode="scale_width"), sizing_mode="stretch_both"))