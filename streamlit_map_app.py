import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
from models import predict_disease_with_explanation, predict_aqi

# --- CONFIG ---
OPENWEATHER_API_KEY = st.secrets["OPENWEATHER_API_KEY"]
DEFAULT_LOCATION = (13.0827, 80.2707)  # Chennai

st.set_page_config(page_title="Air Quality & Disease Risk Map", layout="wide")
st.markdown("""
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }

/* ── Full-width overrides for Streamlit ── */
.main .block-container {
    padding: 0 !important;
    max-width: 100% !important;
    width: 100% !important;
}
.main { padding: 0 !important; background: #f0f4f8 !important; }
body { background: #f0f4f8 !important; }
section[data-testid="stSidebar"] { display: none; }

/* ── Hero ── */
.hero {
    background: #0072B5;
    padding: 28px 5% 60px;
    width: 100%;
}
.hero-title {
    color: #fff;
    font-size: 26px;
    font-weight: 700;
    margin-bottom: 4px;
    display: flex;
    align-items: center;
    gap: 10px;
}
.hero-sub { color: #B5D4F4; font-size: 14px; }

/* ── Floating metric cards ── */
.metric-row {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
    padding: 0 5%;
    margin-top: -36px;
    margin-bottom: 20px;
    position: relative;
    z-index: 10;
}
.metric-card {
    background: #fff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 12px 16px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.07);
    display: flex;
    align-items: center;
    gap: 12px;
}
.metric-card .m-icon {
    width: 36px; height: 36px;
    border-radius: 8px;
    background: #EFF6FF;
    display: flex; align-items: center; justify-content: center;
    font-size: 17px;
    flex-shrink: 0;
}
.metric-card .m-label {
    font-size: 11px;
    color: #64748b;
    font-weight: 600;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}
.metric-card .m-value {
    font-size: 20px;
    font-weight: 700;
    color: #0f172a;
    line-height: 1.15;
}
.metric-card .m-unit { font-size: 11px; color: #94a3b8; }
.metric-card.aqi-good .m-value     { color: #009966; }
.metric-card.aqi-fair .m-value     { color: #1e90ff; }
.metric-card.aqi-moderate .m-value { color: #c9a800; }
.metric-card.aqi-poor .m-value     { color: #ff9933; }
.metric-card.aqi-verypoor .m-value { color: #cc0033; }

/* ── Page body ── */
.page-body {
    padding: 0 5% 40px;
    width: 100%;
}

/* ── How-to expander ── */
div[data-testid="stExpander"] {
    background: #fff !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 10px !important;
    margin-bottom: 14px !important;
}
div[data-testid="stExpander"] summary {
    color: #0072B5 !important;
    font-weight: 600 !important;
    font-size: 13px !important;
}

/* ── Search ── */
div[data-testid="stTextInput"] input {
    border-radius: 10px !important;
    border: 1px solid #e2e8f0 !important;
    background: #fff !important;
    font-size: 14px !important;
    padding: 10px 14px !important;
}

/* ── Panel cards ── */
.panel {
    background: #fff;
    border: 1px solid #e2e8f0;
    border-radius: 14px;
    overflow: hidden;
    width: 100%;
}
.panel-head {
    padding: 12px 18px;
    border-bottom: 1px solid #f1f5f9;
    font-size: 13px;
    font-weight: 600;
    color: #0072B5;
    display: flex;
    align-items: center;
    gap: 7px;
}

/* ── Fetch button ── */
.stButton > button {
    background: #0072B5 !important;
    color: #fff !important;
    font-weight: 700 !important;
    border-radius: 10px !important;
    border: none !important;
    width: 100%;
    padding: 11px 0 !important;
    font-size: 14px !important;
}
.stButton > button:hover { background: #005a91 !important; }

/* ── Risk badges ── */
.risk-badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 700;
    margin-left: 8px;
    vertical-align: middle;
}
.risk-high { background: #fde8e8; color: #b91c1c; border: 1px solid #fca5a5; }
.risk-low  { background: #dcfce7; color: #15803d; border: 1px solid #86efac; }

/* ── AQI text ── */
.aqi-good     { color: #009966; font-weight: 700; }
.aqi-fair     { color: #1e90ff; font-weight: 700; }
.aqi-moderate { color: #c9a800; font-weight: 700; }
.aqi-poor     { color: #ff9933; font-weight: 700; }
.aqi-verypoor { color: #cc0033; font-weight: 700; }

/* ── Results panel ── */
.results-wrap {
    background: #fff;
    border: 1px solid #e2e8f0;
    border-radius: 14px;
    overflow: hidden;
    margin-bottom: 20px;
    width: 100%;
}
.results-head {
    padding: 12px 18px;
    border-bottom: 1px solid #f1f5f9;
    font-size: 13px;
    font-weight: 600;
    color: #0072B5;
}
.results-body { padding: 18px 20px; }

/* ── Empty state ── */
.empty-state {
    text-align: center;
    padding: 40px 16px;
    color: #94a3b8;
}
.empty-state .empty-icon { font-size: 36px; margin-bottom: 10px; }
.empty-state p { font-size: 13px; line-height: 1.6; }

/* ── Disease rows ── */
.disease-row {
    padding: 12px 0;
    border-bottom: 1px solid #f1f5f9;
}
.disease-row:last-child { border-bottom: none; }
.disease-name { font-size: 14px; font-weight: 600; color: #1e293b; }
.info-box {
    background: #f8fafc;
    border-left: 3px solid #0072B5;
    border-radius: 0 8px 8px 0;
    padding: 9px 13px;
    margin-top: 7px;
    font-size: 13px;
    color: #475569;
    line-height: 1.6;
}

/* ── Footer ── */
.footer-sub {
    text-align: right;
    font-size: 11px;
    color: #94a3b8;
    margin-top: 10px;
    padding-bottom: 20px;
}

/* ── Streamlit column gap fix ── */
div[data-testid="stHorizontalBlock"] {
    gap: 1.5rem;
    align-items: stretch;
}
</style>
""", unsafe_allow_html=True)

