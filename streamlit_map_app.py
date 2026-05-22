import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
from models import predict_disease_with_explanation, predict_aqi
import os
import base64

# --- CONFIG ---

OPENWEATHER_API_KEY = st.secrets["OPENWEATHER_API_KEY"]
DEFAULT_LOCATION = (13.0827, 80.2707)  # Chennai

st.set_page_config(page_title="Air Quality & Disease Risk Map", layout="wide")
st.markdown("""
<style>
    body, .main {
        background: linear-gradient(120deg, #f8fafc 0%, #e0e7ef 100%) !important;
    }
    .app-header {
        background: #0072B5;
        color: white;
        padding: 2rem 1rem 1rem 1rem;
        border-radius: 0 0 24px 24px;
        box-shadow: 0 4px 16px rgba(0,0,0,0.07);
        margin-bottom: 2rem;
        text-align: center;
    }
    .big-font {font-size: 1.3em; font-weight: bold;}
    .aqi-good {color: #009966; font-weight: bold;}
    .aqi-fair {color: #1e90ff; font-weight: bold;}
    .aqi-moderate {color: #ffde33; font-weight: bold;}
    .aqi-poor {color: #ff9933; font-weight: bold;}
    .aqi-verypoor {color: #cc0033; font-weight: bold;}
    .risk-badge {
        display: inline-block;
        padding: 0.25em 0.8em;
        border-radius: 16px;
        font-weight: 600;
        font-size: 1em;
        box-shadow: 0 2px 8px rgba(0,0,0,0.07);
        margin-left: 0.5em;
        vertical-align: middle;
    }
    .risk-high {
        background: #ff4d4f;
        color: #fff;
        border: 1px solid #ff7875;
    }
    .risk-low {
        background: #52c41a;
        color: #fff;
        border: 1px solid #b7eb8f;
    }
    .stButton>button {background-color: #0072B5; color: white; font-weight: bold; border-radius: 8px;}
    .help-btn {float: right; margin-top: -2.5rem; margin-right: 1rem;}
    .minimal-search input {
        border: none;
        border-radius: 24px;
        padding: 0.7em 1.2em;
        font-size: 1.1em;
        width: 100%;
        background: #fff;
        box-shadow: none;
        outline: none;
        margin-bottom: 0.5em;
    }
</style>
""", unsafe_allow_html=True)

# --- Stylish Header ---
st.markdown("""
<div class='app-header'>
    <h1 style='margin-bottom:0.2em; font-size:2.4em; font-weight:800; letter-spacing:-1px; display:flex; align-items:center; justify-content:center;'>
        <span style='font-size:1.3em; margin-right:0.4em;'>🌏</span> Air Quality & Disease Risk Map
    </h1>
</div>
""", unsafe_allow_html=True)

# --- Modern Divider ---
st.markdown("<hr style='height:3px; background:linear-gradient(90deg,#0072B5 0%,#52c41a 100%); border:none; border-radius:2px; margin:1.2em 0 1.8em 0;'>", unsafe_allow_html=True)

# --- Help/Info Button ---
with st.expander("ℹ️ How to use this tool", expanded=False):
    st.write("""
    1. Search for a city or click a location on the map to fetch real-time air quality and weather data.
    2. Review the auto-filled features. Adjust if needed.
    3. Click 'Fetch Data & Predict' to see AQI and disease risk.
    """)

# --- AQI Category Function ---
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

# --- Disease Definitions (should match models.py) ---
disease_labels = {
    'Asthma': ['PM2.5', 'PM10', 'NO2'],
    'COPD': ['PM2.5', 'PM10', 'SO2'],
    'Lung Cancer': ['PM2.5', 'PM10', 'NO2', 'O3'],
    'Pneumonia & Bronchitis': ['PM2.5', 'PM10', 'SO2', 'CO'],
    'Reduced Lung Function in Children': ['PM2.5', 'NO2', 'O3'],
    'Heart Attacks': ['PM2.5', 'PM10', 'CO'],
    'Hypertension': ['NO2', 'SO2', 'CO'],
    'Strokes': ['PM2.5', 'PM10', 'NO2'],
    'Arrhythmia': ['NO2', 'SO2', 'CO'],
    "Alzheimer's & Dementia": ['PM2.5', 'NO2'],
    "Parkinson's Disease": ['PM2.5', 'NO2', 'O3'],
    "Cognitive Impairment in Children": ['PM2.5', 'NO2'],
    "Low Birth Weight": ['PM2.5', 'PM10', 'NO2'],
    "Preterm Births": ['PM2.5', 'PM10', 'NO2'],
    "Sudden Infant Death Syndrome (SIDS)": ['PM2.5', 'PM10'],
    "Bladder Cancer": ['PM2.5', 'NO2', 'O3'],
    "Diabetes": ['PM2.5', 'NO2', 'SO2'],
    "Eye & Skin Irritation": ['SO2', 'O3']
}

