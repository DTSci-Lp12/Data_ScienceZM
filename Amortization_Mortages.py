import streamlit as st
import pandas as pd
import io
import datetime
from datetime import datetime
from fpdf import FPDF
from PIL import Image, ImageDraw
import time
import tempfile

# Function to calculate the amortization schedule
def calculate_amortization(loan_amount, interest_rate, loan_term):
    monthly_interest_rate = (interest_rate / 100) / 12
    pmt = (loan_amount * monthly_interest_rate * ((1 + monthly_interest_rate) ** loan_term)) / \
        ((1 + monthly_interest_rate) ** loan_term - 1)

    schedule = []
    for i in range(1, loan_term + 1):
        interest = loan_amount * monthly_interest_rate
        principal_payment = pmt - interest
        loan_amount -= principal_payment
        schedule.append([i, principal_payment, interest, pmt, loan_amount])

    df = pd.DataFrame(schedule, columns=["Payment No.", "Principal Payment", "Interest", "Payment", "Principal Remaining"])
    return df, pmt

# Convert DataFrame to Excel
def convert_df_to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Amortization Schedule")
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
logo_image = border_image

# Convert PIL image to temporary file
def pil_image_to_temp_file(pil_image):
    # Create a temporary file to save the image
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmpfile:
        pil_image.save(tmpfile, format='PNG')  # Save the image in PNG format
        return tmpfile.name  # Return the file path

def generate_pdf(loan_amount, interest_rate, loan_term, monthly_payment, schedule_df, logo_image):
    pdf = FPDF()
    pdf.set_left_margin(9)
    pdf.set_right_margin(15)
    pdf.set_top_margin(20)
    pdf.add_page()
    # Generate dynamic report number using time module (current timestamp)
    report_number = str(int(time.time()))  # Use time since epoch as a unique identifier

    # Convert the PIL image to a temporary file and pass the file path to FPDF
    logo_image_path = pil_image_to_temp_file(logo_image)

    # Header Section
    pdf.set_font("Arial", 'B', 12)
    
    # 1. Add logo aligned right
    pdf.image(logo_image_path, x=170, y=10, w=30)  # Adjust as necessary
    
    # 2. Center-align the timestamp
    pdf.set_xy(90, 10)  # Center X position
    # Alternative method for generating timestamp
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
    pdf.cell(0, 10, timestamp, ln=0, align='C')

    # 3. Left-align the dynamic report number
    pdf.set_xy(10, 10)  # Left position
    pdf.cell(0, 10, f"Report #{report_number}", ln=0, align='L')

    # Skip 3 lines after the header
    pdf.ln(15)

    # Title: Bold and underline
    pdf.set_font("Arial", 'BU', 16)
    pdf.cell(0, 10, "Loan Amortization Schedule Report", ln=1, align="C")

    # Subheader
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "Loan Details:", ln=1, align="L")

    # Skip a line
    pdf.ln(5)

    # Add loan details in a table, center-aligned
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(50, 10, "Loan Amount", 1, 0, 'C')
    pdf.cell(50, 10, "Interest Rate", 1, 0, 'C')
    pdf.cell(50, 10, "Loan Term", 1, 0, 'C')
    pdf.cell(50, 10, "Monthly Payment", 1, 1, 'C')

    pdf.set_font("Arial", '', 10)
    pdf.cell(50, 10, f"K {loan_amount:,.2f}", 1, 0, 'C')
    pdf.cell(50, 10, f"{interest_rate} %", 1, 0, 'C')
    pdf.cell(50, 10, f"{loan_term} months", 1, 0, 'C')
    pdf.cell(50, 10, f"K {monthly_payment:,.2f}", 1, 1, 'C')

    # Skip a line
    pdf.ln(10)

    # Key Insights Section
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, "Key Insights:", ln=True)

    pdf.set_font("Arial", '', 10)
    payment_number = schedule_df[schedule_df["Principal Payment"] > schedule_df["Interest"]].iloc[0]["Payment No."]
    years_to_principal_payment = round(payment_number / 12, 1)
    total_interest_paid = schedule_df["Interest"].sum()
    total_principal_paid = schedule_df["Principal Payment"].sum()
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(200, 10, f"You will start paying more principal than interest on payment number: {payment_number}", ln=True)
    pdf.cell(200, 10, f"For the first {years_to_principal_payment} years, you'll be mostly servicing interest.", ln=True)
    pdf.cell(200, 10, f"Total interest paid over the term: K {total_interest_paid:,.2f}", ln=True)
    pdf.cell(200, 10, f"Total principal paid over the term: K {total_principal_paid:,.2f}", ln=True)

    # Skip a line
    pdf.ln(10)

    # Schedule Table (Payment details)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(30, 10, "Payment No.", 1, 0, 'C')
    pdf.cell(40, 10, "Principal Payment", 1, 0, 'C')
    pdf.cell(40, 10, "Interest", 1, 0, 'C')
    pdf.cell(40, 10, "Payment", 1, 0, 'C')
    pdf.cell(50, 10, "Principal Remaining", 1, 1, 'C')

    pdf.set_font("Arial", size=10)
    for index, row in schedule_df.iterrows():
        pdf.cell(30, 10, str(int(row["Payment No."])), 1, 0, 'C')
        pdf.cell(40, 10, f"K {row['Principal Payment']:,.2f}", 1, 0, 'C')
        pdf.cell(40, 10, f"K {row['Interest']:,.2f}", 1, 0, 'C')
        pdf.cell(40, 10, f"K {row['Payment']:,.2f}", 1, 0, 'C')
        pdf.cell(50, 10, f"K {row['Principal Remaining']:,.2f}", 1, 1, 'C')

    # Footer Section
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 8)
    pdf.cell(0, 10, "Disclaimer: This report is for informational purposes only.", ln=True, align='C')

    # Copyright Section
    pdf.set_font("Arial", 'I', 8)
    pdf.cell(0, 10, "© 2025 Yengo Corporation. All Rights Reserved.", ln=True, align='C')

    # Output the PDF
    return pdf.output(dest='S').encode('latin1')

