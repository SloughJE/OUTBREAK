import dash
from dash import html, dcc
import dash_bootstrap_components as dbc


def get_dropdown_menu(label_and_info, uncertainty_level_tooltip,id_dropdown):
    return dbc.Row([
            dbc.Col(
                html.Div(
                    [
                        html.Div([
                            html.Div([
                                label_and_info, 
                                uncertainty_level_tooltip,  
                            ], style={'display': 'inline-block', 'marginRight': '5px', 'verticalAlign': 'middle'}),
                            html.Div(
                                dcc.Dropdown(
                                    id=id_dropdown,
                                    options=[
                                        {'label': '80%', 'value': 80},
                                        {'label': '90%', 'value': 90},
                                        {'label': '95%', 'value': 95},
                                        {'label': '97%', 'value': 97},
                                        {'label': '99%', 'value': 99},
                                        {'label': '99.9%', 'value': 99.9},
                                    ],
                                    value=99,  
                                    clearable=False,
                                    className='dropdown-input',
                                ),
                                style={'display': 'inline-block', 'width': '150px', 'fontSize': '24px', 'textAlign': 'left', 'fontWeight': 'bold','marginRight': '5px','paddingRight':'0px'},  
                            ),
                        ], style={
                            'display': 'inline-flex', 'alignItems': 'center', 'justifyContent': 'center', 
                            'border': '1px solid #ccc', 'border-radius': '15px', 'marginRight': '0px',
                            'paddingTop': '7px','paddingBottom': '7px','paddingRight':'0px','paddingLeft':'40px', 'box-shadow': '0 2px 4px rgba(0,0,0,0.1)'
                        }),
                    ],
                    style={'textAlign': 'left', 'color': 'white', 'fontSize': '24px', 'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center', 'height': '100px'}
                ),
                width={'size': 12},
            )
        ], style={'margin': '20px auto', 'width': 'fit-content', 'justifyContent': 'center', 'display': 'block'})
