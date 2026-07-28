import dash
from dash import dcc, html, ctx, dash_table
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
import dash_bootstrap_components as dbc
import pandas as pd

from src.tabs.history_tab_helper import (
    plot_outbreak,
    summarize_history_period,
    get_flagged_episodes
)
from src.tabs.summary_tab_helper import (
    get_outbreaks,
    create_us_map,
    is_outbreak_resolved,
    create_sankey_chart,
    get_outbreaks_all,
    state_code_mapping
)
from src.tabs.load_data import load_preds
from src.tabs.summary_tab import summary_tab_layout
from src.tabs.history_tab import details_tab_layout 
from src.tabs.disease_info import disease_groups, disease_details
from src.tabs.outbreaks_history_tab import outbreaks_history_tab_layout
from src.tabs.outbreaks_history_tab_helper import (
    agg_outbreak_counts,
    plot_time_series,
    agg_new_episode_counts,
    plot_new_episode_trends,
    filter_weekly_display_period
)
from src.tabs.info_tab import info_view_tab_layout


app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY, dbc.icons.BOOTSTRAP])
server = app.server # Expose the Flask server for Gunicorn

app.title = "Outbreak Dashboard"

###################################################

NEW_SIGNAL_COLOR = "#FF7A00"
ONGOING_SIGNAL_COLOR = "#C6283D"


# Jurisdictions intentionally excluded from map-click filtering.
# The initial implementation supports the 50 states plus DC only.
SUMMARY_MAP_EXCLUDED_CODES = {
    "PR",
    "GU",
    "VI",
    "AS",
    "MP",
    "NYC"
}


STATE_NAME_BY_CODE = {
    code: state_name
    for state_name, code in state_code_mapping.items()
    if code not in SUMMARY_MAP_EXCLUDED_CODES
}


def format_summary_state_name(state_name):
    """
    Convert uppercase source names to readable display names.
    """
    if not state_name:
        return "United States"

    return (
        str(state_name)
        .title()
        .replace(" Of ", " of ")
    )


cols_wanted = ['item_id', 'state', 'date', 'label', 'new_cases']
date_filter_hist = [('date', '>=', pd.to_datetime('2024-01-01'))]
date_filter_preds = [('date', '>=', pd.to_datetime('2024-01-01'))]

df_historical = pd.read_parquet("data/df_historical.parquet", columns=cols_wanted, filters=date_filter_hist)
df_preds_all =  pd.read_parquet("data/df_predictions.parquet", filters=date_filter_preds)

df_historical['date'] = pd.to_datetime(df_historical.date.dt.date)
max_hist = df_historical.date.max()
df_preds_all = pd.merge(df_historical,df_preds_all,on=['item_id','date'], how='inner')

df_latest = df_historical[df_historical.date==max_hist].copy()
df_historical = df_historical[df_historical.date<max_hist]

df_preds_all['date'] = pd.to_datetime(df_preds_all.date.dt.date)

min_date_preds = df_preds_all.date.min()
df_preds = df_preds_all[df_preds_all.date==df_preds_all.date.max()].copy()

#df_preds_all['label'] = df_preds_all['item_id'].str.split('_').str[1]
#df_preds_all['state'] = df_preds_all['item_id'].str.split('_').str[0]
#df_preds_all = df_preds_all.fillna(0)
available_states = list(sorted(df_historical.state.unique()))

num_diseases_tracked = len(df_latest['label'].unique())

df_latest['state'] = df_latest['item_id'].str.split('_').str[0]
df_preds['state'] = df_preds['item_id'].str.split('_').str[0]
df_preds['label'] = df_preds['item_id'].str.split('_').str[1]

df_historical = df_historical.sort_values(['date', 'item_id'])
df_preds = df_preds.sort_values(['date', 'item_id'])
df_preds_all = df_preds_all.sort_values(['date', 'item_id'])

df_latest = df_latest.sort_values(['date', 'item_id'])


#######################################################
# add G analytics tracking
GA_MEASUREMENT_ID = 'G-FCN8R7FYVK'

# Modify the index_string to include Google Analytics script and required placeholders
app.index_string = f"""
<!DOCTYPE html>
<html>
    <head>
        <meta charset="UTF-8">
        <title>Outbreak!</title>
        <!-- Google Analytics -->
        <script async src="https://www.googletagmanager.com/gtag/js?id={GA_MEASUREMENT_ID}"></script>
        <script>
            window.dataLayer = window.dataLayer || [];
            function gtag(){{dataLayer.push(arguments);}}
            gtag('js', new Date());
            gtag('config', '{GA_MEASUREMENT_ID}');
        </script>
        <!-- End Google Analytics -->
        {{%metas%}}
        {{%favicon%}}
        {{%css%}}
    </head>
    <body>
        <div id="react-entry-point">
            {{%app_entry%}}
        </div>
        <footer>
            {{%config%}}
            {{%scripts%}}
            {{%renderer%}}
        </footer>
    </body>
</html>
"""

