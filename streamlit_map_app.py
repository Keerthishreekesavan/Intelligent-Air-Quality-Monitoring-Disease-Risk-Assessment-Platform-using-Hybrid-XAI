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
/* ── Reset & base ── */
* { box-sizing: border-box; }
.main, body { background: #f0f4f8 !important; }
.block-container {
    padding: 0 !important;
    max-width: 100% !important;
}
section[data-testid="stSidebar"] { display: none; }

/* ── Hero banner ── */
.hero {
    background: #0072B5;
    padding: 36px 48px 52px;
    position: relative;
}
.hero-title {
    color: #fff;
    font-size: 28px;
    font-weight: 700;
    margin-bottom: 4px;
    letter-spacing: -0.3px;
}
.hero-sub {
    color: #B5D4F4;
    font-size: 15px;
    margin-bottom: 0;
}

/* ── Floating metric cards ── */
.metric-row {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
    padding: 0 48px;
    margin-top: -28px;
    margin-bottom: 28px;
    position: relative;
    z-index: 10;
}
.metric-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 14px;
    padding: 16px 20px;
    box-shadow: 0 4px 16px rgba(0,0,0,0.08);
}
.metric-card .m-label {
    font-size: 11px;
    color: #64748b;
    font-weight: 600;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    margin-bottom: 4px;
}
.metric-card .m-value {
    font-size: 26px;
    font-weight: 700;
    color: #0f172a;
    line-height: 1.1;
}
.metric-card .m-unit {
    font-size: 12px;
    color: #94a3b8;
    font-weight: 400;
}
.metric-card.aqi-good .m-value    { color: #009966; }
.metric-card.aqi-fair .m-value    { color: #1e90ff; }
.metric-card.aqi-moderate .m-value{ color: #c9a800; }
.metric-card.aqi-poor .m-value    { color: #ff9933; }
.metric-card.aqi-verypoor .m-value{ color: #cc0033; }

/* ── Page content wrapper ── */
.page-body {
    padding: 0 48px 48px;
}

/* ── Search row in hero ── */
.hero-search-hint {
    color: #B5D4F4;
    font-size: 13px;
    margin-top: 18px;
    margin-bottom: 0;
}

/* ── Two col layout ── */
.two-col {
    display: grid;
    grid-template-columns: 3fr 2fr;
    gap: 20px;
    margin-bottom: 24px;
}

/* ── Panel cards ── */
.panel {
    background: #fff;
    border: 1px solid #e2e8f0;
    border-radius: 16px;
    overflow: hidden;
}
.panel-head {
    padding: 14px 20px;
    border-bottom: 1px solid #f1f5f9;
    font-size: 13px;
    font-weight: 600;
    color: #0072B5;
    display: flex;
    align-items: center;
    gap: 7px;
}

/* ── Risk badges ── */
.risk-badge {
    display: inline-block;
    padding: 3px 11px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 700;
    margin-left: 8px;
    vertical-align: middle;
    letter-spacing: 0.03em;
}
.risk-high { background: #fde8e8; color: #b91c1c; border: 1px solid #fca5a5; }
.risk-low  { background: #dcfce7; color: #15803d; border: 1px solid #86efac; }

/* ── AQI text colours ── */
.aqi-good     { color: #009966; font-weight: 700; }
.aqi-fair     { color: #1e90ff; font-weight: 700; }
.aqi-moderate { color: #c9a800; font-weight: 700; }
.aqi-poor     { color: #ff9933; font-weight: 700; }
.aqi-verypoor { color: #cc0033; font-weight: 700; }

/* ── Predict button ── */
.stButton > button {
    background: #0072B5 !important;
    color: #fff !important;
    font-weight: 700 !important;
    border-radius: 10px !important;
    border: none !important;
    width: 100%;
    padding: 12px 0 !important;
    font-size: 15px !important;
    letter-spacing: 0.01em;
}
.stButton > button:hover { background: #005a91 !important; }

/* ── Results panel ── */
.results-wrap {
    background: #fff;
    border: 1px solid #e2e8f0;
    border-radius: 16px;
    overflow: hidden;
    margin-bottom: 24px;
}
.results-head {
    padding: 14px 20px;
    border-bottom: 1px solid #f1f5f9;
    font-size: 13px;
    font-weight: 600;
    color: #0072B5;
    display: flex;
    align-items: center;
    gap: 7px;
}
.results-body { padding: 20px; }

/* ── Empty state ── */
.empty-state {
    text-align: center;
    padding: 48px 16px;
    color: #94a3b8;
}
.empty-state .empty-icon { font-size: 40px; margin-bottom: 12px; }
.empty-state p { font-size: 14px; line-height: 1.6; max-width: 340px; margin: 0 auto; }

/* ── Disease row ── */
.disease-row {
    padding: 14px 0;
    border-bottom: 1px solid #f1f5f9;
}
.disease-row:last-child { border-bottom: none; }
.disease-name { font-size: 14px; font-weight: 600; color: #1e293b; }

/* ── Info box ── */
.info-box {
    background: #f8fafc;
    border-left: 3px solid #0072B5;
    border-radius: 0 8px 8px 0;
    padding: 10px 14px;
    margin-top: 8px;
    font-size: 13px;
    color: #475569;
    line-height: 1.6;
}

/* ── Footer ── */
.footer-section {
    background: #fff;
    border: 1px solid #e2e8f0;
    border-radius: 16px;
    padding: 20px 24px;
    display: flex;
    align-items: center;
    gap: 16px;
}
.footer-name {
    font-size: 17px;
    font-weight: 700;
    color: #0f172a;
    margin-bottom: 2px;
}
.footer-role {
    font-size: 13px;
    color: #64748b;
}

/* ── How-to expander ── */
div[data-testid="stExpander"] {
    background: rgba(255,255,255,0.12) !important;
    border: 1px solid rgba(255,255,255,0.25) !important;
    border-radius: 10px !important;
    color: #fff !important;
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
    air_resp     = requests.get(air_url)
    weather_resp = requests.get(weather_url)
    return (
        air_resp.json()     if air_resp.status_code == 200     else None,
        weather_resp.json() if weather_resp.status_code == 200 else None,
    )

def extract_features(air_data, weather_data):
    f = {
        'PM2.5': 10.0, 'PM10': 20.0, 'NO2': 10.0, 'SO2': 5.0,
        'CO': 0.5, 'O3': 15.0, 'NH3': 1.0, 'NO': 1.0,
        'Temperature': 25.0, 'Humidity': 50.0, 'Wind Speed': 2.0, 'Pressure': 1013.0
    }
    if air_data and "list" in air_data and air_data["list"]:
        c = air_data["list"][0]["components"]
        for k, a in [('PM2.5','pm2_5'),('PM10','pm10'),('NO2','no2'),
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
    "Eye & Skin Irritation": ['SO2', 'O3'],
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
    "Eye & Skin Irritation": "Redness, itching, and discomfort in eyes and skin.",
}
disease_precautions = {
    'Asthma': "Avoid outdoor activity on high-pollution days, use air purifiers, follow your asthma action plan.",
    'COPD': "Quit smoking, avoid polluted areas, get regular vaccinations.",
    'Lung Cancer': "Avoid smoking and secondhand smoke, reduce pollutant exposure, get regular checkups.",
    'Pneumonia & Bronchitis': "Practice good hygiene, avoid sick contacts, get vaccinated.",
    'Reduced Lung Function in Children': "Limit outdoor activity on high-pollution days, use indoor air filters.",
    'Heart Attacks': "Maintain a healthy diet, exercise regularly, monitor blood pressure.",
    'Hypertension': "Reduce salt intake, exercise regularly, manage stress.",
    'Strokes': "Control blood pressure, avoid smoking, maintain a healthy weight.",
    'Arrhythmia': "Avoid stimulants, manage stress, follow your doctor's advice.",
    "Alzheimer's & Dementia": "Regular mental and physical activity, maintain a healthy diet.",
    "Parkinson's Disease": "Exercise regularly and follow prescribed treatments.",
    "Cognitive Impairment in Children": "Encourage learning activities, minimise pollutant exposure.",
    "Low Birth Weight": "Good prenatal care, avoid smoke and pollution during pregnancy.",
    "Preterm Births": "Regular prenatal checkups, avoid stress and pollutants.",
    "Sudden Infant Death Syndrome (SIDS)": "Place babies on their backs to sleep, avoid soft bedding.",
    "Bladder Cancer": "Avoid smoking and exposure to industrial chemicals.",
    "Diabetes": "Healthy diet, exercise regularly, monitor blood sugar.",
    "Eye & Skin Irritation": "Wear protective eyewear, avoid rubbing eyes, use gentle skin products.",
}

# --- Session state ---
if 'map_center' not in st.session_state:
    st.session_state.map_center = DEFAULT_LOCATION
if 'marker' not in st.session_state:
    st.session_state.marker = DEFAULT_LOCATION
if 'fetched_features' not in st.session_state:
    st.session_state.fetched_features = None

lat, lon = st.session_state.marker

# ═══════════════════════════════════════════════════════════
# HERO BANNER
# ═══════════════════════════════════════════════════════════
st.markdown("""
<div class="hero">
    <div class="hero-title">🌏 Air Quality & Disease Risk Map</div>
    <div class="hero-sub">Real-time air quality monitoring and health risk predictions</div>
</div>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════
# FLOATING METRIC CARDS
# ═══════════════════════════════════════════════════════════
f = st.session_state.fetched_features
pm25 = f"{f['PM2.5']:.1f}"  if f else "—"
pm10 = f"{f['PM10']:.1f}"   if f else "—"
no2  = f"{f['NO2']:.1f}"    if f else "—"

aqi_val_str   = "—"
aqi_card_class = ""
if f:
    aqi_inp = [f[k] for k in ['PM2.5','PM10','NO2','SO2','CO','O3'] if k in f]
    aqi_res = predict_aqi(aqi_inp)
    if aqi_res:
        aqi_num, _, _ = aqi_res
        cat, cls = aqi_category(aqi_num)
        aqi_val_str   = f"{aqi_num:.1f}"
        aqi_card_class = cls

st.markdown(f"""
<div class="metric-row">
    <div class="metric-card">
        <div class="m-label">PM2.5</div>
        <div class="m-value">{pm25}<span class="m-unit"> μg/m³</span></div>
    </div>
    <div class="metric-card">
        <div class="m-label">PM10</div>
        <div class="m-value">{pm10}<span class="m-unit"> μg/m³</span></div>
    </div>
    <div class="metric-card">
        <div class="m-label">NO2</div>
        <div class="m-value">{no2}<span class="m-unit"> μg/m³</span></div>
    </div>
    <div class="metric-card {aqi_card_class}">
        <div class="m-label">AQI Index</div>
        <div class="m-value">{aqi_val_str}</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════
# PAGE BODY
# ═══════════════════════════════════════════════════════════
st.markdown('<div class="page-body">', unsafe_allow_html=True)

# How-to
with st.expander("ℹ️  How to use this tool"):
    st.write("""
    1. Type a city name in the search box and click **Search**, or click anywhere on the map.
    2. The four metric cards at the top update with live PM2.5, PM10, NO2, and AQI data.
    3. Click **Fetch Data & Predict** to run the full disease risk analysis.
    """)

# ── Search row ───────────────────────────────────────────
search_c, btn_c = st.columns([5, 1])
with search_c:
    search_query = st.text_input("", "Chennai", placeholder="Search for a city or location…",
                                 label_visibility="collapsed", key="searchbar")
with btn_c:
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

st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

# ── Map + right panel ────────────────────────────────────
map_col, right_col = st.columns([3, 2], gap="large")

with map_col:
    st.markdown("<div class='panel'><div class='panel-head'>🗺️ Map — click to select a location</div>", unsafe_allow_html=True)
    m = folium.Map(location=st.session_state.map_center, zoom_start=7, control_scale=True)
    folium.Marker(
        location=st.session_state.marker,
        icon=folium.Icon(color='red', icon='info-sign'),
        popup="Selected Location"
    ).add_to(m)
    map_data = st_folium(m, width="100%", height=420, returned_objects=["last_clicked"])
    st.markdown("</div>", unsafe_allow_html=True)

    if map_data and map_data.get("last_clicked"):
        lat = map_data["last_clicked"]["lat"]
        lon = map_data["last_clicked"]["lng"]
        st.session_state.marker     = (lat, lon)
        st.session_state.map_center = (lat, lon)
    else:
        lat, lon = st.session_state.marker

with right_col:
    st.markdown("<div class='panel'><div class='panel-head'>💨 All pollutants & weather</div>", unsafe_allow_html=True)
    if st.session_state.fetched_features:
        fd = st.session_state.fetched_features
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
            <div style='display:flex;justify-content:space-between;padding:9px 20px;
                        border-bottom:1px solid #f1f5f9;font-size:13px;'>
                <span style='color:#64748b;'>{label}</span>
                <span style='font-weight:600;color:#0f172a;'>{val}</span>
            </div>""", unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style='padding:20px;color:#94a3b8;font-size:13px;text-align:center;'>
            Fetch data to see pollutant details
        </div>""", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
    fetch_btn = st.button("⟳  Fetch Data & Predict", key="fetchbtn")

# ═══════════════════════════════════════════════════════════
# RESULTS
# ═══════════════════════════════════════════════════════════
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

    # AQI result
    aqi_input  = [features[k] for k in ['PM2.5','PM10','NO2','SO2','CO','O3'] if k in features]
    aqi_result = predict_aqi(aqi_input)
    if aqi_result:
        aqi_value, lime_exp, shap_exp = aqi_result
        cat, cls = aqi_category(aqi_value)
        st.markdown(f"<p style='font-size:20px;margin:20px 0 12px;font-weight:700;'>"
                    f"Predicted AQI: <span class='{cls}'>{aqi_value:.2f} — {cat}</span></p>",
                    unsafe_allow_html=True)
        with st.expander("AQI — explainable AI details"):
            st.write("LIME:", lime_exp or "N/A")
            st.write("SHAP:", shap_exp or "N/A")
    else:
        st.error("AQI prediction failed or model not available.")

    # Disease risks
    st.markdown("<p style='font-size:16px;font-weight:700;margin:20px 0 4px;'>Disease risk breakdown</p>", unsafe_allow_html=True)
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
            eff  = disease_effects.get(disease, '')
            prec = disease_precautions.get(disease, '')
            st.markdown(f"""
            <div class='info-box'>
                <b>Effects:</b> {eff}<br>
                <b>Precautions:</b> {prec}
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
        <p>Search for a location or click the map,<br>then hit <strong>Fetch Data & Predict</strong> to see results.</p>
    </div>""", unsafe_allow_html=True)

st.markdown("</div></div>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════
# FOOTER
# ═══════════════════════════════════════════════════════════
st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
fc1, fc2 = st.columns([4, 1])
with fc1:
    fl1, fl2 = st.columns([1, 5])
    with fl1:
        st.image("tulip.jpg", width=80)
    with fl2:
        st.markdown("""
        <div style='padding-top:6px;'>
            <div style='font-size:20px;font-weight:700;color:#0f172a;'>Created by Keerthishree Kesavan</div>
            <div style='font-size:14px;color:#64748b;margin-top:2px;'>AI/ML Focused Full Stack Developer</div>
        </div>""", unsafe_allow_html=True)
with fc2:
    st.link_button("GitHub Profile", "https://github.com/Keerthishreekesavan")

st.markdown("""
<div style='text-align:right;font-size:11px;color:#94a3b8;margin-top:12px;padding-bottom:24px;'>
    Developed by Air Quality AI &nbsp;·&nbsp; Powered by OpenWeather &amp; Explainable AI
</div>""", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)