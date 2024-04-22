import pandas as pd
from dash import html, dcc
import dash_bootstrap_components as dbc
import plotly.graph_objects as go


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


def filter_prediction_interval(df, interval_percentage):
    """
    Filters the DataFrame for a specific prediction interval, retrieving the corresponding
    upper and lower bounds as well as the mean prediction.

    Parameters:
    - df: The long-format DataFrame with prediction data.
    - interval_percentage: The desired interval as a percentage (e.g., 80 for "Upper 80%").

    Returns:
    - A DataFrame filtered for the specified upper and lower prediction interval and the mean.
    """
    # Define the quantile names based on the selected interval
    upper_quantile = f"Upper {interval_percentage}%"
    lower_quantile = f"Lower {interval_percentage}%"
    
    # Filter the DataFrame for the selected quantiles and the mean
    filtered_df = df[df['quantile'].isin([upper_quantile, lower_quantile, "Median", "Mean"])]
    
    return filtered_df


def identify_outbreaks(df_pred_wide, df_latest):
    
    df_outbreak = pd.merge(df_pred_wide, df_latest,on=['item_id','date','state','label'], how='left')
    df_outbreak['potential_outbreak'] = df_outbreak['new_cases'] > df_outbreak['pred_upper']
    return df_outbreak

def get_outbreaks(df_preds, chosen_interval=99):

    df_outbreak = filter_prediction_interval_all_outbreaks(df_preds, chosen_interval)
    #df_outbreak = pd.merge(df_latest, filtered_df,on=['item_id','date','label','state'])
    #print(df_preds.columns)
    df_outbreak['potential_outbreak'] = df_outbreak['new_cases'] > df_outbreak['pred_upper']

    return df_outbreak

def filter_prediction_interval_all_outbreaks(df_preds_all, chosen_interval):

    upper_interval_to_column = {
        80: 'pred_upper_0_8',
        90: 'pred_upper_0_9',
        95: 'pred_upper_0_95',
        97: 'pred_upper_0_97',
        99: 'pred_upper_0_99',
        99.9: 'pred_upper_0_999'
    }
    upper_chosen_column = upper_interval_to_column.get(chosen_interval)

    lower_interval_to_column = {
        80: 'pred_lower_0_2',
        90: 'pred_lower_0_1',
        95: 'pred_lower_0_05',
        97: 'pred_lower_0_03',
        99: 'pred_lower_0_01',
        99.9: 'pred_lower_0_001'
    }
    lower_chosen_column = lower_interval_to_column.get(chosen_interval)

    df_filtered = df_preds_all.copy()
    df_filtered['pred_upper'] = df_filtered[upper_chosen_column]
    df_filtered['pred_lower'] = df_filtered[lower_chosen_column]

    return df_filtered

def get_outbreaks_all(df_preds_all, chosen_interval=99):

    filtered_df = filter_prediction_interval_all_outbreaks(df_preds_all, chosen_interval)
    filtered_df = filtered_df.copy()  
    
    filtered_df['potential_outbreak'] = filtered_df['new_cases'] > filtered_df['pred_upper']
    filtered_df = is_outbreak_resolved(filtered_df)
    
    return filtered_df


def is_outbreak_resolved(df):
    # Make a copy of the DataFrame to ensure we're not modifying the original unintentionally
    df_copy = df.copy()
    
    # Step 1: Sort the DataFrame by 'item_id' and 'date'
    df_copy = df_copy.sort_values(by=['item_id', 'date'])  # Removed inplace=True
    
    # Step 2: Remove rows with NA for new cases (assume data skips a week)
    df_copy = df_copy[df_copy.new_cases.notna()]
    
    # Step 3: Create a column for potential outbreak in the past week by shifting the current week
    df_copy['potential_outbreak_past_week'] = df_copy.groupby('item_id')['potential_outbreak'].shift(1)
    
    # Step 4: Determine if the potential outbreak was resolved
    # An outbreak is resolved if it was present last week but not this week
    df_copy['Potential_Outbreak_Resolved'] = ~((df_copy['potential_outbreak'] == True) & (df_copy['potential_outbreak_past_week'] == True))
    
    return df_copy


