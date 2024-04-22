import dash
from dash import dcc, html, ctx, dash_table
from dash.dependencies import Input, Output
import plotly.graph_objects as go
import dash_bootstrap_components as dbc
import pandas as pd

from src.tabs.history_tab_helper import plot_outbreak

from src.tabs.summary_tab_helper import (
    get_outbreaks, create_us_map, 
    is_outbreak_resolved, create_sankey_chart,
    get_outbreaks_all)
from src.tabs.load_data import load_preds
from src.tabs.summary_tab import summary_tab_layout
from src.tabs.history_tab import details_tab_layout 
from src.tabs.disease_info import add_disease_info , bar_chart_counts, disease_groups, disease_details
from src.tabs.outbreaks_history_tab import outbreaks_history_tab_layout
from src.tabs.outbreaks_history_tab_helper import agg_outbreak_counts, plot_time_series
from src.tabs.type_counts import outbreaks_type_counts_tab_layout

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY, dbc.icons.BOOTSTRAP])
server = app.server # Expose the Flask server for Gunicorn

app.title = "Outbreak Dashboard"

###################################################
cols_wanted = ['item_id', 'state', 'date', 'label', 'new_cases']
date_filter_hist = [('date', '>=', pd.to_datetime('2022-01-01'))]
date_filter_preds = [('date', '>=', pd.to_datetime('2024-01-01'))]

def load_data():
    df_historical = pd.read_parquet("data/df_historical.parquet", columns=cols_wanted, filters=date_filter_hist)
    df_preds_all =  pd.read_parquet("data/df_predictions.parquet", filters=date_filter_preds)
    return df_historical, df_preds_all

df_historical, df_preds_all = load_data()

#################################################

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

# Callback to update data
@app.callback(Output('hidden-div', 'children'), [Input('interval-component', 'n_intervals')])
def update_data(n):
    df_historical, df_preds_all = load_data()
    # Additional processing or manipulation of the data if needed
    return ""

#######################################################

