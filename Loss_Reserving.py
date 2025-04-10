import streamlit as st
import pandas as pd
import numpy as np

# Function to compute Chain Ladder Method
def chain_ladder_method(data):
    LDF = []
    n_rows, n_cols = data.shape
    for i in range(1, n_cols):
        LDF.append(np.sum(data.iloc[:-1, i+1]) / np.sum(data.iloc[:-1, i]))
    
    # Apply the development factors (LDF) to the data
    for j in range(1, n_cols):
        for i in range(n_rows):
            if data.iloc[i, j] == 0:
                data.iloc[i, j] = data.iloc[i, j-1] * LDF[j-1]
    
    # Calculate ultimate loss
    ultimate_loss = data.iloc[:, -1].sum()
    
    # Calculate paid loss
    paid_loss = data.iloc[:, 1:].sum().sum() - data.iloc[:, -1].sum()
    
    reserves = ultimate_loss - paid_loss
    return LDF, data, ultimate_loss, paid_loss, reserves

# Function to compute Bornhuetter-Ferguson Method
def bornhuetter_ferguson_method(data):
    LDF = []
    n_rows, n_cols = data.shape
    for i in range(1, n_cols):
        LDF.append(np.sum(data.iloc[:-1, i+1]) / np.sum(data.iloc[:-1, i]))
    
    CDF = [1]
    for i in range(1, len(LDF)):
        CDF.append(CDF[i-1] * LDF[i-1])
    
    Formula_Calculated = [1 - 1/c for c in CDF]
    
    # Simulate premiums
    premiums = np.random.uniform(0, 1, n_rows) * np.max(data.sum(axis=1)) * 4
    
    # Assume a constant loss ratio annually
    loss_ratio = data.iloc[0, -1] / premiums[0]
    
    # Initial ultimate loss
    initial_ultimate_loss = loss_ratio * premiums
    initial_ultimate_loss[0] = data.iloc[0, -1]
    
    # Emerging liabilities
    emerging_liabilities = initial_ultimate_loss * Formula_Calculated
    
    # Reserve requirement excluding IBNR
    reserve_requirement = emerging_liabilities.sum()
    
    return LDF, CDF, Formula_Calculated, premiums, loss_ratio, initial_ultimate_loss, emerging_liabilities, reserve_requirement

# Streamlit app UI
def app():
    st.title("Loss Reserving Methods")
    st.subheader("Actuarial Take on Loss Reserving")

    # App description
    st.write("""
    Loss reserving helps insurers ensure adequate capital for covering unpaid claim obligations. 
    This app allows you to perform loss reserving using two key actuarial methods: 
    the **Chain Ladder Method** and the **Bornhuetter-Ferguson Method**.
    """)

    # Upload data
    uploaded_file = st.file_uploader("Upload Claims Data (CSV)", type="csv", help="Upload a CSV file with claim data. Ensure it contains multiple columns with historical claim data.")

    if uploaded_file is not None:
        # Load the data
        data = pd.read_csv(uploaded_file)
        st.write("Data Preview:")
        st.write(data.head())

        # Instructions on how the data file should look
        st.markdown("""
        **File Format Instructions:**
        - The CSV should contain columns representing **Claim Development** over time, with each column being a year or a quarter of the claim development process.
        - The rows represent different accident years (or groups of claims).
        - Ensure that the data has no missing or zero values for the development factors (unless naturally zero due to the structure of the claims).

        Example:

        | Accident Year | Development Year 1 | Development Year 2 | Development Year 3 |
        |---------------|---------------------|---------------------|---------------------|
        | 2017          | 100                 | 150                 | 200                 |
        | 2018          | 120                 | 180                 | 250                 |
        """)
        
        # Chain Ladder Method
        if st.button("Calculate Chain Ladder Method"):
            LDF, updated_data, ultimate_loss, paid_loss, reserves = chain_ladder_method(data)
            st.subheader("Chain Ladder Method Results")
            st.write("Development Factors (LDF):", LDF)
            st.write("Updated Data after applying LDF:", updated_data)
            st.write(f"Ultimate Loss: {ultimate_loss}")
            st.write(f"Paid Loss: {paid_loss}")
            st.write(f"Reserves (excluding IBNR): {reserves}")

        # Bornhuetter-Ferguson Method
        if st.button("Calculate Bornhuetter-Ferguson Method"):
            LDF, CDF, Formula_Calculated, premiums, loss_ratio, initial_ultimate_loss, emerging_liabilities, reserve_requirement = bornhuetter_ferguson_method(data)
            st.subheader("Bornhuetter-Ferguson Method Results")
            st.write("Development Factors (LDF):", LDF)
            st.write("Cumulative Development Factors (CDF):", CDF)
            st.write("Formula Calculated (1 - 1/f):", Formula_Calculated)
            st.write("Simulated Premiums:", premiums)
            st.write(f"Loss Ratio: {loss_ratio}")
            st.write("Initial Ultimate Losses:", initial_ultimate_loss)
            st.write("Emerging Liabilities:", emerging_liabilities)
            st.write(f"Reserve Requirement (excluding IBNR): {reserve_requirement}")
        
        # Allow download of results
        download_data = {
            "LDF": LDF,
            "Updated Data": updated_data,
            "Ultimate Loss": [ultimate_loss],
            "Paid Loss": [paid_loss],
            "Reserves": [reserves]
        }

        download_df = pd.DataFrame(download_data)
        st.download_button(
            label="Download Results as Excel",
            data=download_df.to_excel(index=False),
            file_name="loss_reserving_results.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
# Run the app
if __name__ == "__main__":
    app()
