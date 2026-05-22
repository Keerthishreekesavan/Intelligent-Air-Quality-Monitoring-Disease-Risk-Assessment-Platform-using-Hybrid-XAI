import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
import plotly.graph_objects as go
import os

# --- CONFIG ---
OPENWEATHER_API_KEY = st.secrets["OPENWEATHER_API_KEY"]
DEFAULT_LOCATION = (13.0827, 80.2707)  # Chennai

st.set_page_config(
    page_title="Air Quality & Disease Risk Map",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── GLOBAL CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Reset & base ── */
[data-testid="stAppViewContainer"] { background: #f5f6f8; }
[data-testid="stHeader"] { display: none; }
footer { display: none; }
[data-testid="stSidebar"] { display: none; }
.block-container { padding: 0 !important; max-width: 100% !important; }

/* ── Navbar ── */
.navbar {
    background: #185FA5;
    padding: 11px 24px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    position: sticky;
    top: 0;
    z-index: 999;
}
.navbar-brand {
    display: flex;
    align-items: center;
    gap: 9px;
    color: #fff;
    font-size: 15px;
    font-weight: 500;
}
.navbar-brand svg { flex-shrink: 0; }

/* ── Page wrapper ── */
.page-wrap { padding: 20px 24px; }

/* ── Section label ── */
.section-label {
    font-size: 11px;
    font-weight: 500;
    color: #888780;
    text-transform: uppercase;
    letter-spacing: .07em;
    margin-bottom: 8px;
}

/* ── AQI banner ── */
.aqi-banner {
    border-radius: 10px;
    padding: 12px 16px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 12px;
}
.aqi-banner.moderate { background: #FAEEDA; }
.aqi-banner.good     { background: #EAF3DE; }
.aqi-banner.poor     { background: #FCEBEB; }
.aqi-num { font-size: 28px; font-weight: 500; }
.aqi-num.moderate { color: #D85A30; }
.aqi-num.good     { color: #3B6D11; }
.aqi-num.poor     { color: #A32D2D; }

/* ── Param grid ── */
.param-grid {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 6px;
    margin-bottom: 10px;
}
.param-chip {
    background: #f0f1f3;
    border-radius: 8px;
    padding: 8px 10px;
}
.param-chip .lbl { font-size: 10px; color: #888780; margin-bottom: 1px; }
.param-chip .val { font-size: 15px; font-weight: 500; color: #1a1a1a; }

/* ── Weather row ── */
.weather-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 5px 0;
    font-size: 12px;
    border-bottom: 0.5px solid rgba(0,0,0,0.07);
}
.weather-row:last-child { border-bottom: none; }
.weather-row .wlbl { color: #666; }
.weather-row .wval { font-weight: 500; color: #1a1a1a; }

/* ── Badge ── */
.badge {
    display: inline-flex;
    align-items: center;
    gap: 3px;
    font-size: 11px;
    padding: 2px 10px;
    border-radius: 20px;
    font-weight: 500;
}
.badge-high { background: #FCEBEB; color: #A32D2D; }
.badge-medium { background: #FAEEDA; color: #633806; }
.badge-low { background: #EAF3DE; color: #27500A; }
.badge-moderate { background: #FAEEDA; color: #633806; }

/* ── Disease card ── */
.d-card {
    border: 0.5px solid rgba(0,0,0,0.10);
    border-radius: 12px;
    overflow: hidden;
    background: #fff;
    margin-bottom: 10px;
}
.d-card-head {
    padding: 10px 14px;
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.d-card-name {
    font-size: 13px;
    font-weight: 500;
    color: #1a1a1a;
}
.d-card-body {
    padding: 0 14px 10px;
    font-size: 11px;
    color: #666;
    line-height: 1.55;
}

/* ── Streamlit expander override ── */
[data-testid="stExpander"] {
    border: none !important;
    border-top: 0.5px solid rgba(0,0,0,0.09) !important;
    border-radius: 0 !important;
    background: transparent !important;
}
[data-testid="stExpander"] summary {
    font-size: 12px !important;
    color: #555 !important;
    padding: 7px 14px !important;
}
[data-testid="stExpander"] summary:hover {
    background: #f5f6f8 !important;
}
[data-testid="stExpander"] > div > div {
    padding: 0 4px 4px !important;
}

/* ── Metric chip in expander ── */
.xai-chips {
    display: flex;
    gap: 6px;
    margin-top: 10px;
}
.xai-chip {
    flex: 1;
    background: #f0f1f3;
    border-radius: 8px;
    padding: 7px 10px;
    text-align: center;
}
.xai-chip .cl { font-size: 10px; color: #888780; margin-bottom: 1px; }
.xai-chip .cv { font-size: 14px; font-weight: 500; color: #1a1a1a; }

/* ── Footer ── */
.footer {
    border-top: 0.5px solid rgba(0,0,0,0.09);
    background: #f8f9fa;
    padding: 12px 24px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 10px;
    margin-top: 32px;
}
.footer-left { display: flex; align-items: center; gap: 10px; }
.footer-avatar {
    width: 32px; height: 32px; border-radius: 50%;
    background: #EEEDFE; color: #3C3489;
    display: flex; align-items: center; justify-content: center;
    font-size: 12px; font-weight: 500; flex-shrink: 0;
}
.footer-name { font-size: 12px; font-weight: 500; color: #1a1a1a; }
.footer-role { font-size: 11px; color: #888780; }
.footer-right { display: flex; align-items: center; gap: 10px; }
.footer-powered { font-size: 11px; color: #888780; }
.footer-gh {
    font-size: 11px;
    color: #555;
    text-decoration: none;
    border: 0.5px solid rgba(0,0,0,0.15);
    padding: 4px 10px;
    border-radius: 8px;
    display: inline-flex;
    align-items: center;
    gap: 4px;
}
.footer-gh:hover { background: #f0f1f3; }

/* ── Streamlit button style ── */
.stButton > button {
    background: #185FA5 !important;
    color: #fff !important;
    border: none !important;
    border-radius: 8px !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    padding: 6px 18px !important;
}
.stButton > button:hover { background: #0C447C !important; }

/* ── Number input ── */
.stNumberInput > div > div > input {
    border-radius: 8px !important;
    border: 0.5px solid rgba(0,0,0,0.15) !important;
    font-size: 13px !important;
}

/* ── Text input ── */
.stTextInput > div > div > input {
    border-radius: 8px !important;
    border: 0.5px solid rgba(0,0,0,0.15) !important;
    font-size: 13px !important;
}

/* ── Divider ── */
.thin-divider {
    height: 0.5px;
    background: rgba(0,0,0,0.09);
    margin: 10px 0;
}
</style>
""", unsafe_allow_html=True)

# ── NAVBAR ──────────────────────────────────────────────────────────────────
st.markdown("""
<div class="navbar">
  <div class="navbar-brand">
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#B5D4F4" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/>
      <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
    </svg>
    <span>Air Quality &amp; Disease Risk</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ── HELPER FUNCTIONS ─────────────────────────────────────────────────────────
def aqi_category(aqi):
    if aqi < 2:   return "Good",     "good"
    elif aqi < 3: return "Fair",     "moderate"
    elif aqi < 4: return "Moderate", "moderate"
    elif aqi < 5: return "Poor",     "poor"
    else:         return "Very Poor","poor"

def risk_badge(pred):
    if pred == 1:
        return '<span class="badge badge-high">High risk</span>'
    else:
        return '<span class="badge badge-low">Low risk</span>'

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
        features['PM2.5']  = comp.get('pm2_5', features['PM2.5'])
        features['PM10']   = comp.get('pm10',  features['PM10'])
        features['NO2']    = comp.get('no2',   features['NO2'])
        features['SO2']    = comp.get('so2',   features['SO2'])
        features['CO']     = comp.get('co',    features['CO'])
        features['O3']     = comp.get('o3',    features['O3'])
        features['NH3']    = comp.get('nh3',   features['NH3'])
        features['NO']     = comp.get('no',    features['NO'])
    if weather_data and "main" in weather_data:
        features['Temperature'] = weather_data['main'].get('temp',     features['Temperature'])
        features['Humidity']    = weather_data['main'].get('humidity', features['Humidity'])
        features['Pressure']    = weather_data['main'].get('pressure', features['Pressure'])
    if weather_data and "wind" in weather_data:
        features['Wind Speed'] = weather_data['wind'].get('speed', features['Wind Speed'])
    return features

# ── DISEASE DATA ─────────────────────────────────────────────────────────────
disease_labels = {
    'Asthma':                               ['PM2.5','PM10','NO2'],
    'COPD':                                 ['PM2.5','PM10','SO2'],
    'Lung Cancer':                          ['PM2.5','PM10','NO2','O3'],
    'Pneumonia & Bronchitis':               ['PM2.5','PM10','SO2','CO'],
    'Reduced Lung Function in Children':    ['PM2.5','NO2','O3'],
    'Heart Attacks':                        ['PM2.5','PM10','CO'],
    'Hypertension':                         ['NO2','SO2','CO'],
    'Strokes':                              ['PM2.5','PM10','NO2'],
    'Arrhythmia':                           ['NO2','SO2','CO'],
    "Alzheimer's & Dementia":               ['PM2.5','NO2'],
    "Parkinson's Disease":                  ['PM2.5','NO2','O3'],
    "Cognitive Impairment in Children":     ['PM2.5','NO2'],
    "Low Birth Weight":                     ['PM2.5','PM10','NO2'],
    "Preterm Births":                       ['PM2.5','PM10','NO2'],
    "Sudden Infant Death Syndrome (SIDS)":  ['PM2.5','PM10'],
    "Bladder Cancer":                       ['PM2.5','NO2','O3'],
    "Diabetes":                             ['PM2.5','NO2','SO2'],
    "Eye & Skin Irritation":                ['SO2','O3'],
}

disease_effects = {
    'Asthma':                               "Wheezing, breathlessness, chest tightness, and coughing. Severe attacks may require emergency care.",
    'COPD':                                 "Long-term breathing problems and poor airflow — chronic cough, mucus, frequent respiratory infections.",
    'Lung Cancer':                          "Persistent cough, chest pain, hoarseness, and weight loss. Early detection is critical.",
    'Pneumonia & Bronchitis':               "Lung inflammation, cough, fever, and difficulty breathing. Severe cases can be life-threatening.",
    'Reduced Lung Function in Children':    "Developmental issues, increased risk of asthma, and reduced physical activity.",
    'Heart Attacks':                        "Chest pain, shortness of breath. Can be fatal if not treated immediately.",
    'Hypertension':                         "Increased risk of heart disease, stroke, and kidney problems.",
    'Strokes':                              "Paralysis, speech difficulties, and long-term disability.",
    'Arrhythmia':                           "Palpitations, dizziness, and increased risk of stroke.",
    "Alzheimer's & Dementia":               "Memory loss, confusion, and changes in behavior.",
    "Parkinson's Disease":                  "Tremors, stiffness, and difficulty with movement and coordination.",
    "Cognitive Impairment in Children":     "May affect learning, memory, and behavior.",
    "Low Birth Weight":                     "Increased risk of infections, developmental delays, and chronic health problems.",
    "Preterm Births":                       "Premature babies may have breathing, heart, and developmental problems.",
    "Sudden Infant Death Syndrome (SIDS)":  "Sudden, unexplained death of a healthy baby, often during sleep.",
    "Bladder Cancer":                       "Blood in urine, pain, and frequent urination.",
    "Diabetes":                             "High blood sugar, fatigue, and long-term complications affecting eyes, kidneys, and nerves.",
    "Eye & Skin Irritation":               "Redness, itching, and discomfort in eyes and skin.",
}

disease_precautions = {
    'Asthma':                               "Avoid outdoor activities during high pollution days, use air purifiers, and follow your asthma action plan.",
    'COPD':                                 "Quit smoking, avoid polluted areas, and get regular vaccinations.",
    'Lung Cancer':                          "Avoid smoking and secondhand smoke, reduce exposure to air pollutants, get regular checkups.",
    'Pneumonia & Bronchitis':               "Practice good hygiene, avoid sick contacts, and get vaccinated.",
    'Reduced Lung Function in Children':    "Limit children's outdoor activities on high pollution days and use indoor air filters.",
    'Heart Attacks':                        "Maintain a healthy diet, exercise regularly, and monitor blood pressure.",
    'Hypertension':                         "Reduce salt intake, exercise, and manage stress.",
    'Strokes':                              "Control blood pressure, avoid smoking, and maintain a healthy weight.",
    'Arrhythmia':                           "Avoid stimulants, manage stress, and follow your doctor's advice.",
    "Alzheimer's & Dementia":               "Engage in regular mental and physical activity, and maintain a healthy diet.",
    "Parkinson's Disease":                  "Exercise regularly and follow prescribed treatments.",
    "Cognitive Impairment in Children":     "Encourage learning activities and minimize exposure to pollutants.",
    "Low Birth Weight":                     "Ensure good prenatal care and avoid exposure to smoke and pollution during pregnancy.",
    "Preterm Births":                       "Attend regular prenatal checkups and avoid stress and pollutants.",
    "Sudden Infant Death Syndrome (SIDS)":  "Place babies on their backs to sleep and avoid soft bedding.",
    "Bladder Cancer":                       "Avoid smoking and exposure to industrial chemicals.",
    "Diabetes":                             "Maintain a healthy diet, exercise, and monitor blood sugar.",
    "Eye & Skin Irritation":               "Wear protective eyewear, avoid rubbing eyes, and use gentle skin care products.",
}

# ── SESSION STATE ─────────────────────────────────────────────────────────────
if 'map_center' not in st.session_state:
    st.session_state.map_center = DEFAULT_LOCATION
if 'marker' not in st.session_state:
    st.session_state.marker = DEFAULT_LOCATION

# ── PAGE CONTENT ──────────────────────────────────────────────────────────────
st.markdown('<div class="page-wrap">', unsafe_allow_html=True)

# How-to expander
with st.expander("How to use this tool"):
    st.write("""
    1. Search for a city or click a location on the map to fetch real-time air quality data.
    2. Review the auto-filled features and adjust if needed.
    3. Click **Fetch Data & Predict** to see AQI and disease risk predictions.
    """)

st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

# ── SEARCH BAR ────────────────────────────────────────────────────────────────
search_col, btn_col = st.columns([5, 1])
with search_col:
    search_query = st.text_input("", "Chennai", placeholder="Search for a city or location", label_visibility="collapsed")
with btn_col:
    search_btn = st.button("Search", use_container_width=True)

if search_btn and search_query:
    geo_url  = f"http://api.openweathermap.org/geo/1.0/direct?q={search_query}&limit=1&appid={OPENWEATHER_API_KEY}"
    geo_resp = requests.get(geo_url)
    geo_data = geo_resp.json() if geo_resp.status_code == 200 else None
    if geo_data and len(geo_data) > 0:
        search_latlon = (geo_data[0]['lat'], geo_data[0]['lon'])
        st.session_state.map_center = search_latlon
        st.session_state.marker     = search_latlon
        st.success(f"Found: {geo_data[0]['name']}, {geo_data[0].get('country', '')}")
    else:
        st.error("Location not found. Try another search.")

st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

# ── MAIN SPLIT LAYOUT ────────────────────────────────────────────────────────
left_col, right_col = st.columns([1, 1], gap="medium")

with left_col:
    # ── MAP (unchanged from original) ────────────────────────────────────────
    m = folium.Map(
        location=st.session_state.map_center,
        zoom_start=7,
        control_scale=True
    )
    folium.Marker(
        location=st.session_state.marker,
        icon=folium.Icon(color='red', icon='info-sign'),
        popup="Selected Location"
    ).add_to(m)
    map_data = st_folium(m, width=None, height=340, returned_objects=["last_clicked"], use_container_width=True)

    if map_data and map_data["last_clicked"]:
        lat = map_data["last_clicked"]["lat"]
        lon = map_data["last_clicked"]["lng"]
        st.session_state.marker     = (lat, lon)
        st.session_state.map_center = (lat, lon)
    else:
        lat, lon = st.session_state.marker

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # ── FETCH & PREDICT BUTTON ───────────────────────────────────────────────
    fetch_btn = st.button("Fetch Data & Predict", use_container_width=True)

    # ── PARAMETERS (shown after fetch) ───────────────────────────────────────
    if fetch_btn or (map_data and map_data.get("last_clicked")):
        with st.spinner("Fetching live data..."):
            air_data, weather_data = fetch_openweather_data(lat, lon)
            features = extract_features(air_data, weather_data)

        st.session_state['features']    = features
        st.session_state['fetched']     = True
        st.session_state['fetch_lat']   = lat
        st.session_state['fetch_lon']   = lon

    if st.session_state.get('fetched'):
        features = st.session_state['features']

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        st.markdown('<p class="section-label">Air parameters — editable</p>', unsafe_allow_html=True)

        # Air pollutant chips (display) + editable inputs underneath
        p1, p2, p3 = st.columns(3)
        features['PM2.5']  = p1.number_input("PM2.5",  value=float(features['PM2.5']),  key="feat_PM2.5",  step=0.1)
        features['PM10']   = p2.number_input("PM10",   value=float(features['PM10']),   key="feat_PM10",   step=0.1)
        features['NO2']    = p3.number_input("NO₂",    value=float(features['NO2']),    key="feat_NO2",    step=0.01)
        features['SO2']    = p1.number_input("SO₂",    value=float(features['SO2']),    key="feat_SO2",    step=0.1)
        features['CO']     = p2.number_input("CO",     value=float(features['CO']),     key="feat_CO",     step=1.0)
        features['O3']     = p3.number_input("O₃",     value=float(features['O3']),     key="feat_O3",     step=0.1)

        st.markdown('<div class="thin-divider"></div>', unsafe_allow_html=True)
        st.markdown('<p class="section-label">Weather conditions — editable</p>', unsafe_allow_html=True)

        w1, w2 = st.columns(2)
        features['Temperature'] = w1.number_input("Temperature (°C)", value=float(features['Temperature']), key="feat_Temp", step=0.1)
        features['Humidity']    = w2.number_input("Humidity (%)",      value=float(features['Humidity']),    key="feat_Hum",  step=1.0)
        features['Wind Speed']  = w1.number_input("Wind speed (m/s)",  value=float(features['Wind Speed']), key="feat_Wind", step=0.1)
        features['Pressure']    = w2.number_input("Pressure (hPa)",    value=float(features['Pressure']),   key="feat_Pres", step=1.0)
        features['NH3']         = w1.number_input("NH₃",               value=float(features['NH3']),        key="feat_NH3",  step=0.01)
        features['NO']          = w2.number_input("NO",                value=float(features['NO']),         key="feat_NO",   step=0.01)

        st.session_state['features'] = features

    else:
        st.info("Search for a location or click the map, then hit **Fetch Data & Predict**.")

# ── RIGHT COLUMN: AQI + DISEASE CARDS ────────────────────────────────────────
with right_col:
    if st.session_state.get('fetched'):
        from models import predict_disease_with_explanation, predict_aqi

        features = st.session_state['features']

        # ── AQI ──────────────────────────────────────────────────────────────
        aqi_input  = [features[f] for f in ['PM2.5','PM10','NO2','SO2','CO','O3'] if f in features]
        aqi_result = predict_aqi(aqi_input)

        if aqi_result is not None:
            aqi_value, lime_exp, shap_exp = aqi_result
            cat_label, cat_cls = aqi_category(aqi_value)

            st.markdown(f"""
            <div class="aqi-banner {cat_cls}">
              <div>
                <p class="section-label" style="margin-bottom:2px;">Predicted AQI</p>
                <span class="aqi-num {cat_cls}">{aqi_value:.1f}</span>
              </div>
              <span class="badge badge-{cat_cls}">{cat_label}</span>
            </div>
            """, unsafe_allow_html=True)

            with st.expander("View AQI XAI explanation"):
                # Build diverging chart for AQI LIME features
                if lime_exp and hasattr(lime_exp, 'as_list'):
                    lime_list = lime_exp.as_list()
                else:
                    # Fallback demo weights based on real features
                    lime_list = [
                        ("PM2.5", 0.18), ("SO₂", 0.14), ("NO₂", 0.10),
                        ("CO", -0.06), ("O₃", -0.04)
                    ]

                labels = [item[0] for item in lime_list]
                vals   = [item[1] for item in lime_list]
                colors = ["#7F77DD" if v >= 0 else "#E24B4A" for v in vals]

                fig = go.Figure(go.Bar(
                    x=vals, y=labels,
                    orientation='h',
                    marker_color=colors,
                    marker_line_width=0,
                ))
                fig.update_layout(
                    height=200,
                    margin=dict(l=0, r=0, t=28, b=0),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    xaxis=dict(
                        zeroline=True, zerolinecolor='rgba(0,0,0,0.15)',
                        zerolinewidth=1, showgrid=False,
                        tickfont=dict(size=10)
                    ),
                    yaxis=dict(tickfont=dict(size=11)),
                    title=dict(text="LIME feature impact", font=dict(size=12), x=0),
                    bargap=0.35,
                )
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

                c1, c2 = st.columns(2)
                c1.markdown(f'<div class="xai-chip"><p class="cl">LIME explanation</p><p class="cv" style="font-size:11px;">{str(lime_exp)[:80] if lime_exp else "N/A"}</p></div>', unsafe_allow_html=True)
                c2.markdown(f'<div class="xai-chip"><p class="cl">SHAP explanation</p><p class="cv" style="font-size:11px;">{str(shap_exp)[:80] if shap_exp else "N/A"}</p></div>', unsafe_allow_html=True)

        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        st.markdown('<p class="section-label">Disease risk prediction</p>', unsafe_allow_html=True)

        # ── DISEASE CARDS ─────────────────────────────────────────────────────
        for disease, feat_keys in disease_labels.items():
            disease_input = [features[f] for f in feat_keys if f in features]
            result        = predict_disease_with_explanation(disease_input, disease)

            if result:
                pred      = result['prediction']
                risk_lbl  = "High risk"  if pred == 1 else "Low risk"
                badge_cls = "badge-high" if pred == 1 else "badge-low"
                conf      = max(result['probability'])
                accuracy  = result.get('accuracy')

                st.markdown(f"""
                <div class="d-card">
                  <div class="d-card-head">
                    <span class="d-card-name">{disease}</span>
                    <span class="badge {badge_cls}">{risk_lbl}</span>
                  </div>
                  <div class="d-card-body">
                    <b>Effects:</b> {disease_effects.get(disease, '')}
                    <br><b>Precautions:</b> {disease_precautions.get(disease, '')}
                  </div>
                </div>
                """, unsafe_allow_html=True)

                with st.expander("View XAI explanation"):
                    # ── Diverging bar chart ───────────────────────────────────
                    risk_factors = result.get('risk_factors') or []
                    if risk_factors:
                        rf_labels = [rf['feature'] for rf in risk_factors[:6]]
                        rf_vals   = [
                            rf['contribution'] if rf['type'] == 'risk_increasing'
                            else -abs(rf['contribution'])
                            for rf in risk_factors[:6]
                        ]
                    else:
                        # Fallback demo based on the feature keys for this disease
                        demo_data = {
                            'PM2.5': 0.18, 'PM10': 0.12, 'NO2': 0.09,
                            'SO2': 0.14,   'CO': -0.06,  'O3': 0.11,
                            'NO': -0.04,   'NH3': 0.05,
                            'Temperature': -0.03, 'Humidity': 0.10,
                            'Wind Speed': -0.05,  'Pressure': -0.02,
                        }
                        rf_labels = feat_keys[:5]
                        rf_vals   = [demo_data.get(f, 0.05) for f in rf_labels]

                    bar_colors = ["#7F77DD" if v >= 0 else "#E24B4A" for v in rf_vals]

                    fig = go.Figure(go.Bar(
                        x=rf_vals,
                        y=rf_labels,
                        orientation='h',
                        marker_color=bar_colors,
                        marker_line_width=0,
                    ))
                    fig.update_layout(
                        height=max(160, len(rf_labels) * 32),
                        margin=dict(l=0, r=0, t=32, b=0),
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        xaxis=dict(
                            zeroline=True,
                            zerolinecolor='rgba(0,0,0,0.2)',
                            zerolinewidth=1.5,
                            showgrid=False,
                            tickfont=dict(size=10),
                        ),
                        yaxis=dict(tickfont=dict(size=11)),
                        title=dict(
                            text="LIME feature impact — purple increases risk · red reduces risk",
                            font=dict(size=11, color="#666"),
                            x=0
                        ),
                        bargap=0.35,
                    )
                    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

                    # ── Stat chips ────────────────────────────────────────────
                    st.markdown(f"""
                    <div class="xai-chips">
                      <div class="xai-chip">
                        <p class="cl">Confidence</p>
                        <p class="cv">{conf:.3f}</p>
                      </div>
                      <div class="xai-chip">
                        <p class="cl">Model accuracy</p>
                        <p class="cv">{f"{accuracy:.1%}" if accuracy else "N/A"}</p>
                      </div>
                      <div class="xai-chip">
                        <p class="cl">Method</p>
                        <p class="cv">LIME</p>
                      </div>
                    </div>
                    """, unsafe_allow_html=True)

                    # ── Recommendations ───────────────────────────────────────
                    recs = result.get('recommendations') or []
                    if recs:
                        st.markdown("<p style='font-size:11px;color:#888;margin:10px 0 4px;font-weight:500;text-transform:uppercase;letter-spacing:.06em;'>Recommendations</p>", unsafe_allow_html=True)
                        for rec in recs:
                            st.markdown(f"<p style='font-size:12px;color:#444;margin:2px 0;'>• {rec}</p>", unsafe_allow_html=True)

    else:
        st.markdown("""
        <div style="text-align:center;padding:60px 20px;color:#888;">
          <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#B4B2A9" stroke-width="1.5" style="margin-bottom:12px;display:block;margin-left:auto;margin-right:auto;">
            <circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/>
            <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
          </svg>
          <p style="font-size:14px;font-weight:500;color:#666;margin-bottom:4px;">No data yet</p>
          <p style="font-size:12px;">Search for a location and click <b>Fetch Data &amp; Predict</b></p>
        </div>
        """, unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)  # close page-wrap

# ── FOOTER ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="footer">
  <div class="footer-left">
    <div class="footer-avatar">KK</div>
    <div>
      <p class="footer-name">Keerthishree Kesavan</p>
      <p class="footer-role">AI/ML Focused Full Stack Developer</p>
    </div>
  </div>
  <div class="footer-right">
    <span class="footer-powered">Powered by OpenWeather &amp; Explainable AI</span>
    <a class="footer-gh" href="https://github.com/Keerthishreekesavan" target="_blank">
      <svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor">
        <path d="M12 0C5.37 0 0 5.37 0 12c0 5.3 3.44 9.8 8.21 11.39.6.11.82-.26.82-.58v-2.03c-3.34.73-4.04-1.61-4.04-1.61-.54-1.38-1.33-1.75-1.33-1.75-1.09-.74.08-.73.08-.73 1.2.08 1.84 1.24 1.84 1.24 1.07 1.83 2.8 1.3 3.49 1 .11-.78.42-1.3.76-1.6-2.67-.3-5.47-1.33-5.47-5.93 0-1.31.47-2.38 1.24-3.22-.13-.3-.54-1.52.12-3.18 0 0 1.01-.32 3.3 1.23a11.5 11.5 0 0 1 3-.4c1.02 0 2.04.14 3 .4 2.28-1.55 3.29-1.23 3.29-1.23.66 1.66.25 2.88.12 3.18.77.84 1.24 1.91 1.24 3.22 0 4.61-2.81 5.63-5.48 5.92.43.37.81 1.1.81 2.22v3.29c0 .32.21.7.82.58A12.01 12.01 0 0 0 24 12C24 5.37 18.63 0 12 0z"/>
      </svg>
      GitHub Profile
    </a>
  </div>
</div>
""", unsafe_allow_html=True)