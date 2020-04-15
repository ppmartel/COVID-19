from bokeh.io import curdoc, output_notebook, show, output_file
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, GeoJSONDataSource, LinearColorMapper, LogColorMapper, ColorBar
from bokeh.models import Label, LabelSet, HoverTool, TapTool, RadioButtonGroup, Button, DateSlider, Span
from bokeh.models import DatetimeTickFormatter, PrintfTickFormatter, BasicTicker, LogTicker, Toggle
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

if os.path.exists('COVID-19_WHO_Cases.csv'):
    print("Database exists - Reading it")

    df_cases_tot = pd.read_csv('COVID-19_WHO_Cases.csv', encoding='utf-8', index_col='Country')
    df_deaths_tot = pd.read_csv('COVID-19_WHO_Deaths.csv', encoding='utf-8', index_col='Country')

    last_dt = datetime.strptime(df_cases_tot.columns.values[-1],'%Y-%m-%d')
else:
    print("Database does not exist")
    sys.exit()

prev_dt = (last_dt - timedelta(1)).strftime("%Y-%m-%d")
show_dt = last_dt.strftime("%Y-%m-%d")

df_cases_tot.fillna(0, inplace = True)
df_deaths_tot.fillna(0, inplace = True)

# Make a copy within which the day to day changes are calculated
# Probably a better way to do this, but this works for now
df_cases_new = df_cases_tot.copy()
df_deaths_new = df_deaths_tot.copy()
new_dt = last_dt
while new_dt > first_dt:
    df_cases_new[new_dt.strftime("%Y-%m-%d")] = df_cases_new[new_dt.strftime("%Y-%m-%d")] - df_cases_new[(new_dt - timedelta(1)).strftime("%Y-%m-%d")]
    df_deaths_new[new_dt.strftime("%Y-%m-%d")] = df_deaths_new[new_dt.strftime("%Y-%m-%d")] - df_deaths_new[(new_dt - timedelta(1)).strftime("%Y-%m-%d")]
    new_dt = (new_dt - timedelta(1))
df_cases_new[first_dt.strftime("%Y-%m-%d")] = 0
df_deaths_new[first_dt.strftime("%Y-%m-%d")] = 0

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
df_cases_map = df_geo.merge(df_cases_tot, left_on = 'Country', right_on = 'Country', how = 'left')
df_deaths_map = df_geo.merge(df_deaths_tot, left_on = 'Country', right_on = 'Country', how = 'left')

# Build results map
df_map = df_geo.copy()
df_map['Population'] = df_cases_map['Population']
df_map['Cases_Tot_Abs'] = df_cases_map[show_dt]
df_map['Cases_New_Abs'] = df_cases_map[show_dt]-df_cases_map[prev_dt]
df_map['Cases_Tot_Rel'] = 1000*df_cases_map[show_dt]/df_cases_map['Population']
df_map['Cases_New_Rel'] = 1000*(df_cases_map[show_dt]-df_cases_map[prev_dt])/df_cases_map['Population']
df_map['Deaths_Tot_Abs'] = df_deaths_map[show_dt]
df_map['Deaths_New_Abs'] = df_deaths_map[show_dt]-df_deaths_map[prev_dt]
df_map['Deaths_Tot_Rel'] = 1000*df_deaths_map[show_dt]/df_deaths_map['Population']
df_map['Deaths_New_Rel'] = 1000*(df_deaths_map[show_dt]-df_deaths_map[prev_dt])/df_deaths_map['Population']
df_map['Selected'] = df_map['Cases_Tot_Abs']

#Read data to json.
df_map_json = json.loads(df_map.to_json())

#Convert to String like object.
json_map = json.dumps(df_map_json)

#Input GeoJSON source that contains features for plotting.
source_map = GeoJSONDataSource(geojson = json_map)

df_cases_tot = df_cases_tot.drop(['Continental Region','Statistical Region','Population'], axis=1).T
df_cases_tot.reset_index(inplace = True)
df_cases_tot.rename(columns = {df_cases_tot.columns[0]:'Date'}, inplace=True)
df_cases_tot['Date'] = pd.to_datetime(df_cases_tot['Date'])
df_cases_tot['World'] = df_cases_tot.apply(lambda row: row[1 : -1].sum(),axis=1)
df_cases_tot['ToolTipDate'] = df_cases_tot.Date.map(lambda x: x.strftime("%b %d"))

