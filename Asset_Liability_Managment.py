import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import io
from fpdf import FPDF
from io import BytesIO
from fpdf import FPDF
from io import BytesIO
from datetime import datetime
import random
from PIL import Image, ImageDraw
import plotly.graph_objects as go

# Function to handle the uploaded CSVs
def load_data(uploaded_file):
    return pd.read_csv(uploaded_file)
def run_monte_carlo_simulation(stock_data, inflation_data, interest_data, forex_data, bond_data, initial_user_price, runs=10000):
    stock_returns = stock_data['Close'].pct_change().dropna()
    inflation_returns = inflation_data['InflationRate'].pct_change().dropna()
    interest_returns = interest_data['InterestRate'].pct_change().dropna()
    forex_returns = forex_data['USD/ZMW'].pct_change().dropna()
    bond_returns = bond_data['Yield'].pct_change().dropna()

    # Align datasets
    min_len = min(len(stock_returns), len(inflation_returns), len(interest_returns), len(forex_returns), len(bond_returns))
    stock_returns = stock_returns[-min_len:]
    inflation_returns = inflation_returns[-min_len:]
    interest_returns = interest_returns[-min_len:]
    forex_returns = forex_returns[-min_len:]
    bond_returns = bond_returns[-min_len:]

    df = pd.DataFrame({
        'stock': stock_returns.values,
        'inflation': inflation_returns.values,
        'interest': interest_returns.values,
        'forex': forex_returns.values,
        'bond': bond_returns.values
    })

    correlations = df.corr()['stock'].drop('stock')
    weights = {
        'inflation': -abs(correlations['inflation']),
        'interest': -abs(correlations['interest']),
        'forex': correlations['forex'],
        'bond': -abs(correlations['bond'])
    }

    adjusted_returns = df['stock'] + (
        weights['inflation'] * df['inflation'] +
        weights['interest'] * df['interest'] +
        weights['forex'] * df['forex'] +
        weights['bond'] * df['bond']
    )

    simulated_prices = np.zeros(runs)
    for i in range(runs):
        simulated_path = np.random.choice(adjusted_returns, size=min_len, replace=True)
        simulated_prices[i] = float(initial_user_price) * np.prod(1 + simulated_path)

    return simulated_prices
# Excel export without requiring xlsxwriter

