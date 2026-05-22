import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

from models import predict_disease_with_explanation, predict_aqi

# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="AirSense AI",
    page_icon="🌍",
    layout="wide"
)

OPENWEATHER_API_KEY = st.secrets["OPENWEATHER_API_KEY"]

DEFAULT_LOCATION = (13.0827, 80.2707)

# =========================================================
# SESSION STATE
# =========================================================

if "map_center" not in st.session_state:
    st.session_state.map_center = DEFAULT_LOCATION

if "marker" not in st.session_state:
    st.session_state.marker = DEFAULT_LOCATION

if "city_name" not in st.session_state:
    st.session_state.city_name = "Chennai"

if "search_message" not in st.session_state:
    st.session_state.search_message = ""

# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown("""
<style>

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.main {
    background: #f4f7fb;
}

.block-container {
    padding-top: 1rem;
    max-width: 1600px;
}

/* ================= SIDEBAR ================= */

section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #f8fbff 0%, #eef4ff 100%);
    border-right: 1px solid #dbeafe;
    width: 320px !important;
}

.sidebar-title {
    font-size: 36px;
    font-weight: 800;
    color: #2563eb;
    margin-bottom: 8px;
}

.sidebar-sub {
    color: #64748b;
    font-size: 15px;
    line-height: 1.5;
    margin-bottom: 35px;
}

/* ================= HEADINGS ================= */

