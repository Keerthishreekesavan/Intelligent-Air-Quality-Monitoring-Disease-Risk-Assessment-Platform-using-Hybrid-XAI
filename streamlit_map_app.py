import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
from models import predict_disease_with_explanation, predict_aqi
import os

# --- CONFIG ---
OPENWEATHER_API_KEY = st.secrets["OPENWEATHER_API_KEY"]
DEFAULT_LOCATION = (13.0827, 80.2707)  # Chennai

st.set_page_config(page_title="Air Quality & Disease Risk Map", layout="wide")

st.markdown("""
<style>
    /* Page background */
    .main, body { background: #f4f6f9 !important; }

    /* Remove default streamlit padding */
    .block-container { padding-top: 0 !important; padding-bottom: 0 !important; }

    /* Top nav bar */
    .topbar {
        background: #0072B5;
        padding: 14px 28px;
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 24px;
    }
    .topbar h1 {
        color: #fff;
        font-size: 20px;
        font-weight: 600;
        letter-spacing: 0.01em;
        margin: 0;
    }

    /* Panel cards */
    .panel {
        background: #fff;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        overflow: hidden;
        margin-bottom: 0;
    }
    .panel-head {
        padding: 12px 18px;
        border-bottom: 1px solid #e5e7eb;
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 13px;
        font-weight: 600;
        color: #0072B5;
    }

    /* Metric mini-cards */
    .metric-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 10px;
        margin-bottom: 16px;
    }
    .metric-card {
        background: #f8fafc;
        border-radius: 8px;
        padding: 10px 14px;
    }
    .metric-card .label {
        font-size: 11px;
        color: #6b7280;
        margin-bottom: 2px;
    }
    .metric-card .value {
        font-size: 20px;
        font-weight: 600;
        color: #111827;
    }

    /* AQI colour classes */
    .aqi-good    { color: #009966; font-weight: 700; }
    .aqi-fair    { color: #1e90ff; font-weight: 700; }
    .aqi-moderate{ color: #c9a800; font-weight: 700; }
    .aqi-poor    { color: #ff9933; font-weight: 700; }
    .aqi-verypoor{ color: #cc0033; font-weight: 700; }

    /* Risk badges */
    .risk-badge {
        display: inline-block;
        padding: 3px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        margin-left: 8px;
        vertical-align: middle;
    }
    .risk-high { background: #fde8e8; color: #b91c1c; border: 1px solid #fca5a5; }
    .risk-low  { background: #dcfce7; color: #166534; border: 1px solid #86efac; }

    /* Results section */
    .results-panel {
        background: #fff;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        overflow: hidden;
        margin-top: 20px;
    }
    .results-head {
        padding: 12px 18px;
        border-bottom: 1px solid #e5e7eb;
        font-size: 13px;
        font-weight: 600;
        color: #0072B5;
    }
    .results-body { padding: 16px 18px; }

    /* Empty state */
    .empty-state {
        text-align: center;
        padding: 32px 16px;
        color: #9ca3af;
        font-size: 13px;
    }

    /* How-to expander style */
    .streamlit-expanderHeader {
        background: #fff !important;
        border: 1px solid #e5e7eb !important;
        border-radius: 8px !important;
        font-size: 13px !important;
        color: #374151 !important;
        margin-bottom: 16px;
    }

    /* Primary button */
    .stButton > button {
        background: #0072B5 !important;
        color: #fff !important;
        font-weight: 600 !important;
        border-radius: 8px !important;
        border: none !important;
        width: 100%;
        padding: 10px 0 !important;
    }
    .stButton > button:hover { background: #005a91 !important; }

    /* Footer */
    .footer-wrap {
        margin-top: 32px;
        border-top: 1px solid #e5e7eb;
        padding-top: 20px;
        padding-bottom: 8px;
    }
    .footer-sub {
        font-size: 11px;
        color: #9ca3af;
        text-align: right;
        margin-top: 12px;
    }
</style>
""", unsafe_allow_html=True)

# --- Top bar ---
st.markdown("""
<div class='topbar'>
    <span style='font-size:22px;'>🌏</span>
    <h1>Air Quality & Disease Risk Map</h1>
</div>
""", unsafe_allow_html=True)

# --- How to use ---
with st.expander("ℹ️  How to use this tool", expanded=False):
    st.write("""
    1. Search for a city or click a location on the map.
    2. The air quality snapshot on the right auto-fills from live data.
    3. Click **Fetch Data & Predict** to see AQI and disease risk predictions.
    """)

