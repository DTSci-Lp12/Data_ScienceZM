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
# Image Processing
from PIL import Image, ImageDraw, ImageOps
import plotly.graph_objects as go
import plotly.figure_factory as ff
# Dark mode & custom styling
st.markdown("""
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
# App title and metadata
st.title("Yengo | Lusaka Stock Exchange (LUSE) Portfolio Management Effective portfolio management tool")
st.markdown("About the Author: Limbani Phiri brings a wealth of experience from his extensive career across the banking, insurance, and commerce industries. As the CEO of Yengo, he has played a pivotal role in the development and creation of the Yengo platform. His leadership and expertise have been instrumental in shaping the platform’s vision, ensuring its impact and success in the market.")
st.markdown(f"🕒 **{datetime.now().strftime('%A, %d %B %Y | %I:%M %p')}**")
st.markdown("<hr class='red-line' />", unsafe_allow_html=True)

# App introduction
st.markdown("""
Welcome to the **Lusaka Stock Exchange (LUSE) Portfolio Management Effective portfolio management tools for tracking and optimizing investments on the Lusaka Stock Exchange (LUSE).** application. 
This app allows you to upload data from the Lusaka Stock Exchange (LUSE) to perform stock price analysis, including:

- 📈 Time series forecasting of stock prices using ARIMA.
- 🔁 Simulated future movements based on historical data.
- 💼 Portfolio value predictions based on closing stock prices.

---

### 📌 Instructions:
1. **Download the template** below.
2. Fill it with your LUSE Stock Data.
3. Upload the CSV to run the analysis.

The file should have the following structure:
- `COMPANY`: Column with company names (e.g., Zanaco, MTN Zambia)
- `Dates`: Columns representing closing stock prices for each date
""")

# ---- 📄 CSV Template Download ----
def create_luse_template():
    template_data = {
        "COMPANY": ["Zanaco", "MTN Zambia"],
        "2021-10-01": [25.50, 15.20],
        "2021-10-02": [25.75, 15.50],
        "2021-10-03": [26.00, 15.80]
    }
    df_template = pd.DataFrame(template_data)
    buffer = BytesIO()
    df_template.to_csv(buffer, index=False)
    buffer.seek(0)
    return buffer

st.markdown("### 📥 Download LUSE Template")
st.markdown("Use this file as a starting point for your data:")
st.download_button(
    label="📄 Download Template CSV",
    data=create_luse_template(),
    file_name="LUSE_template.csv",
    mime="text/csv"
)

# ---- 🚀 Main App Logic ----
def app():
    # ---- 📂 File Uploader ----
    st.markdown("<hr class='red-line' />", unsafe_allow_html=True)
    uploaded_file = st.file_uploader("📁 Upload your LUSE Stock Data CSV file", type=["csv"])
    if uploaded_file is not None:
        # Load and clean data
        LUSE_Stock_Data = pd.read_csv(uploaded_file)
        LUSE_Stock_Data = LUSE_Stock_Data.fillna(0)
        # Clean company names to avoid trailing spaces or case mismatches
        LUSE_Stock_Data['COMPANY'] = LUSE_Stock_Data['COMPANY'].str.strip()

        st.markdown("<hr class='red-line' />", unsafe_allow_html=True)
        st.markdown("### 🔍 Preview of Uploaded Data")
        st.dataframe(LUSE_Stock_Data.head())
        st.markdown("<hr class='red-line' />", unsafe_allow_html=True)

        # Restructure for analysis
        temp = LUSE_Stock_Data.drop(columns=['COMPANY']).transpose()
        temp.columns = LUSE_Stock_Data['COMPANY'].values
        name = LUSE_Stock_Data['COMPANY'].values
        ModelData_Margins = np.diff(temp.values, axis=0)
        ModelData_Margins[ModelData_Margins == 0] = np.nan

        # Dynamic company selection
        selected_company = st.selectbox("📊 Select a company for analysis", options=list(temp.columns))
        i = np.where(name == selected_company)[0][0]
        st.markdown("<hr class='red-line' />", unsafe_allow_html=True)
        st.markdown(f"## 📊 Analysis for: `{selected_company}`")
        
        # ---- 📉 Plot Stock Prices ----
        fig = go.Figure()

        # Plot closing prices as a line chart
        fig.add_trace(go.Scatter(
            x=temp.index, 
            y=temp.iloc[:, i], 
            mode='lines', 
            name='Closing Price',
            line=dict(color='red', width=3)
        ))

        # Layout customization
        fig.update_layout(
            title=f"{selected_company} - Time Series of Closing Prices",
            title_font=dict(size=22, color='white', family='Arial'),
            xaxis_title="Days",
            yaxis_title="Price",
            plot_bgcolor='black',
            paper_bgcolor='black',
            font=dict(color='white', family='Arial'),
            xaxis=dict(
                showgrid=True, gridcolor='grey',
                showline=True, linecolor='grey', linewidth=2,
                ticks='outside', tickangle=45
            ),
            yaxis=dict(
                showgrid=True, gridcolor='grey',
                showline=True, linecolor='grey', linewidth=2
            ),
            legend=dict(
                font=dict(color='white'),
                bgcolor='rgba(0, 0, 0, 0.7)',
                bordercolor='grey', borderwidth=1
            ),
            hovermode='x',
            hoverlabel=dict(
                bgcolor="rgba(0, 0, 0, 0.8)",
                font_size=12,
                font_family="Arial",
                font_color="white"
            )
        )

        # Display in Streamlit
        st.plotly_chart(fig, use_container_width=True)

        # ---- 📊 Histogram of Margins ----
        fig = go.Figure()

        # Histogram for margins
        fig.add_trace(go.Histogram(
            x=ModelData_Margins[:, i],
            nbinsx=30,
            marker=dict(color='grey', line=dict(color='red', width=1.5)),
            opacity=0.75,
            name='Data Margins'
        ))

        # Layout customization
        fig.update_layout(
            title=f"{selected_company} - Data Margins Distribution",
            title_font=dict(size=22, color='white', family='Arial'),
            xaxis_title="Price Difference",
            yaxis_title="Frequency",
            plot_bgcolor='black',
            paper_bgcolor='black',
            font=dict(color='white', family='Arial'),
            xaxis=dict(
                showgrid=True, gridcolor='grey',
                showline=True, linecolor='grey', linewidth=2,
                ticks='outside'
            ),
            yaxis=dict(
                showgrid=True, gridcolor='grey',
                showline=True, linecolor='grey', linewidth=2
            ),
            hovermode='x',
            hoverlabel=dict(
                bgcolor="rgba(0, 0, 0, 0.85)",
                font_size=12,
                font_family="Arial",
                font_color="white"
            ),
            showlegend=False
        )

        # Display in Streamlit
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("<hr class='red-line' />", unsafe_allow_html=True)
        # ---- 🧪 T-Test ----
        t_stat, p_value = stats.ttest_1samp(temp.iloc[:, i], 23)
        st.markdown(f"### 🧪 T-test against value 23 for `{selected_company}`")
        st.write(f"**t-statistic** = `{t_stat:.3f}`, **p-value** = `{p_value:.3f}`")
        st.markdown("<hr class='red-line' />", unsafe_allow_html=True)
        # ---- 🔮 ARIMA Forecast ----
        st.markdown(f"### 🔮 ARIMA Model Forecast for `{selected_company}`")
        model = ARIMA(temp.iloc[:, i], order=(5, 1, 0))
        fit = model.fit()
        forecast = fit.forecast(steps=300)

        fig = go.Figure()

        # Plot the ARIMA forecast
        fig.add_trace(go.Scatter(
            x=list(range(len(forecast))),  # X-axis as future days (could be an index for future days)
            y=forecast, 
            mode='lines', 
            name='Forecast',
            line=dict(color='limegreen', width=3)
        ))

        # Customize the layout with a smooth, eye-pleasing dark theme
        fig.update_layout(
            title=f"ARIMA Forecast - {selected_company}",
            title_font=dict(size=22, color='white', family='Arial'),
            xaxis_title="Future Days",
            yaxis_title="Forecasted Price",
            plot_bgcolor='black',  # Background color of the plot area
            paper_bgcolor='black',  # Background color of the whole plot
            font=dict(color='white', family='Arial'),  # Font color and family
            xaxis=dict(
                showgrid=True, 
                gridcolor='grey', 
                tickangle=45,  # Angling the ticks for better visibility
                ticks='outside',  # Ticks outside for clarity
                showline=True, 
                linewidth=2, 
                linecolor='grey'
            ),
            yaxis=dict(
                showgrid=True, 
                gridcolor='grey', 
                showline=True, 
                linewidth=2, 
                linecolor='grey'
            ),
            legend=dict(
                font=dict(color='white'),  # Set legend text color to white
                bgcolor='rgba(0, 0, 0, 0.7)',  # Background color of the legend for better contrast
                bordercolor='grey',  # Border color for the legend
                borderwidth=1
            ),
            showlegend=True,
            hovermode='closest',  # Show closest hover values
            hoverlabel=dict(
                bgcolor="rgba(0, 0, 0, 0.8)",  # Background color for the hover box
                font_size=12,  # Font size of hover text
                font_family="Arial",  # Font family for hover text
                font_color="white"  # Font color for hover text
            )
        )

        # Show plot in Streamlit
        st.plotly_chart(fig, use_container_width=True)
        # ---- 📈 Simulated Portfolio ----
        initial_portfolio = 1000
        initial_price = temp.iloc[-1, i]
        initial_value = initial_portfolio * initial_price

        mean_margin = np.nanmean(ModelData_Margins[:, i])
        std_margin = np.nanstd(ModelData_Margins[:, i])

        # Simulate 10,000 future price paths over 300 days
        runs = 10000
        simulated_final_prices = []

        for _ in range(runs):
            daily_returns = np.random.normal(loc=mean_margin, scale=std_margin, size=300)
            simulated_path = initial_price + np.cumsum(daily_returns)
            simulated_final_prices.append(simulated_path[-1])

        # ---- 🧠 KDE Plot for Simulated Final Prices ----
        fig = ff.create_distplot(
            [simulated_final_prices],
            group_labels=[f"{selected_company} Simulation"],
            show_hist=False,
            colors=['orange'],
            curve_type='kde'
        )

        fig.update_layout(
            title=f"{selected_company} - Simulated Closing Price Distribution",
            title_font=dict(size=22, color='white', family='Arial'),
            xaxis_title="Simulated Final Closing Price",
            yaxis_title="Density",
            plot_bgcolor='black',
            paper_bgcolor='black',
            font=dict(color='white', family='Arial'),
            xaxis=dict(
                showgrid=True, gridcolor='grey',
                showline=True, linecolor='grey', linewidth=2,
                ticks='outside'
            ),
            yaxis=dict(
                showgrid=True, gridcolor='grey',
                showline=True, linecolor='grey', linewidth=2
            ),
            hovermode='x unified',
            hoverlabel=dict(
                bgcolor="rgba(0, 0, 0, 0.8)",
                font_size=12,
                font_family="Arial",
                font_color="white"
            ),
            showlegend=False
        )

        # Show chart
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("<hr class='red-line' />", unsafe_allow_html=True)
        # ---- 💼 Portfolio Summary ----
        expected_price = np.mean(simulated_final_prices)
        final_value = expected_price * initial_portfolio
        change = final_value - initial_value

        st.markdown("### 💼 Portfolio Prediction Summary")
        st.write(f"**Expected Final Portfolio Value**: K`{final_value:.2f}`")
        st.write(f"**Change in Value**: K`{change:.2f}`")
        st.markdown("<hr class='red-line' />", unsafe_allow_html=True)

        st.subheader("📤 Downloads")
        # PDF download button
        pdf_buffer = export_pdf_summary(temp, forecast,simulated_final_prices, selected_company, logo_image)
        if pdf_buffer:
            st.download_button(
                label="🧾 Download PDF Report",
                data=pdf_buffer,
                file_name=f"{selected_company}_report.pdf",
                mime="application/pdf"
            )
    else:
        st.warning("🚨 Please upload a CSV file with `COMPANY` column and historical stock prices.")

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

# Function to generate a PDF summary
def export_pdf_summary(temp, forecast, closing_prices, selected_company, logo_image):
    from fpdf import FPDF
    from datetime import datetime
    import tempfile

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

        pdf.ln(10)

        # === 🔍 Forecast Summary Table ===
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, f"Closing Price Summary for {selected_company}", ln=1)
        pdf.ln(5)

        column_index = list(temp.columns).index(selected_company)
        last_price = temp.iloc[-1, column_index]
        expected_price = np.mean(closing_prices)
        final_value = expected_price * 1000
        change = final_value - (last_price * 1000)
        # Determine analysis verdict
        verdict = "Positive" if change >= 0 else "Negative"


        # Table headers
        pdf.set_font("Arial", 'B', 12)
        pdf.set_fill_color(230, 230, 230)
        pdf.cell(70, 10, "Metric", 1, 0, 'C', fill=True)
        pdf.cell(60, 10, "Value", 1, 0, 'C', fill=True)
        pdf.cell(50, 10, "Analysis", 1, 1, 'C', fill=True)

        # Table rows with bolded contents
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(70, 10, "Last Known Price", 1)
        pdf.cell(60, 10, f"K{last_price:.2f}", 1)
        pdf.cell(50, 10, "-", 1, 1)

        pdf.cell(70, 10, "Forecasted Avg. Price", 1)
        pdf.cell(60, 10, f"K{expected_price:.2f}", 1)
        pdf.cell(50, 10, "-", 1, 1)

        pdf.cell(70, 10, "Portfolio Value (x1000)", 1)
        pdf.cell(60, 10, f"K{final_value:.2f}", 1)
        pdf.cell(50, 10, verdict, 1, 1)

        pdf.cell(70, 10, "Expected Change", 1)
        pdf.cell(60, 10, f"K{change:.2f}", 1)
        pdf.cell(50, 10, verdict, 1, 1)

        pdf.ln(10)



        # Footer
        pdf.set_y(-30)
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(0, 10, "DISCLAIMER: This is a simulation and does not constitute financial advice.", 0, 1, 'C')
        pdf.cell(0, 10, "© 2025 Limbani Phiri. All Rights Reserved.", 0, 1, 'C')

        return pdf.output(dest='S').encode('latin-1')

    except Exception as e:
        st.error(f"❌ PDF export failed: {e}")
        return None



# Run the app
if __name__ == "__main__":
    app()
