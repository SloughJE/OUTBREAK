import pandas as pd
from dash import html, dcc
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from html import escape
import textwrap

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

DISEASE_DISPLAY_NAMES = {
    (
        "Salmonellosis (excluding Salmonella Typhi infection "
        "and Salmonella Paratyphi infection)"
    ): "Non-typhoidal salmonellosis",

    (
        "Vibriosis (any species of the family Vibrionaceae, "
        "other than toxigenic Vibrio cholerae O1 or O139), Confirmed"
    ): "Vibriosis",

    "Q fever, Acute": "Q fever (acute)",
    "Q fever, Total": "Q fever (total)"
}


def get_disease_display_name(label):
    """
    Return a concise disease name for charts and tooltips,
    while leaving the original source label unchanged.
    """
    label = str(label).strip()

    return DISEASE_DISPLAY_NAMES.get(label, label)


def format_hover_disease_name(
    label,
    width=38,
    max_lines=2
):
    """
    Format a disease label for a compact Plotly tooltip.

    - Wraps at word boundaries.
    - Shows at most `max_lines`.
    - Adds an ellipsis when additional text is omitted.
    - Escapes HTML after wrapping.
    """
    text = get_disease_display_name(label).strip()

    wrapped_lines = textwrap.wrap(
        text,
        width=width,
        break_long_words=False,
        break_on_hyphens=False
    )

    if not wrapped_lines:
        return ""

    if len(wrapped_lines) <= max_lines:
        visible_lines = wrapped_lines
    else:
        # Preserve the initial lines, then compress everything
        # remaining into the final permitted line.
        visible_lines = wrapped_lines[:max_lines - 1]

        remaining_text = " ".join(
            wrapped_lines[max_lines - 1:]
        )

        final_line = textwrap.shorten(
            remaining_text,
            width=width,
            placeholder="…"
        )

        visible_lines.append(final_line)

    return "<br>".join(
        escape(line)
        for line in visible_lines
    )


def build_territory_table_tooltip(row):
    """
    Build Markdown tooltip content for a territory/city row.

    Assumes these columns are present:
      - US Territory / City
      - Potential Outbreaks
      - disease_details
    """
    location_name = str(
        row["US Territory / City"]
    ).title()

    outbreak_total = int(
        row["Potential Outbreaks"]
    )

    outbreak_word = (
        "outbreak"
        if outbreak_total == 1
        else "outbreaks"
    )

    disease_rows = row["disease_details"]

    lines = [
        f"**{location_name}**",
        "",
        f"**{outbreak_total:,} potential {outbreak_word}**"
    ]

    if disease_rows:
        lines.extend([
            "",
            "**Latest-week cases**",
            ""
        ])

        for item in disease_rows:
            disease_name = get_disease_display_name(
                item["disease"]
            )

            case_count = format_case_count(
                item["latest_cases"]
            )

            lines.append(
                f"- {disease_name}: **{case_count}**"
            )
    else:
        lines.extend([
            "",
            "No potential outbreaks."
        ])

    return "\n".join(lines)


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



def format_case_count(value):
    """Format case counts cleanly for tooltips."""
    if pd.isna(value):
        return "NA"

    value = float(value)

    if value.is_integer():
        return f"{int(value):,}"

    return f"{value:,.1f}"


def build_location_outbreak_summary(df_outbreak):
    """
    Create one row per state/territory for the latest week, including:
      - total number of potential outbreaks
      - diseases identified as potential outbreaks
      - latest-week case count for each disease
      - formatted Plotly hover text
    """
    date_wanted = df_outbreak["date"].max()

    latest = df_outbreak.loc[
        df_outbreak["date"].eq(date_wanted)
    ].copy()

    latest["potential_outbreak"] = (
        latest["potential_outbreak"]
        .fillna(False)
        .astype(bool)
    )

    latest["new_cases"] = pd.to_numeric(
        latest["new_cases"],
        errors="coerce"
    )

    # One total per state/territory.
    location_totals = (
        latest
        .groupby("state", as_index=False)["potential_outbreak"]
        .sum()
        .rename(
            columns={
                "potential_outbreak": "Potential Outbreaks"
            }
        )
    )

    # Disease-level details only for rows currently identified
    # as potential outbreaks.
    disease_details = (
        latest.loc[
            latest["potential_outbreak"],
            ["state", "label", "new_cases"]
        ]
        .groupby(
            ["state", "label"],
            as_index=False,
            dropna=False
        )["new_cases"]
        .sum(min_count=1)
        .sort_values(
            ["state", "new_cases", "label"],
            ascending=[True, False, True]
        )
    )

    details_by_location = {
        state: [
            {
                "disease": str(row["label"]),
                "latest_cases": row["new_cases"]
            }
            for _, row in group.iterrows()
        ]
        for state, group in disease_details.groupby(
            "state",
            sort=False
        )
    }

    location_totals["disease_details"] = (
        location_totals["state"]
        .map(details_by_location)
        .apply(lambda value: value if isinstance(value, list) else [])
    )

    location_totals["hover_text"] = location_totals.apply(
        make_plotly_hover,
        axis=1
    )

    return date_wanted, location_totals

