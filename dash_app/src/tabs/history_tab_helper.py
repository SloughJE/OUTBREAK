import pandas as pd
import plotly.graph_objects as go

def plot_outbreak(df_historical_filtered, df_latest_filtered, df_preds_filtered, selected_state, selected_label):
    fig = go.Figure(layout_template="plotly_dark")

    pred_upper = None
    latest_actual_row = None

    # Combine actuals, then sort by date so the line does not go backward in time
    df_historical_filtered = pd.concat([df_historical_filtered, df_latest_filtered], ignore_index=True)

    if not df_historical_filtered.empty:
        df_historical_filtered = df_historical_filtered.copy()
        df_historical_filtered["date"] = pd.to_datetime(df_historical_filtered["date"])
        df_historical_filtered = (
            df_historical_filtered
            .sort_values("date")
            .drop_duplicates(subset=["date"], keep="last")
        )

        fig.add_trace(go.Scatter(
            x=df_historical_filtered['date'],
            y=df_historical_filtered['new_cases'],
            mode='lines+markers',
            name='Actual',
            line=dict(color='skyblue'),
            marker=dict(color='skyblue', size=5)
        ))

        # Latest actual should come from the same sorted actual dataframe
        df_actual_for_latest = df_historical_filtered.dropna(subset=['new_cases'])
        if not df_actual_for_latest.empty:
            latest_actual_row = df_actual_for_latest.iloc[-1]

    # Plot latest actual marker
    if latest_actual_row is not None:
        fig.add_trace(go.Scatter(
            x=[latest_actual_row['date']],
            y=[latest_actual_row['new_cases']],
            mode='markers',
            name='Latest Actual',
            marker=dict(color='#3CB371', size=13)
        ))

    # Plot predictions using the latest prediction row by date
    if not df_preds_filtered.empty:
        df_preds_filtered = df_preds_filtered.copy()
        df_preds_filtered['date'] = pd.to_datetime(df_preds_filtered['date'])
        df_preds_filtered = df_preds_filtered.sort_values('date')
        pred_row = df_preds_filtered.iloc[-1]

        pred_date = pred_row['date']
        pred_median = pred_row['pred_median']
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

    # Potential outbreak marker
    if pred_upper is not None and latest_actual_row is not None and latest_actual_row['new_cases'] > pred_upper:
        fig.add_trace(go.Scatter(
            x=[latest_actual_row['date']],
            y=[latest_actual_row['new_cases']],
            mode='markers+text',
            name='Potential Outbreak',
            marker=dict(color='#DAA520', size=9, symbol='x', line=dict(color='#B22222', width=1.8)),
            text="Potential Outbreak",
            textposition="top center"
        ))

    # Empty placeholders
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


def summarize_history_period(df_outbreak_history, weeks):
    """
    Summarize one state-disease time series over the selected
    number of calendar weeks.

    Returns:
      - period_start
      - period_end
      - total_cases
      - flagged_weeks
      - episodes_started
      - peak_weekly_cases
    """
    if df_outbreak_history.empty:
        return None

    history = (
        df_outbreak_history
        .sort_values("date")
        .copy()
    )

    history["date"] = pd.to_datetime(history["date"])
    history["new_cases"] = pd.to_numeric(
        history["new_cases"],
        errors="coerce"
    )

    history["potential_outbreak"] = (
        history["potential_outbreak"]
        .fillna(False)
        .astype(bool)
    )

    period_end = history["date"].max()

    # Subtract 11 weeks for a 12-week inclusive window,
    # 25 weeks for a 26-week window, etc.
    period_start = period_end - pd.Timedelta(
        weeks=weeks - 1
    )

    period_data = history.loc[
        history["date"].between(
            period_start,
            period_end
        )
    ].copy()

    period_data = period_data.loc[
        period_data["new_cases"].notna()
    ].copy()

    if period_data.empty:
        return None

    # Determine whether the first flagged week in the displayed
    # period continued an episode that began before the window.
    preceding_rows = history.loc[
        history["date"] < period_start
    ]

    if preceding_rows.empty:
        previous_flag = False
    else:
        previous_flag = bool(
            preceding_rows.iloc[-1]["potential_outbreak"]
        )

    flags = period_data["potential_outbreak"]

    episode_starts = (
        flags
        & ~flags.shift(
            1,
            fill_value=previous_flag
        )
    )

    return {
        "period_start": period_start,
        "period_end": period_end,
        "total_cases": int(
            period_data["new_cases"].sum()
        ),
        "flagged_weeks": int(flags.sum()),
        "episodes_started": int(
            episode_starts.sum()
        ),
        "peak_weekly_cases": int(
            period_data["new_cases"].max()
        ),
    }