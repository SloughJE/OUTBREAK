import pandas as pd
import plotly.graph_objects as go


def plot_outbreak(df_historical_filtered, df_latest_filtered, df_preds_filtered, selected_state, selected_label):
    
    fig = go.Figure(layout_template="plotly_dark")
    
    pred_upper = None

    if not df_historical_filtered.empty:
        fig.add_trace(go.Scatter(
            x=df_historical_filtered['date'], 
            y=df_historical_filtered['new_cases'], 
            mode='lines+markers',
            name='Historical',
            line=dict(color='skyblue'),
            marker=dict(  
                color='skyblue',
                size=5
            )
        ))


    if not df_preds_filtered.empty:
        pred_date = df_preds_filtered['date'].iloc[0]
        pred_median = df_preds_filtered['pred_median'].iloc[0]
        pred_mean = df_preds_filtered['pred_mean'].iloc[0]
        pred_lower = df_preds_filtered['pred_lower'].iloc[0]
        pred_upper = df_preds_filtered['pred_upper'].iloc[0]
        
        fig.add_trace(go.Scatter(x=[pred_date], y=[pred_median], mode='lines', name='Prediction Interval', 
            error_y=dict(type='data', symmetric=False, array=[pred_upper - pred_median], arrayminus=[pred_median - pred_lower]), marker=dict(color='#a50a0a', size=12)))
        fig.add_trace(go.Scatter(x=[pred_date], y=[pred_mean], mode='markers', name='Prediction Mean', marker=dict(color='#FF6347', size=12)))
        fig.add_trace(go.Scatter(x=[pred_date], y=[pred_median], mode='markers', name='Prediction Median', marker=dict(color='#a50a0a', size=12)))

    if not df_latest_filtered.empty:
        fig.add_trace(go.Scatter(x=df_latest_filtered['date'], y=df_latest_filtered['new_cases'], mode='markers', name='Latest', marker=dict(color='#3CB371', size=12)))

    if pred_upper is not None and not df_latest_filtered.empty and df_latest_filtered['new_cases'].iloc[0] > pred_upper:
        outbreak_date = df_latest_filtered['date'].iloc[0]
        outbreak_cases = df_latest_filtered['new_cases'].iloc[0]
        fig.add_trace(go.Scatter(x=[outbreak_date], y=[outbreak_cases], mode='markers+text', 
            name='Potential Outbreak', marker=dict(color='#DAA520', size=15, symbol='x', line=dict(color='#B22222', width=2)), text="Potential Outbreak", textposition="top center"))
    else:
        fig.add_trace(go.Scatter(x=[None], y=[None], mode='markers+text', name='Potential Outbreak',
                         marker=dict(color='#DAA520', size=15, symbol='x', line=dict(color='#800000', width=2)),
                         text="Potential Outbreak", textposition="top center", visible='legendonly'))


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