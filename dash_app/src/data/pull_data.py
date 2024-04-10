import boto3
from botocore.exceptions import NoCredentialsError
from dotenv import load_dotenv
import os
import pandas as pd
from pyathena import connect
# Load environment variables from .env file
load_dotenv()


# Connection settings
region_name = 'us-east-2'
s3_staging_dir = 's3://nndss/query_results/'

# Initialize connection
conn = connect(aws_access_key_id=os.getenv('aws_dash_access_key'),
               aws_secret_access_key=os.getenv('aws_dash_secret_key'),
               region_name=region_name,
               s3_staging_dir=s3_staging_dir)

def pull_data():

    query = """SELECT * FROM (
    SELECT item_id, year, week, date, state, label, new_cases, filled_with_0
    FROM cdc_nndss.historical
    UNION ALL
    SELECT item_id, year, week, date, state, label, new_cases, NULL AS filled_with_0
    FROM cdc_nndss.weekly
    ) AS combined_data 
    """

    df_weekly = pd.read_sql(query, conn)
    max_date = df_weekly['date'].max()
    
    print(f"querying predictions for date: {max_date}")
    

    query_predictions = f"SELECT * FROM cdc_nndss.predictions WHERE prediction_for_date = TIMESTAMP '{max_date}'"
    df_predictions = pd.read_sql(query_predictions, conn)
    # Split df_weekly into df_historical and df_latest
    df_historical = df_weekly[df_weekly['date'] < max_date]
    df_latest = df_weekly[df_weekly['date'] == max_date]

    df_historical.to_parquet(f"dash_app/data/historical.parquet")
    df_predictions.to_parquet(f"dash_app/data/predictions.parquet")
    df_latest.to_parquet(f"dash_app/data/latest.parquet")
    print("Latest data:")
    print(df_latest.head(2))
    print("Prediction data:")
    print(df_predictions.head(2))

    print(f"data saved to dash_app/data/")
    


"""
def get_latest_parquet(prefix, bucket_name):
    # List objects within the specified prefix
    response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)

    # Extract the keys (file paths) and last modified dates
    files = [{'Key': obj['Key'], 'LastModified': obj['LastModified']} for obj in response['Contents'] if obj['Key'].endswith('.parquet')]

    # Sort the files by last modified date, descending
    files_sorted = sorted(files, key=lambda x: x['LastModified'], reverse=True)

    # Get the most recent file's key
    if files_sorted:
        most_recent_file_key = files_sorted[0]['Key']
        #most_recent_file_path = f's3://{bucket_name}/{most_recent_file_key}'
        
        return most_recent_file_key

    else:
        raise ValueError("No parquet files found in the specified S3 path.")
    
    

def pull_parquet(bucket_name, most_recent_file_key,local_filename):

    s3_client.download_file(bucket_name, most_recent_file_key, local_filename)



def pull_parquet_latest_files(
        bucket_name = 'nndss', 
        prefix = 'weekly/'
                    ):
    
    local_filename = f"dash_app/data/{prefix[0:-1]}.parquet"

    most_recent_file_key = get_latest_parquet(prefix, bucket_name)

    pull_parquet(bucket_name, most_recent_file_key, local_filename)

    # Read the Parquet file into a pandas DataFrame
    df = pd.read_parquet(local_filename)
    #os.remove(local_filename)
    print(df.head(2))

def get_all_data(bucket_name = 'nndss'):

    pull_parquet_latest_files(bucket_name, 'weekly/')
    pull_parquet_latest_files(bucket_name, 'predictions/')
    pull_parquet_latest_files(bucket_name, 'historical/')
"""