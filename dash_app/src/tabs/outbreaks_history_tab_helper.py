import pandas as pd
import plotly.graph_objects as go


def agg_outbreak_counts(df, condition='potential_outbreak'):


    if df.empty:
        return df
    
    min_date = df['date'].min()
    max_date = df['date'].max()


    if condition=='potential_outbreak':
        df_outbreak_counts = df[df.potential_outbreak==True].copy()
    elif condition=='ongoing_outbreaks':
        df_outbreak_counts = df[(df['potential_outbreak']) & (df['potential_outbreak_past_week'])].copy()
        df_outbreak_counts = df_outbreak_counts[df_outbreak_counts['date']>min_date]
        min_date = df_outbreak_counts['date'].min()
    elif condition=='resolved_outbreaks':
        df_outbreak_counts = df[(df['potential_outbreak']==False) & (df['potential_outbreak_past_week']==True)].copy()
        # need to remove the first date here, as it will always be 0 for resolved as we need one week of previous data
        df_outbreak_counts = df_outbreak_counts[df_outbreak_counts['date']>min_date]
        min_date = df_outbreak_counts['date'].min()

    if df_outbreak_counts.empty:
        return df_outbreak_counts
    
    all_week_starts = pd.date_range(start=min_date - pd.to_timedelta(min_date.dayofweek, unit='d'),
                                    end=max_date, freq='7D')
    df_all_weeks = pd.DataFrame(all_week_starts, columns=['date'])

    if df_outbreak_counts.empty:
        print("No data with 'potential_outbreak' as True.")
    else:

        df_outbreak_counts['date'] = df_outbreak_counts['date'] - pd.to_timedelta(df_outbreak_counts['date'].dt.dayofweek, unit='d')

        weekly_counts = df_outbreak_counts.groupby('date').size().reset_index(name='count')
        df_all_weeks = pd.merge(df_all_weeks, weekly_counts, on='date', how='left').fillna(0)

    df_all_weeks['count'] = df_all_weeks['count'].astype(int)
    df_all_weeks['cumulative_count'] = df_all_weeks['count'].cumsum()

    return df_all_weeks


def plot_time_series(df_aggregated, title="Time Series of Counts", display_col='count', primary_name = 'potential outbreaks', primary_color = '#DE2D26', 
                     df_secondary=None, secondary_display_col=None, secondary_name=None, min_date=None):
    """
    Plots the time series from the aggregated DataFrame using Plotly with a dark theme. Optionally includes a second DataFrame.

    Args:
    - df_aggregated: Aggregated DataFrame with the date and count columns for the primary data.
    - title: Title of the plot.
    - display_col: Column name in the primary DataFrame to display.
    - df_secondary: Optional. A secondary DataFrame to plot on the same chart.
    - secondary_display_col: Optional. Column name in the secondary DataFrame to display.
    - secondary_name: Optional. Name for the secondary data trace.

    Returns:
    - Plotly Figure
    """
    fig = go.Figure()

    if df_aggregated.empty:

        fig.add_annotation(text=f"No {primary_name}",
                           xref="paper", yref="paper",
                           x=0.5, y=0.5, showarrow=False,
                           font=dict(size=20, color="white"))
        fig.update_layout(template="plotly_dark")
        return fig

    # Primary dataset
    # potential: #DE2D26
    # resolved: #FCBBA1
    # ongoing: #A50A0A
    df_aggregated = df_aggregated[df_aggregated['date']!=pd.to_datetime('2024-02-26')]

    fig.add_trace(go.Scatter(x=df_aggregated['date'], y=df_aggregated[display_col],
                             mode='lines+markers',
                             name=primary_name))
    
    fig.update_traces(line=dict(color=primary_color, width=3),
                      marker=dict(color=primary_color),
                      selector=dict(name=primary_name))

    # Check if a secondary DataFrame is provided
    if df_secondary is not None and secondary_display_col is not None:
        df_secondary = df_secondary[df_secondary['date']!=pd.to_datetime('2024-02-26')]

        fig.add_trace(go.Scatter(x=df_secondary['date'], y=df_secondary[secondary_display_col],
                                 mode='lines+markers',
                                 name=secondary_name))
        
        fig.update_traces(line=dict(color='#FCBBA1', width=3),
                          marker=dict(color='#FCBBA1'),
                          selector=dict(name=secondary_name))

    xaxis_config = {
        'title': 'Date',
        'type': 'date'
    }
    if min_date is not None:
        start_date = pd.to_datetime(min_date) - pd.Timedelta(hours=12)
        end_date = pd.to_datetime(df_aggregated['date'].max()) + pd.Timedelta(hours=12)
        xaxis_config['range'] = [start_date, end_date]

    fig.update_layout(title=title,
                    title_font=dict(size=22, color='white', family="Arial, sans-serif"),  
                    xaxis=xaxis_config,
                    yaxis_title='Count',
                    xaxis_title='',
                    template="plotly_dark",
                    paper_bgcolor='black',
                    plot_bgcolor='black',
                    legend=dict(orientation='h', x=0.5, xanchor='center', y=-0.1, yanchor='top'))
 


    return fig


