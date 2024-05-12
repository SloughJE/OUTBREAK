import pandas as pd
import numpy as np
import json
from io import BytesIO


def align_data_schema(df):
    """
    Transforms the data fetched from the API to the desired schema.
    """
    
    df.rename(columns={'states': 'state'}, inplace=True)  # Renaming 'states' to 'state'
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
        
    df['date'] = pd.to_datetime(df['date'])
    df.sort_values(by=['item_id', 'date'], inplace=True)

    # Randomly shuffle the time series
    random_groups = pd.Series(np.random.permutation(df['item_id'].unique()), index=df['item_id'].unique())
    df['random_group'] = df['item_id'].map(random_groups)

    df = df.sort_values(by=['random_group', 'date']).drop('random_group', axis=1).reset_index(drop=True)

    # Encode the 'label' as integers
    unique_labels = df['label'].unique()
    cardinality = len(unique_labels)

    label_to_int = {label: idx for idx, label in enumerate(unique_labels)}
    df['label_encoded'] = df['label'].map(label_to_int)

    # Prepare containers for the JSON Lines and mappings
    json_lines = []
    time_series_mapping = {}

    for idx, (item_id, group) in enumerate(df.groupby('item_id')):
        # Get the encoded label; assuming one label per item_id group
        encoded_label = group['label_encoded'].iloc[0]

        # Create time series data with 'cat' for static features
        time_series = {
            "start": str(group['date'].dt.date.iloc[0]),
            "target": convert_target(group['new_cases']),
            # Convert numpy int64 to Python int before including it in the 'cat' field
            "cat": [int(encoded_label)]  # Ensuring it's a native Python int type
        }
        json_lines.append(json.dumps(time_series))

        # Map item_id to its index and label encoding in the JSON Lines file
        time_series_mapping[item_id] = {'index': idx, 'label_encoded': encoded_label}

    # Convert JSON Lines list to a single string for storage or transmission
    json_lines_str = "\n".join(json_lines)

    # Optionally, save the mappings as JSON for future reference
    time_series_mapping = convert_numpy_int64(time_series_mapping)
    time_series_mapping_json = json.dumps(time_series_mapping)
    label_to_int_json = json.dumps(label_to_int)

    return json_lines_str, time_series_mapping_json, label_to_int_json, cardinality


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
                print(f"filling data with NaN for skipped week: {(unique_dates[-2] + pd.Timedelta(weeks=i)).strftime('%Y-%m-%d')}")
                temp_df['date'] = unique_dates[-2] + pd.Timedelta(weeks=i)
                temp_df['week'] = second_last_date_df['week'].iloc[0] + i
                temp_df['new_cases'] = np.nan
                temp_df = align_data_types(df, temp_df)
                # save skipped week to s3
                save_missing_week_to_s3(s3_client, temp_df, bucket_name, bucket_folder)

                df = pd.concat([df, temp_df], ignore_index=True)

            df = df.sort_values(['item_id','date'])
        else:
            break

    return df