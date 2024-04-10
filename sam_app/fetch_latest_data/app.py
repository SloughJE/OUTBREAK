import json
import requests
import boto3
from botocore.exceptions import NoCredentialsError, ClientError
from io import BytesIO
import pandas as pd

from data_processing import align_data_schema

def lambda_handler(event, context):

    def get_secret():
        secret_name = "CDC_NNDSS_API"
        region_name = "us-east-2"

        session = boto3.session.Session()
        client = session.client(service_name='secretsmanager', region_name=region_name)

        try:
            get_secret_value_response = client.get_secret_value(SecretId=secret_name)
        except ClientError as e:
            raise e
        return json.loads(get_secret_value_response['SecretString'])

    # Retrieve the API token
    secret = get_secret()
    nndss_app_token = secret['NNDSS_APP_TOKEN']
    limit = 50000  # num max rows for api request
    bucket_name = "nndss"
    bucket_folder = "weekly"
    base_url = "https://data.cdc.gov/resource/x9gk-5huc.json"
    columns = 'states,year,week,label,m1'
    
    query_url = f"{base_url}?$$app_token={nndss_app_token}&$select={columns}&$where=location1 IS NOT NULL&$order=year DESC, week DESC&$limit=1"
    response = requests.get(query_url)
    
    if response.status_code == 200:
        latest_record = response.json()
        if latest_record:
            latest_year = latest_record[0]['year']
            latest_week = latest_record[0]['week']
            

            week_data_query_url = f"{base_url}?$$app_token={nndss_app_token}&$select={columns}&$where=year='{latest_year}' AND week='{latest_week}' AND location1 IS NOT NULL&$limit={limit}"            
            week_data_response = requests.get(week_data_query_url)
            
            if week_data_response.status_code == 200:
                latest_week_data = week_data_response.json()

                # Convert JSON to DataFrame
                df = pd.DataFrame(latest_week_data)
                df = align_data_schema(df)
                file_date = df.date.max().strftime('%Y-%m-%d')
                # Convert DataFrame to Parquet and upload to S3
                try:
                    s3_resource = boto3.resource('s3')
                    file_key = f"{bucket_folder}/weekly_actuals_{file_date}.parquet"
                    
                    # Use a buffer for the Parquet file
                    buffer = BytesIO()
                    df.to_parquet(buffer, index=False)
                    
                    # Reset buffer position to the start
                    buffer.seek(0)
                    s3_resource.Object(bucket_name, file_key).put(Body=buffer.getvalue())
                    print(f"Parquet file for the most recent week of year {latest_year}, week {latest_week} saved to S3")
                except NoCredentialsError:
                    print("Credentials not available")

                return {
                    'statusCode': 200,
                    'body': json.dumps(f"Parquet file for the most recent week of year {latest_year}, week {latest_week} saved to S3")
                }
            else:
                print(f"Failed to fetch data for the latest week: {week_data_response.status_code}")
        else:
            print("No recent data found.")
    else:
        print(f"Failed to fetch the latest data: {response.status_code}")

    return {
        'statusCode': 500,
        'body': json.dumps('Failed to fetch or save the latest data')
    }
