import dash
from dash import html, dcc
import dash_bootstrap_components as dbc

from src.tabs.outbreak_dropdown import get_dropdown_menu, outbreak_uncertainty_level_explanation

common_div_style = {
    'backgroundColor': 'black', 
    'padding': '10px', 
    'borderRadius': '5px',
    'marginBottom': '20px'  
}



app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY, dbc.icons.BOOTSTRAP])

def summary_tab_layout():

    layout = dbc.Container([

        html.Div([

            html.Div([
                html.H2(
                    "Latest Week Summary of Potential Outbreaks",
                    style={
                        'color': 'white',
                        'textAlign': 'center',
                        'fontSize': '3vw',
                        'marginTop': '40px',
                    }
                )
            ]),

            get_dropdown_menu(
                id_suffix="tab1",
                label_text="Outbreak Model Certainty Level",
                tooltip_text=outbreak_uncertainty_level_explanation,
                id_dropdown="interval_dropdown"
            ),
            #get_dropdown_menu(label_and_info, uncertainty_level_tooltip,'interval_dropdown'),
            html.Div([
                html.Div(id='outbreak_kpi', style={**common_div_style, 'width': '700px','color': 'white', 'textAlign': 'center'}),
                html.Div(id='other_stats_content',
                    style={
                        **common_div_style, 
                        'color': 'white',
                        'fontSize': '26px',
                        'maxWidth': '700px',
                        #'width': '700px',
                        'margin': '0 auto',
                        'display': 'flex',
                        'flexDirection': 'column',
                        'alignItems': 'center'
                        }
                ),
            ], 
            style={ 'display': 'flex', 'flexDirection': 'column', 'alignItems': 'center', 'justifyContent': 'center','paddingBottom':'20px'}
            ),

            html.Div([
                dbc.Row([
                    dbc.Col(
                        html.Div([  
                            dcc.Graph(id='us-map', style={**common_div_style, 'width': '100%', 'display': 'block', 'marginBottom': '0px', 'margin-left': 'auto', 'margin-right': 'auto'}),
                            html.Div(id='territories-table', style={'color': 'white', 'padding': '0px', 'marginTop': '0px'})
                        ], style={**common_div_style}),  
                        width=6
                    ),

                    dbc.Col(
                        html.Div([  
                            dcc.Graph(id='sankey-chart', style={**common_div_style, 'width': '100%', 'display': 'block', 'marginBottom': '0px', 'margin-left': 'auto', 'margin-right': 'auto'}),
                            html.Div(id='ongoing-outbreaks-table', style={'color': 'white', 'padding': '0px', 'marginTop': '0px'})                             
                        ], style={**common_div_style}),  
                        width=6
                    )
                ], align="stretch", style={'color': '#7FDBFF'}),
            ], style={'backgroundColor': 'black'}),

            dbc.Row(
                [
                    dbc.Col(html.Div([
                        html.H2("Potential Outbreak Disease Counts:",
                                style={'color': 'white', 'textAlign': 'center','marginBottom':'0px','paddingTop':'20px','fontSize':'2em'}),
                        html.H4("pathogen, affected bodily system, and transmission type",
                                style={'color': 'white', 'textAlign': 'center','marginBottom':'15px','fontSize':'1.5em'}),
                        html.Div(
                            dcc.RadioItems(
                                id='analysis-toggle',
                                options=[
                                    {'label': ' Count per State and Disease', 'value': 'all'},
                                    {'label': ' Count per Unique Disease Only', 'value': 'unique'}
                                ],
                                value='all',  # Default value
                                labelStyle={'display': 'block'},  # Arrange radio items vertically
                                style={'fontSize': '20px', 'marginBottom': '0px', 'marginTop': '0px', 'textAlign': 'left', 'color': 'white'}
                            ), style={
                                    'width': 'fit-content',
                                    'margin': 'auto',
                                    'backgroundColor': 'black',
                                    'paddingTop': '5px',  # Adjust the top padding
                                    'paddingBottom': '5px',  # Adjust the bottom padding
                                    'paddingRight': '10px',  # Keep the right padding as it was
                                    'paddingLeft': '10px',  # Keep the left padding as it was
                                    'borderRadius': '15px'
                                }),

                    ]), width=12)
                ],
                justify="center",
                style={'marginBottom': '10px'}
                ),
            dbc.Row([
                dbc.Col(dcc.Graph(id='pathogen-chart', style={**common_div_style}), width=4),
                dbc.Col(dcc.Graph(id='bodily-chart', style={**common_div_style}), width=4),
                dbc.Col(dcc.Graph(id='transmission-chart', style={**common_div_style}), width=4),
            ], align="stretch", style={'color': '#7FDBFF'})

        ], style={'color': '#7FDBFF', 'paddingBottom': '20px'})

    ], fluid=True)


    return layout