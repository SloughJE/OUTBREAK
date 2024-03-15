import requests
import os
import pandas as pd


def get_latest_data(nndss_app_token, 
                        base_url = "https://data.cdc.gov/resource/x9gk-5huc.json",
                        output_dir="data/raw/latest"):
    
    columns = 'states,year,week,label,m1'

    base_url = "https://data.cdc.gov/resource/x9gk-5huc.json"


    # Fetch the most recent records based on year and week, where location1 is not null
    query_url = f"{base_url}?$$app_token={nndss_app_token}&$select={columns}&$where=location1 IS NOT NULL&$order=year DESC, week DESC&$limit=1"

    response = requests.get(query_url)

    if response.status_code == 200:
        latest_record = response.json()
        if latest_record:
            # Extract the year and week from the most recent record
            latest_year = latest_record[0]['year']
            latest_week = latest_record[0]['week']
            
            # Now fetch all records for the most recent year and week, where location1 is not null
            week_data_query_url = f"{base_url}?$$app_token={nndss_app_token}&$select={columns}&$where=year='{latest_year}' AND week='{latest_week}' AND location1 IS NOT NULL AND label NOT LIKE '%25Probable%25'"

            week_data_response = requests.get(week_data_query_url)
            
            if week_data_response.status_code == 200:
                latest_week_data = week_data_response.json()
                print(f"Data for the most recent week of year {latest_year}, week {latest_week}")
            else:
                print(f"Failed to fetch data for the latest week: {week_data_response.status_code}")
        else:
            print("No recent data found.")
    else:
        print(f"Failed to fetch the latest data: {response.status_code}")

    # Convert to DataFrame
    df = pd.DataFrame(latest_week_data)
    print(f"Total rows fetched: {len(df)}")
    print(df.head())

    filepath_out = f"{output_dir}/df_NNDSS_{latest_week}_{latest_year}.pkl"
    if not os.path.exists(output_dir):
        print(f"creating output dir: {output_dir}")
        os.makedirs(output_dir)

    df.to_pickle(filepath_out)
    print(f"latest data saved to: {filepath_out}")