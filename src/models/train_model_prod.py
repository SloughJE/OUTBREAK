import os
import pandas as pd
from pathlib import Path

from gluonts.dataset.pandas import PandasDataset
from gluonts.torch import DeepAREstimator
from gluonts.torch.distributions.negative_binomial import NegativeBinomialOutput


def train_prod_model(
        input_filepath="data/interim/df_NNDSS_historical.parquet",
        prediction_for_dates=["2024-03-04"] 
        ):
    
    prediction_length = 1

    df = pd.read_parquet(input_filepath)
    df['label'] = df['label'].astype('category')

    print(f"training and predicting for dates: {prediction_for_dates}")
    # Loop through each date in the input dates list
    for date_str in prediction_for_dates:
        # Filter the dataframe for each date
        df_mod = df[df.date < pd.to_datetime(date_str)]

        max_date_str = df_mod['date'].max().strftime('%Y-%m-%d')
        min_date_str = df_mod['date'].min().strftime('%Y-%m-%d')
        print(f"date range in training data: {min_date_str} to {max_date_str}")
        
        # Identify the max date in df_mod
        max_date = df_mod['date'].max()
        # Check if all 'new_cases' values are NA on the max date
        if df_mod[df_mod['date'] == max_date]['new_cases'].isna().all():
            # If true, forward fill 'new_cases' from the previous date for all item_ids
            # First, sort df_mod by 'item_id' and 'date' to ensure correct forward fill
            df_mod.sort_values(by=['item_id', 'date'], inplace=True)
            df_mod['new_cases'] = df_mod.groupby('item_id')['new_cases'].ffill()

            print(f"forward filled last new cases value as ALL were NA due to needing regular date intervals, in GluonTS DeepAR this results in all 0s for predictions for some reason")
            print(df_mod.tail(3))

        model_ds = PandasDataset.from_long_dataframe(df_mod, target='new_cases', item_id='item_id', 
                                                    timestamp='date', freq='W',static_feature_columns=["label"])

        num_static_cat = 1  # Number of static categorical features
        cardinality = [len(df_mod['label'].unique())]  # Unique values of 'label'
                                                    
        estimator = DeepAREstimator(
            prediction_length=prediction_length,
            freq="W",
            num_feat_static_cat=num_static_cat,
            cardinality=cardinality,
            distr_output=NegativeBinomialOutput(),
            trainer_kwargs={"max_epochs": 25}
        )

        predictor = estimator.train(model_ds)
        
        output_dir = f"models/{max_date_str}/"
        if not os.path.exists(output_dir):
            print(f"creating output dir: {output_dir}")
            os.makedirs(output_dir)
        predictor.serialize(Path(output_dir))
        print(f"model saved to: {output_dir}")

        # predict the next week and process into a dataframe
        preds = list(predictor.predict(model_ds,num_samples=200))
        start_date = df_mod['date'].max() + pd.Timedelta(weeks=1)
        prediction_dates = pd.date_range(start=start_date, periods=prediction_length, freq='7D')
        print(prediction_dates)

        all_preds = []

        for i, forecast in enumerate(preds):
            item_id = forecast.item_id
            # Creating a DataFrame with additional quantile columns based on the second chunk
            pred_df = pd.DataFrame({
                'item_id': item_id,
                'pred_mean': forecast.mean,
                'pred_median': forecast.quantile(0.5),
                'pred_lower_0_001': forecast.quantile(0.001),
                'pred_upper_0_999': forecast.quantile(0.999),
                'pred_lower_0_01': forecast.quantile(0.01),
                'pred_upper_0_99': forecast.quantile(0.99),
                'pred_lower_0_03': forecast.quantile(0.03),
                'pred_upper_0_97': forecast.quantile(0.97),
                'pred_lower_0_05': forecast.quantile(0.05),
                'pred_upper_0_95': forecast.quantile(0.95),
                'pred_lower_0_1': forecast.quantile(0.1),
                'pred_upper_0_9': forecast.quantile(0.9),
                'pred_lower_0_2': forecast.quantile(0.2),
                'pred_upper_0_8': forecast.quantile(0.8),
                'prediction_for_date': prediction_dates,

            })
            all_preds.append(pred_df)

        all_preds_df = pd.concat(all_preds, ignore_index=True)
        print("prediction dataset:")
        print(all_preds_df.head(1))
        output_filepath = f"data/results/weekly_predictions_{start_date.strftime('%Y-%m-%d')}.parquet"
        all_preds_df.to_parquet(output_filepath)
        print(f"predictions for {start_date.strftime('%Y-%m-%d')} saved to {output_filepath}")