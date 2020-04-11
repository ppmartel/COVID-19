from bokeh.io import curdoc, output_notebook, show, output_file
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, GeoJSONDataSource, LinearColorMapper, LogColorMapper, ColorBar
from bokeh.models import Label, LabelSet, HoverTool, TapTool, RadioButtonGroup, Button, DateSlider, Span
from bokeh.models import DatetimeTickFormatter, PrintfTickFormatter, LogTicker, Toggle
from bokeh.palettes import brewer, Category20_16
from bokeh.layouts import row, column
from datetime import timedelta, date, datetime
import geopandas as gpd
import json
import os
import pandas as pd
import sys
import time

##################################################
# Check that the data exists
##################################################

first_dt = datetime.strptime('2020-01-21',"%Y-%m-%d")
first_rep = 1

if os.path.exists('COVID-19_WHO_Cases.csv'):
    print("Database exists - Reading it")

    df_cases = pd.read_csv('COVID-19_WHO_Cases.csv', encoding='utf-8', index_col='Country')
    df_deaths = pd.read_csv('COVID-19_WHO_Deaths.csv', encoding='utf-8', index_col='Country')

    last_dt = datetime.strptime(df_cases.columns.values[-1],'%Y-%m-%d')
    last_rep = first_rep + int ((last_dt - first_dt).days)
else:
    print("Database does not exist")
    sys.exit()

show_dt = last_dt.strftime("%Y-%m-%d")
show_rep = last_rep

df_cases.fillna(0, inplace = True)
df_deaths.fillna(0, inplace = True)

##################################################
# Plot world map using geopandas
##################################################

#output_notebook()

geofile = '/home/martel/.local/share/cartopy/shapefiles/natural_earth/cultural/ne_110m_admin_0_countries.shp'

df_geo = gpd.read_file(geofile)[['ADMIN', 'ADM0_A3', 'geometry']]
df_geo.columns = ['Country','Code','geometry']

# 2019 update of Macedonia to North Macedonia
df_geo['Country'] = df_geo['Country'].str.replace('Macedonia','North Macedonia')

# Remove Antarctica
df_geo.drop([159], inplace = True)
#df_geo.drop([239], inplace = True)

# Fix multipolygon rendering (though now selecting a polygon does not select the other parts)
df_geo = df_geo.explode()
df_geo.reset_index(inplace = True)

# Merge cases and deaths with map
df_cases_map = df_geo.merge(df_cases, left_on = 'Country', right_on = 'Country', how = 'left')
df_deaths_map = df_geo.merge(df_deaths, left_on = 'Country', right_on = 'Country', how = 'left')

# Build results map
df_map = df_geo.copy()
df_map['Population'] = df_cases_map['Population']
df_map['Cases_Tot'] = df_cases_map[show_dt]
df_map['Cases_Per'] = 1000*df_cases_map[show_dt]/df_cases_map['Population']
df_map['Deaths_Tot'] = df_deaths_map[show_dt]
df_map['Deaths_Per'] = 1000*df_deaths_map[show_dt]/df_deaths_map['Population']

#Read data to json.
df_map_json = json.loads(df_map.to_json())

#Convert to String like object.
json_map = json.dumps(df_map_json)

#Input GeoJSON source that contains features for plotting.
source_map = GeoJSONDataSource(geojson = json_map)

df_cases_tran = df_cases.drop(['Continental Region','Statistical Region','Population'], axis=1).T
df_cases_tran.reset_index(inplace = True)
df_cases_tran.rename(columns = {df_cases_tran.columns[0]:'Date'}, inplace=True)
df_cases_tran['Date'] = pd.to_datetime(df_cases_tran['Date'])
df_cases_tran['World'] = df_cases_tran.apply(lambda row: row[1 : -1].sum(),axis=1)
df_cases_tran['ToolTipDate'] = df_cases_tran.Date.map(lambda x: x.strftime("%b %d"))

df_deaths_tran = df_deaths.drop(['Continental Region','Statistical Region','Population'], axis=1).T
df_deaths_tran.reset_index(inplace = True)
df_deaths_tran.rename(columns = {df_deaths_tran.columns[0]:'Date'}, inplace=True)
df_deaths_tran['Date'] = pd.to_datetime(df_deaths_tran['Date'])
df_deaths_tran['World'] = df_deaths_tran.apply(lambda row: row[1 : -1].sum(),axis=1)
df_deaths_tran['ToolTipDate'] = df_deaths_tran.Date.map(lambda x: x.strftime("%b %d"))

