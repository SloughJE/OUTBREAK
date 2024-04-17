import json

from endpoint_predictions import create_pred_endpoint_predict_save


def lambda_handler(event, context):

    training_job_name = event.get('training_job_name')

    try:
        create_pred_endpoint_predict_save(training_job_name)
    except Exception as e:
        print(f"An error occurred during endpoint creation or prediction: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps(f"Endpoint creation or prediction failed: {str(e)}")
        }

    return {
        'statusCode': 200,
        'body': json.dumps("New data pulled and saved. DeepAR model input data, training, model creation, and prediction jobs have been successfully completed.")
    }
        