app.layout = html.Div([
    dcc.Store(id='shared-dropdown-value'),

    html.Div([
        html.Div(children=[
            html.H1("OUTBREAK!", style={
                'color': 'black',
                'fontSize': 'clamp(56px, 8vw, 100px)',
                'textAlign': 'center',
                'marginTop': '20px',
                'textShadow': '''
                0 0 5px #B22222,
                0 0 10px #B22222,
                0 0 15px #B22222,
                0 0 20px #B22222,
                0 0 25px #B22222,
                0 0 30px #B22222''',
                'fontWeight': 'bold',
                'backgroundColor': 'black',
                'display': 'inline-block',
                'padding': '10px',
                'borderRadius': '50px'
            }),
        ], style={'textAlign': 'center', 'width': '100%', 'marginTop': '0px', 'backgroundColor': 'black'}),
        html.Div("Automatic Weekly Identification of Potential Outbreak Signals for CDC Nationally Notifiable Diseases", className='main-subtitle',
                 style={'justifyContent': 'center', 'color': 'white',
                        'fontSize': '26px', 'color': '#F08080',
                        'alignItems': 'center', 'textAlign': 'center', 'paddingBottom': '20px',
                        'backgroundColor': 'black'}),

        dcc.Tabs(id="tabs", value='tab-1', className='tab-container', children=[
            dcc.Tab(label='Latest Week', value='tab-1', className='custom-tab', selected_className='custom-tab-active', children=summary_tab_layout()),
            dcc.Tab(label='Disease Explorer', value='tab-2', className='custom-tab', selected_className='custom-tab-active', children=details_tab_layout()),
            dcc.Tab(label='Outbreak Trends', value='tab-3', className='custom-tab', selected_className='custom-tab-active', children=outbreaks_history_tab_layout()),
            dcc.Tab(label='About', value='tab-5', className='custom-tab', selected_className='custom-tab-active', children=info_view_tab_layout()),
        ], style={'position': 'sticky', 'top': '0', 'zIndex': '1000', 'width': '100%', 'display': 'block'}),
    ], className='full-width')

], style={'width': '100%'})


##############################
##### CALLBACKS###############
##############################

@app.callback(
    Output(
        "selected-summary-state-code",
        "data"
    ),
    Input(
        "us-map",
        "clickData"
    ),
    Input(
        "reset-summary-state-button",
        "n_clicks"
    ),
    State(
        "selected-summary-state-code",
        "data"
    ),
    prevent_initial_call=True
)
def update_selected_summary_state(
    map_click_data,
    reset_clicks,
    current_state_code
):
    """
    Save the clicked map state in dcc.Store.

    The reset button clears the selection. Territory and NYC
    codes are intentionally ignored for this initial version.
    """
    trigger_id = ctx.triggered_id

    if trigger_id == "reset-summary-state-button":
        return None

    if trigger_id == "us-map" and map_click_data:
        points = map_click_data.get(
            "points",
            []
        )

        if points:
            clicked_code = points[0].get(
                "location"
            )

            if clicked_code in STATE_NAME_BY_CODE:
                return clicked_code

    # Preserve the current selection for invalid or empty clicks.
    return current_state_code

@app.callback(
    Output(
        "summary-state-filter-label",
        "children"
    ),
    Output(
        "reset-summary-state-button",
        "style"
    ),
    Input(
        "selected-summary-state-code",
        "data"
    )
)
def update_summary_state_filter_controls(
    selected_state_code
):
    reset_button_base_style = {
        "marginLeft": "12px"
    }

    selected_state_name = STATE_NAME_BY_CODE.get(
        selected_state_code
    )

    if not selected_state_name:
        return (
            (
                "Showing: All states — click a state "
                "on the map to filter"
            ),
            {
                **reset_button_base_style,
                "display": "none"
            }
        )

    display_name = format_summary_state_name(
        selected_state_name
    )

    return (
        f"Showing: {display_name}",
        {
            **reset_button_base_style,
            "display": "inline-block"
        }
    )


@app.callback(
    Output('state_dropdown', 'options'),
    [Input('show_outbreaks_toggle', 'value'),
     Input('interval_dropdown_detail', 'value')]  
)
def update_state_options(toggle_values, selected_interval):

    df_outbreak = get_outbreaks(df_preds, chosen_interval=selected_interval)
    
    if 'SHOW_OUTBREAKS' in toggle_values:
        states = df_outbreak[df_outbreak['potential_outbreak'] == True]['state'].unique()
    else:
        states = sorted(list(set(df_historical['state']) | set(df_preds['state']) | set(df_latest['state'])))
    
    return [{'label': state, 'value': state} for state in states]


@app.callback(
    Output('label_dropdown', 'options'),
    [Input('state_dropdown', 'value'),
     Input('show_outbreaks_toggle', 'value'),
     Input('interval_dropdown_detail', 'value')]  
)
def set_item_options(selected_state, toggle_values, selected_interval):

    df_outbreak = get_outbreaks(df_preds, chosen_interval=selected_interval)

    if 'SHOW_OUTBREAKS' in toggle_values and selected_state:
        df_filtered = df_outbreak[(df_outbreak['state'] == selected_state) & (df_outbreak['potential_outbreak'] == True)]
        labels_set = set(df_filtered['label'].unique())
    else:
        labels_set = set()
        if selected_state:

            labels_set = set(df_historical[df_historical['state'] == selected_state]['label'].unique()) | \
                         set(df_preds[df_preds['state'] == selected_state]['label'].unique()) | \
                         set(df_latest[df_latest['state'] == selected_state]['label'].unique())

    labels = sorted(list(labels_set))
    return [{'label': i, 'value': i} for i in labels]


