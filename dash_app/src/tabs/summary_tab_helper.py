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


def create_sankey_chart(df_outbreak):

    date_arr = df_outbreak.date.unique()

    date_latest = date_arr[-1]
    date_previous = date_arr[-2]

    date_previous_str = date_previous.strftime('%Y-%m-%d')
    date_latest_str = date_latest.strftime('%Y-%m-%d')

    week_1_data = df_outbreak[df_outbreak['date'] == date_previous]
    week_2_data = df_outbreak[df_outbreak['date'] == date_latest]


    # ------------------------------------------------------------
    # Weekly signal transition counts
    # ------------------------------------------------------------

    previous_total = int(
        week_1_data["potential_outbreak"]
        .fillna(False)
        .sum()
    )

    current_flags = (
        week_2_data["potential_outbreak"]
        .fillna(False)
        .astype(bool)
    )

    previous_flags = (
        week_2_data["potential_outbreak_past_week"]
        .fillna(False)
        .astype(bool)
    )

    continuing_signals = int(
        (current_flags & previous_flags).sum()
    )

    new_signals = int(
        (current_flags & ~previous_flags).sum()
    )

    no_longer_flagged = max(
        previous_total - continuing_signals,
        0
    )

    current_total = int(current_flags.sum())

# ------------------------------------------------------------
# Two-period stacked transition chart
# ------------------------------------------------------------

    bar_width = 0.42
    ongoing_midpoint = continuing_signals / 2

    fig = go.Figure()

    # Same ongoing signals form the bottom of both bars.
    fig.add_trace(
        go.Bar(
            x=[0, 1],
            y=[continuing_signals, continuing_signals],
            width=bar_width,
            name="Ongoing",
            marker_color="#CB181D",
            hovertemplate=(
                "%{customdata}<br>"
                f"Ongoing: {continuing_signals} signals"
                "<extra></extra>"
            ),
            customdata=[
                "Previous week",
                "Latest week"
            ]
        )
    )

    # Previous-week signals that did not continue.
    fig.add_trace(
        go.Bar(
            x=[0],
            y=[no_longer_flagged],
            width=bar_width,
            name="No longer flagged",
            marker_color="#FCBBA1",
            text=[f"No longer flagged<br>{no_longer_flagged}"],
            textfont=dict(
                size=14,
                color="#333333"
            ),
            textposition="inside",
            insidetextanchor="middle",
            hovertemplate=(
                "Previous week"
                "<br>No longer flagged: %{y} signals"
                "<extra></extra>"
            )
        )
    )

    # Current-week signals that are new.
    fig.add_trace(
        go.Bar(
            x=[1],
            y=[new_signals],
            width=bar_width,
            name="New this week",
            marker_color="#EF3B2C",
            text=[
                f"New this week<br>{new_signals}"
            ],
            textposition="inside",
            insidetextanchor="middle",
            hovertemplate=(
                "Latest week"
                "<br>New this week: %{y} signals"
                "<extra></extra>"
            )
        )
    )

    # Direct labels inside both ongoing segments.
    for x_position in [0, 1]:
        fig.add_annotation(
            x=x_position,
            y=ongoing_midpoint,
            text=f"Ongoing<br>{continuing_signals}",
            showarrow=False,
            font=dict(
                color="white",
                size=14
            ),
            align="center"
        )

    # Connect the top boundaries of the two ongoing segments.
    # This explicitly indicates that these are the same signals.
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
            f"{continuing_signals} ongoing signals"),
        showarrow=False,
        yshift=12,
        font=dict(
            color="#E0E0E0",
            size=14
        ),
        bgcolor="rgba(0,0,0,0.65)",
        borderpad=2
    )

    # Total labels above each bar.
    fig.add_annotation(
        x=0,
        y=previous_total,
        text=f"Total: {previous_total}",
        showarrow=False,
        yanchor="bottom",
        yshift=5,
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
        yshift=5,
        font=dict(
            color="white",
            size=14
        )
    )

    maximum_total = max(
        previous_total,
        current_total
    )

    fig.update_layout(
        barmode="stack",

        title=dict(
            text=(
                "How Potential Outbreaks Changed This Week"
                "<br>"
                "<span style='font-size:16px'>"
                f"{previous_total} previous week signals "
                f"→ {current_total} latest week signals"
                "</span>"
            ),
            x=0.5,
            xanchor="center",
            y=0.97,
            yanchor="top",
            font=dict(
                size=22,
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

        # Direct labels already identify every segment.
        showlegend=False,

        uniformtext_minsize=10,
        uniformtext_mode="hide",

        margin=dict(
            l=55,
            r=20,
            t=65,
            b=40
        ),

        xaxis=dict(
            title="",
            tickfont=dict(size=14),
            tickmode="array",
            tickvals=[0, 1],
            ticktext=[
                "Previous week",
                "Latest week"
            ],
            range=[-0.55, 1.55],
            showgrid=False,
            zeroline=False,
            fixedrange=True
        ),

        yaxis=dict(
            title=dict(
                text="Potential Outbreaks",
                font=dict(size=14)
            ),
            tickfont=dict(size=13),
        
            range=[
                0,
                maximum_total * 1.16
            ],
            showgrid=True,
            gridcolor="rgba(70, 90, 105, 0.35)",
            zeroline=False,
            fixedrange=True
        )
    )

    # ------------------------------------------------------------
    # Unified latest-week signal table
    # ------------------------------------------------------------

    latest_week_signals_table = week_2_data.loc[
        current_flags,
        [
            "state",
            "label",
            "new_cases",
            "potential_outbreak_past_week",
        ]
    ].copy()

    # A signal is ongoing when it was also flagged the previous week.
    # Otherwise, it is new this week.
    latest_week_signals_table["Status"] = (
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
                "state",
                "label",
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
            on=["state", "label"],
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

    # Convert case counts to ordinary Python integers where available.
    # Using None for missing values keeps the DataFrame JSON-serializable
    # when passed to Dash DataTable.
    for column in [
        "Previous Week",
        "Latest Week"
    ]:
        latest_week_signals_table[column] = (
            latest_week_signals_table[column]
            .apply(
                lambda value:
                None
                if pd.isna(value)
                else int(round(value))
            )
        )

    # Put new signals first, then ongoing signals.
    # Within each group, show the largest latest-week counts first.
    latest_week_signals_table["_status_order"] = (
        latest_week_signals_table["Status"]
        .map({
            "New": 0,
            "Ongoing": 1
        })
    )

    latest_week_signals_table = (
        latest_week_signals_table
        .sort_values(
            [
                "_status_order",
                "Latest Week"
            ],
            ascending=[
                True,
                False
            ]
        )
        .drop(
            columns=[
                "_status_order",
                "potential_outbreak_past_week"
            ]
        )
        [
            [
                "US State / Territory",
                "Disease",
                "Status",
                "Previous Week",
                "Latest Week"
            ]
        ]
        .reset_index(drop=True)
    )

    resolved_outbreaks_week_2 = no_longer_flagged

    return (
        fig,
        latest_week_signals_table,
        resolved_outbreaks_week_2
    )

