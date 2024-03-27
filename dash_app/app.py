import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objects as go
import dash_bootstrap_components as dbc

import pandas as pd

from src.data.pull_data import pull_data
from src.charts.outbreak_charts import plot_outbreak
from src.tabs.main_tab_helper import get_outbreaks, label_and_info, uncertainty_level_tooltip

common_div_style = {
    'backgroundColor': 'black', 
    'padding': '10px', 
    'border-radius': '5px',
    'margin-bottom': '20px'  
}

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY, dbc.icons.BOOTSTRAP])
app.title = "Outbreak Dashboard"

# Load your dataframes
df_latest = pd.read_parquet("data/latest.parquet")
df_preds = pd.read_parquet("data/predictions.parquet")
df_historical = pd.read_parquet("data/historical.parquet")
df_preds = df_preds.rename(columns={'prediction_for_date': 'date'})
df_latest['new_cases'] = df_latest.new_cases.fillna(0)

df_preds['label'] = df_preds['item_id'].str.split('_').str[1]
num_diseases_tracked = len(df_latest['label'].unique())

#item_ids_all_na = df_historical.groupby('item_id').filter(lambda x: x['new_cases'].isna().all())['item_id'].unique()

#df_historical = df_historical[~df_historical.item_id.isin(item_ids_all_na)]
#df_preds = df_preds[~df_preds.item_id.isin(item_ids_all_na)]
#print(df_preds[df_preds.item_id=='KENTUCKY_Shigellosis'])

df_latest['state'] = df_latest['item_id'].str.split('_').str[0]
df_preds['state'] = df_preds['item_id'].str.split('_').str[0]

df_historical = df_historical.sort_values(['date', 'item_id'])
df_preds = df_preds.sort_values(['date', 'item_id'])
df_latest = df_latest.sort_values(['date', 'item_id'])
#print(df_historical[df_historical.item_id=='ARIZONA_Anthrax'])
#print(df_latest[df_latest.item_id=='ARIZONA_Anthrax'])
#df_latest = df_latest.drop(columns='fill_type')
#fill_type_df = df_historical[['item_id', 'fill_type']].drop_duplicates()
#df_latest = df_latest.merge(fill_type_df, on='item_id', how='left')
#df_latest.loc[df_latest['fill_type'] == 'fill with 0', 'new_cases'] = 0


#df_outbreak = pd.merge(df_preds, df_latest, on=['item_id', 'date', 'state', 'label'])
#df_outbreak['potential_outbreak'] = df_outbreak['new_cases'] > df_outbreak['pred_upper']
#num_outbreaks = len(df_outbreak[df_outbreak.potential_outbreak == True])

