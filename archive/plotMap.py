import plotly.graph_objects as go
import pandas as pd
import numpy as np

df_airports = pd.read_csv('mapData/Maize-marketplaces.csv')
print(df_airports.head())

df_flight_paths = pd.read_csv('mapData/Maize-lines.csv')
print(df_flight_paths.head())

fig = go.Figure()

fig.add_trace(go.Scattergeo(
    lon = df_airports['long'],
    lat = df_airports['lat'],
    text = df_airports['name'],
    mode = 'markers+text',
    marker = dict(
        size = 15,
        color = 'rgb(0, 0, 0,0.95)',
        line = dict(
            width = 3,
            color = 'rgba(68, 68, 68, 0)'
        )
    )))

flight_paths = []
for i in range(len(df_flight_paths)):
    fig.add_trace(
        go.Scattergeo(
            lon = [df_flight_paths['start_lon'][i], df_flight_paths['end_lon'][i]],
            lat = [df_flight_paths['start_lat'][i], df_flight_paths['end_lat'][i]],
            mode = 'lines',
            line = dict(width = df_flight_paths['lineSize'][i],color = 'red'),
            opacity = 0.75,
        )
    )

fig.update_layout(
    title_text = 'Trade Flow Corridors',
    showlegend = False,
    height=900,
    width=1800,
    geo = dict(
        scope = 'africa',
        projection_type = 'azimuthal equal area',
        showland = True,
        landcolor = 'rgb(243, 243, 243)',
        countrycolor = 'rgb(204, 204, 204)',
    ),
)
fig.update_geos(fitbounds="locations", resolution=110)
fig.write_image("images/test.png")