state_code_mapping = {
    'ALABAMA': 'AL', 'ALASKA': 'AK', 'AMERICAN SAMOA': 'AS', 'ARIZONA': 'AZ',
    'ARKANSAS': 'AR', 'CALIFORNIA': 'CA', 'COLORADO': 'CO', 'CONNECTICUT': 'CT',
    'DELAWARE': 'DE', 'DISTRICT OF COLUMBIA': 'DC', 'FLORIDA': 'FL', 'GEORGIA': 'GA',
    'GUAM': 'GU', 'HAWAII': 'HI', 'IDAHO': 'ID', 'ILLINOIS': 'IL',
    'INDIANA': 'IN', 'IOWA': 'IA', 'KANSAS': 'KS', 'KENTUCKY': 'KY',
    'LOUISIANA': 'LA', 'MAINE': 'ME', 'MARYLAND': 'MD', 'MASSACHUSETTS': 'MA',
    'MICHIGAN': 'MI', 'MINNESOTA': 'MN', 'MISSISSIPPI': 'MS', 'MISSOURI': 'MO',
    'MONTANA': 'MT', 'NEBRASKA': 'NE', 'NEVADA': 'NV', 'NEW HAMPSHIRE': 'NH',
    'NEW JERSEY': 'NJ', 'NEW MEXICO': 'NM', 'NEW YORK CITY': 'NYC', 'NEW YORK': 'NY',
    'NORTH CAROLINA': 'NC', 'NORTH DAKOTA': 'ND', 'NORTHERN MARIANA ISLANDS': 'MP',
    'OHIO': 'OH', 'OKLAHOMA': 'OK', 'OREGON': 'OR', 'PENNSYLVANIA': 'PA',
    'PUERTO RICO': 'PR', 'RHODE ISLAND': 'RI', 'SOUTH CAROLINA': 'SC',
    'SOUTH DAKOTA': 'SD', 'TENNESSEE': 'TN', 'TEXAS': 'TX', 'U.S. VIRGIN ISLANDS': 'VI',
    'UTAH': 'UT', 'VERMONT': 'VT', 'VIRGINIA': 'VA', 'WASHINGTON': 'WA',
    'WEST VIRGINIA': 'WV', 'WISCONSIN': 'WI', 'WYOMING': 'WY'
}

def create_us_map(df_outbreak):
    
    
    date_wanted = df_outbreak.date.max()
    outbreaks_per_state = df_outbreak[df_outbreak.date==date_wanted].groupby('state')['potential_outbreak'].apply(lambda x: x.astype(int).sum()).reset_index()
    outbreaks_per_state['state_code'] = outbreaks_per_state['state'].map(state_code_mapping)
    territories = ['PR', 'GU', 'VI', 'AS', 'MP','NYC']  # Puerto Rico, Guam, U.S. Virgin Islands, American Samoa, Northern Mariana Islands, NYC

    df_states = outbreaks_per_state[~outbreaks_per_state['state_code'].isin(territories)]
    df_territories = outbreaks_per_state[outbreaks_per_state['state_code'].isin(territories)]
    df_territories = df_territories.rename(columns={"state":"US Territory / City","potential_outbreak":"Potential Outbreaks"})

    fig = go.Figure(data=go.Choropleth(
        locations=df_states['state_code'],
        z=df_states['potential_outbreak'].astype(float),
        locationmode='USA-states',
        colorscale='Reds',
        #colorbar_title="",
        
        colorbar=dict(x=0.9,thickness=5,len=.7), 
    ))

    fig.update_layout(
        title_text=f"Potential Outbreaks by State", #: {date_wanted.strftime('%Y-%m-%d')}",
        title_x=0.5,  
        title_y=0.97,  
        geo_scope='usa',
        paper_bgcolor='black',
        plot_bgcolor='black',
        template="plotly_dark",
        geo=dict(
            landcolor='rgb(83, 83, 83)',
            lakecolor='rgb(32, 32, 32)',
            subunitcolor='rgb(100, 100, 100)',
            countrycolor='rgb(100, 100, 100)',
            bgcolor='rgb(0, 0, 0)',
        ),
        #width=600, 
        #height=400,
        margin=dict(l=0, r=0, b=10,t=20),
        title_font=dict(size=22, color='white', family="Arial, sans-serif"),  
    )


    return fig, df_territories[["US Territory / City","Potential Outbreaks"]]