df_cases_new = df_cases_new.drop(['Continental Region','Statistical Region','Population'], axis=1).T
df_cases_new.reset_index(inplace = True)
df_cases_new.rename(columns = {df_cases_new.columns[0]:'Date'}, inplace=True)
df_cases_new['Date'] = pd.to_datetime(df_cases_new['Date'])
df_cases_new['World'] = df_cases_new.apply(lambda row: row[1 : -1].sum(),axis=1)
df_cases_new['ToolTipDate'] = df_cases_new.Date.map(lambda x: x.strftime("%b %d"))

df_deaths_tot = df_deaths_tot.drop(['Continental Region','Statistical Region','Population'], axis=1).T
df_deaths_tot.reset_index(inplace = True)
df_deaths_tot.rename(columns = {df_deaths_tot.columns[0]:'Date'}, inplace=True)
df_deaths_tot['Date'] = pd.to_datetime(df_deaths_tot['Date'])
df_deaths_tot['World'] = df_deaths_tot.apply(lambda row: row[1 : -1].sum(),axis=1)
df_deaths_tot['ToolTipDate'] = df_deaths_tot.Date.map(lambda x: x.strftime("%b %d"))

df_deaths_new = df_deaths_new.drop(['Continental Region','Statistical Region','Population'], axis=1).T
df_deaths_new.reset_index(inplace = True)
df_deaths_new.rename(columns = {df_deaths_new.columns[0]:'Date'}, inplace=True)
df_deaths_new['Date'] = pd.to_datetime(df_deaths_new['Date'])
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

sum_cases_tot_abs = df_grp[df_grp['Date'] == show_dt]['Cases_Tot_Abs'].sum()
sum_cases_new_abs = df_grp[df_grp['Date'] == show_dt]['Cases_New_Abs'].sum()
sum_cases_tot_rel = df_grp[df_grp['Date'] == show_dt]['Cases_Tot_Rel'].sum()
sum_cases_new_rel = df_grp[df_grp['Date'] == show_dt]['Cases_New_Rel'].sum()
sum_deaths_tot_abs = df_grp[df_grp['Date'] == show_dt]['Deaths_Tot_Abs'].sum()
sum_deaths_new_abs = df_grp[df_grp['Date'] == show_dt]['Deaths_New_Abs'].sum()
sum_deaths_tot_rel = df_grp[df_grp['Date'] == show_dt]['Deaths_Tot_Rel'].sum()
sum_deaths_new_rel = df_grp[df_grp['Date'] == show_dt]['Deaths_New_Rel'].sum()

#Define a sequential multi-hue color palette.
palette = brewer['YlGnBu'][9]

#Reverse color order so that dark blue is highest obesity.
palette = palette[::-1]

hover = HoverTool(tooltips= [('Date','@ToolTipDate'),
                             ('Country/region','@Country'), ('Population','@Population'), 
                             ('Tot Cases','@Cases_Tot_Abs (@Cases_Tot_Rel/1k Ppl)')], mode = 'vline')

# Make the map
def make_map():
    #Create figure object.
    p = figure(title = 'Map of COVID-19 '+plot_title[sel_var]+' (WHO)', plot_height = 550 , plot_width = 950, 
                     x_range=(-180, 180), y_range=(-65, 90), toolbar_location = 'right',
                     tools = 'pan, wheel_zoom, box_zoom, reset, tap')
    p.xgrid.grid_line_color = None
    p.ygrid.grid_line_color = None
    
    p.add_layout(labels)
    
    #Instantiate ColorMapper that maps numbers in a range, into a sequence of colors
    if lin_map.active:
        mapper = LinearColorMapper(palette = palette, low = 0, high = plot_max[sel_var])
        color_bar = ColorBar(color_mapper = mapper, label_standoff = 8, width = 500, height = 20, 
                             border_line_color = None, location = (0,0), orientation = 'horizontal', 
                             ticker = BasicTicker(), major_label_overrides = tick_lin[sel_var])
    else:
        mapper = LogColorMapper(palette = palette, low = plot_min[sel_var], high = plot_max[sel_var])
        color_bar = ColorBar(color_mapper = mapper, label_standoff = 8, width = 500, height = 20, 
                             border_line_color = None, location = (0,0), orientation = 'horizontal', 
                             ticker = LogTicker(), major_label_overrides = tick_log[sel_var])
    
    #Add patch renderer to figure. 
    ren_map = p.patches('xs', 'ys', source = source_map, line_color = 'black', line_width = 0.25,
                        fill_color = {'field' : 'Selected', 'transform' : mapper}, fill_alpha = 1)

    #Specify figure layout.
    p.add_layout(color_bar, 'below')
    
    #Add hover tool
    p.add_tools(HoverTool(tooltips = [('Country/region','@Country'), ('Population','@Population'), 
                                      ('Tot Cases','@Cases_Tot_Abs (@Cases_Tot_Rel/1k Ppl)'),
                                      ('New Cases','@Cases_New_Abs (@Cases_New_Rel/1k Ppl)'),
                                      ('Tot Deaths','@Deaths_Tot_Abs (@Deaths_Tot_Rel/1k Ppl)'),
                                      ('New Deaths','@Deaths_New_Abs (@Deaths_New_Rel/1k Ppl)')]))

    return p

