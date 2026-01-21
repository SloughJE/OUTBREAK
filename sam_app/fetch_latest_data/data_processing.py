import pandas as pd
import numpy as np
import requests
import json
from io import BytesIO


def fetch_api_data(url):
    response = requests.get(url)
    if response.status_code != 200:
        return None, f"Failed to fetch data: {response.status_code}"
    return response.json(), None


def get_current_max_year_week(df):
    """
    Return the maximum (year, week) from the given DataFrame
    by looking at the 'year' and 'week' columns.
    """
    max_year = df['year'].max()
    max_week = df.loc[df['year'] == max_year, 'week'].max()
    return (max_year, max_week)


def align_data_schema(df: pd.DataFrame) -> pd.DataFrame:
    """
    Transforms CDC NNDSS API output into the canonical schema.

    Critical: construct `date` using ISO week rules so that (year, week) maps
    consistently to a Monday timestamp across year boundaries.
    """
    df = df.copy()

    df.rename(columns={'states': 'state'}, inplace=True)
    df["state"] = df["state"].astype(str).str.upper()

    # Ensure types early
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    df["week"] = pd.to_numeric(df["week"], errors="coerce").astype("Int64")

    # Drop rows where year/week missing
    df = df.dropna(subset=["year", "week"])

    df["year"] = df["year"].astype(int)
    df["week"] = df["week"].astype(int)

    # ISO week -> Monday date.
    # %G = ISO year, %V = ISO week number, %u = ISO weekday (1=Mon)
    df["date"] = pd.to_datetime(
        df["year"].astype(str)
        + "-W"
        + df["week"].astype(str).str.zfill(2)
        + "-1",
        format="%G-W%V-%u",
        errors="coerce",
        utc=False,
    )

    # If any dates failed to parse, you want to know immediately.
    # (Optional) Keep this as a print or raise; in Lambda I suggest print.
    if df["date"].isna().any():
        bad = df[df["date"].isna()][["year", "week"]].drop_duplicates().head(20)
        print("WARNING: Failed to parse ISO week->date for some rows. Sample:", bad.to_dict("records"))

    df["new_cases"] = pd.to_numeric(df.get("m1"), errors="coerce").fillna(0)

    df["item_id"] = df["state"] + "_" + df["label"].astype(str)

    expected_columns = ["item_id", "year", "week", "state", "date", "label", "new_cases"]
    return df[expected_columns]



