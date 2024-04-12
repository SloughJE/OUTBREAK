import pandas as pd
#from dotenv import load_dotenv
#import os
import pandas as pd
from sqlalchemy import create_engine


# Load environment variables from .env file
#load_dotenv()

# Connection settings
region_name = 'us-east-2'
s3_staging_dir = 's3://nndss/query_results/'
database_name = 'cdc_nndss'

# Fetch AWS credentials from environment variables
#aws_access_key_id = os.getenv('aws_dash_access_key')
#aws_secret_access_key = os.getenv('aws_dash_secret_key')
# query from local
#conn_str = (
#    f"awsathena+rest://"
#    f"{aws_access_key_id}:{aws_secret_access_key}@athena.{region_name}.amazonaws.com:443/"
#    f"{database_name}?s3_staging_dir={s3_staging_dir}"
#)

# query from EC2 with Athena acces
conn_str = (
    f"awsathena+rest://@athena.{region_name}.amazonaws.com:443/"
    f"{database_name}?s3_staging_dir={s3_staging_dir}"
)

# Create an SQLAlchemy engine using the PyAthena dialect
engine = create_engine(conn_str)

def check_and_fetch_new_data(max_date_historical, max_date_preds, engine):
    """
    Check for and fetch new weekly and predictions data from Athena using SQLAlchemy engine.

    Args:
    - max_date_historical (str): The maximum date in the 'historical' dataset, in 'YYYY-MM-DD' format.
    - max_date_preds (str): The maximum date in the 'predictions' dataset, in 'YYYY-MM-DD' format.
    - engine: An SQLAlchemy engine connected to Athena.

    Returns:
    - DataFrames containing any new weekly data and new predictions data, respectively.
    """
    # Construct the SQL query for new weekly data
    query_weekly_new_data = f"""
    SELECT * FROM cdc_nndss.weekly
    WHERE date > TIMESTAMP '{max_date_historical}'
    """
    
    # Construct the SQL query for new predictions data up to the max date of the weekly data
    query_predictions_new_data = f"""
    SELECT * FROM cdc_nndss.predictions
    WHERE prediction_for_date > TIMESTAMP '{max_date_preds}'
      AND prediction_for_date <= TIMESTAMP '{max_date_historical}'
    """

    # Execute the queries and fetch results into pandas DataFrames using the engine
    df_new_weekly = pd.read_sql(query_weekly_new_data, engine)
    df_new_predictions = pd.read_sql(query_predictions_new_data, engine)

    return df_new_weekly, df_new_predictions


def get_max_dates(filepath_historical="/home/ec2-user/dash_app/NNDSS/dash_app/data/df_historical.parquet",
                  filepath_predictions="/home/ec2-user/dash_app/NNDSS/dash_app/data/df_predictions.parquet"):

    df_historical = pd.read_parquet(filepath_historical, columns=['date'])
    df_preds_all = pd.read_parquet(filepath_predictions, columns=['date'])

    max_date_historical = df_historical.date.max()
    max_date_preds = df_preds_all.date.max()

    return max_date_historical, max_date_preds


def check_and_save_new_data(engine,
                            filepath_historical="/home/ec2-user/dash_app/NNDSS/dash_app/data/df_historical.parquet",
                            filepath_predictions="/home/ec2-user/dash_app/NNDSS/dash_app/data/df_predictions.parquet"):

    max_date_historical, max_date_preds = get_max_dates(filepath_historical, filepath_predictions)

    df_new_weekly, df_new_predictions = check_and_fetch_new_data(max_date_historical, max_date_preds, engine)

    if not df_new_weekly.empty:
        df_historical = pd.read_parquet(filepath_historical)
        df_updated_historical = pd.concat([df_historical, df_new_weekly], ignore_index=True)
        df_updated_historical.to_parquet(filepath_historical)
        print("Historical data updated.")
    else:
        print("No new weekly data.")
    
    if not df_new_predictions.empty:
        df_predictions = pd.read_parquet(filepath_predictions)
        df_updated_predictions = pd.concat([df_predictions, df_new_predictions], ignore_index=True)
        df_updated_predictions.to_parquet(filepath_predictions)
        print("Predictions data updated.")
    else:
        print("No new predictions data.")


check_and_save_new_data(engine,
    filepath_historical="/home/ec2-user/dash_app/NNDSS/dash_app/data/df_historical.parquet",
    filepath_predictions="/home/ec2-user/dash_app/NNDSS/dash_app/data/df_predictions.parquet"
    )