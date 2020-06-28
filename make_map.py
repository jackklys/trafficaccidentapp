import pandas as pd
import numpy as np
import plotly.graph_objects as go
import json
from urllib.request import urlopen


def fips_total(x, d, ft):
    ''' e.g. d = {'YEAR': 2012, 'DAY_WEEK': 1} '''
    # restrict x and fips_table to d['STATE'] if applicable
    if 'STATE' in d:
        x = x.loc[x['STATE']==d['STATE']]
        new_fips_table = ft.loc[ft['STATE']==d['STATE']]
    else:
        new_fips_table = ft
    
    # find max value for the grouping given by d
    max_val = x.groupby(['STATE', 'COUNTY', 'fips']+list(d.keys())).sum()['Total'].max()
    
    # extract rows specified by d
    if d:
        mask = pd.concat([x[key]==val for key,val in d.items()], axis=1).all(axis=1)
        x = x[mask]
        
    # aggregate and rename
    x = x.groupby(['STATE', 'COUNTY', 'fips']).sum()
    x.index = x.index.droplevel([0,1])
    x = x.reset_index()
    
    # add rows for fips with 0 totals
    x = new_fips_table.drop(['STATE','COUNTY'], axis=1).join(x.set_index('fips'), on='fips')    
    x.loc[x['Total'].isna(), 'Total']=0
    return x, max_val

def make_map(z, max_val, counties):
    fig = go.Figure(go.Choroplethmapbox(geojson=counties, locations=z['fips'], z=z['Total'],
                                    colorscale='YlGnBu', zmin=0, zmax=max_val,
                                    marker_opacity=1, marker_line_width=0.1))
    fig.update_layout(mapbox_style="carto-positron",
                      mapbox_zoom=3, mapbox_center = {"lat": 37.0902, "lon": -95.7129})
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    return fig
    
def totals_map(x, d, ft, counties):
    z, max_val = fips_total(x, d, ft)
    
    #transform
    temp = z['Total']!=0
    z.loc[temp,'Total'] = z.loc[temp,'Total'].apply(np.log)
    max_val = np.log(max_val)
    
    fig = make_map(z, max_val, counties)
    return fig