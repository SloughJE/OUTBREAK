import os
import pandas as pd
from pathlib import Path

from gluonts.dataset.pandas import PandasDataset
from gluonts.torch import DeepAREstimator
from gluonts.torch.distributions.negative_binomial import NegativeBinomialOutput


def train_prod_model(
        input_filepath="data/interim/df_NNDSS_historical.pkl"
        ):
    
    prediction_length = 1

    
    df = pd.read_pickle(input_filepath)
    # testing
    df = df[df.date<pd.to_datetime("2024-03-04")]

    max_date_str = df['date'].max().strftime('%Y-%m-%d')
    min_date_str = df['date'].min().strftime('%Y-%m-%d')
    print(f"date range in training data: {min_date_str} to {max_date_str}")

    model_ds = PandasDataset.from_long_dataframe(df, target='new_cases', item_id='item_id', 
                                                timestamp='date', freq='W')

                                                
    estimator = DeepAREstimator(
        prediction_length=prediction_length,
        freq="W",
        distr_output=NegativeBinomialOutput(),
        trainer_kwargs={"max_epochs": 5}
    )

    predictor = estimator.train(model_ds)
    
    output_dir = f"models/{max_date_str}/"
    if not os.path.exists(output_dir):
        print(f"creating output dir: {output_dir}")
        os.makedirs(output_dir)
    predictor.serialize(Path(output_dir))
    print(f"model saved to: {output_dir}")

    # predict the next week and process into a dataframe
    preds = list(predictor.predict(model_ds))
    start_date = df['date'].max() + pd.Timedelta(weeks=1)
    prediction_dates = pd.date_range(start=start_date, periods=prediction_length, freq='7D')
    print(prediction_dates)

    all_preds = []

    for i, forecast in enumerate(preds):
        item_id = forecast.item_id
        pred_df = pd.DataFrame({
            'date': prediction_dates,
            'item_id': item_id,
            'pred_mean': forecast.mean,
            'pred_lower': forecast.quantile(0.01),
            'pred_upper': forecast.quantile(0.99)
        })
        all_preds.append(pred_df)

    all_preds_df = pd.concat(all_preds, ignore_index=True)
    print("prediction dataset:")
    print(all_preds_df.head())
    output_filepath = f"data/results/df_preds_{start_date.strftime('%Y-%m-%d')}.pkl"
    all_preds_df.to_pickle(output_filepath)
    print(f"predictions for {start_date.strftime('%Y-%m-%d')} saved to {output_filepath}")