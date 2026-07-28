# Section Titles
dashboard_information_title = "Dashboard Information"

# Developed by
developed_by = "JS Data Science Services LLC"

# Goal of Dashboard
dashboard_info_title = "Dashboard Overview"

# Tab Information
tab_information_title = "Tabs Information"

# Summary Tab
summary_tab_title = "Latest Week"

summary_tab_data = (
    "Summarizes potential-outbreak signals for the latest available reporting week. "
    "The tab includes total signals, diseases, and jurisdictions flagged; a map of "
    "signals by state; a comparison of previous-week and latest-week signals; and a "
    "table of all latest-week signals classified as New or Ongoing. New York City is "
    "represented separately from New York State in the source data."
)


# Disease Explorer Tab
disease_tab_title = "Disease Explorer"

disease_tab_data = (
    "Allows the user to examine a selected state/territory–disease series. The tab "
    "displays historical weekly case counts, the model median and certainty interval, "
    "and the latest potential-outbreak status. It also provides summary statistics for "
    "a selected 12-, 26-, or 52-week period, including total reported cases, flagged "
    "weeks, potential-outbreak episodes, and peak weekly cases. Disease classification "
    "and transmission information are also provided."
)


# Outbreak Trends Tab
outbreaks_tab_title = "Outbreak Trends"

outbreaks_tab_data = (
    "Summarizes how model-generated potential-outbreak signals have changed over time. "
    "The tab displays weekly counts of newly started potential-outbreak episodes, a "
    "four-week rolling average, and counts of ongoing signals. Users may select a "
    "display period and optionally filter the results by state or territory. Summary "
    "metrics are provided for the selected period."
)

# Section Titles
data_title = "Data"

# CDC NNDSS data
data_source_title = "CDC NNDSS Weekly Data"
data_source_text = """
The data source for this dashboard is the CDC NNDSS (Nationally Notifiable Disease Surveillance System) which publishes weekly cases for all nationally notifiable diseases, 
accessible by their API, on a State/Territory level. 
'The National Notifiable Disease Surveillance System (NNDSS) is a nationwide collaboration that enables all levels of public health (local, \
    state, territorial, federal, and international) to share health information to monitor, control, and prevent the occurrence and spread of state-reportable and nationally notifiable \
        infectious and some noninfectious diseases and conditions.'
Typically, there is a 1 to 2 week lag between the end of the current week and the release of its corresponding data.
Note that New York City is treated as a separate reporting entity, distinct from New York state, meaning that case counts for NYC are \
not included in those for the state.\n
A single time series in our data is considered to be the number of weekly cases of a specific disease in a specific State or Territory (or NYC), for example weekly case counts for the disease Cryptosporidiosis in Kentucky.
Our data has over 7,000 unique time series. 
"""

# Section Titles
modeling_title = "Potential Outbreaks Model and Automated Weekly Retraining"

# Model
modeling_subtitle = "Potential Outbreaks Model"
modeling_text = """
The model used to identify Potential Outbreaks is the Amazon Sagemaker DeepAR model, a type of autoregressive recurrent neural network designed for \
    forecasting across a large number of related time series. \
It operates as a global model, which means that it doesn't model each time series independently; instead it creates a single model that learns from many related time series. \
As DeepAR learns from similar time series, it is capable of providing forecasts for those with little or no historical data. 
The model is probabilistic, predicting a full probability distribution for each future time point, rather than just a single value. \
We use the Negative Binomial distribution to model the output, \
which is well-suited for count data with overdispersion, a common characteristic in epidemiological data like disease case counts. \
All of these features make DeepAR an effective choice for modeling disease cases on a state/territory level.

Defining a Potential Outbreak:
A Potential Outbreak is identified when the actual observed cases exceed the upper bound threshold of the predicted distribution for a specific time series. \
This threshold is adjustable, allowing users to define what constitutes an outbreak based on their desired level of certainty regarding the model's predictions. \
The "Outbreak Model Certainty Level" of the dashboard corresponds to the model's predicted upper quantile. In other words, \
an Outbreak Model Certainty Level of 99% means we use the 99th percentile of the predicted distribution values as the threshold for identifying a "Potential Outbreak".

Essentially, with our model, we determine the typical range of cases for a disease in a specific state or territory for the next week. \
Then, when the actual data becomes available, we check to see if the actual cases exceeds our chosen threshold for that predicted distribution. If it does, it's a "Potential Outbreak".
"""

# Weekly Data Retrieval and Model Training
automated_title = "Automated Weekly Model Retraining"
automated_text = """
Every week, we check if new data has been released from the CDC's NNDSS API.
If new weekly data is available, it's fetched and stored.
With the new data in place, a SageMaker training job is triggered. This retraining incorporates the latest data to ensure the model reflects the most current trends and information.
Once the model is finished retraining, predictions are made for the next week.
When the subsequent week's data becomes available, these predictions are compared to the actual data for that week to identify potential outbreaks.
"""
