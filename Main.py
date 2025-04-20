import streamlit as st
import feedparser
from datetime import datetime
import pytz
import time
from PIL import Image, ImageDraw
import requests
import pandas as pd
from bs4 import BeautifulSoup
from itertools import islice
import re
import base64
from io import BytesIO

# --- Set timezone and get datetime ---
tz = pytz.timezone("Africa/Lusaka")
now = datetime.now(tz)
date_today = now.strftime("%d %B %Y")
time_now = now.strftime("%I:%M %p")
region = "Lusaka, Zambia"
current_year = now.year

# --- Page Config ---
st.set_page_config(
    page_title = "Yengo | Financial Analysis & Tools"
    page_icon="favicon-16x16.png",  # You can replace with an emoji or a link to a favicon image
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Load Logo & Process ---
logo_path = "Yengo_1.jpg"
image = Image.open(logo_path).convert("L").convert("RGBA")
min_side = min(image.size)
image = image.crop(((image.width - min_side) // 2, (image.height - min_side) // 2, 
                    (image.width + min_side) // 2, (image.height + min_side) // 2))

mask = Image.new('L', image.size, 0)
ImageDraw.Draw(mask).ellipse((0, 0, image.size[0], image.size[1]), fill=255)
image.putalpha(mask)

border_size = 10
border_image = Image.new('RGBA', (image.size[0] + border_size * 2, image.size[1] + border_size * 2), (255, 255, 255, 0))
border_mask = Image.new('L', border_image.size, 0)
ImageDraw.Draw(border_mask).ellipse((0, 0, border_image.size[0], border_image.size[1]), fill=255)
border_image.paste(image, (border_size, border_size), image)
border_image.putalpha(border_mask)

buffered = BytesIO()
border_image.save(buffered, format="PNG")
border_image_b64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

# --- CSS & Header ---
st.markdown(f"""
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&display=swap" rel="stylesheet">
<style>
    body {{
        font-family: 'Playfair Display', serif;
    }}
    .main {{
        background-image: url('https://static.vecteezy.com/system/resources/thumbnails/051/264/341/small_2x/black-and-white-of-a-lion-in-the-grass-photo.jpg');
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
        position: relative;
        padding: 60px 20px;
        border-radius: 12px;
        z-index: 1;
    }}
    .main::after {{
        content: '';
        position: absolute;
        top: 0; left: 0;
        width: 100%; height: 100%;
        background-color: rgba(0, 0, 0, 0.85);
        z-index: -1;
        border-radius: 12px;
    }}
    .custom-logo-bar {{
        width: 100%;
        background-color: red;
        display: flex;
        justify-content: center;
        align-items: center;
        padding: 10px 0;
        z-index: 999;
        position: fixed;
        top: 0;
        left: 0;
    }}
    .custom-logo-bar img {{
        height: 50px;
    }}
    .block-container {{
        padding-top: 90px !important;
    }}
    .header-text {{
        text-align: center;
        font-size: 30px;
        color: #FF5722;
        font-weight: 700;
        margin-bottom: 10px;
    }}
    .date-region {{
        text-align: center;
        font-size: 16px;
        background-color: #222;
        color: white;
        padding: 12px;
        border-radius: 10px;
    }}
    .rss-feed {{
        font-size: 14px;
        color: #333;
        background-color: #f5f5f5;
        padding: 12px;
        border-radius: 8px;
        margin: 10px auto;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        border-left: 5px solid #FF5722;
        animation: fadeIn 1s ease-in;
    }}
    hr.red-line {{
        border: none;
        height: 2px;
        background-color: #FF4C4C;
        margin: 30px 0;
    }}
    .footer {{
        text-align: center;
        padding: 20px;
        font-size: 14px;
        background-color: rgba(38, 50, 56, 0.9);
        color: white;
        border-top: 5px solid #FF5722;
        margin-top: 50px;
    }}
</style>
<div class="custom-logo-bar">
    <img src="data:image/png;base64,{border_image_b64}" alt="Yengo Logo">
</div>
""", unsafe_allow_html=True)

# --- MAIN SECTION START ---
st.markdown("<div class='main'>", unsafe_allow_html=True)

# Header
st.markdown("<div class='header-text'>Yengo | Financial Analysis & Tools</div>", unsafe_allow_html=True)

# --- Sidebar Logo ---
logo_path = "Yengo_1.jpg"
image = Image.open(logo_path).convert("L").convert("RGBA")  # Convert to grayscale

# Crop to square
min_side = min(image.size)
image = image.crop((
    (image.width - min_side) // 2,
    (image.height - min_side) // 2,
    (image.width + min_side) // 2,
    (image.height + min_side) // 2
))

# Circle mask
mask = Image.new('L', image.size, 0)
draw = ImageDraw.Draw(mask)
draw.ellipse((0, 0, image.size[0], image.size[1]), fill=255)
image.putalpha(mask)

# Add white border
border_size = 10
border_image = Image.new('RGBA', (image.size[0] + border_size * 2, image.size[1] + border_size * 2), (255, 255, 255, 0))
border_mask = Image.new('L', border_image.size, 0)
border_draw = ImageDraw.Draw(border_mask)
border_draw.ellipse((0, 0, border_image.size[0], border_image.size[1]), fill=255)
border_image.paste(image, (border_size, border_size), image)
border_image.putalpha(border_mask)

# --- Convert image to base64 ---
buffered = BytesIO()
border_image.save(buffered, format="PNG")
border_image_b64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

@st.cache_data(ttl=1800)
def fetch_luse_top5_by_closing_price():
    url = "https://www.luse.co.zm/trading/market-data/"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return {"Error": "Failed to fetch data"}

    soup = BeautifulSoup(response.text, "html.parser")
    meta_tag = soup.find("meta", property="og:description")
    if not meta_tag or not meta_tag.get("content"):
        return {"Error": "Meta description not found or empty"}

    content = meta_tag["content"]

    # Clean up HTML entities and newlines
    content = content.replace("&hellip;", "").replace("Edit", "").strip()

    # Extract rows using regex
    pattern = re.compile(
        r"([A-Z]{2,10})\s+([A-Z0-9]{12})\s+([\d.]+)\s*(?:([\d.-]+)?)\s*(?:([\d,]+)?)\s*(?:([\d,.]+)?)\s*(?:([\d,.]+)?)"
    )

    stock_data = []
    for match in pattern.finditer(content):
        security, isin, price, change, trades, volume, value = match.groups()
        try:
            closing_price = float(price.replace(",", ""))
        except:
            continue

        stock_data.append({
            "Security": security,
            "ISIN": isin,
            "Closing Price (ZMW)": closing_price,
            "Price Change": change or "0",
            "Trades": trades or "0",
            "Volume Traded": volume or "0",
            "Value Traded (ZMW)": value or "0"
        })

    # Sort and return top 5 by closing price
    top5 = sorted(stock_data, key=lambda x: x["Closing Price (ZMW)"], reverse=True)[:5]
    return top5

def fetch_zambia_economic_indicators():
    indicators = {
        'NY.GDP.MKTP.CD': 'GDP (current US$)',
        'NY.GDP.PCAP.CD': 'GDP per capita (current US$)',
        'SL.UEM.TOTL.ZS': 'Unemployment rate (%)',
        'FP.CPI.TOTL.ZG': 'Inflation rate (%)',
        'GC.DOD.TOTL.GD.ZS': 'Total debt (% of GDP)'
    }

    data = {}
    for indicator_code, indicator_name in indicators.items():
        url = f"http://api.worldbank.org/v2/country/ZM/indicator/{indicator_code}?format=json&per_page=1"
        response = requests.get(url)
        if response.status_code == 200:
            json_data = response.json()
            try:
                value = json_data[1][0]['value']
                data[indicator_name] = value
            except (IndexError, TypeError):
                data[indicator_name] = None
        else:
            data[indicator_name] = None
    return data

@st.cache_data(ttl=1800)
def get_cached_economic_data():
    return fetch_zambia_economic_indicators()

# --- Sidebar ---
with st.sidebar:
    # Sidebar logo and slogan styling
    st.sidebar.markdown(f"""
        <style>
        .logo-bar {{
            background-color: #000000;
            border-radius: 20px;
            padding: 15px 20px;
            display: flex;
            align-items: center;
            justify-content: flex-start;
            margin-bottom: 30px;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
        }}
        .logo-bar img {{
            height: 50px;
            border-radius: 50%;
            margin-right: 20px;
            border: 3px solid #ECF0F1;
        }}
        .slogan {{
            color: white;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            text-align: left;
        }}
        .slogan .brand {{
            font-size: 20px;
            font-weight: 700;
            color: #F39C12;
            text-shadow: 2px 2px 5px rgba(0, 0, 0, 0.3);
        }}
        .slogan .tagline {{
            font-size: 14px;
            font-weight: 400;
            color: #ECF0F1;
            margin-top: 5px;
            letter-spacing: 0.5px;
            text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.2);
        }}
        </style>

        <div class="logo-bar">
            <img src="data:image/png;base64,{border_image_b64}" alt="Logo">
            <div class="slogan">
                <div class="tagline">"Only Serve, Only Service"</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("### 📌 Main Menu")
    selected = st.selectbox(
        "", 
        ["Amortization Mortgages", "Annuity Calculator", "Asset Liability Management", 
         "Investment Calculator", "Loss Reserving", "LUSE Portfolio Management"]
    )

    st.markdown("---")
    
    top5_stocks = fetch_luse_top5_by_closing_price()

    if isinstance(top5_stocks, dict) and "Error" in top5_stocks:
        st.error(top5_stocks["Error"])
    else:
        st.markdown("### 🏦 Lusaka Stock Exchange (LuSE) Live Market")
        current_index = int(time.time() // 45) % len(top5_stocks)
        stock = top5_stocks[current_index]
        st.markdown(f"""
        <div class="rss-feed",style='border-left: 5px solid #d62728; padding: 1rem; background-color: #f9f9f9; font-family: monospace;'>
            <h4>📈 {stock['Security']}</h4>
            <b>Closing Price: </b>{stock['Closing Price (ZMW)']} ZMW <br>
            <b>Price Change: </b>{stock['Price Change']} <br>
            <b>Volume Traded: </b>{stock['Volume Traded']} <br>
            <b>Value Traded: </b>{stock['Value Traded (ZMW)']} ZMW
        </div>
        """, unsafe_allow_html=True)
   # --- Economic Indicators Section ---
    st.markdown("### 📊 Zambia Economic Indicators")

    economic_data = get_cached_economic_data()

    if economic_data:
        indicators = [
            ("GDP (current US$)", economic_data.get('GDP (current US$)', 'N/A')),
            ("GDP per capita (current US$)", economic_data.get('GDP per capita (current US$)', 'N/A')),
            ("Unemployment rate (%)", economic_data.get('Unemployment rate (%)', 'N/A')),
            ("Inflation rate (%)", economic_data.get('Inflation rate (%)', 'N/A')),
            ("Total debt (% of GDP)", economic_data.get('Total debt (% of GDP)', 'N/A'))
        ]

        for indicator, value in indicators:
            st.markdown(f"""
            <div class="rss-feed", style="border-left: 5px solid #FF5722; padding: 1rem; background-color: #f9f9f9; font-family: monospace;">
                <strong>{indicator}:</strong> {value}
            </div>
            """, unsafe_allow_html=True)

    else:
        st.warning("Failed to fetch economic data.")

# --- RSS Feed Section ---
@st.cache_data(ttl=900)  # Cache for 15 minutes
def fetch_bloomberg_rss():
    rss_url = "https://feeds.bloomberg.com/markets/news.rss"
    return feedparser.parse(rss_url)

# 🔄 Load the feed
feed = fetch_bloomberg_rss()

# 📰 Section heading
st.markdown("©Yengo | Latest Market Highlights", unsafe_allow_html=True)

# 📌 Display top 3 entries
if feed.entries:
    for entry in feed.entries[:3]:
        st.markdown(f"""
            <div class="rss-feed",style="padding: 10px; border-left: 4px solid #f63366; background-color: #f9f9f9; margin-bottom: 10px; border-radius: 5px;">
                <strong>{entry.title}</strong><br>
                <a href="{entry.link}" target="_blank">Read more</a><br>
                <small><i>Published: {entry.published}</i></small>
            </div>
        """, unsafe_allow_html=True)
else:
    st.info("No news available at the moment. Please check back later.")
    

# --- Header ---
st.markdown("<div class='header-text'> Yengo | Financial Analysis & Tools</div>", unsafe_allow_html=True)

# --- Date/Time/Region ---
st.markdown(f"""
    <div class='date-region'>
        📅 <b>Date:</b> {date_today} | 🕒 <b>Time:</b> {time_now} | 🌍 <b>Region:</b> {region}
    </div>
    <hr class='red-line' />
""", unsafe_allow_html=True)

# --- Page Routing ---
if selected == "Amortization Mortgages":
    with st.spinner("Loading Amortization Mortgages..."):
        time.sleep(3)
    import Amortization_Mortages
    Amortization_Mortages.app()

elif selected == "Annuity Calculator":
    with st.spinner("Loading Annuity Calculator..."):
        time.sleep(3)
    import Annuity_Calculator
    Annuity_Calculator.app()

elif selected == "Asset Liability Management":
    with st.spinner("Loading Asset Liability Management..."):
        time.sleep(3)
    import Asset_Liability_Managment
    Asset_Liability_Managment.app()

elif selected == "Investment Calculator":
    with st.spinner("Loading Investment Calculator..."):
        time.sleep(3)
    import Investment_Calculator
    Investment_Calculator.app()

elif selected == "Loss Reserving":
    with st.spinner("Loading Loss Reserving..."):
        time.sleep(3)
    import Loss_Reserving
    Loss_Reserving.app()

elif selected == "LUSE Portfolio Management":
    with st.spinner("Loading LUSE Portfolio Management..."):
        time.sleep(3)
    import LUSE_Portfolio_Management
    LUSE_Portfolio_Management.app()

# --- Footer ---
st.markdown(f"""
    <hr class='red-line' />
    <div class="disclaimer">
        <strong>Legal Disclaimer:</strong><br>
        The financial tools and calculators provided on this platform are for educational and informational purposes only.
        They are not financial advice. Please consult a qualified professional for financial decisions.
    </div>
    <hr class='red-line' />
    <div class="footer">
        &copy; {current_year} Yengo. All Rights Reserved. | Lusaka, Zambia
    </div>
""", unsafe_allow_html=True)