@app.callback(
    [
        Output("outbreak_kpi", "children"),
        Output("left_column_metrics", "children"),
        Output("right_column_metrics", "children"),
        Output("us-map", "figure"),
        Output("territories-table", "children"),
        Output("sankey-chart", "figure"),
        Output("ongoing-outbreaks-table", "children"),
    ],
    [
        Input(
            "interval_dropdown",
            "value"
        ),
        Input(
            "selected-summary-state-code",
            "data"
        ),
    ]
)
def update_kpi(
    selected_interval,
    selected_summary_state_code
):
    
    df_outbreak = get_outbreaks(df_preds, chosen_interval=selected_interval)

    current_week = df_latest['date'].max().strftime('%Y-%m-%d')
    num_outbreaks_per_state_and_disease = df_outbreak['potential_outbreak'].sum()
    num_outbreaks_per_disease = len(df_outbreak[df_outbreak['potential_outbreak'] == True]['label'].unique())
    num_states_with_outbreak = len(df_outbreak[df_outbreak['potential_outbreak'] == True]['state'].unique())

    #top_state = df_outbreak.groupby(['state'],as_index=False)['potential_outbreak'].sum().sort_values('potential_outbreak',ascending=False).iloc[0]
    
    df_outbreak = is_outbreak_resolved(df_outbreak)
    map_content, df_territories = create_us_map(df_outbreak)

    territory_columns = [
        "US Territory / City",
        "Potential Outbreaks"
    ]

    territory_records = df_territories.to_dict(
        "records"
    )

    territory_tooltip_data = [
        {
            column: {
                "value": row["_tooltip"],
                "type": "markdown"
            }
            for column in territory_columns
        }
        for row in territory_records
    ]

    table_content = html.Div([
            html.H3("US Territories Potential Outbreaks", style={'textAlign': 'center', 'color': 'white','fontSize':'22px'}),
            dash_table.DataTable(
                columns=[
                    {"name": column, "id": column}
                    for column in territory_columns
                ],

                data=df_territories[
                    territory_columns
                ].to_dict("records"),

                tooltip_data=territory_tooltip_data,

                tooltip_delay=150,

                # Keep the tooltip visible for as long as
                # the user remains over the cell.
                tooltip_duration=None,

                css=[
                    {
                        "selector": ".dash-table-tooltip",
                        "rule": """
                            background-color: #222222;
                            color: white;
                            border: 1px solid #777777;
                            border-radius: 4px;
                            max-width: 420px;
                            white-space: normal;
                            overflow-wrap: anywhere;
                            font-family: Arial, sans-serif;
                            font-size: 14px;
                            text-align: left;
                            padding: 10px;
                        """
                    }
                ],
                style_as_list_view=True,
                style_header={'backgroundColor': 'rgb(50, 50, 50)', 'color': 'white','fontWeight':'bold','border':'1px solid white',
                              'whiteSpace': 'normal','height':'3em'},
                style_cell={'backgroundColor': 'rgb(0, 0, 0)', 'color': 'white','border':'1px solid grey',
                    'whiteSpace': 'normal',
                    'height': 'auto'},
                style_table={
                    'maxHeight': '300px',  
                    'overflowY': 'auto',  
                    'width': '75%',  
                    'margin': '0 auto',  
                    'padding': '0px',
                    'marginTop': '0px',
                    'overflowX': 'auto', 
                },
                style_header_conditional=[
                    {
                        'if': {'column_id': 'Potential Outbreaks'},  
                        'paddingRight': '5px'  
                    }
                ],
                style_data_conditional=[
                    {
                        'if': {'column_id': 'Potential Outbreaks'},  
                        'paddingRight': '5px'  
                    },
                    {
                        'if': {
                                'filter_query': '{Potential Outbreaks} > 0 && {Potential Outbreaks} <= 2',
                            },
                            'backgroundColor': 'rgba(254, 224, 210, 0.6)', 
                            'color': 'white',
                        },
                    {
                        'if': {
                            'filter_query': '{Potential Outbreaks} > 2 && {Potential Outbreaks} <= 5',
                        },
                        'backgroundColor': 'rgba(252, 146, 114, 0.6)',
                        'color': 'white',
                    },
                    {
                        'if': {
                            'filter_query': '{Potential Outbreaks} > 5 && {Potential Outbreaks} <= 7',
                        },
                        'backgroundColor': 'rgba(251, 106, 74, 0.6)',
                        'color': 'white',
                    },
                    {
                        'if': {
                            'filter_query': '{Potential Outbreaks} > 7 && {Potential Outbreaks} <= 12',
                        },
                        'backgroundColor': 'rgba(222, 45, 38, 0.6)',
                        'color': 'white',  
                    },
                    {
                        'if': {
                            'filter_query': '{Potential Outbreaks} > 12',
                        },
                        'backgroundColor': 'rgba(165, 15, 21, 0.6)', 
                        'color': 'white',
                    }
                ]
            )
        ], style={'marginBottom': '20px'})


    df_outbreak_all = get_outbreaks_all(
        df_preds_all,
        selected_interval
    )


    # --------------------------------------------------
    # National ongoing signals for the top KPI cards
    # --------------------------------------------------
    # These remain national even when the transition
    # chart and latest-week table are filtered by state.

    if df_outbreak_all.empty:
        ongoing_outbreaks = df_outbreak_all.copy()

    else:
        national_data = df_outbreak_all.copy()

        national_data["date"] = pd.to_datetime(
            national_data["date"],
            errors="coerce"
        )

        national_data = national_data.dropna(
            subset=["date"]
        )

        if national_data.empty:
            ongoing_outbreaks = national_data.copy()

        else:
            latest_reporting_date = national_data["date"].max()

            national_latest_week = national_data.loc[
                national_data["date"].eq(
                    latest_reporting_date
                )
            ].copy()

            current_flags = (
                national_latest_week[
                    "potential_outbreak"
                ]
                .fillna(False)
                .astype(bool)
            )

            previous_week_flags = (
                national_latest_week[
                    "potential_outbreak_past_week"
                ]
                .fillna(False)
                .astype(bool)
            )

            ongoing_outbreaks = national_latest_week.loc[
                current_flags & previous_week_flags
            ].copy()


    # --------------------------------------------------
    # Selected-state transition chart and table
    # --------------------------------------------------

    selected_state_name = STATE_NAME_BY_CODE.get(
        selected_summary_state_code
    )

    scope_label = format_summary_state_name(
        selected_state_name
    )

    sankey_chart, latest_week_signals, _ = (
        create_sankey_chart(
            df_outbreak_all,
            selected_state=selected_state_name,
            scope_label=scope_label
        )
    )

    if selected_state_name:
        table_title = (
            "Latest-Week Potential-Outbreak Signals"
            f" — {scope_label}"
        )
    else:
        table_title = (
            "Latest-Week Potential-Outbreak Signals"
        )
    
    if latest_week_signals.empty:
        table_content_ongoing_outbreaks = html.Div(
            [
                html.H3(
                    table_title,
                    style={
                        "textAlign": "center",
                        "color": "white",
                        "fontSize": "22px"
                    }
                ),

                html.Div(
                    (
                        "No latest-week potential-outbreak "
                        f"signals were identified for "
                        f"{scope_label}."
                    ),
                    style={
                        "color": "#C8C8C8",
                        "textAlign": "center",
                        "padding": "24px",
                        "fontSize": "15px"
                    }
                )
            ],
            style={
                "marginBottom": "20px"
            }
        )

    else:
        table_content_ongoing_outbreaks = html.Div(
            [
                html.H3(
                    table_title,
                    style={
                        "textAlign": "center",
                        "color": "white",
                        "fontSize": "22px"
                    }
                ),

                dash_table.DataTable(
                    columns=[
                        {
                            "name": column,
                            "id": column
                        }
                        for column in (
                            latest_week_signals.columns
                        )
                    ],

                    data=latest_week_signals.to_dict(
                        "records"
                    ),

                    sort_action="native",
                    style_as_list_view=True,

                    style_header={
                        "backgroundColor": (
                            "rgb(50, 50, 50)"
                        ),
                        "color": "white",
                        "fontWeight": "bold",
                        "border": "1px solid white",
                        "whiteSpace": "normal",
                        "height": "3em"
                    },

                    style_cell={
                        "backgroundColor": "black",
                        "color": "white",
                        "border": "1px solid grey",
                        "whiteSpace": "normal",
                        "height": "auto",
                        "padding": "8px"
                    },

                    style_cell_conditional=[
                        {
                            "if": {
                                "column_id":
                                    "US State / Territory"
                            },
                            "width": "20%"
                        },
                        {
                            "if": {
                                "column_id": "Disease"
                            },
                            "width": "43%"
                        },
                        {
                            "if": {
                                "column_id": "Status"
                            },
                            "width": "13%",
                            "textAlign": "center"
                        },
                        {
                            "if": {
                                "column_id":
                                    "Previous Week"
                            },
                            "width": "12%",
                            "textAlign": "right",
                            "paddingRight": "5px"
                        },
                        {
                            "if": {
                                "column_id":
                                    "Latest Week"
                            },
                            "width": "12%",
                            "textAlign": "right",
                            "paddingRight": "5px"
                        }
                    ],

                    style_data_conditional=[
                        {
                            "if": {
                                "filter_query":
                                    '{Status} = "New"',
                                "column_id": "Status"
                            },
                            "color": NEW_SIGNAL_COLOR,
                            "fontWeight": "bold"
                        },
                        {
                            "if": {
                                "filter_query":
                                    '{Status} = "Ongoing"',
                                "column_id": "Status"
                            },
                            "color": (
                                ONGOING_SIGNAL_COLOR
                            ),
                            "fontWeight": "bold"
                        }
                    ],

                    style_table={
                        "maxHeight": "320px",
                        "overflowY": "auto",
                        "width": "95%",
                        "margin": "0 auto",
                        "padding": "0px",
                        "marginTop": "0px",
                        "overflowX": "auto"
                    }
                )
            ],
            style={
                "marginBottom": "20px"
            }
        )
    
    kpi_content = [
        html.H2(f"Latest Week: {current_week}", className='latest-week', style={'fontSize':'26px'}),
        #html.H3(f"Outbreak Model Certainty Level: {selected_interval:.1f}%",style={'fontSize':'22px'}),
    ]
    # Left column metrics
    left_column_metrics = [
        html.Div([
            html.Div("Potential Outbreaks by State and Disease:", className='metric-label'),
            html.Div(f"{num_outbreaks_per_state_and_disease}", className='metric-value')
        ],className='metric-row'),
        
        html.Div([
            html.Div("Potential Outbreaks by Disease:", className='metric-label'),
            html.Div(f"{num_outbreaks_per_disease}", className='metric-value')
        ],className='metric-row'),
        
        html.Div([
            html.Div("States with Potential Outbreaks:", className='metric-label'),
            html.Div(f"{num_states_with_outbreak}", className='metric-value')
        ],className='metric-row'),
    ]

    # Right column metrics
    right_column_metrics = [
        html.Div([
            html.Div(
                (
                    "Ongoing Potential-Outbreak "
                    "Signals by State and Disease:"
                ),
                className="metric-label"
            ),
            html.Div(
                f"{len(ongoing_outbreaks)}",
                className="metric-value"
            )
        ], className="metric-row"),

        html.Div([
            html.Div(
                "Ongoing Signals by Disease:",
                className="metric-label"
            ),
            html.Div(
                f"{ongoing_outbreaks['label'].nunique()}",
                className="metric-value"
            )
        ], className="metric-row"),

        html.Div([
            html.Div(
                "Jurisdictions with Ongoing Signals:",
                className="metric-label"
            ),
            html.Div(
                f"{ongoing_outbreaks['state'].nunique()}",
                className="metric-value"
            )
        ], className="metric-row"),
    ]

    # df_outbreak = df_outbreak[['item_id','date','state','label','potential_outbreak']]
    # df_outbreak = add_disease_info(df_outbreak)

    # if analysis_type == 'all':
    #     outbreak_counts_category = df_outbreak[df_outbreak['potential_outbreak']][['category']].groupby('category').size()
    #     body_system_counts = df_outbreak[df_outbreak['potential_outbreak']][['body_system']].explode('body_system').groupby('body_system').size()
    #     transmission_counts = df_outbreak[df_outbreak['potential_outbreak']][['transmission']].explode('transmission').groupby('transmission').size()
    #     note_text=""
    #     pathogen_chart = bar_chart_counts(outbreak_counts_category,"Pathogen Type", "blue",note_text)
    #     note_text = "*a single disease may belong to multiple categories"
    #     bodily_system_chart = bar_chart_counts(body_system_counts, "Affected Bodily System", "green",note_text)
    #     transmission_type_chart = bar_chart_counts(transmission_counts, "Transmission Type", "purple",note_text)

    # else:
    #     unique_outbreak_counts_category = df_outbreak[df_outbreak['potential_outbreak']][['category','label']].groupby('category')['label'].nunique()
    #     exploded_body_system = df_outbreak[df_outbreak['potential_outbreak']][['body_system','label']].explode('body_system')
    #     unique_outbreak_counts_body_system = exploded_body_system.groupby('body_system')['label'].nunique()
    #     exploded_transmission = df_outbreak[df_outbreak['potential_outbreak']][['transmission','label']].explode('transmission')
    #     unique_outbreak_counts_transmission = exploded_transmission.groupby('transmission')['label'].nunique()

    #     pathogen_chart = bar_chart_counts(unique_outbreak_counts_category,"Pathogen Type", "blue", "")
    #     note_text = "*a single disease may belong to multiple categories"
    #     bodily_system_chart = bar_chart_counts(unique_outbreak_counts_body_system, "Affected Bodily System", "green", note_text)
    #     transmission_type_chart = bar_chart_counts(unique_outbreak_counts_transmission, "Transmission Type", "purple", note_text)


    return kpi_content, left_column_metrics, right_column_metrics, map_content, table_content, sankey_chart, table_content_ongoing_outbreaks

