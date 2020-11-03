import plotly.graph_objects as go
import pandas as pd
import numpy as np
import json
from urllib.request import urlopen
###
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Output, Input, State

from make_map import *

data = pd.read_csv('app_data/historic_data.csv', dtype={"fips": str})
model_predictions = pd.read_csv('app_data/model_predictions.csv', dtype={"fips": str})

with urlopen('https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json') as response:
    counties = json.load(response)
fips_table = pd.read_csv('app_data/fips_table.csv', dtype={"fips": str})

# YEAR
# 2012, ... , 2017
YEARS = data['YEAR'].unique()
YEARS.sort()
min_YEARS = int(min(YEARS)-1)

# DAY_WEEK
# 1: Saturday, 2: Monday, ... , 7: Sunday
DAY_WEEKS_labels = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
DAY_WEEKS = data['DAY_WEEK'].unique()
DAY_WEEKS.sort()
min_DAY_WEEKS = int(min(DAY_WEEKS)-1)

# HOUR
# 0: 12am - 4am
# 1: 4am - 8am
# .. 5: 8pm -12am
HOURS_labels = ['12am - 4am', '4am - 8am', '8am - 12pm', '12pm - 4pm', '4pm - 8pm', '8pm - 12am']
HOURS = data['HOUR'].unique()
HOURS.sort()
min_HOURS = int(min(HOURS)-1)

fig_initial = totals_map(x=data, d={}, ft = fips_table, counties=counties)


app = dash.Dash(__name__)
server = app.server

app.layout = html.Div([
	html.Div(id='root', style={'width': '90%', 'padding-left': '5%', 'padding-right': '5%', 'padding-bottom': '3%', 'float': 'left'}, children=[
		html.Div(id="header", children=[
            html.H1(children="U.S. Vehicle Accident Fatalities"),
            html.P(
            	children=["A heatmap of accidents per county in the U.S. involving at least one fatality.",
            	html.Br(),
            	"Historical data for 2012-2018 obtained from ",
            	html.A(href='https://www.nhtsa.gov/research-data/fatality-analysis-reporting-system-fars', children="NHTSA.\n"),
            	html.Br(),
            	html.Br(),
            	"Use the sliders to specify constraints on the time of occurence of the accidents.",
            	html.Br(),
            	"The model predicts the total expected number of fatal accidents satisfying the selected constraints, over a year of time.",
            ]),
			# html.P( 
   #          	children=[
   #          	"Use the sliders to specify constraints on the time of occurence of the accidents.",
   #          ]),
   #          html.P( 
   #          	children=[
   #          	'The model predicts the total expected number of fatal accidents satisfying the selected constraints, over a year of time.',
   #          ]),
        ]),
		html.Div(id='map-container', style={'width': '64%', 'float': 'right'}, children=[
			dcc.Graph(id='map', figure=fig_initial)
		]),
		html.Div(id='settings-container', style={'width': '34%', 'float': 'left', 'padding-top': '1%'}, children=[
			dcc.Dropdown(
				id='toggle-mode',
				options = [{'label': 'Historic data', 'value': 'historic'}, {'label': 'Model predictions', 'value': 'model'}],
				value='historic',
				clearable=False
			),
			html.Div(id='sliders-container', style={'padding-top': '5%', 'padding-right': '2%'}, children=[
				html.Div(id='year-slider-div', style={'display': 'block'}, children=[
				    dcc.Slider(
				    	id='year-slider',
				    	min=min_YEARS,
				    	max=2018,
				    	value=min_YEARS,
				    	# marks = {str(year) for year in YEARS},
				    	marks={**{min_YEARS: 'All'}, **{int(year): str(year) for year in YEARS}},
				    	step=None
				    )
		    	]),
				dcc.Slider(
			    	id='day_week-slider',
			    	min=min_DAY_WEEKS,
			    	max=7,
			    	value=min_DAY_WEEKS,
			    	marks = {**{min_DAY_WEEKS: 'All'},**{int(day_week): label for day_week, label in zip(DAY_WEEKS, DAY_WEEKS_labels)}},
			    	step=None
			    ),
			    dcc.Slider(
			    	id='hour-slider',
			    	min=min_HOURS,
			    	max=5,
			    	value=min_HOURS,
			    	marks = {**{min_HOURS: 'All'},**{int(hour): label for hour, label in zip(HOURS, HOURS_labels)}},
			    	step=None
			    )
			])
		]),
	]),
	html.Div(id='footer', style={'width': '90%', 'padding-left': '5%', 'padding-right': '5%'}, children=[
        html.H3(children="Notes"),
        html.P(
        	children=["1. Data is transformed by log(x+1) for the visualization.",
        	html.Br(),
        	"2. The prediction model is a random forest fitted on the data from years 2012-2017. See the ",
        	html.A(href='https://github.com/jackklys/trafficaccidentapp', children='github repo'),
        	" for more details."
        ])
	])
])

@app.callback(
	Output('year-slider-div', 'style'),
	[Input('toggle-mode', 'value')])
def hide_slider(mode):
	if mode=='model':
		style={'display': 'none'}
	elif mode=='historic':
		style={'display': 'block'}

	return style


@app.callback(
	Output('map', 'figure'),
	[Input('year-slider', 'value'),
	Input('day_week-slider', 'value'),
	Input('hour-slider', 'value'),
	Input('toggle-mode', 'value')
	],
	[State('map', 'figure')])
def draw_map(year, day_week, hour, mode, figure):
	d = {}
	if year!=min_YEARS and mode=='historic':
		d['YEAR'] = year
	if day_week!=min_DAY_WEEKS:
		d['DAY_WEEK'] = day_week
	if hour!=min_HOURS:
		d['HOUR'] = hour

	if mode=='model':
		data_in = model_predictions
	elif mode=='historic':
		data_in = data
	z, max_val = fips_total(data_in, d, fips_table)

	temp = z['Total']!=0
	z.loc[temp,'Total'] += 1
	z.loc[temp,'Total'] = z.loc[temp,'Total'].apply(np.log)
	max_val = np.log(max_val)

	figure['data'][0]['z'] = z['Total']
	figure['data'][0]['zmax'] = max_val

	return figure

if __name__ == "__main__":
    server.run(host='0.0.0.0', debug=True)
