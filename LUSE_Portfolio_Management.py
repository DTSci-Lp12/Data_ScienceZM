import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from statsmodels.tsa.arima.model import ARIMA
from datetime import datetime
from io import BytesIO
from fpdf import FPDF
from openpyxl import Workbook
from PIL import Image, ImageDraw, ImageOps
import plotly.graph_objects as go
import plotly.figure_factory as ff
import os
import logging
import tempfile

# --- Logging ---
logging.basicConfig(
    filename='app.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
# --- Data Validation ---
def validate_data_structure(data):
    return 'COMPANY' in data.columns

# --- Load CSV with validation ---
def load_data(file):
    try:
        data = pd.read_csv(file)
        if not validate_data_structure(data):
            st.error("Invalid structure! File must include a 'COMPANY' column.")
            return None
        data = data.fillna(0)
        data['COMPANY'] = data['COMPANY'].str.strip()
        return data
    except Exception as e:
        logging.error(f"Error loading data: {e}")
        st.error("There was an error processing the file. Please try again.")
        return None
# --- Generate a downloadable CSV template ---
def generate_template():
    template_df = pd.DataFrame({
        "COMPANY": ["ZAMBEEF", "ZANACO", "CEC"],
        "2021-01-01": [1.5, 2.1, 3.0],
        "2021-01-02": [1.6, 2.0, 3.1],
        "2021-01-03": [1.55, 2.05, 3.05]
    })
    buffer = BytesIO()
    template_df.to_csv(buffer, index=False)
    buffer.seek(0)
    return buffer
# --- Streamlit App ---
def app():
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
    </style>
""", unsafe_allow_html=True)

    st.title("Yengo | Lusaka Stock Exchange (LUSE) Portfolio Management")

    st.markdown("""
        About the Author: Limbani Phiri brings a wealth of experience from his extensive career across the banking, insurance, and commerce industries. As the CEO of Yengo, he has played a pivotal role in the development and creation of the Yengo platform.
    """)
    st.markdown(f"🕒 **{datetime.now().strftime('%A, %d %B %Y | %I:%M %p')}**")
    # --- Download Template Section ---
    st.markdown("### 📥 Download CSV Template")
    st.markdown("""
        To get started, download the CSV template below.  
        Fill it in with your own historical data, ensuring:
        - The first column is `COMPANY`
        - Subsequent columns are dates (format: YYYY-MM-DD)
        - Each row represents stock prices for a single company
    """)
    template_csv = generate_template()
    st.download_button(
        label="📄 Download Template CSV",
        data=template_csv,
        file_name="LUSE_template.csv",
        mime="text/csv"
    )
    uploaded_file = st.file_uploader("📁 Upload your LUSE Stock Data CSV file", type=["csv"])

    if uploaded_file:
        data = load_data(uploaded_file)
        if data is not None:
            st.markdown("### 🔍 Preview of Uploaded Data")
            st.dataframe(data.head())
            st.markdown("<hr class='red-line' />", unsafe_allow_html=True)

            try:
                temp = data.drop(columns=['COMPANY']).transpose()
                temp.columns = data['COMPANY'].values
                company_names = data['COMPANY'].values
                ModelData_Margins = np.diff(temp.values, axis=0)
                ModelData_Margins[ModelData_Margins == 0] = np.nan
            except Exception as e:
                logging.error(f"Error processing stock data: {e}")
                st.error("Could not process stock data. Check format.")
                return

            selected_company = st.selectbox("📊 Select a company for analysis", options=list(temp.columns))
            st.markdown(f"## 📊 Analysis for: `{selected_company}`")

            try:
                # --- Plot closing prices ---
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=temp.index, y=temp[selected_company], mode='lines', name='Closing Price', line=dict(color='red', width=3)))
                fig.update_layout(title=f"{selected_company} - Time Series", title_font=dict(size=22, color='white'))
                st.plotly_chart(fig)

                # --- ARIMA Forecast ---
                model = ARIMA(temp[selected_company], order=(5, 1, 0))
                fit = model.fit()
                forecast = fit.forecast(steps=300)
                fig2 = go.Figure()
                fig2.add_trace(go.Scatter(x=list(range(len(forecast))), y=forecast, mode='lines', name='Forecast', line=dict(color='limegreen', width=3)))
                st.plotly_chart(fig2)

            except Exception as e:
                logging.error(f"Error in forecast or plot: {e}")
                st.error("There was a problem with forecasting.")
                return

            try:
                # --- Portfolio Simulation ---
                initial_portfolio = 1000
                initial_price = temp[selected_company].iloc[-1]
                initial_value = initial_portfolio * initial_price
                mean_margin = np.nanmean(ModelData_Margins[:, temp.columns.get_loc(selected_company)])
                std_margin = np.nanstd(ModelData_Margins[:, temp.columns.get_loc(selected_company)])

                simulated_prices = []
                for _ in range(10000):
                    returns = np.random.normal(loc=mean_margin, scale=std_margin, size=300)
                    path = initial_price + np.cumsum(returns)
                    simulated_prices.append(path[-1])

                fig3 = ff.create_distplot([simulated_prices], group_labels=[f"{selected_company} Simulation"], show_hist=False, colors=['orange'])
                fig3.update_layout(title=f"{selected_company} - Simulated Distribution", title_font=dict(size=22, color='white'))
                st.plotly_chart(fig3)

                # --- Summary ---
                expected_price = np.mean(simulated_prices)
                final_value = expected_price * initial_portfolio
                change = final_value - initial_value

                st.markdown("### 💼 Portfolio Prediction Summary")
                st.write(f"**Expected Final Portfolio Value**: K`{final_value:.2f}`")
                st.write(f"**Change in Value**: K`{change:.2f}`")

            except Exception as e:
                logging.error(f"Simulation error: {e}")
                st.error("There was a problem simulating the portfolio.")
                return
        else:
            st.warning("Please upload a valid CSV file.")
    else:
        st.warning("🚨 Please upload a CSV with `COMPANY` column and historical prices.")

# --- PDF Export ---
def export_pdf_summary(temp, forecast, closing_prices, selected_company, logo_image):
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
            logo_image.save(tmp.name, format="PNG")
            logo_path = tmp.name

        pdf.set_font("Arial", 'B', 14)
        pdf.image(logo_path, x=10, y=8, w=30)
        pdf.cell(0, 10, f"Report Number: {np.random.randint(1000, 9999)}", align='R', ln=1)
        pdf.cell(0, 10, datetime.now().strftime('%A, %d %B %Y | %I:%M %p'), align='C', ln=1)
        pdf.ln(5)

        pdf.set_font("Arial", 'B', 18)
        pdf.set_text_color(220, 50, 50)
        pdf.cell(0, 15, "Lusaka Stock Exchange Portfolio Prediction", ln=1, align='C')

        pdf.set_font("Arial", 'B', 14)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 10, f"Company: {selected_company}", ln=1, align='C')

        # Summary Table
        col_index = list(temp.columns).index(selected_company)
        last_price = temp.iloc[-1, col_index]
        expected_price = np.mean(closing_prices)
        final_value = expected_price * 1000
        change = final_value - (last_price * 1000)

        pdf.set_font("Arial", 'B', 12)
        for label, value, analysis in [
            ("Last Known Price", f"K{last_price:.2f}", "-"),
            ("Forecasted Avg. Price", f"K{expected_price:.2f}", "-"),
            ("Portfolio Value (x1000)", f"K{final_value:.2f}", "Positive" if change >= 0 else "Negative"),
            ("Expected Change", f"K{change:.2f}", "Positive" if change >= 0 else "Negative"),
        ]:
            pdf.cell(70, 10, label, 1)
            pdf.cell(60, 10, value, 1)
            pdf.cell(50, 10, analysis, 1, 1)

        pdf.set_y(-30)
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(0, 10, "DISCLAIMER: This is a simulation and does not guarantee future performance.", 0, 1, 'C')

        buffer = BytesIO()
        pdf.output(buffer)
        buffer.seek(0)
        return buffer

    except Exception as e:
        logging.error(f"PDF export failed: {e}")
        st.error("Failed to generate PDF summary.")

# --- Main Execution ---
if __name__ == "__main__":
    app
