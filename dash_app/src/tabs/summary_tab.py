import dash
from dash import html, dcc
import dash_bootstrap_components as dbc

from src.tabs.outbreak_dropdown import get_dropdown_menu, outbreak_uncertainty_level_explanation

common_div_style = {
    'backgroundColor': 'black', 
    'padding': '10px', 
    'borderRadius': '10px',
    'marginBottom': '20px'  
}

SUMMARY_GRAPH_HEIGHT = "720px"

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY, dbc.icons.BOOTSTRAP])

def summary_tab_layout():

    layout = dbc.Container([

        html.Div([

            html.Div([
                html.H2(
                    "Latest Week Summary of Potential Outbreaks", className='tab-title-long',
                    style={
                        'color': 'white',
                        'textAlign': 'center',
                        'fontSize': '44px',
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
         
            html.Div([
                html.Div(id='outbreak_kpi', style={'justifyContent': 'center','display': 'flex', 'flexDirection': 'column', 
                                                   'alignItems': 'center', 'paddingTop': '19px','paddingBottom': '15px','paddingLeft': '40px','paddingRight': '40px',
                                                   'borderRadius': '10px', 'color': 'white', 'backgroundColor': 'black'}),

                html.Div([
                    dbc.Row([
                        dbc.Col(html.Div(id='left_column_metrics', className='responsive-text', style={**common_div_style}), 
                                xs=12,  
                                lg=6),  
                        dbc.Col(html.Div(id='right_column_metrics', className='responsive-text', style={**common_div_style}),
                                xs=12,  
                                lg=6), 
                    ], align="stretch", style={'color': 'white', 'backgroundColor': 'black','borderRadius': '10px'})
                ], style={
                    'color': 'white',
                    'margin': '20px 0 0',
                    'display': 'flex',
                    'flexDirection': 'column',
                    'alignItems': 'center', 'padding': '0 10px','borderRadius': '10px',
                }),

            ], 
            style={ 'display': 'flex', 'flexDirection': 'column', 'alignItems': 'center', 'justifyContent': 'center','paddingBottom':'20px','borderRadius': '10px'}
            ),

            html.Div([
                dbc.Row([
                    dbc.Col(
                        html.Div([  
                            dcc.Graph(
                                id="us-map",
                                style={
                                    **common_div_style,
                                    "width": "100%",
                                    "height": SUMMARY_GRAPH_HEIGHT,
                                    "display": "block",
                                    "marginBottom": "6px",
                                    "marginLeft": "auto",
                                    "marginRight": "auto"
                                },
                                config={
                                    "responsive": True
                                }
                            ),                            
                            html.Div(id='territories-table', style={'color': 'white', 'padding': '0px', 'marginTop': '14px'})
                        ], style={**common_div_style}),  
                        xs=12, lg=6
                    ),

                    dbc.Col(
                        html.Div([  
                            dcc.Graph(
                                id="sankey-chart",
                                style={
                                    **common_div_style,
                                    "width": "100%",
                                    "height": SUMMARY_GRAPH_HEIGHT,
                                    "display": "block",
                                    "marginBottom": "6px",
                                    "marginLeft": "auto",
                                    "marginRight": "auto"
                                },
                                config={
                                    "responsive": True
                                }
                            ),                            
                            html.Div(id='ongoing-outbreaks-table', style={'color': 'white', 'padding': '0px', 'marginTop': '14px'})                             
                        ], style={**common_div_style}),  
                        xs=12, lg=6
                    )
                ], align="stretch", style={'color': '#7FDBFF','borderRadius': '10px'}),
            ], style={'backgroundColor': 'black','borderRadius': '10px'}),

         ], style={'color': '#7FDBFF', 'paddingBottom': '20px','borderRadius': '10px'})

    ], fluid=True)


    return layout

