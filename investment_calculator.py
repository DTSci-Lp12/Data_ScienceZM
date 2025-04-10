import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import io
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, inch

# Calculation functions
def calculate_treasury_bill(investment, term, yield_rate):
    price = (1 / (1 + ((term / 365) * yield_rate))) * 100
    cost_value = investment * (price / 100)
    handling_fee = 0.01
    cost_value_post_fee = cost_value * (1 - handling_fee)
    interest = investment - cost_value_post_fee
    return price, cost_value_post_fee, interest

def calculate_bond(investment, term, coupon_rate, interest_rate, purchase_date):
    bond_price = investment
    handling_fee = 0.01
    bond_cost_post_fee = bond_price * (1 - handling_fee)
    bond_coupon = investment * (coupon_rate / 100) * (182 / 365)
    bond_coupon_after_tax = bond_coupon * (1 - 0.15)
    coupon_dates, payments = [], []
    for i in range(1, term * 2 + 1):
        coupon_date = purchase_date + timedelta(days=182 * i)
        payment = round(bond_coupon_after_tax if i != term * 2 else investment, 2)
        coupon_dates.append(coupon_date.strftime('%Y-%m-%d'))
        payments.append(payment)
    return bond_price, bond_cost_post_fee, bond_coupon_after_tax, coupon_dates, payments

# Export functions
def export_to_excel(investment_data, coupon_dates, payments):
    if "Term (Years)" in investment_data:  # Check if it's bond data
        bond_df = pd.DataFrame([{
            "Investment Amount (K)": investment_data["Investment Amount (K)"],
            "Term (Years)": investment_data["Term (Years)"],
            "Coupon Rate (%)": investment_data["Coupon Rate (%)"],
            "Interest Rate (%)": investment_data["Interest Rate (%)"],
            "Bond Price per Unit (K)": investment_data["Bond Price per Unit (K)"],
            "Total Cost (Post Fee) (K)": investment_data["Total Cost (Post Fee) (K)"],
            "Coupon (After Tax) (K)": investment_data["Coupon (After Tax) (K)"],
            "Total Return on Bond (K)": investment_data["Total Return on Bond (K)"]
        }])
    else:  # Handle Treasury Bill data
        bond_df = pd.DataFrame([{
            "Investment Amount (K)": investment_data["Investment Amount (K)"],
            "Term (Days)": investment_data["Term (Days)"],
            "Target Yield (%)": investment_data["Target Yield (%)"],
            "Price per Unit (K)": investment_data["Price per Unit (K)"],
            "Total Cost (Post Fee) (K)": investment_data["Total Cost (Post Fee) (K)"],
            "Interest (K)": investment_data["Interest (K)"]
        }])

    coupon_schedule_df = pd.DataFrame({
        'Coupon Date': coupon_dates,
        'Coupon Payment (K)': payments
    })

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        bond_df.to_excel(writer, index=False, sheet_name='Investment Details')
        coupon_schedule_df.to_excel(writer, index=False, sheet_name='Coupon Schedule')
    output.seek(0)
    return output


def export_to_pdf(bond_data, coupon_dates, payments, user_details):
    output = io.BytesIO()
    doc = SimpleDocTemplate(output, pagesize=letter)
    styles = getSampleStyleSheet()
    content = [Paragraph("<b>Investment Calculation Summary:</b>", styles['Title'])]
    content.append(Paragraph("<b>User Details:</b>", styles['Heading2']))
    for key, value in user_details.items():
        content.append(Paragraph(f"<b>{key}:</b> {value}", styles['Normal']))
    content.append(Paragraph("<b>Investment Details:</b>", styles['Heading2']))
    for key, value in bond_data.items():
        content.append(Paragraph(f"<b>{key}:</b> {value}", styles['Normal']))

    content.append(Paragraph("<b>Coupon Schedule:</b>", styles['Heading2']))
    table_data = [["Coupon Date", "Coupon Payment (K)"]]  # Table header
    for coupon_date, payment in zip(coupon_dates, payments):
        table_data.append([coupon_date, f"{payment:.2f}"])

    table = Table(table_data, colWidths=[2.5 * inch, 2.5 * inch])
    table_style = TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-BoldOblique'),
    ])
    table.setStyle(table_style)
    content.append(table)
    content.append(Paragraph("<b>Copyright:</b>", styles['Heading2']))
    content.append(Paragraph(f"<b>I, Limbani Phiri, assert my intellectual property rights under Zambia's Copyright and Neighbouring Rights Act, No. 9 of 2016. These rights include exclusive control over my works and moral rights.</b> ", styles['Normal']))

    doc.build(content)
    output.seek(0)
    return output

