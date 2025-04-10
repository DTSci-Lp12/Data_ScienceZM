import streamlit as st
from datetime import datetime

# Page Config
st.set_page_config(
    page_title="Annuity Value Calculator",
    page_icon="📊",
    layout="centered"
)

# Custom Soft Theme CSS
st.markdown("""
    <style>
        body {
            background-color: #ECF0F1;
        }
        .main {
            background-color: #F9F9F9;
            border-radius: 10px;
            padding: 2rem;
            box-shadow: 0 6px 20px rgba(0,0,0,0.08);
        }
        h1, h2, h3 {
            color: #2C3E50;
        }
        .stButton button {
            background-color: #2980B9;
            color: white;
            font-weight: 600;
            border-radius: 6px;
            padding: 0.5rem 1.2rem;
        }
        .stButton button:hover {
            background-color: #1A5276;
        }
        .stTextInput, .stNumberInput, .stDateInput {
            background-color: #f1f1f1;
        }
        .metric-label {
            color: #7F8C8D;
        }
    </style>
""", unsafe_allow_html=True)

# Main Container
st.markdown("<div class='main'>", unsafe_allow_html=True)

# Title and Date/Time
st.title("📊 Annuity Value Calculator")
st.caption("Calculate the present and future value of daily contributions with ease.")
st.markdown(f"🕒 **{datetime.now().strftime('%A, %d %B %Y | %I:%M %p')}**")

st.markdown("---")

# Input Section
st.subheader("🔧 Input Parameters")
col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("Start Date", datetime(2022, 1, 1))
with col2:
    end_date = st.date_input("End Date", datetime(2022, 12, 31))

col3, col4 = st.columns(2)
with col3:
    annual_contribution = st.number_input("Annual Contribution (ZMW)", min_value=0.0, value=12000.0, step=100.0)
with col4:
    nominal_rate = st.number_input("Annual Interest Rate (%)", min_value=0.0, value=12.0, step=0.1)

# Computation
if start_date < end_date:
    num_days = (end_date - start_date).days
    daily_payment = annual_contribution / num_days
    effective_daily_rate = (nominal_rate / 100) / num_days

    compounding_factors = [(1 + effective_daily_rate) ** i for i in reversed(range(num_days))]
    future_value = sum([daily_payment * f for f in compounding_factors])
    discounting_factors = [1 / f for f in compounding_factors]
    present_value = sum([daily_payment * f for f in discounting_factors])
    effective_return = (future_value / present_value) - 1
    total_gain = future_value - present_value

    st.markdown("---")
    st.subheader("📈 Results Summary")
    
    colA, colB = st.columns(2)
    colA.metric("Contribution Days", num_days)
    colB.metric("Daily Contribution", f"ZMW {daily_payment:.2f}")

    colC, colD = st.columns(2)
    colC.metric("Future Value", f"ZMW {future_value:,.2f}")
    colD.metric("Present Value", f"ZMW {present_value:,.2f}")

    colE, colF = st.columns(2)
    colE.metric("Interest Earned", f"ZMW {total_gain:,.2f}")
    colF.metric("Effective Annual Return", f"{effective_return * 100:.2f}%")
else:
    st.error("⚠️ Please ensure the start date is earlier than the end date.")

st.markdown("</div>", unsafe_allow_html=True)
