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

def outbreaks_history_tab_layout():

    layout = dbc.Container([

        html.Div([
                html.H2(
                    "Potential Outbreaks History", className='tab-title-long',
                    style={
                        'color': 'white',
                        'textAlign': 'center',
                        'fontSize': '44px',
                        'marginTop': '40px',
                    }
                )
            ]),

        html.Div([
            get_dropdown_menu(
                id_suffix="tab3",
                label_text="Outbreak Model Certainty Level",
                tooltip_text=outbreak_uncertainty_level_explanation,
                id_dropdown="interval_dropdown_outbreak"
            ),
            #get_dropdown_menu(label_and_info, uncertainty_level_tooltip,'interval_dropdown_outbreak'),

            html.Div([  
                dcc.Dropdown(
                    id='state_dropdown_outbreak_history',
                    placeholder='Select State or States', 
                    style={'fontSize': '18px', 'textAlign': 'left', 'fontWeight': 'bold','width':'100%'},
                    multi=True, 
                    options=[{'label': state, 'value': state} for state in available_states],
                    className='detail-dropdown',  
                ),
            #    dcc.Dropdown(
            #        id='label_dropdown',
            #        placeholder='Select Disease',  # Set the placeholder text
            #        style={'fontSize': '18px', 'textAlign': 'left', 'fontWeight': 'bold'},
            #        className='detail-dropdown',  # Use this class for further CSS customizations
            #    ), 
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


            dcc.Graph(id='outbreak_history_potential_resolved',style={**common_div_style,'padding': '20px'}),

            dcc.Checklist(
                id='show_cumulative_toggle',
                options=[
                    {'label': ' Show Cumulative Counts', 'value': 'cumulative'},
                ],
                value=[],
                labelStyle={'display': 'block', 'color': 'white', 'fontSize': 22},  
                style={'textAlign': 'center', 'marginBottom': '20px'}
            ),
            dcc.Graph(id='outbreak_history_ongoing',style={**common_div_style,'padding': '20px'}),
    


        ]),
    
    ],fluid=True)

    return layout
