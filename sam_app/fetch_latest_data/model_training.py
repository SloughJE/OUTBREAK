import boto3
import json
import time
import pandas as pd
from datetime import datetime, timedelta


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

def trigger_sagemaker_training(client, bucket, data_key, role, cardinality):

    region = boto3.Session().region_name

    container = get_deepar_container_uri(region)
    print("Container URI for DeepAR:", container)
    # Setting up the training job name with a timestamp
    training_job_name = "deepar-training-job-" + time.strftime("%Y-%m-%d-%H-%M-%S", time.gmtime())
    print(f"Generated Training Job Name: {training_job_name}")

    training_params = {
        "TrainingJobName": training_job_name,
        "AlgorithmSpecification": {
            "TrainingImage": container,
            "TrainingInputMode": "File"
        },
        "RoleArn": role,
        "InputDataConfig": [{
            "ChannelName": "train",
            "DataSource": {
                "S3DataSource": {
                    "S3DataType": "S3Prefix",
                    "S3Uri": f's3://{bucket}/{data_key}',
                    "S3DataDistributionType": "FullyReplicated"
                }
            },
            "ContentType": "json",
            "CompressionType": "None",
            "RecordWrapperType": "None"
        }],
        "OutputDataConfig": {
            "S3OutputPath": f's3://{bucket}/deepar/output/'
        },
        "ResourceConfig": {
            "InstanceType": "ml.c4.xlarge",
            "InstanceCount": 1,
            "VolumeSizeInGB": 50
        },
        "StoppingCondition": {
            "MaxRuntimeInSeconds": 1200,  
            "MaxWaitTimeInSeconds": 1600  
        },
        "EnableManagedSpotTraining": True,  # Enable spot training
        "CheckpointConfig": {
            "S3Uri": f's3://{bucket}/checkpoints/',  # Checkpoint location for spot instance training
            "LocalPath": "/opt/ml/checkpoints"  # Optional local checkpointing
        },
        "HyperParameters": {
            "time_freq": 'W',                
            "epochs": '47',                  
            "context_length": '2',           
            "prediction_length": '1',        
            "likelihood": "negative-binomial",
            "learning_rate": "1E-4",
            "embedding_dimension": "3",  
            "cardinality": "auto" # str(cardinality)
        }
    }

    try:
        response = client.create_training_job(**training_params)
        print(f"Started SageMaker training job: {response['TrainingJobArn']}")
        return training_job_name  
    except KeyError as e:
        print(f"Key error: {str(e)} - Likely a key is missing in the response.")
        return None
    except Exception as e:
        print(f"An error occurred trying to train the model: {str(e)}")
        return None

