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
    'padding': '0px', 
    'borderRadius': '5px',
    'marginBottom': '20px'  
}

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY, dbc.icons.BOOTSTRAP])

def outbreaks_type_counts_tab_layout():

    layout = dbc.Container([

        html.Div([
                html.H2(
                    "Latest Week Potential Outbreaks Profile",
                    style={
                        'color': 'white',
                        'textAlign': 'center',
                        'font-size': '3vw',
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
            #get_dropdown_menu(label_and_info, uncertainty_level_tooltip,'interval_dropdown_outbreak'),

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
                    'justifyContent': 'center',  # Centers the dropdown horizontally
                    'alignItems': 'center',  # Align items vertically, not needed here but useful for other layouts
                    'padding': '5px',
                    'border': '1px solid #ccc',
                    'borderRadius': '15px',
                    'margin': '20px auto',  # Auto margin for horizontal centering, and 20px vertical margin
                    'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'
                }
            ),

            dbc.Row(
                [
                dbc.Col(html.Div([
                    #html.H2("Potential Outbreak Type Counts:",
                    #        style={'color': 'white', 'textAlign': 'center','marginBottom':'0px','paddingTop':'20px','fontSize':'2em'}),
                    html.H3("Pathogen, Affected bodily system, and Transmission Type",
                            style={'color': 'white', 'textAlign': 'center','marginBottom':'15px','paddingTop':'20px','fontSize':'1.75em'}),
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


        ]),
    
    ],fluid=True)

    return layout