def generate_excel(simulated_prices, investor_name, profession, address, csd_number, bank_name, bank_account, employer):
    df_prices = pd.DataFrame(simulated_prices, columns=["Simulated Price"])

    # Calculate simulation statistics
    mean_price = round(float(np.mean(simulated_prices)), 2)
    std_dev = round(float(np.std(simulated_prices)), 2)
    max_price = round(float(np.max(simulated_prices)), 2)
    min_price = round(float(np.min(simulated_prices)), 2)

    # Prepare summary data row-by-row
    summary_data = [
        ("Investor Name", investor_name),
        ("Profession", profession),
        ("Address", address),
        ("CSD Account Number", csd_number),
        ("Commercial Bank Name", bank_name),
        ("Bank Account Number", bank_account),
        ("Employer", employer),
        ("Mean Price", mean_price),
        ("Standard Deviation", std_dev),
        ("Max Price", max_price),
        ("Min Price", min_price),
    ]
    df_summary = pd.DataFrame(summary_data, columns=["Field", "Value"])

    # Write both sheets to Excel
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df_prices.to_excel(writer, index=False, sheet_name="Simulation")
        df_summary.to_excel(writer, index=False, sheet_name="Summary")
    buffer.seek(0)
    return buffer


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
# PDF export
from fpdf import FPDF
from io import BytesIO
from datetime import datetime
import random
logo_image=border_image
def  generate_pdf_report(mean_price, std_dev, max_price, min_price, logo_image, investor_name, profession, address, csd_number, bank_name, bank_account, employer):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # --- Convert logo image to temp file path ---
    buffered = BytesIO()
    logo_image.save(buffered, format="PNG")
    logo_bytes = buffered.getvalue()
    logo_path = "/tmp/logo_mc.png"
    with open(logo_path, "wb") as f:
        f.write(logo_bytes)

    # --- Header: Logo | Timestamp | Report Number ---
    pdf.image(logo_path, x=10, y=10, w=25)  # Logo left

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report_number = f"Report #{random.randint(1000, 9999)}"

    pdf.set_font("Arial", size=10)
    pdf.set_xy(60, 10)
    pdf.cell(90, 10, txt=timestamp, ln=0, align="C")  # Timestamp center

    pdf.set_xy(150, 10)
    pdf.cell(50, 10, txt=report_number, ln=1, align="R")  # Report number right

    pdf.ln(20)

    # --- Title ---
    pdf.set_font("Arial", 'B', 14)
    title = f"Monte Carlo Simulation Report"
    pdf.cell(0, 10, title, ln=True, align="C")
    pdf.ln(10)

  

    # --- Short Description ---
    pdf.set_font("Arial", size=11)
    description = (
        "This report presents the results of a Monte Carlo simulation, "
        "estimating potential future stock prices based on historical and macroeconomic data. "
        "Below are the investor's details:"
    )
    pdf.multi_cell(0, 8, description)
    pdf.ln(5)

    # --- Investor Details Section ---
    pdf.set_font("Arial", 'B', 11)

    # Set red color for border
    pdf.set_draw_color(255, 0, 0)  # RGB for red

    # Define position and size for the box
    box_x = pdf.get_x()
    box_y = pdf.get_y()
    box_width = 190  # Full width minus margins
    box_height = 60  # Adjust depending on content

    # Draw the red rectangle box
    pdf.rect(x=box_x, y=box_y, w=box_width, h=box_height)

    # Padding inside the box (optional)
    pdf.set_xy(box_x + 2, box_y + 2)

    # Investor details
    details = [
        ("Investor Name", investor_name),
        ("Profession", profession),
        ("Address", address),
        ("CSD Account Number", csd_number),
        ("Commercial Bank Name", bank_name),
        ("Bank Account Number", bank_account),
        ("Employer", employer),
    ]

    for label, value in details:
        pdf.cell(60, 8, f"{label}:", ln=0)
        pdf.cell(0, 8, f"{value}", ln=1, align="R")

    pdf.ln(5)  # Space after the box

    
      # --- Table Header ---
    pdf.set_font("Arial", 'B', 12)
    pdf.set_fill_color(230, 230, 230)
    pdf.set_text_color(0)
    pdf.cell(90, 10, "Metric", border=1, align="C", fill=True)
    pdf.cell(90, 10, "Value", border=1, align="C", fill=True)
    pdf.ln()
    # --- Table Rows ---
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(90, 10, "Average Simulated Price", border=1, align="C")
    pdf.cell(90, 10, f"K{mean_price:,.2f}", border=1, align="C")
    pdf.ln()

    pdf.cell(90, 10, "Standard Deviation", border=1, align="C")
    pdf.cell(90, 10, f"K{std_dev:,.2f}", border=1, align="C")
    pdf.ln()

    pdf.cell(90, 10, "Maximum Simulated Price", border=1, align="C")
    pdf.cell(90, 10, f"K{max_price:,.2f}", border=1, align="C")
    pdf.ln()

    pdf.cell(90, 10, "Minimum Simulated Price", border=1, align="C")
    pdf.cell(90, 10, f"K{min_price:,.2f}", border=1, align="C")
    pdf.ln(15)

    # --- Disclaimer Footer ---
    pdf.set_font("Arial", 'B', 10)
    disclaimer = "Disclaimer: This simulation is for informational purposes only and should not be considered financial advice."
    pdf.multi_cell(0, 8, disclaimer, align="C")

    pdf.ln(5)
    pdf.set_font("Arial", size=9)
    copyright_text = f"© {datetime.now().year} Yengo. All Rights Reserved."
    pdf.cell(0, 10, txt=copyright_text, align="C")

    # --- Return as BytesIO ---
    pdf_bytes = pdf.output(dest='S').encode('latin1')
    return BytesIO(pdf_bytes)