app.layout = html.Div([
    
    html.Div(children=[
        html.H1("OUTBREAK!", style={
        'color': 'black',  # Text color
        'font-size': '6vw',
        'textAlign': 'center',
        'margin-top': '20px',
        'text-shadow': '''
            0 0 5px #B22222, 
            0 0 10px #B22222, 
            0 0 15px #B22222, 
            0 0 20px #B22222, 
            0 0 25px #B22222, 
            0 0 30px #B22222''',  # Multiple layers of red shadow for a deeper red effect
        'font-weight': 'bold',
        'background-color': '#300',  # Optional: dark red background for contrast
        'display': 'inline-block',  # Ensures the background only wraps the text
        'padding': '10px',  # Adds some space around the text within its "button-like" background
        'border-radius': '50px'  # Optional: rounds the corners of the background for a smoother look
        }),
        ], style={'textAlign': 'center', 'width': '100%', 'margin-top': '0px'}),


    dbc.Row(
        dbc.Col([
            html.Div([
                    label_and_info,  # Assuming this includes your H2 and info icon
                    uncertainty_level_tooltip  # Ensure this tooltip targets the ID of the info_icon correctly
                ], style={'textAlign': 'left', 'color': 'white', 'font-size': '1.5vw'}),
            dcc.Dropdown(
                id='interval_dropdown',
                options=[
                    {'label': '80%', 'value': 80},
                    {'label': '90%', 'value': 90},
                    {'label': '95%', 'value': 95},
                    {'label': '97%', 'value': 97},
                    {'label': '99%', 'value': 99},
                    {'label': '99.9%', 'value': 99.9}
                ],
                value=99,  # Default value
                clearable=False,
                style={'marginBottom': '10px', 'fontSize': '1.2em', 'width': '200px', 'margin': '0 auto', 'textAlign': 'left',
                    'backgroundColor': '#303030'}
            ),
        ], width={'size': 6, 'offset': 0}),  # Adjust 'size' and 'offset' for perfect centering
            align="center",  
            style={'margin': '20px auto', 'width': '100%'}
        ),

        # KPI and Placeholder Row
        dbc.Row([
            dbc.Col(html.Div(id='outbreak_kpi', style={**common_div_style, 'height': '95%'}), width=6),
            dbc.Col(html.Div(id='county-map-placeholder', children=[html.H3("Placeholder")], style={**common_div_style, 'height': '95%'}), width=6)
        ], align="stretch"),
    
    dcc.Checklist(
        id='show_outbreaks_toggle',
        options=[
            {'label': ' Show Outbreaks Only', 'value': 'SHOW_OUTBREAKS'},
        ],
        value=[],
        labelStyle={'display': 'block', 'color': 'white', 'fontSize': 20},  
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
    [Input('show_outbreaks_toggle', 'value'),
     Input('interval_dropdown', 'value')]  # Add this input
)
def update_state_options(toggle_values, selected_interval):
    # Generate df_outbreak dynamically based on the selected interval
    df_outbreak = get_outbreaks(df_preds, df_latest, chosen_interval=selected_interval)
    
    if 'SHOW_OUTBREAKS' in toggle_values:
        states = df_outbreak[df_outbreak['potential_outbreak'] == True]['state'].unique()
    else:
        states = sorted(list(set(df_historical['state']) | set(df_preds['state']) | set(df_latest['state'])))
    
    return [{'label': state, 'value': state} for state in states]


@app.callback(
    Output('label_dropdown', 'options'),
    [Input('state_dropdown', 'value'),
     Input('show_outbreaks_toggle', 'value'),
     Input('interval_dropdown', 'value')]  # Add this input
)
def set_item_options(selected_state, toggle_values, selected_interval):
    # Generate df_outbreak dynamically based on the selected interval
    df_outbreak = get_outbreaks(df_preds, df_latest, chosen_interval=selected_interval)
    
    if 'SHOW_OUTBREAKS' in toggle_values and selected_state:
        df_filtered = df_outbreak[(df_outbreak['state'] == selected_state) & (df_outbreak['potential_outbreak'] == True)]
        labels_set = set(df_filtered['label'].unique())
    else:
        labels_set = set()
        if selected_state:
            # Combine unique 'label' values from the filtered DataFrames
            labels_set = set(df_historical[df_historical['state'] == selected_state]['label'].unique()) | \
                         set(df_preds[df_preds['state'] == selected_state]['label'].unique()) | \
                         set(df_latest[df_latest['state'] == selected_state]['label'].unique())

    labels = sorted(list(labels_set))
    return [{'label': i, 'value': i} for i in labels]


@app.callback(
    Output('outbreak_kpi', 'children'),
    [Input('state_dropdown', 'value'),
     Input('label_dropdown', 'value'),
     Input('interval_dropdown', 'value')]  # Add this line
)
def update_kpi(selected_state, selected_label, selected_interval):
    # Ensure the interval is an integer, as it's used directly in get_outbreaks
    #selected_interval = int(selected_interval) if selected_interval else 99  # Default to 95% if none selected

    df_outbreak = get_outbreaks(df_preds, df_latest, chosen_interval=selected_interval)
    current_week = df_latest['date'].max().strftime('%Y-%m-%d')
    num_outbreaks_per_state_and_disease = df_outbreak['potential_outbreak'].sum()
    num_outbreaks_per_disease = len(df_outbreak[df_outbreak['potential_outbreak'] == True]['label'].unique())
    num_states_with_outbreak = len(df_outbreak[df_outbreak['potential_outbreak'] == True]['state'].unique())

    top_state = df_outbreak.groupby(['state'],as_index=False)['potential_outbreak'].sum().sort_values('potential_outbreak',ascending=False).iloc[0]
    # Prepare the KPI display content
    kpi_content = [
        html.H2(f"Current Week: {current_week}"),
        html.H2(f"Outbreak Detection Interval: {selected_interval:.1f}%"),
        html.H3(f"Diseases Tracked: {num_diseases_tracked}"),
        html.H3(f"Potential Outbreaks: {num_outbreaks_per_disease}"),
        html.H3(f"States with Potential Outbreaks: {num_states_with_outbreak}"),
        html.H3(f"State-Specific Potential Outbreaks: {num_outbreaks_per_state_and_disease}")
        #html.H3(f"Most Outbreaks State: {top_state}")
    ]
    
    return kpi_content


@app.callback(
    Output('outbreak_graph', 'figure'),
    [Input('state_dropdown', 'value'),
     Input('label_dropdown', 'value'),
     Input('interval_dropdown', 'value')]  # Add this line
)
def update_graph(selected_state, label_dropdown, selected_interval):
    # Make sure to handle the case where selected_interval might be None
    if selected_state and label_dropdown and selected_interval is not None:
        # Here, adjust your function calls as necessary to include the selected_interval
        df_outbreak = get_outbreaks(df_preds, df_latest, chosen_interval=selected_interval)
        # Now filter df_outbreak further if needed, based on selected_state and label_dropdown
        df_historical_filtered = df_historical[(df_historical['state'] == selected_state) & (df_historical['label'] == label_dropdown)]
        df_latest_filtered = df_outbreak[(df_outbreak['state'] == selected_state) & (df_outbreak['label'] == label_dropdown) & (df_outbreak.new_cases.notna())]
        df_preds_filtered = df_outbreak[(df_outbreak['state'] == selected_state) & (df_outbreak['label'] == label_dropdown)]

        # Assuming plot_outbreak can handle the df_outbreak directly
        fig = plot_outbreak(df_historical_filtered, df_latest_filtered, df_preds_filtered, selected_state, label_dropdown)
        return fig
    return go.Figure()

if __name__ == '__main__':
    #app.run_server(debug=False, host='0.0.0.0', port=8050)
    app.run_server(debug=True, port=8080)