# ... disease_effects and disease_precautions dicts unchanged ...
disease_effects = {
    'Asthma': "Asthma can cause wheezing, breathlessness, chest tightness, and coughing. Severe attacks may require emergency care.",
    'COPD': "COPD leads to long-term breathing problems and poor airflow. It can cause chronic cough, mucus, and frequent respiratory infections.",
    'Lung Cancer': "Lung cancer may cause persistent cough, chest pain, hoarseness, and weight loss. Early detection is critical.",
    'Pneumonia & Bronchitis': "These conditions cause lung inflammation, cough, fever, and difficulty breathing. Severe cases can be life-threatening.",
    'Reduced Lung Function in Children': "Can lead to developmental issues, increased risk of asthma, and reduced physical activity.",
    'Heart Attacks': "Heart attacks can cause chest pain, shortness of breath, and can be fatal if not treated immediately.",
    'Hypertension': "High blood pressure increases the risk of heart disease, stroke, and kidney problems.",
    'Strokes': "Strokes can cause paralysis, speech difficulties, and long-term disability.",
    'Arrhythmia': "Irregular heartbeat can lead to palpitations, dizziness, and increased risk of stroke.",
    "Alzheimer's & Dementia": "Can cause memory loss, confusion, and changes in behavior.",
    "Parkinson's Disease": "Leads to tremors, stiffness, and difficulty with movement and coordination.",
    "Cognitive Impairment in Children": "May affect learning, memory, and behavior.",
    "Low Birth Weight": "Increases risk of infections, developmental delays, and chronic health problems.",
    "Preterm Births": "Premature babies may have breathing, heart, and developmental problems.",
    "Sudden Infant Death Syndrome (SIDS)": "Sudden, unexplained death of a healthy baby, often during sleep.",
    "Bladder Cancer": "May cause blood in urine, pain, and frequent urination.",
    "Diabetes": "Can lead to high blood sugar, fatigue, and long-term complications affecting eyes, kidneys, and nerves.",
    "Eye & Skin Irritation": "Can cause redness, itching, and discomfort in eyes and skin."
}
disease_precautions = {
    'Asthma': "Avoid outdoor activities during high pollution days, use air purifiers, and follow your asthma action plan.",
    'COPD': "Quit smoking, avoid polluted areas, and get regular vaccinations.",
    'Lung Cancer': "Avoid smoking and secondhand smoke, reduce exposure to air pollutants, and get regular health checkups.",
    'Pneumonia & Bronchitis': "Practice good hygiene, avoid sick contacts, and get vaccinated.",
    'Reduced Lung Function in Children': "Limit children's outdoor activities on high pollution days and use indoor air filters.",
    'Heart Attacks': "Maintain a healthy diet, exercise regularly, and monitor blood pressure.",
    'Hypertension': "Reduce salt intake, exercise, and manage stress.",
    'Strokes': "Control blood pressure, avoid smoking, and maintain a healthy weight.",
    'Arrhythmia': "Avoid stimulants, manage stress, and follow your doctor's advice.",
    "Alzheimer's & Dementia": "Engage in regular mental and physical activity, and maintain a healthy diet.",
    "Parkinson's Disease": "Exercise regularly and follow prescribed treatments.",
    "Cognitive Impairment in Children": "Encourage learning activities and minimize exposure to pollutants.",
    "Low Birth Weight": "Ensure good prenatal care and avoid exposure to smoke and pollution during pregnancy.",
    "Preterm Births": "Attend regular prenatal checkups and avoid stress and pollutants.",
    "Sudden Infant Death Syndrome (SIDS)": "Place babies on their backs to sleep and avoid soft bedding.",
    "Bladder Cancer": "Avoid smoking and exposure to industrial chemicals.",
    "Diabetes": "Maintain a healthy diet, exercise, and monitor blood sugar.",
    "Eye & Skin Irritation": "Wear protective eyewear, avoid rubbing eyes, and use gentle skin care products."
}

