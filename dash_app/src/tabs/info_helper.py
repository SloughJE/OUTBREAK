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
data_title = "Data Source"

# CDC NNDSS data
data_source_title = "CDC NNDSS Weekly Data"
data_source_text = """
The CDC publishes weekly cases for all nationally nofiable diseases, accessible by their API.
"""

# Section Titles
modeling_title = "Potential Outbreaks Model and Automated Weekly Training"

# Model
modeling_subtitle = "Potential Outbreaks Model"
modeling_text = """
The model used to identify Potential Outbreaks is the Amazon Sagemaker DeepAR model, a type of recurrent neural network designed for forecasting on multiple time series. 
The model is probabilistic, meaning that it predicts a full probability distribution for each future time point, not just a single value. 
We use the Negative Binomial distribution to model the output, 
which is particularly suited for count data with overdispersion, a common characteristic in epidemiological data like disease incidence counts. 

A Potential Outbreak is flagged when the actual observed cases exceed the upper bound threshold of the predicted interval. 
This threshold is adjustable, allowing users to define what constitutes an outbreak based on their desired level of certainty regarding the model's predictions.
"""

# Weekly Data Retrieval and Model Training
automated_title = "Automated Weekly Data Retrieval and Model Training"
automated_text = """
Every week, we check if new data has been released from the CDC's NNDSS API. 
If new weekly data is available, it's fetched and stored.
With the new data in place, a SageMaker training job is triggered. This retraining incorporates the latest data to ensure the model reflects the most current trends and information.
Once the model is finished training, predictions are made for the next week.
When new data is available, these predictions are compared to the actual data in order to identify Potential Outbreaks.
"""
