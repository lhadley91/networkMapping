from matplotlib.pyplot import margins
import plotly.graph_objects as go
import pandas as pd
import numpy as np
def lineSizeType (row):##Here, the exponent determines the 'distance' between each value, and the multiplier just inflates it to the right size (determined by the circle size divided by the max of the ... Maize exponent result) 
    maxValue = 1.270211203
    seperationLength = 1.4
    if row['lineSize']>1:
        return 21
    else:
        return row['lineSize']**seperationLength*(21*maxValue)

pairwiseResults = pd.read_csv("./pairwiseResults/pairwiseResults.csv")
uniqueProducts = pairwiseResults['Product'].unique()
uniqueProducts = np.append(uniqueProducts, "All")
for uniqueProduct in uniqueProducts:
    print("---",uniqueProduct,"--------")
    df_airports = pd.read_csv('./mapData/'+uniqueProduct+'-marketplaces.csv')

    df_flight_paths = pd.read_csv('./mapData/'+uniqueProduct+'-lines.csv')
    df_flight_paths['lineSizeType'] = df_flight_paths.apply (lambda row: lineSizeType(row), axis=1)


    fig = go.Figure()
    flight_paths = []
    for i in range(len(df_flight_paths)):
        fig.add_trace(
            go.Scattergeo(
                lon = [df_flight_paths['start_long'][i], df_flight_paths['end_long'][i]],
                lat = [df_flight_paths['start_lat'][i], df_flight_paths['end_lat'][i]],
                mode = 'lines',
                line = dict(width = df_flight_paths['lineSizeType'][i],color = 'red'),
                opacity = 0.75,
            )
        )
    fig.add_trace(go.Scattergeo(
        lon = df_airports['long'],
        lat = df_airports['lat'],
        text = df_airports['name'],
        textposition="top center", 
        mode = 'markers+text',
        marker = dict(
            size = 21,
            color = 'rgb(0, 0, 0,0.95)',
            line = dict(
                width = 3,
                color = 'rgba(68, 68, 68, 0)'
            )
        )))

    

    fig.update_layout(
        #title_text = 'Trade Flow Corridors',
        showlegend = False,
        margin=dict(l=0, r=0, t=0, b=0),
        height=900,
        width=900,
        geo = dict(
            scope = 'africa',
            projection_type = 'azimuthal equal area',
            showland = True,
            landcolor = 'rgb(243, 243, 243)',
            countrycolor = 'rgb(204, 204, 204)',
        ),
    )
    fig.update_geos(fitbounds="locations", resolution=110)
    fig.write_image("images/"+uniqueProduct+".png")