# --- OpenWeather API ---
def fetch_openweather_data(lat, lon, api_key=OPENWEATHER_API_KEY):
    air_url = f"https://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={api_key}"
    weather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric"
    air_resp = requests.get(air_url)
    weather_resp = requests.get(weather_url)
    air_data = air_resp.json() if air_resp.status_code == 200 else None
    weather_data = weather_resp.json() if weather_resp.status_code == 200 else None
    return air_data, weather_data

def extract_features(air_data, weather_data):
    features = {
        'PM2.5': 10.0, 'PM10': 20.0, 'NO2': 10.0, 'SO2': 5.0, 'CO': 0.5, 'O3': 15.0,
        'NH3': 1.0, 'NO': 1.0, 'Temperature': 25.0, 'Humidity': 50.0, 'Wind Speed': 2.0, 'Pressure': 1013.0
    }
    if air_data and "list" in air_data and air_data["list"]:
        comp = air_data["list"][0]["components"]
        features['PM2.5'] = comp.get('pm2_5', features['PM2.5'])
        features['PM10'] = comp.get('pm10', features['PM10'])
        features['NO2'] = comp.get('no2', features['NO2'])
        features['SO2'] = comp.get('so2', features['SO2'])
        features['CO'] = comp.get('co', features['CO'])
        features['O3'] = comp.get('o3', features['O3'])
        features['NH3'] = comp.get('nh3', features['NH3'])
        features['NO'] = comp.get('no', features['NO'])
    if weather_data and "main" in weather_data:
        features['Temperature'] = weather_data['main'].get('temp', features['Temperature'])
        features['Humidity'] = weather_data['main'].get('humidity', features['Humidity'])
        features['Pressure'] = weather_data['main'].get('pressure', features['Pressure'])
    if weather_data and "wind" in weather_data:
        features['Wind Speed'] = weather_data['wind'].get('speed', features['Wind Speed'])
    return features

# --- Session State for Map Center and Marker ---
if 'map_center' not in st.session_state:
    st.session_state.map_center = DEFAULT_LOCATION
if 'marker' not in st.session_state:
    st.session_state.marker = DEFAULT_LOCATION

# --- Minimal Search Bar (no floating box) ---
st.markdown('<div class="minimal-search" style="max-width:600px;margin:0 auto 0.5em auto;">', unsafe_allow_html=True)
search_query = st.text_input("", "Chennai", key="searchbar", placeholder="Search for a city or location")
search_btn = st.button("🔍 Search", key="searchbtn")
search_latlon = None
if search_btn and search_query:
    geo_url = f"http://api.openweathermap.org/geo/1.0/direct?q={search_query}&limit=1&appid={OPENWEATHER_API_KEY}"
    geo_resp = requests.get(geo_url)
    geo_data = geo_resp.json() if geo_resp.status_code == 200 else None
    if geo_data and len(geo_data) > 0:
        search_latlon = (geo_data[0]['lat'], geo_data[0]['lon'])
        st.session_state.map_center = search_latlon
        st.session_state.marker = search_latlon
        st.success(f"Found: {geo_data[0]['name']}, {geo_data[0].get('country', '')}")
    else:
        st.error("Location not found. Try another search.")
st.markdown('</div>', unsafe_allow_html=True)

# --- Map UI ---
st.markdown('<div style="margin-bottom:1.5em;"></div>', unsafe_allow_html=True)
map_height = 550
map_width = 1600
m = folium.Map(location=st.session_state.map_center, zoom_start=7, control_scale=True)
folium.Marker(
    location=st.session_state.marker,
    icon=folium.Icon(color='red', icon='info-sign'),
    popup="Selected Location"
).add_to(m)
map_data = st_folium(m, width=map_width, height=map_height, returned_objects=["last_clicked"])

if map_data and map_data["last_clicked"]:
    lat = map_data["last_clicked"]["lat"]
    lon = map_data["last_clicked"]["lng"]
    st.session_state.marker = (lat, lon)
    st.session_state.map_center = (lat, lon)
else:
    lat, lon = st.session_state.marker

