import os
import pandas as pd

from src.data.data_utils import year_week_to_date


def process_data(
        input_filepath = "data/raw/latest/df_NNDSS_10_2024.pkl",
        output_filepath = "data/interim/df_NNDSS_latest.pkl"
        ):

    df = pd.read_pickle(input_filepath)
    
    df.columns = ['state','year','week','label','new_cases']

    df['week'] = df.week.astype(int)
    df['year'] = df.year.astype(int)
    # Update the 'date' column with the calculated Monday dates
    #df['date'] = df.apply(lambda row: year_week_to_date(int(row['year']), int(row['week'])), axis=1)
    df['date'] = pd.to_datetime(df['year'].astype(str) + '-' + df['week'].astype(str) + '-1', format='%Y-%W-%w')

    df['item_id'] = df['state'] + '_' + df['label']
    df.sort_values(['item_id', 'date'], inplace=True)

    # fill 0 for NA
    df['new_cases'] = df.groupby('item_id')['new_cases'].transform(lambda x: x.ffill().bfill().fillna(0))
    df['new_cases'] = df.new_cases.astype(int)

    df = df[['item_id','year','week','date','label','new_cases']]

    print(df.head())
    
    print("dtypes:")
    print(df.dtypes)

    na_counts = df.isna().sum()
    print("NaN Counts:")
    print(na_counts)

    df.to_pickle(output_filepath)
    print(f"latest data saved to: {output_filepath}")