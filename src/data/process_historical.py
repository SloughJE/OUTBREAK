import os
import pandas as pd
import numpy as np
from src.data.data_utils import year_week_to_date, get_weeks_in_year, fill_weekly_gaps
import pandas as pd
from sam_app.fetch_latest_data.data_processing import align_data_schema


def process_data_historical(
        input_filepath = "data/raw/historical/df_NNDSS_historical.pkl",
        output_filepath = "data/interim/df_NNDSS_historical.parquet"
        ):

   df = pd.read_pickle(input_filepath)

   #df.columns = ['state','year','week','label','new_cases']


   #df['week'] = df.week.astype(int)
   #df['year'] = df.year.astype(int)
   # Update the 'date' column with the calculated Monday dates
   #df['date'] = df.apply(lambda row: year_week_to_date(int(row['year']), int(row['week'])), axis=1)
   #df['date'] = pd.to_datetime(df['year'].astype(str) + '-' + df['week'].astype(str) + '-1', format='%Y-%W-%w')

   #df['item_id'] = df['state'] + '_' + df['label']
   df = align_data_schema(df)

   ############# testing
   item_ids = ['ARKANSAS_Chlamydia trachomatis infection', 'ARKANSAS_Gonorrhea',
      'CALIFORNIA_Campylobacteriosis','ARIZONA_Campylobacteriosis',
      'CALIFORNIA_Chlamydia trachomatis infection',
      'CALIFORNIA_Gonorrhea', 'COLORADO_Chlamydia trachomatis infection',
      'COLORADO_Gonorrhea', 'DELAWARE_Chlamydia trachomatis infection',
      'FLORIDA_Chlamydia trachomatis infection', 'FLORIDA_Gonorrhea',
      'GEORGIA_Chlamydia trachomatis infection', 'GEORGIA_Gonorrhea',
      'IDAHO_Chlamydia trachomatis infection',
      'ILLINOIS_Chlamydia trachomatis infection',]
   #df = df[df.item_id.isin(item_ids)]
   ###########

   df.sort_values(['item_id', 'date'], inplace=True)

   # fill 0 for NA
   #df['new_cases'] = df.groupby('item_id')['new_cases'].transform(lambda x: x.ffill().bfill().fillna(0))
   df['new_cases'] = df['new_cases'].astype(float)

   # check unique item_id
   print(f"unique item ids before filling gaps: {df.item_id.nunique()}")
         
   df = fill_weekly_gaps(df)
   print(f"unique item ids after filling gaps: {df.item_id.nunique()}")

   # fill in the state and label for the inserted rows if needed later
   df['state'] = df.groupby('item_id')['state'].ffill().bfill()
   df['label'] = df.groupby('item_id')['label'].ffill().bfill()

   # fill in any dates added by week/year
   df['date'] = pd.to_datetime(df['year'].astype(str) + '-' + df['week'].astype(str) + '-1', format='%Y-%W-%w')

   df['date'] = df['date'].values.astype('datetime64[ms]')
   #df = df[['item_id','year','week','date','label','new_cases','filled_value']]
   df['new_cases'] = df['new_cases'].astype(float)

   print(df.tail())
   print(f"dtypes: {df.dtypes}")

   na_counts = df.isna().sum()
   print(na_counts)



   df = df[df.date<pd.to_datetime("2024-03-04")]

   max_date_str = df['date'].max().strftime('%Y-%m-%d')
   min_date_str = df['date'].min().strftime('%Y-%m-%d')
   print(f"date range historical data: {min_date_str} to {max_date_str}")
   #df = df[df.filled_value==False]

   print(df.iloc[175:180])

   #df = df.drop(index=226)
   #df = df.drop(index=177)
   #df = df.drop(index=200)

   selected_item_id = "ARKANSAS_Chlamydia trachomatis infection"
   print(df[df.item_id==selected_item_id])
   #df.loc[177, 'new_cases'] = np.nan
   #df.loc[226, 'new_cases'] = 155
   #print(df.iloc[175:180])
   #print(df[df.date==pd.to_datetime("2024-02-26")])
   #print(df[(df.item_id==selected_item_id) & (df.filled_value==True)])
   #df.to_pickle(output_filepath)
   

   df.to_parquet(output_filepath, index=False, engine='pyarrow')
   import pyarrow.parquet as pq

   parquet_file = pq.read_table(output_filepath)
   print(parquet_file.schema)
   print(f"latest data saved to: {output_filepath}")