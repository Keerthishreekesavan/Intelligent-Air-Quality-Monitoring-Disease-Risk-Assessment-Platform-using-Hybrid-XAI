import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
import plotly.express as px
import plotly.graph_objects as go
from models import predict_disease_with_explanation, predict_aqi

# -----------------------------------------------------
# PAGE CONFIG
# -----------------------------------------------------

st.set_page_config(
    page_title="AirSense AI",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------------------------------
# CONFIG
# -----------------------------------------------------

OPENWEATHER_API_KEY = st.secrets["OPENWEATHER_API_KEY"]
DEFAULT_LOCATION = (13.0827, 80.2707)

# -----------------------------------------------------
# CUSTOM CSS
# -----------------------------------------------------

st.markdown("""
<style>

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.main {
    background: linear-gradient(135deg, #0f172a 0%, #111827 100%);
    color: white;
}

.block-container {
    max-width: 96%;
    padding-top: 1.5rem;
}

section[data-testid="stSidebar"] {
    background: #0b1220;
    border-right: 1px solid rgba(255,255,255,0.08);
}

.hero-card {
    background: rgba(255,255,255,0.05);
    backdrop-filter: blur(10px);
    border-radius: 24px;
    padding: 2rem;
    border: 1px solid rgba(255,255,255,0.08);
    margin-bottom: 1.5rem;
}

.metric-card {
    background: rgba(255,255,255,0.05);
    border-radius: 20px;
    padding: 1.2rem;
    border: 1px solid rgba(255,255,255,0.08);
    text-align: center;
}

.metric-title {
    color: #94a3b8;
    font-size: 0.95rem;
}

.metric-value {
    font-size: 2rem;
    font-weight: 700;
    color: white;
}

.metric-sub {
    color: #38bdf8;
}

.disease-card {
    background: rgba(255,255,255,0.05);
    border-radius: 20px;
    padding: 1rem;
    border-left: 5px solid #22c55e;
    margin-bottom: 1rem;
}

.high-risk {
    border-left: 5px solid #ef4444;
}

.glow-title {
    font-size: 3rem;
    font-weight: 800;
    color: #38bdf8;
}

.subtitle {
    color: #94a3b8;
}

.stButton>button {
    background: linear-gradient(90deg,#0284c7,#2563eb);
    color: white;
    border: none;
    border-radius: 12px;
    font-weight: 600;
}

</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------
# AQI CATEGORY
# -----------------------------------------------------

def aqi_category(aqi):
    if aqi < 50:
        return "Good"
    elif aqi < 100:
        return "Fair"
    elif aqi < 150:
        return "Moderate"
    elif aqi < 200:
        return "Poor"
    return "Very Poor"

# -----------------------------------------------------
# DISEASE LABELS
# -----------------------------------------------------

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

# -----------------------------------------------------
# API FETCH
# -----------------------------------------------------

def fetch_openweather_data(lat, lon):

    air_url = f"https://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}"

    weather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric"

    air_resp = requests.get(air_url)
    weather_resp = requests.get(weather_url)

    air_data = air_resp.json() if air_resp.status_code == 200 else None
    weather_data = weather_resp.json() if weather_resp.status_code == 200 else None

    return air_data, weather_data

# -----------------------------------------------------
# FEATURE EXTRACTION
# -----------------------------------------------------

def extract_features(air_data, weather_data):

    features = {
        'PM2.5': 10.0,
        'PM10': 20.0,
        'NO2': 10.0,
        'SO2': 5.0,
        'CO': 0.5,
        'O3': 15.0,
        'NH3': 1.0,
        'NO': 1.0,
        'Temperature': 25.0,
        'Humidity': 50.0,
        'Wind Speed': 2.0,
        'Pressure': 1013.0
    }

    if air_data and "list" in air_data:
        comp = air_data["list"][0]["components"]

        features['PM2.5'] = comp.get('pm2_5', 0)
        features['PM10'] = comp.get('pm10', 0)
        features['NO2'] = comp.get('no2', 0)
        features['SO2'] = comp.get('so2', 0)
        features['CO'] = comp.get('co', 0)
        features['O3'] = comp.get('o3', 0)
        features['NH3'] = comp.get('nh3', 0)
        features['NO'] = comp.get('no', 0)

    if weather_data:
        features['Temperature'] = weather_data['main'].get('temp', 25)
        features['Humidity'] = weather_data['main'].get('humidity', 50)
        features['Pressure'] = weather_data['main'].get('pressure', 1013)
        features['Wind Speed'] = weather_data['wind'].get('speed', 2)

    return features

# -----------------------------------------------------
# SESSION STATE
# -----------------------------------------------------

if 'map_center' not in st.session_state:
    st.session_state.map_center = DEFAULT_LOCATION

if 'marker' not in st.session_state:
    st.session_state.marker = DEFAULT_LOCATION

# -----------------------------------------------------
# SIDEBAR
# -----------------------------------------------------

with st.sidebar:

    st.markdown("# 🌍 AirSense AI")

    st.caption("Environmental Health Intelligence Platform")

    st.markdown("---")

    search_query = st.text_input(
        "Search Location",
        "Chennai"
    )

    search_btn = st.button("🔍 Search")

    if search_btn and search_query:

        geo_url = f"http://api.openweathermap.org/geo/1.0/direct?q={search_query}&limit=1&appid={OPENWEATHER_API_KEY}"

        geo_resp = requests.get(geo_url)

        geo_data = geo_resp.json()

        if geo_data:
            st.session_state.map_center = (
                geo_data[0]['lat'],
                geo_data[0]['lon']
            )

            st.session_state.marker = st.session_state.map_center

# -----------------------------------------------------
# HERO
# -----------------------------------------------------

st.markdown("""
<div class='hero-card'>
    <div class='glow-title'>🌍 AirSense AI</div>
    <div class='subtitle'>
        AI-Powered Air Quality & Disease Risk Intelligence Platform
    </div>
</div>
""", unsafe_allow_html=True)

# -----------------------------------------------------
# MAP
# -----------------------------------------------------

left, right = st.columns([2,1])

with left:

    st.markdown("## 🗺️ Interactive Pollution Map")

    m = folium.Map(
        location=st.session_state.map_center,
        zoom_start=7,
        tiles='CartoDB dark_matter'
    )

    folium.Marker(
        location=st.session_state.marker,
        popup='Selected Location'
    ).add_to(m)

    map_data = st_folium(
        m,
        height=600,
        use_container_width=True,
        returned_objects=['last_clicked']
    )

    if map_data and map_data['last_clicked']:
        lat = map_data['last_clicked']['lat']
        lon = map_data['last_clicked']['lng']

        st.session_state.marker = (lat, lon)
        st.session_state.map_center = (lat, lon)

    else:
        lat, lon = st.session_state.marker

with right:

    st.markdown("## 📊 AQI Gauge")

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

    if aqi_result:

        aqi_value, lime_exp, shap_exp = aqi_result

        gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=aqi_value,
            title={'text': "AQI"},
            gauge={
                'axis': {'range': [0, 300]},
                'steps': [
                    {'range': [0, 50], 'color': 'green'},
                    {'range': [50, 100], 'color': 'yellow'},
                    {'range': [100, 200], 'color': 'orange'},
                    {'range': [200, 300], 'color': 'red'}
                ]
            }
        ))

        gauge.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='white',
            height=300
        )

        st.plotly_chart(gauge, use_container_width=True)

        st.markdown(f"### AQI Status: {aqi_category(aqi_value)}")

        pollutants = {
            'PM2.5': features['PM2.5'],
            'PM10': features['PM10'],
            'NO2': features['NO2'],
            'SO2': features['SO2'],
            'CO': features['CO'],
            'O3': features['O3']
        }

        fig = px.bar(
            x=list(pollutants.keys()),
            y=list(pollutants.values()),
            title='Pollutant Levels'
        )

        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font_color='white'
        )

        st.plotly_chart(fig, use_container_width=True)

# -----------------------------------------------------
# TOP METRICS
# -----------------------------------------------------

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class='metric-card'>
        <div class='metric-title'>Temperature</div>
        <div class='metric-value'>{features['Temperature']}°C</div>
        <div class='metric-sub'>Weather</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class='metric-card'>
        <div class='metric-title'>Humidity</div>
        <div class='metric-value'>{features['Humidity']}%</div>
        <div class='metric-sub'>Air Moisture</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class='metric-card'>
        <div class='metric-title'>Wind Speed</div>
        <div class='metric-value'>{features['Wind Speed']}</div>
        <div class='metric-sub'>m/s</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class='metric-card'>
        <div class='metric-title'>Pressure</div>
        <div class='metric-value'>{features['Pressure']}</div>
        <div class='metric-sub'>hPa</div>
    </div>
    """, unsafe_allow_html=True)

# -----------------------------------------------------
# EDITABLE FEATURES
# -----------------------------------------------------

st.markdown("## ⚙️ Editable Environmental Features")

f1, f2 = st.columns(2)

feature_keys = list(features.keys())

for i, key in enumerate(feature_keys):

    if i < len(feature_keys)//2:
        features[key] = f1.number_input(
            key,
            value=float(features[key]),
            key=f'feat_{key}'
        )
    else:
        features[key] = f2.number_input(
            key,
            value=float(features[key]),
            key=f'feat_{key}'
        )

# -----------------------------------------------------
# TABS
# -----------------------------------------------------

risk_tab, xai_tab, rec_tab = st.tabs([
    '🩺 Disease Risks',
    '📈 Explainable AI',
    '🛡️ Recommendations'
])

# -----------------------------------------------------
# DISEASE RISKS
# -----------------------------------------------------

all_results = {}

with risk_tab:

    st.markdown("## Disease Risk Assessment")

    cols = st.columns(2)

    idx = 0

    for disease, feats in disease_labels.items():

        disease_input = [features[f] for f in feats if f in features]

        result = predict_disease_with_explanation(
            disease_input,
            disease
        )

        if result:

            all_results[disease] = result

            risk = 'HIGH RISK' if result['prediction'] == 1 else 'LOW RISK'

            card_class = 'disease-card high-risk' if risk == 'HIGH RISK' else 'disease-card'

            emoji = '⚠️' if risk == 'HIGH RISK' else '✅'

            with cols[idx % 2]:

                st.markdown(f"""
                <div class='{card_class}'>
                    <h3>{emoji} {disease}</h3>
                    <h2>{risk}</h2>
                    <p>Confidence: {max(result['probability']):.2f}</p>
                </div>
                """, unsafe_allow_html=True)

                with st.expander(f'View {disease} Details'):

                    st.write('### LIME Explanation')
                    st.write(result.get('lime_explanation'))

                    st.write('### SHAP Explanation')
                    st.write(result.get('shap_explanation'))

                    st.write('### Risk Factors')

                    if result.get('risk_factors'):
                        for factor in result['risk_factors'][:5]:
                            st.write(
                                f"- {factor['feature']} : {factor['contribution']:.4f}"
                            )

                    st.write('### Recommendations')

                    if result.get('recommendations'):
                        for rec in result['recommendations']:
                            st.write(f'- {rec}')

            idx += 1

# -----------------------------------------------------
# XAI TAB
# -----------------------------------------------------

with xai_tab:

    st.markdown('## Explainable AI Insights')

    impact_data = {
        'Feature': ['PM2.5', 'PM10', 'NO2', 'SO2', 'CO', 'O3'],
        'Impact': [
            features['PM2.5'],
            features['PM10'],
            features['NO2'],
            features['SO2'],
            features['CO'],
            features['O3']
        ]
    }

    fig2 = px.bar(
        impact_data,
        x='Feature',
        y='Impact',
        title='Environmental Impact Analysis'
    )

    fig2.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font_color='white'
    )

    st.plotly_chart(fig2, use_container_width=True)

    if aqi_result:
        with st.expander('AQI Explainability'):
            st.write('### LIME')
            st.write(lime_exp)

            st.write('### SHAP')
            st.write(shap_exp)

# -----------------------------------------------------
# RECOMMENDATIONS TAB
# -----------------------------------------------------

with rec_tab:

    st.markdown('## Health Recommendations')

    st.success('Use N95 masks during high pollution periods.')

    st.warning('Avoid outdoor activities during peak traffic hours.')

    st.info('Use indoor air purifiers if AQI remains elevated.')

    st.error('Sensitive groups should minimize outdoor exposure.')

# -----------------------------------------------------
# FOOTER
# -----------------------------------------------------

st.markdown('---')

footer1, footer2 = st.columns([4,1])

with footer1:

    left1, left2 = st.columns([1,4])

    with left1:
        st.image('tulip.jpg', width=90)

    with left2:

        st.markdown("""
        <h2 style='margin-bottom:0;'>
            Created by Keerthishree Kesavan
        </h2>

        <p style='color:gray;'>
            AI/ML Focused Full Stack Developer
        </p>
        """, unsafe_allow_html=True)

with footer2:

    st.link_button(
        'GitHub Profile',
        'https://github.com/Keerthishreekesavan'
    )

st.markdown('---')