# Make linear plot
def make_lin():
    #Create figure object.
    p = figure(title = 'Linear Plot of COVID-19 '+plot_title[sel_var]+' (WHO)', toolbar_location = 'right',
               plot_height = 375, plot_width = 475, x_axis_type = 'datetime', 
               tools = 'pan, wheel_zoom, box_zoom, reset')

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
    #p.add_tools(HoverTool(tooltips= [('Date','@ToolTipDate'),
    #                                 ('Country/region','@Country'), ('Population','@Population'), 
    #                                 ('Tot Cases','@Cases_Tot_Abs (@Cases_Tot_Rel/1k Ppl)'),
    #                                 ('New Cases','@Cases_New_Abs (@Cases_New_Rel/1k Ppl)'),
    #                                 ('Tot Deaths','@Deaths_Tot_Abs (@Deaths_Tot_Rel/1k Ppl)'),
    #                                 ('New Deaths','@Deaths_New_Abs (@Deaths_New_Rel/1k Ppl)')]))
    return p

# Make logarithmic plot
def make_log():
    #Create figure object.
    p = figure(title = 'Logarithmic Plot of COVID-19 '+plot_title[sel_var]+' (WHO)',toolbar_location = 'right',
               plot_height = 375, plot_width = 475, x_axis_type = 'datetime', y_axis_type = 'log', 
               tools = 'pan, wheel_zoom, box_zoom, reset')

    # Format your x-axis as datetime.
    p.xaxis[0].formatter = DatetimeTickFormatter(days='%b %d')

    p.circle(x = 'Date', y = 'Selected', source=source_grp, fill_color = 'Color', line_color = 'Color', 
             legend_field = 'Country')

    p.legend.location = "top_left"
    p.legend.click_policy="mute"

    p.add_layout(dt_span)
    
    # Add your tooltips
    p.add_tools(hover)
    #p.add_tools(HoverTool(tooltips = [('Date','@ToolTipDate'),
    #                                  ('Country/region','@Country'), ('Population','@Population'), 
    #                                  ('Tot Cases','@Cases_Tot_Abs (@Cases_Tot_Rel/1k Ppl)'),
    #                                  ('New Cases','@Cases_New_Abs (@Cases_New_Rel/1k Ppl)'),
    #                                  ('Tot Deaths','@Deaths_Tot_Abs (@Deaths_Tot_Rel/1k Ppl)'),
    #                                  ('New Deaths','@Deaths_New_Abs (@Deaths_New_Rel/1k Ppl)')]))
    return p
    
