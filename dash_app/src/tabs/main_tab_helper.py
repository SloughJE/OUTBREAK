import pandas as pd
from dash import html, dcc
import dash_bootstrap_components as dbc


outbreak_uncertainty_level_explanation = """• Indicates how certain we want to be in identifying a "potential outbreak"
• Corresponds to the model prediction interval
• The model forecasts by predicting distributions of values for the future time period, reflecting the probable range of outcome values.
• If the actual value for the current week is greater than the upper prediction interval value from last week's prediction, we label it as an "outbreak".
• A higher "Outbreak Model Certainty Level" yields a higher threshold value, and is therefore less like to identify a new value as an "outbreak".
• Example: 99% means we use the 99th percentile of the predicted distribution values as the threshold for identifying an "outbreak".

- Model accuracy is contingent upon the quality and completeness of the training data. Sparse or missing data for specific time series may adversely affect predictions and identification of "outbreaks".
- Please note, the designation of values as "outbreaks" is solely for the purpose of entertainment and does not carry any official public health significance. It is a predictive tool intended for informational use only and should not be construed as medical or health advice.
"""


info_icon = html.I(className="bi bi-info-circle", id="outbreak-uncertainty-tooltip-target", 
                   style={
                       'cursor': 'pointer', 
                        'font-size': '22px', 
                        'marginLeft': '10px',
                        'textAlign': 'left',

                        })

label_and_info = html.H2(
    ["Outbreak Model Certainty Level", info_icon],
    style={
        'color': 'white',
        'textAlign': 'center',
        'fontSize': '24px',
        'margin': '20px',
    }
)
uncertainty_level_tooltip = dbc.Tooltip(
    outbreak_uncertainty_level_explanation,
    target="outbreak-uncertainty-tooltip-target",
    placement="right",
    className='custom-tooltip',    
    style={'white-space': 'pre-line'}
)


def preds_to_long(df):

    quantile_mapping = {
        'pred_lower_0_001': 'Lower 99.9%',
        'pred_upper_0_999': 'Upper 99.9%',
        'pred_lower_0_01': 'Lower 99%',
        'pred_upper_0_99': 'Upper 99%',
        'pred_lower_0_03': 'Lower 97%',
        'pred_upper_0_97': 'Upper 97%',
        'pred_lower_0_05': 'Lower 95%',
        'pred_upper_0_95': 'Upper 95%',
        'pred_lower_0_1': 'Lower 90%',
        'pred_upper_0_9': 'Upper 90%',
        'pred_lower_0_2': 'Lower 80%',
        'pred_upper_0_8': 'Upper 80%',
    }
    # Assuming 'df' is your initial DataFrame
    long_df = pd.melt(df, 
                    id_vars=['item_id', 'date', 'state', 'label'], 
                    var_name='quantile', 
                    value_name='value')

    # Apply the quantile mapping to the 'quantile' column
    long_df['quantile'] = long_df['quantile'].map(quantile_mapping).fillna(long_df['quantile'])

    # For 'pred_mean' and 'pred_median', you might want to handle them separately
    # as they do not fit directly into the 'Lower xx%' or 'Upper xx%' pattern
    long_df['quantile'] = long_df['quantile'].replace({
        'pred_mean': 'Mean',
        'pred_median': 'Median'
    })

    return long_df

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

def back_to_wide(df):
    
    wide_df = df.pivot(index=['item_id', 'date', 'state', 'label'], 
                                columns='quantile', 
                                values='value').reset_index()

    # Reset the column names from multi-level to single level for easier manipulation
    wide_df.columns.name = None

    # Dynamically find and rename the columns based on their 'Lower xx%' and 'Upper xx%' pattern
    for col in wide_df.columns:
        if col.startswith('Lower'):
            wide_df.rename(columns={col: 'pred_lower'}, inplace=True)
        elif col.startswith('Upper'):
            wide_df.rename(columns={col: 'pred_upper'}, inplace=True)
        elif col == 'Mean':
            wide_df.rename(columns={col: 'pred_mean'}, inplace=True)
        elif col == 'Median':
            wide_df.rename(columns={col: 'pred_median'}, inplace=True)

    return wide_df

def identify_outbreaks(df_pred_wide, df_latest):
    df_outbreak = pd.merge(df_pred_wide, df_latest,on=['item_id','date','state','label'], how='left')
    df_outbreak['potential_outbreak'] = df_outbreak['new_cases'] > df_outbreak['pred_upper']
    return df_outbreak

def get_outbreaks(df_preds, df_latest, chosen_interval=99):

    df_preds_long = preds_to_long(df_preds)
    filtered_df = filter_prediction_interval(df_preds_long, chosen_interval)
    df_pred_wide = back_to_wide(filtered_df)
    df_outbreak = identify_outbreaks(df_pred_wide, df_latest)

    return df_outbreak
