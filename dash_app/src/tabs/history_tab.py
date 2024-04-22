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

def details_tab_layout():

    layout = dbc.Container([

        html.Div([
                html.H2(
                    "Disease History with Latest Week Potential Outbreak",
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
                id_suffix="tab2",
                label_text="Outbreak Model Certainty Level",
                tooltip_text=outbreak_uncertainty_level_explanation,
                id_dropdown="interval_dropdown_detail"
            ),
            #get_dropdown_menu(label_and_info, uncertainty_level_tooltip,'interval_dropdown_detail'),

            dcc.Checklist(
                id='show_outbreaks_toggle',
                options=[
                    {'label': ' Show Outbreaks Only', 'value': 'SHOW_OUTBREAKS'},
                ],
                value=[],
                labelStyle={'display': 'block', 'color': 'white', 'fontSize': 22},  
                style={'textAlign': 'center', 'marginBottom': '20px'}
            ),
            html.Div([  
                dcc.Dropdown(
                    id='state_dropdown',
                    placeholder='Select a State',  
                    style={'fontSize': '18px', 'textAlign': 'left', 'fontWeight': 'bold', 'width':'100%'},
                    className='detail-dropdown', 
                ),
                dcc.Dropdown(
                    id='label_dropdown',
                    placeholder='Select a Disease',  
                    style={'fontSize': '18px', 'textAlign': 'left', 'fontWeight': 'bold', 'width':'100%'},
                    className='detail-dropdown',  
                ), 
                ], style={
                    'width': '80%',
                    #'display': 'flex',  
                    'justifyContent': 'center',  # Centers the dropdown horizontally
                    'alignItems': 'center',  # Align items vertically, not needed here but useful for other layouts
                    'padding': '5px',
                    'border': '1px solid #ccc',
                    'borderRadius': '15px',
                    'margin': '20px auto',  # Auto margin for horizontal centering, and 20px vertical margin
                    'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'
                }
                ),
            dcc.Graph(id='outbreak_graph',style={**common_div_style}),
            

        ]),
        html.Div(id='disease_info_display',
                     style={**common_div_style,'padding': '20px'}),
    ],fluid=True)

    return layout