def create_sankey_chart(df_outbreak):

    date_arr = df_outbreak.date.unique()

    date_latest = date_arr[-1]
    date_previous = date_arr[-2]

    date_previous_str = date_previous.strftime('%Y-%m-%d')
    date_latest_str = date_latest.strftime('%Y-%m-%d')

    week_1_data = df_outbreak[df_outbreak['date'] == date_previous]
    week_2_data = df_outbreak[df_outbreak['date'] == date_latest]
    potential_outbreaks_week_1 = week_1_data['potential_outbreak'].sum()  
    resolved_outbreaks_week_2 = week_2_data[(week_2_data.potential_outbreak_past_week==True)]['Potential_Outbreak_Resolved'].sum()  
    ongoing_outbreaks_week_2 = week_2_data[(week_2_data['potential_outbreak_past_week'] == True) & (week_2_data['potential_outbreak'] == True)].shape[0]


    labels = [
        f"Previous Week<br>Potential Outbreaks: {int(potential_outbreaks_week_1)}",
        f"Ongoing Outbreaks: {int(ongoing_outbreaks_week_2)}",       
        f"Current Week<br>Resolved Outbreaks: {int(resolved_outbreaks_week_2)}",
    ]

    # Adjusting source and target arrays based on the updated labels order
    source = [0, 0]  
    target = [1, 2]  
    value = [
        ongoing_outbreaks_week_2,  # From Potential to Ongoing
        resolved_outbreaks_week_2,  # From Potential to Resolved
    ]

    # Colors similar to the plotly reds colorscale used in map
    node_colors = [
        'rgb(222, 45, 38)',  # Virginia's lighter red for Potential Outbreaks
        'rgb(165, 10, 10)',  # Florida's darkest red for Ongoing Outbreaks
        'rgb(252, 187, 161)',  # North Carolina's very light red for Resolved Outbreaks
    ]

    # Link colors as intermediate colors closer to the node colors they connect to
    link_colors = [
        'rgb(203, 24, 29)',  # Arizona's red for the transition to "Ongoing Outbreaks"
        'rgb(251, 106, 74)',  # Colorado's light red for the transition to "Resolved Outbreaks"
    ]

    hover_colors = [
        'rgba(223, 54, 60, 0.8)',    # Brightened version of Arizona's red for link to Ongoing Outbreaks hover
        'rgba(251, 146, 114, 0.8)',  # Brightened version of Colorado's light red for link to Resolved Outbreaks hover
    ]
    
    node_customdata = [
        f"Potential Outbreaks: {int(potential_outbreaks_week_1)}",
        f"Ongoing Outbreaks: {int(ongoing_outbreaks_week_2)}",
        f"Resolved Outbreaks: {int(resolved_outbreaks_week_2)}",

    ]
    node_hovertemplate = '%{customdata}<extra></extra>'
    
    link_customdata = [
        "Transition to Ongoing",
        "Transition to Resolved"
    ]
    link_hovertemplate = '%{source.customdata} to %{target.customdata}<extra></extra>'


    fig = go.Figure(data=[go.Sankey(
        
        node=dict(
            pad=20,
            thickness=20,
        line=dict(color="rgba(50,50,50,0.5)", width=1), 
            label=labels,
            color=node_colors,
            customdata=node_customdata,
            hovertemplate=node_hovertemplate
        ),
        link=dict(
            arrowlen=15,    
            source=source,
            target=target,
            value=value,
            color=link_colors,
            hovercolor=hover_colors,
            customdata=link_customdata,
            hovertemplate=link_hovertemplate
            ))])

    fig.update_layout(
     title=dict(
        text=f"Ongoing Potential Outbreaks<br>previous week to current week",
        font=dict(size=22, color='white', family="Arial, bold"),
        
        x=0.5,  
        y=0.94,  
        xanchor='center',  
        yanchor='top'      
    ),
        font=dict(size=16, color='white'),
        paper_bgcolor='rgba(0,0,0,0.95)',
        plot_bgcolor='rgba(0,0,0,0.95)',
        #margin=dict(l=20, r=20, t=40, b=20), 
    )
    ongoing_outbreaks_table = week_2_data[(week_2_data.Potential_Outbreak_Resolved==False)][['state','label','new_cases']]
    ongoing_outbreaks_table = pd.merge(week_1_data[['state','label','new_cases']], ongoing_outbreaks_table, 
                                            on=['state','label'], how='inner',suffixes=['_previous','_latest'])
    ongoing_outbreaks_table = ongoing_outbreaks_table.sort_values('new_cases_latest',ascending=False)
    #print(ongoing_outbreaks_table.head())
    #print(ongoing_outbreaks_table_test.head(3))
    ongoing_outbreaks_table.columns = ['US State / Territory','Disease','Previous Week','Latest Week']
    return fig, ongoing_outbreaks_table, resolved_outbreaks_week_2