import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objects as go
import dash_bootstrap_components as dbc

import pandas as pd

from src.data.pull_data import pull_data
from src.charts.outbreak_charts import plot_outbreak

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])
app.title = "Outbreak Dashboard"

# Load your dataframes
df_latest = pd.read_parquet("data/latest.parquet")
df_preds = pd.read_parquet("data/predictions.parquet")
df_historical = pd.read_parquet("data/historical.parquet")
df_preds = df_preds.rename(columns={'prediction_for_date': 'date'})

df_latest['state'] = df_latest['item_id'].str.split('_').str[0]
df_preds['state'] = df_preds['item_id'].str.split('_').str[0]
df_preds['label'] = df_preds['item_id'].str.split('_').str[1]

df_historical = df_historical.sort_values(['date', 'item_id'])
df_preds = df_preds.sort_values(['date', 'item_id'])
df_latest = df_latest.sort_values(['date', 'item_id'])

df_outbreak = pd.merge(df_preds, df_latest, on=['item_id', 'date', 'state', 'label'])
df_outbreak['potential_outbreak'] = df_outbreak['new_cases'] > df_outbreak['pred_upper']
num_outbreaks = len(df_outbreak[df_outbreak.potential_outbreak == True])

app.layout = html.Div([
    html.H1("OUTBREAK!", style={
        'color': 'white',
        'font-size': '3vw',
        'textAlign': 'center',
        'margin-top': '20px',
    }),
    html.H2(f"Currently there are {num_outbreaks} outbreaks!", style={
        'color': 'white',
        'font-size': '3vw',
        'textAlign': 'center',
        'margin-top': '20px',
    }),
    dcc.Checklist(
        id='show_outbreaks_toggle',
        options=[
            {'label': 'Show Outbreaks Only', 'value': 'SHOW_OUTBREAKS'},
        ],
        value=[],
        labelStyle={'display': 'block', 'color': 'white'},
        style={'textAlign': 'center', 'margin': '20px'}
    ),
    dcc.Dropdown(
        id='state_dropdown',
    ),
    dcc.Dropdown(
        id='label_dropdown',
    ),
    dcc.Graph(id='outbreak_graph')
], style={'backgroundColor': '#111111', 'color': '#7FDBFF'})

@app.callback(
    Output('state_dropdown', 'options'),
    [Input('show_outbreaks_toggle', 'value')]
)
def update_state_options(toggle_values):
    if 'SHOW_OUTBREAKS' in toggle_values:
        states = df_outbreak[df_outbreak['potential_outbreak'] == True]['state'].unique()
    else:
        states = df_historical['state'].unique()
    
    return [{'label': state, 'value': state} for state in states]

@app.callback(
    Output('label_dropdown', 'options'),
    [Input('state_dropdown', 'value'),
     Input('show_outbreaks_toggle', 'value')]
)
def set_item_options(selected_state, toggle_values):
    if 'SHOW_OUTBREAKS' in toggle_values and selected_state:
        df_filtered = df_outbreak[(df_outbreak['state'] == selected_state) & (df_outbreak['potential_outbreak'] == True)]
    else:
        df_filtered = df_historical[df_historical['state'] == selected_state]
    
    labels = df_filtered['label'].unique() if selected_state else []
    return [{'label': i, 'value': i} for i in labels]

@app.callback(
    Output('outbreak_graph', 'figure'),
    [Input('state_dropdown', 'value'),
     Input('label_dropdown', 'value')]
)
def update_graph(selected_state, label_dropdown):
    if selected_state and label_dropdown:
        filtered_latest = df_latest[(df_latest['state'] == selected_state) & (df_latest.label == label_dropdown)]
        filtered_preds = df_preds[(df_preds['state'] == selected_state) & (df_preds.label == label_dropdown)]
        filtered_historical_chart = df_historical[(df_historical['state'] == selected_state) & (df_historical.label == label_dropdown)]
        fig = plot_outbreak(filtered_historical_chart, filtered_latest, filtered_preds, selected_state, label_dropdown)
        return fig
    return go.Figure()

if __name__ == '__main__':
    #app.run_server(debug=False, host='0.0.0.0', port=8050)
    app.run_server(debug=True, port=8080)
