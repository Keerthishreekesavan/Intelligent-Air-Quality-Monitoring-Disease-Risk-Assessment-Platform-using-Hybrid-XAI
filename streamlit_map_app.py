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

if "search_status" not in st.session_state:
    st.session_state.search_status = None

# =========================================================
# STYLING
# =========================================================

st.markdown("""
<style>

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

body {
    background: #f4f7fb;
}

.main {
    background-color: #f4f7fb;
}

.block-container {
    padding-top: 1.2rem;
    padding-bottom: 2rem;
    max-width: 1600px;
}

/* ================= SIDEBAR ================= */

section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #f8fbff 0%, #eef4ff 100%);
    border-right: 1px solid #dbeafe;
    width: 320px !important;
}

section[data-testid="stSidebar"] * {
    color: #111827 !important;
}

.sidebar-title {
    font-size: 38px;
    font-weight: 800;
    color: #2563eb;
    margin-bottom: 8px;
}

.sidebar-sub {
    color: #6b7280;
    font-size: 15px;
    margin-bottom: 35px;
    line-height: 1.5;
}

.search-success {
    background: #dcfce7;
    color: #166534;
    padding: 14px;
    border-radius: 14px;
    font-weight: 600;
    margin-top: 18px;
    border: 1px solid #bbf7d0;
}

.search-fail {
    background: #fee2e2;
    color: #b91c1c;
    padding: 14px;
    border-radius: 14px;
    font-weight: 600;
    margin-top: 18px;
    border: 1px solid #fecaca;
}

/* ================= HEADERS ================= */

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
    font-size: 38px;
    font-weight: 800;
    color: #0f172a;
    margin-bottom: 22px;
}

/* ================= CARDS ================= */

.metric-card {
    background: rgba(255,255,255,0.95);
    border-radius: 24px;
    padding: 24px;
    border: 1px solid #e2e8f0;
    box-shadow: 0 10px 30px rgba(15,23,42,0.05);
    backdrop-filter: blur(8px);
    transition: 0.3s ease;
    overflow: hidden;
}

.metric-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 18px 40px rgba(15,23,42,0.08);
}

.metric-title {
    font-size: 15px;
    color: #64748b;
    margin-bottom: 10px;
    font-weight: 600;
}

.metric-value {
    font-size: 34px;
    font-weight: 800;
    color: #0f172a;
}

.info-card {
    background: white;
    border-radius: 22px;
    padding: 20px;
    border: 1px solid #e2e8f0;
    box-shadow: 0 8px 24px rgba(15,23,42,0.05);
}

/* ================= MAP ================= */

.map-wrapper {
    background: white;
    border-radius: 26px;
    padding: 18px;
    border: 1px solid #e2e8f0;
    box-shadow: 0 12px 35px rgba(15,23,42,0.06);
    overflow: hidden;
}

[data-testid="stVerticalBlock"] iframe {
    border-radius: 20px !important;
}

/* ================= BUTTON ================= */

.stButton > button {
    width: 100%;
    height: 52px;
    border-radius: 14px;
    border: none;
    background: linear-gradient(90deg, #2563eb, #38bdf8);
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

/* ================= RISK TAGS ================= */

.risk-high {
    background: #fee2e2;
    color: #dc2626;
    padding: 10px 16px;
    border-radius: 999px;
    font-weight: 700;
}

.risk-low {
    background: #dcfce7;
    color: #16a34a;
    padding: 10px 16px;
    border-radius: 999px;
    font-weight: 700;
}

/* ================= EXPANDER ================= */

.streamlit-expanderHeader {
    font-weight: 700;
    font-size: 16px;
}

/* ================= HIDE RAW HTML CODE ================= */

code {
    white-space: pre-wrap !important;
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
# FETCH WEATHER DATA
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

        st.session_state.search_status = (
            f"✅ Successfully fetched {city}, {country}"
        )

    else:

        st.session_state.search_status = (
            "❌ Location not found. Please try another city."
        )

# =========================================================
# SIDEBAR STATUS
# =========================================================

with st.sidebar:

    if st.session_state.search_status:

        if "Successfully" in st.session_state.search_status:

            st.markdown(
                f"""
                <div class="search-success">
                    {st.session_state.search_status}
                </div>
                """,
                unsafe_allow_html=True
            )

        else:

            st.markdown(
                f"""
                <div class="search-fail">
                    {st.session_state.search_status}
                </div>
                """,
                unsafe_allow_html=True
            )

# =========================================================
# MAP SECTION
# =========================================================

st.markdown(
    """
    <div class='section-title'>
        🗺️ Interactive Pollution Map
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown('<div class="map-wrapper">', unsafe_allow_html=True)

m = folium.Map(
    location=st.session_state.map_center,
    zoom_start=5,
    tiles="CartoDB positron",
    control_scale=True
)

folium.Marker(
    location=st.session_state.marker,
    popup=st.session_state.city_name,
    icon=folium.Icon(color="red", icon="info-sign")
).add_to(m)

map_data = st_folium(
    m,
    width=None,
    height=620,
    returned_objects=["last_clicked"],
    use_container_width=True
)

st.markdown('</div>', unsafe_allow_html=True)

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
# AQI + CHART SECTION
# =========================================================

st.markdown("<br>", unsafe_allow_html=True)

left_col, right_col = st.columns([1, 1])

# =========================================================
# AQI GAUGE
# =========================================================

with left_col:

    st.markdown(
        "<div class='section-title'>📊 AQI Overview</div>",
        unsafe_allow_html=True
    )

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
            height=340,
            margin=dict(l=20, r=20, t=30, b=20)
        )

        st.plotly_chart(fig, use_container_width=True)

        st.markdown(f"""
        <div class="metric-card">

            <div class="metric-title">
                AQI STATUS
            </div>

            <div class="metric-value">
                {category}
            </div>

            <div style="margin-top:12px;color:#64748b;font-size:16px;">
                Current AQI Value: <b>{aqi_value:.2f}</b>
            </div>

        </div>
        """, unsafe_allow_html=True)