# --- Helper functions ---
def aqi_category(aqi):
    if aqi < 2:   return "Good",     "aqi-good"
    elif aqi < 3: return "Fair",     "aqi-fair"
    elif aqi < 4: return "Moderate", "aqi-moderate"
    elif aqi < 5: return "Poor",     "aqi-poor"
    else:         return "Very Poor","aqi-verypoor"

def fetch_openweather_data(lat, lon):
    air_url     = f"https://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}"
    weather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric"
    air_resp     = requests.get(air_url)
    weather_resp = requests.get(weather_url)
    air_data     = air_resp.json()     if air_resp.status_code == 200     else None
    weather_data = weather_resp.json() if weather_resp.status_code == 200 else None
    return air_data, weather_data

def extract_features(air_data, weather_data):
    features = {
        'PM2.5': 10.0, 'PM10': 20.0, 'NO2': 10.0, 'SO2': 5.0,
        'CO': 0.5, 'O3': 15.0, 'NH3': 1.0, 'NO': 1.0,
        'Temperature': 25.0, 'Humidity': 50.0, 'Wind Speed': 2.0, 'Pressure': 1013.0
    }
    if air_data and "list" in air_data and air_data["list"]:
        comp = air_data["list"][0]["components"]
        for key, api_key in [('PM2.5','pm2_5'),('PM10','pm10'),('NO2','no2'),
                              ('SO2','so2'),('CO','co'),('O3','o3'),('NH3','nh3'),('NO','no')]:
            features[key] = comp.get(api_key, features[key])
    if weather_data and "main" in weather_data:
        features['Temperature'] = weather_data['main'].get('temp',     features['Temperature'])
        features['Humidity']    = weather_data['main'].get('humidity', features['Humidity'])
        features['Pressure']    = weather_data['main'].get('pressure', features['Pressure'])
    if weather_data and "wind" in weather_data:
        features['Wind Speed']  = weather_data['wind'].get('speed',    features['Wind Speed'])
    return features

# --- Disease data ---
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
disease_effects = {
    'Asthma': "Wheezing, breathlessness, chest tightness, and coughing. Severe attacks may need emergency care.",
    'COPD': "Long-term breathing problems, chronic cough, mucus, and frequent respiratory infections.",
    'Lung Cancer': "Persistent cough, chest pain, hoarseness, and weight loss.",
    'Pneumonia & Bronchitis': "Lung inflammation, cough, fever, and difficulty breathing.",
    'Reduced Lung Function in Children': "Developmental issues, increased asthma risk, reduced physical activity.",
    'Heart Attacks': "Chest pain, shortness of breath — can be fatal without immediate treatment.",
    'Hypertension': "Increased risk of heart disease, stroke, and kidney problems.",
    'Strokes': "Paralysis, speech difficulties, and long-term disability.",
    'Arrhythmia': "Palpitations, dizziness, and increased stroke risk.",
    "Alzheimer's & Dementia": "Memory loss, confusion, and behavioural changes.",
    "Parkinson's Disease": "Tremors, stiffness, and difficulty with movement.",
    "Cognitive Impairment in Children": "Affects learning, memory, and behaviour.",
    "Low Birth Weight": "Risk of infections, developmental delays, and chronic health issues.",
    "Preterm Births": "Breathing, heart, and developmental problems in premature babies.",
    "Sudden Infant Death Syndrome (SIDS)": "Sudden, unexplained death of a healthy baby, often during sleep.",
    "Bladder Cancer": "Blood in urine, pain, and frequent urination.",
    "Diabetes": "High blood sugar, fatigue, and complications affecting eyes, kidneys, and nerves.",
    "Eye & Skin Irritation": "Redness, itching, and discomfort in eyes and skin."
}
disease_precautions = {
    'Asthma': "Avoid outdoor activity on high-pollution days, use air purifiers, follow your asthma plan.",
    'COPD': "Quit smoking, avoid polluted areas, get regular vaccinations.",
    'Lung Cancer': "Avoid smoking and secondhand smoke, reduce pollutant exposure, get regular checkups.",
    'Pneumonia & Bronchitis': "Practice good hygiene, avoid sick contacts, get vaccinated.",
    'Reduced Lung Function in Children': "Limit outdoor activity on high-pollution days, use indoor air filters.",
    'Heart Attacks': "Maintain a healthy diet, exercise regularly, monitor blood pressure.",
    'Hypertension': "Reduce salt intake, exercise, manage stress.",
    'Strokes': "Control blood pressure, avoid smoking, maintain a healthy weight.",
    'Arrhythmia': "Avoid stimulants, manage stress, follow your doctor's advice.",
    "Alzheimer's & Dementia": "Regular mental and physical activity, maintain a healthy diet.",
    "Parkinson's Disease": "Exercise regularly and follow prescribed treatments.",
    "Cognitive Impairment in Children": "Encourage learning activities, minimise pollutant exposure.",
    "Low Birth Weight": "Good prenatal care, avoid smoke and pollution during pregnancy.",
    "Preterm Births": "Regular prenatal checkups, avoid stress and pollutants.",
    "Sudden Infant Death Syndrome (SIDS)": "Place babies on their backs to sleep, avoid soft bedding.",
    "Bladder Cancer": "Avoid smoking and industrial chemical exposure.",
    "Diabetes": "Healthy diet, exercise, monitor blood sugar.",
    "Eye & Skin Irritation": "Wear protective eyewear, avoid rubbing eyes, use gentle skin products."
}

