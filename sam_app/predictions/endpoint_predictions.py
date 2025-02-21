import boto3
import json
import time
import pandas as pd
from datetime import datetime, timedelta

from botocore.config import Config


def get_deepar_container_uri(region_name):
    # AWS account IDs that host SageMaker algorithm containers
    algorithm_containers = {
        #'us-west-1': '632365934929',
        #'us-west-2': '174872318107',
        #'us-east-1': '382416733822',
        'us-east-2': '566113047672',
    }
    account_id = algorithm_containers.get(region_name)
    if not account_id:
        raise ValueError(f"No container account available for region {region_name}")
    
    return f"{account_id}.dkr.ecr.{region_name}.amazonaws.com/forecasting-deepar:1"
# https://docs.aws.amazon.com/sagemaker/latest/dg-ecr-paths/sagemaker-algo-docker-registry-paths.html


############ deploying prediction endpoint and making predictions

def load_deepar_training_data(bucket, key):
    s3 = boto3.client('s3')
    obj = s3.get_object(Bucket=bucket, Key=key)
    data = obj['Body'].read().decode('utf-8')
    deepar_training = data.strip().split('\n')
    deepar_training = [json.loads(line) for line in deepar_training]
    return deepar_training


def load_json_from_s3(bucket, key):
    """Load JSON data from an S3 bucket."""
    s3 = boto3.client('s3')
    try:
        response = s3.get_object(Bucket=bucket, Key=key)
        json_data = json.loads(response['Body'].read().decode('utf-8'))
        return json_data
    except Exception as e:
        print(f"Failed to load JSON from {bucket}/{key}: {str(e)}")
        return None

    
def create_sagemaker_model(sagemaker_client, model_data_url, role):
    model_name = 'deepar-model-' + time.strftime("%Y-%m-%d-%H-%M-%S", time.gmtime())
    primary_container = {
        'Image': '566113047672.dkr.ecr.us-east-2.amazonaws.com/forecasting-deepar:1',  # US East 2
        'ModelDataUrl': model_data_url
    }
    create_model_response = sagemaker_client.create_model(
        ModelName=model_name,
        ExecutionRoleArn=role,
        PrimaryContainer=primary_container
    )
    print(f"Model created: {model_name}")
    return model_name


def create_endpoint_config(sagemaker_client, model_name, instance_type='ml.m4.2xlarge'):
    endpoint_config_name = 'deepar-endpoint-config-' + time.strftime("%Y-%m-%d-%H-%M-%S", time.gmtime())
    response = sagemaker_client.create_endpoint_config(
        EndpointConfigName=endpoint_config_name,
        ProductionVariants=[{
            'InstanceType': instance_type,
            'InitialInstanceCount': 1,
            'ModelName': model_name,
            'VariantName': 'AllTraffic'
        }]
    )
    print(f"Endpoint Config created: {endpoint_config_name}")
    return endpoint_config_name


def create_and_deploy_endpoint(sagemaker_client, endpoint_config_name):
    endpoint_name = 'deepar-endpoint-' + time.strftime("%Y-%m-%d-%H-%M-%S", time.gmtime())
    response = sagemaker_client.create_endpoint(
        EndpointName=endpoint_name,
        EndpointConfigName=endpoint_config_name
    )
    print(f"Endpoint created and in service: {endpoint_name}")
    return endpoint_name


def wait_for_endpoint_to_be_in_service(sagemaker_client, endpoint_name, timeout_minutes=14):
    start_time = time.time()  # Record the start time
    timeout = start_time + 60 * timeout_minutes  # Timeout in seconds
    while True:
        current_time = time.time()
        elapsed_time = current_time - start_time
        response = sagemaker_client.describe_endpoint(EndpointName=endpoint_name)
        status = response['EndpointStatus']
        if status == 'InService':
            print(f"Endpoint {endpoint_name} is in service after {elapsed_time // 60} minutes {elapsed_time % 60:.0f} seconds.")
            break
        elif status in ['Failed', 'Deleting', 'Deleted']:
            raise Exception(f"Endpoint status is {status}, cannot continue.")
        elif current_time > timeout:
            raise TimeoutError(f"Timed out waiting for endpoint to be in service after {timeout_minutes} minutes.")
        else:
            print(f"Endpoint status: {status}. Waiting for it to be in service. Elapsed time: {int(elapsed_time // 60)} minutes {elapsed_time % 60:.0f} seconds.")
            time.sleep(20)