def make_plotly_hover(row):
    state_name = escape(
        str(row["state"]).title()
    )

    outbreak_total = int(
        row["Potential Outbreaks"]
    )

    outbreak_word = (
        "outbreak"
        if outbreak_total == 1
        else "outbreaks"
    )

    disease_rows = row["disease_details"]

    if disease_rows:
        formatted_diseases = []

        for item in disease_rows:
            disease_name = format_hover_disease_name(
                item["disease"],
                width=38,
                max_lines=2
            )

            # Indent the second line of wrapped disease names.
            disease_name = disease_name.replace(
                "<br>",
                "<br>&nbsp;&nbsp;&nbsp;"
            )

            case_count = format_case_count(
                item["latest_cases"]
            )

            formatted_diseases.append(
                f"• {disease_name}: "
                f"<b>{case_count}</b>"
            )

        disease_text = "<br>".join(
            formatted_diseases
        )

    else:
        disease_text = "No potential outbreaks"

    return (
        f"<b>{state_name}</b>"
        f"<br><br>"
        f"<b>{outbreak_total:,} potential "
        f"{outbreak_word}</b>"
        f"<br><br>"
        f"<b>Latest-week cases</b>"
        f"<br><br>"
        f"{disease_text}"
    )


def create_us_map(df_outbreak):

    date_wanted, location_summary = (
        build_location_outbreak_summary(df_outbreak)
    )

    location_summary["state_code"] = (
        location_summary["state"].map(state_code_mapping)
    )

    territories = [
        "PR", "GU", "VI", "AS", "MP", "NYC"
    ]

    df_states = location_summary.loc[
        ~location_summary["state_code"].isin(territories)
        & location_summary["state_code"].notna()
    ].copy()

    df_territories = location_summary.loc[
        location_summary["state_code"].isin(territories)
    ].copy()

    df_territories = df_territories.rename(
        columns={
            "state": "US Territory / City"
        }
    )

    fig = go.Figure(
        data=go.Choropleth(
            locations=df_states["state_code"],
            z=df_states["Potential Outbreaks"].astype(float),
            locationmode="USA-states",
            colorscale="Reds",

            # The complete tooltip is stored as one custom-data value
            # for each state.
            customdata=df_states["hover_text"],

            # Suppresses Plotly's default state abbreviation and z value.
            hovertemplate="%{customdata}<extra></extra>",

            colorbar=dict(
                x=0.9,
                thickness=5,
                len=0.7
            )
        )
    )

    fig.update_layout(
        height=720,
        title=dict(
            text=("Potential Outbreaks by State")),        
        title_x=0.5,
        title_y=0.97,
        geo_scope="usa",
        paper_bgcolor="black",
        plot_bgcolor="black",
        template="plotly_dark",
        font=dict(
                size=22,
                color="white",
                family="Arial, sans-serif"
            ),
        hoverlabel=dict(
            align="left",
            bgcolor="#242424",
            bordercolor="#A8A8A8",
            font=dict(
                color="white",
                size=15,
                family="Arial, sans-serif"
            )
        ),

        geo=dict(
            landcolor="rgb(83, 83, 83)",
            lakecolor="rgb(32, 32, 32)",
            subunitcolor="rgb(100, 100, 100)",
            countrycolor="rgb(100, 100, 100)",
            bgcolor="rgb(0, 0, 0)"
        ),

        margin=dict(
            l=0,
            r=0,
            b=10,
            t=20
        ),

        title_font=dict(
            size=22,
            color="white",
            family="Arial, sans-serif"
        )
    )

    df_territories["_tooltip"] = df_territories.apply(
        build_territory_table_tooltip,
        axis=1
    )
    territory_output = df_territories[
        [
            "US Territory / City",
            "Potential Outbreaks",
            "_tooltip"
        ]
    ].copy()

    return fig, territory_output


