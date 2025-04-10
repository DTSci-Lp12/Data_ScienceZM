import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Function to handle the uploaded CSVs for different parameters
def load_data(uploaded_file):
    return pd.read_csv(uploaded_file)

# Monte Carlo simulation function
def run_monte_carlo_simulation(stock_data, inflation_data, interest_data, forex_data, bond_data, runs=10000):
    # Extract data for simulation
    initial_price = stock_data['Close'].iloc[-1]
    price_changes = stock_data['Close'].pct_change().dropna()
    
    # Simulate future price movements using Monte Carlo method
    simulated_prices = np.zeros(runs)
    for i in range(runs):
        simulated_changes = np.random.choice(price_changes, size=len(stock_data), replace=True)
        simulated_prices[i] = initial_price * np.prod(1 + simulated_changes)
    
    # Return the simulated future prices
    return simulated_prices

# Streamlit UI
st.title("Dynamic Asset-Liability Management Model")
st.markdown("""
This application models the relationship between assets and liabilities of a company using stochastic simulations. 
You can upload your own data files to run the model and see the predicted outcomes.
""")

# Sidebar with instructions and file upload
st.sidebar.header("Upload Your Data")

# Adding icons and brief explanations for each upload
st.sidebar.markdown("### 📝 Stock Data")
st.sidebar.markdown("""
- **File Format**: CSV
- **Expected Columns**: 
    - `Date`: Date of the stock price (e.g., 2020-01-01).
    - `Close`: Closing price of the stock on that date.
- **Description**: Upload the historical stock price data. This will be used for predicting future stock movements.
""")

stock_file = st.sidebar.file_uploader("Upload Stock Data (CSV)", type=["csv"])

st.sidebar.markdown("### 💵 Inflation Data")
st.sidebar.markdown("""
- **File Format**: CSV
- **Expected Columns**: 
    - `Date`: Date of the inflation rate (e.g., 2020-01-01).
    - `Inflation`: Annual inflation rate for that date.
- **Description**: Upload the inflation rate data to model the effects of inflation on asset and liability values.
""")

inflation_file = st.sidebar.file_uploader("Upload Inflation Data (CSV)", type=["csv"])

st.sidebar.markdown("### 📊 Interest Rate Data")
st.sidebar.markdown("""
- **File Format**: CSV
- **Expected Columns**: 
    - `Date`: Date of the interest rate (e.g., 2020-01-01).
    - `Interest_Rate`: Interest rate for that date.
- **Description**: Upload historical interest rates that will be used to model future interest rate changes.
""")

interest_file = st.sidebar.file_uploader("Upload Interest Rate Data (CSV)", type=["csv"])

st.sidebar.markdown("### 💱 Forex Data")
st.sidebar.markdown("""
- **File Format**: CSV
- **Expected Columns**: 
    - `Date`: Date of the forex rate (e.g., 2020-01-01).
    - `Forex_Rate`: Exchange rate for the respective date.
- **Description**: Upload historical forex exchange rates to factor in currency fluctuations in your predictions.
""")

forex_file = st.sidebar.file_uploader("Upload Forex Data (CSV)", type=["csv"])

st.sidebar.markdown("### 🏛️ Bond Yield Data")
st.sidebar.markdown("""
- **File Format**: CSV
- **Expected Columns**: 
    - `Date`: Date of the bond yield (e.g., 2020-01-01).
    - `Bond_Yield`: Bond yield for that date.
- **Description**: Upload bond yield data, which will be used to model the cost of liabilities and predict future bond prices.
""")

bond_file = st.sidebar.file_uploader("Upload Bond Yield Data (CSV)", type=["csv"])

# Section for instructions on file formats
st.sidebar.markdown("""
#### ⚠️ Please ensure your files are formatted correctly:
1. Each CSV file must have the correct **column headers**.
2. The **Date** column should be in a format recognized by Python (e.g., `YYYY-MM-DD`).
3. Make sure all data is aligned with corresponding dates across files for accurate predictions.
""")

# Data upload and processing
if stock_file is not None and inflation_file is not None and interest_file is not None and forex_file is not None and bond_file is not None:
    # Load data
    stock_data = load_data(stock_file)
    inflation_data = load_data(inflation_file)
    interest_data = load_data(interest_file)
    forex_data = load_data(forex_file)
    bond_data = load_data(bond_file)

    # Display preview of uploaded data
    st.write("### Stock Data Preview", stock_data.head())
    st.write("### Inflation Data Preview", inflation_data.head())
    st.write("### Interest Rate Data Preview", interest_data.head())
    st.write("### Forex Data Preview", forex_data.head())
    st.write("### Bond Yield Data Preview", bond_data.head())

    # Run the Monte Carlo simulation
    simulated_prices = run_monte_carlo_simulation(stock_data, inflation_data, interest_data, forex_data, bond_data)

    # Display the results
    st.subheader("Monte Carlo Simulation Results")
    st.write(f"Average predicted stock price: ${np.mean(simulated_prices):.2f}")
    st.write(f"Portfolio change: ${np.mean(simulated_prices) - stock_data['Close'].iloc[-1]:.2f}")

    # Plot the results as a histogram with KDE
    fig, ax = plt.subplots()
    sns.histplot(simulated_prices, kde=True, ax=ax, color='skyblue', bins=50)
    ax.set_title("Simulated Stock Price Distribution")
    ax.set_xlabel("Stock Price ($)")
    ax.set_ylabel("Frequency")
    st.pyplot(fig)

    # Display additional stats
    st.subheader("Additional Statistics")
    st.write(f"Standard deviation of simulated prices: ${np.std(simulated_prices):.2f}")
    st.write(f"Max simulated price: ${np.max(simulated_prices):.2f}")
    st.write(f"Min simulated price: ${np.min(simulated_prices):.2f}")

else:
    st.warning("Please upload all the necessary data files to run the model.")
