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
# DISEASE DETAILS
# =========================================================

disease_effects = {
    "Asthma": "Air pollution can trigger breathing difficulty, chest tightness, wheezing, and coughing.",
    "COPD": "Polluted air can worsen lung inflammation and reduce oxygen flow in the respiratory system.",
    "Lung Cancer": "Long-term exposure to pollutants increases the risk of abnormal lung cell growth.",
    "Pneumonia & Bronchitis": "Pollution can weaken respiratory immunity and increase lung infections.",
    "Heart Attacks": "Fine particulate matter can affect blood circulation and increase cardiovascular stress.",
    "Hypertension": "Air pollutants can elevate blood pressure and stress cardiovascular functions."
}

disease_precautions = {
    "Asthma": "Wear masks outdoors, avoid heavy traffic areas, and use air purifiers indoors.",
    "COPD": "Avoid smoking zones, monitor AQI daily, and limit outdoor exposure during poor air quality.",
    "Lung Cancer": "Reduce long-term exposure to toxic pollutants and maintain healthy indoor ventilation.",
    "Pneumonia & Bronchitis": "Stay hydrated, avoid polluted environments, and strengthen respiratory hygiene.",
    "Heart Attacks": "Reduce outdoor activity during poor AQI and maintain cardiovascular fitness.",
    "Hypertension": "Practice stress management and avoid exposure to highly polluted environments."
}

# =========================================================
# CUSTOM CSS
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

/* ================= HEADER ================= */

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
    font-size: 34px;
    font-weight: 800;
    color: #0f172a;
    margin-bottom: 20px;
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

/* ================= METRICS ================= */

[data-testid="metric-container"] {
    background: white;
    border: 1px solid #e2e8f0;
    padding: 18px;
    border-radius: 20px;
    box-shadow: 0 8px 24px rgba(15,23,42,0.04);
}

/* ================= MAP ================= */

iframe {
    border-radius: 22px !important;
    overflow: hidden !important;
}

/* ================= DISEASE CARDS ================= */

.disease-card {
    background: white;
    border-radius: 24px;
    padding: 22px;
    margin-bottom: 22px;
    border: 1px solid #e2e8f0;
    box-shadow: 0 10px 30px rgba(15,23,42,0.05);
}

.disease-title {
    font-size: 24px;
    font-weight: 800;
    color: #0f172a;
}

.disease-desc {
    color: #64748b;
    margin-top: 10px;
    line-height: 1.7;
    font-size: 15px;
}

.risk-high {
    background: #fee2e2;
    color: #dc2626;
    padding: 8px 14px;
    border-radius: 999px;
    font-size: 13px;
    font-weight: 700;
    display: inline-block;
}

.risk-low {
    background: #dcfce7;
    color: #16a34a;
    padding: 8px 14px;
    border-radius: 999px;
    font-size: 13px;
    font-weight: 700;
    display: inline-block;
}

/* ================= REMOVE BROKEN HTML VISUALS ================= */

code {
    white-space: pre-wrap !important;
}

pre {
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

        st.session_state.search_message = (
            f"✅ Successfully fetched {city}, {country}"
        )

    else:

        st.session_state.search_message = (
            "❌ Location not found."
        )

# =========================================================
# SIDEBAR SEARCH STATUS
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
# AQI + POLLUTANT CHARTS
# =========================================================

st.markdown("<br>", unsafe_allow_html=True)

left_col, right_col = st.columns(2)

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
            margin=dict(l=20, r=20, t=30, b=20)
        )

        st.plotly_chart(fig, use_container_width=True)

        st.success(
            f"AQI STATUS: {category} | Current AQI Value: {aqi_value:.2f}"
        )

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

    fig2.update_traces(textposition="outside")

    fig2.update_layout(
        height=520,
        template="plotly_white",
        showlegend=False
    )

    st.plotly_chart(fig2, use_container_width=True)

# =========================================================
# ENVIRONMENTAL CONDITIONS
# =========================================================

st.markdown("<br>", unsafe_allow_html=True)

st.markdown("""
<div class="section-title">
🌤 Environmental Conditions
</div>
""", unsafe_allow_html=True)

env1, env2, env3, env4 = st.columns(4)

with env1:
    st.metric(
        "🌡 Temperature",
        f"{features['Temperature']:.1f} °C"
    )

with env2:
    st.metric(
        "💧 Humidity",
        f"{features['Humidity']:.0f}%"
    )

with env3:
    st.metric(
        "🌬 Wind Speed",
        f"{features['Wind Speed']:.1f} m/s"
    )

with env4:
    st.metric(
        "📈 Pressure",
        f"{features['Pressure']:.0f} hPa"
    )

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
# DISEASE RISK PREDICTIONS
# =========================================================

# =========================================================
# DISEASE DATABASE
# =========================================================

disease_labels = {

    "Arrhythmia": ['CO', 'NO2'],
    "Asthma": ['PM2.5', 'PM10', 'NO2'],
    "COPD": ['PM2.5', 'PM10', 'SO2'],
    "Hypertension": ['NO2', 'SO2', 'CO'],
    "Heart Attacks": ['PM2.5', 'PM10', 'CO'],
    "Pneumonia and Bronchitis": ['PM2.5', 'PM10', 'SO2', 'CO'],
    "Eye and Skin Irritation": ['SO2', 'O3'],
    "Low Birth Weight": ['PM2.5', 'PM10', 'NO2'],
    "Preterm Births": ['PM2.5', 'PM10', 'NO2'],
    "Cognitive Impairment in Children": ['PM2.5', 'NO2'],
    "Reduced Lung Function in Children": ['PM2.5', 'NO2', 'O3']
}