# =========================================================
# POLLUTANT CHART
# =========================================================

with right_col:

    st.markdown(
        "<div class='section-title'>📈 Pollutant Analysis</div>",
        unsafe_allow_html=True
    )

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
        showlegend=False,
        margin=dict(l=10, r=10, t=40, b=10)
    )

    st.plotly_chart(fig2, use_container_width=True)

# =========================================================
# WEATHER METRICS
# =========================================================

st.markdown("<br>", unsafe_allow_html=True)

st.markdown(
    "<div class='section-title'>🌦️ Environmental Conditions</div>",
    unsafe_allow_html=True
)

c1, c2, c3, c4 = st.columns(4)

cards = [
    ("🌡️ Temperature", f"{features['Temperature']} °C"),
    ("💧 Humidity", f"{features['Humidity']}%"),
    ("🌬️ Wind Speed", f"{features['Wind Speed']} m/s"),
    ("📈 Pressure", f"{features['Pressure']} hPa")
]

for col, item in zip([c1, c2, c3, c4], cards):

    with col:

        st.markdown(f"""
        <div class="metric-card">

            <div class="metric-title">
                {item[0]}
            </div>

            <div class="metric-value" style="font-size:30px;">
                {item[1]}
            </div>

        </div>
        """, unsafe_allow_html=True)

# =========================================================
# EDITABLE FEATURES
# =========================================================

st.markdown(
    "<div class='section-title'>⚙️ Editable Environmental Features</div>",
    unsafe_allow_html=True
)

col1, col2, col3 = st.columns(3)

feature_keys = list(features.keys())

for i, key in enumerate(feature_keys):

    if i % 3 == 0:
        features[key] = col1.number_input(key, value=float(features[key]))

    elif i % 3 == 1:
        features[key] = col2.number_input(key, value=float(features[key]))

    else:
        features[key] = col3.number_input(key, value=float(features[key]))

# =========================================================
# DISEASE PREDICTIONS
# =========================================================

disease_labels = {
    'Asthma': ['PM2.5', 'PM10', 'NO2'],
    'COPD': ['PM2.5', 'PM10', 'SO2'],
    'Lung Cancer': ['PM2.5', 'PM10', 'NO2', 'O3'],
    'Pneumonia & Bronchitis': ['PM2.5', 'PM10', 'SO2', 'CO'],
    'Heart Attacks': ['PM2.5', 'PM10', 'CO'],
    'Hypertension': ['NO2', 'SO2', 'CO'],
}

st.markdown(
    "<div class='section-title'>🩺 Disease Risk Predictions</div>",
    unsafe_allow_html=True
)

for disease, feats in disease_labels.items():

    disease_input = [features[f] for f in feats]

    result = predict_disease_with_explanation(
        disease_input,
        disease
    )

    if result:

        risk = (
            "HIGH RISK"
            if result["prediction"] == 1
            else "LOW RISK"
        )

        risk_class = (
            "risk-high"
            if risk == "HIGH RISK"
            else "risk-low"
        )

        st.markdown(f"""
        <div class="metric-card">

            <div style="
                display:flex;
                justify-content:space-between;
                align-items:center;
                margin-bottom:15px;
            ">

                <div style="
                    font-size:26px;
                    font-weight:800;
                    color:#0f172a;
                ">
                    {disease}
                </div>

                <div class="{risk_class}">
                    {risk}
                </div>

            </div>

            <div style="
                color:#64748b;
                font-size:15px;
                margin-top:5px;
            ">
                AI-driven respiratory health risk analysis
            </div>

        </div>
        """, unsafe_allow_html=True)

        with st.expander("🔍 Explainable AI Details"):

            st.write(
                "Prediction Confidence:",
                round(max(result["probability"]), 4)
            )

            st.write(
                "Model Accuracy:",
                result["accuracy"]
            )

            st.write(
                "LIME Explanation:",
                result.get("lime_explanation")
            )

            st.write(
                "SHAP Explanation:",
                result.get("shap_explanation")
            )

# =========================================================
# FOOTER
# =========================================================

st.markdown("<br><hr><br>", unsafe_allow_html=True)

f1, f2 = st.columns([5, 1])

with f1:

    st.markdown("""
    <div style="font-size:30px;font-weight:800;color:#0f172a;">
        Created by Keerthishree Kesavan
    </div>

    <div style="color:#64748b;font-size:17px;margin-top:4px;">
        AI/ML Focused Full Stack Developer
    </div>
    """, unsafe_allow_html=True)

with f2:

    st.link_button(
        "GitHub",
        "https://github.com/Keerthishreekesavan"
    )