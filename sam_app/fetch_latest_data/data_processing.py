import pandas as pd


def align_data_schema(df):
    """
    Transforms the data fetched from the API to the desired schema.
    """
    
    df.rename(columns={'states': 'state'}, inplace=True)  # Renaming 'states' to 'state'
    df['item_id'] = df['state'] + '_' + df['label']  # Using the renamed 'state' column
    df['date'] = pd.to_datetime(df['year'].astype(str) + df['week'].astype(str) + '-1', format='%Y%W-%w')
    df['new_cases'] = pd.to_numeric(df['m1'], errors='coerce')
    df['week'] = df.week.astype(int)
    df['year'] = df.year.astype(int)
    # Ensure the DataFrame has only the expected columns, in the correct order
    expected_columns = ['item_id', 'year', 'week','state', 'date', 'label', 'new_cases']
    # Reorder or filter the DataFrame to match the expected schema
    df = df[expected_columns]
    
    return df