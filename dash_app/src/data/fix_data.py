import pandas as pd

def remove_dates_in_data(filepath_historical="/home/ec2-user/dash_app/NNDSS/dash_app/data/df_historical.parquet",
                  filepath_predictions="/home/ec2-user/dash_app/NNDSS/dash_app/data/df_predictions.parquet"):

    df_historical = pd.read_parquet(filepath_historical)
    df_preds_all = pd.read_parquet(filepath_predictions)
    
    print(df_historical.tail())
    df_historical = df_historical[df_historical['date'] < df_historical['date'].max()]
    print(df_historical.tail())

    print(df_preds_all.tail())
    df_preds_all = df_preds_all[df_preds_all['date'] < df_preds_all['date'].max()]
    print(df_preds_all.tail())

    df_historical.to_parquet(filepath_historical)
    print(f"saved data to {filepath_historical}")
    df_preds_all.to_parquet(filepath_predictions)
    print(f"saved data to {filepath_predictions}")

    
remove_dates_in_data(filepath_historical="/home/ec2-user/dash_app/NNDSS/dash_app/data/df_historical.parquet",
                  filepath_predictions="/home/ec2-user/dash_app/NNDSS/dash_app/data/df_predictions.parquet")