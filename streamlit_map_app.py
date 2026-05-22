import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
from models import predict_disease_with_explanation, predict_aqi

OPENWEATHER_API_KEY = st.secrets["OPENWEATHER_API_KEY"]
DEFAULT_LOCATION = (13.0827, 80.2707)

st.set_page_config(page_title="Air Quality & Disease Risk Map", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700&display=swap');

*, *::before, *::after { box-sizing: border-box; }

html, body,
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
[data-testid="stMainBlockContainer"] {
    font-family: 'DM Sans', sans-serif !important;
    background: #f4f6f9 !important;
    margin: 0 !important;
    padding: 0 !important;
}
[data-testid="stHeader"]  { display: none !important; }
[data-testid="stSidebar"] { display: none !important; }
[data-testid="stBottom"]  { display: none !important; }
.block-container {
    padding: 0 !important;
    max-width: 100% !important;
}

/* ── NAV ── */
.topnav {
    background: #1a3a5c;
    padding: 0 40px;
    height: 56px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    position: sticky;
    top: 0;
    z-index: 100;
}
.topnav-brand {
    display: flex;
    align-items: center;
    gap: 12px;
}
.topnav-brand-text {
    font-size: 17px;
    font-weight: 600;
    color: #fff;
    letter-spacing: -0.01em;
}
.topnav-pills { display: flex; gap: 8px; }
.topnav-pill {
    display: flex;
    align-items: center;
    gap: 6px;
    background: rgba(255,255,255,0.1);
    border: 1px solid rgba(255,255,255,0.15);
    border-radius: 20px;
    padding: 6px 16px;
    font-size: 13px;
    color: #cbd5e1;
}

/* ── PAGE WRAPPER ── */
.page {
    max-width: 900px;
    margin: 0 auto;
    padding: 36px 24px 60px;
}

/* ── SECTION BLOCK ── */
.section {
    background: #fff;
    border: 1px solid #e2e8f0;
    border-radius: 14px;
    padding: 24px 28px;
    margin-bottom: 20px;
}
.section-heading {
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #94a3b8;
    margin-bottom: 16px;
}

/* ── SEARCH ROW ── */
[data-testid="stTextInput"] input {
    border: 1px solid #e2e8f0 !important;
    border-radius: 10px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 15px !important;
    color: #1e293b !important;
    background: #f8fafc !important;
    padding: 10px 16px !important;
    height: 46px !important;
}
[data-testid="stTextInput"] input:focus {
    border-color: #1a3a5c !important;
    box-shadow: 0 0 0 3px rgba(26,58,92,0.08) !important;
    outline: none !important;
}
[data-testid="stTextInput"] label { display: none !important; }

div[data-testid="stButton"] > button {
    background: #1a3a5c !important;
    color: #fff !important;
    border: none !important;
    border-radius: 10px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 600 !important;
    font-size: 14px !important;
    padding: 10px 28px !important;
    height: 46px !important;
    letter-spacing: 0.01em !important;
    transition: background 0.18s !important;
    white-space: nowrap !important;
    width: 100% !important;
}
div[data-testid="stButton"] > button:hover { background: #254e7a !important; }

/* ── MAP ── */
.map-wrap {
    border-radius: 10px;
    overflow: hidden;
    border: 1px solid #e2e8f0;
    margin-bottom: 0;
}
/* hide leaflet attribution */
.leaflet-control-attribution { display: none !important; }

/* ── METRIC GRID ── */
.metric-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
    margin-top: 16px;
}
.metric-card {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 14px 18px;
}
.metric-label {
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.09em;
    text-transform: uppercase;
    color: #94a3b8;
    margin-bottom: 5px;
}
.metric-val {
    font-size: 20px;
    font-weight: 700;
    color: #1e293b;
}

/* ── STEPS BAR ── */
.steps-bar {
    display: flex;
    align-items: center;
    gap: 24px;
    padding: 14px 0 4px;
}
.step-item {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 13px;
    color: #64748b;
    font-weight: 500;
}
.step-num {
    width: 22px; height: 22px;
    border-radius: 50%;
    background: #1a3a5c;
    color: #fff;
    font-size: 11px;
    font-weight: 700;
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0;
}

/* ── POLLUTANT ROW ── */
.poll-row-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
    margin-top: 14px;
}
.poll-card {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 14px 18px;
    text-align: center;
}
.poll-card-label {
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.09em;
    text-transform: uppercase;
    color: #94a3b8;
    margin-bottom: 5px;
}
.poll-card-val {
    font-size: 20px;
    font-weight: 700;
    color: #1e293b;
}

