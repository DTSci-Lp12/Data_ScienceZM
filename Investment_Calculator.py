import streamlit as st
import pandas as pd
import numpy as np
import io
from datetime import datetime, timedelta
import random

# Visualization
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go

# PDF Generation
from fpdf import FPDF
from io import BytesIO

# ReportLab for advanced PDF styling
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as PlatypusImage
)
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER

# Image Processing
from PIL import Image, ImageDraw, ImageOps


# Calculation functions
def calculate_treasury_bill(investment, term, yield_rate):
    price = (1 / (1 + ((term / 365) * yield_rate))) * 100
    cost_value = investment * (price / 100)
    handling_fee = 0.01
    cost_value_post_fee = cost_value
    interest = investment - cost_value_post_fee
    return price, cost_value_post_fee, interest

def calculate_bond(investment, term, coupon_rate, yield_rate, purchase_date):
    bond_price = investment
    handling_fee = 0.01
    bond_cost_post_fee = bond_price
    bond_coupon = investment * (coupon_rate / 100) * (182 / 365)
    bond_coupon_after_tax = bond_coupon * (1 - (0.15+handling_fee))
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
            "Yield Rate (%)": investment_data["Yield Rate (%)"],
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

# --- Load and process your logo into `border_image` ---
logo_path = "Yengo_1.jpg"  # adjust path if needed
# 1. Open and convert to RGBA
image = Image.open(logo_path).convert("L").convert("RGBA")

# 2. Crop to square
min_side = min(image.size)
image = image.crop((
    (image.width - min_side) // 2,
    (image.height - min_side) // 2,
    (image.width + min_side) // 2,
    (image.height + min_side) // 2
))

# 3. Create circular mask
mask = Image.new('L', image.size, 0)
draw = ImageDraw.Draw(mask)
draw.ellipse((0, 0, image.size[0], image.size[1]), fill=255)
image.putalpha(mask)

# 4. Add white border
border_size = 8
border_image = Image.new(
    'RGBA',
    (image.size[0] + border_size*2, image.size[1] + border_size*2),
    (255, 255, 255, 0)
)
border_mask = Image.new('L', border_image.size, 0)
border_draw = ImageDraw.Draw(border_mask)
border_draw.ellipse(
    (0, 0, border_image.size[0], border_image.size[1]),
    fill=255
)
border_image.paste(image, (border_size, border_size), image)
border_image.putalpha(border_mask)
logo_image=border_image
def export_to_pdf(bond_data, coupon_dates, payments, user_details, logo_image):
    output = io.BytesIO()
    doc = SimpleDocTemplate(output, pagesize=letter)
    styles = getSampleStyleSheet()
    content = []

    # Convert and add logo
    logo_buffer = io.BytesIO()
    logo_image.save(logo_buffer, format="PNG")
    logo_buffer.seek(0)
    logo = PlatypusImage(logo_buffer, width=1.0 * inch, height=1.0 * inch)
    content.append(logo)
    content.append(Spacer(1, 12))

    # Title (avoid emojis)
    content.append(Paragraph("<b>Investment Report</b>", styles['Title']))
    content.append(Spacer(1, 12))
    
    # Short description of the report
    content.append(Paragraph(
        "This report provides a summary of investment calculations for fixed income securities, including both short-term instruments such as Treasury Bills and long-term options like Government Bonds.",
        styles['Normal']
    ))
    content.append(Spacer(1, 12))
    
    # Timestamp
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report_number = datetime.now().strftime("RPT-%Y%m%d%H%M%S")

    header_table = Table([[f"Generated on: {now}", f"Report No: {report_number}"]],
                         colWidths=[300, 200])

    header_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))

    content.append(header_table)
    content.append(Spacer(1, 12))

    # User details
    content.append(Paragraph("<b>User Details</b>", styles['Heading2']))
    user_table_data = [[Paragraph(f"<b>{key}</b>", styles['Normal']), Paragraph(str(value), styles['Normal'])] for key, value in user_details.items()]
    user_table = Table(user_table_data, colWidths=[2.5 * inch, 3.5 * inch])
    user_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 2, colors.red),
        ('BACKGROUND', (0, 0), (-1, -1), colors.whitesmoke),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
    ]))
    content.append(user_table)
    content.append(Spacer(1, 16))

    # Bond details
    content.append(Paragraph("<b>Investment Details</b>", styles['Heading2']))
    bond_table_data = [[Paragraph(f"<b>{key}</b>", styles['Normal']), Paragraph(str(value), styles['Normal'])] for key, value in bond_data.items()]
    bond_table = Table(bond_table_data, colWidths=[2.5 * inch, 3.5 * inch])
    bond_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('BACKGROUND', (0, 0), (-1, -1), colors.beige),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
    ]))
    content.append(bond_table)
    content.append(Spacer(1, 16))

    # Coupon Schedule
    content.append(Paragraph("<b>Coupon Schedule</b>", styles['Heading2']))
    table_data = [["Coupon Date", "Coupon Payment (K)"]] + [[cd, f"{p:.2f}"] for cd, p in zip(coupon_dates, payments)]
    table = Table(table_data, colWidths=[2.5 * inch, 3.5 * inch])
    table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
    ]))
    content.append(table)
    content.append(Spacer(1, 24))

    # Footer
    # Define a centered style for the disclaimer
    centered_bold_style = ParagraphStyle(
        name='CenteredBold',
        parent=styles['Normal'],
        alignment=TA_CENTER
    )

    # Add the centered, bold disclaimer
    content.append(Paragraph(
        "<b>Disclaimer:This report is for informational purposes only and does not constitute financial advice.</b> ",
        centered_bold_style
    ))

    content.append(Spacer(1, 12))

    # Add the left-aligned copyright
    content.append(Paragraph(
        f"<b> © {datetime.now().year} Yengo. All Rights Reserved.</b> ",
        styles['Normal']
    ))

    doc.build(content)
    output.seek(0)
    return output


