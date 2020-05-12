# COVID-19
A python dashboard for COVID-19 statistics. Deployed at https://worldwide-covid-19.herokuapp.com

History
-------
With the world in the grips of the COVID-19 pandemic, I got tired of looking at daily situation reports from the World Health Organization. I started writing some python code to simply scrape the data from the report pdfs, and plot it. I started to look into producing a dashboard with a map, and eventually landed with Bokeh and GeoPandas. After yet another change to the format of the WHO reports (each requiring new tweaking to the scraper) I found where the data can be directly downloaded, and will rely on that from now on.

Built With
----------
* Python 3.6.10
  * Bokeh 2.0.1
  * Geopandas 0.7.0

Running
-------
First, obviously get python running with the above libraries. Second, go into the cloned directory and download the COVID-19 data from the WHO website into this directory. It is a csv file found at:

https://covid19.who.int/

with the 'Download Map Data' button in the bottom right of the map. Also download, and unzip into this directory, the shape files from natural earth:

https://www.naturalearthdata.com/http//www.naturalearthdata.com/download/110m/cultural/ne_110m_admin_0_countries.zip

Finally run:

`bokeh serve --show COVID-19_WHO.py`

Resources
---------
Data obtained from
* WHO - https://www.who.int/emergencies/diseases/novel-coronavirus-2019/situation-reports/
* Johns Hopkins (working on) - https://github.com/CSSEGISandData/COVID-19

Ideas and code snippets for
* Visualization
  * https://towardsdatascience.com/walkthrough-mapping-basics-with-bokeh-and-geopandas-in-python-43f40aa5b7e9
  * https://towardsdatascience.com/a-complete-guide-to-an-interactive-geographical-map-using-python-f4c5197e23e0
  * https://towardsdatascience.com/data-visualization-with-bokeh-in-python-part-ii-interactions-a4cf994e2512
  * https://jimking100.github.io/2019-09-04-Post-3/
  * http://dmnfarrell.github.io/bioinformatics/bokeh-maps
* Animating
  * https://github.com/bokeh/bokeh/blob/master/examples/app/gapminder/main.py
* Deploying
  * https://blog.thedataincubator.com/2015/09/painlessly-deploying-data-apps-with-bokeh-flask-and-heroku/
  * https://pjandir.github.io/Bokeh-Heroku-Tutorial/
  * https://github.com/datademofun/heroku-basic-flask
