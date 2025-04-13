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

# Set up logging for the app
logging.basicConfig(filename='app.log', level=logging.DEBUG, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Dark mode & custom styling
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

# Utility function to check the structure of the uploaded CSV
def validate_data_structure(data):
    required_columns = ['COMPANY']
    if not all(col in data.columns for col in required_columns):
        return False
    return True

# Safeguard: Add error handling for data loading and processing
def load_data(file):
    try:
        data = pd.read_csv(file)
        if not validate_data_structure(data):
            st.error("Invalid data structure! Ensure your file has a 'COMPANY' column.")
            return None
        data = data.fillna(0)
        data['COMPANY'] = data['COMPANY'].str.strip()  # Clean company names
        return data
    except Exception as e:
        logging.error(f"Error loading data: {e}")
        st.error("There was an error processing the file. Please try again.")
        return None

# Safeguard: File upload function with validation
def app():
    st.title("Yengo | Lusaka Stock Exchange (LUSE) Portfolio Management")
    st.markdown("About the Author: Limbani Phiri ...")
    st.markdown(f"🕒 **{datetime.now().strftime('%A, %d %B %Y | %I:%M %p')}**")

    uploaded_file = st.file_uploader("📁 Upload your LUSE Stock Data CSV file", type=["csv"])
    if uploaded_file:
        LUSE_Stock_Data = load_data(uploaded_file)
        if LUSE_Stock_Data is not None:
            st.markdown("### 🔍 Preview of Uploaded Data")
            st.dataframe(LUSE_Stock_Data.head())
            st.markdown("<hr class='red-line' />", unsafe_allow_html=True)

            # Safeguard: Ensure the data has the expected format
            try:
                temp = LUSE_Stock_Data.drop(columns=['COMPANY']).transpose()
                temp.columns = LUSE_Stock_Data['COMPANY'].values
                name = LUSE_Stock_Data['COMPANY'].values
                ModelData_Margins = np.diff(temp.values, axis=0)
                ModelData_Margins[ModelData_Margins == 0] = np.nan
            except Exception as e:
                logging.error(f"Error processing stock data: {e}")
                st.error("There was an error processing the stock data. Please check the file format.")
                return

            # Dynamic company selection
            selected_company = st.selectbox("📊 Select a company for analysis", options=list(temp.columns))
            st.markdown(f"## 📊 Analysis for: `{selected_company}`")

            try:
                # Plot stock prices
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=temp.index, y=temp[selected_company], mode='lines', name='Closing Price', line=dict(color='red', width=3)))
                fig.update_layout(title=f"{selected_company} - Time Series of Closing Prices", title_font=dict(size=22, color='white', family='Arial'))
                st.plotly_chart(fig)

                # ARIMA Forecast
                model = ARIMA(temp[selected_company], order=(5, 1, 0))
                fit = model.fit()
                forecast = fit.forecast(steps=300)
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=list(range(len(forecast))), y=forecast, mode='lines', name='Forecast', line=dict(color='limegreen', width=3)))
                st.plotly_chart(fig)

            except Exception as e:
                logging.error(f"Error generating plots or performing analysis: {e}")
                st.error("There was an issue generating the analysis. Please try again.")
                return

            # Simulate Portfolio
            try:
                initial_portfolio = 1000
                initial_price = temp[selected_company].iloc[-1]
                initial_value = initial_portfolio * initial_price
                mean_margin = np.nanmean(ModelData_Margins[:, temp.columns.get_loc(selected_company)])
                std_margin = np.nanstd(ModelData_Margins[:, temp.columns.get_loc(selected_company)])

                simulated_final_prices = []
                for _ in range(10000):
                    daily_returns = np.random.normal(loc=mean_margin, scale=std_margin, size=300)
                    simulated_path = initial_price + np.cumsum(daily_returns)
                    simulated_final_prices.append(simulated_path[-1])

                fig = ff.create_distplot([simulated_final_prices], group_labels=[f"{selected_company} Simulation"], show_hist=False, colors=['orange'], curve_type='kde')
                fig.update_layout(title=f"{selected_company} - Simulated Closing Price Distribution", title_font=dict(size=22, color='white', family='Arial'))
                st.plotly_chart(fig)

                # Portfolio Summary
                expected_price = np.mean(simulated_final_prices)
                final_value = expected_price * initial_portfolio
                change = final_value - initial_value

                st.markdown("### 💼 Portfolio Prediction Summary")
                st.write(f"**Expected Final Portfolio Value**: K`{final_value:.2f}`")
                st.write(f"**Change in Value**: K`{change:.2f}`")
            except Exception as e:
                logging.error(f"Error in portfolio simulation: {e}")
                st.error("There was an issue simulating the portfolio. Please try again.")
                return

        else:
            st.warning("Please upload a valid CSV file.")
    else:
        st.warning("🚨 Please upload a CSV file with `COMPANY` column and historical stock prices.")

