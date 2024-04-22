import dash
from dash import html, dcc
import dash_bootstrap_components as dbc

from src.tabs.outbreak_dropdown import get_dropdown_menu, outbreak_uncertainty_level_explanation


available_states = ['ALABAMA', 'ALASKA', 'AMERICAN SAMOA', 'ARIZONA', 'ARKANSAS', 'CALIFORNIA', 'COLORADO', 'CONNECTICUT', 'DELAWARE', 'DISTRICT OF COLUMBIA', 
                    'FLORIDA', 'GEORGIA', 'GUAM', 'HAWAII', 'IDAHO', 'ILLINOIS', 'INDIANA', 'IOWA', 'KANSAS', 'KENTUCKY', 'LOUISIANA', 'MAINE', 'MARYLAND', 'MASSACHUSETTS', 
                    'MICHIGAN', 'MINNESOTA', 'MISSISSIPPI', 'MISSOURI', 'MONTANA', 'NEBRASKA', 'NEVADA', 'NEW HAMPSHIRE', 'NEW JERSEY', 'NEW MEXICO', 'NEW YORK', 'NEW YORK CITY', 
                    'NORTH CAROLINA', 'NORTH DAKOTA', 'NORTHERN MARIANA ISLANDS', 'OHIO', 'OKLAHOMA', 'OREGON', 'PENNSYLVANIA', 'PUERTO RICO', 'RHODE ISLAND', 'SOUTH CAROLINA', 
                    'SOUTH DAKOTA', 'TENNESSEE', 'TEXAS', 'U.S. VIRGIN ISLANDS', 'UTAH', 'VERMONT', 'VIRGINIA', 'WASHINGTON', 'WEST VIRGINIA', 'WISCONSIN', 'WYOMING']

common_div_style = {
    'backgroundColor': 'black', 
    'padding': '10px', 
    'borderRadius': '10px',
    'marginBottom': '20px'  
}

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY, dbc.icons.BOOTSTRAP])

def outbreaks_type_counts_tab_layout():

    layout = dbc.Container([

        html.Div([
                html.H2(
                    "Latest Week Potential Outbreaks Profiles",
                    style={
                        'color': 'white',
                        'textAlign': 'center',
                        'fontSize': 'clamp(30px, 8vw, 44px)',
                        'marginTop': '40px',
                    }
                )
            ]),

        html.Div([
            get_dropdown_menu(
                id_suffix="tab4",
                label_text="Outbreak Model Certainty Level",
                tooltip_text=outbreak_uncertainty_level_explanation,
                id_dropdown="interval_dropdown_type"
            ),

            html.Div([  
                dcc.Dropdown(
                    id='state_dropdown_outbreak_type_counts',
                    placeholder='Select State or States', 
                    style={'fontSize': '18px', 'textAlign': 'left', 'fontWeight': 'bold', 'width':'100%'},
                    multi=True, 
                    options=[{'label': state, 'value': state} for state in available_states],
                    className='detail-dropdown',  
                ),

                ], style={
                    'width': '60%',
                    'display': 'flex',  
                    'justifyContent': 'center',  
                    'alignItems': 'center', 
                    'padding': '5px',
                    'border': '1px solid #ccc',
                    'borderRadius': '15px',
                    'margin': '20px auto',  
                    'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'
                }
            ),

            dbc.Row(
                [
                dbc.Col(html.Div([
                    #html.H2("Potential Outbreak Type Counts:",
                    #        style={'color': 'white', 'textAlign': 'center','marginBottom':'0px','paddingTop':'20px','fontSize':'2em'}),
                    html.H3("Pathogen, Affected Bodily System, and Transmission Type",
                            style={'color': 'white', 'textAlign': 'center','marginBottom':'15px','paddingTop':'10px','fontSize':'26px'}),
                    html.Div(
                        dcc.RadioItems(
                            id='analysis-toggle',
                            options=[
                                {'label': ' Count per State and Disease', 'value': 'all'},
                                {'label': ' Count per Unique Disease Only', 'value': 'unique'}
                            ],
                            value='all', 
                            labelStyle={'display': 'block'},  
                            style={'fontSize': '22px', 'marginBottom': '0px', 'marginTop': '0px', 'textAlign': 'left', 'color': 'white'}
                        ), style={
                                'width': 'fit-content',
                                'margin': 'auto',
                                'backgroundColor': 'black',
                                'paddingTop': '5px',  
                                'paddingBottom': '5px',  
                                'paddingRight': '10px',  
                                'paddingLeft': '10px',  
                                'borderRadius': '10px'
                            }),

                    ]), width=12)
                ],
                justify="center",
                style={'marginBottom': '10px'}
                ),
            dbc.Row([
                dbc.Col(dcc.Graph(id='pathogen-chart', style={**common_div_style}), xs=12, lg=4),
                dbc.Col(dcc.Graph(id='bodily-chart', style={**common_div_style}), xs=12, lg=4),
                dbc.Col(dcc.Graph(id='transmission-chart', style={**common_div_style}), xs=12, lg=4),
            ], align="stretch", style={'color': '#7FDBFF'}),

            html.Div(id='outbreak-table', style={'color': 'white', 'padding': '0px','paddingBottom':'20px', 'marginTop': '0px'})

        ]),
    
    ],fluid=True)

    return layout