# --- Helpers ---
def aqi_category(aqi):
    if aqi < 2:   return "Good",      "aqi-good"
    elif aqi < 3: return "Fair",      "aqi-fair"
    elif aqi < 4: return "Moderate",  "aqi-moderate"
    elif aqi < 5: return "Poor",      "aqi-poor"
    else:         return "Very Poor", "aqi-verypoor"

def fetch_openweather_data(lat, lon):
    air_url     = f"https://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}"
    weather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric"
    ar = requests.get(air_url)
    wr = requests.get(weather_url)
    return (ar.json() if ar.status_code == 200 else None,
            wr.json() if wr.status_code == 200 else None)

def extract_features(air_data, weather_data):
    f = {'PM2.5':10.0,'PM10':20.0,'NO2':10.0,'SO2':5.0,
         'CO':0.5,'O3':15.0,'NH3':1.0,'NO':1.0,
         'Temperature':25.0,'Humidity':50.0,'Wind Speed':2.0,'Pressure':1013.0}
    if air_data and "list" in air_data and air_data["list"]:
        c = air_data["list"][0]["components"]
        for k,a in [('PM2.5','pm2_5'),('PM10','pm10'),('NO2','no2'),
                    ('SO2','so2'),('CO','co'),('O3','o3'),('NH3','nh3'),('NO','no')]:
            f[k] = c.get(a, f[k])
    if weather_data:
        m = weather_data.get("main", {})
        f['Temperature'] = m.get('temp',     f['Temperature'])
        f['Humidity']    = m.get('humidity', f['Humidity'])
        f['Pressure']    = m.get('pressure', f['Pressure'])
        f['Wind Speed']  = weather_data.get("wind", {}).get('speed', f['Wind Speed'])
    return f

