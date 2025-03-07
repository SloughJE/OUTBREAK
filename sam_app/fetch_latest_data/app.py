import json
import requests
import boto3
import os
import time
import pandas as pd
from io import BytesIO
from botocore.exceptions import ClientError

from data_processing import (align_data_schema, process_dataframe_deepar, read_all_parquets_from_s3, 
                             get_current_max_year_week, fill_missing_weeks, backfill_missing_weeks)
from model_training import trigger_sagemaker_training


def get_secret():
    secret_name = "CDC_NNDSS_API"
    region_name = "us-east-2"
    session = boto3.session.Session()
    client = session.client(service_name='secretsmanager', region_name=region_name)
    try:
        response = client.get_secret_value(SecretId=secret_name)
        return json.loads(response['SecretString'])
    except ClientError as e:
        raise e


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
    
    data, error = fetch_api_data(query_url)  # Re-use your existing fetch_api_data
    if error:
        raise RuntimeError(f"Failed to fetch data: {error}")
    
    if not data:
        # No records returned for that (year, week).
        return pd.DataFrame()
    
    df = pd.DataFrame(data)
    df = align_data_schema(df)  # your existing schema alignment
    return df


#def get_latest_file_from_s3(bucket, folder):
#    s3 = boto3.client('s3')
#    paginator = s3.get_paginator('list_objects_v2')
#    latest_file = None
#    latest_date = None
#    for page in paginator.paginate(Bucket=bucket, Prefix=folder):
#        for obj in page.get('Contents', []):
#            if obj['Key'].endswith('.parquet') and (not latest_date or obj['LastModified'] > latest_date):
#                latest_date = obj['LastModified']
#                latest_file = obj['Key']
#    return latest_file

def get_latest_data_from_parquet(bucket, file_key):
    s3_resource = boto3.resource('s3')
    obj = s3_resource.Object(bucket_name=bucket, key=file_key)
    df = pd.read_parquet(BytesIO(obj.get()["Body"].read()))
    latest_year = df['year'].max()
    latest_week = df[df['year'] == latest_year]['week'].max()
    return latest_year, latest_week

def fetch_api_data(url):
    response = requests.get(url)
    if response.status_code != 200:
        return None, f"Failed to fetch data: {response.status_code}"
    return response.json(), None


def wait_for_training_completion(sagemaker_client, training_job_name):
    while True:
        response = sagemaker_client.describe_training_job(TrainingJobName=training_job_name)
        status = response['TrainingJobStatus']
        if status == 'Completed':
            print("Training job completed successfully.")
            break
        elif status == 'Failed':
            print("Training job failed.")
            print("Reason:", response['FailureReason'])
            break
        else:
            print("Training job still in progress...")
            time.sleep(20)  # wait for 60 seconds before checking again
    return response


