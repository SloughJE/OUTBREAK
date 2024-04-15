import json
import requests
import boto3
from botocore.exceptions import NoCredentialsError, ClientError
from io import BytesIO
import pandas as pd

from data_processing import align_data_schema, process_dataframe_deepar

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
    

    def get_latest_file_from_s3(bucket, folder):
        s3 = boto3.client('s3')
        paginator = s3.get_paginator('list_objects_v2')
        page_iterator = paginator.paginate(Bucket=bucket, Prefix=folder)
        latest_file = None
        latest_date = None
        for page in page_iterator:
            if "Contents" in page:
                for obj in page['Contents']:
                    file_key = obj['Key']
                    # Check if the object is a file (not a folder)
                    if file_key.endswith('.parquet'):
                        file_date = obj['LastModified']
                        if not latest_date or file_date > latest_date:
                            latest_date = file_date
                            latest_file = file_key

        return latest_file



    def get_latest_data_from_parquet(bucket, file_key):
        s3_resource = boto3.resource('s3')
        obj = s3_resource.Object(bucket_name=bucket, key=file_key)
        buffer = BytesIO(obj.get()["Body"].read())
        df = pd.read_parquet(buffer)
        latest_year = df['year'].max()
        latest_week = df[df['year'] == latest_year]['week'].max()
        return latest_year, latest_week


    # Retrieve the API token
    secret = get_secret()
    nndss_app_token = secret['NNDSS_APP_TOKEN']
    limit = 50000  # num max rows for api request
    bucket_name = "nndss"
    bucket_folder = "weekly"
    base_url = "https://data.cdc.gov/resource/x9gk-5huc.json"
    columns = 'states,year,week,label,m1'
    
    # Get the latest data file from S3
    latest_file_key = get_latest_file_from_s3(bucket_name, bucket_folder)
    print(f"latest_file_key: {latest_file_key}")

    if latest_file_key:
        latest_year, latest_week = get_latest_data_from_parquet(bucket_name, latest_file_key)
        print(f"latest week and year in s3: week {latest_week}, {latest_year}")
        week_data_response = None

        # Get the latest data date from the API
        query_url = f"{base_url}?$$app_token={nndss_app_token}&$select=year,week&$where=location1 IS NOT NULL&$order=year DESC, week DESC&$limit=1"
        response = requests.get(query_url)

        if response.status_code == 200:
            latest_record = response.json()
            if latest_record:
                api_latest_year = int(latest_record[0]['year'])
                api_latest_week = int(latest_record[0]['week'])

                # Only proceed if the API data is newer than the S3 data
                if (api_latest_year > latest_year) or (api_latest_year == latest_year and api_latest_week > latest_week):
                    week_data_query_url = f"{base_url}?$$app_token={nndss_app_token}&$select=year,week,states,label,m1&$where=year='{api_latest_year}' AND week='{api_latest_week}' AND location1 IS NOT NULL&$limit={limit}"
                    week_data_response = requests.get(week_data_query_url)
                    if week_data_response.status_code == 200:
                        latest_week_data = week_data_response.json()

                        # Convert JSON to DataFrame
                        df = pd.DataFrame(latest_week_data)
                        df = align_data_schema(df)
                        file_date = df.date.max().strftime('%Y-%m-%d')
                        # Convert DataFrame to Parquet and upload to S3
                        try:
                            s3 = boto3.client('s3')
                            file_key = f"{bucket_folder}/weekly_actuals_{file_date}.parquet"
                            
                            # Use a buffer for the Parquet file
                            buffer = BytesIO()
                            df.to_parquet(buffer, index=False)
                            buffer.seek(0)
                            s3.put_object(Bucket=bucket_name, Key=file_key, Body=buffer.getvalue())
                            print(f"Parquet file for the most recent week of year {latest_year}, week {latest_week} saved to S3")

                            # now we create the DeepAR training data with this new data included
                            print("creating DeepAR input data ")
                            json_lines_str, mapping_str, label_to_int_str = process_dataframe_deepar(df)
                            transformed_key = 'deepar_input_data/deepar_dataset.jsonl'
                            s3.put_object(Bucket=bucket_name, Key=transformed_key, Body=json_lines_str)
                            print("Data processed and saved to 'deepar_input_data/deepar_dataset.jsonl'")
                            mapping_key = 'deepar_input_data/time_series_mapping_with_labels.json'
                            s3.put_object(Bucket=bucket_name, Key=mapping_key, Body=mapping_str)
                            print(f"Mapping file saved to s3://{bucket_name}/{mapping_key}")
                            label_to_int_key = 'deepar_input_data/label_to_int_mapping.json'
                            s3.put_object(Bucket=bucket_name, Key=label_to_int_key, Body=label_to_int_str)
                            print(f"Label-to-int mapping file saved to s3://{bucket_name}/{label_to_int_key}")

                            return {
                            'statusCode': 200,
                            'body': json.dumps(f"New weekly data pulled for week {latest_week} {latest_year} and saved to {file_key}. DeepAR input data created and saved to {bucket_name}")
                            }
                        except NoCredentialsError:
                            return {
                                'statusCode': 500,
                                'body': json.dumps("Credentials not available")
                            }
                    else:
                        return {
                            'statusCode': 500,
                            'body': json.dumps(f"Failed to fetch data for the latest week: {week_data_response.status_code}")
                        }
                else:
                    return {
                        'statusCode': 200,
                        'body': json.dumps("No recent data found.")
                    }
            else:
                return {
                    'statusCode': 200,
                    'body': json.dumps("No recent data found.")
                }
        else:
            return {
                'statusCode': 500,
                'body': json.dumps(f"Failed to fetch the latest data: {response.status_code}")
            }

    return {
        'statusCode': 500,
        'body': json.dumps('Failed to fetch or save the latest data')
    }