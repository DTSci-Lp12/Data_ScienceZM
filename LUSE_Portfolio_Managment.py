import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import norm
import statsmodels.api as sm
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.graphics.tsaplots import plot_pacf
from statsmodels.tsa.stattools import adfuller
from datetime import datetime

# Page configuration
st.set_page_config(page_title="LUSE Portfolio Management", page_icon="📈", layout="wide")

# Title and Metadata
st.title("LUSE Portfolio Management")
st.markdown("### Author: Mr. Limbani Phiri")
st.markdown("### Date: 11/04/2023")

# Add an icon and introductory description
st.markdown("""
Welcome to the **LUSE Portfolio Management** application. 
This app allows you to upload data from the Lusaka Stock Exchange (LUSE) to perform stock price analysis, including:

- Time series forecasting of stock prices using ARIMA.
- Simulated future movements based on historical data.
- Portfolio value predictions based on closing stock prices.

### Instructions:
1. **Upload a CSV file with your LUSE Stock Data.**
2. The file should have the following structure:
    - **COMPANY**: A column with company names (for example: "Zanaco", "MTN Zambia").
    - **Date columns**: Columns representing the closing stock prices for each company for each date.

📂 **Please upload your file below**.

#### Example CSV format:
COMPANY,2021-10-01,2021-10-02,2021-10-03,... Zanaco,25.50,25.75,26.00,... MTN Zambia,15.20,15.50,15.80,... ...

Note: Ensure the data has at least one company's prices with dates listed as column headers.
""")

# File uploader with improved UI
uploaded_file = st.file_uploader("Upload your LUSE Stock Data CSV file", type=["csv"])

if uploaded_file is not None:
    # Load and preprocess data
    LUSE_Stock_Data = pd.read_csv(uploaded_file)
    LUSE_Stock_Data = LUSE_Stock_Data.fillna(0)  # Replace missing values with 0

    # Show the first few rows of the data
    st.write("Here is a preview of your data:")
    st.write(LUSE_Stock_Data.head())

    # Process the data
    temp = LUSE_Stock_Data.drop(columns=['COMPANY']).transpose()  # Transpose data for further analysis

    # Model Data
    runs = 10000
    name = LUSE_Stock_Data['COMPANY'].values
    ModelData_Margins = np.diff(temp.values, axis=0)  # Marginal data (price differences)
    ModelData_Margins[ModelData_Margins == 0] = np.nan  # Replace zeros with NaN (for proper plotting)

    # Select a company (change index as needed)
    i = 2  # Index for the company (adjust based on the data)
    st.markdown(f"### Analysis for {name[i]}")

    # Plotting Closing Stock Prices
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(temp.iloc[:, i], label="Closing Stock Price", color='blue', linewidth=2)
    ax.set_xlabel('Days', fontsize=12)
    ax.set_ylabel('Closing Stock Price', fontsize=12)
    ax.set_title(f"Time Series of {name[i]} Closing Stock Prices", fontsize=14)
    st.pyplot(fig)

    # Plot the histogram for data margins
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.hist(ModelData_Margins[:, i], bins=30, color='blue', edgecolor='black', alpha=0.7)
    ax.set_xlabel("Data Margins", fontsize=12)
    ax.set_ylabel("Frequency", fontsize=12)
    ax.set_title(f"{name[i]} Data Margins", fontsize=14)
    st.pyplot(fig)

    # Display t-test result
    from scipy import stats
    t_stat, p_value = stats.ttest_1samp(temp.iloc[:, i], 23)
    st.markdown(f"### T-test result for {name[i]}:")
    st.write(f"t-statistic = {t_stat:.3f}, p-value = {p_value:.3f}")

    # Fit ARIMA model and plot forecast
    st.markdown(f"### Fitting ARIMA model for {name[i]}...")
    model = ARIMA(temp.iloc[:, i], order=(5, 1, 0))  # Example ARIMA model, adjust parameters as needed
    fit = model.fit()
    forecast = fit.forecast(steps=300)

    # Plot ARIMA forecast
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(forecast, label="Forecasted Stock Prices", color='green', linewidth=2)
    ax.set_xlabel('Days', fontsize=12)
    ax.set_ylabel('Forecasted Stock Price', fontsize=12)
    ax.set_title(f"ARIMA Forecast for {name[i]}", fontsize=14)
    st.pyplot(fig)

    # Simulate future stock price movements and portfolio predictions
    initial_portfolio = 1000
    initial_price = temp.iloc[-1, i]
    initial_portfolio_value = initial_portfolio * initial_price

    # Simulate random walks for future closing stock prices
    mean_margin = np.mean(ModelData_Margins[:, i])
    std_margin = np.std(ModelData_Margins[:, i])

    closing_stock_price = []
    for _ in range(runs):
        simulated_prices = initial_price + np.random.lognormal(mean_margin, std_margin, size=300)
        closing_stock_price.append(simulated_prices[-1])

    # Plot the density of simulated closing stock prices
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.kdeplot(closing_stock_price, shade=True, color='gold', linewidth=2)
    ax.set_xlabel("Closing Stock Price", fontsize=12)
    ax.set_title(f"Density of Predicted Closing Stock Prices for {name[i]}", fontsize=14)
    st.pyplot(fig)

    # Calculate and display expected portfolio value
    expected_closing_price = np.mean(closing_stock_price)
    final_portfolio_value = expected_closing_price * initial_portfolio
    portfolio_change = final_portfolio_value - initial_portfolio_value

    st.markdown(f"### Portfolio Prediction Results:")
    st.write(f"**Expected average final portfolio value for {name[i]}**: K{final_portfolio_value:.2f}")
    st.write(f"**The change in portfolio value is**: K{portfolio_change:.2f}")

    # Show the number of trading days
    start_date = datetime(2021, 10, 1)
    end_date = datetime(2022, 12, 30)
    days_diff = (end_date - start_date).days
    st.write(f"**Trading days**: {days_diff}")

else:
    st.warning("Please upload a CSV file containing LUSE Stock Data. The file should include a `COMPANY` column and stock price data.")
    st.markdown("""
    #### File Format:
    - **COMPANY** column (company names)
    - Date columns (closing stock prices for each date)
    
    **Example CSV Format:**
    ```
    COMPANY,2021-10-01,2021-10-02,2021-10-03,...
    Zanaco,25.50,25.75,26.00,...
    MTN Zambia,15.20,15.50,15.80,...
    ...
    ```

    - Ensure that each column after **COMPANY** contains the closing stock prices for each company.
    - If there are missing values in your data, they will be automatically replaced with `0`.
    """)