/* ── AQI RESULT ── */
.aqi-result-card {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 20px 24px;
    margin-bottom: 14px;
}
.aqi-result-label {
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #94a3b8;
    margin-bottom: 6px;
}
.aqi-result-num {
    font-size: 38px;
    font-weight: 700;
    line-height: 1;
    margin-bottom: 4px;
}
.aqi-result-cat {
    font-size: 14px;
    font-weight: 600;
}

/* ── DISEASE ROWS ── */
.disease-section-title {
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #94a3b8;
    margin: 6px 0 12px;
}
.disease-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 16px 0;
    border-bottom: 1px solid #f1f5f9;
}
.disease-item:last-child { border-bottom: none; }
.disease-name  { font-size: 15px; font-weight: 600; color: #1e293b; margin-bottom: 3px; }
.disease-blurb { font-size: 13px; color: #64748b; }
.badge {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    font-size: 12px;
    font-weight: 600;
    padding: 5px 13px;
    border-radius: 20px;
    white-space: nowrap;
    flex-shrink: 0;
    margin-left: 16px;
}
.badge-high { background: #fff1f2; color: #e11d48; border: 1px solid #fecdd3; }
.badge-low  { background: #f0fdf4; color: #16a34a; border: 1px solid #bbf7d0; }

/* ── EXPANDERS ── */
[data-testid="stExpander"] {
    background: #f8fafc !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 10px !important;
    margin: 0 0 8px !important;
}
[data-testid="stExpander"] summary {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 13px !important;
    color: #475569 !important;
    font-weight: 500 !important;
    padding: 12px 16px !important;
}

/* number inputs */
[data-testid="stNumberInput"] input {
    background: #f8fafc !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 8px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 13px !important;
    color: #1e293b !important;
}
[data-testid="stNumberInput"] label {
    font-size: 12px !important;
    color: #64748b !important;
    font-family: 'DM Sans', sans-serif !important;
}

/* columns gap fix */
[data-testid="column"] { padding: 0 6px !important; }

/* ── FOOTER ── */
.footer {
    max-width: 900px;
    margin: 0 auto;
    padding: 20px 24px 40px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    border-top: 1px solid #e2e8f0;
}
.footer-creator { display: flex; align-items: center; gap: 12px; }
.footer-name    { font-size: 15px; font-weight: 600; color: #1e293b; }
.footer-role    { font-size: 12px; color: #94a3b8; margin-top: 2px; }
.footer-center  { font-size: 12px; color: #94a3b8; }
.footer-btn {
    font-size: 13px;
    font-weight: 600;
    color: #1a3a5c;
    text-decoration: none;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 8px 18px;
    background: #fff;
}
</style>
""", unsafe_allow_html=True)

# ── DATA ──────────────────────────────────────────────────────────────────────
disease_labels = {
    'Asthma':                              ['PM2.5','PM10','NO2'],
    'COPD':                                ['PM2.5','PM10','SO2'],
    'Lung Cancer':                         ['PM2.5','PM10','NO2','O3'],
    'Pneumonia & Bronchitis':              ['PM2.5','PM10','SO2','CO'],
    'Reduced Lung Function in Children':   ['PM2.5','NO2','O3'],
    'Heart Attacks':                       ['PM2.5','PM10','CO'],
    'Hypertension':                        ['NO2','SO2','CO'],
    'Strokes':                             ['PM2.5','PM10','NO2'],
    'Arrhythmia':                          ['NO2','SO2','CO'],
    "Alzheimer's & Dementia":              ['PM2.5','NO2'],
    "Parkinson's Disease":                 ['PM2.5','NO2','O3'],
    "Cognitive Impairment in Children":    ['PM2.5','NO2'],
    "Low Birth Weight":                    ['PM2.5','PM10','NO2'],
    "Preterm Births":                      ['PM2.5','PM10','NO2'],
    "Sudden Infant Death Syndrome (SIDS)": ['PM2.5','PM10'],
    "Bladder Cancer":                      ['PM2.5','NO2','O3'],
    "Diabetes":                            ['PM2.5','NO2','SO2'],
    "Eye & Skin Irritation":               ['SO2','O3'],
}
disease_effects = {
    'Asthma':                              "Wheezing, breathlessness, chest tightness.",
    'COPD':                                "Chronic cough, poor airflow, respiratory infections.",
    'Lung Cancer':                         "Persistent cough, chest pain, hoarseness.",
    'Pneumonia & Bronchitis':              "Lung inflammation, fever, difficulty breathing.",
    'Reduced Lung Function in Children':   "Developmental issues, increased asthma risk.",
    'Heart Attacks':                       "Chest pain, shortness of breath — can be fatal.",
    'Hypertension':                        "Increased risk of heart disease and stroke.",
    'Strokes':                             "Paralysis, speech difficulties, long-term disability.",
    'Arrhythmia':                          "Irregular heartbeat, palpitations, dizziness.",
    "Alzheimer's & Dementia":              "Progressive memory loss and confusion.",
    "Parkinson's Disease":                 "Tremors, rigidity, worsening movement.",
    "Cognitive Impairment in Children":    "Impacts on learning, memory, and behaviour.",
    "Low Birth Weight":                    "Higher infection risk, developmental delays.",
    "Preterm Births":                      "Breathing, cardiac and developmental complications.",
    "Sudden Infant Death Syndrome (SIDS)": "Sudden unexplained infant death during sleep.",
    "Bladder Cancer":                      "Blood in urine, pelvic pain, frequent urination.",
    "Diabetes":                            "High blood sugar, fatigue, kidney complications.",
    "Eye & Skin Irritation":              "Redness, itching, burning in eyes and skin.",
}
disease_precautions = {
    'Asthma':                              "Avoid outdoor activity on high-pollution days. Use air purifiers and follow your asthma action plan.",
    'COPD':                                "Stop smoking, avoid polluted areas, keep vaccinations up to date.",
    'Lung Cancer':                         "Avoid smoking and secondhand smoke. Minimise pollutant exposure, get regular checkups.",
    'Pneumonia & Bronchitis':              "Practice good hygiene, avoid sick contacts, get vaccinated.",
    'Reduced Lung Function in Children':   "Limit outdoor activity on bad air days. Use indoor HEPA filters.",
    'Heart Attacks':                       "Heart-healthy diet, regular exercise, monitor blood pressure.",
    'Hypertension':                        "Reduce salt intake, exercise consistently, manage stress.",
    'Strokes':                             "Control blood pressure, quit smoking, maintain healthy weight.",
    'Arrhythmia':                          "Avoid stimulants, manage stress, follow cardiologist advice.",
    "Alzheimer's & Dementia":              "Stay mentally and physically active. Anti-inflammatory diet.",
    "Parkinson's Disease":                 "Regular exercise and strict adherence to prescribed treatments.",
    "Cognitive Impairment in Children":    "Stimulating learning activities, minimise pollutant exposure.",
    "Low Birth Weight":                    "Consistent prenatal care. Avoid smoke and pollution during pregnancy.",
    "Preterm Births":                      "Attend all prenatal appointments, reduce stress, avoid pollutants.",
    "Sudden Infant Death Syndrome (SIDS)": "Place babies on their backs to sleep, avoid soft bedding.",
    "Bladder Cancer":                      "Stop smoking, reduce exposure to industrial chemicals.",
    "Diabetes":                            "Balanced diet, regular exercise, monitor blood glucose.",
    "Eye & Skin Irritation":              "Protective eyewear outdoors, avoid rubbing eyes, gentle skincare.",
}

# ── HELPERS ───────────────────────────────────────────────────────────────────
def aqi_category(v):
    if v < 2: return "Good",     "#16a34a"
    if v < 3: return "Fair",     "#2563eb"
    if v < 4: return "Moderate", "#d97706"
    if v < 5: return "Poor",     "#dc2626"
    return          "Very Poor", "#7c3aed"

def fetch_openweather_data(lat, lon):
    air = requests.get(f"https://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}")
    wx  = requests.get(f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric")
    return (air.json() if air.status_code == 200 else None,
            wx.json()  if wx.status_code  == 200 else None)

def extract_features(air, wx):
    f = {'PM2.5':10.,'PM10':20.,'NO2':10.,'SO2':5.,'CO':0.5,'O3':15.,
         'NH3':1.,'NO':1.,'Temperature':25.,'Humidity':50.,'Wind Speed':2.,'Pressure':1013.}
    if air and "list" in air and air["list"]:
        c = air["list"][0]["components"]
        for k,v in [('PM2.5','pm2_5'),('PM10','pm10'),('NO2','no2'),
                    ('SO2','so2'),('CO','co'),('O3','o3'),('NH3','nh3'),('NO','no')]:
            f[k] = c.get(v, f[k])
    if wx:
        if "main" in wx:
            f['Temperature'] = wx['main'].get('temp',     f['Temperature'])
            f['Humidity']    = wx['main'].get('humidity', f['Humidity'])
            f['Pressure']    = wx['main'].get('pressure', f['Pressure'])
        if "wind" in wx:
            f['Wind Speed'] = wx['wind'].get('speed', f['Wind Speed'])
    return f

# ── SESSION STATE ─────────────────────────────────────────────────────────────
for k, v in [('map_center', DEFAULT_LOCATION), ('marker', DEFAULT_LOCATION),
             ('city_name', 'Chennai, IN'), ('features', None), ('results', None)]:
    if k not in st.session_state:
        st.session_state[k] = v

# ── TOP NAV ───────────────────────────────────────────────────────────────────
st.markdown("""
<div class="topnav">
  <div class="topnav-brand">
    <span style="font-size:24px;">🌏</span>
    <span class="topnav-brand-text">Air Quality &amp; Disease Risk Map</span>
  </div>
  <div class="topnav-pills">
    <div class="topnav-pill">☁ OpenWeather</div>
    <div class="topnav-pill">⚡ XAI Powered</div>
  </div>
</div>
<div class="page">
""", unsafe_allow_html=True)

# ══════════════════════════════
# SECTION 1 — LOCATION
# ══════════════════════════════
st.markdown('<div class="section">', unsafe_allow_html=True)
st.markdown('<div class="section-heading">📍 Location</div>', unsafe_allow_html=True)

col_inp, col_s, col_f = st.columns([5, 1.2, 1.5])
with col_inp:
    search_query = st.text_input("loc", value="Chennai", key="searchbar", label_visibility="collapsed")
with col_s:
    search_btn = st.button("🔍 Search", key="searchbtn")
with col_f:
    fetch_btn = st.button("⟳ Fetch & Predict", key="fetchbtn")

if search_btn and search_query:
    geo = requests.get(
        f"http://api.openweathermap.org/geo/1.0/direct?q={search_query}&limit=1&appid={OPENWEATHER_API_KEY}"
    )
    geo_data = geo.json() if geo.status_code == 200 else []
    if geo_data:
        loc = geo_data[0]
        st.session_state.map_center = (loc['lat'], loc['lon'])
        st.session_state.marker     = (loc['lat'], loc['lon'])
        st.session_state.city_name  = f"{loc['name']}, {loc.get('country','')}"
        st.session_state.features   = None
        st.session_state.results    = None
        st.rerun()
    else:
        st.error("Location not found. Try a different name.")

st.markdown('</div>', unsafe_allow_html=True)  # close section

# ══════════════════════════════
# SECTION 2 — MAP
# ══════════════════════════════
st.markdown('<div class="section" style="padding:20px 20px;">', unsafe_allow_html=True)

m = folium.Map(
    location=st.session_state.map_center,
    zoom_start=7,
    tiles="CartoDB positron",
    control_scale=False,
    attr=" ",
)
folium.Marker(
    location=st.session_state.marker,
    icon=folium.Icon(color='red', icon='map-marker', prefix='fa'),
    popup=st.session_state.city_name,
).add_to(m)

map_data = st_folium(m, width="100%", height=420, returned_objects=["last_clicked"], key="map")

if map_data and map_data.get("last_clicked"):
    clat = map_data["last_clicked"]["lat"]
    clon = map_data["last_clicked"]["lng"]
    if (clat, clon) != st.session_state.marker:
        st.session_state.marker     = (clat, clon)
        st.session_state.map_center = (clat, clon)
        st.session_state.city_name  = f"{clat:.4f}°N, {clon:.4f}°E"
        st.session_state.features   = None
        st.session_state.results    = None
        st.rerun()

st.markdown('</div>', unsafe_allow_html=True)

# ── Fetch & predict logic ─────────────────────────────────────────────────────
if fetch_btn:
    lat, lon = st.session_state.marker
    with st.spinner("Fetching air quality data and running predictions…"):
        air, wx = fetch_openweather_data(lat, lon)
        features = extract_features(air, wx)
        st.session_state.features = features

        aqi_input = [features[k] for k in ['PM2.5','PM10','NO2','SO2','CO','O3']]
        aqi_res   = predict_aqi(aqi_input)
        disease_res = {}
        for disease, feats in disease_labels.items():
            inp = [features[k] for k in feats if k in features]
            disease_res[disease] = predict_disease_with_explanation(inp, disease)
        st.session_state.results = {'aqi': aqi_res, 'diseases': disease_res}
    st.rerun()

f = st.session_state.features
results = st.session_state.results

# ══════════════════════════════
# SECTION 3 — METRICS
# ══════════════════════════════
st.markdown('<div class="section">', unsafe_allow_html=True)
st.markdown('<div class="section-heading">📊 Air Quality Metrics</div>', unsafe_allow_html=True)

def fv(key, dec=1):
    return f"{f[key]:.{dec}f}" if f else "—"

st.markdown(f"""
<div class="metric-grid">
  <div class="metric-card"><div class="metric-label">PM2.5</div><div class="metric-val">{fv('PM2.5')}</div></div>
  <div class="metric-card"><div class="metric-label">PM10</div><div class="metric-val">{fv('PM10')}</div></div>
  <div class="metric-card"><div class="metric-label">NO2</div><div class="metric-val">{fv('NO2')}</div></div>
  <div class="metric-card"><div class="metric-label">SO2</div><div class="metric-val">{fv('SO2')}</div></div>
  <div class="metric-card"><div class="metric-label">CO</div><div class="metric-val">{fv('CO')}</div></div>
  <div class="metric-card"><div class="metric-label">O3</div><div class="metric-val">{fv('O3')}</div></div>
  <div class="metric-card"><div class="metric-label">Temperature</div><div class="metric-val">{fv('Temperature')}°C</div></div>
  <div class="metric-card"><div class="metric-label">Humidity</div><div class="metric-val">{fv('Humidity', 0)}%</div></div>
</div>
""", unsafe_allow_html=True)

if f:
    with st.expander("⚙ Edit feature values before re-running"):
        c1, c2 = st.columns(2)
        keys = list(f.keys())
        for i, k in enumerate(keys):
            col = c1 if i < len(keys)//2 else c2
            f[k] = col.number_input(k, value=float(f[k]), key=f"feat_{k}")
        st.session_state.features = f

st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════
# SECTION 4 — RESULTS
# ══════════════════════════════
st.markdown('<div class="section">', unsafe_allow_html=True)
st.markdown("""
<div style="display:flex;align-items:center;gap:10px;margin-bottom:20px;">
  <span style="font-size:20px;">📈</span>
  <span style="font-size:17px;font-weight:700;color:#1e293b;">Prediction Results</span>
</div>
""", unsafe_allow_html=True)

if not results:
    st.markdown("""
    <div class="steps-bar">
      <div class="step-item"><div class="step-num">1</div> Search or click the map</div>
      <div class="step-item"><div class="step-num">2</div> Review metrics above</div>
      <div class="step-item"><div class="step-num">3</div> Click Fetch &amp; Predict</div>
    </div>
    <div style="text-align:center;padding:36px 0;color:#94a3b8;font-size:14px;">
        No predictions yet — fetch data to see AQI and disease risk results.
    </div>
    """, unsafe_allow_html=True)
else:
    # AQI
    aqi_val, lime_exp, shap_exp = results['aqi'] if results.get('aqi') else (None, None, None)
    if aqi_val is not None:
        cat, color = aqi_category(aqi_val)
        st.markdown(f"""
        <div class="aqi-result-card">
          <div class="aqi-result-label">Predicted AQI</div>
          <div class="aqi-result-num" style="color:{color};">{aqi_val:.2f}</div>
          <div class="aqi-result-cat" style="color:{color};">{cat}</div>
        </div>
        """, unsafe_allow_html=True)
        with st.expander("Show XAI details — AQI"):
            st.write("**LIME explanation:**", lime_exp or "N/A")
            st.write("**SHAP explanation:**", shap_exp or "N/A")

    # disease breakdown
    st.markdown('<div class="disease-section-title" style="margin-top:20px;">Disease Risk Breakdown</div>', unsafe_allow_html=True)

    disease_res = results.get('diseases', {})
    sorted_diseases = sorted(
        disease_labels.keys(),
        key=lambda d: 0 if (disease_res.get(d) and disease_res[d]['prediction'] == 1) else 1
    )

    for disease in sorted_diseases:
        res = disease_res.get(disease)
        if not res:
            continue
        is_high   = res['prediction'] == 1
        badge_cls = "badge-high" if is_high else "badge-low"
        badge_txt = "⚠ HIGH"     if is_high else "✓ LOW"
        effect    = disease_effects.get(disease, "")

        st.markdown(f"""
        <div class="disease-item">
          <div>
            <div class="disease-name">{disease}</div>
            <div class="disease-blurb">{effect}</div>
          </div>
          <div class="badge {badge_cls}">{badge_txt}</div>
        </div>
        """, unsafe_allow_html=True)

        with st.expander(f"Full details — {disease}"):
            conf = max(res['probability'])
            acc  = res['accuracy'] if res['accuracy'] is not None else "N/A"
            m1, m2, m3 = st.columns(3)
            m1.metric("Risk",       "HIGH" if is_high else "LOW")
            m2.metric("Confidence", f"{conf:.3f}")
            m3.metric("Accuracy",   str(acc))

            st.markdown(f"**Health effects:** {disease_effects.get(disease,'')}")
            st.markdown(f"**Precautions:** {disease_precautions.get(disease,'')}")

            if res.get('risk_factors'):
                st.markdown("**Key risk factors:**")
                for factor in res['risk_factors'][:5]:
                    direction = "increases" if factor['type'] == 'risk_increasing' else "decreases"
                    st.markdown(f"- `{factor['feature']}` **{direction}** risk — contribution: `{factor['contribution']:.4f}`")

            if res.get('recommendations'):
                st.markdown("**Recommendations:**")
                for rec in res['recommendations']:
                    st.markdown(f"- {rec}")

            with st.expander("LIME / SHAP explanation"):
                st.write("**LIME:**", res.get('lime_explanation') or "N/A")
                st.write("**SHAP:**", res.get('shap_explanation') or "N/A")

st.markdown('</div>', unsafe_allow_html=True)  # close results section
st.markdown('</div>', unsafe_allow_html=True)  # close page

# ── FOOTER ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="footer">
  <div class="footer-creator">
    <span style="font-size:32px;">🌷</span>
    <div>
      <div class="footer-name">Keerthishree Kesavan</div>
      <div class="footer-role">AI/ML Focused Full Stack Developer</div>
    </div>
  </div>
  <div class="footer-center">Powered by OpenWeather &amp; Explainable AI</div>
  <a class="footer-btn" href="https://github.com/Keerthishreekesavan" target="_blank">⎇ GitHub Profile</a>
</div>
""", unsafe_allow_html=True)