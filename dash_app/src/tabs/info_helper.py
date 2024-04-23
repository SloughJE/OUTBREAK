# Section Titles
dashboard_information_title = "Dashboard Information"

# Developed by
developed_by = "JS Data Science Services LLC"

# Goal of Dashboard
dashboard_info_title = "Dashboard Overview"

# Tab Information
tab_information_title = "Tabs Information"

# Summary Tab
summary_tab_title = "Latest Week Summary"
summary_tab_data = (
    "Provides Summaries of Potential Outbreaks and Ongoing Potential Outbreaks in the USA (including territories) for the latest week the data is available. Note that in the source data New York City is defined as a separate entity from the state of New York."
)

# Profiles Tab
profiles_tab_title = "Outbreak Profiles"
profiles_tab_data = (
    "Provides an analysis of the types of outbreaks based on pathogen type, affected bodily system, and transmission type. Additionally, a table of all potential outbreaks with details is provided."
)

# Disease History Tab
disease_tab_title = "Disease History"

disease_tab_data = (
    "Displays a time series chart of the number of cases for a chosen disease, with the identification of Potential Outbreaks for the latest week. The model median and certainty interval is shown as well"
)

# Outbreaks History Tab
outbreaks_tab_title = "Outbreaks History"

outbreaks_tab_data = (
"Displays a time series chart of the number of Potential vs Resolved Outbreaks, and Ongoing Potential Outbreaks.")

# Section Titles
data_title = "Data"

# CDC NNDSS data
data_source_title = "CDC NNDSS Weekly Data"
data_source_text = """
The data source for this dashboard is the CDC NNDSS (Nationally Notifiable Disease Surveillance System) which publishes weekly cases for all nationally notifiable diseases, 
accessible by their API on a State/Territory level. Note that New York City is treated as a separate reporting entity, distinct from New York state, meaning that case counts for NYC are \
    not included in those for the state.\n
A single time series in our data is considered to be the number of weekly cases of a specific disease in a specific State or Territory (or NYC), for example case counts for the disease Cryptosporidiosis in Kentucky.
"""

# Section Titles
modeling_title = "Potential Outbreaks Model and Automated Weekly Retraining"

# Model
modeling_subtitle = "Potential Outbreaks Model"
modeling_text = """
The model used to identify Potential Outbreaks is the Amazon Sagemaker DeepAR model, a type of autoregressive recurrent neural network designed for forecasting on multiple related time series. \
It operates as a global model, which means that it doesn't model each time series independently, instead it creates a single model that learns from many related time series. \
DeepAR is probabilistic, predicting a full probability distribution for each future time point, rather than just a single value. \
We use the Negative Binomial distribution to model the output, \
which is well-suited for count data with overdispersion, a common characteristic in epidemiological data like disease case counts.

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