# --- Session state ---
if 'map_center' not in st.session_state:
    st.session_state.map_center = DEFAULT_LOCATION
if 'marker' not in st.session_state:
    st.session_state.marker = DEFAULT_LOCATION
if 'features' not in st.session_state:
    st.session_state.features = None

# ── TWO-COLUMN LAYOUT ────────────────────────────────────────────────────────
left_col, right_col = st.columns([3, 2], gap="large")

# ── LEFT: Map panel ──────────────────────────────────────────────────────────
with left_col:
    st.markdown("<div class='panel'><div class='panel-head'>📍 Location</div>", unsafe_allow_html=True)

    search_col, btn_col = st.columns([4, 1])
    with search_col:
        search_query = st.text_input("", "Chennai", key="searchbar",
                                     placeholder="Search city or location",
                                     label_visibility="collapsed")
    with btn_col:
        search_btn = st.button("Search", key="searchbtn")

    if search_btn and search_query:
        geo_url  = f"http://api.openweathermap.org/geo/1.0/direct?q={search_query}&limit=1&appid={OPENWEATHER_API_KEY}"
        geo_resp = requests.get(geo_url)
        geo_data = geo_resp.json() if geo_resp.status_code == 200 else None
        if geo_data:
            loc = (geo_data[0]['lat'], geo_data[0]['lon'])
            st.session_state.map_center = loc
            st.session_state.marker     = loc
            st.success(f"Found: {geo_data[0]['name']}, {geo_data[0].get('country','')}")
        else:
            st.error("Location not found. Try another search.")

    m = folium.Map(location=st.session_state.map_center, zoom_start=7, control_scale=True)
    folium.Marker(
        location=st.session_state.marker,
        icon=folium.Icon(color='red', icon='info-sign'),
        popup="Selected Location"
    ).add_to(m)
    map_data = st_folium(m, width="100%", height=400, returned_objects=["last_clicked"])

    if map_data and map_data["last_clicked"]:
        lat = map_data["last_clicked"]["lat"]
        lon = map_data["last_clicked"]["lng"]
        st.session_state.marker     = (lat, lon)
        st.session_state.map_center = (lat, lon)
    else:
        lat, lon = st.session_state.marker

    st.markdown("</div>", unsafe_allow_html=True)