# Main app logic in app() function
def app():
    # Add a red, white, and black theme
    st.markdown("""
        <style>
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
    /* Make number input fields white */
    .stNumberInput input {
        background-color: black !important;
        color: white !important;
        border: 1px solid #ccc !important;
        border-radius: 5px !important;
    }
    /* Make the labels white */
    label, .stNumberInput label {
        color: white !important;
        font-weight: 600;
    }
    /* Make number input fields white */
    .stTextInput input {
        background-color: black !important;
        color: white !important;
        border: 1px solid #ccc !important;
        border-radius: 5px !important;
    }
    /* Make the labels white */
    label, .stTextInput label {
        color: black !important;
        font-weight: 600;
    }
    </style>
    """, unsafe_allow_html=True)

    # Add a sidebar with options
    with st.sidebar:
        # Load image and apply grayscale
        image = Image.open("Bonds_1.jpg")
        image = ImageOps.grayscale(image)  # Make it black and white

        # Make it a square crop (if it's not already)
        min_dim = min(image.size)
        image = ImageOps.fit(image, (min_dim, min_dim), centering=(0.5, 0.5))

        # Make it circular
        mask = Image.new("L", (min_dim, min_dim), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.ellipse((0, 0, min_dim, min_dim), fill=255)
        image.putalpha(mask)

        # Convert to bytes for Streamlit
        buf = io.BytesIO()
        image.save(buf, format="PNG")
        buf.seek(0)

        # Display the circular image
        st.image(buf, width=250)

        st.header("Investment Selection")
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
    <div class="header">Yengo | Smart Financial Planner!</div>
    <p style="font-size: 20px;">Yengo’s Investment Calculator utilizes the latest guidelines from the Bank of Zambia, ensuring full compliance with current regulatory standards. It delivers real-time, data-driven projections, providing transparent and reliable figures suitable for professional analysis and review.
To begin, please enter your investor details in the fields provided on the sidebar.</p>
    """, unsafe_allow_html=True)
    st.markdown("<hr class='red-line' />", unsafe_allow_html=True)

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
                st.markdown("<span style='color:white; font-weight:600;'>Choose report format:</span>", unsafe_allow_html=True)
                
                # Format selection dropdown for Treasury report
                st.markdown("<h3 style='color:#f5f5f5;'>📥 Download Treasury Investment Report</h3>", unsafe_allow_html=True)

                col1, col2 = st.columns(2)

                with col1:
                    excel_file = export_to_excel(treasury_data, [], [])
                    st.download_button(
                        label="⬇️ Download Excel Report",
                        data=excel_file,
                        file_name="Treasury_Bill_Investment_Output.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

                with col2:
                    pdf_file = export_to_pdf(treasury_data, [], [], user_details, logo_image)
                    st.download_button(
                        label="📄 Download PDF Report",
                        data=pdf_file,
                        file_name="Treasury_Bill_Investment_Output.pdf",
                        mime="application/pdf"
                    )

    # Handle Bond logic
    elif investment_type == "Bond":
        st.header("Bond Investment")
        investment = st.number_input("Investment Amount (K)", min_value=5000, step=5000)
        term = st.number_input("Term (Years)", min_value=1)
        coupon_rate = st.number_input("Coupon Rate (%)", min_value=0.0)
        yield_rate = st.number_input("Yield Rate (%)", min_value=0.0)
        purchase_date = st.date_input("Purchase Date", min_value=datetime.today())

        if st.button("Calculate Bond"):
            if investment % 5000 != 0:
                st.error("Investment must be in multiples of 5000.")
            elif investment <= 0 or term <= 0 or coupon_rate <= 0 or yield_rate <= 0:
                st.error("Please enter valid inputs for all fields.")
            else:
                bond_price, bond_cost_post_fee, bond_coupon_after_tax, coupon_dates, payments = calculate_bond(
                    investment, term, coupon_rate, yield_rate / 100, purchase_date
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
                    "Yield Rate (%)": yield_rate,
                    "Bond Price per Unit (K)": round(bond_price, 2),
                    "Total Cost (Post Fee) (K)": round(bond_cost_post_fee, 2),
                    "Coupon (After Tax) (K)": round(bond_coupon_after_tax, 2),
                    "Total Return on Bond (K)": round(investment + (bond_coupon_after_tax * term * 2), 2),
                    "Coupon Dates": coupon_dates,
                    "Coupon Payments": payments
                }
                st.markdown("<span style='color:white; font-weight:600;'>Choose report format:</span>", unsafe_allow_html=True)
                # Format selection dropdown for Bond report
                st.markdown("<h3 style='color:#f5f5f5;'>📥 Download Bond Investment Report</h3>", unsafe_allow_html=True)

                col1, col2 = st.columns(2)

                with col1:
                    excel_file = export_to_excel(bond_data, coupon_dates, payments)
                    st.download_button(
                        label="⬇️ Download Excel Report",
                        data=excel_file,
                        file_name="Bond_Investment_Output.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

                with col2:
                    pdf_file = export_to_pdf(bond_data, coupon_dates, payments, user_details, logo_image)
                    st.download_button(
                        label="📄 Download PDF Report",
                        data=pdf_file,
                        file_name="Bond_Investment_Output.pdf",
                        mime="application/pdf"
                    )



if __name__ == "__main__":
    app()