def agg_new_episode_counts(
    df_outbreak_history,
    max_gap_days=8
):
    """
    Count new potential-outbreak episodes by reporting week.

    A new episode begins when:
      1. a state-disease series is flagged after not being flagged, or
      2. a flagged observation follows a gap longer than max_gap_days.

    Returns one row for every reporting date, including dates with
    zero new episodes.
    """
    output_columns = [
        "date",
        "new_episodes",
        "rolling_4_week"
    ]

    if df_outbreak_history.empty:
        return pd.DataFrame(columns=output_columns)

    data = df_outbreak_history.copy()

    data["date"] = pd.to_datetime(
        data["date"],
        errors="coerce"
    )

    data["potential_outbreak"] = (
        data["potential_outbreak"]
        .fillna(False)
        .astype(bool)
    )

    data = (
        data
        .dropna(subset=["item_id", "date"])
        .sort_values(["item_id", "date"])
        .copy()
    )

    if data.empty:
        return pd.DataFrame(columns=output_columns)

    # Preserve every reporting date so weeks with no new episodes
    # appear as zero rather than disappearing from the chart.
    all_dates = pd.DataFrame({
        "date": sorted(data["date"].unique())
    })

    previous_flag = (
        data
        .groupby("item_id")["potential_outbreak"]
        .shift(1)
    )

    previous_date = (
        data
        .groupby("item_id")["date"]
        .shift(1)
    )

    gap_break = (
        data["date"] - previous_date
    ).gt(
        pd.Timedelta(days=max_gap_days)
    )

    data["episode_start"] = (
        data["potential_outbreak"]
        & (
            ~previous_flag.eq(True)
            | gap_break
        )
    )

    weekly_counts = (
        data
        .groupby("date", as_index=False)["episode_start"]
        .sum()
        .rename(
            columns={
                "episode_start": "new_episodes"
            }
        )
    )

    weekly_counts = all_dates.merge(
        weekly_counts,
        on="date",
        how="left"
    )

    weekly_counts["new_episodes"] = (
        weekly_counts["new_episodes"]
        .fillna(0)
        .astype(int)
    )

    weekly_counts["rolling_4_week"] = (
        weekly_counts["new_episodes"]
        .rolling(
            window=4,
            min_periods=1
        )
        .mean()
    )

    return weekly_counts[output_columns]


def plot_new_episode_trends(df_weekly):
    """
    Plot weekly new potential-outbreak episodes and their
    four-week rolling average.
    """
    fig = go.Figure()

    if df_weekly.empty:
        fig.update_layout(
            title="New Potential-Outbreak Episodes by Week",
            template="plotly_dark",
            paper_bgcolor="black",
            plot_bgcolor="black"
        )

        return fig

    fig.add_trace(
        go.Bar(
            x=df_weekly["date"],
            y=df_weekly["new_episodes"],
            name="New episodes",
            marker_color="#DE2D26",
            opacity=0.85,
            customdata=df_weekly[
                ["rolling_4_week"]
            ],
            hovertemplate=(
                "<b>%{x|%Y-%m-%d}</b>"
                "<br>New episodes: %{y:,}"
                "<br>4-week average: "
                "%{customdata[0]:.1f}"
                "<extra></extra>"
            )
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df_weekly["date"],
            y=df_weekly["rolling_4_week"],
            name="4-week average",
            mode="lines",
            line=dict(
                color="#FCAE91",
                width=3
            ),
            hovertemplate=(
                "<b>%{x|%Y-%m-%d}</b>"
                "<br>4-week average: %{y:.1f}"
                "<extra></extra>"
            )
        )
    )

    fig.update_layout(
        title=dict(
            text="New Potential-Outbreak Episodes by Week",
            x=0.055,
            xanchor="left",
            font=dict(
                size=20,
                color="white"
            )
        ),
        template="plotly_dark",
        paper_bgcolor="black",
        plot_bgcolor="black",
        font=dict(
            color="white"
        ),
        hovermode="x unified",
        bargap=0.25,
        legend=dict(
            orientation="h",
            x=0.5,
            xanchor="center",
            y=-0.15,
            yanchor="top"
        ),
        xaxis=dict(
            title=None,
            showgrid=True,
            gridcolor="rgba(70, 90, 105, 0.45)"
        ),
        yaxis=dict(
            title="New episodes",
            rangemode="tozero",
            showgrid=True,
            gridcolor="rgba(70, 90, 105, 0.45)"
        ),
        margin=dict(
            l=70,
            r=35,
            t=75,
            b=70
        )
    )

    return fig