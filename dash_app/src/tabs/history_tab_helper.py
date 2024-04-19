import pandas as pd
import plotly.graph_objects as go

def plot_outbreak(df_historical_filtered, df_latest_filtered, df_preds_filtered, selected_state, selected_label):
    fig = go.Figure(layout_template="plotly_dark")
    
    pred_upper = None

    # Plot historical data
    df_historical_filtered = pd.concat([df_historical_filtered,df_latest_filtered])

    if not df_historical_filtered.empty:
        fig.add_trace(go.Scatter(
            x=df_historical_filtered['date'], 
            y=df_historical_filtered['new_cases'], 
            mode='lines+markers',
            name='Actual',
            line=dict(color='skyblue'),
            marker=dict(color='skyblue', size=5)
        ))
    # Plot latest data
    if not df_latest_filtered.empty:
        fig.add_trace(go.Scatter(x=df_latest_filtered['date'], y=df_latest_filtered['new_cases'], mode='markers', name='Latest Actual', marker=dict(color='#3CB371', size=13)))

    # Plot predictions
    if not df_preds_filtered.empty:
        pred_date = df_preds_filtered['date'].iloc[0]
        pred_median = df_preds_filtered['pred_median'].iloc[0]
        pred_mean = df_preds_filtered['pred_mean'].iloc[0]
        pred_lower = df_preds_filtered['pred_lower'].iloc[0]
        pred_upper = df_preds_filtered['pred_upper'].iloc[0]
        
        
        #fig.add_trace(go.Scatter(x=[pred_date], y=[pred_mean], mode='markers', name='Model Mean', marker=dict(color='#FF6347', size=12)))
        fig.add_trace(go.Scatter(x=[pred_date], y=[pred_median], mode='markers', name='Model Median', marker=dict(color='rgb(222, 45, 38)', size=13)))
        fig.add_trace(go.Scatter(x=[pred_date], y=[pred_median], mode='lines', name='Model Certainty Interval', line=dict(width=3),
            error_y=dict(type='data', thickness=3, symmetric=False, array=[pred_upper - pred_median], arrayminus=[pred_median - pred_lower]), marker=dict(color='rgb(222, 45, 38)', size=13)))

    # Handle potential outbreak
    if pred_upper is not None and not df_latest_filtered.empty and df_latest_filtered['new_cases'].iloc[0] > pred_upper:
        outbreak_date = df_latest_filtered['date'].iloc[0]
        outbreak_cases = df_latest_filtered['new_cases'].iloc[0]
        fig.add_trace(go.Scatter(x=[outbreak_date], y=[outbreak_cases], mode='markers+text', 
            name='Potential Outbreak', marker=dict(color='#DAA520', size=9, symbol='x', line=dict(color='#B22222', width=1.8)), text="Potential Outbreak", textposition="top center"))

    # Empty data placeholders
    if df_historical_filtered.empty:
        fig.add_trace(go.Scatter(x=[None], y=[None], mode='lines', name='Actual',
                                 line=dict(color='skyblue'), visible='legendonly'))
    if df_latest_filtered.empty:
        fig.add_trace(go.Scatter(x=[None], y=[None], mode='markers', name='Latest Actual',
                                 marker=dict(color='#98FF98', size=12), visible='legendonly'))
    if df_preds_filtered.empty:
        fig.add_trace(go.Scatter(x=[None], y=[None], mode='markers', name='Model',
                                 marker=dict(color='darkred', size=12), visible='legendonly'))
        fig.add_trace(go.Scatter(x=[None], y=[None], mode='lines', name='Model Certainty Interval',
                                 line=dict(color='red'), visible='legendonly'))

    # Update layout
    fig.update_layout(title=f"{selected_state}: {selected_label}", xaxis_title="", yaxis_title="Cases")

    return fig