def invoke_endpoint(sagemaker_runtime_client, endpoint_name, full_payload):

    full_payload = json.dumps(full_payload)

    response = sagemaker_runtime_client.invoke_endpoint(
        EndpointName=endpoint_name,
        ContentType='application/json',
        Body=full_payload
    )
    predictions = response['Body'].read().decode('utf-8')
    return predictions


def deploy_model_with_boto3(sagemaker_client, model_data_url, role, instance_type='ml.m4.xlarge'):
    # Create the SageMaker model
    model_name = create_sagemaker_model(sagemaker_client, model_data_url, role)
    # Create the endpoint configuration
    endpoint_config_name = create_endpoint_config(sagemaker_client, model_name, instance_type)
    # Deploy the endpoint
    endpoint_name = create_and_deploy_endpoint(sagemaker_client, endpoint_config_name)
    return endpoint_name


def predict_with_boto3(sagemaker_runtime_client, endpoint_name, payload):
    # Make a prediction
    return invoke_endpoint(sagemaker_runtime_client, endpoint_name, payload)


def delete_sagemaker_endpoint(sagemaker_client, endpoint_name):
    # Delete the endpoint
    sagemaker_client.delete_endpoint(EndpointName=endpoint_name)
    print(f"Endpoint {endpoint_name} deleted")


def save_preds_to_s3(prediction_df,s3_path):
    
    prediction_df.to_parquet(s3_path, engine='pyarrow', index=False)
    print(f"prediction df saved to {s3_path}")


def find_max_date(deepar_training):
    latest_dates = []
    for series in deepar_training:
        start_date = datetime.strptime(series['start'], "%Y-%m-%d")
        # Assuming weekly frequency, calculate the end date of each series
        end_date = start_date + timedelta(weeks=len(series['target']) - 1)
        latest_dates.append(end_date)

    # Find the maximum date across all series, which is the last known date in the dataset
    max_date = max(latest_dates)
    return max_date


def list_all_endpoints(sagemaker_client, status_filter=None):
    """List all endpoints, optionally filtered by status."""
    endpoints = []
    paginator = sagemaker_client.get_paginator('list_endpoints')
    for page in paginator.paginate():
        for endpoint in page['Endpoints']:
            if status_filter:
                if endpoint['EndpointStatus'] == status_filter:
                    endpoints.append(endpoint['EndpointName'])
            else:
                endpoints.append(endpoint['EndpointName'])
    return endpoints


def delete_all_endpoints(sagemaker_client, status_filter='InService'):
    """Delete all endpoints, optionally filtered by their status."""
    endpoints = list_all_endpoints(sagemaker_client, status_filter=status_filter)
    for endpoint_name in endpoints:
        try:
            sagemaker_client.delete_endpoint(EndpointName=endpoint_name)
            print(f"Deleted endpoint: {endpoint_name}")
        except Exception as e:
            print(f"Failed to delete endpoint {endpoint_name}: {str(e)}")


