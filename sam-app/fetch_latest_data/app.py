import os
import json
import requests
import boto3
from botocore.exceptions import NoCredentialsError, ClientError


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
    
    bucket_name = "nndss"
    
    base_url = "https://data.cdc.gov/resource/x9gk-5huc.json"
    columns = 'states,year,week,label,m1'
    
    query_url = f"{base_url}?$$app_token={nndss_app_token}&$select={columns}&$where=location1 IS NOT NULL&$order=year DESC, week DESC&$limit=1"
    response = requests.get(query_url)
    
    if response.status_code == 200:
        latest_record = response.json()
        if latest_record:
            latest_year = latest_record[0]['year']
            latest_week = latest_record[0]['week']
            
            week_data_query_url = f"{base_url}?$$app_token={nndss_app_token}&$select={columns}&$where=year='{latest_year}' AND week='{latest_week}' AND location1 IS NOT NULL AND label NOT LIKE '%25Probable%25'"
            week_data_response = requests.get(week_data_query_url)
            
            if week_data_response.status_code == 200:
                latest_week_data = week_data_response.json()
                
                # Upload raw JSON to S3
                try:
                    s3_client = boto3.client('s3')
                    file_key = f"latest/df_latest_{latest_year}_{latest_week}.json"
                    s3_client.put_object(Body=json.dumps(latest_week_data), Bucket=bucket_name, Key=file_key, ContentType='application/json')
                    print(f"Raw data for the most recent week of year {latest_year}, week {latest_week} saved to S3")
                except NoCredentialsError:
                    print("Credentials not available")
                    
                return {
                    'statusCode': 200,
                    'body': json.dumps(f"Raw data for the most recent week of year {latest_year}, week {latest_week} saved to S3")
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