.main-title {
    font-size: 64px;
    font-weight: 800;
    text-align: center;
    background: linear-gradient(90deg, #2563eb, #38bdf8);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0;
}

.sub-title {
    text-align: center;
    color: #64748b;
    font-size: 24px;
    margin-top: -10px;
    margin-bottom: 45px;
}

.section-title {
    font-size: 36px;
    font-weight: 800;
    color: #0f172a;
    margin-bottom: 18px;
}

/* ================= BUTTON ================= */

.stButton > button {
    width: 100%;
    height: 52px;
    border-radius: 14px;
    border: none;
    background: linear-gradient(90deg,#2563eb,#38bdf8);
    color: white;
    font-weight: 700;
    font-size: 16px;
    transition: 0.3s ease;
}

.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 20px rgba(37,99,235,0.25);
}

/* ================= INPUT ================= */

.stTextInput input {
    border-radius: 14px !important;
    height: 50px !important;
    border: 1px solid #dbeafe !important;
    font-size: 16px !important;
}

/* ================= CARD ================= */

.custom-card {
    background: white;
    padding: 24px;
    border-radius: 24px;
    border: 1px solid #e2e8f0;
    box-shadow: 0 10px 30px rgba(15,23,42,0.05);
    margin-bottom: 18px;
}

/* ================= METRICS ================= */

[data-testid="metric-container"] {
    background: white;
    border: 1px solid #e2e8f0;
    padding: 20px;
    border-radius: 20px;
    box-shadow: 0 10px 24px rgba(15,23,42,0.04);
}

/* ================= MAP ================= */

.st-emotion-cache-1kyxreq {
    justify-content: center;
}

iframe {
    border-radius: 20px !important;
}

/* ================= EXPANDER ================= */

.streamlit-expanderHeader {
    font-size: 16px;
    font-weight: 700;
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# HEADER
# =========================================================

st.markdown("""
<div class="main-title">
🌍 AirSense AI
</div>

<div class="sub-title">
AI-Powered Air Quality & Disease Risk Intelligence Platform
</div>
""", unsafe_allow_html=True)

# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.markdown("""
    <div class="sidebar-title">
        🌍 AirSense AI
    </div>

    <div class="sidebar-sub">
        Environmental Health Intelligence Platform
    </div>
    """, unsafe_allow_html=True)

    search_query = st.text_input(
        "Search Location",
        value=st.session_state.city_name
    )

    search_btn = st.button("🔍 Search Location")

# =========================================================
# AQI CATEGORY
# =========================================================

def aqi_category(aqi):

    if aqi < 2:
        return "Good"

    elif aqi < 3:
        return "Fair"

    elif aqi < 4:
        return "Moderate"

    elif aqi < 5:
        return "Poor"

    else:
        return "Very Poor"

# =========================================================
# FETCH OPENWEATHER DATA
# =========================================================

def fetch_openweather_data(lat, lon):

    air_url = (
        f"https://api.openweathermap.org/data/2.5/air_pollution?"
        f"lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}"
    )

    weather_url = (
        f"https://api.openweathermap.org/data/2.5/weather?"
        f"lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric"
    )

    air_resp = requests.get(air_url)
    weather_resp = requests.get(weather_url)

    air_data = air_resp.json()
    weather_data = weather_resp.json()

    return air_data, weather_data

# =========================================================
# EXTRACT FEATURES
# =========================================================

def extract_features(air_data, weather_data):

    comp = air_data["list"][0]["components"]

    features = {
        'PM2.5': comp.get('pm2_5', 0),
        'PM10': comp.get('pm10', 0),
        'NO2': comp.get('no2', 0),
        'SO2': comp.get('so2', 0),
        'CO': comp.get('co', 0),
        'O3': comp.get('o3', 0),
        'NH3': comp.get('nh3', 0),
        'NO': comp.get('no', 0),
        'Temperature': weather_data['main'].get('temp', 0),
        'Humidity': weather_data['main'].get('humidity', 0),
        'Wind Speed': weather_data['wind'].get('speed', 0),
        'Pressure': weather_data['main'].get('pressure', 0)
    }

    return features

# =========================================================
# SEARCH LOCATION
# =========================================================

if search_btn:

    geo_url = (
        f"http://api.openweathermap.org/geo/1.0/direct?"
        f"q={search_query}&limit=1&appid={OPENWEATHER_API_KEY}"
    )

    geo_resp = requests.get(geo_url)
    geo_data = geo_resp.json()

    if geo_data:

        lat = geo_data[0]["lat"]
        lon = geo_data[0]["lon"]

        city = geo_data[0]["name"]
        country = geo_data[0]["country"]

        st.session_state.map_center = (lat, lon)
        st.session_state.marker = (lat, lon)
        st.session_state.city_name = city

        st.session_state.search_message = (
            f"✅ Successfully fetched {city}, {country}"
        )

    else:

        st.session_state.search_message = (
            "❌ Location not found."
        )

# =========================================================
# SIDEBAR STATUS
# =========================================================

with st.sidebar:

    if st.session_state.search_message:

        st.success(st.session_state.search_message)

# =========================================================
# MAP SECTION
# =========================================================

st.markdown("""
<div class="section-title">
🗺️ Interactive Pollution Map
</div>
""", unsafe_allow_html=True)

m = folium.Map(
    location=st.session_state.map_center,
    zoom_start=5,

    # THIS RESTORES GREEN MAP
    tiles="OpenStreetMap",

    control_scale=True
)

folium.Marker(
    location=st.session_state.marker,
    popup=st.session_state.city_name,
    icon=folium.Icon(color="red")
).add_to(m)

map_data = st_folium(
    m,
    height=620,
    width=None,
    use_container_width=True,
    returned_objects=["last_clicked"]
)

if map_data and map_data["last_clicked"]:

    lat = map_data["last_clicked"]["lat"]
    lon = map_data["last_clicked"]["lng"]

    st.session_state.marker = (lat, lon)

lat, lon = st.session_state.marker

# =========================================================
# FETCH DATA
# =========================================================

air_data, weather_data = fetch_openweather_data(lat, lon)

features = extract_features(air_data, weather_data)

aqi_input = [
    features['PM2.5'],
    features['PM10'],
    features['NO2'],
    features['SO2'],
    features['CO'],
    features['O3']
]

aqi_result = predict_aqi(aqi_input)

# =========================================================
# AQI + POLLUTION CHART
# =========================================================

st.markdown("<br>", unsafe_allow_html=True)

left_col, right_col = st.columns([1, 1])

# =========================================================
# AQI SECTION
# =========================================================

with left_col:

    st.markdown("""
    <div class="section-title">
    📊 AQI Overview
    </div>
    """, unsafe_allow_html=True)

    if aqi_result:

        aqi_value, lime_exp, shap_exp = aqi_result

        category = aqi_category(aqi_value)

        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=aqi_value,

            gauge={
                'axis': {'range': [0, 6]},
                'bar': {'color': "#2563eb"},

                'steps': [
                    {'range': [0, 2], 'color': "#22c55e"},
                    {'range': [2, 3], 'color': "#eab308"},
                    {'range': [3, 4], 'color': "#fb923c"},
                    {'range': [4, 6], 'color': "#ef4444"},
                ],
            }
        ))

        fig.update_layout(
            height=350,
            margin=dict(l=20, r=20, t=40, b=20)
        )

        st.plotly_chart(fig, use_container_width=True)

        st.info(
            f"""
AQI STATUS: {category}

Current AQI Value: {aqi_value:.2f}
"""
        )

# =========================================================
# POLLUTANT CHART
# =========================================================

with right_col:

    st.markdown("""
    <div class="section-title">
    📈 Pollutant Analysis
    </div>
    """, unsafe_allow_html=True)

    pollutant_df = pd.DataFrame({
        "Pollutant": ["PM2.5", "PM10", "NO2", "SO2", "CO", "O3"],
        "Value": aqi_input
    })

    fig2 = px.bar(
        pollutant_df,
        x="Pollutant",
        y="Value",
        text="Value"
    )

    fig2.update_traces(
        textposition="outside"
    )

    fig2.update_layout(
        height=520,
        template="plotly_white",
        showlegend=False
    )

    st.plotly_chart(fig2, use_container_width=True)

# =========================================================
# ENVIRONMENTAL METRICS
# =========================================================

st.markdown("<br>", unsafe_allow_html=True)

st.markdown("""
<div class="section-title">
🌦️ Environmental Conditions
</div>
""", unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4)

cards = [
    ("🌡️ Temperature", f"{features['Temperature']} °C"),
    ("💧 Humidity", f"{features['Humidity']}%"),
    ("🌬️ Wind Speed", f"{features['Wind Speed']} m/s"),
    ("📈 Pressure", f"{features['Pressure']} hPa")
]

for col, item in zip([c1, c2, c3, c4], cards):

    with col:

        st.metric(
            label=item[0],
            value=item[1]
        )
# =========================
# ENVIRONMENTAL CONDITIONS
# =========================


st.markdown("""
<div class="section-title">
    🌤 Environmental Conditions
</div>
""", unsafe_allow_html=True)

# SMALLER + CLEANER FEATURE BOXES
feature_style = """
<style>
.feature-box {
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 18px;
    padding: 16px;
    margin-bottom: 15px;
    backdrop-filter: blur(10px);
    transition: 0.3s ease;
    box-shadow: 0 4px 14px rgba(0,0,0,0.12);
}

.feature-box:hover {
    transform: translateY(-2px);
    border: 1px solid rgba(0,255,255,0.25);
}

.feature-label {
    color: #9fb3c8;
    font-size: 13px;
    margin-bottom: 8px;
    font-weight: 500;
}

.feature-value {
    color: white;
    font-size: 22px;
    font-weight: 700;
}

.feature-unit {
    color: #6ee7ff;
    font-size: 13px;
    margin-left: 5px;
}
</style>
"""

st.markdown(feature_style, unsafe_allow_html=True)

# ENVIRONMENT CARDS
env1, env2, env3, env4 = st.columns(4)

with env1:
    st.markdown(f"""
    <div class="feature-box">
        <div class="feature-label">🌡 Temperature</div>
        <div class="feature-value">{features['Temperature']:.1f}
            <span class="feature-unit">°C</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

with env2:
    st.markdown(f"""
    <div class="feature-box">
        <div class="feature-label">💧 Humidity</div>
        <div class="feature-value">{features['Humidity']:.0f}
            <span class="feature-unit">%</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

with env3:
    st.markdown(f"""
    <div class="feature-box">
        <div class="feature-label">🌬 Wind Speed</div>
        <div class="feature-value">{features['Wind Speed']:.1f}
            <span class="feature-unit">m/s</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

with env4:
    st.markdown(f"""
    <div class="feature-box">
        <div class="feature-label">🧭 Pressure</div>
        <div class="feature-value">{features['Pressure']:.0f}
            <span class="feature-unit">hPa</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# =========================================================
# EDITABLE FEATURES
# =========================================================

st.markdown("<br>", unsafe_allow_html=True)

st.markdown("""
<div class="section-title">
⚙️ Editable Environmental Features
</div>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

feature_keys = list(features.keys())

for i, key in enumerate(feature_keys):

    if i % 3 == 0:
        features[key] = col1.number_input(
            key,
            value=float(features[key])
        )

    elif i % 3 == 1:
        features[key] = col2.number_input(
            key,
            value=float(features[key])
        )

    else:
        features[key] = col3.number_input(
            key,
            value=float(features[key])
        )

# =========================================================
# DISEASE PREDICTIONS
# =========================================================

st.markdown("""
<div class="section-title" style="margin-top:35px;">
    🩺 Disease Risk Analysis
</div>
""", unsafe_allow_html=True)

# REMOVE THOSE UGLY WHITE OVAL SEPARATORS
st.markdown("""
<style>
hr {
    display: none !important;
}

[data-testid="stExpander"] {
    border: none !important;
    box-shadow: none !important;
    background: transparent !important;
}

.disease-card {
    background: rgba(255,255,255,0.05);
    border-radius: 18px;
    padding: 18px;
    margin-bottom: 18px;
    border: 1px solid rgba(255,255,255,0.08);
    box-shadow: 0 4px 18px rgba(0,0,0,0.14);
}

.disease-title {
    color: white;
    font-size: 18px;
    font-weight: 700;
    margin-bottom: 10px;
}

.risk-high {
    background: rgba(255, 77, 77, 0.18);
    color: #ff6b6b;
    padding: 6px 14px;
    border-radius: 999px;
    font-size: 13px;
    font-weight: 700;
    display: inline-block;
}

.risk-low {
    background: rgba(0, 255, 170, 0.16);
    color: #00ffaa;
    padding: 6px 14px;
    border-radius: 999px;
    font-size: 13px;
    font-weight: 700;
    display: inline-block;
}

.effect-text {
    color: #c7d5e0;
    font-size: 14px;
    line-height: 1.7;
    margin-top: 12px;
}
</style>
""", unsafe_allow_html=True)

# SHOW EVERY DISEASE
for disease, feats in disease_labels.items():

    disease_input = [features[f] for f in feats if f in features]

    result = predict_disease_with_explanation(
        disease_input,
        disease
    )

    if result:

        risk = (
            "HIGH RISK"
            if result['prediction'] == 1
            else "LOW RISK"
        )

        risk_class = (
            "risk-high"
            if risk == "HIGH RISK"
            else "risk-low"
        )

        st.markdown(f"""
        <div class="disease-card">

            <div class="disease-title">
                {disease}
            </div>

            <div class="{risk_class}">
                {risk}
            </div>

            <div class="effect-text">
                <b>Health Effects:</b><br>
                {disease_effects.get(disease, "N/A")}
            </div>

            <div class="effect-text">
                <b>Precautions:</b><br>
                {disease_precautions.get(disease, "N/A")}
            </div>

        </div>
        """, unsafe_allow_html=True)

# =========================================================
# FOOTER
# =========================================================

st.markdown("<br><hr><br>", unsafe_allow_html=True)

footer_left, footer_right = st.columns([5, 1])

with footer_left:

    st.markdown("""
    ### Created by Keerthishree Kesavan

    AI/ML Focused Full Stack Developer
    """)

with footer_right:

    st.link_button(
        "GitHub",
        "https://github.com/Keerthishreekesavan"
    )