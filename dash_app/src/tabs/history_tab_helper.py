import pandas as pd
import plotly.graph_objects as go

def plot_outbreak(df_historical_filtered, df_latest_filtered, df_preds_filtered, selected_state, selected_label):
    fig = go.Figure(layout_template="plotly_dark")

    pred_upper = None
    latest_actual_row = None

    # Keep actual line behavior the same
    df_historical_filtered = pd.concat([df_historical_filtered, df_latest_filtered])

    if not df_historical_filtered.empty:
        fig.add_trace(go.Scatter(
            x=df_historical_filtered['date'],
            y=df_historical_filtered['new_cases'],
            mode='lines+markers',
            name='Actual',
            line=dict(color='skyblue'),
            marker=dict(color='skyblue', size=5)
        ))

        # Fix: derive latest actual from the same combined actual dataframe
        df_actual_for_latest = df_historical_filtered.copy()
        df_actual_for_latest['date'] = pd.to_datetime(df_actual_for_latest['date'])
        df_actual_for_latest = df_actual_for_latest.dropna(subset=['new_cases']).sort_values('date')

        if not df_actual_for_latest.empty:
            latest_actual_row = df_actual_for_latest.iloc[-1]

    # Plot latest actual marker using the true latest actual row
    if latest_actual_row is not None:
        fig.add_trace(go.Scatter(
            x=[latest_actual_row['date']],
            y=[latest_actual_row['new_cases']],
            mode='markers',
            name='Latest Actual',
            marker=dict(color='#3CB371', size=13)
        ))

    # Plot predictions
    if not df_preds_filtered.empty:
        df_preds_filtered = df_preds_filtered.copy()
        df_preds_filtered['date'] = pd.to_datetime(df_preds_filtered['date'])
        df_preds_filtered = df_preds_filtered.sort_values('date')

        # Fix: use latest prediction row by date, not iloc[0]
        pred_row = df_preds_filtered.iloc[-1]

        pred_date = pred_row['date']
        pred_median = pred_row['pred_median']
        pred_mean = pred_row['pred_mean']
        pred_lower = pred_row['pred_lower']
        pred_upper = pred_row['pred_upper']

        fig.add_trace(go.Scatter(
            x=[pred_date],
            y=[pred_median],
            mode='markers',
            name='Model Median',
            marker=dict(color='rgb(222, 45, 38)', size=13)
        ))
        fig.add_trace(go.Scatter(
            x=[pred_date],
            y=[pred_median],
            mode='lines',
            name='Model Certainty Interval',
            line=dict(width=3),
            error_y=dict(
                type='data',
                thickness=3,
                symmetric=False,
                array=[pred_upper - pred_median],
                arrayminus=[pred_median - pred_lower]
            ),
            marker=dict(color='rgb(222, 45, 38)', size=13)
        ))

    # Handle potential outbreak using the true latest actual row
    if pred_upper is not None and latest_actual_row is not None and latest_actual_row['new_cases'] > pred_upper:
        outbreak_date = latest_actual_row['date']
        outbreak_cases = latest_actual_row['new_cases']
        fig.add_trace(go.Scatter(
            x=[outbreak_date],
            y=[outbreak_cases],
            mode='markers+text',
            name='Potential Outbreak',
            marker=dict(color='#DAA520', size=9, symbol='x', line=dict(color='#B22222', width=1.8)),
            text="Potential Outbreak",
            textposition="top center"
        ))

    # Empty data placeholders
    if df_historical_filtered.empty:
        fig.add_trace(go.Scatter(
            x=[None], y=[None], mode='lines', name='Actual',
            line=dict(color='skyblue'), visible='legendonly'
        ))
    if latest_actual_row is None:
        fig.add_trace(go.Scatter(
            x=[None], y=[None], mode='markers', name='Latest Actual',
            marker=dict(color='#98FF98', size=12), visible='legendonly'
        ))
    if df_preds_filtered.empty:
        fig.add_trace(go.Scatter(
            x=[None], y=[None], mode='markers', name='Model',
            marker=dict(color='darkred', size=12), visible='legendonly'
        ))
        fig.add_trace(go.Scatter(
            x=[None], y=[None], mode='lines', name='Model Certainty Interval',
            line=dict(color='red'), visible='legendonly'
        ))

    fig.update_layout(
        title=f"{selected_state}: {selected_label}",
        title_font=dict(size=22, color='white', family="Arial, sans-serif"),
        xaxis_title="",
        yaxis_title="Cases",
        paper_bgcolor='black',
        plot_bgcolor='black'
    )

    return fig