df_grp = df_cases_tran[['Date', 'ToolTipDate']].copy()
df_grp['Country'] = 'World'
df_grp['Cases_Tot'] = df_cases_tran['World']
df_grp['Cases_Per'] = df_cases_tran['World']/7776350
df_grp['Deaths_Tot'] = df_deaths_tran['World']
df_grp['Deaths_Per'] = df_deaths_tran['World']/7776350
df_grp['Color'] = Category20_16[0]
df_grp = df_grp.sort_values(['Country', 'Date'])
source_grp = ColumnDataSource(df_grp)

sum_cases_tot = df_grp[df_grp['Date'] == show_dt]['Cases_Tot'].sum()
sum_cases_per = df_grp[df_grp['Date'] == show_dt]['Cases_Per'].sum()
sum_deaths_tot = df_grp[df_grp['Date'] == show_dt]['Deaths_Tot'].sum()
sum_deaths_per = df_grp[df_grp['Date'] == show_dt]['Deaths_Per'].sum()

#Define a sequential multi-hue color palette.
palette = brewer['YlGnBu'][8]

#Reverse color order so that dark blue is highest obesity.
palette = palette[::-1]

def make_map(setting, linear):
    #Instantiate LinearColorMapper that linearly maps numbers in a range, into a sequence of colors.
    if setting == 0:
        if linear:
            tick_labels = {'0':'0', '50000':'50k', '100000':'100k', '150000':'150k', '200000':'200k', 
                           '250000':'250k', '300000':'300k', '350000':'350k', '400000':'400k', '500000':'500k'}
        else:
            tick_labels = {'1':'1', '10':'10', '100':'100', '1000':'1k', '10000':'10k',
                           '100000':'100k', '1000000':'1M'}
    elif setting == 1:
        if linear:
            tick_labels = {'0.5':'1/2000', '1':'1/1000', '1.5':'1/666', '2':'1/500', '2.5':'1/400', '3':'1/333', 
                           '3.5':'1/286', '4':'1/250', '4.5':'1/222', '5':'1/200'}
        else:
            tick_labels = {'0.001':'1/1M', '0.01':'1/100k', '0.1':'1/10k', '1':'1/1k', '10':'1/100', '100':'1/10'}
    elif setting == 2:
        if linear:
            tick_labels = {'0':'0', '50000':'50k', '100000':'100k', '150000':'150k', '200000':'200k', 
                           '250000':'250k', '300000':'300k', '350000':'350k', '400000':'400k', '500000':'500k'}
        else:
            tick_labels = {'1':'1', '10':'10', '100':'100', '1000':'1k', '10000':'10k',
                           '100000':'100k', '1000000':'1M'}
    else:
        if linear:
            tick_labels = {'0.5':'1/2000', '1':'1/1000', '1.5':'1/666', '2':'1/500', '2.5':'1/400', '3':'1/333', 
                           '3.5':'1/286', '4':'1/250', '4.5':'1/222', '5':'1/200'}
        else:
            tick_labels = {'0.001':'1/1M', '0.01':'1/100k', '0.1':'1/10k', '1':'1/1k', '10':'1/100', '100':'1/10'}

    min_val = plot_min[setting]
    max_val = plot_max[setting]

    if linear:
        color_mapper = LinearColorMapper(palette = palette, low = 0, high = max_val)
        color_bar = ColorBar(color_mapper = color_mapper, label_standoff = 8, width = 500, height = 20, 
                             border_line_color = None, location = (0,0), orientation = 'horizontal', 
                             major_label_overrides = tick_labels)
    else:
        color_mapper = LogColorMapper(palette = palette, low = min_val, high = max_val)
        color_bar = ColorBar(color_mapper = color_mapper, label_standoff = 8, width = 500, height = 20, 
                             border_line_color = None, location = (0,0), orientation = 'horizontal', 
                             ticker = LogTicker(), major_label_overrides = tick_labels)

    #Add hover tool
    hover = HoverTool(tooltips = [('Country/region','@Country'), ('Population','@Population'), 
                                  ('Cases','@Cases_Tot (@Cases_Per/1k Ppl)'),
                                  ('Deaths','@Deaths_Tot (@Deaths_Per/1k Ppl)')])
    
    #Create figure object.
    p = figure(title = 'Map of COVID-19 '+plot_title[setting]+' (WHO)', plot_height = 550 , plot_width = 950, 
               x_range=(-180, 180), y_range=(-65, 90), toolbar_location = 'right',
               tools = 'pan, wheel_zoom, box_zoom, reset, tap')
    p.xgrid.grid_line_color = None
    p.ygrid.grid_line_color = None

    p.add_layout(labels)

    #Add patch renderer to figure. 
    p.patches('xs', 'ys', source = source_map, fill_color = {'field' : plot_var[setting], 'transform' : color_mapper},
              line_color = 'black', line_width = 0.25, fill_alpha = 1)

    #Specify figure layout.
    p.add_layout(color_bar, 'below')
    p.add_tools(hover)
    
    return p

