import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
from models import predict_disease_with_explanation, predict_aqi
import os

# ── CONFIG ────────────────────────────────────────────────────────────────────
OPENWEATHER_API_KEY = st.secrets["OPENWEATHER_API_KEY"]
DEFAULT_LOCATION = (13.0827, 80.2707)  # Chennai

st.set_page_config(
    page_title="AirRisk AI",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── GLOBAL CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

/* ── reset ── */
html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
    margin: 0 !important; padding: 0 !important;
    background: #060d1a !important;
    font-family: 'Syne', sans-serif;
    overflow: hidden;
}
[data-testid="stHeader"] { display: none !important; }
[data-testid="stSidebar"] { display: none !important; }
[data-testid="stBottom"] { display: none !important; }
.block-container {
    padding: 0 !important;
    max-width: 100vw !important;
}

/* ── layout shell ── */
.shell {
    display: grid;
    grid-template-columns: 300px 1fr;
    height: 100vh;
    width: 100vw;
    overflow: hidden;
}

/* ── left panel ── */
.left-panel {
    background: #060d1a;
    border-right: 1px solid rgba(74,222,128,0.12);
    display: flex;
    flex-direction: column;
    height: 100vh;
    overflow: hidden;
}
.left-header {
    padding: 22px 20px 16px;
    border-bottom: 1px solid rgba(255,255,255,0.05);
}
.logo-tag {
    font-size: 10px;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: #4ade80;
    font-family: 'JetBrains Mono', monospace;
    margin-bottom: 4px;
}
.app-title {
    font-size: 18px;
    font-weight: 700;
    color: #f0fdf4;
    line-height: 1.2;
}
.app-subtitle {
    font-size: 11px;
    color: #4b5563;
    margin-top: 3px;
    font-family: 'JetBrains Mono', monospace;
}

/* ── search section ── */
.search-section {
    padding: 14px 16px;
    border-bottom: 1px solid rgba(255,255,255,0.05);
}

