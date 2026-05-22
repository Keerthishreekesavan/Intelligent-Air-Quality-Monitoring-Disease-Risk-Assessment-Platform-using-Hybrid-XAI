import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

from models import predict_disease_with_explanation, predict_aqi

# =========================================================
# CONFIG
# =========================================================

st.set_page_config(
    page_title="AirSense AI",
    layout="wide"
)

OPENWEATHER_API_KEY = st.secrets["OPENWEATHER_API_KEY"]

DEFAULT_LOCATION = (13.0827, 80.2707)

# =========================================================
# STYLING
# =========================================================

st.markdown("""
<style>

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.block-container {
    padding-top: 1.5rem;
    padding-bottom: 1rem;
    max-width: 1450px;
}

.main {
    background-color: #f5f7fb;
}

section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #f8fbff 0%, #eef5ff 100%);
    border-right: 1px solid #dbeafe;
}

section[data-testid="stSidebar"] * {
    color: #111827 !important;
}

.sidebar-title {
    font-size: 34px;
    font-weight: 800;
    color: #2563eb;
    margin-bottom: 5px;
}

.sidebar-sub {
    color: #6b7280;
    font-size: 14px;
    margin-bottom: 35px;
}

.metric-card {
    background: white;
    padding: 22px;
    border-radius: 20px;
    border: 1px solid #e5e7eb;
    box-shadow: 0 4px 14px rgba(0,0,0,0.04);
    margin-bottom: 20px;
}

.metric-title {
    font-size: 15px;
    color: #6b7280;
    margin-bottom: 8px;
}

.metric-value {
    font-size: 34px;
    font-weight: 700;
    color: #111827;
}

.main-title {
    font-size: 54px;
    font-weight: 800;
    color: #38bdf8;
    text-align: center;
    margin-bottom: 0px;
}

.sub-title {
    text-align: center;
    color: #94a3b8;
    font-size: 24px;
    margin-top: -10px;
    margin-bottom: 40px;
}

.section-title {
    font-size: 38px;
    font-weight: 700;
    margin-bottom: 20px;
    color: #1e293b;
}

.risk-high {
    background: #fee2e2;
    color: #dc2626;
    padding: 8px 15px;
    border-radius: 12px;
    font-weight: 700;
}

.risk-low {
    background: #dcfce7;
    color: #16a34a;
    padding: 8px 15px;
    border-radius: 12px;
    font-weight: 700;
}

.stButton > button {
    width: 100%;
    border-radius: 12px;
    height: 50px;
    background: linear-gradient(90deg,#2563eb,#38bdf8);
    color: white;
    border: none;
    font-weight: 700;
    font-size: 16px;
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
        value="Chennai"
    )

    search_btn = st.button("🔍 Search")

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
# FETCH WEATHER
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

if "map_center" not in st.session_state:
    st.session_state.map_center = DEFAULT_LOCATION

if "marker" not in st.session_state:
    st.session_state.marker = DEFAULT_LOCATION

if search_btn:

    geo_url = (
        f"http://api.openweathermap.org/geo/1.0/direct?"
        f"q={search_query}&limit=1&appid={OPENWEATHER_API_KEY}"
    )

    geo_resp = requests.get(geo_url)
    geo_data = geo_resp.json()

    if geo_data:

        lat = geo_data[0]['lat']
        lon = geo_data[0]['lon']

        st.session_state.map_center = (lat, lon)
        st.session_state.marker = (lat, lon)

# =========================================================
# MAIN LAYOUT
# =========================================================

left, right = st.columns([2.1, 1])

# =========================================================
# MAP
# =========================================================

with left:

    st.markdown(
        "<div class='section-title'>🗺️ Interactive Pollution Map</div>",
        unsafe_allow_html=True
    )

    m = folium.Map(
        location=st.session_state.map_center,
        zoom_start=6,
        tiles="OpenStreetMap",
        control_scale=True
    )

    folium.Marker(
        location=st.session_state.marker,
        popup="Selected Location",
        icon=folium.Icon(color="red")
    ).add_to(m)

    map_data = st_folium(
        m,
        width=950,
        height=520,
        returned_objects=["last_clicked"]
    )

    if map_data["last_clicked"]:

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
# RIGHT PANEL
# =========================================================

with right:

    st.markdown(
        "<div class='section-title'>📊 AQI Dashboard</div>",
        unsafe_allow_html=True
    )

    if aqi_result:

        aqi_value, lime_exp, shap_exp = aqi_result

        cat = aqi_category(aqi_value)

        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=aqi_value,
            gauge={
                'axis': {'range': [0, 6]},
                'bar': {'color': "#2563eb"},
                'steps': [
                    {'range': [0, 2], 'color': "#22c55e"},
                    {'range': [2, 3], 'color': "#eab308"},
                    {'range': [3, 4], 'color': "#f97316"},
                    {'range': [4, 6], 'color': "#ef4444"},
                ],
            }
        ))

        fig.update_layout(height=300)

        st.plotly_chart(fig, use_container_width=True)

        st.markdown(f"""
        <div class="metric-card">

            <div class="metric-title">
                AQI STATUS
            </div>

            <div class="metric-value">
                {cat}
            </div>

            <div style='margin-top:10px;color:#6b7280;font-size:15px;'>
                AQI Value: {aqi_value:.2f}
            </div>

        </div>
        """, unsafe_allow_html=True)

        pollutant_df = pd.DataFrame({
            "Pollutant": ["PM2.5", "PM10", "NO2", "SO2", "CO", "O3"],
            "Value": aqi_input
        })

        fig2 = px.bar(
            pollutant_df,
            x="Pollutant",
            y="Value"
        )

        fig2.update_layout(
            height=350,
            template="plotly_white"
        )

        st.plotly_chart(fig2, use_container_width=True)

# =========================================================
# WEATHER CARDS
# =========================================================

st.markdown("<br>", unsafe_allow_html=True)

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

            <div class="metric-value" style="font-size:28px;">
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
# DISEASES
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

        risk = "HIGH RISK" if result["prediction"] == 1 else "LOW RISK"

        risk_class = "risk-high" if risk == "HIGH RISK" else "risk-low"

        with st.container():

            st.markdown(f"""
            <div class="metric-card">

                <div style="display:flex;justify-content:space-between;align-items:center;">

                    <div style="font-size:24px;font-weight:700;">
                        {disease}
                    </div>

                    <div class="{risk_class}">
                        {risk}
                    </div>

                </div>

            </div>
            """, unsafe_allow_html=True)

            with st.expander("Explainable AI Details"):

                st.write(
                    "Confidence:",
                    max(result["probability"])
                )

                st.write(
                    "Accuracy:",
                    result["accuracy"]
                )

                st.write(
                    "LIME:",
                    result.get("lime_explanation")
                )

                st.write(
                    "SHAP:",
                    result.get("shap_explanation")
                )

# =========================================================
# FOOTER
# =========================================================

st.markdown("<br><hr><br>", unsafe_allow_html=True)

f1, f2 = st.columns([4, 1])

with f1:

    left1, left2 = st.columns([1, 5])

    with left1:
        st.image("tulip.jpg", width=80)

    with left2:

        st.markdown("""
        <div style="font-size:28px;font-weight:700;">
            Created by Keerthishree Kesavan
        </div>

        <div style="color:#64748b;font-size:17px;">
            AI/ML Focused Full Stack Developer
        </div>
        """, unsafe_allow_html=True)

with f2:

    st.link_button(
        "GitHub",
        "https://github.com/Keerthishreekesavan"
    )

st.markdown("<br>", unsafe_allow_html=True)