# Function to generate a PDF summary (as it was previously)
def export_pdf_summary(temp, forecast, closing_prices, selected_company, logo_image):
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)

        # Save the logo image temporarily to disk
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
            logo_image.save(tmp.name, format="PNG")
            logo_path = tmp.name

        # Title Section
        pdf.set_font("Arial", 'B', 14)
        pdf.image(logo_path, x=10, y=8, w=30)  # Now uses the saved temp image
        pdf.cell(0, 10, f"Report Number: {np.random.randint(1000, 9999)}", align='R', ln=1)
        pdf.cell(0, 10, datetime.now().strftime('%A, %d %B %Y | %I:%M %p'), align='C', ln=1)
        pdf.ln(5)
        pdf.set_font("Arial", 'B', 18)
        pdf.set_text_color(220, 50, 50)  # Red-ish highlight color
        pdf.cell(0, 15, f"Lusaka Stock Exchange Portfolio Prediction", ln=1, align='C')
        pdf.set_font("Arial", 'B', 14)
        pdf.set_text_color(0, 0, 0)  # Reset to black
        pdf.cell(0, 10, f"Company: {selected_company}", ln=1, align='C')

        # Summary Table
        column_index = list(temp.columns).index(selected_company)
        last_price = temp.iloc[-1, column_index]
        expected_price = np.mean(closing_prices)
        final_value = expected_price * 1000
        change = final_value - (last_price * 1000)

        pdf.set_font("Arial", 'B', 12)
        pdf.cell(70, 10, "Metric", 1, 0, 'C', fill=True)
        pdf.cell(60, 10, "Value", 1, 0, 'C', fill=True)
        pdf.cell(50, 10, "Analysis", 1, 1, 'C', fill=True)

        # Table rows
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(70, 10, "Last Known Price", 1)
        pdf.cell(60, 10, f"K{last_price:.2f}", 1)
        pdf.cell(50, 10, "-", 1, 1)

        pdf.cell(70, 10, "Forecasted Avg. Price", 1)
        pdf.cell(60, 10, f"K{expected_price:.2f}", 1)
        pdf.cell(50, 10, "-", 1, 1)

        pdf.cell(70, 10, "Portfolio Value (x1000)", 1)
        pdf.cell(60, 10, f"K{final_value:.2f}", 1)
        pdf.cell(50, 10, "Positive" if change >= 0 else "Negative", 1, 1)

        pdf.cell(70, 10, "Expected Change", 1)
        pdf.cell(60, 10, f"K{change:.2f}", 1)
        pdf.cell(50, 10, "Positive" if change >= 0 else "Negative", 1, 1)

        # Footer
        pdf.set_y(-30)
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(0, 10, "DISCLAIMER: This is a simulation and does not guarantee future performance.", 0, 1, 'C')

        # Return the PDF as buffer
        buf = BytesIO()
        pdf.output(buf)
        buf.seek(0)
        return buf

    except Exception as e:
        logging.error(f"Error generating PDF: {e}")
        st.error("An error occurred while generating the PDF summary.")

# Run the app
if __name__ == "__main__":
    app()