# --- Results (no white box, just clean display) ---
st.markdown("<h3 style='margin-top:2em; color:#0072B5; font-weight:700;'>Prediction Results</h3>", unsafe_allow_html=True)
if st.button("Fetch Data & Predict", type="primary", key="fetchbtn") or (map_data and map_data["last_clicked"]):
    with st.spinner("Fetching data and running predictions..."):
        air_data, weather_data = fetch_openweather_data(lat, lon)
        features = extract_features(air_data, weather_data)
        st.markdown("<h4 style='margin-top:1.2em; color:#222; font-weight:600;'>Fetched Features (editable):</h4>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        for i, k in enumerate(features.keys()):
            if i < len(features)//2:
                features[k] = col1.number_input(k, value=float(features[k]), key=f"feat_{k}")
            else:
                features[k] = col2.number_input(k, value=float(features[k]), key=f"feat_{k}")
        # AQI Prediction
        aqi_input = [features[f] for f in ['PM2.5', 'PM10', 'NO2', 'SO2', 'CO', 'O3'] if f in features]
        aqi_result = predict_aqi(aqi_input)
        if aqi_result is not None:
            aqi_value, lime_exp, shap_exp = aqi_result
            cat = aqi_category(aqi_value)
            cat_class = {
                "Good": "aqi-good",
                "Fair": "aqi-fair",
                "Moderate": "aqi-moderate",
                "Poor": "aqi-poor",
                "Very Poor": "aqi-verypoor"
            }[cat]
            st.markdown(f'<div class="big-font {cat_class}" style="margin-bottom:0.7em;">Predicted AQI: {aqi_value:.2f} ({cat})</div>', unsafe_allow_html=True)
            with st.expander("Show AQI Explainable AI Details"):
                st.write("LIME Explanation:", lime_exp or "N/A")
                st.write("SHAP Explanation:", shap_exp or "N/A")
        else:
            st.error("AQI prediction failed or model not available.")
        # Disease Prediction
        st.markdown("<h4 style='margin-top:1.5em; color:#222; font-weight:600;'>Disease Risk Prediction:</h4>", unsafe_allow_html=True)
        for disease, feats in disease_labels.items():
            disease_input = [features[f] for f in feats if f in features]
            result = predict_disease_with_explanation(disease_input, disease)
            if result:
                risk = 'HIGH RISK' if result['prediction'] == 1 else 'LOW RISK'
                risk_class = 'risk-high' if risk == 'HIGH RISK' else 'risk-low'
                risk_icon = '⚠️' if risk == 'HIGH RISK' else '✅'
                st.markdown(f"<div style='margin-bottom:0.5em'><b>{disease}</b>: <span class='risk-badge {risk_class}'>{risk_icon} {risk}</span></div>", unsafe_allow_html=True)
                st.write(f"**Possible Health Effects:** {disease_effects.get(disease, 'N/A')}")
                st.write(f"**Precautions:** {disease_precautions.get(disease, 'N/A')}")
                with st.expander("Show Explainable AI Details"):
                    st.write(f"Confidence: {max(result['probability']):.3f}")
                    st.write(f"Model Accuracy: {result['accuracy'] if result['accuracy'] is not None else 'N/A'}")
                    st.write("LIME Explanation:", result.get('lime_explanation') or "N/A")
                    st.write("SHAP Explanation:", result.get('shap_explanation') or "N/A")
                    st.write("Risk Factors:")
                    if result.get('risk_factors'):
                        for factor in result['risk_factors'][:5]:
                            risk_type = "INCREASES" if factor['type'] == 'risk_increasing' else "DECREASES"
                            st.write(f"- {factor['feature']} {risk_type} risk (contribution: {factor['contribution']:.4f})")
                    st.write("Recommendations:")
                    if result.get('recommendations'):
                        for rec in result['recommendations']:
                            st.write(f"- {rec}")
else:
    st.info("Search for a location or click on the map, then click 'Fetch Data & Predict' to see results.")

# --- Stylish Footer ---
st.markdown("<div class='footer'>Developed by Air Quality AI | Powered by OpenWeather & Explainable AI</div>", unsafe_allow_html=True) 

# LOAD IMAGE
import streamlit as st
import base64

st.markdown("---")

col1, col2 = st.columns([4,1])

with col1:
    left1, left2 = st.columns([1,4])

    with left1:
        st.image("tulip.jpg", width=90)

    with left2:
        st.markdown("""
        <h4 style='margin-bottom:0px;'>
        Keerthishree Kesavan
        </h4>

        <p style='color:gray; font-size:18px; margin-top:0px;'>
        AI/ML Focused Full Stack Developer
        </p>
        """, unsafe_allow_html=True)

with col2:
    st.link_button(
        "GitHub Profile",
        "https://github.com/Keerthishreekesavan"
    )

st.markdown("---")