# Define the callback function: update_map
def update_map(attr, old, new):
    global show_dt
    show_dt = slider.value_as_date.strftime("%Y-%m-%d")
    dt_span.update(location=slider.value_as_date)

    sum_cases_tot_abs = df_grp[df_grp['Date'] == show_dt]['Cases_Tot_Abs'].sum()
    sum_cases_new_abs = df_grp[df_grp['Date'] == show_dt]['Cases_New_Abs'].sum()
    sum_cases_tot_rel = df_grp[df_grp['Date'] == show_dt]['Cases_Tot_Rel'].sum()
    sum_cases_new_rel = df_grp[df_grp['Date'] == show_dt]['Cases_New_Rel'].sum()
    sum_deaths_tot_abs = df_grp[df_grp['Date'] == show_dt]['Deaths_Tot_Abs'].sum()
    sum_deaths_new_abs = df_grp[df_grp['Date'] == show_dt]['Deaths_New_Abs'].sum()
    sum_deaths_tot_rel = df_grp[df_grp['Date'] == show_dt]['Deaths_Tot_Rel'].sum()
    sum_deaths_new_rel = df_grp[df_grp['Date'] == show_dt]['Deaths_New_Rel'].sum()

    if sum_cases_tot_abs > 0:
        txt_cases_tot = 'Tot Cases: {0} (1/{1:.0f} Ppl)'.format(sum_cases_tot_abs, 1000/sum_cases_tot_rel)
    else:
        txt_cases_tot = 'Tot Cases: 0'
    if sum_cases_new_abs > 0:
        txt_cases_new = 'New Cases: {0} (1/{1:.0f} Ppl)'.format(sum_cases_new_abs, 1000/sum_cases_new_rel)
    else:
        txt_cases_new = 'New Cases: 0'
    if sum_deaths_tot_abs > 0:
        txt_deaths_tot = 'Tot Deaths: {0} (1/{1:.0f} Ppl)'.format(sum_deaths_tot_abs, 1000/sum_deaths_tot_rel)
    else:
        txt_deaths_tot = 'Tot Deaths: 0'
    if sum_deaths_new_abs > 0:
        txt_deaths_new = 'New Deaths: {0} (1/{1:.0f} Ppl)'.format(sum_deaths_new_abs, 1000/sum_deaths_new_rel)
    else:
        txt_deaths_new = 'New Deaths: 0'

    source_lab.data = dict(x=[20,20,20,20,20], y=[100,80,60,40,20],
                           text=[slider.value_as_date.strftime("%d %b %Y"), txt_cases_tot, txt_cases_new,
                                 txt_deaths_tot, txt_deaths_new])
    
    df_map['Population'] = df_cases_map['Population']
    df_map['Cases_Tot_Abs'] = df_cases_map[show_dt]
    df_map['Cases_New_Abs'] = df_cases_map[show_dt]-df_cases_map[prev_dt]
    df_map['Cases_Tot_Rel'] = 1000*df_cases_map[show_dt]/df_cases_map['Population']
    df_map['Cases_New_Rel'] = 1000*(df_cases_map[show_dt]-df_cases_map[prev_dt])/df_cases_map['Population']
    df_map['Deaths_Tot_Abs'] = df_deaths_map[show_dt]
    df_map['Deaths_New_Abs'] = df_deaths_map[show_dt]-df_deaths_map[prev_dt]
    df_map['Deaths_Tot_Rel'] = 1000*df_deaths_map[show_dt]/df_deaths_map['Population']
    df_map['Deaths_New_Rel'] = 1000*(df_deaths_map[show_dt]-df_deaths_map[prev_dt])/df_deaths_map['Population']
    df_map['Selected'] = df_map[plot_var[sel_var]]
    
    df_map_json = json.loads(df_map.to_json())
    json_map = json.dumps(df_map_json)
    source_map.geojson = json_map

