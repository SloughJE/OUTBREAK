import pandas as pd
import numpy as np
import json
from io import BytesIO


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
        