###### DISEASE HISTORY TAB CALLBACK
@app.callback(
    [
        Output("outbreak_graph", "figure"),
        Output("disease_info_display", "children"),
        Output("history_summary_metrics", "children"),
        Output("history_episodes_table", "children"),
    ],
    [
        Input("state_dropdown", "value"),
        Input("label_dropdown", "value"),
        Input("interval_dropdown_detail", "value"),
        Input("history_period_dropdown", "value"),
    ],
)


def update_graph(selected_state, label_dropdown, selected_interval, history_period):

    # Retrieve the outbreak data based on the selected interval
    df_outbreak = get_outbreaks(df_preds, chosen_interval=selected_interval)

    # Retrieve the list of possible states and labels from df_outbreak
    all_states = sorted(df_outbreak[df_outbreak['potential_outbreak'] == True]['state'].unique())
    all_labels = sorted(df_outbreak[(df_outbreak['potential_outbreak'] == True) & (df_outbreak['state'] == all_states[0])]['label'].unique()) if all_states else []

    if not selected_state:
        selected_state = all_states[0] if all_states else None
    if not label_dropdown and selected_state:
        all_labels = sorted(df_outbreak[(df_outbreak['potential_outbreak'] == True) & (df_outbreak['state'] == selected_state)]['label'].unique())
        label_dropdown = all_labels[0] if all_labels else None


    if selected_state and label_dropdown and selected_interval is not None:

        df_historical_filtered = df_historical[(df_historical['state'] == selected_state) & (df_historical['label'] == label_dropdown)]
        df_latest_filtered = df_outbreak[(df_outbreak['state'] == selected_state) & (df_outbreak['label'] == label_dropdown) & (df_outbreak.new_cases.notna())]
        df_preds_filtered = df_outbreak[(df_outbreak['state'] == selected_state) & (df_outbreak['label'] == label_dropdown)]

        fig = plot_outbreak(df_historical_filtered, df_latest_filtered, df_preds_filtered, selected_state, label_dropdown)


        # Filter first so get_outbreaks_all() only processes
        # one state-disease series.
        history_series = df_preds_all.loc[
            (df_preds_all["state"] == selected_state)
            & (df_preds_all["label"] == label_dropdown)
        ].copy()

        history_series = get_outbreaks_all(
            history_series,
            chosen_interval=selected_interval
        )

        history_summary = summarize_history_period(
            history_series,
            weeks=history_period
        )

        # Highlight on the chart the period summarized by the KPI cards.
        if history_summary is not None:
            fig.add_vrect(
                x0=history_summary["period_start"],
                x1=history_summary["period_end"],
                fillcolor="rgba(255, 255, 255, 0.10)",
                line_width=0,
                layer="below",
            )

            fig.add_vline(
                x=history_summary["period_start"],
                line_width=1,
                line_dash="dot",
                line_color="#888888"
            )

            episodes = get_flagged_episodes(
                history_series,
                period_start=history_summary["period_start"],
                period_end=history_summary["period_end"]
            )

            if episodes.empty:
                episode_table_content = html.Div(
                    [
                        html.H3(
                            "Potential-Outbreak Episodes",
                            style={
                                "textAlign": "center",
                                "color": "white",
                                "fontSize": "22px",
                                "marginBottom": "14px"
                            }
                        ),

                        html.Div(
                            (
                                "No potential-outbreak episodes overlap "
                                "the selected summary period."
                            ),
                            style={
                                "color": "#C8C8C8",
                                "textAlign": "center",
                                "padding": "16px"
                            }
                        )
                    ]
                )

            else:
                episode_table_content = html.Div(
                    [
                        html.H3(
                            "Potential-Outbreak Episodes",
                            style={
                                "textAlign": "center",
                                "color": "white",
                                "fontSize": "22px",
                                "marginBottom": "14px"
                            }
                        ),

                        dash_table.DataTable(
                            columns=[
                                {
                                    "name": column,
                                    "id": column
                                }
                                for column in episodes.columns
                            ],

                            data=episodes.to_dict("records"),

                            style_as_list_view=True,
                            sort_action="native",

                            style_header={
                                "backgroundColor": "rgb(50, 50, 50)",
                                "color": "white",
                                "fontWeight": "bold",
                                "border": "1px solid white",
                                "whiteSpace": "normal",
                                "height": "3em",
                                "textAlign": "center"
                            },

                            style_cell={
                                "backgroundColor": "black",
                                "color": "white",
                                "border": "1px solid grey",
                                "whiteSpace": "normal",
                                "height": "auto",
                                "padding": "8px",
                                "textAlign": "center"
                            },

                            style_cell_conditional=[
                                {
                                    "if": {
                                        "column_id": "Episode Started"
                                    },
                                    "width": "17%"
                                },
                                {
                                    "if": {
                                        "column_id": "Episode Ended"
                                    },
                                    "width": "17%"
                                },
                                {
                                    "if": {
                                        "column_id": "Weeks Flagged"
                                    },
                                    "width": "15%"
                                },
                                {
                                    "if": {
                                        "column_id": "Cases During Episode"
                                    },
                                    "width": "20%"
                                },
                                {
                                    "if": {
                                        "column_id": "Peak Weekly Cases"
                                    },
                                    "width": "18%"
                                },
                                {
                                    "if": {
                                        "column_id": "Status"
                                    },
                                    "width": "13%"
                                }
                            ],

                            style_data_conditional=[
                                {
                                    "if": {
                                        "filter_query":
                                            '{Status} = "Ongoing"'
                                    },
                                    "backgroundColor":
                                        "rgba(222, 45, 38, 0.55)",
                                    "color": "white",
                                    "fontWeight": "bold"
                                }
                            ],

                            style_table={
                                "width": "90%",
                                "margin": "0 auto",
                                "overflowX": "auto",
                                "maxHeight": "280px",
                                "overflowY": "auto"
                            }
                        ),

                        html.Div(
                            (
                                "An episode is a contiguous run of flagged "
                                "weekly observations. Episodes are shown when "
                                "they overlap the selected period; dates and "
                                "case totals describe the complete episode."
                            ),
                            style={
                                "color": "#AFAFAF",
                                "fontSize": "13px",
                                "textAlign": "center",
                                "marginTop": "10px"
                            }
                        )
                    ]
                )

        if history_summary is None:
            history_summary_content = html.Div(
                "No data available for this period.",
                style={
                    "color": "white",
                    "textAlign": "center"
                }
            )
            episode_table_content = []

        else:
            def metric_card(title, value):
                return html.Div(
                    [
                        html.Div(
                            title,
                            style={
                                "fontSize": "15px",
                                "color": "#D0D0D0",
                                "marginBottom": "6px",
                                "textAlign": "center"
                            }
                        ),

                        html.Div(
                            value,
                            style={
                                "fontSize": "28px",
                                "fontWeight": "bold",
                                "color": "white",
                                "textAlign": "center"
                            }
                        )
                    ],
                    style={
                        "backgroundColor": "black",
                        "border": "1px solid #555555",
                        "borderRadius": "8px",
                        "padding": "14px 18px",
                        "minWidth": "190px",
                        "flex": "1 1 190px"
                    }
                )

            history_summary_content = [
                metric_card(
                    "Cases reported",
                    f"{history_summary['total_cases']:,}"
                ),

                metric_card(
                    "Weeks flagged",
                    f"{history_summary['flagged_weeks']:,}"
                ),

                metric_card(
                    "Flagged episodes started",
                    f"{history_summary['episodes_started']:,}"
                ),

                metric_card(
                    "Peak weekly cases",
                    f"{history_summary['peak_weekly_cases']:,}"
                ),

                html.Div(
                    (
                        f"Summary period: "
                        f"{history_summary['period_start']:%Y-%m-%d} "
                        f"to "
                        f"{history_summary['period_end']:%Y-%m-%d}"
                    ),
                    style={
                        "width": "100%",
                        "color": "#BDBDBD",
                        "fontSize": "13px",
                        "textAlign": "center",
                        "marginTop": "2px"
                    }
                )
            ]
    else:
        fig = go.Figure(
            layout_template="plotly_dark"
        )

        history_summary_content = []
        episode_table_content = []

    
    disease_group = disease_groups.get(label_dropdown, None)
    details = disease_details.get(disease_group, {})

    if details:  
        if (label_dropdown == "Q fever, Total" and selected_state == "PENNSYLVANIA"):
            transmission_type_content = [
                html.H4(f"Transmission Type: {', '.join(details.get('transmission', ['N/A']))}", style={'color': '#7FDBFF'}),
                html.Img(src="assets/q-who-photo-u2.jpg", style={'height': '100px', 'width': 'auto', 'margin-left': '10px'})
            ]
        else:
            transmission_type_content = html.H4(f"Transmission Type: {', '.join(details.get('transmission', ['N/A']))}", style={'color': '#7FDBFF'})

        disease_html =  [
            html.H2("Disease Information",style={'fontSize':'26px'}),
            html.H4(label_dropdown,style={'color': '#7FDBFF'}),
            html.H4(f"Group: {details.get('group', 'Unknown Group')}",style={'color': '#7FDBFF','fontSize':'22px'}),  
            html.H4(f"Pathogen: {details.get('category', 'N/A')}",style={'color': '#7FDBFF','fontSize':'22px'}),
            html.H4(f"Affected Bodily System: {', '.join(details.get('body_system', ['N/A']))}",style={'color': '#7FDBFF','fontSize':'22px'}),
            html.Div(transmission_type_content, style={'display': 'flex', 'align-items': 'center','fontSize':'22px'})

        ]
    else:
        disease_html = html.H4("")
    
    return (
        fig,
        disease_html,
        history_summary_content,
        episode_table_content
    )

