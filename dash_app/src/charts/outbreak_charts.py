import pandas as pd
import plotly.graph_objects as go


def plot_outbreak(df_historical_filtered, df_latest_filtered, df_preds_filtered, selected_state, selected_label):
    

    fig = go.Figure(layout_template="plotly_dark")
    
    # Initialize pred_upper with a default value
    pred_upper = None
    
    # Filter datasets for the selected item_id
    #df_historical_filtered = df_historical_chart[df_historical_chart['item_id'] == selected_item_id]
    #df_latest_filtered = df_latest_chart[df_latest_chart['item_id'] == selected_item_id]
    #df_preds_filtered = df_preds_chart[df_preds_chart['item_id'] == selected_item_id]

    # Plot historical data if available
    if not df_historical_filtered.empty:
        fig.add_trace(go.Scatter(x=df_historical_filtered['date'], y=df_historical_filtered['new_cases'], mode='lines', name='Historical', line=dict(color='skyblue')))

    # Plot prediction data if available
    if not df_preds_filtered.empty:
        pred_date = df_preds_filtered['date'].iloc[0]
        pred_mean = df_preds_filtered['pred_mean'].iloc[0]
        pred_lower = df_preds_filtered['pred_lower'].iloc[0]
        pred_upper = df_preds_filtered['pred_upper'].iloc[0]
        
        # Include error bars for the prediction interval
        fig.add_trace(go.Scatter(x=[pred_date], y=[pred_mean], mode='lines', name='Prediction Interval', 
            error_y=dict(type='data', symmetric=False, array=[pred_upper - pred_mean], arrayminus=[pred_mean - pred_lower]), marker=dict(color='#FF6347', size=12)))
        fig.add_trace(go.Scatter(x=[pred_date], y=[pred_mean], mode='markers', name='Prediction', marker=dict(color='#FF6347', size=12)))

    # Plot latest data if available
    if not df_latest_filtered.empty:
        fig.add_trace(go.Scatter(x=df_latest_filtered['date'], y=df_latest_filtered['new_cases'], mode='markers', name='Latest', marker=dict(color='#3CB371', size=12)))

    # Check for potential outbreak and update marker if present
    if pred_upper is not None and not df_latest_filtered.empty and df_latest_filtered['new_cases'].iloc[0] > pred_upper:
        outbreak_date = df_latest_filtered['date'].iloc[0]
        outbreak_cases = df_latest_filtered['new_cases'].iloc[0]
        fig.add_trace(go.Scatter(x=[outbreak_date], y=[outbreak_cases], mode='markers+text', 
            name='Potential Outbreak', marker=dict(color='yellow', size=15, symbol='x', line=dict(color='#B22222', width=2)), text="Potential Outbreak", textposition="top center"))
    else:
        fig.add_trace(go.Scatter(x=[None], y=[None], mode='markers+text', name='Potential Outbreak',
                         marker=dict(color='#DAA520', size=15, symbol='x', line=dict(color='#800000', width=2)),
                         text="Potential Outbreak", textposition="top center", visible='legendonly'))

    # Add legend-only traces to ensure all possible data representations are covered in the legend
    if df_historical_filtered.empty:
        fig.add_trace(go.Scatter(x=[None], y=[None], mode='lines', name='Historical',
                                 line=dict(color='skyblue'), visible='legendonly'))
    if df_latest_filtered.empty:
        fig.add_trace(go.Scatter(x=[None], y=[None], mode='markers', name='Latest',
                                 marker=dict(color='#98FF98', size=12), visible='legendonly'))
    if df_preds_filtered.empty:
        fig.add_trace(go.Scatter(x=[None], y=[None], mode='markers', name='Prediction',
                                 marker=dict(color='darkred', size=12), visible='legendonly'))
        fig.add_trace(go.Scatter(x=[None], y=[None], mode='lines', name='Prediction Interval',
                                 line=dict(color='red'), visible='legendonly'))


    fig.update_layout(title=f"{selected_state}: {selected_label}", xaxis_title="Date", yaxis_title="New Cases")

    return fig