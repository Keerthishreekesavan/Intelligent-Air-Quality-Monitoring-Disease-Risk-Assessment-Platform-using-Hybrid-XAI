import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
from models import predict_disease_with_explanation, predict_aqi

# ── CONFIG ────────────────────────────────────────────────────────────────────
OPENWEATHER_API_KEY = st.secrets["OPENWEATHER_API_KEY"]
DEFAULT_LOCATION = (13.0827, 80.2707)

st.set_page_config(
    page_title="Air Quality & Disease Risk Map",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&display=swap');

html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
    font-family: 'DM Sans', sans-serif !important;
    background: #f0f4f8 !important;
    margin: 0; padding: 0;
}
[data-testid="stHeader"]  { display: none !important; }
[data-testid="stSidebar"] { display: none !important; }
[data-testid="stBottom"]  { display: none !important; }
.block-container { padding: 0 !important; max-width: 100vw !important; }

/* ── top nav ── */
.topnav {
    background: #1a3a5c;
    padding: 0 28px;
    height: 52px;
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.topnav-brand { display: flex; align-items: center; gap: 10px; }
.topnav-brand-text { font-size: 16px; font-weight: 600; color: #fff; }
.topnav-pills { display: flex; gap: 8px; }
.topnav-pill {
    display: flex; align-items: center; gap: 6px;
    background: rgba(255,255,255,0.1);
    border: 1px solid rgba(255,255,255,0.15);
    border-radius: 20px;
    padding: 5px 14px;
    font-size: 12px;
    color: #cbd5e1;
    font-family: 'DM Sans', sans-serif;
}

/* ── main layout ── */
.main-layout {
    display: grid;
    grid-template-columns: 320px 1fr;
    gap: 0;
    height: calc(100vh - 52px);
    overflow: hidden;
}

/* ── left column ── */
.left-col {
    background: #fff;
    border-right: 1px solid #e2e8f0;
    display: flex;
    flex-direction: column;
    overflow-y: auto;
    padding: 20px 18px;
    gap: 16px;
}
.loc-label {
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #94a3b8;
    margin-bottom: 6px;
}

/* streamlit input/button overrides */
[data-testid="stTextInput"] input {
    border: 1px solid #e2e8f0 !important;
    border-radius: 8px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 14px !important;
    color: #1e293b !important;
    background: #f8fafc !important;
    padding: 8px 12px !important;
}
[data-testid="stTextInput"] input:focus {
    border-color: #1a3a5c !important;
    box-shadow: 0 0 0 3px rgba(26,58,92,0.08) !important;
}
[data-testid="stTextInput"] label { display: none !important; }

div[data-testid="stButton"] > button {
    width: 100% !important;
    background: #1a3a5c !important;
    color: #fff !important;
    border: none !important;
    border-radius: 10px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 600 !important;
    font-size: 14px !important;
    padding: 10px 0 !important;
    letter-spacing: 0.01em !important;
    transition: background 0.2s !important;
    margin-top: 2px !important;
}
div[data-testid="stButton"] > button:hover { background: #254e7a !important; }

/* ── metric mini cards ── */
.mini-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
    margin-top: 4px;
}
.mini-card {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 10px 12px;
}
.mini-card-label {
    font-size: 10px;
    font-weight: 600;
    color: #94a3b8;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-bottom: 3px;
}
.mini-card-val {
    font-size: 16px;
    font-weight: 600;
    color: #1e293b;
}

/* ── right column ── */
.right-col {
    background: #f0f4f8;
    display: flex;
    flex-direction: column;
    overflow: hidden;
}

/* ── steps bar ── */
.steps-bar {
    background: #fff;
    border-bottom: 1px solid #e2e8f0;
    padding: 10px 22px;
    display: flex;
    align-items: center;
    gap: 20px;
}
.step-item {
    display: flex;
    align-items: center;
    gap: 7px;
    font-size: 13px;
    color: #64748b;
}
.step-num {
    width: 20px; height: 20px;
    border-radius: 50%;
    background: #1a3a5c;
    color: #fff;
    font-size: 11px;
    font-weight: 700;
    display: flex; align-items: center; justify-content: center;
}

/* ── pollutant bar row ── */
.poll-bar-row {
    background: #fff;
    border-bottom: 1px solid #e2e8f0;
    padding: 10px 22px;
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 8px;
}
.poll-bar-card {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 8px 12px;
    text-align: center;
}
.poll-bar-name { font-size: 11px; font-weight: 600; color: #94a3b8; letter-spacing: 0.07em; }
.poll-bar-val  { font-size: 15px; font-weight: 600; color: #1e293b; margin-top: 2px; }

/* ── results area ── */
.results-area {
    flex: 1;
    overflow-y: auto;
    padding: 18px 22px;
}
.results-area::-webkit-scrollbar { width: 4px; }
.results-area::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 2px; }

/* ── aqi card ── */
.aqi-card {
    background: #fff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 16px 20px;
    margin-bottom: 14px;
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.aqi-card-left {}
.aqi-card-label { font-size: 11px; font-weight: 600; letter-spacing: 0.1em; color: #94a3b8; text-transform: uppercase; margin-bottom: 4px; }
.aqi-card-num   { font-size: 30px; font-weight: 700; line-height: 1; }
.aqi-card-cat   { font-size: 13px; font-weight: 500; margin-top: 3px; }

/* ── section title ── */
.section-title {
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.09em;
    text-transform: uppercase;
    color: #475569;
    margin-bottom: 10px;
    margin-top: 4px;
}

/* ── disease row ── */
.disease-list {
    background: #fff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    overflow: hidden;
}
.disease-row {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    padding: 14px 18px;
    border-bottom: 1px solid #f1f5f9;
    cursor: pointer;
    transition: background 0.15s;
}
.disease-row:last-child { border-bottom: none; }
.disease-row:hover { background: #f8fafc; }
.disease-row-left {}
.disease-name { font-size: 14px; font-weight: 600; color: #1e293b; margin-bottom: 2px; }
.disease-effect { font-size: 12px; color: #64748b; }
.badge {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    font-size: 11px;
    font-weight: 600;
    padding: 4px 10px;
    border-radius: 20px;
    white-space: nowrap;
    flex-shrink: 0;
    margin-left: 12px;
    margin-top: 2px;
}
.badge-high { background: #fff1f2; color: #e11d48; border: 1px solid #fecdd3; }
.badge-low  { background: #f0fdf4; color: #16a34a; border: 1px solid #bbf7d0; }

/* ── expander overrides ── */
[data-testid="stExpander"] {
    background: #f8fafc !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 10px !important;
    margin: 4px 0 0 0 !important;
}
[data-testid="stExpander"] summary {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 13px !important;
    color: #475569 !important;
    font-weight: 500 !important;
}

/* number inputs */
[data-testid="stNumberInput"] input {
    background: #f8fafc !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 7px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 13px !important;
    color: #1e293b !important;
}
[data-testid="stNumberInput"] label {
    font-size: 12px !important;
    color: #64748b !important;
    font-family: 'DM Sans', sans-serif !important;
}

/* ── footer ── */
.footer-bar {
    background: #fff;
    border-top: 1px solid #e2e8f0;
    padding: 12px 28px;
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.footer-creator { display: flex; align-items: center; gap: 10px; }
.footer-name { font-size: 14px; font-weight: 600; color: #1e293b; }
.footer-role { font-size: 12px; color: #94a3b8; margin-top: 1px; }
.footer-center { font-size: 12px; color: #94a3b8; }

[data-testid="stSpinner"] { color: #1a3a5c !important; }
[data-testid="column"] { padding: 0 4px !important; }
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
    'Lung Cancer':                         "Avoid smoking and secondhand smoke. Minimise pollutant exposure and get regular checkups.",
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
    <span style="font-size:22px;">🌏</span>
    <span class="topnav-brand-text">Air Quality &amp; Disease Risk Map</span>
  </div>
  <div class="topnav-pills">
    <div class="topnav-pill">☁ OpenWeather</div>
    <div class="topnav-pill">⚡ XAI Powered</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── TWO COLUMNS ───────────────────────────────────────────────────────────────
left_col, right_col = st.columns([32, 68], gap="small")

# ══════════════════════════════
#  LEFT
# ══════════════════════════════
with left_col:
    st.markdown('<div class="loc-label">Location</div>', unsafe_allow_html=True)
    search_query = st.text_input("loc", value="Chennai", key="searchbar", label_visibility="collapsed")

    col_s, col_b = st.columns([3, 2])
    with col_s:
        search_btn = st.button("🔍 Search", key="searchbtn")
    with col_b:
        fetch_btn = st.button("⟳ Fetch & Predict", key="fetchbtn")

    # handle search
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
        else:
            st.error("Location not found.")

    # map
    m = folium.Map(location=st.session_state.map_center, zoom_start=7,
                   tiles="CartoDB positron", control_scale=False)
    folium.Marker(
        location=st.session_state.marker,
        icon=folium.Icon(color='red', icon='map-marker', prefix='fa'),
        popup=st.session_state.city_name,
    ).add_to(m)
    map_data = st_folium(m, width="100%", height=240, returned_objects=["last_clicked"], key="map")

    # map click
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

    # mini metric cards
    f = st.session_state.features
    pm25 = f"{ f['PM2.5']:.1f}" if f else "—"
    pm10 = f"{ f['PM10']:.1f}"  if f else "—"
    no2  = f"{ f['NO2']:.1f}"   if f else "—"
    aqi_disp = "—"
    if st.session_state.results and st.session_state.results.get('aqi'):
        aqi_disp = f"{st.session_state.results['aqi'][0]:.2f}"

    st.markdown(f"""
    <div class="mini-grid">
      <div class="mini-card"><div class="mini-card-label">PM2.5</div><div class="mini-card-val">{pm25}</div></div>
      <div class="mini-card"><div class="mini-card-label">PM10</div><div class="mini-card-val">{pm10}</div></div>
      <div class="mini-card"><div class="mini-card-label">NO2</div><div class="mini-card-val">{no2}</div></div>
      <div class="mini-card"><div class="mini-card-label">AQI</div><div class="mini-card-val" style="color:#1a3a5c;">{aqi_disp}</div></div>
    </div>
    """, unsafe_allow_html=True)

    # fetch & predict
    if fetch_btn or (map_data and map_data.get("last_clicked") and st.session_state.features is None):
        lat, lon = st.session_state.marker
        with st.spinner("Fetching data…"):
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

    # editable features
    if st.session_state.features:
        with st.expander("⚙ Edit feature values"):
            features = st.session_state.features
            c1, c2 = st.columns(2)
            keys = list(features.keys())
            for i, k in enumerate(keys):
                col = c1 if i < len(keys)//2 else c2
                features[k] = col.number_input(k, value=float(features[k]), key=f"feat_{k}")
            st.session_state.features = features

# ══════════════════════════════
#  RIGHT
# ══════════════════════════════
with right_col:
    # steps bar
    st.markdown("""
    <div class="steps-bar">
      <span style="font-size:16px;color:#94a3b8;">ℹ</span>
      <div class="step-item"><div class="step-num">1</div> Search or click map</div>
      <div class="step-item"><div class="step-num">2</div> Review metrics</div>
      <div class="step-item"><div class="step-num">3</div> Fetch &amp; predict</div>
    </div>
    """, unsafe_allow_html=True)

    # pollutant bar row
    f = st.session_state.features
    so2_v  = f"{f['SO2']:.1f}"   if f else "—"
    co_v   = f"{f['CO']:.1f}"    if f else "—"
    o3_v   = f"{f['O3']:.1f}"    if f else "—"
    temp_v = f"{f['Temperature']:.1f}°C" if f else "—"
    st.markdown(f"""
    <div class="poll-bar-row">
      <div class="poll-bar-card"><div class="poll-bar-name">SO2</div><div class="poll-bar-val">{so2_v}</div></div>
      <div class="poll-bar-card"><div class="poll-bar-name">CO</div><div class="poll-bar-val">{co_v}</div></div>
      <div class="poll-bar-card"><div class="poll-bar-name">O3</div><div class="poll-bar-val">{o3_v}</div></div>
      <div class="poll-bar-card"><div class="poll-bar-name">TEMP</div><div class="poll-bar-val">{temp_v}</div></div>
    </div>
    """, unsafe_allow_html=True)

    results = st.session_state.results

    # results area
    st.markdown('<div style="padding:18px 4px 0;">', unsafe_allow_html=True)
    st.markdown("""
    <div style="display:flex;align-items:center;gap:8px;margin-bottom:14px;">
      <span style="font-size:18px;">📊</span>
      <span style="font-size:17px;font-weight:700;color:#1e293b;">Prediction results</span>
    </div>
    """, unsafe_allow_html=True)

    if results:
        # AQI card
        aqi_val, lime_exp, shap_exp = results['aqi'] if results.get('aqi') else (None, None, None)
        if aqi_val is not None:
            cat, color = aqi_category(aqi_val)
            st.markdown(f"""
            <div class="aqi-card">
              <div class="aqi-card-left">
                <div class="aqi-card-label">Predicted AQI</div>
                <div class="aqi-card-num" style="color:{color};">{aqi_val:.2f}</div>
                <div class="aqi-card-cat" style="color:{color};">{cat}</div>
              </div>
            </div>
            """, unsafe_allow_html=True)
            with st.expander("Show XAI details — AQI"):
                st.write("**LIME explanation:**", lime_exp or "N/A")
                st.write("**SHAP explanation:**", shap_exp or "N/A")

        # disease list
        st.markdown('<div class="section-title">Disease risk breakdown</div>', unsafe_allow_html=True)

        disease_res = results.get('diseases', {})
        sorted_diseases = sorted(
            disease_labels.keys(),
            key=lambda d: 0 if (disease_res.get(d) and disease_res[d]['prediction'] == 1) else 1
        )

        st.markdown('<div class="disease-list">', unsafe_allow_html=True)
        for disease in sorted_diseases:
            res = disease_res.get(disease)
            if not res:
                continue
            is_high   = res['prediction'] == 1
            badge_cls = "badge-high" if is_high else "badge-low"
            badge_txt = "⚠ HIGH"     if is_high else "✓ LOW"
            effect    = disease_effects.get(disease, "")

            st.markdown(f"""
            <div class="disease-row">
              <div class="disease-row-left">
                <div class="disease-name">{disease}</div>
                <div class="disease-effect">{effect}</div>
              </div>
              <div class="badge {badge_cls}">{badge_txt}</div>
            </div>
            """, unsafe_allow_html=True)

            with st.expander(f"Full details — {disease}"):
                hi_lo = "HIGH RISK" if is_high else "LOW RISK"
                conf  = max(res['probability'])
                acc   = res['accuracy'] if res['accuracy'] is not None else "N/A"

                col1, col2 = st.columns(2)
                col1.metric("Risk level",  hi_lo)
                col2.metric("Confidence", f"{conf:.3f}")
                col1.metric("Model accuracy", str(acc))

                st.markdown(f"**Health effects:** {disease_effects.get(disease,'')}")
                st.markdown(f"**Precautions:** {disease_precautions.get(disease,'')}")

                if res.get('risk_factors'):
                    st.markdown("**Key risk factors:**")
                    for factor in res['risk_factors'][:5]:
                        direction = "increases" if factor['type'] == 'risk_increasing' else "decreases"
                        st.markdown(f"- `{factor['feature']}` **{direction}** risk &nbsp;(contribution: `{factor['contribution']:.4f}`)")

                if res.get('recommendations'):
                    st.markdown("**Recommendations:**")
                    for rec in res['recommendations']:
                        st.markdown(f"- {rec}")

                with st.expander("LIME / SHAP explanation"):
                    st.write("**LIME:**", res.get('lime_explanation') or "N/A")
                    st.write("**SHAP:**", res.get('shap_explanation') or "N/A")

        st.markdown('</div>', unsafe_allow_html=True)

    else:
        st.markdown("""
        <div style="text-align:center;padding:50px 20px;color:#94a3b8;font-size:14px;">
            Search a city or click the map, then click <b>⟳ Fetch &amp; Predict</b>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

# ── FOOTER ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="footer-bar">
  <div class="footer-creator">
    <span style="font-size:28px;">🌷</span>
    <div>
      <div class="footer-name">Keerthishree Kesavan</div>
      <div class="footer-role">AI/ML Focused Full Stack Developer</div>
    </div>
  </div>
  <div class="footer-center">Powered by OpenWeather &amp; Explainable AI</div>
  <a href="https://github.com/Keerthishreekesavan" target="_blank"
     style="font-size:13px;font-weight:600;color:#1a3a5c;text-decoration:none;
            border:1px solid #e2e8f0;border-radius:8px;padding:7px 16px;">
    ⎇ GitHub Profile
  </a>
</div>
""", unsafe_allow_html=True)