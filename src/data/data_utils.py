from datetime import datetime, timedelta
import pandas as pd
from tqdm.auto import tqdm
from datetime import datetime, timedelta, date


def year_week_to_date(year, week):
    """
    Convert a year and week number into the date of the Monday of that week.
    """
    # Calculate the first day of the year
    first_of_year = datetime(year, 1, 1)
    # ISO-8601 calculation for the first week of the year
    if first_of_year.weekday() > 3:  # If the first day is Friday or later
        # Move to the next Monday
        first_of_year += timedelta(days=7-first_of_year.weekday())
    else:
        # Move to the Monday of the current week
        first_of_year -= timedelta(days=first_of_year.weekday())
    
    # Calculate the Monday of the given week number
    week_start_date = first_of_year + timedelta(weeks=week-1)
    
    return week_start_date

def get_weeks_in_year(year):
    """Determine the number of ISO weeks in a given year."""
    last_day_of_year = date(year, 12, 28)  # ISO-8601; the week containing 28th Dec is the last week of the year
    return last_day_of_year.isocalendar()[1]

def fill_weekly_gaps(df):
    # Determine the maximum year and week present in the data for later use
    max_year = df['year'].max()
    max_week_for_max_year = df[df['year'] == max_year]['week'].max()

    all_combinations = []
    for item_id in tqdm(df['item_id'].unique(), desc='Filling gaps'):
        item_df = df[df['item_id'] == item_id]
        first_year = item_df['year'].min()
        last_year = item_df['year'].max()
        first_week = item_df[item_df['year'] == first_year]['week'].min()
        last_week = item_df[item_df['year'] == last_year]['week'].max()
        
        for year in df['year'].unique():
            if year < first_year or year > last_year:
                continue  # Skip years before the item_id first appears and after it last appears
            
            week_start = first_week if year == first_year else 1
            week_end = last_week if year == last_year else get_weeks_in_year(year)
            for week in range(week_start, week_end + 1):
                all_combinations.append({'item_id': item_id, 'year': year, 'week': week})
                
    all_combinations_df = pd.DataFrame(all_combinations)

    # Merge the generated combinations with the original DataFrame
    df_merged = pd.merge(all_combinations_df, df, on=['item_id', 'year', 'week'], how='left', indicator=True)
    
    # Carry forward the last observed 'new_cases', but only within the bounds of existing data for each item_id
    #df_merged['new_cases'] = df_merged.groupby('item_id')['new_cases'].ffill().bfill()

    # Mark filled values for new_cases
    df_merged['filled_value'] = df_merged['_merge'] == 'left_only'
    df_merged.drop(columns=['_merge'], inplace=True)

    return df_merged

def fill_missing_values_by_filltype(df):

    print("filling missing values strategically")
    print("creating sparsity metrics")
    sparsity_metrics = df.groupby(['item_id']).agg(
        sparsity=('new_cases', lambda x: x.isna().mean()),
        mean=('new_cases', 'mean')).reset_index()

    def assign_fill_type(row):

        sparsity_threshold = 0.5
        mean_threshold = 20
        
        if pd.isna(row['mean']):
            return "fill with 0"
        if row['sparsity'] < sparsity_threshold:
            return "no change"
        elif row['sparsity'] >= sparsity_threshold and row['mean'] < mean_threshold:
            return "fill with 0"
        elif row['sparsity'] >= sparsity_threshold and row['mean'] >= mean_threshold:
            return "linearly interpolate"

    # Apply the function to each row to determine the fill type
    sparsity_metrics['fill_type'] = sparsity_metrics.apply(assign_fill_type, axis=1)
    df = df.merge(sparsity_metrics[['item_id', 'fill_type']], on='item_id', how='left')
    def apply_fill_strategy(group):
        fill_type = group['fill_type'].iloc[0]  
        if fill_type == 'fill with 0':
            group['new_cases_filled'] = group['new_cases'].fillna(0)
        elif fill_type == 'linearly interpolate':
            group['new_cases_filled'] = group['new_cases'].interpolate().round() # NO DECIMALS FOR DEEP AR NEGATIVE BINOMIAL
        else:
            group['new_cases_filled'] = group['new_cases']
        return group
    df = df.groupby('item_id').apply(apply_fill_strategy)
    print("data filled with 0 or linear interpolation, depending on sparsity and mean")

    df = df[['item_id','year','week','state','date','label','new_cases_filled','fill_type']]
    df = df.rename(columns={'new_cases_filled':'new_cases'})

    return df