###### OUTBREAK TRENDS TAB CALLBACK
@app.callback(
    [
        Output(
            "outbreak_history_potential_resolved",
            "figure"
        ),
        Output(
            "outbreak_history_ongoing",
            "figure"
        ),
        Output(
            "trends_summary_metrics",
            "children"
        ),
    ],
    [
        Input(
            "state_dropdown_outbreak_history",
            "value"
        ),
        Input(
            "show_cumulative_toggle",
            "value"
        ),
        Input(
            "interval_dropdown_outbreak",
            "value"
        ),
        Input(
            "trends_period_dropdown",
            "value"
        ),
    ],
)
def update_outbreak_history_graph(
    selected_states,
    show_cumulative_toggle,
    selected_interval,
    trends_period
):

    if selected_states:
        df_outbreak_history_filt = (
            df_preds_all.loc[
                df_preds_all["state"].isin(
                    selected_states
                )
            ].copy()
        )
    else:
        df_outbreak_history_filt = (
            df_preds_all.copy()
        )

    # Calculate outbreak status using the full available history.
    df_outbreak_history_filt = get_outbreaks_all(
        df_outbreak_history_filt,
        selected_interval
    )

    df_outbreak_history_filt = (
        df_outbreak_history_filt[
            [
                "item_id",
                "state",
                "label",
                "date",
                "potential_outbreak",
                "potential_outbreak_past_week",
                "Potential_Outbreak_Resolved",
            ]
        ].copy()
    )

    # The same end date is used for both charts.
    if df_outbreak_history_filt.empty:
        display_end_date = None
    else:
        display_end_date = (
            df_outbreak_history_filt["date"].max()
        )

    # -------------------------------------------------
    # Aggregate using the complete history first.
    # -------------------------------------------------
    df_weekly_new_episodes_full = (
        agg_new_episode_counts(
            df_outbreak_history_filt
        )
    )

    df_weekly_ongoing_full = agg_outbreak_counts(
        df_outbreak_history_filt,
        condition="ongoing_outbreaks"
    )

    # -------------------------------------------------
    # Only now restrict what is displayed.
    # -------------------------------------------------
    df_weekly_new_episodes = (
        filter_weekly_display_period(
            df_weekly_new_episodes_full,
            period_weeks=trends_period,
            end_date=display_end_date
        )
    )

    df_weekly_ongoing = (
        filter_weekly_display_period(
            df_weekly_ongoing_full,
            period_weeks=trends_period,
            end_date=display_end_date
        )
    )

    # Cumulative counts restart at zero for the selected
    # display period.
    if not df_weekly_ongoing.empty:
        df_weekly_ongoing[
            "cumulative_count"
        ] = (
            df_weekly_ongoing["count"]
            .cumsum()
        )

    # -------------------------------------------------
    # Summary metrics for the selected display period
    # -------------------------------------------------
    if df_weekly_new_episodes.empty:
        trends_summary_content = html.Div(
            "No outbreak trend data are available for this period.",
            style={
                "color": "#C8C8C8",
                "textAlign": "center",
                "width": "100%",
                "padding": "12px"
            }
        )

    else:
        new_episodes_period = int(
            df_weekly_new_episodes[
                "new_episodes"
            ].sum()
        )

        latest_new_episodes = int(
            df_weekly_new_episodes.iloc[-1][
                "new_episodes"
            ]
        )

        latest_week_date = pd.to_datetime(
            df_weekly_new_episodes.iloc[-1]["date"]
        )

        peak_index = (
            df_weekly_new_episodes[
                "new_episodes"
            ].idxmax()
        )

        peak_row = df_weekly_new_episodes.loc[
            peak_index
        ]

        peak_week_value = int(
            peak_row["new_episodes"]
        )

        peak_week_date = pd.to_datetime(
            peak_row["date"]
        )

        currently_ongoing = (
            int(df_weekly_ongoing.iloc[-1]["count"])
            if not df_weekly_ongoing.empty
            else 0
        )

        def trend_metric_card(
            title,
            value,
            subtitle=None
        ):
            card_children = [
                html.Div(
                    title,
                    style={
                        "fontSize": "15px",
                        "color": "#D0D0D0",
                        "marginBottom": "6px",
                        "textAlign": "center"
                    }
                ),

                html.Div(
                    value,
                    style={
                        "fontSize": "28px",
                        "fontWeight": "bold",
                        "color": "white",
                        "textAlign": "center"
                    }
                )
            ]

            if subtitle:
                card_children.append(
                    html.Div(
                        subtitle,
                        style={
                            "fontSize": "12px",
                            "color": "#AFAFAF",
                            "marginTop": "4px",
                            "textAlign": "center"
                        }
                    )
                )

            return html.Div(
                card_children,
                style={
                    "backgroundColor": "black",
                    "border": "1px solid #555555",
                    "borderRadius": "8px",
                    "padding": "14px 18px",
                    "minWidth": "215px",
                    "flex": "1 1 215px"
                }
            )

        trends_summary_content = [
            trend_metric_card(
                "New episodes during period",
                f"{new_episodes_period:,}"
            ),

            trend_metric_card(
                "Peak new-episode week",
                f"{peak_week_value:,}",
                peak_week_date.strftime(
                    "%Y-%m-%d"
                )
            ),

            trend_metric_card(
                "Latest week new episodes",
                f"{latest_new_episodes:,}",
                latest_week_date.strftime(
                    "%Y-%m-%d"
                )
            ),

            trend_metric_card(
                "Currently ongoing signals",
                f"{currently_ongoing:,}"
            )
        ]

    fig_new_episodes = plot_new_episode_trends(
        df_weekly_new_episodes
    )

    display_start_date = (
        df_weekly_new_episodes["date"].min()
        if not df_weekly_new_episodes.empty
        else None
    )

    if (
        show_cumulative_toggle
        and "cumulative" in show_cumulative_toggle
    ):
        fig_ongoing = plot_time_series(
            df_weekly_ongoing,
            title=(
                "Cumulative Ongoing "
                "Potential Outbreaks"
            ),
            display_col="cumulative_count",
            primary_name="Ongoing",
            primary_color="#A50A0A",
            min_date=display_start_date
        )

    else:
        fig_ongoing = plot_time_series(
            df_weekly_ongoing,
            title="Ongoing Potential Outbreaks",
            display_col="count",
            primary_name="Ongoing",
            primary_color="#A50A0A",
            min_date=display_start_date
        )

    return (
        fig_new_episodes,
        fig_ongoing,
        trends_summary_content
    )    


