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
import numpy as np
import pandas as pd

callback_id = None

##################################################
# Function to get the WHO data from disk
##################################################

def get_who(resolution):
    df = pd.read_csv('WHO-COVID-19-global-data.csv', encoding='utf-8', error_bad_lines=False)

    df.drop(df.columns[[1,3]], axis=1, inplace=True)
    df.rename(columns = {df.columns[0]:'Date', df.columns[1]:'Country', df.columns[2]:'Deaths_New_Abs', df.columns[3]:'Deaths_Tot_Abs', df.columns[4]:'Cases_New_Abs', df.columns[5]:'Cases_Tot_Abs'}, inplace=True)
    df['Date'] = pd.to_datetime(df['Date'])
    df['ToolTipDate'] = df.Date.map(lambda x: x.strftime("%b %d"))

    df['Country'] = df['Country'].str.replace('\s*\(.*\)','')

    df['Country'] = df['Country'].str.replace('Bahamas','The Bahamas')
    df['Country'] = df['Country'].str.replace('Bonaire, Sint Eustatius and Saba','Caribbean Netherlands')
    df['Country'] = df['Country'].str.replace('Brunei Darussalam','Brunei')
    df['Country'] = df['Country'].str.replace('^Congo','Republic of the Congo')
    df['Country'] = df['Country'].str.replace('.*Ivoire','Ivory Coast')
    df['Country'] = df['Country'].str.replace('Curacao','Curaçao')
    df['Country'] = df['Country'].str.replace('Eswatini', 'eSwatini')
    df['Country'] = df['Country'].str.replace('Holy See','Vatican')
    df['Country'] = df['Country'].str.replace('International conveyance','Diamond Princess')
    df['Country'] = df['Country'].str.replace('^Kosovo.*','Kosovo')
    df['Country'] = df['Country'].str.replace('^Lao.*', 'Laos')
    df['Country'] = df['Country'].str.replace('^occupied.*','Palestine')
    df['Country'] = df['Country'].str.replace('Republic of Korea', 'South Korea')
    df['Country'] = df['Country'].str.replace('Republic of Moldova', 'Moldova')
    df['Country'] = df['Country'].str.replace('Russian Federation', 'Russia')
    df['Country'] = df['Country'].str.replace('Saint Barthélemy','Saint Barthelemy')
    df['Country'] = df['Country'].str.replace('Sao Tome and Principe','São Tomé and Príncipe')
    df['Country'] = df['Country'].str.replace('Serbia','Republic of Serbia')
    df['Country'] = df['Country'].str.replace('Syrian Arab Republic','Syria')
    df['Country'] = df['Country'].str.replace('The United Kingdom','United Kingdom')
    df['Country'] = df['Country'].str.replace('Timor-Leste','East Timor')
    df['Country'] = df['Country'].str.replace('Viet Nam','Vietnam')

    for i, index_this in enumerate(df_sub.index[np.where((df_sub[resolution] == 'No') & (df_sub['Subunit'] != df_sub['Country']), True, False)].tolist()):
        df['Country'] = df['Country'].str.replace(df_sub.iloc[index_this,0],df_sub.iloc[index_this,1])
    
    df = df.groupby(['Date','Country']).sum()
    df = df.sort_values(['Country', 'Date'])
    df.reset_index(inplace = True)

    return df

##################################################
# Function to get shapes using geopandas
##################################################

def get_geo(resolution):
    geofile = 'ne_' + resolution + '_admin_0_countries.shp'

    df = gpd.read_file(geofile)[['ADMIN', 'ADM0_A3', 'geometry']]
    df.columns = ['Country','Code','geometry']

    # 2019 update of Macedonia to North Macedonia
    df['Country'] = df['Country'].str.replace('Macedonia','North Macedonia')

    # Specific for JHU, includes Puerto Rico as part of US
    #df['Country'] = df['Country'].str.replace('Puerto Rico','United States of America')

    # Remove Antarctica
    df.drop(df[df['Country'] == 'Antarctica'].index, inplace = True)

    df_countries = pd.read_csv('Countries.csv', encoding='utf-8')[['Country', 'Population']]
    df = df.merge(df_countries, left_on = 'Country', right_on = 'Country', how = 'left')

    # Fix multipolygon rendering (though now selecting a polygon does not select the other parts)
    df = df.explode()
    df.reset_index(inplace = True)

    return df

def get_map(date):
    global df_map
    # Build results map
    df_map = df_geo.copy()
    df_tmp = df_who[df_who['Date'] == date][['Country', 'Cases_Tot_Abs', 'Cases_New_Abs', 'Deaths_Tot_Abs', 'Deaths_New_Abs']]
    df_map = df_map.merge(df_tmp, left_on = 'Country', right_on = 'Country', how = 'left')
    df_map['Cases_Tot_Rel'] = 1000*df_map['Cases_Tot_Abs']/df_map['Population']
    df_map['Cases_New_Rel'] = 1000*df_map['Cases_New_Abs']/df_map['Population']
    df_map['Deaths_Tot_Rel'] = 1000*df_map['Deaths_Tot_Abs']/df_map['Population']
    df_map['Deaths_New_Rel'] = 1000*df_map['Deaths_New_Abs']/df_map['Population']
    df_map['Selected'] = df_map[plot_var[sel_var]]
    df_map.fillna(0, inplace = True)

    #Convert to json for plotting
    df_map_json = json.loads(df_map.to_json())
    json_map = json.dumps(df_map_json)
    return json_map

