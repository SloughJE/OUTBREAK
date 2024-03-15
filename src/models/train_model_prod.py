import pandas as pd

from gluonts.dataset.pandas import PandasDataset
from gluonts.torch import DeepAREstimator
from gluonts.torch.distributions.negative_binomial import NegativeBinomialOutput


def train_prod_model(
        input_filepath="data/interim/df_NNDSS_historical.pkl"
        ):
    
    prediction_length = 3

    df = pd.read_pickle(input_filepath)
    
    model_ds = PandasDataset.from_long_dataframe(df, target='new_cases', item_id='item_id', 
                                                timestamp='date', freq='W')

                                                
    # Train the model and make predictions
    estimator = DeepAREstimator(
        prediction_length=prediction_length,
        freq="W",
        distr_output=NegativeBinomialOutput(),
        trainer_kwargs={"max_epochs": 5}
    )

    model = estimator.train(model_ds)


    preds = list(model.predict(model_ds))
    start_date = df['date'].max() + pd.Timedelta(days=7)
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

    all_preds_df.to_pickle("data/results/df_preds.pkl")