# --- Disease data ---
disease_labels = {
    'Asthma': ['PM2.5','PM10','NO2'],
    'COPD': ['PM2.5','PM10','SO2'],
    'Lung Cancer': ['PM2.5','PM10','NO2','O3'],
    'Pneumonia & Bronchitis': ['PM2.5','PM10','SO2','CO'],
    'Reduced Lung Function in Children': ['PM2.5','NO2','O3'],
    'Heart Attacks': ['PM2.5','PM10','CO'],
    'Hypertension': ['NO2','SO2','CO'],
    'Strokes': ['PM2.5','PM10','NO2'],
    'Arrhythmia': ['NO2','SO2','CO'],
    "Alzheimer's & Dementia": ['PM2.5','NO2'],
    "Parkinson's Disease": ['PM2.5','NO2','O3'],
    "Cognitive Impairment in Children": ['PM2.5','NO2'],
    "Low Birth Weight": ['PM2.5','PM10','NO2'],
    "Preterm Births": ['PM2.5','PM10','NO2'],
    "Sudden Infant Death Syndrome (SIDS)": ['PM2.5','PM10'],
    "Bladder Cancer": ['PM2.5','NO2','O3'],
    "Diabetes": ['PM2.5','NO2','SO2'],
    "Eye & Skin Irritation": ['SO2','O3'],
}
disease_effects = {
    'Asthma':"Wheezing, breathlessness, chest tightness, and coughing.",
    'COPD':"Long-term breathing problems, chronic cough, and frequent respiratory infections.",
    'Lung Cancer':"Persistent cough, chest pain, hoarseness, and weight loss.",
    'Pneumonia & Bronchitis':"Lung inflammation, cough, fever, and difficulty breathing.",
    'Reduced Lung Function in Children':"Developmental issues, increased asthma risk, reduced physical activity.",
    'Heart Attacks':"Chest pain, shortness of breath — can be fatal without immediate treatment.",
    'Hypertension':"Increased risk of heart disease, stroke, and kidney problems.",
    'Strokes':"Paralysis, speech difficulties, and long-term disability.",
    'Arrhythmia':"Palpitations, dizziness, and increased stroke risk.",
    "Alzheimer's & Dementia":"Memory loss, confusion, and behavioural changes.",
    "Parkinson's Disease":"Tremors, stiffness, and difficulty with movement.",
    "Cognitive Impairment in Children":"Affects learning, memory, and behaviour.",
    "Low Birth Weight":"Risk of infections, developmental delays, and chronic health issues.",
    "Preterm Births":"Breathing, heart, and developmental problems in premature babies.",
    "Sudden Infant Death Syndrome (SIDS)":"Sudden unexplained death of a healthy baby, often during sleep.",
    "Bladder Cancer":"Blood in urine, pain, and frequent urination.",
    "Diabetes":"High blood sugar, fatigue, and complications affecting eyes, kidneys, and nerves.",
    "Eye & Skin Irritation":"Redness, itching, and discomfort in eyes and skin.",
}
disease_precautions = {
    'Asthma':"Avoid outdoor activity on high-pollution days, use air purifiers.",
    'COPD':"Quit smoking, avoid polluted areas, get regular vaccinations.",
    'Lung Cancer':"Avoid smoking and secondhand smoke, get regular checkups.",
    'Pneumonia & Bronchitis':"Practice good hygiene, avoid sick contacts, get vaccinated.",
    'Reduced Lung Function in Children':"Limit outdoor activity on high-pollution days, use indoor air filters.",
    'Heart Attacks':"Maintain a healthy diet, exercise regularly, monitor blood pressure.",
    'Hypertension':"Reduce salt intake, exercise regularly, manage stress.",
    'Strokes':"Control blood pressure, avoid smoking, maintain a healthy weight.",
    'Arrhythmia':"Avoid stimulants, manage stress, follow your doctor's advice.",
    "Alzheimer's & Dementia":"Regular mental and physical activity, maintain a healthy diet.",
    "Parkinson's Disease":"Exercise regularly and follow prescribed treatments.",
    "Cognitive Impairment in Children":"Encourage learning activities, minimise pollutant exposure.",
    "Low Birth Weight":"Good prenatal care, avoid smoke and pollution during pregnancy.",
    "Preterm Births":"Regular prenatal checkups, avoid stress and pollutants.",
    "Sudden Infant Death Syndrome (SIDS)":"Place babies on their backs to sleep, avoid soft bedding.",
    "Bladder Cancer":"Avoid smoking and exposure to industrial chemicals.",
    "Diabetes":"Healthy diet, exercise regularly, monitor blood sugar.",
    "Eye & Skin Irritation":"Wear protective eyewear, avoid rubbing eyes, use gentle skin products.",
}

