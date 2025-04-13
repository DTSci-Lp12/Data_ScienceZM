import streamlit as st
import pandas as pd
import base64
import random
import re
import io
from io import BytesIO
from datetime import datetime
from fpdf import FPDF
from PIL import Image, ImageDraw

# --- Load and process logo ---
logo_path = "Yengo_1.jpg"
image = Image.open(logo_path).convert("L").convert("RGBA")
min_side = min(image.size)
image = image.crop((
    (image.width - min_side) // 2,
    (image.height - min_side) // 2,
    (image.width + min_side) // 2,
    (image.height + min_side) // 2
))

mask = Image.new('L', image.size, 0)
draw = ImageDraw.Draw(mask)
draw.ellipse((0, 0, image.size[0], image.size[1]), fill=255)
image.putalpha(mask)

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
st.markdown("""
    <style>
    /* Styling */
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
    </style>
""", unsafe_allow_html=True)

# ---------- Annuity Calculation ----------
def calculate_annuity_value(start_date, end_date, annual_contribution, nominal_rate):
    num_days = (end_date - start_date).days
    daily_payment = annual_contribution / num_days
    effective_daily_rate = (nominal_rate / 100) / num_days
    compounding_factors = [(1 + effective_daily_rate) ** i for i in reversed(range(num_days))]
    future_value = sum([daily_payment * f for f in compounding_factors])
    discounting_factors = [1 / f for f in compounding_factors]
    present_value = sum([daily_payment * f for f in discounting_factors])
    effective_return = (future_value / present_value) - 1
    total_gain = future_value - present_value
    return num_days, daily_payment, future_value, present_value, total_gain, effective_return

# ---------- Clean text ----------
def clean_text(text):
    return re.sub(r'[^\x00-\x7F]+', '', text)

# ---------- Excel Export ----------
def convert_to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Annuity Results")
    output.seek(0)
    return output

# ---------- PDF Report ----------
def generate_pdf(data, investor_name, border_image):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    buffered = BytesIO()
    border_image.save(buffered, format="PNG")
    img_bytes = buffered.getvalue()
    img_path = "/tmp/logo.png"
    with open(img_path, "wb") as f:
        f.write(img_bytes)

    pdf.image(img_path, x=10, y=10, w=25)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report_number = f"Report #{random.randint(1000, 9999)}"

    pdf.set_font("Arial", size=10)
    pdf.set_xy(60, 10)
    pdf.cell(90, 10, txt=timestamp, ln=0, align="C")
    pdf.set_xy(150, 10)
    pdf.cell(50, 10, txt=report_number, ln=1, align="R")
    pdf.ln(20)

    pdf.set_font("Arial", 'B', 14)
    title = f"Yengo Annuity Summary Report for {investor_name}"
    pdf.cell(0, 10, title, ln=True, align="C")
    pdf.ln(8)

    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "Report", ln=True)
    pdf.set_font("Arial", size=11)
    summary_text = "This report summarizes your annuity projections based on your inputs. It includes present value, future value, contributions, and effective returns."
    pdf.multi_cell(0, 8, summary_text)
    pdf.ln(5)

    pdf.set_font("Arial", 'B', 11)
    pdf.set_fill_color(240, 240, 240)
    pdf.set_text_color(0)
    pdf.cell(60, 10, "Metric", border=1, align="C", fill=True)
    pdf.cell(120, 10, "Value", border=1, align="C", fill=True)
    pdf.ln()

    pdf.set_font("Arial", size=11)
    for key, value in data.items():
        pdf.cell(60, 10, txt=key, border=1)
        pdf.cell(120, 10, txt=str(value), border=1)
        pdf.ln()

    pdf.ln(10)
    pdf.set_font("Arial", 'B', 10)
    disclaimer = "Disclaimer: This report is for informational purposes only and does not constitute financial advice."
    pdf.multi_cell(0, 8, disclaimer, align="C")
    pdf.ln(5)
    pdf.set_font("Arial", size=9)
    copyright_text = f"© {datetime.now().year} Yengo. All Rights Reserved."
    pdf.cell(0, 10, txt=copyright_text, align="C")
    return pdf.output(dest='S').encode('latin1')


# ---------- Streamlit App ----------
def app():
    st.sidebar.header("Investor Inputs")
    investor_name = st.sidebar.text_input("Investor Name", value="John Doe")
    annual_contribution = st.sidebar.number_input("Annual Contribution (ZMW)", min_value=0.0, value=12000.0, step=100.0)
    nominal_rate = st.sidebar.number_input("Annual Interest Rate (%)", min_value=0.0, value=12.0, step=0.1)
    start_date = st.sidebar.date_input("Start Date", datetime(2022, 1, 1))
    end_date = st.sidebar.date_input("End Date", datetime(2022, 12, 31))

    st.title("Yengo | Annuity Valuation Calculator")
    st.write("Calculate the present and future value of daily contributions. Simply input your parameters on the sidebar.")
    st.write(f"Date: {datetime.now().strftime('%A, %d %B %Y | %I:%M %p')}")

    if start_date < end_date:
        num_days, daily_payment, future_value, present_value, total_gain, effective_return = calculate_annuity_value(
            start_date, end_date, annual_contribution, nominal_rate
        )

        st.subheader("Results Summary")
        st.write(f"Contribution Days: {num_days}")
        st.write(f"Daily Contribution: ZMW {daily_payment:.2f}")
        st.write(f"Future Value: ZMW {future_value:,.2f}")
        st.write(f"Present Value: ZMW {present_value:,.2f}")
        st.write(f"Interest Earned: ZMW {total_gain:,.2f}")
        st.write(f"Effective Annual Return: {effective_return * 100:.2f}%")

        results_data = {
            "Investor Name": investor_name,
            "Contribution Days": num_days,
            "Daily Contribution (ZMW)": f"{daily_payment:.2f}",
            "Future Value (ZMW)": f"{future_value:,.2f}",
            "Present Value (ZMW)": f"{present_value:,.2f}",
            "Interest Earned (ZMW)": f"{total_gain:,.2f}",
            "Effective Annual Return (%)": f"{effective_return * 100:.2f}",
        }

        st.subheader("Downloads")
        st.write("Download a detailed report of your annuity calculations.")

        format_choice = st.selectbox(
            "Choose report format:",
            ["Select format", "Excel (.xlsx)", "PDF (.pdf)"]
        )

        if format_choice == "Excel (.xlsx)":
            excel_data = convert_to_excel(pd.DataFrame([results_data]))
            st.download_button(
                label="Download Excel Report",
                data=excel_data,
                file_name="Yengo_Annuity_Report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        elif format_choice == "PDF (.pdf)":
            if investor_name and results_data and border_image:
                pdf_bytes = generate_pdf(results_data, investor_name, border_image)
                st.download_button(
                    label="Download PDF Report",
                    data=pdf_bytes,
                    file_name="Yengo_Annuity_Summary.pdf",
                    mime="application/pdf",
                )

    else:
        st.error("Please ensure the start date is earlier than the end date.")

# ---------- Run App ----------
if __name__ == "__main__":
    app()
