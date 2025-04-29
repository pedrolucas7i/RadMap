# PORTUGAL RADIATION PANEL (RADMAP)
# CODE: Pedro Lucas
# FILE: app.py

import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dotenv import load_dotenv
import os
import pymysql
from apscheduler.schedulers.background import BackgroundScheduler
import time

# Load sensitive information
load_dotenv('.env')
host = os.getenv('MARIADB_HOST')
user = os.getenv('MARIADB_USER')
password = os.getenv('MARIADB_PASSWORD')
database_name = os.getenv('MARIADB_DATABASE')

# Connect to MariaDB
connection = pymysql.connect(
    host=host,
    user=user,
    password=password,
    database=database_name
)

def update_data():
    """Fetch the data from MariaDB and convert it to a DataFrame"""
    query = f"SELECT * FROM {os.getenv('MARIADB_TABLE')}"
    db_df = pd.read_sql(query, connection)
    return db_df

def get_place(place):
    """Get the latest data for a specific place"""
    global latest_data
    data = latest_data[latest_data['place'] == place]
    return data.iloc[-1] if not data.empty else None

def get_all_from_place(place):
    """Get all data for a specific place"""
    global latest_data
    data = latest_data[latest_data['place'] == place]
    df = pd.DataFrame(data, columns=['hour', 'place', 'value', 'latitude', 'longitude'])
    return df

def create_dataframes():
    """Create a consolidated DataFrame for the places."""
    global latest_data
    data = []
    for place in latest_data['place'].unique():
        data.append(get_place(place))
    df = pd.DataFrame(data, columns=['hour', 'place', 'value', 'latitude', 'longitude'])
    return df

def fetch_and_update_data():
    """Fetch new data every minute and update the global DataFrame."""
    global latest_data
    print("Updating data...")
    latest_data = update_data()
    print("Data updated!")

# Initialize data
fetch_and_update_data()
latest_data = update_data()

# Set up the scheduler to update data every 5 minutes
scheduler = BackgroundScheduler()
scheduler.add_job(func=fetch_and_update_data, trigger="interval", minutes=5)
scheduler.start()

selected_place = "Lisboa"

# Create the Dash app
app = dash.Dash(__name__, title="Radioactivity Dashboard")

app.layout = html.Div([
    html.Div(
        id='info-title',
        className='info-title',
        children=[
            html.H1("Radioactivity Dashboard"),
            html.Div(
                id='history',
                className='history',
                children=[
                    dcc.Dropdown(
                        id='title-dropdown',
                        options=[],
                        value=None,
                        className='dropdown'
                    ),
                    html.Br(),
                    dcc.Graph(
                        id='history-graph',
                    )
                ]
            )
        ]
    ),
    dcc.Graph(
        id='map',
    ),
    html.A(
        children=[
            html.Img(
                id='vostpt-logo',
                src="assets/VOSTPT_LOGO_2023_cores.svg",
            )
        ],
        href="https://vost.pt",
    ),
    dcc.Interval(
        id='interval-component',
        interval=60*5000,  # Update every 5 minutes
        n_intervals=0
    )
])

@app.callback(
    [Output('title-dropdown', 'options'),
     Output('title-dropdown', 'value')],
    Input('title-dropdown', 'value')
)
def update_dropdown(selected_place):
    """Update the dropdown options with the available places."""
    dropdown_options = [{'label': place, 'value': place} for place in latest_data['place'].unique()]

    # Set the initial value to "Lisboa" if not selected
    if selected_place is None:
        initial_value = "Lisboa"
    else:
        initial_value = selected_place

    return dropdown_options, initial_value

@app.callback(
    Output("history-graph", "figure"), 
    Input("title-dropdown", "value"))
def update_history_graph(place):
    """Update the history graph based on the selected place."""
    selected_place = place if place is not None else selected_place
    fig = px.line(
        get_all_from_place(selected_place),
        x="hour",
        y="value",
        color="place"
    )
    return fig

@app.callback(
    Output('map', 'figure'),
    Input('interval-component', 'n_intervals')
)
def update_map(n_intervals):
    """Update the map with the latest data."""
    figure = go.Figure(
        data=go.Scattermapbox(
            lat=create_dataframes()['latitude'],
            lon=create_dataframes()['longitude'],
            mode='markers',
            marker=dict(
                size=(create_dataframes()['value'] / 9) + 5,  # Adjust marker size
                color=create_dataframes()['value'],
                colorscale='Viridis',  # Color scale for the markers
                colorbar=dict(
                    title='Radioactivity'
                )
            ),
            text=create_dataframes()['value'],
            customdata=create_dataframes()[['hour', 'place', 'value']],
            hovertemplate=(
                "<b>Hour:</b> %{customdata[0]}<br>"
                "<b>Place:</b> %{customdata[1]}<br>"
                "<b>Value:</b> %{customdata[2]} nSv/h<br>"
                "<extra></extra>"
            )
        ),
        layout=go.Layout(
            mapbox=dict(
                style="open-street-map",  # Map style
                center=dict(lat=create_dataframes()['latitude'].mean(), lon=create_dataframes()['longitude'].mean()),
                zoom=5
            ),
            margin=dict(r=0, t=0, l=0, b=0)
        )
    )
    return figure

if __name__ == '__main__':
    try:
        app.run_server(debug=False, host='0.0.0.0')
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