# --- Session state ---
if 'map_center' not in st.session_state:
    st.session_state.map_center = DEFAULT_LOCATION
if 'marker' not in st.session_state:
    st.session_state.marker = DEFAULT_LOCATION
if 'fetched_features' not in st.session_state:
    st.session_state.fetched_features = None

lat, lon = st.session_state.marker

# ═══════════════════════════════════
# HERO
# ═══════════════════════════════════
st.markdown("""
<div class="hero">
    <div class="hero-title">🌏 Air Quality &amp; Disease Risk Map</div>
    <div class="hero-sub">Real-time air quality monitoring and health risk predictions</div>
</div>
""", unsafe_allow_html=True)

# ═══════════════════════════════════
# FLOATING METRIC CARDS
# ═══════════════════════════════════
fd = st.session_state.fetched_features
pm25 = f"{fd['PM2.5']:.1f}" if fd else "—"
pm10 = f"{fd['PM10']:.1f}"  if fd else "—"
no2  = f"{fd['NO2']:.1f}"   if fd else "—"
aqi_val_str    = "—"
aqi_card_class = ""
if fd:
    aqi_inp = [fd[k] for k in ['PM2.5','PM10','NO2','SO2','CO','O3'] if k in fd]
    aqi_res = predict_aqi(aqi_inp)
    if aqi_res:
        aqi_num, _, _ = aqi_res
        cat, cls = aqi_category(aqi_num)
        aqi_val_str    = f"{aqi_num:.1f}"
        aqi_card_class = cls