# Define the callback function: update_map
def update_map(attr, old, new):
    global show_dt
    show_dt = slider.value_as_date.strftime("%Y-%m-%d")
    dt_span.update(location=slider.value_as_date)

    sum_cases_tot = df_grp[df_grp['Date'] == show_dt]['Cases_Tot'].sum()
    sum_cases_per = df_grp[df_grp['Date'] == show_dt]['Cases_Per'].sum()
    sum_deaths_tot = df_grp[df_grp['Date'] == show_dt]['Deaths_Tot'].sum()
    sum_deaths_per = df_grp[df_grp['Date'] == show_dt]['Deaths_Per'].sum()
    source_lab.data = dict(x=[20,20,20,20,20], y=[100,80,60,40,20],
                           text=[slider.value_as_date.strftime("%d %b %Y"),
                                 'Cases: {0}'.format(sum_cases_tot),
                                 'Cases/1k Ppl: {0:.1e}'.format(sum_cases_per),
                                 'Deaths: {0}'.format(sum_deaths_tot),
                                 'Deaths/1k Ppl: {0:.1e}'.format(sum_deaths_per)])
    
    df_map['Population'] = df_cases_map['Population']
    df_map['Cases_Tot'] = df_cases_map[show_dt]
    df_map['Cases_Per'] = 1000*df_cases_map[show_dt]/df_cases_map['Population']
    df_map['Deaths_Tot'] = df_deaths_map[show_dt]
    df_map['Deaths_Per'] = 1000*df_deaths_map[show_dt]/df_deaths_map['Population']
    
    df_map_json = json.loads(df_map.to_json())
    json_map = json.dumps(df_map_json)
    source_map.geojson = json_map

def make_lin(setting):
    #Create figure object.
    p = figure(title = 'Linear Plot of COVID-19 '+plot_title[setting]+' (WHO)', toolbar_location = 'right',
               plot_height = 375, plot_width = 475, x_axis_type = 'datetime', 
               tools = 'pan, wheel_zoom, box_zoom, reset')
    
    # Format your x-axis as datetime.
    p.xaxis[0].formatter = DatetimeTickFormatter(days='%b %d')
    p.yaxis[0].formatter = PrintfTickFormatter(format='%.1e')

    p.circle(x = 'Date', y = plot_var[setting], source=source_grp, fill_color = 'Color', line_color = 'Color', 
             legend_field = 'Country')
    
    p.legend.location = "top_left"
    p.legend.click_policy="mute"

    p.add_layout(dt_span)

    # Add your tooltips
    p.add_tools(HoverTool(tooltips= [('Country/region','@Country'), ('Date','@ToolTipDate'), 
                                     ('Cases','@Cases_Tot'), ('Cases/1k Ppl','@Cases_Per'),
                                     ('Deaths','@Deaths_Tot'), ('Deaths/1k Ppl','@Deaths_Per')]))

    return p

def make_log(setting):
    #Create figure object.
    p = figure(title = 'Logarithmic Plot of COVID-19 '+plot_title[setting]+' (WHO)', toolbar_location = 'right',
               plot_height = 375, plot_width = 475, x_axis_type = 'datetime', y_axis_type = 'log', 
               tools = 'pan, wheel_zoom, box_zoom, reset')
    
    # Format your x-axis as datetime.
    p.xaxis[0].formatter = DatetimeTickFormatter(days='%b %d')

    p.circle(x = 'Date', y = plot_var[setting], source=source_grp, fill_color = 'Color', line_color = 'Color', 
             legend_field = 'Country')
    
    p.legend.location = "top_left"
    p.legend.click_policy="mute"

    p.add_layout(dt_span)

    # Add your tooltips
    p.add_tools(HoverTool(tooltips= [('Country/region','@Country'), ('Date','@ToolTipDate'), 
                                     ('Cases','@Cases_Tot'), ('Cases/1k Ppl','@Cases_Per'),
                                     ('Deaths','@Deaths_Tot'), ('Deaths/1k Ppl','@Deaths_Per')]))

    return p

