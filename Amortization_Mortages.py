import streamlit as st
import pandas as pd
import io
from datetime import datetime

# Function to calculate the amortization schedule
def calculate_amortization(loan_amount, interest_rate, loan_term, monthly_payment):
    monthly_interest_rate = (interest_rate / 100) / 12
    pmt = (loan_amount * monthly_interest_rate * ((1 + monthly_interest_rate) ** loan_term)) / \
        ((1 + monthly_interest_rate) ** loan_term - 1)
    
    schedule = []
    for i in range(1, loan_term + 1):
        interest = loan_amount * monthly_interest_rate
        principal_payment = pmt - interest
        loan_amount -= principal_payment
        schedule.append([i, principal_payment, interest, pmt, loan_amount])
    
    # Convert to DataFrame for easier display
    df = pd.DataFrame(schedule, columns=["Payment No.", "Principal Payment", "Interest", "Payment", "Principal Remaining"])
    return df

# Function to convert DataFrame to Excel for downloading
def convert_df_to_excel(df):
    # Use BytesIO to save the Excel file to a binary stream
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:  # Using openpyxl as the engine
        df.to_excel(writer, index=False, sheet_name="Amortization Schedule")
    output.seek(0)  # Move to the start of the file before returning it
    return output

# Streamlit app
def app():
    # Custom CSS for styling
    st.markdown("""
        <style>
        body {
            background-color: white;
            font-family: 'Arial', sans-serif;
            color: black;
            padding: 20px;
        }
        .title {
            color: #D32F2F;
            font-size: 36px;
            font-weight: bold;
        }
        .header {
            background-color: white;
            padding: 10px;
            color: #D32F2F;
            border-radius: 10px;
            text-align: center;
            margin-bottom: 20px;
            border: 3px solid #D32F2F; /* Red border around header */
        }
        .button {
            background-color: #D32F2F;
            color: white;
            padding: 15px 32px;
            text-align: center;
            font-size: 18px;
            cursor: pointer;
            border-radius: 5px;
            border: none;
        }
        .button:hover {
            background-color: #b71c1c;
        }
        .insights {
            background-color: white;
            padding: 15px;
            border-radius: 10px;
            margin-top: 20px;
            color: black;
            border: 2px solid #D32F2F; /* Red border around insights */
        }
        .input-label {
            font-weight: bold;
            color: #D32F2F;
        }
        .container {
            border: 3px solid #D32F2F;
            border-radius: 10px;
            padding: 20px;
        }
        .date-stamp {
            color: #D32F2F;
            font-size: 14px;
            font-style: italic;
        }
        </style>
    """, unsafe_allow_html=True)

    # Title header with a professional look
    st.markdown('<div class="header"><h2>Amortization of ZNBS Mortgages</h2></div>', unsafe_allow_html=True)
    
    # Display current date
    current_date = datetime.now().strftime("%Y-%m-%d")
    st.markdown(f'<p class="date-stamp">Date: {current_date}</p>', unsafe_allow_html=True)
    
    # Input fields in a two-column layout with visible labels
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<p class="input-label">Loan Amount (K)</p>', unsafe_allow_html=True)
        loan_amount = st.number_input("", min_value=100000, value=5000000, step=10000, label_visibility="collapsed")
        
        st.markdown('<p class="input-label">Nominal Annual Interest Rate (%)</p>', unsafe_allow_html=True)
        interest_rate = st.number_input("", min_value=0.0, value=6.3, step=0.1, label_visibility="collapsed")
        
    with col2:
        st.markdown('<p class="input-label">Loan Term (Months)</p>', unsafe_allow_html=True)
        loan_term = st.number_input("", min_value=12, value=360, step=12, label_visibility="collapsed")
        
        st.markdown('<p class="input-label">Monthly Payment (K)</p>', unsafe_allow_html=True)
        monthly_payment = st.number_input("", min_value=0, value=87670, step=500, label_visibility="collapsed")
    
    # Icon button to generate amortization schedule
    if st.button("Generate Amortization Schedule", key="generate", help="Click to calculate the schedule"):
        schedule_df = calculate_amortization(loan_amount, interest_rate, loan_term, monthly_payment)
        
        # Display the amortization schedule
        st.subheader("Amortization Schedule")
        st.write(schedule_df)
        
        # Key Insights
        payment_number = schedule_df[schedule_df["Principal Payment"] > schedule_df["Interest"]].iloc[0]["Payment No."]
        years_to_principal_payment = round(payment_number / 12, 1)
        total_interest_paid = schedule_df["Interest"].sum()
        total_principal_paid = schedule_df["Principal Payment"].sum()
        
        st.markdown("<div class='insights'>", unsafe_allow_html=True)
        st.subheader("Key Insights:")
        st.write(f"📅 You will start paying more principal than interest on payment number: {payment_number}")
        st.write(f"💰 For the first {years_to_principal_payment} years, you'll be mostly servicing interest.")
        st.write(f"💸 Total interest paid over the term: K {total_interest_paid:,.2f}")
        st.write(f"🏡 Total principal paid over the term: K {total_principal_paid:,.2f}")
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Create the download button for the Excel file
        excel_file = convert_df_to_excel(schedule_df)
        download_button = st.download_button(
            label="📥 Download Amortization Schedule as Excel",
            data=excel_file,
            file_name="amortization_schedule.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
        
        # Trigger rerun after the download button is clicked
        if download_button:
            st.experimental_rerun()

if __name__ == "__main__":
    app()
