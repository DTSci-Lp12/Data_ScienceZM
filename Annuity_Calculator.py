import streamlit as st
import pandas as pd
import base64
import random
import re  # To remove emojis
import io
from io import BytesIO
from datetime import datetime
from fpdf import FPDF
from PIL import Image, ImageDraw
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

# Now `border_image` is your circular logo with a white border, ready to pass into generate_pdf(...)


# ---------- Custom Styling ----------
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


# ---------- Clean text (remove emojis) ----------
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
def clean_text(text):
    return str(text).replace("_", " ").title()
def generate_pdf(data, investor_name, border_image):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # --- Convert logo image to base64 and insert ---
    buffered = BytesIO()
    border_image.save(buffered, format="PNG")
    img_bytes = buffered.getvalue()
    img_path = "/tmp/logo.png"
    with open(img_path, "wb") as f:
        f.write(img_bytes)

    # Header: Logo Left, Timestamp Center, Report Number Right
    pdf.image(img_path, x=10, y=10, w=25)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report_number = f"Report #{random.randint(1000, 9999)}"
    
    pdf.set_font("Arial", size=10)
    pdf.set_xy(60, 10)
    pdf.cell(90, 10, txt=timestamp, ln=0, align="C")

    pdf.set_xy(150, 10)
    pdf.cell(50, 10, txt=report_number, ln=1, align="R")

    pdf.ln(20)  # space after header

    # Title
    pdf.set_font("Arial", 'B', 14)
    title = f"Yengo Annuity Summary Report for {investor_name}"
    pdf.cell(0, 10, title, ln=True, align="C")

    pdf.ln(8)

    # Report Summary
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "Report", ln=True)
    pdf.set_font("Arial", size=11)
    summary_text = "This report summarizes your annuity projections based on your inputs. It includes present value, future value, contributions, and effective returns."
    pdf.multi_cell(0, 8, summary_text)

    pdf.ln(5)

    # Output Data Table
    pdf.set_font("Arial", 'B', 11)
    pdf.set_fill_color(240, 240, 240)
    pdf.set_text_color(0)

    # Table headers
    pdf.cell(60, 10, "Metric", border=1, align="C", fill=True)
    pdf.cell(120, 10, "Value", border=1, align="C", fill=True)
    pdf.ln()

    pdf.set_font("Arial", size=11)
    for key, value in data.items():
        pdf.cell(60, 10, txt=key, border=1)
        pdf.cell(120, 10, txt=str(value), border=1)
        pdf.ln()

    pdf.ln(10)

    # Footer
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
    # Sidebar Inputs
    st.sidebar.header("Investor Inputs")
    investor_name = st.sidebar.text_input("Investor Name", value="John Doe")
    annual_contribution = st.sidebar.number_input("Annual Contribution (ZMW)", min_value=0.0, value=12000.0, step=100.0)
    nominal_rate = st.sidebar.number_input("Annual Interest Rate (%)", min_value=0.0, value=12.0, step=0.1)
    start_date = st.sidebar.date_input("Start Date", datetime(2022, 1, 1))
    end_date = st.sidebar.date_input("End Date", datetime(2022, 12, 31))

    # Title & Info
    st.title("Yengo | Annuity Valuation Calculator")
    st.markdown("<p style='color:white; font-weight:bold; font-style:italic;'>Calculate the present and future value of daily contributions with ease. Simlpy input your parameters on the input fields found on the sidebar.</p>", unsafe_allow_html=True)
    st.markdown(f"🕒 **{datetime.now().strftime('%A, %d %B %Y | %I:%M %p')}**")
    st.markdown("<hr class='red-line'>", unsafe_allow_html=True)

    # Perform Calculation
    if start_date < end_date:
        num_days, daily_payment, future_value, present_value, total_gain, effective_return = calculate_annuity_value(
            start_date, end_date, annual_contribution, nominal_rate
        )

        st.subheader("Results Summary")
        box_style = """
            background-color: rgba(255, 255, 255, 0.05);
            color: white;
            padding: 10px 20px;
            border-radius: 12px;
            border: 1.5px solid white;
            display: inline-block;
        """

        colA, colB = st.columns(2)
        with colA:
            st.markdown(f"""
                <div style="color: white;">
                    <h5>Contribution Days</h5>
                    <div style="{box_style}">
                        <h3>{num_days}</h3>
                    </div>
                </div><br>
            """, unsafe_allow_html=True)

        with colB:
            st.markdown(f"""
                <div style="color: white;">
                    <h5>Daily Contribution</h5>
                    <div style="{box_style}">
                        <h3>ZMW {daily_payment:.2f}</h3>
                    </div>
                </div><br>
            """, unsafe_allow_html=True)

        colC, colD = st.columns(2)
        with colC:
            st.markdown(f"""
                <div style="color: white;">
                    <h5>Future Value</h5>
                    <div style="{box_style}">
                        <h3>ZMW {future_value:,.2f}</h3>
                    </div>
                </div><br>
            """, unsafe_allow_html=True)

        with colD:
            st.markdown(f"""
                <div style="color: white;">
                    <h5>Present Value</h5>
                    <div style="{box_style}">
                        <h3>ZMW {present_value:,.2f}</h3>
                    </div>
                </div><br>
            """, unsafe_allow_html=True)

        colE, colF = st.columns(2)
        with colE:
            st.markdown(f"""
                <div style="color: white;">
                    <h5>Interest Earned</h5>
                    <div style="{box_style}">
                        <h3>ZMW {total_gain:,.2f}</h3>
                    </div>
                </div><br>
            """, unsafe_allow_html=True)
        with colF:
            st.markdown(f"""
                <div style="color: white;">
                    <h5>Effective Annual Return</h5>
                    <div style="{box_style}">
                        <h3>{effective_return * 100:.2f}%</h3>
                    </div>
                </div><br><br>
            """, unsafe_allow_html=True)

        # Prepare Data for Export
        results_data = {
            "Investor Name": investor_name,
            "Contribution Days": num_days,
            "Daily Contribution (ZMW)": f"{daily_payment:.2f}",
            "Future Value (ZMW)": f"{future_value:,.2f}",
            "Present Value (ZMW)": f"{present_value:,.2f}",
            "Interest Earned (ZMW)": f"{total_gain:,.2f}",
            "Effective Annual Return (%)": f"{effective_return * 100:.2f}",
        }

        # Example: Only show download section if all inputs are filled
        if daily_payment and num_days and future_value:  # or whatever conditions are appropriate
            st.markdown("""
                <hr class='red-line' />
            """, unsafe_allow_html=True)

            st.subheader("📂 Downloads")
            st.markdown("""
                <div style="color: white;">
                    You can download a detailed report of your annuity calculations in your preferred format below.
                </div><br> 
            """, unsafe_allow_html=True)

          # Inject CSS to style the selectbox
        # Inject CSS to style the selectbox and options
        st.markdown("""
            <style>
            div[data-baseweb="select"] > div {
                background-color: transparent !important;
                color: white !important;
                border: 1px solid white;
                border-radius: 8px;
            }
            div[data-baseweb="select"] div[role="option"] {
                background-color: black !important;
                color: white !important;
            }
            </style>
        """, unsafe_allow_html=True)

        # White-colored label
        st.markdown("<span style='color:white; font-weight:600;'>Choose report format:</span>", unsafe_allow_html=True)

        # Selectbox without internal label
        format_choice = st.selectbox(
            "",
            ["Select format", "Excel (.xlsx)", "PDF (.pdf)"]
        )



        # Show the single download button only after a format is chosen
        if format_choice != "Select format":
            st.markdown("<h3 style='color:#f5f5f5;'>📥 Download Report</h3>", unsafe_allow_html=True)

            if format_choice == "Excel (.xlsx)":
                excel_data = convert_to_excel(pd.DataFrame([results_data]))
                st.download_button(
                    label="⬇️ Download Excel Report",
                    data=excel_data,
                    file_name="Yengo_Annuity_Report.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            elif format_choice == "PDF (.pdf)":
                if investor_name and results_data and border_image:
                    pdf_bytes = generate_pdf(results_data, investor_name, border_image)
                    st.download_button(
                        label="⬇️ Download PDF Report",
                        data=pdf_bytes,
                        file_name="Yengo_Annuity_Summary.pdf",
                        mime="application/pdf",
                    )



    else:
        st.error("⚠️ Please ensure the start date is earlier than the end date.")


# ---------- Run App ----------
if __name__ == "__main__":
    app()