import boto3
from botocore.exceptions import NoCredentialsError
from dotenv import load_dotenv
import os
import pandas as pd


# Load environment variables from .env file
load_dotenv()
aws_access_key = os.getenv('aws_access_key')
aws_secret_key = os.getenv('aws_secret_key')

# Initialize a session using your AWS credentials
session = boto3.Session(
    aws_access_key_id=aws_access_key,
    aws_secret_access_key=aws_secret_key,
    region_name='us-east-2' # e.g. us-west-2
)

# Create an S3 client using the session
s3_client = session.client('s3')

def upload_files_in_folder_to_s3(local_folder, bucket_name, object_key_prefix):

    # get list of files in folder
    file_list = os.listdir(local_folder)
    for fl in file_list:
        local_file_path = f"{local_folder}{fl}"
        object_key = f"{object_key_prefix}{fl}"
        upload_file_to_s3(local_file_path, bucket_name, object_key)
    
    print(f"uploaded all files in {local_folder}")


def upload_file_to_s3(local_file_path, bucket_name, object_key):
    try:
        with open(local_file_path, "rb") as f:
            s3_client.upload_fileobj(f, bucket_name, object_key)
        print(f"File {local_file_path} uploaded to {bucket_name}/{object_key}")
    except FileNotFoundError:
        print(f"The file {local_file_path} was not found")
    except NoCredentialsError:
        print("Credentials not available")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

# Example usage:
#https://nndss.s3.us-east-2.amazonaws.com/historical/