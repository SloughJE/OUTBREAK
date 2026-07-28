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

SUMMARY_FILTER_ROW_STYLE = {
    "height": "44px",
    "minHeight": "44px",
    "marginBottom": "4px"
}

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY, dbc.icons.BOOTSTRAP])

def summary_tab_layout():

    layout = dbc.Container([

        dcc.Store(
            id="selected-summary-state-code",
            data=None,
            storage_type="memory"
        ),

        html.Div([

            html.Div([
                html.H2(
                    "Latest Week Potential Outbreak Signals", className='tab-title-long',
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

                            html.Div(
                                style=SUMMARY_FILTER_ROW_STYLE
                            ),

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

                            html.Div(
                                id="territories-table",
                                style={
                                    "color": "white",
                                    "padding": "0px",
                                    "marginTop": "14px"
                                }
                            )

                        ], style={**common_div_style}),
                        xs=12,
                        lg=6
                    ),

                    dbc.Col(
                        html.Div(
                            [
                                # --------------------------------------------------
                                # Selected-state label and reset button
                                # --------------------------------------------------
                                html.Div(
                                    [
                                        html.Span(
                                            id="summary-state-filter-label",
                                            children=(
                                                "Showing: All states — click a state "
                                                "on the map to filter"
                                            ),
                                            style={
                                                "color": "#D0D0D0",
                                                "fontSize": "20px",
                                                "fontWeight": "bold"
                                            }
                                        ),

                                    dbc.Button(
                                        "Reset to all states",
                                        id="reset-summary-state-button",
                                        n_clicks=0,
                                        color="light",
                                        size="sm",
                                        style={
                                            "display": "none",
                                            "marginLeft": "12px",
                                            "backgroundColor": "#3A3A3A",
                                            "border": "1px solid #BFBFBF",
                                            "color": "white",
                                            "fontWeight": "600",
                                            "fontSize": "14px",
                                            "padding": "4px 10px",
                                            "borderRadius": "6px"
                                        }
                                    )
                                    ],
                                    style={
                                        **SUMMARY_FILTER_ROW_STYLE,
                                        "display": "flex",
                                        "justifyContent": "center",
                                        "alignItems": "center",
                                        "textAlign": "center",
                                        "whiteSpace": "nowrap"
                                    }
                                ),

                                # --------------------------------------------------
                                # Transition chart and latest-week table
                                # --------------------------------------------------
                                html.Div(
                                    [
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

                                        html.Div(
                                            id="ongoing-outbreaks-table",
                                            style={
                                                "color": "white",
                                                "padding": "0px",
                                                "marginTop": "14px"
                                            }
                                        )
                                    ],
                                    style={
                                        **common_div_style
                                    }
                                )
                            ]
                        ),
                        xs=12,
                        lg=6
                    )
                ], align="stretch", style={'color': '#7FDBFF','borderRadius': '10px'}),
            ], style={'backgroundColor': 'black','borderRadius': '10px'}),

         ], style={'color': '#7FDBFF', 'paddingBottom': '20px','borderRadius': '10px'})

    ], fluid=True)


    return layout