def get_stats():
    sum_population = df_grp[df_grp['Date'] == show_dt]['Population'].sum()
    sum_cases_tot_abs = df_grp[df_grp['Date'] == show_dt]['Cases_Tot_Abs'].sum()
    sum_cases_new_abs = df_grp[df_grp['Date'] == show_dt]['Cases_New_Abs'].sum()
    sum_cases_tot_rel = 1000*sum_cases_tot_abs/sum_population
    sum_cases_new_rel = 1000*sum_cases_new_abs/sum_population
    sum_deaths_tot_abs = df_grp[df_grp['Date'] == show_dt]['Deaths_Tot_Abs'].sum()
    sum_deaths_new_abs = df_grp[df_grp['Date'] == show_dt]['Deaths_New_Abs'].sum()
    sum_deaths_tot_rel = 1000*sum_deaths_tot_abs/sum_population
    sum_deaths_new_rel = 1000*sum_deaths_new_abs/sum_population

    my_stats = dict(stat=['Tot Cases', 'New Cases', 'Tot Deaths', 'New Deaths'],
                    vabs=[sum_cases_tot_abs, sum_cases_new_abs, sum_deaths_tot_abs, sum_deaths_new_abs],
                    vrel=[my_format(sum_cases_tot_rel), my_format(sum_cases_new_rel),
                          my_format(sum_deaths_tot_rel), my_format(sum_deaths_new_rel)])
    return my_stats


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
    if tog_lin.active:
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
    
    source_out.data = get_stats()
    source_map.geojson = get_map(show_dt)

# Define the callback function: update_plot
def update_plot(attr, old, new):
    global df_grp
    try:
        selected_index = source_map.selected.indices[0]
        old_list = source_map.selected.indices
        old_list.sort()
        new_list = []
        for i,  selected_index in enumerate(source_map.selected.indices):
            new_list = new_list + list(df_map['Country'][df_map['Country'] == df_map.iloc[selected_index]['Country']].index)

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
            selected_country = df_map.iloc[selected_index]['Country']
            if selected_country != prev_country:
                prev_country = selected_country
                pop_country = df_map.iloc[selected_index]['Population']
                df_sel = df_who[df_who['Country'] == selected_country].copy()
                df_sel['Country'] = selected_country
                df_sel['Population'] = pop_country
                df_sel['Cases_Tot_Rel'] = 1000*df_sel['Cases_Tot_Abs']/pop_country
                df_sel['Cases_New_Rel'] = 1000*df_sel['Cases_New_Abs']/pop_country
                df_sel['Deaths_Tot_Rel'] = 1000*df_sel['Deaths_Tot_Abs']/pop_country
                df_sel['Deaths_New_Rel'] = 1000*df_sel['Deaths_New_Abs']/pop_country
                df_sel['Selected'] = df_sel[plot_var[sel_var]]
                df_sel['Color'] = Category20_16[color_index]
                color_index = color_index + 1
                df_grp = df_grp.append(df_sel, ignore_index=True)
                        
        df_grp = df_grp.sort_values(['Country', 'Date'])
        source_grp.data = df_grp

    except IndexError:
        df_grp = df_all.copy()
        df_grp['Selected'] = df_grp[plot_var[sel_var]]
        source_grp.data = df_grp
    
    source_out.data = get_stats()
    
def change_var(attr, old, new):
    curdoc().clear()
    
    global sel_var
    global source_map

    sel_var = int(str(rb_cases_deaths.active)+str(rb_abs_rel.active)+str(rb_tot_new.active), 2)
    source_map = GeoJSONDataSource(geojson = get_map(show_dt))
    
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

    curdoc().add_root(row(column(make_map(), row(column(heading, row(button, tog_lin, tog_res, sizing_mode="stretch_width"), sizing_mode="stretch_width"), column(rb_cases_deaths, rb_tot_new, rb_abs_rel, sizing_mode="stretch_width")), slider, table_out, sizing_mode="scale_width"), column(make_lin(), make_log(), sizing_mode="scale_width"), sizing_mode="stretch_both"))

def change_res(attr, old, new):
    global df_who
    global df_geo

    if tog_res.active:
        df_who = get_who('50m')
        df_geo = get_geo('50m')
    else:
        df_who = get_who('110m')
        df_geo = get_geo('110m')

    change_var(attr, old, new)

