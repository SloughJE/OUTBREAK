import dash
from dash import html, dcc
import dash_bootstrap_components as dbc

import dash
from dash import html, dcc
import dash_bootstrap_components as dbc

outbreak_uncertainty_level_explanation = """• Indicates how certain we want to be in identifying a "potential outbreak"
• Corresponds to the model prediction interval
• The model forecasts by predicting distributions of values for the future time period, reflecting the probable range of outcome values.
• If the actual value for the current week is greater than the upper prediction interval value from last week's prediction, we label it as an "outbreak".
• A higher "Outbreak Model Certainty Level" yields a higher threshold value, and is therefore less like to identify a new value as an "outbreak".
• In other words, a higher "Outbreak Model Certainty Level" means if the model identifies a value as an "outhreak", we are more confident that it is actually an outbreak.
• Example: 99% means we use the 99th percentile of the predicted distribution values as the threshold for identifying an "outbreak".

- Model accuracy is contingent upon the quality and completeness of the training data. Sparse or missing data for specific time series may adversely affect predictions and identification of "outbreaks".
- Please note, the designation of values as "outbreaks" is solely for the purpose of entertainment and does not carry any official public health significance. It is a predictive tool intended for informational use only and should not be construed as medical or health advice.
"""


def get_tooltip_with_icon(id_suffix, tooltip_text):
    """
    Creates a tooltip with an associated information icon.
    
    Parameters:
    - id_suffix (str): A unique suffix to ensure the tooltip and icon have unique IDs.
    - tooltip_text (str): The text to display in the tooltip.
    
    Returns:
    - A tuple containing the info icon and the tooltip components.
    """
    info_icon_id = f"outbreak-uncertainty-tooltip-target-{id_suffix}"
    info_icon = html.I(className="bi bi-info-circle", id=info_icon_id, 
                       style={'cursor': 'pointer', 'fontSize': '22px', 'marginLeft': '10px', 'textAlign': 'left',})
    
    tooltip = dbc.Tooltip(tooltip_text, target=info_icon_id, placement="right", className='custom-tooltip',    
                           style={'white-space': 'pre-line'})
    
    return info_icon, tooltip

def get_dropdown_menu(id_suffix, label_text, tooltip_text, id_dropdown):
    """
    Creates a dropdown menu with a label, an info icon, and a tooltip.
    
    Parameters:
    - id_suffix (str): A unique suffix to ensure IDs are unique.
    - label_text (str): The text for the label.
    - tooltip_text (str): The text for the tooltip.
    - id_dropdown (str): The ID for the dropdown component.
    
    Returns:
    - A Dash component representing the dropdown menu.
    """
    info_icon, tooltip = get_tooltip_with_icon(id_suffix, tooltip_text)
    
    label_and_info = html.H2([info_icon, f" {label_text}:"], style={
        'color': 'white', 'textAlign': 'center', 'fontSize': '24px', 'marginRight': '0px', 'marginBottom': '3px',
    })
    
    return dbc.Row([
        dbc.Col(
            html.Div(
                [
                    html.Div([
                        html.Div([
                            label_and_info, 
                            tooltip,  
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
                                    ], value=99,  
                                clearable=False,
                                className='dropdown-input',
                            ),
                            style={'display': 'inline-block', 'width': '150px', 'fontSize': '24px', 'textAlign': 'left', 'fontWeight': 'bold','marginRight': '5px','paddingRight':'0px'},  
                        ),
                    ], style={
                        'display': 'inline-flex', 'alignItems': 'center', 'justifyContent': 'center', 
                        'border': '1px solid #ccc', 'borderRadius': '15px', 'marginRight': '0px',
                        'paddingTop': '7px','paddingBottom': '7px','paddingRight':'0px','paddingLeft':'40px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'
                    }),
                ],
                style={'textAlign': 'left', 'color': 'white', 'fontSize': '24px', 'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center', 'height': '100px'}
            ),
            width={'size': 12},
        )
    ], style={'margin': '20px auto', 'width': 'fit-content', 'justifyContent': 'center', 'display': 'block'})

# Example usage:
# You would call get_dropdown_menu with a unique id_suffix for each tab or place where you're using it.


"""
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
                            'border': '1px solid #ccc', 'borderRadius': '15px', 'marginRight': '0px',
                            'paddingTop': '7px','paddingBottom': '7px','paddingRight':'0px','paddingLeft':'40px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'
                        }),
                    ],
                    style={'textAlign': 'left', 'color': 'white', 'fontSize': '24px', 'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center', 'height': '100px'}
                ),
                width={'size': 12},
            )
        ], style={'margin': '20px auto', 'width': 'fit-content', 'justifyContent': 'center', 'display': 'block'})
"""