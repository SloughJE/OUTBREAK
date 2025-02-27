# OUTBREAK!

**Automatic Weekly Identification of Potential Outbreaks of CDC Nationally Notifiable Diseases**

This repository contains a dashboard and accompanying code that automatically retrieves weekly CDC NNDSS data, trains a DeepAR model on Amazon SageMaker, and identifies potential disease outbreaks at a state/territory-disease level. The application is built with [Plotly Dash](https://dash.plotly.com/) and containerized with Docker for consistent development and deployment. The dashboard is currently hosted on an Amazon EC2 instance and can be viewed at **[outbreak-tracker.com](https://outbreak-tracker.com/)**.

---

## Table of Contents
1. [Project Overview](#project-overview)  
2. [Key Features](#key-features)  
3. [Repository Structure](#repository-structure)  
4. [DeepAR Model and Outbreak Detection](#deepar-model-and-outbreak-detection)  
5. [CDC NNDSS Data Source](#cdc-nndss-data-source)  
6. [License and Credits](#license-and-credits)  

---

## Project Overview

**OUTBREAK!** is a dashboard that provides:
- **Potential Outbreaks**: Automatically flagged weekly based on case counts exceeding a chosen threshold of the DeepAR forecast distribution.  
- **Ongoing Potential Outbreaks**: Identified when a specific disease in a specific state or territory remains above the threshold for at least two consecutive weeks.  
- **Resolved Potential Outbreaks**: Marked when a disease was flagged one week but falls below the threshold the following week.  

The system regularly pulls the latest CDC NNDSS data, retrains the DeepAR model when new data is available, and updates the dashboard to reflect the most current potential outbreaks.

---

## Key Features

1. **Automatic Weekly Data Retrieval**  
   Pulls new data from the CDC NNDSS API as soon as it is published (typically 1–2 weeks after each reporting week ends).

2. **Automatic Weekly Model Retraining**  
   Uses Amazon SageMaker DeepAR to retrain the model whenever new data is available, ensuring the forecasts are up to date.

3. **Data Granularity**  
   Tracks and forecasts at the state/territory-disease level (including NYC as a separate entity), creating thousands of individual time series.

4. **Dashboard Visualizations**  
   - **Latest Week Summary**: Overview of newly flagged Potential Outbreaks and Ongoing Potential Outbreaks.  
   - **Outbreaks Profiles**: Analysis by pathogen type, affected bodily system, and transmission type, plus a detailed table of all flagged outbreaks.  
   - **Disease History**: Historical time series charts for specific diseases with forecast intervals and outbreak flags.  
   - **Outbreaks History**: Visualization of the number of Potential vs. Resolved Outbreaks and Ongoing Potential Outbreaks over time.  

---

## Repository Structure

At a high level, the code is organized into several main directories:

- **`dash_app/`**: Contains the [Plotly Dash](https://dash.plotly.com/) code for the web application, including layout definitions, callbacks, and assets (such as CSS or images).  

- **`sam_app/`**: Holds AWS SAM (Serverless Application Model) files, including Lambda functions and SageMaker training scripts. This directory manages the serverless infrastructure for data pulling and model retraining.  

- **`src/`**: Contains local testing and development scripts for data retrieval, preprocessing, modeling, and other utility functions.  

- **`data/`**: Used to store or cache any local datasets or processed artifacts needed for the application (if applicable).  

Other notable items include:
- **`Dockerfile`** and related Docker assets for containerizing the entire application.  
- **`requirements.txt`** (and other dependency files) for Python package dependencies.  
- **`README.md`** (this document) describing the project structure and purpose.

---

## DeepAR Model and Outbreak Detection

This project leverages the [Amazon SageMaker DeepAR algorithm](https://docs.aws.amazon.com/sagemaker/latest/dg/deepar.html) for forecasting weekly disease counts. Key points:

1. **Global Model**: DeepAR learns from many related time series (diseases across multiple states/territories) rather than training a separate model for each.  
2. **Probabilistic Forecasting**: DeepAR produces a distribution of future values rather than a single point estimate.  
3. **Negative Binomial Distribution**: Chosen to handle overdispersed count data, which is common in epidemiological case counts.  
4. **Outbreak Threshold**: A “Potential Outbreak” is flagged if the actual observed cases for a given disease and location exceed the model’s upper quantile threshold (e.g., 95th or 99th percentile).

---

## CDC NNDSS Data Source

All disease case data is retrieved from the [CDC NNDSS (National Notifiable Disease Surveillance System)](https://wwwn.cdc.gov/nndss/) via their public API.  
- **Weekly Updates**: Data is typically released 1–2 weeks after each reporting week.  
- **7,000+ Time Series**: Each state/territory-disease combination is modeled separately in the DeepAR framework.  

---

## License and Credits

- **Developed by**: JS Data Science Services LLC.  
- **Data Source**: CDC NNDSS (publicly available data).  
- **DeepAR**: Amazon SageMaker implementation.  

*(Include a license section here if your project is open source, e.g., MIT License, Apache License 2.0, etc.)*

---

**Disclaimer**  
This project provides an automated approach to **identify “Potential Outbreaks”** based on statistical thresholds. It does **not** diagnose or confirm actual outbreaks. For any real-world public health decisions, please consult official public health authorities and epidemiologists.

---
