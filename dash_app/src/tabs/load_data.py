import pandas as pd
import glob

def load_preds(directory_path = "data"):


    file_pattern = f"{directory_path}/weekly_predictions*.parquet"  

    file_list = glob.glob(file_pattern)
    dfs = []

    for filename in file_list:
        df = pd.read_parquet(filename)  
        dfs.append(df)

    concatenated_df = pd.concat(dfs, ignore_index=True)
    concatenated_df.rename(columns={"prediction_for_date":"date"},inplace=True)
    return concatenated_df


def load_process_preds(df_historical):
    
    df_preds = load_preds(directory_path = "../data/results")
    df_mg = pd.merge(df_historical,df_preds,on=['item_id','date'])

    return df_mg

def get_outbreaks(df_historical):

    df_historical['potential_outbreak'] = df_historical['new_cases'] > df_historical['pred_upper_0_99']