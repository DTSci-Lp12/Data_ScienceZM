import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO
import xlsxwriter

# Function to compute Chain Ladder Method
def chain_ladder_method(data):
    LDF = []
    n_rows, n_cols = data.shape
    
    for i in range(1, n_cols - 1):  # Change range to n_cols - 1
        LDF.append(np.sum(data.iloc[:-1, i+1]) / np.sum(data.iloc[:-1, i]))
    
    for j in range(1, n_cols - 1):  # Update this loop as well
        for i in range(n_rows):
            if data.iloc[i, j] == 0:
                data.iloc[i, j] = data.iloc[i, j-1] * LDF[j-1]
    
    ultimate_loss = data.iloc[:, -1].sum()
    paid_loss = data.iloc[:, 1:].sum().sum() - data.iloc[:, -1].sum()
    reserves = ultimate_loss - paid_loss
    return LDF, data, ultimate_loss, paid_loss, reserves

def bornhuetter_ferguson_method(data):
    LDF = []
    n_rows, n_cols = data.shape
    
    # Loop through the columns (except the last one)
    for i in range(1, n_cols - 1):  # Ensure the loop stops at second-to-last column
        if i + 1 < n_cols:
            LDF.append(np.sum(data.iloc[:-1, i+1]) / np.sum(data.iloc[:-1, i]))

    # Calculate the Cumulative Development Factors (CDF)
    CDF = [1]
    for i in range(1, len(LDF)):
        CDF.append(CDF[i-1] * LDF[i-1])
    
    # Calculate the Formula (1 - 1/f) for the Bornhuetter-Ferguson method
    Formula_Calculated = [1 - 1/c for c in CDF]
    
    # Simulate premiums (you may need to adjust this for your specific needs)
    premiums = np.random.uniform(0, 1, n_rows) * np.max(data.sum(axis=1)) * 4
    
    # Assume a constant loss ratio annually
    loss_ratio = data.iloc[0, -1] / premiums[0]
    
    # Calculate initial ultimate loss using the loss ratio and premiums
    initial_ultimate_loss = loss_ratio * premiums
    
    # Ensure initial_ultimate_loss and Formula_Calculated have the same length
    if len(initial_ultimate_loss) > len(Formula_Calculated):
        # If initial_ultimate_loss is longer, truncate it to match Formula_Calculated
        initial_ultimate_loss = initial_ultimate_loss[:len(Formula_Calculated)]
    elif len(initial_ultimate_loss) < len(Formula_Calculated):
        # If Formula_Calculated is longer, truncate it to match initial_ultimate_loss
        Formula_Calculated = Formula_Calculated[:len(initial_ultimate_loss)]
    
    # Calculate emerging liabilities
    emerging_liabilities = initial_ultimate_loss * Formula_Calculated
    
    # Reserve requirement excluding IBNR (Incurred But Not Reported)
    reserve_requirement = emerging_liabilities.sum()
    
    return LDF, CDF, Formula_Calculated, premiums, loss_ratio, initial_ultimate_loss, emerging_liabilities, reserve_requirement


# Function to create a CSV template
def create_template():
    # Example template data
    template_data = {
        "Accident Year": [2017, 2018, 2019],
        "Development Year 1": [100, 200, 300],
        "Development Year 2": [400, 500, 600],
        "Development Year 3": [700, 800, 900]
    }
    
    df = pd.DataFrame(template_data)
    
    # Save as CSV
    buffer = BytesIO()
    df.to_csv(buffer, index=False)
    buffer.seek(0)
    return buffer