# Main app logic
def main():
    # Add a red, white, and black theme
    st.markdown(
        """
        <style>
        .main {
            background-color: #E6E6E6; 
            color: black;
            padding: 5% 10%;
            border-radius: 10px;
        }
        .header {
            color: #D61B29;
            font-size: 30px;
            font-weight: bold;
            text-align: center;
        }
        .sidebar {
            background-color: #D61B29;
            color: white;
        }
        .button {
            background-color: #D61B29;
            color: white;
            font-weight: bold;
            border-radius: 8px;
        }
        </style>
        """, unsafe_allow_html=True)

    st.title("Welcome to the Investment Calculator")

    # Add a sidebar with options
    with st.sidebar:
        st.image("Bonds_1.jpg", width=250)
        st.header("Investestment Selection")
        st.write("_____________________________")
         # User selection for investment type
        investment_type = st.radio("Select Investment Type", ("Treasury Bill", "Bond"))
        st.write("_____________________________")
        
        if investment_type:
            st.header("Investor Details")
            st.write("_____________________________")
            user_details = {
            "Investor Name": st.text_input("Investor Name"),
            "Profession": st.text_input("Profession"),
            "Address": st.text_input("Address"),
            "CSD Account Number": st.text_input("CSD Account Number"),
            "Commercial Bank Name": st.text_input("Commercial Bank Name"),
            "Commercial Bank Account Number": st.text_input("Commercial Bank Account Number"),
            "Employer": st.text_input("Employer")
            
        }
            st.write("_____________________________")

    # Add greeting and description
    st.markdown("""
    <div class="header">Good Day, Welcome to the Investment Calculator!</div>
    <p style="font-size: 20px;">Here, you can calculate investment returns for both Treasury Bills and Bonds. 
    Please select an investment type from the  and proceed.</p>
    """, unsafe_allow_html=True)
    # Handle Treasury Bill logic
    if investment_type == "Treasury Bill":
        st.header("Treasury Bill Investment")
        investment = st.number_input("Investment Amount (K)", min_value=5000, step=5000)
        term = st.number_input("Term (Days)", min_value=1)
        yield_rate = st.number_input("Target Yield (%)", min_value=0.0)

        if st.button("Calculate Treasury Bill"):
            if investment % 5000 != 0:
                st.error("Investment must be in multiples of 5000.")
            elif investment <= 0 or term <= 0 or yield_rate <= 0:
                st.error("Please enter valid inputs for all fields.")
            else:
                price, cost_value_post_fee, interest = calculate_treasury_bill(investment, term, yield_rate / 100)
                st.subheader("Treasury Bill Investment Results")
                st.write(f"Price per unit: K{round(price, 2)}")
                st.write(f"Total Cost (After Handling Fee): K{round(cost_value_post_fee, 2)}")
                st.write(f"Interest: K{round(interest, 2)}")

                treasury_data = {
                        "Investment Amount (K)": investment,
                        "Term (Days)": term,
                        "Target Yield (%)": yield_rate,
                        "Price per Unit (K)": round(price, 2),
                        "Total Cost (Post Fee) (K)": round(cost_value_post_fee, 2),
                        "Interest (K)": round(interest, 2)
                    }


                # Correct the call to export_to_excel by passing the dictionary directly
                excel_file = export_to_excel(treasury_data, [], [])
                pdf_file = export_to_pdf(treasury_data, [], [], user_details)

                # Export to Excel and PDF
                st.download_button("Download Excel", excel_file, "Treasury_Bill_Investment_Output.xlsx")
                st.download_button("Download PDF", pdf_file, "Treasury_Bill_Investment_Output.pdf")

    # Handle Bond logic
    elif investment_type == "Bond":
        st.header("Bond Investment")
        investment = st.number_input("Investment Amount (K)", min_value=5000, step=5000)
        term = st.number_input("Term (Years)", min_value=1)
        coupon_rate = st.number_input("Coupon Rate (%)", min_value=0.0)
        interest_rate = st.number_input("Interest Rate (%)", min_value=0.0)
        purchase_date = st.date_input("Purchase Date", min_value=datetime.today())

        if st.button("Calculate Bond"):
            if investment % 5000 != 0:
                st.error("Investment must be in multiples of 5000.")
            elif investment <= 0 or term <= 0 or coupon_rate <= 0 or interest_rate <= 0:
                st.error("Please enter valid inputs for all fields.")
            else:
                bond_price, bond_cost_post_fee, bond_coupon_after_tax, coupon_dates, payments = calculate_bond(
                    investment, term, coupon_rate, interest_rate / 100, purchase_date
                )
                st.subheader("Bond Investment Results")
                st.write(f"Bond Price per unit: K{round(bond_price, 2)}")
                st.write(f"Total Cost (After Fee): K{round(bond_cost_post_fee, 2)}")
                st.write(f"Semi-annual Coupon (After Tax): K{round(bond_coupon_after_tax, 2)}")
                st.write(f"Total Return on Bond: K{round(investment + (bond_coupon_after_tax * term * 2), 2)}")

                bond_data = {
                    "Investment Amount (K)": investment,
                    "Term (Years)": term,
                    "Coupon Rate (%)": coupon_rate,
                    "Interest Rate (%)": interest_rate,
                    "Bond Price per Unit (K)": round(bond_price, 2),
                    "Total Cost (Post Fee) (K)": round(bond_cost_post_fee, 2),
                    "Coupon (After Tax) (K)": round(bond_coupon_after_tax, 2),
                    "Total Return on Bond (K)": round(investment + (bond_coupon_after_tax * term * 2), 2),
                    "Coupon Dates": coupon_dates,
                    "Coupon Payments": payments
                }

                # Correct the call to export_to_excel by passing the dictionary directly
                excel_file = export_to_excel(bond_data, coupon_dates, payments)
                pdf_file = export_to_pdf(bond_data, coupon_dates, payments, user_details)

                # Export to Excel and PDF
                st.download_button("Download Excel", excel_file, "Bond_Investment_Output.xlsx")
                st.download_button("Download PDF", pdf_file, "Bond_Investment_Output.pdf")

if __name__ == "__main__":
    main()