# Define the callback function: update_plot
def update_plot(attr, old, new):
    global df_grp
    try:
        selected_index = source_map.selected.indices[0]
        df_grp = pd.DataFrame(columns=['Date', 'ToolTipDate', 'Country', 'Population', 'Cases_Tot_Abs', 'Cases_New_Abs', 'Cases_Tot_Rel', 'Cases_New_Rel',
                                       'Deaths_Tot_Abs', 'Deaths_New_Abs', 'Deaths_Tot_Rel', 'Deaths_New_Rel', 'Selected', 'Color'])
        
        for i, selected_index in enumerate(source_map.selected.indices):
            selected_country = df_cases_map.iloc[selected_index]['Country']
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
            df_sel['Color'] = Category20_16[i]
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

    sum_cases_tot_abs = df_grp[df_grp['Date'] == show_dt]['Cases_Tot_Abs'].sum()
    sum_cases_new_abs = df_grp[df_grp['Date'] == show_dt]['Cases_New_Abs'].sum()
    sum_cases_tot_rel = df_grp[df_grp['Date'] == show_dt]['Cases_Tot_Rel'].sum()
    sum_cases_new_rel = df_grp[df_grp['Date'] == show_dt]['Cases_New_Rel'].sum()
    sum_deaths_tot_abs = df_grp[df_grp['Date'] == show_dt]['Deaths_Tot_Abs'].sum()
    sum_deaths_new_abs = df_grp[df_grp['Date'] == show_dt]['Deaths_New_Abs'].sum()
    sum_deaths_tot_rel = df_grp[df_grp['Date'] == show_dt]['Deaths_Tot_Rel'].sum()
    sum_deaths_new_rel = df_grp[df_grp['Date'] == show_dt]['Deaths_New_Rel'].sum()

    if sum_cases_tot_abs > 0:
        txt_cases_tot = 'Tot Cases: {0} (1/{1:.0f} Ppl)'.format(sum_cases_tot_abs, 1000/sum_cases_tot_rel)
    else:
        txt_cases_tot = 'Tot Cases: 0'
    if sum_cases_new_abs > 0:
        txt_cases_new = 'New Cases: {0} (1/{1:.0f} Ppl)'.format(sum_cases_new_abs, 1000/sum_cases_new_rel)
    else:
        txt_cases_new = 'New Cases: 0'
    if sum_deaths_tot_abs > 0:
        txt_deaths_tot = 'Tot Deaths: {0} (1/{1:.0f} Ppl)'.format(sum_deaths_tot_abs, 1000/sum_deaths_tot_rel)
    else:
        txt_deaths_tot = 'Tot Deaths: 0'
    if sum_deaths_new_abs > 0:
        txt_deaths_new = 'New Deaths: {0} (1/{1:.0f} Ppl)'.format(sum_deaths_new_abs, 1000/sum_deaths_new_rel)
    else:
        txt_deaths_new = 'New Deaths: 0'
        
    source_lab.data = dict(x=[20,20,20,20,20], y=[100,80,60,40,20],
                           text=[slider.value_as_date.strftime("%d %b %Y"), txt_cases_tot, txt_cases_new,
                                 txt_deaths_tot, txt_deaths_new])
    
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
        hover.tooltips = [('Country/region','@Country'), ('Population','@Population'), 
                          ('New Deaths','@Deaths_New_Abs (@Deaths_New_Rel/1k Ppl)')]
    elif rb_cases_deaths.active:
        hover.tooltips = [('Country/region','@Country'), ('Population','@Population'), 
                          ('Tot Deaths','@Deaths_Tot_Abs (@Deaths_Tot_Rel/1k Ppl)')]
    elif rb_tot_new.active:
        hover.tooltips = [('Country/region','@Country'), ('Population','@Population'), 
                          ('New Cases','@Cases_New_Abs (@Cases_New_Rel/1k Ppl)')]
    else:
        hover.tooltips = [('Country/region','@Country'), ('Population','@Population'), 
                          ('Tot Cases','@Cases_Tot_Abs (@Cases_Tot_Rel/1k Ppl)')]

    curdoc().add_root(column(row(rb_cases_deaths, rb_abs_rel, rb_tot_new), row(button, slider, lin_map), make_map(), row(make_lin(), make_log())))

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
plot_title = ['Tot Cases', 'New Cases', 'Tot Cases/1k Ppl', 'New Cases/1k Ppl', 'Tot Deaths', 'New Deaths', 'Tot Deaths/1k Ppl', 'New Deaths/1k Ppl']
plot_var = ['Cases_Tot_Abs', 'Cases_New_Abs', 'Cases_Tot_Rel', 'Cases_New_Rel', 'Deaths_Tot_Abs', 'Deaths_New_Abs', 'Deaths_Tot_Rel', 'Deaths_New_Rel']
plot_min = [1, 1, 0.0005, 0.0005, 1, 1, 0.0005, 0.00001]
plot_max = [max(df_map[plot_var[0]]), max(df_map[plot_var[1]]), max(df_map[plot_var[2]]), max(df_map[plot_var[3]]), max(df_map[plot_var[4]]), max(df_map[plot_var[5]]), max(df_map[plot_var[6]]), max(df_map[plot_var[7]])]
tick_lin = [{'0':'0', '50000':'50k', '100000':'100k', '150000':'150k', '200000':'200k', '250000':'250k', '300000':'300k', '350000':'350k', '400000':'400k', '500000':'500k'},
            {'0':'0', '50000':'50k', '100000':'100k', '150000':'150k', '200000':'200k', '250000':'250k', '300000':'300k', '350000':'350k', '400000':'400k', '500000':'500k'},
            {'0.5':'1/2000', '1':'1/1000', '1.5':'1/666', '2':'1/500', '2.5':'1/400', '3':'1/333', '3.5':'1/286', '4':'1/250', '4.5':'1/222', '5':'1/200'},
            {'0.5':'1/2000', '1':'1/1000', '1.5':'1/666', '2':'1/500', '2.5':'1/400', '3':'1/333', '3.5':'1/286', '4':'1/250', '4.5':'1/222', '5':'1/200'},
            {'0':'0', '50000':'50k', '100000':'100k', '150000':'150k', '200000':'200k', '250000':'250k', '300000':'300k', '350000':'350k', '400000':'400k', '500000':'500k'},
            {'0':'0', '50000':'50k', '100000':'100k', '150000':'150k', '200000':'200k', '250000':'250k', '300000':'300k', '350000':'350k', '400000':'400k', '500000':'500k'},
            {'0.5':'1/2000', '1':'1/1000', '1.5':'1/666', '2':'1/500', '2.5':'1/400', '3':'1/333', '3.5':'1/286', '4':'1/250', '4.5':'1/222', '5':'1/200'},
            {'0.5':'1/2000', '1':'1/1000', '1.5':'1/666', '2':'1/500', '2.5':'1/400', '3':'1/333', '3.5':'1/286', '4':'1/250', '4.5':'1/222', '5':'1/200'}]