app.layout = html.Div([ 


    dcc.Store(id='shared-dropdown-value'),
    html.Div([
        html.Div(children=[
            html.H1("OUTBREAK!", style={
            'color': 'black',  
            'fontSize': '6vw',
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
            ], style={'textAlign': 'center', 'width': '100%', 'marginTop': '0px','backgroundColor':'black'}),

        dcc.Tabs(id="tabs", value='tab-1', className='tab-container', children=[
            dcc.Tab(label='Latest Week Summary', value='tab-1', className='custom-tab', selected_className='custom-tab-active', children=summary_tab_layout()),
            dcc.Tab(label='Outbreaks Profiles', value='tab-4', className='custom-tab', selected_className='custom-tab-active',children=outbreaks_type_counts_tab_layout()),
            dcc.Tab(label='Disease History', value='tab-2', className='custom-tab', selected_className='custom-tab-active', children=details_tab_layout()),
            dcc.Tab(label='Outbreaks History', value='tab-3', className='custom-tab', selected_className='custom-tab-active',children=outbreaks_history_tab_layout()),
            #dcc.Tab(label='Info', value='tab-5', className='custom-tab', selected_className='custom-tab-active',children=ai_patient_view_tab_layout()),
        ], style={'position': 'sticky', 'top': '0', 'zIndex': '1000','width': '100%', 'display': 'block'}),
    ], className='full-width'),
    
    dbc.Container([
        html.Div(id='tabs-content'),

        html.Div(id='hidden-div', style={'display': 'none'}),
        dcc.Interval(
            id='interval-component',
            interval=12*3600*1000,  # every 12 hours
            n_intervals=0
        )
        ], fluid=True)
    ], style={'width': '100%'})

##############################
##### CALLBACKS###############
##############################
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
    Output('outbreak_kpi', 'children'),
    Output('left_column_metrics','children'),
    Output('right_column_metrics','children'),
    Output('us-map', 'figure'),
    Output('territories-table', 'children'),
    Output('sankey-chart', 'figure'),
    #Output('pathogen-chart', 'figure'),
    #Output('bodily-chart', 'figure'),
    #Output('transmission-chart', 'figure'),
    Output('ongoing-outbreaks-table', 'children'),
    ],
    [
    Input('interval_dropdown', 'value'),
    ]  
)
def update_kpi(selected_interval):
    
    df_outbreak = get_outbreaks(df_preds, chosen_interval=selected_interval)

    current_week = df_latest['date'].max().strftime('%Y-%m-%d')
    num_outbreaks_per_state_and_disease = df_outbreak['potential_outbreak'].sum()
    num_outbreaks_per_disease = len(df_outbreak[df_outbreak['potential_outbreak'] == True]['label'].unique())
    num_states_with_outbreak = len(df_outbreak[df_outbreak['potential_outbreak'] == True]['state'].unique())

    top_state = df_outbreak.groupby(['state'],as_index=False)['potential_outbreak'].sum().sort_values('potential_outbreak',ascending=False).iloc[0]
    
    df_outbreak = is_outbreak_resolved(df_outbreak)
    map_content, df_territories = create_us_map(df_outbreak)

    table_content = html.Div([
            html.H3("US Territories Potential Outbreaks", style={'textAlign': 'center', 'color': 'white','fontSize':'22px'}),
            dash_table.DataTable(
                columns=[{"name": i, "id": i} for i in df_territories.columns],
                data=df_territories.to_dict('records'),
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

    df_outbreak_all = get_outbreaks_all(df_preds_all, selected_interval)
    sankey_chart, ongoing_outbreaks, resolved_outbreaks_week_2 = create_sankey_chart(df_outbreak_all)

    if ongoing_outbreaks.empty:
        table_title = "Ongoing Outbreaks: None"
    else:
        table_title = "Ongoing Outbreak Cases"
        
    table_content_ongoing_outbreaks = html.Div([
        html.H3(table_title, style={'textAlign': 'center', 'color': 'white','fontSize':'22px'}),
        dash_table.DataTable(
            columns=[{"name": i, "id": i} for i in ongoing_outbreaks.columns],
            data=ongoing_outbreaks.to_dict('records'),
            style_as_list_view=True,
            style_header={'backgroundColor': 'rgb(50, 50, 50)', 'color': 'white', 'fontWeight': 'bold', 'border': '1px solid white',
                          'whiteSpace': 'normal','height':'3em'},
            style_cell={'backgroundColor': 'rgb(0, 0, 0)', 'color': 'white', 'border': '1px solid grey',
                    'whiteSpace': 'normal',
                    'height': 'auto'},
            style_header_conditional=[
                    {
                        'if': {'column_id': 'Latest Week'},  
                        'paddingRight': '5px'  
                    }
                ],
            style_cell_conditional=[
                    {
                        'if': {'column_id': 'Latest Week'}, 
                        'paddingRight': '5px'  
                    }
                ],
            style_table={
                'maxHeight': '215px',  
                'overflowY': 'auto',  
                'width': '90%',  
                'margin': '0 auto',  
                'padding': '0px',
                'marginTop': '0px',
                'overflowX': 'auto', 
            },
        )
    ], style={'marginBottom': '20px'})
    
    kpi_content = [
        html.H2(f"Latest Week: {current_week}",style={'fontSize':'26px'}),
        #html.H3(f"Outbreak Model Certainty Level: {selected_interval:.1f}%",style={'fontSize':'22px'}),
    ]
    # Left column metrics
    left_column_metrics = [
        html.Div([
            html.Div("Potential Outbreaks by State and Disease:", style={'textAlign': 'right', 'width': '530px'}),
            html.Div(f"{num_outbreaks_per_state_and_disease}", style={'textAlign': 'right', 'width': '50px'})
        ], style={'display': 'grid', 'gridTemplateColumns': '530px 100px', 'alignItems': 'center'}),
        
        html.Div([
            html.Div("Potential Outbreaks by Disease:", style={'textAlign': 'right', 'width': '530px'}),
            html.Div(f"{num_outbreaks_per_disease}", style={'textAlign': 'right', 'width': '50px'})
        ], style={'display': 'grid', 'gridTemplateColumns': '530px 100px', 'alignItems': 'center'}),
        
        html.Div([
            html.Div("States with Potential Outbreaks:", style={'textAlign': 'right', 'width': '530px'}),
            html.Div(f"{num_states_with_outbreak}", style={'textAlign': 'right', 'width': '50px'})
        ], style={'display': 'grid', 'gridTemplateColumns': '530px 100px', 'alignItems': 'center'}),
    ]

    # Right column metrics
    right_column_metrics = [

        html.Div([
            html.Div("Ongoing Potential Outbreaks by State and Disease:", style={'textAlign': 'right', 'width': '530px'}),
            html.Div(f"{len(ongoing_outbreaks)}", style={'textAlign': 'right', 'width': '50px'})
        ], style={'display': 'grid', 'gridTemplateColumns': '530px 100px', 'alignItems': 'center'}),

        html.Div([
            html.Div("Ongoing Potential Outbreaks by Disease:", style={'textAlign': 'right', 'width': '530px'}),
            html.Div(f"{len(ongoing_outbreaks['Disease'].unique())}", style={'textAlign': 'right', 'width': '50px'})
        ], style={'display': 'grid', 'gridTemplateColumns': '530px 100px', 'alignItems': 'center'}),
        
        html.Div([
            html.Div("States with Ongoing Potential Outbreaks:", style={'textAlign': 'right', 'width': '530px'}),
            html.Div(f"{len(ongoing_outbreaks['US State / Territory'].unique())}", style={'textAlign': 'right', 'width': '50px'})
        ], style={'display': 'grid', 'gridTemplateColumns': '530px 100px', 'alignItems': 'center'}),
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
        Output('outbreak_graph', 'figure'),
        Output('disease_info_display', 'children')
    ],
    [
        Input('state_dropdown', 'value'),
        Input('label_dropdown', 'value'),
        Input('interval_dropdown_detail', 'value')
        ]  
)
def update_graph(selected_state, label_dropdown, selected_interval):

    if selected_state and label_dropdown and selected_interval is not None:

        df_outbreak = get_outbreaks(df_preds, chosen_interval=selected_interval)

        df_historical_filtered = df_historical[(df_historical['state'] == selected_state) & (df_historical['label'] == label_dropdown)]
        df_latest_filtered = df_outbreak[(df_outbreak['state'] == selected_state) & (df_outbreak['label'] == label_dropdown) & (df_outbreak.new_cases.notna())]
        df_preds_filtered = df_outbreak[(df_outbreak['state'] == selected_state) & (df_outbreak['label'] == label_dropdown)]

        fig = plot_outbreak(df_historical_filtered, df_latest_filtered, df_preds_filtered, selected_state, label_dropdown)

    else:
        fig = go.Figure(layout_template="plotly_dark")
    
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
    
    return fig, disease_html


###### OUTBREAK HISTORY TAB CALLBACK
@app.callback(
        [
        Output('outbreak_history_potential_resolved', 'figure'),
        Output('outbreak_history_ongoing', 'figure')
        ],
    [
        Input('state_dropdown_outbreak_history', 'value'),
        Input('show_cumulative_toggle', 'value'),
        Input('interval_dropdown_outbreak', 'value')
        ]  
)
def update_outbreak_history_graph(selected_states, show_cumulative_toggle, selected_interval):
    

    if selected_states:
        df_outbreak_history_filt = df_preds_all[df_preds_all.state.isin(selected_states)]
    else:
        df_outbreak_history_filt = df_preds_all
    
    df_outbreak_history_filt = get_outbreaks_all(df_outbreak_history_filt, selected_interval)
    df_outbreak_history_filt = df_outbreak_history_filt[['item_id','state','label','date','potential_outbreak','potential_outbreak_past_week','Potential_Outbreak_Resolved']]
    df_weekly_resolved = agg_outbreak_counts(df_outbreak_history_filt, condition='resolved_outbreaks')
    df_weekly_potential = agg_outbreak_counts(df_outbreak_history_filt,  condition='potential_outbreak')
    df_weekly_ongoing = agg_outbreak_counts(df_outbreak_history_filt,  condition='ongoing_outbreaks')

    if "cumulative" in show_cumulative_toggle:
        fig_potential_resolved = plot_time_series(df_weekly_potential, title="Cumulative Potential vs Resolved Outbreaks", 
                        display_col='cumulative_count', primary_name = 'Potential', primary_color='#DE2D26', df_secondary=df_weekly_resolved, 
                        secondary_display_col='cumulative_count', secondary_name='Resolved',min_date=df_weekly_potential.date.min())
        
        fig_ongoing = plot_time_series(df_weekly_ongoing, title="Cumulative Ongoing Potential Outbreaks", 
                        display_col='cumulative_count', primary_name = 'Ongoing', primary_color='#A50A0A', min_date=df_weekly_potential.date.min())
    else:
        fig_potential_resolved = plot_time_series(df_weekly_potential, title="Potential vs Resolved Outbreaks", 
                display_col='count', primary_name = 'Potential', primary_color='#DE2D26', df_secondary=df_weekly_resolved, 
                secondary_display_col='count', secondary_name='Resolved',min_date=df_weekly_potential.date.min())
        
        fig_ongoing = plot_time_series(df_weekly_ongoing, title="Ongoing Potential Outbreaks", 
                        display_col='count', primary_name = 'Ongoing', primary_color='#A50A0A', min_date=df_weekly_potential.date.min())
    
    return fig_potential_resolved, fig_ongoing


################## TYPE COUNTS TAB##########
@app.callback(
  [
    Output('pathogen-chart', 'figure'),
    Output('bodily-chart', 'figure'),
    Output('transmission-chart', 'figure'),
    Output('outbreak-table', 'children'),

    ],
    [
    Input('interval_dropdown_type', 'value'),
    Input('analysis-toggle', 'value'),
    Input('state_dropdown_outbreak_type_counts', 'value'),
    ]  
)
def update_type_counts(selected_interval, analysis_type, states_selected):
    
    if states_selected:
        df_outbreak_type_filt = df_preds[df_preds.state.isin(states_selected)]
    else:
        df_outbreak_type_filt = df_preds

    df_outbreak = get_outbreaks(df_outbreak_type_filt, chosen_interval=selected_interval)

    current_week = df_latest['date'].max().strftime('%Y-%m-%d')
    num_outbreaks_per_state_and_disease = df_outbreak['potential_outbreak'].sum()
    num_outbreaks_per_disease = len(df_outbreak[df_outbreak['potential_outbreak'] == True]['label'].unique())
    num_states_with_outbreak = len(df_outbreak[df_outbreak['potential_outbreak'] == True]['state'].unique())

    
    #df_outbreak = is_outbreak_resolved(df_outbreak)
    #df_outbreak_all = get_outbreaks_all(df_preds_all, selected_interval)

    df_outbreak = df_outbreak[['item_id','date','state','label','new_cases','potential_outbreak','pred_upper']]
    df_outbreak = add_disease_info(df_outbreak)

    if analysis_type == 'all':
        outbreak_counts_category = df_outbreak[df_outbreak['potential_outbreak']][['category']].groupby('category').size()
        body_system_counts = df_outbreak[df_outbreak['potential_outbreak']][['body_system']].explode('body_system').groupby('body_system').size()
        transmission_counts = df_outbreak[df_outbreak['potential_outbreak']][['transmission']].explode('transmission').groupby('transmission').size()
        note_text=""
        pathogen_chart = bar_chart_counts(outbreak_counts_category,"Pathogen Type", "blue",note_text)
        note_text = "*a single disease may belong to multiple categories"
        bodily_system_chart = bar_chart_counts(body_system_counts, "Affected Bodily System", "green",note_text)
        transmission_type_chart = bar_chart_counts(transmission_counts, "Transmission Type", "purple",note_text)

    else:
        unique_outbreak_counts_category = df_outbreak[df_outbreak['potential_outbreak']][['category','label']].groupby('category')['label'].nunique()
        exploded_body_system = df_outbreak[df_outbreak['potential_outbreak']][['body_system','label']].explode('body_system')
        unique_outbreak_counts_body_system = exploded_body_system.groupby('body_system')['label'].nunique()
        exploded_transmission = df_outbreak[df_outbreak['potential_outbreak']][['transmission','label']].explode('transmission')
        unique_outbreak_counts_transmission = exploded_transmission.groupby('transmission')['label'].nunique()

        pathogen_chart = bar_chart_counts(unique_outbreak_counts_category,"Pathogen Type", "blue", "")
        note_text = "*a single disease may belong to multiple categories"
        bodily_system_chart = bar_chart_counts(unique_outbreak_counts_body_system, "Affected Bodily System", "green", note_text)
        transmission_type_chart = bar_chart_counts(unique_outbreak_counts_transmission, "Transmission Type", "purple", note_text)


    df_out_table = df_outbreak[df_outbreak.potential_outbreak==True][['state','label','category','body_system','transmission','new_cases']]
    #print(df_out_table.head())
    df_out_table['body_system'] = df_out_table['body_system'].apply(lambda x: ', '.join(x))
    df_out_table['transmission'] = df_out_table['transmission'].apply(lambda x: ', '.join(x))
    df_out_table.columns = ['State / Territory','Disease','Pathogen', 'Affected System', 'Transmission', 'Cases']
    df_out_table['Cases'] = df_out_table.Cases.astype(int)

    table_title = "Potential Outbreaks Details"
    table_content_outbreaks = html.Div([
        html.H3(table_title, style={'textAlign': 'center', 'color': 'white','fontSize':'26px'}),
        dash_table.DataTable(
                id='table',
                columns=[{'id': c, 'name': c} for c in df_out_table.columns],
                data=df_out_table.to_dict('records'),
                style_table={'overflowX': 'auto', 'minWdith':'100%'},
                # Enable sorting
                sort_action='native',
                # Optional features
                filter_action='native',  # Enables filtering of data by user
                page_action='native',    # Enables data pagination
                page_size=15,             # Number of rows visible per page

            style_header={'backgroundColor': 'rgb(50, 50, 50)', 'color': 'white', 'fontWeight': 'bold', 'border': '1px solid white',
                          'whiteSpace': 'normal','height':'3em'},
            style_cell={'backgroundColor': 'rgb(0, 0, 0)', 'color': 'white', 'border': '1px solid grey', 'paddingRight': '5px',
                    'whiteSpace': 'normal',
                    'height': 'auto'},
            style_filter={ 'fontWeight': 'bold','fontSize':'20px'},
            style_cell_conditional=[
                {'if': {'column_id': 'State / Territory'}, 'width': '11.5%'},
                {'if': {'column_id': 'Disease'}, 'width': '42.5%'},  # Wide column for variable content
                {'if': {'column_id': 'Pathogen'}, 'width': '7%'},
                {'if': {'column_id': 'Affected System'}, 'width': '17%'},
                {'if': {'column_id': 'Transmission'}, 'width': '17%'},
                {'if': {'column_id': 'Cases'}, 'width': '5%'}
            ],)
        ])

    return pathogen_chart, bodily_system_chart, transmission_type_chart, table_content_outbreaks

################################
@app.callback(
    Output('interval_dropdown', 'value'),
    Output('interval_dropdown_detail', 'value'),
    Output('interval_dropdown_outbreak', 'value'),
    Output('interval_dropdown_type', 'value'),

    Input('interval_dropdown', 'value'),
    Input('interval_dropdown_detail', 'value'),
    Input('interval_dropdown_outbreak', 'value'),
    Input('interval_dropdown_type', 'value'),

)
def synchronize_dropdowns(tab1_value, tab2_value, tab3_value,tab4_value):
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    if trigger_id == 'interval_dropdown':
        value = tab1_value
    elif trigger_id == 'interval_dropdown_detail':
        value = tab2_value
    elif trigger_id == 'interval_dropdown_outbreak':
        value = tab3_value
    else:
        value = tab4_value
    
    return value, value, value, value


#if __name__ == '__main__':
    #app.run_server(debug=False, host='0.0.0.0', port=8050)
    #app.run_server(debug=True, port=8080)