def app():
    # Custom CSS
    st.markdown("""
        <style>
    body, .main, .stApp {
        background-color: black;
        color: white;
    }
    .stButton button {
        background-color: #D32F2F;
        color: white;
        border: none;
        padding: 10px 24px;
        font-size: 16px;
        border-radius: 5px;
    }
    .stButton button:hover {
        background-color: #b71c1c;
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
    .title, h1, h2, h3 {
        color: #FFFFFF !important;
        text-shadow: 2px 2px 5px #000000;
    }
        </style>
    """, unsafe_allow_html=True)

    # Header and date
    st.markdown('<div class="header">Yengo |  Mortgage Amortization Schedule</div>', unsafe_allow_html=True)
    st.markdown(f"🕒 **{datetime.now().strftime('%A, %d %B %Y | %I:%M %p')}**")

    # Input columns
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<p class="input-label">Loan Amount (K)</p>', unsafe_allow_html=True)
        loan_amount = st.number_input("", min_value=100000, value=5000000, step=10000, label_visibility="collapsed")

        st.markdown('<p class="input-label">Nominal Annual Interest Rate (%)</p>', unsafe_allow_html=True)
        interest_rate = st.number_input("", min_value=0.0, value=6.3, step=0.1, label_visibility="collapsed")
    with col2:
        st.markdown('<p class="input-label">Loan Term (Months)</p>', unsafe_allow_html=True)
        loan_term = st.number_input("", min_value=1, value=240, step=1, label_visibility="collapsed")

    # Call the amortization calculator
    schedule_df, monthly_payment = calculate_amortization(loan_amount, interest_rate, loan_term)

    # Download button for the PDF
    if st.button("Generate Amortization Report"):
        # Add Downloads Section with Icon
        st.markdown('''<div class="insights">
        📥 | Downloads </div>''', unsafe_allow_html=True)
        st.markdown("Download Excel or PDF report to keep a copy of your amortization schedule. Select below:")
        pdf_output = generate_pdf(loan_amount, interest_rate, loan_term, monthly_payment, schedule_df, logo_image)

        # Create two columns to place buttons side by side
        col1, col2 = st.columns(2)

        # First column: PDF download button
        with col1:
            st.write("PDF File Download Below")
            st.download_button(
                label="Download PDF",
                data=pdf_output,
                file_name="amortization_schedule.pdf",
                mime="application/pdf"
            )

        # Second column: Excel download button
        with col2:
            excel_file = convert_df_to_excel(schedule_df)
            st.write("Excel File Download Below:")
            st.download_button(
                label="Download Excel",
                data=excel_file,
                file_name="amortization_schedule.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

# Run the app
if __name__ == "__main__":
    app()