# Streamlit app UI
def app():
    st.title("Yengo | Actuarial Loss Reserving Framework")
    st.subheader("Loss Reserving Through an Actuarial Lens : ")
    # Styling
    st.markdown("""
    <style>
    /* Label styling (input labels, checkbox labels, etc.) */
    label, .css-1offfwp, .stCheckbox, .stTextInput > label, .stSelectbox > label, .stDateInput > label {
        color: #FFFFFF !important;
        font-weight: 600;
        font-size: 15px;
    }

    /* Metric cards */
    div[data-testid="metric-container"] {
        background-color: #1e1e1e;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #FF4C4C;
    }

    div[data-testid="metric-container"] > div {
        color: #FFFFFF !important;
        font-size: 1.5em;
        font-weight: bold;
        text-align: center;
    }

    /* Inputs */
    .stTextInput input, .stDateInput input {
        background-color: #121212;
        color: white;
        border: 1px solid #FF4C4C;
        border-radius: 5px;
        padding: 6px;
    }

    /* File uploader label */
    .css-1cpxqw2 {
        color: #FFFFFF !important;
        font-weight: 600;
    }

    /* Divider lines */
    hr, .red-line {
        border: none;
        height: 2px;
        background-color: #FF4C4C;
        margin: 25px 0;
    }

    /* Section spacing */
    .stMarkdown h2 {
        margin-top: 2em;
    }

    body, .main, .stApp {
        background-color: black;
        color: white;
    }
    .stButton button {
    background-color: transparent !important;
    color: white !important;
    border: 1px solid white !important;
    padding: 10px 24px;
    font-size: 16px;
    border-radius: 5px;
    transition: 0.3s ease;
}
    .stButton button:hover {
        background-color: red !important;
        color: white !important;
        border: 1px solid red !important;
    }
    .insights, .header {
        background-color: #1e1e1e;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
        color: #FF4C4C;
        text-align: center;
        font-weight: bold;
        font-size: 28px;
        text-shadow: 1px 1px 2px #000;
    }
    .input-label {
        font-weight: bold;
        color: #f5f5f5;
    }
    .date-stamp {
        color: #CCCCCC;
        font-style: italic;
    }
    /* Bright White Color for Titles and Headers */
    .title, h1, h2, h3 , h4 {
        color: #FFFFFF !important;
        text-shadow: 2px 2px 5px #000000;
    }
    .title,h5 {
        color: #FF0000 !important;
        text-shadow: 2px 2px 5px #000000;
    }
    </style>
""", unsafe_allow_html=True)# Styling
    st.markdown("""
    <style>
    /* Label styling (input labels, checkbox labels, etc.) */
    label, .css-1offfwp, .stCheckbox, .stTextInput > label, .stSelectbox > label, .stDateInput > label {
        color: #FFFFFF !important;
        font-weight: 600;
        font-size: 15px;
    }

    /* Metric cards */
    div[data-testid="metric-container"] {
        background-color: #1e1e1e;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #FF4C4C;
    }

    div[data-testid="metric-container"] > div {
        color: #FFFFFF !important;
        font-size: 1.5em;
        font-weight: bold;
        text-align: center;
    }

    /* Inputs */
    .stTextInput input, .stDateInput input {
        background-color: #121212;
        color: white;
        border: 1px solid #FF4C4C;
        border-radius: 5px;
        padding: 6px;
    }

    /* File uploader label */
    .css-1cpxqw2 {
        color: #FFFFFF !important;
        font-weight: 600;
    }

    /* Divider lines */
    hr, .red-line {
        border: none;
        height: 2px;
        background-color: #FF4C4C;
        margin: 25px 0;
    }

    /* Section spacing */
    .stMarkdown h2 {
        margin-top: 2em;
    }

    body, .main, .stApp {
        background-color: black;
        color: white;
    }
    .stButton button {
    background-color: transparent !important;
    color: white !important;
    border: 1px solid white !important;
    padding: 10px 24px;
    font-size: 16px;
    border-radius: 5px;
    transition: 0.3s ease;
}
    .stButton button:hover {
        background-color: red !important;
        color: white !important;
        border: 1px solid red !important;
    }
    .insights, .header {
        background-color: #1e1e1e;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
        color: #FF4C4C;
        text-align: center;
        font-weight: bold;
        font-size: 28px;
        text-shadow: 1px 1px 2px #000;
    }
    .input-label {
        font-weight: bold;
        color: #f5f5f5;
    }
    .date-stamp {
        color: #CCCCCC;
        font-style: italic;
    }
    /* Bright White Color for Titles and Headers */
    .title, h1, h2, h3 , h4 {
        color: #FFFFFF !important;
        text-shadow: 2px 2px 5px #000000;
    }
    .title,h5 {
        color: #FF0000 !important;
        text-shadow: 2px 2px 5px #000000;
    }
    </style>
""", unsafe_allow_html=True)

    st.write("""
    At Yengo, loss reserving is a critical component of ensuring that insurers maintain sufficient capital to meet outstanding claim obligations. Our platform empowers users to perform loss reserving using two trusted actuarial methodologies: the Chain Ladder Method and the Bornhuetter-Ferguson Method, enabling accurate and compliant reserve estimation with confidence.
    """)

    # Template download option
    st.markdown("""
    #### Download the template CSV file for claim development data:
    This file can be used to upload your claims data for processing.
    """)
    
    template_button = st.download_button(
        label="Download Template CSV",
        data=create_template(),
        file_name="loss_reserving_template.csv",
        mime="text/csv"
    )

    # Upload data
    uploaded_file = st.file_uploader("Upload Claims Data (CSV)", type="csv", help="Upload a CSV file with claim data.")
    st.markdown("<hr class='red-line'>", unsafe_allow_html=True)
    st.markdown("""
        <div style='padding: 10px; background-color: transparent !important; border-left: 5px solid #4A90E2; border-radius: 5px;'>
            <h4 style='margin: 0; color: white;'>🧮 Calculation Results : The results and outputs for the selected method will be displayed below.</h4>
        </div>
        """, unsafe_allow_html=True)


    if uploaded_file is not None:
        # Load the data
        data = pd.read_csv(uploaded_file)
        st.write("Data Preview:")
        st.write(data.head())

        # Ask user for method selection
        method_choice = st.selectbox("Select Method for Loss Reserving", 
                                     ["Select Method", "Chain Ladder Method", "Bornhuetter-Ferguson Method"])

        if method_choice == "Chain Ladder Method":
            if st.button("Calculate Chain Ladder Method"):
                LDF, updated_data, ultimate_loss, paid_loss, reserves = chain_ladder_method(data)
                st.subheader("🔗 Chain Ladder Method Results")

                st.markdown(f"""
                - **Development Factors (LDF):** `{[round(ldf, 3) for ldf in LDF]}`
                - **Ultimate Loss:** `{ultimate_loss:,.2f}`
                - **Paid Loss:** `{paid_loss:,.2f}`
                - **Required Reserves:** `{reserves:,.2f}`
                """)

                st.markdown("##### 📊 Updated Data After Applying LDF:")
                st.dataframe(updated_data.style.format("{:,.2f}"))


                # Ensure all columns have the same length for the download
                num_rows = len(data)

                download_data = {
                    "LDF": LDF + [np.nan] * (num_rows - len(LDF)),  # Pad with NaN if LDF is shorter
                    "Updated Data": updated_data.iloc[:, -1].tolist() + [np.nan] * (num_rows - len(updated_data)),
                    "Ultimate Loss": [ultimate_loss] * num_rows,  # Repeat ultimate_loss
                    "Paid Loss": [paid_loss] * num_rows,  # Repeat paid_loss
                    "Reserves": [reserves] * num_rows  # Repeat reserves
                }

                download_df = pd.DataFrame(download_data)

                # Write the download file to a buffer
                buffer = BytesIO()
                with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                    download_df.to_excel(writer, index=False)
                buffer.seek(0)

                st.download_button(
                    label="Download Loss Reserving Results as Excel",
                    data=buffer,
                    file_name="loss_reserving_results.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

        elif method_choice == "Bornhuetter-Ferguson Method":
            if st.button("Calculate Bornhuetter-Ferguson Method"):
                LDF, CDF, Formula_Calculated, premiums, loss_ratio, initial_ultimate_loss, emerging_liabilities, reserve_requirement = bornhuetter_ferguson_method(data)

                st.subheader("📘 Bornhuetter-Ferguson Method Results")
                st.markdown(f"""
                - **Development Factors (LDF):** `{[round(ldf, 3) for ldf in LDF]}`
                - **Cumulative Development Factors (CDF):** `{[round(cdf, 3) for cdf in CDF]}`
                - **1 - (1 / CDF):** `{[round(f, 3) for f in Formula_Calculated]}`
                - **Loss Ratio:** `{loss_ratio:.2%}`
                - **Reserve Requirement (excluding IBNR):** `{reserve_requirement:,.2f}`
                """)

                st.markdown("##### 💡 Simulated Premiums:")
                st.dataframe(pd.DataFrame({"Premiums": premiums}).style.format("{:,.2f}"))

                st.markdown("##### 📈 Initial Ultimate Losses:")
                st.dataframe(pd.DataFrame({"Ultimate Losses": initial_ultimate_loss}).style.format("{:,.2f}"))

                st.markdown("##### 📉 Emerging Liabilities:")
                st.dataframe(pd.DataFrame({"Emerging Liabilities": emerging_liabilities}).style.format("{:,.2f}"))


                # 🔧 FIX: Ensure all arrays are same length
                # Choose reference length (minimum length of key arrays)
                reference_len = min(
                    len(LDF),
                    len(emerging_liabilities),
                    len(initial_ultimate_loss),
                    len(premiums),
                )

                download_data = {
                    "LDF": LDF[:reference_len],
                    "Emerging Liabilities": emerging_liabilities[:reference_len],
                    "Initial Ultimate Loss": initial_ultimate_loss[:reference_len],
                    "Premiums": premiums[:reference_len],
                    "Loss Ratio": [loss_ratio] * reference_len,
                    "Reserve Requirement": [reserve_requirement] * reference_len
                }

                # ✅ Create DataFrame safely now
                download_df = pd.DataFrame(download_data)

                # 📥 Export to Excel
                with BytesIO() as buffer:
                    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                        download_df.to_excel(writer, index=False, sheet_name="Bornhuetter-Ferguson Results")
                    buffer.seek(0)
                    st.download_button(
                        label="Download Results as Excel",
                        data=buffer,
                        file_name="bornhuetter_ferguson_results.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
# Run the app
if __name__ == "__main__":
    app()
