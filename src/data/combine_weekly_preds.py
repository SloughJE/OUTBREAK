import pandas as pd
import glob


def combine_weekly_preds_for_dash_app(directory_path = "data", output_filepath = "dash_app/data/df_predictions.parquet"):


    file_pattern = f"{directory_path}/weekly_predictions*.parquet"  

    file_list = glob.glob(file_pattern)
    dfs = []

    for filename in file_list:
        df = pd.read_parquet(filename)  
        dfs.append(df)

    concatenated_df = pd.concat(dfs, ignore_index=True)
    concatenated_df.rename(columns={"prediction_for_date":"date"},inplace=True)
    concatenated_df.to_parquet(output_filepath)
    print(concatenated_df.head(2))
    print(concatenated_df.tail(2))
    
    print(f"weekly predictions combined and saved to: {output_filepath}")

