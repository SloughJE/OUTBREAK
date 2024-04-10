import pandas as pd
import requests
import os


def get_historical_data(nndss_app_token, 
                        base_url = "https://data.cdc.gov/resource/x9gk-5huc.json",
                        output_dir="data/raw/historical"):
    

    columns = 'states,year,week,label,m1'
    # Initialize parameters for pagination
    limit = 50000  
    offset = 0
    data = []

    while True:

        # location1 is not null gets only states / territories (not regions or country total)
        query_url = f"{base_url}?$$app_token={nndss_app_token}&$select={columns}&$where=location1 IS NOT NULL &$limit={limit}&$offset={offset}"

        response = requests.get(query_url)
        
        if response.status_code != 200:
            print(f"Failed to fetch data: {response.status_code}")
            break
        
        batch = response.json()
        
        if not batch:
            # If the batch is empty, we've reached the end of the dataset
            break
        
        data.extend(batch)
        offset += limit
        print(f"Fetched {len(batch)} rows, total: {len(data)}")

    # Convert to DataFrame
    df = pd.DataFrame(data)
    print(f"Total rows fetched: {len(df)}")
    print(df.head())

    filepath_out = f"{output_dir}/df_NNDSS_historical.parquet"
    
    if not os.path.exists(output_dir):
        print(f"creating output dir: {output_dir}")
        os.makedirs(output_dir)
    
    df.to_parquet(filepath_out)
    print(f"historical data saved to: {filepath_out}")