def animate_update():
    global show_dt
    slider.value = slider.value_as_date + timedelta(1)
    show_dt = pd.to_datetime(slider.value_as_date)
    if last_dt == pd.to_datetime(slider.value_as_date):
        animate()

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

##################################################
# Main code
##################################################
             
# heading fills available width
heading = Div(text='Worldwide COVID-19 Statistics - <a href="https://www.who.int/emergencies/diseases/novel-coronavirus-2019/situation-reports" target="_blank">WHO</a></br>Click on countries (multiple with shift)</br>Created by Phil Martel - <a href="https://github.com/ppmartel/COVID-19" target="_blank">GitHub Repository</a>',
              style={'background-color':'#c8cfd6', 'outline':'black solid thin', 'text-align':'center'},
              height=70, align="center", sizing_mode="stretch_width")

# Make a toggle to cycle through the dates
button = Button(label='► Play', height = 30)
button.on_click(animate)

# Make a toggle for changing the map to linear
tog_lin = Toggle(label = 'Lin Map', active = False, height = 30)
tog_lin.on_change('active', change_var)

tog_res = Toggle(label = 'Hi Res', active = False, height = 30)
tog_res.on_change('active', change_res)

rb_cases_deaths = RadioButtonGroup(labels=['Cases', 'Deaths'], active=0, height = 30)
rb_cases_deaths.on_change('active', change_var)

rb_abs_rel = RadioButtonGroup(labels=['Per Region', 'Per 1k Ppl'], active=0, height = 30)
rb_abs_rel.on_change('active', change_var)

rb_tot_new = RadioButtonGroup(labels=['Total', 'New'], active=0, height = 30)
rb_tot_new.on_change('active', change_var)

sel_var = int(str(rb_cases_deaths.active)+str(rb_abs_rel.active)+str(rb_tot_new.active), 2)

# Make a selection of what to plot
plot_title = ['Tot Cases', 'New Cases', 'Tot Cases/1k Ppl', 'New Cases/1k Ppl',
              'Tot Deaths', 'New Deaths', 'Tot Deaths/1k Ppl', 'New Deaths/1k Ppl']
plot_var = ['Cases_Tot_Abs', 'Cases_New_Abs', 'Cases_Tot_Rel', 'Cases_New_Rel',
            'Deaths_Tot_Abs', 'Deaths_New_Abs', 'Deaths_Tot_Rel', 'Deaths_New_Rel']

##################################################
# Get subunits for countries to merge
##################################################
df_sub = pd.read_csv('Subunits_and_small_shapes.csv', encoding='utf-8', error_bad_lines=False)

df_who = get_who('110m')
df_geo = get_geo('110m')

first_dt = min(df_who['Date'])
last_dt = max(df_who['Date'])
prev_dt = (last_dt - timedelta(1))
show_dt = last_dt

source_map = GeoJSONDataSource(geojson = get_map(show_dt))

# Sum to get world statistics
df_all = df_who.groupby('Date').sum()
df_all.reset_index(inplace = True)
df_all['ToolTipDate'] = df_all.Date.map(lambda x: x.strftime("%b %d"))
df_all['Country'] = 'World'
df_all['Population'] = 7776350000
df_all['Cases_Tot_Rel'] = df_all['Cases_Tot_Abs']/7776350
df_all['Cases_New_Rel'] = df_all['Cases_New_Abs']/7776350
df_all['Deaths_Tot_Rel'] = df_all['Deaths_Tot_Abs']/7776350
df_all['Deaths_New_Rel'] = df_all['Deaths_New_Abs']/7776350
df_all['Selected'] = df_all['Cases_Tot_Abs']
df_all['Color'] = Category20_16[0]

df_grp = df_all.copy()
source_grp = ColumnDataSource(df_grp)

#Define a sequential multi-hue color palette.
palette = brewer['YlGnBu'][9]

#Reverse color order so that dark blue is highest obesity.
palette = palette[::-1]

# Hover tool
hover = HoverTool(tooltips= [('Date','@ToolTipDate'),
                             ('Country/region','@Country'), ('Population','@Population'),
                             ('Cases','@Cases_Tot_Abs @Cases_Tot_Rel{custom}')],
                  formatters={'@Cases_Tot_Rel' : custom}, mode = 'vline')

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
source_out = ColumnDataSource(get_stats())
columns_out = [TableColumn(field='stat', title="Statistic"),
               TableColumn(field='vabs', title="Per Region"),
               TableColumn(field='vrel', title="Per Capita")]
table_out = DataTable(source=source_out, columns=columns_out, height=125, width=100, sizing_mode="stretch_width")

# Make a column layout of widgets and plots
curdoc().add_root(row(column(make_map(), row(column(heading, row(button, tog_lin, tog_res, sizing_mode="stretch_width"), sizing_mode="stretch_width"), column(rb_cases_deaths, rb_tot_new, rb_abs_rel, sizing_mode="stretch_width")), slider, table_out, sizing_mode="scale_width"), column(make_lin(), make_log(), sizing_mode="scale_width"), sizing_mode="stretch_both"))