def lambda_handler(event, context):
    try:
        secret = get_secret()
    except ClientError as e:
        return {'statusCode': 500, 'body': json.dumps("Failed to retrieve secret: " + str(e))}

    nndss_app_token = secret['NNDSS_APP_TOKEN']
    bucket_name = "nndss"
    bucket_folder = "weekly"
    base_url = "https://data.cdc.gov/resource/x9gk-5huc.json"

    # 1) Read ALL Parquets from S3
    s3_client = boto3.client('s3')
    df_all = read_all_parquets_from_s3(s3_client, bucket_name, bucket_folder)
    if df_all.empty:
        print("No existing data found in S3. We'll treat this as having year=0, week=0.")
        latest_year_in_s3, latest_week_in_s3 = (0, 0)
    else:
        # 2) Find the maximum (year, week) in the entire DataFrame
        latest_year_in_s3, latest_week_in_s3 = get_current_max_year_week(df_all)
        del df_all
    print(f"Current data in S3 goes up to year={latest_year_in_s3}, week={latest_week_in_s3}")

    # 3) Query the CDC API for the absolute newest (year, week) they have
    query_url = (
        f"{base_url}?$$app_token={nndss_app_token}"
        "&$select=year,week&$where=location1 IS NOT NULL"
        "&$order=year DESC, week DESC&$limit=1"
    )
    latest_record, error = fetch_api_data(query_url)
    if error:
        print(f"Error: {error}")
        return {'statusCode': 500, 'body': json.dumps(error)}

    if not latest_record:
        print("No latest record from CDC.")
        return {'statusCode': 200, 'body': json.dumps("No recent data found.")}

    # CDC's latest year/week
    api_latest_year = int(latest_record[0]['year'])
    api_latest_week = int(latest_record[0]['week'])

    ########
    # 4) Compare new vs. S3
    if (api_latest_year > latest_year_in_s3) or (
        api_latest_year == latest_year_in_s3 and api_latest_week > latest_week_in_s3
    ):
        print(
            f"CDC data goes up to year={api_latest_year}, week={api_latest_week}, "
            f"while S3 has year={latest_year_in_s3}, week={latest_week_in_s3}."
        )
        print("Backfilling all missing weeks now...")

        df_new = backfill_missing_weeks(
            start_year=latest_year_in_s3,
            start_week=latest_week_in_s3,
            end_year=api_latest_year,
            end_week=api_latest_week,
            app_token=nndss_app_token
        )

        if df_new.empty:
            print("No data returned for missing weeks. Possibly no data from CDC.")
            return {
                'statusCode': 200,
                'body': json.dumps("No new data. CDC returned no records.")
            }
        else:
            print(f"Backfilled {len(df_new)} total rows from CDC for all missing weeks.")
            # Merge with existing df_all
            # df_all = pd.concat([df_all, df_new], ignore_index=True)

            ##################################################
            #print(df_new['date'].dtype)  # Check the original type
            #print(df_new['date'].unique())  # See if there are unexpected values
            #print(df_new['date'].min())
            #print(df_new['date'].max())
            df_new['date'] = pd.to_datetime(df_new['date'])
            #df_new = df_new[df_new['date'] <= '2025-02-17'] ##
            print(df_new['date'].min())
            print(df_new['date'].max())
            #print(df_new['date'].dtype)  # Check the original type
            print(df_new['date'].unique())  # See if there are unexpected values

            ##################################################

            # Save the newly fetched data to S3 in one Parquet file --
            file_date = df_new['date'].max().strftime('%Y-%m-%d')
            file_key = f"{bucket_folder}/weekly_actuals_{file_date}.parquet"
            print(f"Saving merged backfill data to S3 -> {file_key}")

            buffer = BytesIO()
            df_new.to_parquet(buffer, index=False)
            buffer.seek(0)
            s3_client.put_object(Bucket=bucket_name, Key=file_key, Body=buffer.getvalue())

        
        # now we create the DeepAR training data with this new data included
        print("creating DeepAR input data ")
        s3_client = boto3.client('s3')
        df = read_all_parquets_from_s3(s3_client, bucket_name, bucket_folder)
        print("df heads and tails")
        print(df.head(2))
        print(df.tail(2))
        # check for skipped weeks
        df = fill_missing_weeks(s3_client, df, bucket_name, bucket_folder)

        # remove the last week of data for training, so that we make predictions for the current (latest) week of data
        df = df[df['date'] < df['date'].max()]
        print(f"max date in df: {df['date'].max()}")

        s3 = boto3.client('s3')
        json_lines_str, time_series_mapping_json, state_map_json, disease_map_json, cardinality = process_dataframe_deepar(df)

        # json_lines_str, mapping_str, label_to_int_str, cardinality = process_dataframe_deepar(df)
        transformed_key = 'deepar_input_data/deepar_dataset.jsonl'
        s3.put_object(Bucket=bucket_name, Key=transformed_key, Body=json_lines_str)
        print("Data processed and saved to 'deepar_input_data/deepar_dataset.jsonl'")

        mapping_key = 'deepar_input_data/time_series_mapping_with_labels.json'
        s3.put_object(Bucket=bucket_name, Key=mapping_key, Body=time_series_mapping_json)
        print(f"Mapping file saved to s3://{bucket_name}/{mapping_key}")

        label_to_int_key = 'deepar_input_data/label_to_int_mapping.json'
        s3.put_object(Bucket=bucket_name, Key=label_to_int_key, Body=disease_map_json)
        print(f"Label-to-int mapping file saved to s3://{bucket_name}/{label_to_int_key}")

        state_map_key = 'deepar_input_data/state_map.json'
        s3.put_object(Bucket=bucket_name, Key=state_map_key, Body=state_map_json)
        print(f"state_map mapping file saved to s3://{bucket_name}/{state_map_key}")

        cardinality_str = json.dumps(cardinality) 
        
        try:
            print("Setting up SageMaker training job")
            # Client for SageMaker
            sagemaker_client = boto3.client('sagemaker')
            role = os.environ['SAGEMAKER_ROLE_ARN']
            
            print(f"Starting the SageMaker training job with role: {role}")
            training_job_name = trigger_sagemaker_training(sagemaker_client, bucket_name, transformed_key, role, cardinality_str)
            
            if training_job_name:
                wait_for_training_completion(sagemaker_client, training_job_name)
                 # Now invoke the second Lambda for predictions without waiting for it to finish
                lambda_client = boto3.client('lambda')
                payload = {
                    'training_job_name': training_job_name,
                }
                lambda_client.invoke(
                    FunctionName='arn:aws:lambda:us-east-2:047290901679:function:NNDSSDataFetcher-PredictionsLambdaFunction-jHBncip3gtsy',
                    InvocationType='Event',  # Asynchronous invocation (don't wait for 2nd lambda to finsh)
                    Payload=json.dumps(payload)
                )
                print("Prediction lambda invoked!")

            else:
                print("Failed to start the training job.")
                return {
                    'statusCode': 400,
                    'body': json.dumps("Training job could not be initiated.")
                }
          
            return {
                'statusCode': 200,
                'body': json.dumps("New data pulled and saved. DeepAR model input data created and new model trained successfully.")
            }
        
        except Exception as e:
            print(f"An error occurred trying to train the model : {str(e)}")
            return {
                'statusCode': 500,
                'body': json.dumps(f"An error occurred: {str(e)}")
            }
    else:
        print("S3 Data is up to date.")

        return {'statusCode': 200, 'body': json.dumps("Data is up to date.")}