# Template CSV generators
def generate_template(data_type):
    example_data = {
        "Stock": pd.DataFrame({
            "Date": pd.date_range(start="2023-01-01", periods=5, freq='D'),
            "Close": [100, 102, 101, 103, 105]
        }),
        "Inflation": pd.DataFrame({
            "Date": pd.date_range(start="2023-01-01", periods=5, freq='M'),
            "InflationRate": [3.5, 3.6, 3.4, 3.7, 3.8]
        }),
        "Interest": pd.DataFrame({
            "Date": pd.date_range(start="2023-01-01", periods=5, freq='M'),
            "InterestRate": [4.5, 4.6, 4.4, 4.7, 4.8]
        }),
        "Forex": pd.DataFrame({
            "Date": pd.date_range(start="2023-01-01", periods=5, freq='D'),
            "USD/ZMW": [19.5, 19.7, 19.6, 19.8, 20.0]
        }),
        "Bond": pd.DataFrame({
            "Date": pd.date_range(start="2023-01-01", periods=5, freq='M'),
            "Yield": [6.5, 6.6, 6.7, 6.8, 6.9]
        })
    }
    df = example_data.get(data_type)
    buffer = io.BytesIO()
    df.to_csv(buffer, index=False)
    buffer.seek(0)
    return buffer

