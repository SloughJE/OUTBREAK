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


def align_data_schema(df):
    """
    Transforms the data fetched from the API to the desired schema.
    """
    
    df.rename(columns={'states': 'state'}, inplace=True)  # Renaming 'states' to 'state'
    df["state"] = df["state"].str.upper()
    df['item_id'] = df['state'] + '_' + df['label']  # Using the renamed 'state' column
    df['date'] = pd.to_datetime(df['year'].astype(str) + df['week'].astype(str) + '-1', format='%Y%W-%w')
    df['new_cases'] = pd.to_numeric(df['m1'], errors='coerce').fillna(0)

    df['week'] = df.week.astype(int)
    df['year'] = df.year.astype(int)
    # Ensure the DataFrame has only the expected columns, in the correct order
    expected_columns = ['item_id', 'year', 'week','state', 'date', 'label', 'new_cases']
    # Reorder or filter the DataFrame to match the expected schema
    df = df[expected_columns]
    
    return df


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

    for obj in response.get('Contents', []):
        key = obj['Key']
        if key.endswith('.parquet'):
            # Corrected parameter names in the get_object call
            obj_response = s3_client.get_object(Bucket=bucket_name, Key=key)
            buffer = BytesIO(obj_response['Body'].read())
            df = pd.read_parquet(buffer)
            expected_columns = ['item_id', 'year', 'week', 'state', 'date', 'label', 'new_cases']
            df = df[expected_columns]
            all_dfs.append(df)

    # Concatenate all dataframes into one
    if all_dfs:
        full_df = pd.concat(all_dfs, ignore_index=True)
        return full_df
    else:
        return pd.DataFrame()
        

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

    # CDC API seems to sometimes skip weeks. We deal with that here
    df = df.sort_values(by='date')

    while True:

        unique_dates = df['date'].unique()
        unique_dates = sorted(unique_dates)  # Sort the dates
        
        gap = unique_dates[-1] - unique_dates[-2]

        if gap > pd.Timedelta(days=7):
            
            max_date_df = df[df['date'] == unique_dates[-1]].copy()
            second_last_date_df = df[df['date'] == unique_dates[-2]].copy()
            
            # Create a new dataframe for missing weeks by concatenating max and second last date dataframes
            missing_weeks_df = pd.concat([max_date_df, second_last_date_df])
            missing_weeks_df = missing_weeks_df.drop_duplicates(subset=['item_id'], keep='last')

            weeks_to_fill = gap.days // 7
            print(weeks_to_fill)
            # Generate skipped weeks
            for i in range(1, weeks_to_fill):
                temp_df = missing_weeks_df.copy()
                new_date = unique_dates[-2] + pd.Timedelta(weeks=i)
                
                print(f"filling data with NaN for skipped week: {new_date.strftime('%Y-%m-%d')}")
                
                temp_df['date'] = new_date
                temp_df['week'] = second_last_date_df['week'].iloc[0] + i

                # Ensure the year remains 2024 if the date is still in 2024
                if new_date.year == 2024:
                    temp_df['year'] = 2024  # Force year to 2024 even if it's week 53
                
                temp_df['new_cases'] = np.nan
                temp_df = align_data_types(df, temp_df)
                
                # Save skipped week to S3
                save_missing_week_to_s3(s3_client, temp_df, bucket_name, bucket_folder)

                df = pd.concat([df, temp_df], ignore_index=True)


            df = df.sort_values(['item_id','date'])
        else:
            break

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
