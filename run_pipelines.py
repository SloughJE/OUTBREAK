import sys 
import yaml
import argparse
from dotenv import load_dotenv
import os

from src.data.request_historical import get_historical_data
from src.data.request_latest_week import get_latest_data
from src.data.process_latest import process_data
from src.data.process_historical import process_data_historical

# Load environment variables from .env file
load_dotenv()
nndss_app_token = os.getenv('NNDSS_APP_TOKEN')

if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--get_historical_data",
        help="pull historical data from CDC API",
        action="store_true"
    )
     
    parser.add_argument(
        "--get_latest_data",
        help="pull latest week data from CDC API",
        action="store_true"
    )

    parser.add_argument(
        "--process_data",
        help="process data",
        action="store_true"
    )

    parser.add_argument(
        "--process_historical_data",
        help="process historical data",
        action="store_true"
    )


    args = parser.parse_args()

    if len(sys.argv) == 1:
        print("No arguments, please add arguments")
    else:
        with open("params.yaml") as f:
            params = yaml.safe_load(f)

        if args.get_historical_data:
            get_historical_data(
                nndss_app_token, 
                base_url = "https://data.cdc.gov/resource/x9gk-5huc.json",
                output_dir="data/raw/historical"
                )


        if args.get_latest_data:
            get_latest_data(
                nndss_app_token, 
                base_url = "https://data.cdc.gov/resource/x9gk-5huc.json",
                output_dir="data/raw/latest"
                )
            
        if args.process_data:
            process_data(
                input_filepath = "data/raw/latest/df_NNDSS_10_2024.pkl",
                output_filepath = "data/interim/df_NNDSS_latest.pkl"
                )
            
        if args.process_historical_data:
            process_data_historical(
                input_filepath = "data/raw/historical/df_NNDSS_historical.pkl",
                output_filepath = "data/interim/df_NNDSS_historical.pkl"
                )
            