# ── RIGHT: Snapshot + Predict ────────────────────────────────────────────────
with right_col:
    st.markdown("<div class='panel'><div class='panel-head'>💨 Air quality snapshot</div>", unsafe_allow_html=True)

    feats = st.session_state.features
    pm25_val  = f"{feats['PM2.5']:.1f}"  if feats else "—"
    pm10_val  = f"{feats['PM10']:.1f}"   if feats else "—"
    no2_val   = f"{feats['NO2']:.1f}"    if feats else "—"
    temp_val  = f"{feats['Temperature']:.1f} °C" if feats else "—"

    st.markdown(f"""
    <div class='metric-grid' style='padding:14px 18px 0 18px;'>
        <div class='metric-card'><div class='label'>PM2.5 (μg/m³)</div><div class='value'>{pm25_val}</div></div>
        <div class='metric-card'><div class='label'>PM10 (μg/m³)</div><div class='value'>{pm10_val}</div></div>
        <div class='metric-card'><div class='label'>NO2 (μg/m³)</div><div class='value'>{no2_val}</div></div>
        <div class='metric-card'><div class='label'>Temperature</div><div class='value'>{temp_val}</div></div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='padding:0 18px 16px;'>", unsafe_allow_html=True)
    fetch_btn = st.button("⟳  Fetch Data & Predict", key="fetchbtn")
    st.markdown("</div></div>", unsafe_allow_html=True)

# ── RESULTS ──────────────────────────────────────────────────────────────────
st.markdown("<div class='results-panel'><div class='results-head'>📊 Prediction results</div><div class='results-body'>", unsafe_allow_html=True)

if fetch_btn or (map_data and map_data.get("last_clicked")):
    with st.spinner("Fetching data and running predictions..."):
        air_data, weather_data = fetch_openweather_data(lat, lon)
        features = extract_features(air_data, weather_data)
        st.session_state.features = features

    st.markdown("#### Fetched features (editable)")
    col1, col2 = st.columns(2)
    for i, k in enumerate(features.keys()):
        target = col1 if i < len(features) // 2 else col2
        features[k] = target.number_input(k, value=float(features[k]), key=f"feat_{k}")

    # AQI
    aqi_input  = [features[f] for f in ['PM2.5','PM10','NO2','SO2','CO','O3'] if f in features]
    aqi_result = predict_aqi(aqi_input)
    if aqi_result:
        aqi_value, lime_exp, shap_exp = aqi_result
        cat, cat_class = aqi_category(aqi_value)
        st.markdown(f"<p style='font-size:18px;margin:16px 0 8px;'>"
                    f"Predicted AQI: <span class='{cat_class}'>{aqi_value:.2f} ({cat})</span></p>",
                    unsafe_allow_html=True)
        with st.expander("AQI — explainable AI details"):
            st.write("LIME:", lime_exp or "N/A")
            st.write("SHAP:", shap_exp or "N/A")
    else:
        st.error("AQI prediction failed or model not available.")

    # Disease risk
    st.markdown("#### Disease risk prediction")
    for disease, feats_list in disease_labels.items():
        disease_input = [features[f] for f in feats_list if f in features]
        result = predict_disease_with_explanation(disease_input, disease)
        if result:
            high   = result['prediction'] == 1
            risk   = 'HIGH RISK' if high else 'LOW RISK'
            badge  = 'risk-high' if high else 'risk-low'
            icon   = '⚠️' if high else '✅'
            st.markdown(
                f"<div style='margin-bottom:4px'><b>{disease}</b>"
                f"<span class='risk-badge {badge}'>{icon} {risk}</span></div>",
                unsafe_allow_html=True
            )
            st.caption(f"**Effects:** {disease_effects.get(disease,'N/A')}")
            st.caption(f"**Precautions:** {disease_precautions.get(disease,'N/A')}")
            with st.expander(f"{disease} — AI details"):
                st.write(f"Confidence: {max(result['probability']):.3f}")
                st.write(f"Accuracy: {result['accuracy'] or 'N/A'}")
                st.write("LIME:", result.get('lime_explanation') or "N/A")
                st.write("SHAP:", result.get('shap_explanation') or "N/A")
                if result.get('risk_factors'):
                    st.write("Risk factors:")
                    for f in result['risk_factors'][:5]:
                        direction = "increases" if f['type'] == 'risk_increasing' else "decreases"
                        st.write(f"  - {f['feature']} {direction} risk (contribution: {f['contribution']:.4f})")
                if result.get('recommendations'):
                    st.write("Recommendations:")
                    for rec in result['recommendations']:
                        st.write(f"  - {rec}")
else:
    st.markdown("""
    <div class='empty-state'>
        🗺️<br><br>
        Search for a location or click the map,<br>then click <b>Fetch Data &amp; Predict</b> to see results.
    </div>
    """, unsafe_allow_html=True)

st.markdown("</div></div>", unsafe_allow_html=True)

# ── FOOTER (unchanged) ───────────────────────────────────────────────────────
st.markdown("<div class='footer-wrap'>", unsafe_allow_html=True)
st.markdown("---")

col1, col2 = st.columns([4, 1])
with col1:
    left1, left2 = st.columns([1, 4])
    with left1:
        st.image("tulip.jpg", width=90)
    with left2:
        st.markdown("""
        <h4 style='margin-bottom:0px;'>Created by Keerthishree Kesavan</h4>
        <p style='color:gray; font-size:18px; margin-top:0px;'>AI/ML Focused Full Stack Developer</p>
        """, unsafe_allow_html=True)
with col2:
    st.link_button("GitHub Profile", "https://github.com/Keerthishreekesavan")

st.markdown("---")
st.markdown("<p class='footer-sub'>Developed by Air Quality AI &nbsp;·&nbsp; Powered by OpenWeather &amp; Explainable AI</p>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)