tick_log = [{'1':'1', '10':'10', '100':'100', '1000':'1k', '10000':'10k', '100000':'100k', '1000000':'1M'},
            {'1':'1', '10':'10', '100':'100', '1000':'1k', '10000':'10k', '100000':'100k', '1000000':'1M'},
            {'0.00001':'1/100M', '0.0001':'1/10M', '0.001':'1/1M', '0.01':'1/100k', '0.1':'1/10k', '1':'1/1k', '10':'1/100', '100':'1/10'},
            {'0.00001':'1/100M', '0.0001':'1/10M', '0.001':'1/1M', '0.01':'1/100k', '0.1':'1/10k', '1':'1/1k', '10':'1/100', '100':'1/10'},
            {'1':'1', '10':'10', '100':'100', '1000':'1k', '10000':'10k', '100000':'100k', '1000000':'1M'},
            {'1':'1', '10':'10', '100':'100', '1000':'1k', '10000':'10k', '100000':'100k', '1000000':'1M'},
            {'0.00001':'1/100M', '0.0001':'1/10M', '0.001':'1/1M', '0.01':'1/100k', '0.1':'1/10k', '1':'1/1k', '10':'1/100', '100':'1/10'},
            {'0.00001':'1/100M', '0.0001':'1/10M', '0.001':'1/1M', '0.01':'1/100k', '0.1':'1/10k', '1':'1/1k', '10':'1/100', '100':'1/10'}]

rb_cases_deaths = RadioButtonGroup(labels=['Cases', 'Deaths'], active=0)
rb_cases_deaths.on_change('active', change_var)

rb_abs_rel = RadioButtonGroup(labels=['Per Region', 'Per 1k Ppl'], active=0)
rb_abs_rel.on_change('active', change_var)

rb_tot_new = RadioButtonGroup(labels=['Total', 'New'], active=0)
rb_tot_new.on_change('active', change_var)

sel_var = int(str(rb_cases_deaths.active)+str(rb_abs_rel.active)+str(rb_tot_new.active), 2)

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
                                              'Tot Cases: {0} (1/{1:.0f} Ppl)'.format(sum_cases_tot_abs, 1000/sum_cases_tot_rel),
                                              'New Cases: {0} (1/{1:.0f} Ppl)'.format(sum_cases_new_abs, 1000/sum_cases_new_rel),
                                              'Tot Deaths: {0} (1/{1:.0f} Ppl)'.format(sum_deaths_tot_abs, 1000/sum_deaths_tot_rel),
                                              'New Deaths: {0} (1/{1:.0f} Ppl)'.format(sum_deaths_new_abs, 1000/sum_deaths_new_rel)]))
labels = LabelSet(x='x', y='y', x_units='screen', y_units='screen', text='text', source=source_lab,
                  text_font_size='10pt', background_fill_color='white', background_fill_alpha=1.0)

# Make a column layout of widgets and plots
curdoc().add_root(column(row(rb_cases_deaths, rb_abs_rel, rb_tot_new), row(button, slider, lin_map), make_map(), row(make_lin(), make_log())))