/* streamlit widget overrides inside left panel */
[data-testid="stTextInput"] input {
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid rgba(74,222,128,0.2) !important;
    border-radius: 8px !important;
    color: #e2e8f0 !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 13px !important;
    padding: 8px 12px !important;
}
[data-testid="stTextInput"] input:focus {
    border-color: rgba(74,222,128,0.6) !important;
    box-shadow: 0 0 0 2px rgba(74,222,128,0.1) !important;
}
[data-testid="stTextInput"] label { color: #4b5563 !important; font-size: 11px !important; }

div[data-testid="stButton"] > button {
    width: 100% !important;
    background: #4ade80 !important;
    color: #052e16 !important;
    border: none !important;
    border-radius: 8px !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important;
    font-size: 13px !important;
    padding: 9px 0 !important;
    letter-spacing: 0.04em !important;
    transition: background 0.2s !important;
    margin-top: 6px !important;
}
div[data-testid="stButton"] > button:hover {
    background: #86efac !important;
}

/* ── aqi display ── */
.aqi-block {
    padding: 16px 20px;
    border-bottom: 1px solid rgba(255,255,255,0.05);
}
.aqi-label {
    font-size: 10px;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: #4b5563;
    font-family: 'JetBrains Mono', monospace;
    margin-bottom: 6px;
}
.aqi-number {
    font-size: 42px;
    font-weight: 700;
    line-height: 1;
    margin-bottom: 2px;
}
.aqi-cat {
    font-size: 13px;
    font-family: 'JetBrains Mono', monospace;
    margin-bottom: 10px;
}
.aqi-bar-wrap {
    height: 4px;
    background: rgba(255,255,255,0.07);
    border-radius: 2px;
    overflow: hidden;
    margin-bottom: 10px;
}
.aqi-bar-fill { height: 100%; border-radius: 2px; transition: width 0.6s ease; }
.aqi-pills {
    display: flex; gap: 6px; flex-wrap: wrap;
}
.aqi-pill {
    font-size: 10px;
    font-family: 'JetBrains Mono', monospace;
    padding: 3px 8px;
    border-radius: 20px;
    background: rgba(255,255,255,0.06);
    color: #64748b;
    border: 1px solid rgba(255,255,255,0.06);
}

/* ── pollutants ── */
.poll-block {
    padding: 14px 20px;
    flex: 1;
    overflow-y: auto;
    border-bottom: 1px solid rgba(255,255,255,0.05);
}
.poll-block::-webkit-scrollbar { width: 3px; }
.poll-block::-webkit-scrollbar-track { background: transparent; }
.poll-block::-webkit-scrollbar-thumb { background: rgba(74,222,128,0.2); border-radius: 2px; }
.section-label {
    font-size: 10px;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: #4b5563;
    font-family: 'JetBrains Mono', monospace;
    margin-bottom: 10px;
}
.poll-row {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 5px 0;
}
.poll-name {
    font-size: 12px;
    color: #64748b;
    font-family: 'JetBrains Mono', monospace;
    width: 44px;
    flex-shrink: 0;
}
.poll-bar-wrap {
    flex: 1;
    height: 3px;
    background: rgba(255,255,255,0.06);
    border-radius: 2px;
    overflow: hidden;
}
.poll-bar-fill { height: 100%; border-radius: 2px; }
.poll-val {
    font-size: 11px;
    color: #94a3b8;
    font-family: 'JetBrains Mono', monospace;
    width: 52px;
    text-align: right;
    flex-shrink: 0;
}

/* ── left footer ── */
.left-footer {
    padding: 12px 20px;
    border-top: 1px solid rgba(255,255,255,0.05);
}
.footer-loc {
    font-size: 11px;
    color: #374151;
    font-family: 'JetBrains Mono', monospace;
}
.footer-coords {
    font-size: 10px;
    color: #1f2937;
    font-family: 'JetBrains Mono', monospace;
    margin-top: 2px;
}
.footer-credit {
    font-size: 10px;
    color: #1f2937;
    margin-top: 8px;
    display: flex;
    align-items: center;
    gap: 6px;
}

/* ── right panel ── */
.right-panel {
    display: flex;
    flex-direction: column;
    height: 100vh;
    background: #0d1829;
    overflow: hidden;
}
.map-area {
    flex: 1;
    position: relative;
    overflow: hidden;
}

/* ── risk strip ── */
.risk-strip {
    background: #060d1a;
    border-top: 1px solid rgba(74,222,128,0.12);
    padding: 14px 18px 10px;
    max-height: 42vh;
    overflow-y: auto;
}
.risk-strip::-webkit-scrollbar { width: 3px; }
.risk-strip::-webkit-scrollbar-thumb { background: rgba(74,222,128,0.2); border-radius: 2px; }
.risk-strip-title {
    font-size: 10px;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: #4b5563;
    font-family: 'JetBrains Mono', monospace;
    margin-bottom: 10px;
}
.risk-chips {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
    gap: 8px;
}
.risk-chip {
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 8px;
    padding: 10px 12px;
    background: rgba(255,255,255,0.02);
    cursor: pointer;
    transition: border-color 0.2s, background 0.2s;
}
.risk-chip:hover {
    border-color: rgba(74,222,128,0.3);
    background: rgba(74,222,128,0.04);
}
.risk-chip.high-risk { border-color: rgba(239,68,68,0.25); }
.risk-chip.high-risk:hover { border-color: rgba(239,68,68,0.5); }
.chip-name {
    font-size: 12px;
    font-weight: 600;
    color: #cbd5e1;
    margin-bottom: 5px;
}
.chip-badge {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    font-size: 10px;
    font-family: 'JetBrains Mono', monospace;
    padding: 2px 8px;
    border-radius: 20px;
    font-weight: 500;
}
.badge-high { background: rgba(239,68,68,0.15); color: #fca5a5; border: 1px solid rgba(239,68,68,0.2); }
.badge-low  { background: rgba(74,222,128,0.1);  color: #86efac;  border: 1px solid rgba(74,222,128,0.15); }

/* ── expander overrides ── */
[data-testid="stExpander"] {
    background: rgba(255,255,255,0.02) !important;
    border: 1px solid rgba(255,255,255,0.07) !important;
    border-radius: 8px !important;
    margin-bottom: 6px !important;
}
[data-testid="stExpander"] summary {
    color: #94a3b8 !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 12px !important;
}
[data-testid="stExpander"] > div > div {
    color: #64748b !important;
    font-size: 12px !important;
}

/* ── number inputs (editable features) ── */
[data-testid="stNumberInput"] input {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    color: #94a3b8 !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 12px !important;
    border-radius: 6px !important;
}
[data-testid="stNumberInput"] label {
    color: #4b5563 !important;
    font-size: 11px !important;
    font-family: 'JetBrains Mono', monospace !important;
}

/* ── info / error / success ── */
[data-testid="stAlert"] {
    background: rgba(74,222,128,0.05) !important;
    border: 1px solid rgba(74,222,128,0.15) !important;
    color: #86efac !important;
    border-radius: 8px !important;
    font-size: 12px !important;
}

/* scrollbar for folium iframe area */
.map-area iframe {
    border: none !important;
    width: 100% !important;
    height: 100% !important;
}

/* spinner */
[data-testid="stSpinner"] { color: #4ade80 !important; }

/* streamlit columns reset */
[data-testid="column"] { padding: 0 4px !important; }
</style>
""", unsafe_allow_html=True)


# ── HELPERS ───────────────────────────────────────────────────────────────────
def aqi_category(aqi):
    if aqi < 2:   return "Good",      "#4ade80", 20
    if aqi < 3:   return "Fair",      "#60a5fa", 40
    if aqi < 4:   return "Moderate",  "#fb923c", 55
    if aqi < 5:   return "Poor",      "#f87171", 75
    return              "Very Poor",  "#ef4444", 95

def fetch_openweather_data(lat, lon):
    air_url     = f"https://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}"
    weather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric"
    air_resp     = requests.get(air_url)
    weather_resp = requests.get(weather_url)
    return (air_resp.json()     if air_resp.status_code == 200     else None,
            weather_resp.json() if weather_resp.status_code == 200 else None)

def extract_features(air_data, weather_data):
    f = {'PM2.5':10.0,'PM10':20.0,'NO2':10.0,'SO2':5.0,'CO':0.5,'O3':15.0,
         'NH3':1.0,'NO':1.0,'Temperature':25.0,'Humidity':50.0,'Wind Speed':2.0,'Pressure':1013.0}
    if air_data and "list" in air_data and air_data["list"]:
        c = air_data["list"][0]["components"]
        f['PM2.5'] = c.get('pm2_5', f['PM2.5']); f['PM10'] = c.get('pm10', f['PM10'])
        f['NO2']   = c.get('no2',   f['NO2']);    f['SO2']  = c.get('so2',  f['SO2'])
        f['CO']    = c.get('co',    f['CO']);      f['O3']   = c.get('o3',   f['O3'])
        f['NH3']   = c.get('nh3',   f['NH3']);     f['NO']   = c.get('no',   f['NO'])
    if weather_data and "main" in weather_data:
        m = weather_data['main']
        f['Temperature'] = m.get('temp',     f['Temperature'])
        f['Humidity']    = m.get('humidity', f['Humidity'])
        f['Pressure']    = m.get('pressure', f['Pressure'])
    if weather_data and "wind" in weather_data:
        f['Wind Speed'] = weather_data['wind'].get('speed', f['Wind Speed'])
    return f

def pollutant_color(name, val):
    thresholds = {'PM2.5':25,'PM10':50,'NO2':40,'SO2':20,'CO':10000,'O3':100}
    limit = thresholds.get(name, 50)
    ratio = min(val / limit, 1.0) if limit else 0
    if ratio < 0.4:  return "#4ade80"
    if ratio < 0.7:  return "#facc15"
    if ratio < 0.9:  return "#fb923c"
    return "#ef4444"

def bar_pct(name, val):
    refs = {'PM2.5':80,'PM10':150,'NO2':200,'SO2':100,'CO':300000,'O3':240,'NH3':200,'NO':100}
    return min(int(val / refs.get(name, 100) * 100), 100)


# ── DATA DEFINITIONS ──────────────────────────────────────────────────────────
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
    'Asthma':                              "Wheezing, breathlessness, chest tightness, and coughing. Severe attacks may need emergency care.",
    'COPD':                                "Long-term breathing problems, chronic cough, mucus build-up, and frequent respiratory infections.",
    'Lung Cancer':                         "Persistent cough, chest pain, hoarseness, and weight loss. Early detection is critical.",
    'Pneumonia & Bronchitis':              "Lung inflammation, cough, fever, and difficulty breathing. Severe cases can be life-threatening.",
    'Reduced Lung Function in Children':   "Developmental issues, increased asthma risk, and reduced physical activity capacity.",
    'Heart Attacks':                       "Chest pain, shortness of breath — can be fatal without immediate treatment.",
    'Hypertension':                        "Elevated blood pressure increases risk of heart disease, stroke, and kidney damage.",
    'Strokes':                             "Paralysis, speech difficulties, and long-term neurological disability.",
    'Arrhythmia':                          "Irregular heartbeat, palpitations, dizziness, and heightened stroke risk.",
    "Alzheimer's & Dementia":              "Progressive memory loss, confusion, and behavioral changes.",
    "Parkinson's Disease":                 "Tremors, rigidity, and worsening movement and coordination.",
    "Cognitive Impairment in Children":    "Impacts on learning capacity, memory retention, and behavior.",
    "Low Birth Weight":                    "Higher susceptibility to infections, developmental delays, and chronic conditions.",
    "Preterm Births":                      "Premature babies may face breathing, cardiac, and developmental complications.",
    "Sudden Infant Death Syndrome (SIDS)": "Sudden unexplained death of an otherwise healthy infant, typically during sleep.",
    "Bladder Cancer":                      "Blood in urine, pelvic pain, and frequent or painful urination.",
    "Diabetes":                            "Elevated blood sugar, fatigue, and long-term damage to eyes, kidneys, and nerves.",
    "Eye & Skin Irritation":              "Redness, itching, burning sensations in eyes and skin.",
}
disease_precautions = {
    'Asthma':                              "Avoid outdoor activity on high-pollution days. Use air purifiers and follow your asthma action plan.",
    'COPD':                                "Stop smoking, avoid polluted areas, and keep vaccinations up to date.",
    'Lung Cancer':                         "Avoid smoking and secondhand smoke. Minimize pollutant exposure and get regular checkups.",
    'Pneumonia & Bronchitis':              "Practice good hygiene, avoid contact with sick individuals, and get vaccinated.",
    'Reduced Lung Function in Children':   "Limit outdoor activity on bad air days. Use indoor HEPA air filters.",
    'Heart Attacks':                       "Eat a heart-healthy diet, exercise regularly, and monitor your blood pressure.",
    'Hypertension':                        "Reduce salt intake, exercise consistently, and actively manage stress.",
    'Strokes':                             "Control blood pressure, quit smoking, and maintain a healthy weight.",
    'Arrhythmia':                          "Avoid stimulants, manage stress levels, and follow your cardiologist's guidance.",
    "Alzheimer's & Dementia":              "Stay mentally and physically active. Maintain a balanced, anti-inflammatory diet.",
    "Parkinson's Disease":                 "Regular exercise and strict adherence to prescribed treatments.",
    "Cognitive Impairment in Children":    "Encourage stimulating learning activities. Minimize pollutant exposure.",
    "Low Birth Weight":                    "Consistent prenatal care. Avoid smoke, alcohol, and pollution during pregnancy.",
    "Preterm Births":                      "Attend all prenatal appointments. Reduce stress and avoid environmental pollutants.",
    "Sudden Infant Death Syndrome (SIDS)": "Always place babies on their backs to sleep. Avoid soft bedding in cribs.",
    "Bladder Cancer":                      "Stop smoking and reduce exposure to industrial chemicals and dyes.",
    "Diabetes":                            "Follow a balanced diet, exercise regularly, and monitor blood glucose levels.",
    "Eye & Skin Irritation":              "Wear protective eyewear outdoors, avoid rubbing eyes, use gentle skincare products.",
}


# ── SESSION STATE ─────────────────────────────────────────────────────────────
if 'map_center'    not in st.session_state: st.session_state.map_center = DEFAULT_LOCATION
if 'marker'        not in st.session_state: st.session_state.marker     = DEFAULT_LOCATION
if 'results'       not in st.session_state: st.session_state.results    = None
if 'features'      not in st.session_state: st.session_state.features   = None
if 'city_name'     not in st.session_state: st.session_state.city_name  = "Chennai, IN"


# ── LAYOUT: TWO STREAMLIT COLUMNS ────────────────────────────────────────────
left_col, right_col = st.columns([300, 700], gap="small")


# ══════════════════════════════════════════════════════════════════════════════
#  LEFT PANEL
# ══════════════════════════════════════════════════════════════════════════════
with left_col:
    st.markdown("""
    <div class="left-header">
        <div class="logo-tag">◆ AirRisk AI</div>
        <div class="app-title">Air Quality &<br>Disease Risk Map</div>
        <div class="app-subtitle">Real-time · Explainable AI</div>
    </div>
    """, unsafe_allow_html=True)

    # ── Search ──
    st.markdown('<div class="search-section">', unsafe_allow_html=True)
    search_query = st.text_input("", value="Chennai", placeholder="Search city…", key="searchbar", label_visibility="collapsed")
    search_btn   = st.button("↗ Fetch data & predict", key="searchbtn")
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Handle search ──
    if search_btn and search_query:
        geo_url  = f"http://api.openweathermap.org/geo/1.0/direct?q={search_query}&limit=1&appid={OPENWEATHER_API_KEY}"
        geo_resp = requests.get(geo_url)
        geo_data = geo_resp.json() if geo_resp.status_code == 200 else None
        if geo_data and len(geo_data) > 0:
            loc = geo_data[0]
            st.session_state.map_center = (loc['lat'], loc['lon'])
            st.session_state.marker     = (loc['lat'], loc['lon'])
            st.session_state.city_name  = f"{loc['name']}, {loc.get('country','')}"
            with st.spinner("Fetching data…"):
                air, weather = fetch_openweather_data(loc['lat'], loc['lon'])
                st.session_state.features = extract_features(air, weather)
                st.session_state.results  = None  # reset; will compute below
        else:
            st.error("Location not found.")

    # ── Compute results when features are ready ──
    if st.session_state.features and st.session_state.results is None:
        features = st.session_state.features
        aqi_input = [features[f] for f in ['PM2.5','PM10','NO2','SO2','CO','O3']]
        aqi_result = predict_aqi(aqi_input)
        disease_results = {}
        for disease, feats in disease_labels.items():
            inp = [features[f] for f in feats if f in features]
            disease_results[disease] = predict_disease_with_explanation(inp, disease)
        st.session_state.results = {
            'aqi':      aqi_result,
            'diseases': disease_results,
            'features': features,
        }

    results  = st.session_state.results
    features = st.session_state.features

    # ── AQI block ──
    if results and results['aqi']:
        aqi_value, lime_exp, shap_exp = results['aqi']
        cat, color, pct = aqi_category(aqi_value)
        st.markdown(f"""
        <div class="aqi-block">
            <div class="aqi-label">Predicted AQI</div>
            <div class="aqi-number" style="color:{color};">{aqi_value:.2f}</div>
            <div class="aqi-cat"    style="color:{color};">{cat}</div>
            <div class="aqi-bar-wrap">
                <div class="aqi-bar-fill" style="width:{pct}%;background:{color};"></div>
            </div>
            <div class="aqi-pills">
                <span class="aqi-pill">Temp {features.get('Temperature',25):.1f}°C</span>
                <span class="aqi-pill">Humidity {features.get('Humidity',50):.0f}%</span>
                <span class="aqi-pill">Wind {features.get('Wind Speed',0):.1f} m/s</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        with st.expander("◆ AQI — Explainable AI details"):
            st.write("**LIME explanation:**", lime_exp or "N/A")
            st.write("**SHAP explanation:**", shap_exp or "N/A")
    else:
        st.markdown("""
        <div class="aqi-block">
            <div class="aqi-label">Predicted AQI</div>
            <div style="font-size:14px;color:#1f2937;font-family:'JetBrains Mono',monospace;margin-top:8px;">
                Search a city to load data
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Pollutants ──
    st.markdown('<div class="poll-block"><div class="section-label">Pollutant levels</div>', unsafe_allow_html=True)
    poll_names = ['PM2.5','PM10','NO2','SO2','O3','CO','NH3','NO']
    if features:
        for pname in poll_names:
            val   = features.get(pname, 0)
            col   = pollutant_color(pname, val)
            pct_b = bar_pct(pname, val)
            st.markdown(f"""
            <div class="poll-row">
                <span class="poll-name">{pname}</span>
                <div class="poll-bar-wrap">
                    <div class="poll-bar-fill" style="width:{pct_b}%;background:{col};"></div>
                </div>
                <span class="poll-val">{val:.1f}</span>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown('<div style="font-size:12px;color:#1f2937;font-family:JetBrains Mono,monospace;">—</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Footer ──
    lat_disp, lon_disp = st.session_state.marker
    st.markdown(f"""
    <div class="left-footer">
        <div class="footer-loc">📍 {st.session_state.city_name}</div>
        <div class="footer-coords">{lat_disp:.4f}° N, {lon_disp:.4f}° E</div>
        <div class="footer-credit" style="margin-top:10px;font-size:10px;color:#1f2937;font-family:'JetBrains Mono',monospace;">
            Powered by OpenWeather · Explainable AI
        </div>
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  RIGHT PANEL — Map + Risk strip
# ══════════════════════════════════════════════════════════════════════════════
with right_col:

    # ── MAP ──
    m = folium.Map(
        location=st.session_state.map_center,
        zoom_start=7,
        tiles="CartoDB dark_matter",
        control_scale=False,
    )
    folium.Marker(
        location=st.session_state.marker,
        icon=folium.Icon(color='green', icon='circle', prefix='fa'),
        popup=st.session_state.city_name,
    ).add_to(m)

    map_data = st_folium(
        m,
        width="100%",
        height=420,
        returned_objects=["last_clicked"],
        key="main_map",
    )

    # handle map click → fetch new location
    if map_data and map_data.get("last_clicked"):
        clat = map_data["last_clicked"]["lat"]
        clon = map_data["last_clicked"]["lng"]
        if (clat, clon) != st.session_state.marker:
            st.session_state.marker     = (clat, clon)
            st.session_state.map_center = (clat, clon)
            st.session_state.city_name  = f"{clat:.4f}°N, {clon:.4f}°E"
            with st.spinner("Fetching data for clicked location…"):
                air, weather = fetch_openweather_data(clat, clon)
                st.session_state.features = extract_features(air, weather)
                st.session_state.results  = None
            st.rerun()

    # ── RISK STRIP ──
    st.markdown("""
    <div class="risk-strip-title" style="padding:12px 4px 6px;font-size:10px;letter-spacing:0.14em;text-transform:uppercase;color:#4b5563;font-family:'JetBrains Mono',monospace;">
        ◆ Disease risk — expand any card for health effects, precautions & AI explanation
    </div>
    """, unsafe_allow_html=True)

    if results and results['diseases']:
        disease_results = results['diseases']
        # show high-risk first
        sorted_diseases = sorted(
            disease_labels.keys(),
            key=lambda d: (0 if (disease_results.get(d) and disease_results[d]['prediction'] == 1) else 1)
        )
        # grid: 3 columns
        cols_per_row = 3
        disease_list = list(sorted_diseases)
        for row_start in range(0, len(disease_list), cols_per_row):
            chunk = disease_list[row_start:row_start + cols_per_row]
            cols  = st.columns(cols_per_row)
            for i, disease in enumerate(chunk):
                res = disease_results.get(disease)
                with cols[i]:
                    if res:
                        is_high  = res['prediction'] == 1
                        badge_cls = "badge-high" if is_high else "badge-low"
                        badge_txt = "⬆ High risk"  if is_high else "✓ Low risk"
                        chip_cls  = "high-risk"    if is_high else ""
                        st.markdown(f"""
                        <div class="risk-chip {chip_cls}">
                            <div class="chip-name">{disease}</div>
                            <div class="chip-badge {badge_cls}">{badge_txt}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        with st.expander("Details & AI"):
                            st.markdown(f"**Health effects:** {disease_effects.get(disease,'')}")
                            st.markdown(f"**Precautions:** {disease_precautions.get(disease,'')}")
                            st.markdown(f"**Confidence:** {max(res['probability']):.3f}")
                            st.markdown(f"**Model accuracy:** {res['accuracy'] if res['accuracy'] is not None else 'N/A'}")
                            if res.get('risk_factors'):
                                st.markdown("**Key risk factors:**")
                                for factor in res['risk_factors'][:5]:
                                    direction = "increases" if factor['type'] == 'risk_increasing' else "decreases"
                                    st.markdown(f"- `{factor['feature']}` {direction} risk (contribution: `{factor['contribution']:.4f}`)")
                            if res.get('recommendations'):
                                st.markdown("**Recommendations:**")
                                for rec in res['recommendations']:
                                    st.markdown(f"- {rec}")
                            with st.expander("LIME / SHAP details"):
                                st.write("LIME:", res.get('lime_explanation') or "N/A")
                                st.write("SHAP:", res.get('shap_explanation') or "N/A")
    else:
        st.markdown("""
        <div style="padding:20px;text-align:center;color:#1f2937;font-size:13px;font-family:'JetBrains Mono',monospace;">
            Search a city or click the map to run disease risk prediction
        </div>
        """, unsafe_allow_html=True)

    # ── Editable features (collapsed by default) ──
    if features:
        with st.expander("⚙ Edit fetched feature values before re-running"):
            st.markdown("Adjust any value then click **Fetch data & predict** again.")
            c1, c2 = st.columns(2)
            keys   = list(features.keys())
            half   = len(keys) // 2
            for k in keys[:half]:
                features[k] = c1.number_input(k, value=float(features[k]), key=f"feat_{k}")
            for k in keys[half:]:
                features[k] = c2.number_input(k, value=float(features[k]), key=f"feat_{k}")
            st.session_state.features = features