def create_pred_df(prediction, bucket_name, deepar_training, ts_mapping_file_key='deepar_input_data/time_series_mapping_with_labels.json'):


    time_series_mapping = load_json_from_s3(bucket_name, ts_mapping_file_key)

    last_known_date = find_max_date(deepar_training)

    # The prediction_for_date is the next time period (e.g., the next week) after the last known date
    prediction_for_date = pd.to_datetime(last_known_date + timedelta(weeks=1))
    print(f"The prediction is for the date: {prediction_for_date.strftime('%Y-%m-%d')}")

    prediction_data = []

    # Directly map indices back to item_ids
    index_to_item_id = {v['index']: k for k, v in time_series_mapping.items()}

    for idx, pred in enumerate(prediction['predictions']):

        item_id = index_to_item_id[idx]

        prediction_data.append({
            'item_id': item_id,
            'pred_mean': pred['mean'],
            'pred_median': pred['quantiles']['0.5'],
            'pred_lower_0_001': pred['quantiles']['0.001'],
            'pred_upper_0_999': pred['quantiles']['0.999'],
            'pred_lower_0_01': pred['quantiles']['0.01'],
            'pred_upper_0_99': pred['quantiles']['0.99'],
            'pred_lower_0_03': pred['quantiles']['0.03'],
            'pred_upper_0_97': pred['quantiles']['0.97'],
            'pred_lower_0_05': pred['quantiles']['0.05'],
            'pred_upper_0_95': pred['quantiles']['0.95'],
            'pred_lower_0_1': pred['quantiles']['0.1'],
            'pred_upper_0_9': pred['quantiles']['0.9'],
            'pred_lower_0_2': pred['quantiles']['0.2'],
            'pred_upper_0_8': pred['quantiles']['0.8'],
        })

    prediction_df = pd.DataFrame(prediction_data)
    prediction_df['prediction_for_date'] = prediction_for_date

    columns_to_process = [
        'pred_mean', 'pred_median', 
        'pred_lower_0_001', 'pred_upper_0_999', 
        'pred_lower_0_01', 'pred_upper_0_99', 
        'pred_lower_0_03', 'pred_upper_0_97', 
        'pred_lower_0_05', 'pred_upper_0_95', 
        'pred_lower_0_1', 'pred_upper_0_9', 
        'pred_lower_0_2', 'pred_upper_0_8'
    ]

    for col in columns_to_process:
        prediction_df[col] = prediction_df[col].apply(lambda x: x[0] if isinstance(x, list) and x else None)
    
    bucket_name = 'nndss'
    folder_path = 'predictions'
    file_name = f"weekly_predictions_{prediction_for_date.strftime('%Y-%m-%d')}.parquet"
    s3_path = f's3://{bucket_name}/{folder_path}/{file_name}'

    save_preds_to_s3(prediction_df, s3_path)
    print(f"prediction dataset created and saved to {s3_path}")
    

def create_pred_endpoint_predict_save(training_job_name):

    my_config = Config(
        read_timeout=600,   # 10 minutes
        connect_timeout=120,
        retries={"max_attempts": 0}
    )

    sagemaker_client = boto3.client('sagemaker')
    sagemaker_runtime_client = boto3.client('sagemaker-runtime', config=my_config)

    role = 'arn:aws:iam::047290901679:role/sagemaker-deepar-deployment'

    bucket_name = 'nndss'
    key = 'deepar_input_data/deepar_dataset.jsonl'

    # 1) Load the entire training data
    deepar_training = load_deepar_training_data(bucket_name, key)

    # 2) Deploy the model as before
    model_data_url = f"s3://{bucket_name}/deepar/output/{training_job_name}/output/model.tar.gz"
    endpoint_name = deploy_model_with_boto3(sagemaker_client, model_data_url, role, instance_type='ml.m4.2xlarge')
    wait_for_endpoint_to_be_in_service(sagemaker_client, endpoint_name)

    # We'll break the "instances" into multiple chunks so each real-time inference call is smaller.
    BATCH_SIZE = 200   # or whatever chunk size you want
    aggregated_predictions = []  # we'll store the partial results here

    # 3) Loop over the data in chunks
    for start_idx in range(0, len(deepar_training), BATCH_SIZE):
        end_idx = start_idx + BATCH_SIZE
        chunk = deepar_training[start_idx:end_idx]

        # Build a chunk-level input payload
        predictor_input = {
            "instances": chunk,
            "configuration": {
                "num_samples": 200,
                "output_types": ["mean", "quantiles"],
                "quantiles": [
                    "0.001", "0.999", "0.01", "0.99", "0.03", "0.97", "0.05", "0.95",
                    "0.1", "0.9", "0.2", "0.8", "0.5"
                ]
            }
        }

        # 4) Invoke the endpoint on this chunk
        chunk_prediction_str = predict_with_boto3(sagemaker_runtime_client, endpoint_name, predictor_input)
        chunk_prediction = json.loads(chunk_prediction_str)

        # chunk_prediction is a dict like {"predictions": [...pred objects...]}
        # We'll accumulate them in aggregated_predictions
        aggregated_predictions.extend(chunk_prediction["predictions"])

    # 5) Now we have a single list of predictions in the original order
    # Construct a final dict so create_pred_df can read it
    final_prediction = {"predictions": aggregated_predictions}

    # 6) Delete the endpoint
    delete_sagemaker_endpoint(sagemaker_client, endpoint_name)

    # 7) Call create_pred_df with the combined predictions
    create_pred_df(final_prediction, bucket_name, deepar_training,
                   ts_mapping_file_key='deepar_input_data/time_series_mapping_with_labels.json')