# =========================================================
# EFFECTS
# =========================================================

disease_effects = {

    "Arrhythmia":
    "Irregular heartbeat triggered by environmental pollution and toxic gases.",

    "Asthma":
    "Inflammation of airways causing wheezing, coughing, and breathing difficulty.",

    "COPD":
    "Long-term lung disease causing airflow blockage and chronic breathing issues.",

    "Hypertension":
    "Persistent high blood pressure caused by pollution-related cardiovascular stress.",

    "Heart Attacks":
    "Reduced oxygen supply and cardiovascular strain increasing heart attack risk.",

    "Pneumonia and Bronchitis":
    "Respiratory infections causing mucus buildup, chest pain, and breathing discomfort.",

    "Eye and Skin Irritation":
    "Air pollutants causing redness, itching, irritation, and allergic reactions.",

    "Low Birth Weight":
    "Poor fetal development associated with prolonged pollution exposure during pregnancy.",

    "Preterm Births":
    "Increased risk of premature delivery due to environmental stress and pollutants.",

    "Cognitive Impairment in Children":
    "Reduced memory, learning ability, and concentration due to toxic air exposure.",

    "Reduced Lung Function in Children":
    "Impaired lung growth and breathing efficiency caused by polluted environments."
}

# =========================================================
# PRECAUTIONS
# =========================================================

disease_precautions = {

    "Arrhythmia":
    "Avoid toxic gases, monitor heart health, and reduce exposure during poor AQI.",

    "Asthma":
    "Wear masks outdoors and avoid high AQI regions.",

    "COPD":
    "Use inhalers and avoid prolonged outdoor exposure.",

    "Hypertension":
    "Monitor blood pressure regularly and reduce pollution exposure.",

    "Heart Attacks":
    "Avoid outdoor workouts during poor AQI and maintain cardiovascular health.",

    "Pneumonia and Bronchitis":
    "Maintain immunity, stay hydrated, and avoid respiratory irritants.",

    "Eye and Skin Irritation":
    "Use protective eyewear, wash exposed skin, and avoid polluted outdoor areas.",

    "Low Birth Weight":
    "Pregnant women should avoid polluted areas and maintain healthy prenatal care.",

    "Preterm Births":
    "Reduce exposure to smoke and industrial pollutants during pregnancy.",

    "Cognitive Impairment in Children":
    "Ensure clean indoor air and limit children's exposure to traffic pollution.",

    "Reduced Lung Function in Children":
    "Use air purifiers indoors and avoid outdoor activities during high AQI."
}

# =========================================================
# SECTION TITLE
# =========================================================

st.markdown(
    """
    <div class="section-title" style="margin-top:40px;">
        🩺 Health Risk Analysis
    </div>
    """,
    unsafe_allow_html=True
)

# =========================================================
# CSS
# =========================================================
st.markdown("""
<style>

.disease-card {
    background-color: white;
    border-radius: 22px;
    padding: 24px;
    margin-bottom: 22px;
    border: 1px solid #e2e8f0;
    box-shadow: 0 8px 24px rgba(15,23,42,0.06);
}

.disease-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 18px;
}

.disease-name {
    font-size: 24px;
    font-weight: 800;
    color: #0f172a;
}

.risk-high {
    background-color: #fee2e2;
    color: #dc2626;
    padding: 8px 16px;
    border-radius: 999px;
    font-weight: 700;
}

.risk-low {
    background-color: #dcfce7;
    color: #16a34a;
    padding: 8px 16px;
    border-radius: 999px;
    font-weight: 700;
}

.info-title {
    font-size: 16px;
    font-weight: 700;
    color: #0f172a;
    margin-top: 12px;
}

.info-text {
    color: #475569;
    line-height: 1.7;
    margin-top: 6px;
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# RENDER DISEASES
# =========================================================

for disease, feats in disease_labels.items():

    try:

        disease_input = []

        for feature_name in feats:

            if feature_name in features:
                disease_input.append(features[feature_name])

        if len(disease_input) == 0:
            continue

        result = predict_disease_with_explanation(
            disease_input,
            disease
        )

        if result is None:
            continue

        prediction = result.get("prediction", 0)

        risk = (
            "HIGH RISK"
            if prediction == 1
            else "LOW RISK"
        )

        risk_class = (
            "risk-high"
            if prediction == 1
            else "risk-low"
        )

        risk_icon = (
            "⚠️"
            if prediction == 1
            else "✅"
        )

        card_html = f"""
        <div class="disease-card">

            <div class="disease-header">

                <div class="disease-name">
                    {disease}
                </div>

                <div class="{risk_class}">
                    {risk_icon} {risk}
                </div>

            </div>

            <div class="info-title">
                Health Effects
            </div>

            <div class="info-text">
                {disease_effects.get(disease, "N/A")}
            </div>

            <div class="info-title">
                Precautions
            </div>

            <div class="info-text">
                {disease_precautions.get(disease, "N/A")}
            </div>

        </div>
        """

        st.markdown(card_html, unsafe_allow_html=True)

        with st.expander(f"🔍 Explainable AI Details — {disease}"):

            probability = result.get("probability")

            if probability is not None:
                st.write(
                    "Prediction Confidence:",
                    max(probability)
                )

            st.write(
                "Model Accuracy:",
                result.get("accuracy", "N/A")
            )

            st.write(
                "LIME Explanation:",
                result.get("lime_explanation", "N/A")
            )

            st.write(
                "SHAP Explanation:",
                result.get("shap_explanation", "N/A")
            )

    except Exception as e:

        st.error(f"Error rendering {disease}: {e}")