# Define the callback function: update_plot
def update_plot(attr, old, new):
    global df_grp
    try:
        selected_index = source_map.selected.indices[0]
        df_grp = pd.DataFrame(columns=['Date', 'ToolTipDate', 'Country', 'Cases_Tot', 'Cases_Per',
                                       'Deaths_Tot', 'Deaths_Per', 'Color'])
        
        for i, selected_index in enumerate(source_map.selected.indices):
            selected_country = df_cases_map.iloc[selected_index]['Country']
            pop_country = df_cases_map.iloc[selected_index]['Population']
            df_sel = df_cases_tran[['Date', 'ToolTipDate']].copy()
            df_sel['Country'] = selected_country
            df_sel['Cases_Tot'] = df_cases_tran[selected_country]
            df_sel['Cases_Per'] = 1000*df_cases_tran[selected_country]/pop_country
            df_sel['Deaths_Tot'] = df_deaths_tran[selected_country]
            df_sel['Deaths_Per'] = 1000*df_deaths_tran[selected_country]/pop_country
            df_sel['Color'] = Category20_16[i]
            df_grp = df_grp.append(df_sel, ignore_index=True)
            
        df_grp = df_grp.sort_values(['Country', 'Date'])
        source_grp.data = df_grp

    except IndexError:
        df_grp = df_cases_tran[['Date', 'ToolTipDate']].copy()
        df_grp['Country'] = 'World'
        df_grp['Cases_Tot'] = df_cases_tran['World']
        df_grp['Cases_Per'] = df_cases_tran['World']/7776350
        df_grp['Deaths_Tot'] = df_deaths_tran['World']
        df_grp['Deaths_Per'] = df_deaths_tran['World']/7776350
        df_grp['Color'] = Category20_16[0]
        df_grp = df_grp.sort_values(['Country', 'Date'])
        source_grp.data = df_grp

    sum_cases_tot = df_grp[df_grp['Date'] == show_dt]['Cases_Tot'].sum()
    sum_cases_per = df_grp[df_grp['Date'] == show_dt]['Cases_Per'].sum()
    sum_deaths_tot = df_grp[df_grp['Date'] == show_dt]['Deaths_Tot'].sum()
    sum_deaths_per = df_grp[df_grp['Date'] == show_dt]['Deaths_Per'].sum()
    source_lab.data = dict(x=[20,20,20,20,20], y=[100,80,60,40,20],
                           text=[slider.value_as_date.strftime("%d %b %Y"),
                                 'Cases: {0}'.format(sum_cases_tot),
                                 'Cases/1k Ppl: {0:.1e}'.format(sum_cases_per),
                                 'Deaths: {0}'.format(sum_deaths_tot),
                                 'Deaths/1k Ppl: {0:.1e}'.format(sum_deaths_per)])
    
def change_var(attr, old, new):
    curdoc().clear()
    curdoc().add_root(column(radio_button, row(button, slider, lin_map), make_map(radio_button.active, lin_map.active), 
                        row(make_lin(radio_button.active), make_log(radio_button.active))))

def animate_update():
    global show_dt
    slider.value = slider.value_as_date + timedelta(1)
    show_dt = slider.value_as_date.strftime("%Y-%m-%d")
    if last_dt.date() == slider.value_as_date:
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
plot_title = ['Cases', 'Cases/1k Ppl', 'Deaths', 'Deaths/1k Ppl']
plot_var = ['Cases_Tot', 'Cases_Per', 'Deaths_Tot', 'Deaths_Per']
plot_min = [1, 0.0005, 1, 0.0005]
plot_max = [max(df_map[plot_var[0]]), max(df_map[plot_var[1]]), max(df_map[plot_var[2]]), max(df_map[plot_var[3]])]

radio_button = RadioButtonGroup(labels=plot_title, active=0)
radio_button.on_change('active', change_var)

# Make a toggle to cycle through the dates
button = Button(label='► Play', width=90, margin = (20, 0, 0, 10))
button.on_click(animate)

# Make a selection of the date to plot
slider = DateSlider(title = 'Date', start = first_dt, end = last_dt, step = 1, value = last_dt, width = 650,
                    margin = (10, 40, 10, 50))
slider.on_change('value_throttled', update_map)

# Make a toggle for changing the map to linear
lin_map = Toggle(label = 'Linear Map', active = False, width = 90, margin = (20, 10, 0, 10))
lin_map.on_change('active', change_var)

# Make a span to show current date in plots
dt_span = Span(location=slider.value_as_date, dimension='height', line_color='red', line_dash='solid',
               line_width=2)

# Update timeseries plots based on selection
source_map.selected.on_change('indices', update_plot)

# Make a set of labels to show some totals on the map
source_lab = ColumnDataSource(data=dict(x=[20,20,20,20,20], y=[100,80,60,40,20],
                                        text=[slider.value_as_date.strftime("%d %b %Y"),
                                              'Cases: {0}'.format(sum_cases_tot),
                                              'Cases/1k Ppl: {0:.1e}'.format(sum_cases_per),
                                              'Deaths: {0}'.format(sum_deaths_tot),
                                              'Deaths/1k Ppl: {0:.1e}'.format(sum_deaths_per)]))
labels = LabelSet(x='x', y='y', x_units='screen', y_units='screen', text='text', source=source_lab,
                  background_fill_color='white', background_fill_alpha=1.0)

# Make a column layout of widgets and plots
curdoc().add_root(column(radio_button, row(button, slider, lin_map), make_map(0,False), row(make_lin(0), make_log(0))))