def process_dataframe_deepar(df):

    # A function to convert NaN values to "NaN" string and others to float
    def convert_target(target_series):
        return [float(x) if pd.notna(x) else "NaN" for x in target_series]

    def convert_numpy_int64(obj):
        if isinstance(obj, dict):
            return {k: convert_numpy_int64(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_numpy_int64(v) for v in obj]
        elif isinstance(obj, np.int64):
            return int(obj)  # Convert numpy.int64 to int
        else:
            return obj

    # 1) Ensure 'date' is datetime and sort by (item_id, date)
    df['date'] = pd.to_datetime(df['date'])
    df.sort_values(by=['item_id', 'date'], inplace=True)

    # 2) Randomly shuffle the time series order (as before)
    random_groups = pd.Series(
        np.random.permutation(df['item_id'].unique()),
        index=df['item_id'].unique()
    )
    df['random_group'] = df['item_id'].map(random_groups)

    df = df.sort_values(by=['random_group', 'date']) \
           .drop('random_group', axis=1) \
           .reset_index(drop=True)

    # 3) Create integer encodings for 'state' and 'label' so we have 2 categorical features.
    unique_states = df['state'].unique()
    unique_diseases = df['label'].unique()

    state_to_int = {st: i for i, st in enumerate(unique_states)}
    disease_to_int = {d: i for i, d in enumerate(unique_diseases)}

    # Add columns to df
    df['state_idx'] = df['state'].map(state_to_int)
    df['disease_idx'] = df['label'].map(disease_to_int)

    # DeepAR expects cardinality = [#states, #diseases]
    cardinality = [len(unique_states), len(unique_diseases)]

    # 4) Build JSON lines and a mapping dictionary
    json_lines = []
    time_series_mapping = {}

    # group by item_id so each group is a single time series
    for idx, (item_id, group) in enumerate(df.groupby('item_id')):
        # Pull the state/disease indices from the first row in this group (they are all the same for that item_id)
        st_idx = int(group['state_idx'].iloc[0])
        ds_idx = int(group['disease_idx'].iloc[0])

        # Build the DeepAR record
        time_series = {
            "start": str(group['date'].dt.date.iloc[0]),  # e.g., "2022-01-03"
            "target": convert_target(group['new_cases']),
            "cat": [st_idx, ds_idx]
        }

        # Convert time_series to JSON and store in json_lines
        json_lines.append(json.dumps(time_series))

        # Also store a mapping for reference
        time_series_mapping[item_id] = {
            "index": idx,
            "state_idx": st_idx,
            "disease_idx": ds_idx
        }

    # 5) Convert JSON Lines list to a single string
    json_lines_str = "\n".join(json_lines)

    # 6) Convert time_series_mapping to JSON
    time_series_mapping = convert_numpy_int64(time_series_mapping)
    time_series_mapping_json = json.dumps(time_series_mapping)

    # Convert the state_to_int and disease_to_int maps to JSON 
    state_map_json = json.dumps(convert_numpy_int64(state_to_int))
    disease_map_json = json.dumps(convert_numpy_int64(disease_to_int))

    # Return everything
    # - json_lines_str: The actual DeepAR dataset
    # - time_series_mapping_json: Which item_id maps to which cat indices
    # - state_map_json, disease_map_json: Mappings of state/disease to integer
    # - cardinality: The [number_of_states, number_of_diseases]
    return (json_lines_str,
            time_series_mapping_json,
            state_map_json,
            disease_map_json,
            cardinality)


def read_all_parquets_from_s3(s3_client, bucket_name, prefix):
    response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
    all_dfs = []


    keys = sorted(
        obj["Key"]
        for obj in response.get("Contents", [])
        if obj["Key"].endswith(".parquet")
    )

    for key in keys:
        obj_response = s3_client.get_object(Bucket=bucket_name, Key=key)
        buffer = BytesIO(obj_response["Body"].read())
        df = pd.read_parquet(buffer)

        expected_columns = ["item_id", "year", "week", "state", "date", "label", "new_cases"]
        df = df[expected_columns]
        all_dfs.append(df)

    return pd.concat(all_dfs, ignore_index=True) if all_dfs else pd.DataFrame()

        

def align_data_types(base_df, target_df):
    for column in target_df.columns:
        if column in base_df.columns:  # Ensure the column exists in both DataFrames
            target_df[column] = target_df[column].astype(base_df[column].dtype)
    return target_df


def save_missing_week_to_s3(s3_client, df, bucket_name, bucket_folder):

    file_date = df.date.max().strftime('%Y-%m-%d')
    # Convert DataFrame to Parquet and upload to S3

    file_key = f"{bucket_folder}/weekly_actuals_{file_date}.parquet"

    # Use a buffer for the Parquet file
    buffer = BytesIO()
    df.to_parquet(buffer, index=False)
    buffer.seek(0)
    s3_client.put_object(Bucket=bucket_name, Key=file_key, Body=buffer.getvalue())
    print(f"Saving skipped week for date {file_date} to s3")


def fill_missing_weeks(s3_client, df, bucket_name, bucket_folder):
    """
    Ensure the dataset has a continuous weekly (W-MON) time index between its min and max date.

    We fill missing weeks by inserting rows (one per item_id) with new_cases = NaN.
    Year/week are derived from the inserted `date` using ISO week rules.

    This function does NOT attempt to guess CDC week numbers by arithmetic.
    """
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    # If date parsing failed anywhere, drop those rows (or handle explicitly)
    # Dropping prevents silent max-date errors.
    df = df.dropna(subset=["date"])

    df = df.sort_values(["item_id", "date"]).reset_index(drop=True)

    min_date = df["date"].min()
    max_date = df["date"].max()

    if pd.isna(min_date) or pd.isna(max_date) or min_date == max_date:
        return df

    # Generate a complete Monday-based weekly range
    full_range = pd.date_range(start=min_date, end=max_date, freq="W-MON")
    existing_dates = set(pd.to_datetime(df["date"].unique()))

    missing_dates = [d for d in full_range if d not in existing_dates]
    if not missing_dates:
        return df

    # Template: last observed row per item_id (keeps state/label/item_id stable)
    latest_by_item = (
        df.sort_values("date")
          .groupby("item_id", as_index=False)
          .tail(1)
          .copy()
    )

    for d in missing_dates:
        temp_df = latest_by_item.copy()
        temp_df["date"] = d

        iso = pd.Timestamp(d).isocalendar()
        temp_df["year"] = int(iso.year)
        temp_df["week"] = int(iso.week)

        temp_df["new_cases"] = np.nan

        # Keep your existing dtype alignment and S3 persistence hooks
        temp_df = align_data_types(df, temp_df)
        save_missing_week_to_s3(s3_client, temp_df, bucket_name, bucket_folder)

        df = pd.concat([df, temp_df], ignore_index=True)

    df = df.sort_values(["item_id", "date"]).reset_index(drop=True)
    return df



def fetch_data_for_week(year, week, app_token):
    """
    Fetch a single (year, week) from the CDC NNDSS API and return a DataFrame.
    If there's no data for that week, returns an empty DataFrame.
    """
    import pandas as pd
    
    base_url = "https://data.cdc.gov/resource/x9gk-5huc.json"
    limit = 50000
    query_url = (
        f"{base_url}?$$app_token={app_token}"
        f"&$select=year,week,states,label,m1"
        f"&$where=year='{year}' AND week='{week}' AND location1 IS NOT NULL"
        f"&$limit={limit}"
    )
    
    data, error = fetch_api_data(query_url)  
    if error:
        raise RuntimeError(f"Failed to fetch data: {error}")
    
    if not data:
        # No records returned for that (year, week).
        return pd.DataFrame()
    
    df = pd.DataFrame(data)
    df = align_data_schema(df)  # your existing schema alignment
    return df


def backfill_missing_weeks(
    start_year, 
    start_week, 
    end_year, 
    end_week, 
    app_token
):
    """
    For all missing (year, week) from (start_year, start_week+1)
    up to (end_year, end_week), fetch from the CDC using fetch_data_for_week.
    Return one concatenated DataFrame with all newly fetched data.
    
    If there's no data for a particular week, we just get an empty DataFrame for that week.
    """

    from datetime import date

    def increment_year_week(y, w):
        max_weeks = date(y, 12, 28).isocalendar()[1]  # 52 or 53 weeks in that year
        if w >= max_weeks:
            return (y + 1, 1)
        else:
            return (y, w + 1)

    
    all_new_dfs = []

    # Start from (start_year, start_week)
    current_year = start_year
    current_week = start_week

    # We'll loop until we reach (end_year, end_week)
    while True:
        # increment the current (year, week)
        (current_year, current_week) = increment_year_week(current_year, current_week)
        
        # if we've passed the end condition, break
        if (current_year > end_year) or (
           current_year == end_year and current_week > end_week):
            break

        # fetch data for this missing week
        df_week = fetch_data_for_week(current_year, current_week, app_token)
        if not df_week.empty:
            print(f"Fetched {len(df_week)} records for (year={current_year}, week={current_week})")
            all_new_dfs.append(df_week)
        else:
            print(f"No data for (year={current_year}, week={current_week})")

    # Combine all
    if all_new_dfs:
        return pd.concat(all_new_dfs, ignore_index=True)
    else:
        return pd.DataFrame()