# Streamlit app
def app():
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
""", unsafe_allow_html=True)

    st.title("Yengo | ALM Financial Optimization Model")
    st.write("At Yengo, our ALM (Asset-Liability Management) model goes beyond traditional forecasting. Using Monte Carlo simulations and correlation analysis, we model the future expected price of a stock by incorporating real-world market complexity. Historical stock prices are analyzed alongside key macroeconomic drivers—inflation, Forex, interest rates, and bond yields—to simulate thousands of potential market scenarios. This allows us to capture the interconnected nature of financial variables and deliver a more robust, data-informed outlook for stock behavior. It's a smarter way to navigate uncertainty and manage portfolio risk.")
    st.write("____________________________________________________________________")
    # Investor Details
    st.subheader("Investor Details")
    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            investor_name = st.text_input("Investor Name")
            profession = st.text_input("Profession")
            address = st.text_input("Address")
        with col2:
            csd_number = st.text_input("CSD Account Number")
            bank_name = st.text_input("Commercial Bank Name")
            bank_account = st.text_input("Commercial Bank Account Number")
            employer = st.text_input("Employer")
            initial_user_price = st.text_input("Initial Stock Price", value="100")
            try:
                initial_user_price = float(initial_user_price)
            except ValueError:
                st.error("Initial price must be a number.")
                return


    # Horizontal divider
    st.markdown("---")
    st.subheader("Upload Your Financial Data")
    
    col1, col2 = st.columns([0.1, 0.9])
    use_stock = col1.checkbox("", key="stock_checkbox")
    col2.markdown("<span style='color:#FFFFFF; font-weight:bold;'>📈 Include Stock Data</span>", unsafe_allow_html=True)

    col1, col2 = st.columns([0.1, 0.9])
    use_inflation = col1.checkbox("", key="inflation_checkbox")
    col2.markdown("<span style='color:#FFFFFF; font-weight:bold;'>💵 Include Inflation Data</span>", unsafe_allow_html=True)

    col1, col2 = st.columns([0.1, 0.9])
    use_interest = col1.checkbox("", key="interest_checkbox")
    col2.markdown("<span style='color:#FFFFFF; font-weight:bold;'>📊 Include Interest Rate Data</span>", unsafe_allow_html=True)

    col1, col2 = st.columns([0.1, 0.9])
    use_forex = col1.checkbox("", key="forex_checkbox")
    col2.markdown("<span style='color:#FFFFFF; font-weight:bold;'>💱 Include Forex Data</span>", unsafe_allow_html=True)

    col1, col2 = st.columns([0.1, 0.9])
    use_bond = col1.checkbox("", key="bond_checkbox")
    col2.markdown("<span style='color:#FFFFFF; font-weight:bold;'>🏛️ Include Bond Yield Data</span>", unsafe_allow_html=True)

    stock_data = inflation_data = interest_data = forex_data = bond_data = None

    # Stock Data Upload
    if use_stock:
        st.markdown("**Stock data should include columns like `Date` and `Close` (daily closing prices).**Use template below:")
        st.download_button("📄 Download Stock Template", generate_template("Stock"), file_name="stock_template.csv", mime="text/csv")
        stock_file = st.file_uploader("Upload Stock Data (CSV)", type=["csv"], key="stock")
        if stock_file:
            stock_data = load_data(stock_file)
            st.write("### Stock Data Preview", stock_data.head())

    # Inflation Data Upload
    if use_inflation:
        st.markdown("**Inflation data should include columns like `Date` and `InflationRate` (monthly inflation %).**Use template below:")
        st.download_button("📄 Download Inflation Template", generate_template("Inflation"), file_name="inflation_template.csv", mime="text/csv")
        inflation_file = st.file_uploader("Upload Inflation Data (CSV)", type=["csv"], key="inflation")
        if inflation_file:
            inflation_data = load_data(inflation_file)
            st.write("### Inflation Data Preview", inflation_data.head())

    # Interest Rate Data Upload
    if use_interest:
        st.markdown("**Interest rate data should include `Date` and `InterestRate` columns (monthly %).**Use template below:")
        st.download_button("📄 Download Interest Rate Template", generate_template("Interest"), file_name="interest_template.csv", mime="text/csv")
        interest_file = st.file_uploader("Upload Interest Rate Data (CSV)", type=["csv"], key="interest")
        if interest_file:
            interest_data = load_data(interest_file)
            st.write("### Interest Rate Data Preview", interest_data.head())

    # Forex Data Upload
    if use_forex:
        st.markdown("**Forex data should include `Date` and `USD/ZMW` exchange rate values.**Use template below:")
        st.download_button("📄 Download Forex Template", generate_template("Forex"), file_name="forex_template.csv", mime="text/csv")
        forex_file = st.file_uploader("Upload Forex Data (CSV)", type=["csv"], key="forex")
        if forex_file:
            forex_data = load_data(forex_file)
            st.write("### Forex Data Preview", forex_data.head())

    # Bond Yield Data Upload
    if use_bond:
        st.markdown("**Bond yield data should include `Date` and `Yield` columns (monthly %).**Use template below:")
        st.download_button("📄 Download Bond Yield Template", generate_template("Bond"), file_name="bond_template.csv", mime="text/csv")
        bond_file = st.file_uploader("Upload Bond Yield Data (CSV)", type=["csv"], key="bond")
        if bond_file:
            bond_data = load_data(bond_file)
            st.write("### Bond Yield Data Preview", bond_data.head())
    # Check if all files are uploaded
    if stock_data is not None and inflation_data is not None and interest_data is not None and forex_data is not None and bond_data is not None:
        st.success("✅ All datasets uploaded successfully.")

        try:
            initial_user_price_float = float(initial_user_price)
            # Run simulation
            simulated_prices = run_monte_carlo_simulation(
                stock_data, inflation_data, interest_data, forex_data, bond_data, initial_user_price_float
            )
            st.markdown("<hr class='red-line'>", unsafe_allow_html=True)
            # Plot results
            st.subheader("📈 Simulation Results (Interactive)")

            # Create histogram using Plotly
            fig = go.Figure()

            fig.add_trace(go.Histogram(
                x=simulated_prices,
                nbinsx=50,
                marker=dict(
                    color='red',
                    line=dict(color='black', width=1),
                    opacity=0.85
                ),
                hoverlabel=dict(
                    bgcolor="white",
                    font_size=13,
                    font_family="Arial"
                ),
                name="Simulated Prices"
            ))

            # Customize layout with dark mode styling
            fig.update_layout(
                title="Monte Carlo Simulation of Stock Prices",
                xaxis_title="Simulated Price",
                yaxis_title="Frequency",
                plot_bgcolor="rgb(30,30,30)",  # dark grey
                paper_bgcolor="rgb(10,10,10)",  # black
                font=dict(color="white", family="Arial"),
                margin=dict(l=40, r=40, t=60, b=40),
                height=500
            )

            # Display interactive chart
            st.plotly_chart(fig, use_container_width=True)
            # 📊 Calculate statistics
            mean_price = np.mean(simulated_prices)
            std_dev = np.std(simulated_prices)
            max_price = np.max(simulated_prices)
            min_price = np.min(simulated_prices)

            # ✅ Display the statistics in a stylish table
            st.markdown("""
                <style>
                    .stats-table {{
                        width: 70%;
                        margin: 20px auto;
                        border-collapse: collapse;
                        font-family: 'Segoe UI', sans-serif;
                        background-color: #1c1c1c;
                        color: white;
                        border: 1px solid red;
                        box-shadow: 0 0 15px rgba(255, 0, 0, 0.3);
                    }}
                    .stats-table th {{
                        background-color: #2e2e2e;
                        color: red;
                        padding: 12px;
                        text-align: left;
                        font-size: 16px;
                    }}
                    .stats-table td {{
                        background-color: #333;
                        color: white;
                        padding: 10px;
                        font-size: 15px;
                        border-top: 1px solid #555;
                    }}
                </style>

                <table class="stats-table">
                    <tr>
                        <th>Statistic</th>
                        <th>Value</th>
                    </tr>
                    <tr>
                        <td>Mean Price</td>
                        <td>{:.2f}</td>
                    </tr>
                    <tr>
                        <td>Standard Deviation</td>
                        <td>{:.2f}</td>
                    </tr>
                    <tr>
                        <td>Max Price</td>
                        <td>{:.2f}</td>
                    </tr>
                    <tr>
                        <td>Min Price</td>
                        <td>{:.2f}</td>
                    </tr>
                </table>
            """.format(mean_price, std_dev, max_price, min_price), unsafe_allow_html=True)

            # ✨ Create a DataFrame with the same data
            stats_df = pd.DataFrame({
                "Statistic": ["Mean Price", "Standard Deviation", "Max Price", "Min Price"],
                "Value": [mean_price, std_dev, max_price, min_price]
            })

            # 📤 Offer download as Excel
            from io import BytesIO

            def download_stats_excel(df):
                buffer = BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name="Simulation Stats")
                buffer.seek(0)
                return buffer

            excel_stats = download_stats_excel(stats_df)

            st.download_button(
                label="📥 Download Simulation Statistics (Excel)",
                data=excel_stats,
                file_name="simulation_statistics.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
            st.markdown("<hr class='red-line'>", unsafe_allow_html=True)
            st.subheader("📂 Downloads")
            st.markdown("""
                <div style="color: white;">
                    You can download a detailed report of your Monte Carlo Simulation forcast in your preferred format below.
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
            # White-colored label for format selection
            st.markdown("<span style='color:white; font-weight:600;'>Choose report format:</span>", unsafe_allow_html=True)
    
            # Format selection dropdown
            monte_carlo_format = st.selectbox(
                "",
                ["Select format", "Excel (.xlsx)", "PDF (.pdf)"],
                key="monte_carlo_format"
            )

            # Only show download button(s) if a valid format is selected
            if monte_carlo_format != "Select format":
                st.markdown("<h3 style='color:#f5f5f5;'>📥 Download Monte Carlo Report</h3>", unsafe_allow_html=True)

                if monte_carlo_format == "Excel (.xlsx)":
                    excel_data = generate_excel(
                    simulated_prices,
                    investor_name,
                    profession,
                    address,
                    csd_number,
                    bank_name,
                    bank_account,
                    employer
                )

                    st.download_button(
                        label="⬇️ Download Excel Report",
                        data=excel_data,
                        file_name="monte_carlo_simulation.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

                elif monte_carlo_format == "PDF (.pdf)":
                    if investor_name and simulated_prices is not None:
                        pdf_report = generate_pdf_report(
                            mean_price,
                            std_dev,
                            max_price,
                            min_price,
                            logo_image,
                            investor_name,
                            profession,
                            address,
                            csd_number,
                            bank_name,
                            bank_account,
                            employer
                        )
                        st.download_button(
                            label="📄 Download PDF Report",
                            data=pdf_report,
                            file_name="monte_carlo_report.pdf",
                            mime="application/pdf"
                        )
        except ValueError:
                st.error("🚫 Initial price must be a numeric value.")

    else:
        st.warning("📂 Please upload all five datasets to proceed with the simulation.")


if __name__ == "__main__":
    app()