################################
@app.callback(
    Output("interval_dropdown", "value"),
    Output("interval_dropdown_detail", "value"),
    Output("interval_dropdown_outbreak", "value"),

    Input("interval_dropdown", "value"),
    Input("interval_dropdown_detail", "value"),
    Input("interval_dropdown_outbreak", "value"),
)
def synchronize_dropdowns(
    summary_value,
    detail_value,
    history_value
):
    trigger_id = ctx.triggered_id

    values = {
        "interval_dropdown": summary_value,
        "interval_dropdown_detail": detail_value,
        "interval_dropdown_outbreak": history_value,
    }

    value = values.get(
        trigger_id,
        summary_value
    )

    return value, value, value


#######################
######INFO TAB#########
#######################

# Callbacks for toggling the collapse

toggle_callbacks = [
    {"trigger": "collapse-button-dashboard-info", "target": "collapse-dashboard-info"},
    {"trigger": "collapse-button-tab-info", "target": "collapse-tab-info"},
   
    {"trigger": "collapse-button-data-sources", "target": "collapse-data-sources"},

    {"trigger": "collapse-button-modeling", "target": "collapse-modeling"},
    {"trigger": "collapse-button-modeling-text", "target": "collapse-modeling-text"},
    {"trigger": "collapse-button-automated", "target": "collapse-automated"},
]

for callback in toggle_callbacks:
    @app.callback(
        Output(callback["target"], "is_open"),
        [Input(callback["trigger"], "n_clicks")],
        [State(callback["target"], "is_open")],
    )
    def toggle_collapse(n, is_open):
        if n:
            return not is_open
        return is_open
    
#if __name__ == '__main__':
    #app.run_server(debug=False, host='0.0.0.0', port=8050)
    #app.run_server(debug=True, port=8080)