st.markdown(f"""
<div class="metric-row">
  <div class="metric-card">
    <div class="m-icon">💨</div>
    <div>
      <div class="m-label">PM2.5</div>
      <div class="m-value">{pm25} <span class="m-unit">μg/m³</span></div>
    </div>
  </div>
  <div class="metric-card">
    <div class="m-icon">🌫️</div>
    <div>
      <div class="m-label">PM10</div>
      <div class="m-value">{pm10} <span class="m-unit">μg/m³</span></div>
    </div>
  </div>
  <div class="metric-card">
    <div class="m-icon">⚗️</div>
    <div>
      <div class="m-label">NO2</div>
      <div class="m-value">{no2} <span class="m-unit">μg/m³</span></div>
    </div>
  </div>
  <div class="metric-card {aqi_card_class}">
    <div class="m-icon">📊</div>
    <div>
      <div class="m-label">AQI Index</div>
      <div class="m-value">{aqi_val_str}</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ═══════════════════════════════════
# PAGE BODY
# ═══════════════════════════════════
st.markdown('<div class="page-body">', unsafe_allow_html=True)

# How-to — now clearly visible on white bg
with st.expander("ℹ️  How to use this tool"):
    st.markdown("""
    1. Type a city name and click **Search**, or click anywhere on the map to select a location.
    2. The metric cards at the top update with live PM2.5, PM10, NO2, and AQI data.
    3. Click **Fetch Data & Predict** to run the full disease risk analysis.
    """)

# Search row
sc, bc = st.columns([5, 1])
with sc:
    search_query = st.text_input("", "Chennai", placeholder="Search for a city or location…",
                                 label_visibility="collapsed", key="searchbar")
with bc:
    search_btn = st.button("🔍  Search", key="searchbtn")

if search_btn and search_query:
    geo_url  = f"http://api.openweathermap.org/geo/1.0/direct?q={search_query}&limit=1&appid={OPENWEATHER_API_KEY}"
    geo_resp = requests.get(geo_url)
    geo_data = geo_resp.json() if geo_resp.status_code == 200 else []
    if geo_data:
        loc = (geo_data[0]['lat'], geo_data[0]['lon'])
        st.session_state.map_center = loc
        st.session_state.marker     = loc
        st.success(f"📍 Found: {geo_data[0]['name']}, {geo_data[0].get('country','')}")
    else:
        st.error("Location not found. Try a different search.")

st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

# ── Map + right panel ────────────────────────────
map_col, right_col = st.columns([3, 2], gap="large")

with map_col:
    st.markdown("<div class='panel'><div class='panel-head'>🗺️ Map — click to select a location</div>", unsafe_allow_html=True)
    m = folium.Map(location=st.session_state.map_center, zoom_start=7, control_scale=True)
    folium.Marker(
        location=st.session_state.marker,
        icon=folium.Icon(color='red', icon='info-sign'),
        popup="Selected Location"
    ).add_to(m)
    map_data = st_folium(m, width="100%", height=400, returned_objects=["last_clicked"])
    st.markdown("</div>", unsafe_allow_html=True)

    if map_data and map_data.get("last_clicked"):
        lat = map_data["last_clicked"]["lat"]
        lon = map_data["last_clicked"]["lng"]
        st.session_state.marker     = (lat, lon)
        st.session_state.map_center = (lat, lon)
    else:
        lat, lon = st.session_state.marker

with right_col:
    # Pollutants detail card
    st.markdown("<div class='panel'><div class='panel-head'>💨 All pollutants & weather</div>", unsafe_allow_html=True)
    if st.session_state.fetched_features:
        rows = [
            ("SO2",        f"{fd['SO2']:.1f} μg/m³"),
            ("CO",         f"{fd['CO']:.2f} mg/m³"),
            ("O3",         f"{fd['O3']:.1f} μg/m³"),
            ("NH3",        f"{fd['NH3']:.1f} μg/m³"),
            ("Temperature",f"{fd['Temperature']:.1f} °C"),
            ("Humidity",   f"{fd['Humidity']:.0f}%"),
            ("Wind Speed", f"{fd['Wind Speed']:.1f} m/s"),
            ("Pressure",   f"{fd['Pressure']:.0f} hPa"),
        ]
        for label, val in rows:
            st.markdown(f"""
            <div style='display:flex;justify-content:space-between;align-items:center;
                        padding:9px 18px;border-bottom:1px solid #f1f5f9;font-size:13px;'>
                <span style='color:#64748b;'>{label}</span>
                <span style='font-weight:600;color:#0f172a;'>{val}</span>
            </div>""", unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style='padding:24px 18px;color:#94a3b8;font-size:13px;text-align:center;'>
            Fetch data to see pollutant details
        </div>""", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    fetch_btn = st.button("⟳  Fetch Data & Predict", key="fetchbtn")

# ═══════════════════════════════════
# RESULTS
# ═══════════════════════════════════
st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
st.markdown("<div class='results-wrap'><div class='results-head'>📊 Prediction results</div><div class='results-body'>", unsafe_allow_html=True)

run_prediction = fetch_btn or (map_data and map_data.get("last_clicked"))

if run_prediction:
    with st.spinner("Fetching live data and running predictions…"):
        air_data, weather_data = fetch_openweather_data(lat, lon)
        features = extract_features(air_data, weather_data)
        st.session_state.fetched_features = features

    st.markdown("#### Editable features")
    ec1, ec2 = st.columns(2)
    for i, k in enumerate(features.keys()):
        col = ec1 if i < len(features) // 2 else ec2
        features[k] = col.number_input(k, value=float(features[k]), key=f"feat_{k}")

    aqi_input  = [features[k] for k in ['PM2.5','PM10','NO2','SO2','CO','O3'] if k in features]
    aqi_result = predict_aqi(aqi_input)
    if aqi_result:
        aqi_value, lime_exp, shap_exp = aqi_result
        cat, cls = aqi_category(aqi_value)
        st.markdown(f"<p style='font-size:20px;margin:16px 0 10px;font-weight:700;'>"
                    f"Predicted AQI: <span class='{cls}'>{aqi_value:.2f} — {cat}</span></p>",
                    unsafe_allow_html=True)
        with st.expander("AQI — explainable AI details"):
            st.write("LIME:", lime_exp or "N/A")
            st.write("SHAP:", shap_exp or "N/A")
    else:
        st.error("AQI prediction failed or model not available.")

    st.markdown("<p style='font-size:15px;font-weight:700;margin:18px 0 4px;'>Disease risk breakdown</p>", unsafe_allow_html=True)
    for disease, feats_list in disease_labels.items():
        disease_input = [features[k] for k in feats_list if k in features]
        result = predict_disease_with_explanation(disease_input, disease)
        if result:
            high       = result['prediction'] == 1
            risk_label = 'HIGH RISK' if high else 'LOW RISK'
            badge_cls  = 'risk-high' if high else 'risk-low'
            icon       = '⚠️' if high else '✅'
            st.markdown(f"""
            <div class='disease-row'>
                <div class='disease-name'>{disease}
                    <span class='risk-badge {badge_cls}'>{icon} {risk_label}</span>
                </div>
            </div>""", unsafe_allow_html=True)
            st.markdown(f"""
            <div class='info-box'>
                <b>Effects:</b> {disease_effects.get(disease,'')}<br>
                <b>Precautions:</b> {disease_precautions.get(disease,'')}
            </div>""", unsafe_allow_html=True)
            with st.expander(f"{disease} — AI details"):
                st.write(f"Confidence: {max(result['probability']):.3f}")
                st.write(f"Model accuracy: {result['accuracy'] or 'N/A'}")
                st.write("LIME:", result.get('lime_explanation') or "N/A")
                st.write("SHAP:", result.get('shap_explanation') or "N/A")
                if result.get('risk_factors'):
                    st.write("Risk factors:")
                    for rf in result['risk_factors'][:5]:
                        direction = "increases" if rf['type'] == 'risk_increasing' else "decreases"
                        st.write(f"  · {rf['feature']} {direction} risk (contribution: {rf['contribution']:.4f})")
                if result.get('recommendations'):
                    st.write("Recommendations:")
                    for rec in result['recommendations']:
                        st.write(f"  · {rec}")
else:
    st.markdown("""
    <div class='empty-state'>
        <div class='empty-icon'>🗺️</div>
        <p>Search for a location or click the map,<br>
        then hit <strong>Fetch Data &amp; Predict</strong> to see results.</p>
    </div>""", unsafe_allow_html=True)

st.markdown("</div></div>", unsafe_allow_html=True)

# ═══════════════════════════════════
# FOOTER (unchanged)
# ═══════════════════════════════════
st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
fc1, fc2 = st.columns([4, 1])
with fc1:
    fl1, fl2 = st.columns([1, 5])
    with fl1:
        st.image("tulip.jpg", width=75)
    with fl2:
        st.markdown("""
        <div style='padding-top:4px;'>
            <div style='font-size:19px;font-weight:700;color:#0f172a;'>Created by Keerthishree Kesavan</div>
            <div style='font-size:13px;color:#64748b;margin-top:2px;'>AI/ML Focused Full Stack Developer</div>
        </div>""", unsafe_allow_html=True)
with fc2:
    st.link_button("GitHub Profile", "https://github.com/Keerthishreekesavan")

st.markdown("""
<div class='footer-sub'>
    Developed by Air Quality AI &nbsp;·&nbsp; Powered by OpenWeather &amp; Explainable AI
</div>""", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)