NEW_SIGNAL_COLOR = "#FF7A00"
ONGOING_SIGNAL_COLOR = "#C6283D"
NO_LONGER_FLAGGED_COLOR = "#F7B399"


def create_sankey_chart(
    df_outbreak,
    selected_state=None,
    scope_label="United States"
):
    """
    Create the previous-week/current-week transition chart and
    unified latest-week signal table.

    Parameters
    ----------
    df_outbreak:
        Full historical outbreak-status DataFrame.

    selected_state:
        Optional uppercase source state name, such as "OHIO".
        The reporting dates are determined before this filter is
        applied so all views use the same latest reporting week.

    scope_label:
        Human-readable label used in the chart subtitle.

    Returns
    -------
    fig:
        Plotly transition figure.

    latest_week_signals_table:
        New and ongoing signals for the latest reporting week,
        optionally restricted to selected_state.

    no_longer_flagged:
        Number of preceding-week signals that are not flagged in
        the latest reporting week.
    """
    output_columns = [
        "US State / Territory",
        "Disease",
        "Status",
        "Previous Week",
        "Latest Week"
    ]

    empty_table = pd.DataFrame(
        columns=output_columns
    )

    def create_empty_figure(message):
        fig = go.Figure()

        fig.add_annotation(
            text=message,
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            align="center",
            font=dict(
                size=17,
                color="#D0D0D0"
            )
        )

        fig.update_layout(
            title=dict(
                text=(
                    "How Potential-Outbreak Signals "
                    "Changed This Week"
                    "<br>"
                    f"<span style='font-size:14px'>"
                    f"{scope_label}"
                    "</span>"
                ),
                x=0.5,
                xanchor="center",
                y=0.97,
                yanchor="top",
                font=dict(
                    size=20,
                    color="white",
                    family="Arial, sans-serif"
                )
            ),
            height=720,
            paper_bgcolor="black",
            plot_bgcolor="black",
            font=dict(
                color="white"
            ),
            margin=dict(
                l=55,
                r=20,
                t=75,
                b=40
            )
        )

        return fig

    if df_outbreak is None or df_outbreak.empty:
        return (
            create_empty_figure(
                "No reporting data are available."
            ),
            empty_table,
            0
        )

    data = df_outbreak.copy()

    data["date"] = pd.to_datetime(
        data["date"],
        errors="coerce"
    )

    data = data.dropna(
        subset=["date"]
    ).copy()

    reporting_dates = sorted(
        data["date"].unique()
    )

    if len(reporting_dates) < 2:
        return (
            create_empty_figure(
                "At least two reporting weeks are required."
            ),
            empty_table,
            0
        )

    # Choose dates from the complete dataset before state filtering.
    date_previous = pd.Timestamp(
        reporting_dates[-2]
    )

    date_latest = pd.Timestamp(
        reporting_dates[-1]
    )

    if selected_state:
        scoped_data = data.loc[
            data["state"].eq(selected_state)
        ].copy()
    else:
        scoped_data = data.copy()

    week_1_data = scoped_data.loc[
        scoped_data["date"].eq(date_previous)
    ].copy()

    week_2_data = scoped_data.loc[
        scoped_data["date"].eq(date_latest)
    ].copy()

    previous_total = int(
        week_1_data.get(
            "potential_outbreak",
            pd.Series(dtype=bool)
        )
        .fillna(False)
        .astype(bool)
        .sum()
    )

    current_flags = (
        week_2_data.get(
            "potential_outbreak",
            pd.Series(
                False,
                index=week_2_data.index,
                dtype=bool
            )
        )
        .fillna(False)
        .astype(bool)
    )

    previous_flags = (
        week_2_data.get(
            "potential_outbreak_past_week",
            pd.Series(
                False,
                index=week_2_data.index,
                dtype=bool
            )
        )
        .fillna(False)
        .astype(bool)
    )

    continuing_signals = int(
        (
            current_flags
            & previous_flags
        ).sum()
    )

    new_signals = int(
        (
            current_flags
            & ~previous_flags
        ).sum()
    )

    no_longer_flagged = max(
        previous_total - continuing_signals,
        0
    )

    current_total = int(
        current_flags.sum()
    )

    # ---------------------------------------------------------
    # Transition chart
    # ---------------------------------------------------------

    bar_width = 0.42
    maximum_total = max(
        previous_total,
        current_total,
        1
    )

    fig = go.Figure()

    # The same ongoing signals form the bottom of both bars.
    fig.add_trace(
        go.Bar(
            x=[0, 1],
            y=[
                continuing_signals,
                continuing_signals
            ],
            width=bar_width,
            name="Ongoing",
            marker_color=ONGOING_SIGNAL_COLOR,
            hovertemplate=(
                "%{customdata}"
                "<br>Ongoing: %{y:,} signals"
                "<extra></extra>"
            ),
            customdata=[
                "Previous week",
                "Current week"
            ]
        )
    )

    # Previous-week signals that are no longer flagged.
    fig.add_trace(
        go.Bar(
            x=[0],
            y=[no_longer_flagged],
            width=bar_width,
            name="No longer flagged",
            marker_color=NO_LONGER_FLAGGED_COLOR,
            text=[
                (
                    f"No longer flagged"
                    f"<br>{no_longer_flagged}"
                    if no_longer_flagged > 0
                    else ""
                )
            ],
            textfont=dict(
                size=14,
                color="#222222"
            ),
            textposition="inside",
            insidetextanchor="middle",
            hovertemplate=(
                "Previous week"
                "<br>No longer flagged: %{y:,} signals"
                "<extra></extra>"
            )
        )
    )

    # Latest-week signals newly entering the flagged group.
    fig.add_trace(
        go.Bar(
            x=[1],
            y=[new_signals],
            width=bar_width,
            name="New this week",
            marker_color=NEW_SIGNAL_COLOR,
            text=[
                (
                    f"New this week"
                    f"<br>{new_signals}"
                    if new_signals > 0
                    else ""
                )
            ],
            textfont=dict(
                size=14,
                color="white"
            ),
            textposition="inside",
            insidetextanchor="middle",
            hovertemplate=(
                "Current week"
                "<br>New this week: %{y:,} signals"
                "<extra></extra>"
            )
        )
    )

    # Add ongoing labels and connector only when ongoing signals exist.
    if continuing_signals > 0:
        ongoing_midpoint = (
            continuing_signals / 2
        )

        for x_position in [0, 1]:
            fig.add_annotation(
                x=x_position,
                y=ongoing_midpoint,
                text=(
                    f"Ongoing"
                    f"<br>{continuing_signals}"
                ),
                showarrow=False,
                align="center",
                font=dict(
                    color="white",
                    size=14
                )
            )

        fig.add_shape(
            type="line",
            xref="x",
            yref="y",
            x0=bar_width / 2,
            x1=1 - bar_width / 2,
            y0=continuing_signals,
            y1=continuing_signals,
            line=dict(
                color="rgba(255,255,255,0.75)",
                width=2,
                dash="dot"
            ),
            layer="above"
        )

        fig.add_annotation(
            x=0.5,
            y=continuing_signals,
            text=(
                f"Same {continuing_signals} "
                f"ongoing signals"
            ),
            showarrow=False,
            yshift=14,
            font=dict(
                color="#E0E0E0",
                size=13
            ),
            bgcolor="rgba(0,0,0,0.70)",
            borderpad=3
        )

    # Total labels remain visible even if a total is zero.
    fig.add_annotation(
        x=0,
        y=previous_total,
        text=f"Total: {previous_total}",
        showarrow=False,
        yanchor="bottom",
        yshift=6,
        font=dict(
            color="white",
            size=14
        )
    )

    fig.add_annotation(
        x=1,
        y=current_total,
        text=f"Total: {current_total}",
        showarrow=False,
        yanchor="bottom",
        yshift=6,
        font=dict(
            color="white",
            size=14
        )
    )

    if previous_total == 0 and current_total == 0:
        fig.add_annotation(
            x=0.5,
            y=0.5,
            xref="paper",
            yref="paper",
            text=(
                "No potential-outbreak signals were "
                "identified in either week."
            ),
            showarrow=False,
            font=dict(
                color="#D0D0D0",
                size=16
            )
        )

    fig.update_layout(
        barmode="stack",
        title=dict(
            text=(
                "How Potential-Outbreak Signals "
                "Changed This Week"
                "<br>"
                "<span style='font-size:14px'>"
                f"{scope_label}: "
                f"{previous_total} previous-week signals "
                f"→ {current_total} current-week signals"
                "</span>"
            ),
            x=0.5,
            xanchor="center",
            y=0.97,
            yanchor="top",
            font=dict(
                size=20,
                color="white",
                family="Arial, sans-serif"
            )
        ),
        height=720,
        paper_bgcolor="black",
        plot_bgcolor="black",
        font=dict(
            color="white",
            size=14
        ),
        showlegend=False,
        uniformtext_minsize=11,
        uniformtext_mode="hide",
        margin=dict(
            l=55,
            r=20,
            t=75,
            b=45
        ),
        xaxis=dict(
            title="",
            tickmode="array",
            tickvals=[0, 1],
            ticktext=[
                "Previous week",
                "Current week"
            ],
            tickfont=dict(
                size=14
            ),
            range=[
                -0.55,
                1.55
            ],
            showgrid=False,
            zeroline=False,
            fixedrange=True
        ),
        yaxis=dict(
            title=dict(
                text="Signals",
                font=dict(
                    size=14
                )
            ),
            tickfont=dict(
                size=13
            ),
            range=[
                0,
                maximum_total * 1.18
            ],
            showgrid=True,
            gridcolor=(
                "rgba(70, 90, 105, 0.35)"
            ),
            zeroline=False,
            fixedrange=True
        )
    )

    # ---------------------------------------------------------
    # Unified latest-week table
    # ---------------------------------------------------------

    if week_2_data.empty or not current_flags.any():
        return (
            fig,
            empty_table,
            no_longer_flagged
        )

    table_columns = [
        "item_id",
        "state",
        "label",
        "new_cases",
        "potential_outbreak_past_week"
    ]

    latest_week_signals_table = (
        week_2_data.loc[
            current_flags,
            table_columns
        ]
        .copy()
    )

    latest_week_signals_table[
        "Status"
    ] = (
        latest_week_signals_table[
            "potential_outbreak_past_week"
        ]
        .fillna(False)
        .astype(bool)
        .map({
            True: "Ongoing",
            False: "New"
        })
    )

    previous_week_cases = (
        week_1_data[
            [
                "item_id",
                "new_cases"
            ]
        ]
        .rename(
            columns={
                "new_cases": "Previous Week"
            }
        )
    )

    latest_week_signals_table = (
        latest_week_signals_table
        .merge(
            previous_week_cases,
            on="item_id",
            how="left"
        )
        .rename(
            columns={
                "state": "US State / Territory",
                "label": "Disease",
                "new_cases": "Latest Week"
            }
        )
    )

    latest_week_signals_table[
        "_status_order"
    ] = (
        latest_week_signals_table["Status"]
        .map({
            "New": 0,
            "Ongoing": 1
        })
    )

    latest_week_signals_table[
        "_latest_sort"
    ] = pd.to_numeric(
        latest_week_signals_table[
            "Latest Week"
        ],
        errors="coerce"
    )

    latest_week_signals_table = (
        latest_week_signals_table
        .sort_values(
            [
                "_status_order",
                "_latest_sort"
            ],
            ascending=[
                True,
                False
            ],
            na_position="last"
        )
        .copy()
    )

    for column in [
        "Previous Week",
        "Latest Week"
    ]:
        converted_values = [
            (
                None
                if pd.isna(value)
                else int(round(value))
            )
            for value in (
                latest_week_signals_table[
                    column
                ]
            )
        ]

        latest_week_signals_table[
            column
        ] = pd.Series(
            converted_values,
            index=(
                latest_week_signals_table.index
            ),
            dtype="object"
        )

    latest_week_signals_table = (
        latest_week_signals_table[
            output_columns
        ]
        .reset_index(drop=True)
    )

    return (
        fig,
        latest_week_signals_table,
        no_longer_flagged
    )