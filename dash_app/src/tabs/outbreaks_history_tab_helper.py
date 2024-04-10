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

    fig.add_trace(go.Scatter(x=df_aggregated['date'], y=df_aggregated[display_col],
                             mode='lines+markers',
                             name=primary_name))
    
    fig.update_traces(line=dict(color=primary_color, width=3),
                      marker=dict(color=primary_color),
                      selector=dict(name=primary_name))

    # Check if a secondary DataFrame is provided
    if df_secondary is not None and secondary_display_col is not None:
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
        xaxis_config['range'] = [min_date, df_aggregated['date'].max()]

    fig.update_layout(title=title,
                      xaxis=xaxis_config,
                      yaxis_title='Count',
                      xaxis_title='',
                      template="plotly_dark",
                      legend=dict(orientation='h', x=0.5, xanchor='center', y=-0.1, yanchor='top'))
 


    return fig
