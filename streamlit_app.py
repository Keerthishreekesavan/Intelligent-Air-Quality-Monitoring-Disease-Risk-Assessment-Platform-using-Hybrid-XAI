import streamlit as st
import numpy as np
import pandas as pd
import joblib
import os
import matplotlib.pyplot as plt
from models import predict_disease_with_explanation, print_comprehensive_explanation, predict_aqi, get_aqi_level_info

st.set_page_config(page_title="Air Pollution Disease & AQI Predictor", layout="centered")
st.title("🌏 Air Pollution Disease & AQI Predictor with Explainable AI")
st.markdown("""
This app predicts disease risk and AQI from air pollution data, and provides LIME/SHAP explanations for transparency.\
**All predictions are for educational purposes only.**
""")

# --- Disease Prediction Section ---
st.header("Disease Risk Prediction")
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

# Disease selection and dynamic feature input
if 'selected_disease' not in st.session_state:
    st.session_state.selected_disease = list(disease_labels.keys())[0]

selected_disease = st.selectbox("Select Disease", list(disease_labels.keys()),
                                index=list(disease_labels.keys()).index(st.session_state.selected_disease),
                                key="disease_select")
st.session_state.selected_disease = selected_disease

# Dynamically show feature inputs for the selected disease
feature_values = []
st.subheader(f"Enter features for {selected_disease}")
for feat in disease_labels[selected_disease]:
    val = st.number_input(f"{feat} (μg/m³ or ppm)", min_value=0.0, max_value=1000.0, value=10.0, key=f"disease_{feat}")
    feature_values.append(val)

predict_btn = st.button("Predict Disease Risk")

if predict_btn:
    with st.spinner("Predicting and explaining..."):
        result = predict_disease_with_explanation(feature_values, selected_disease)
    if result:
        st.success(f"Prediction: {'HIGH RISK' if result['prediction'] == 1 else 'LOW RISK'}")
        st.write(f"Confidence: {max(result['probability']):.3f}")
        st.write(f"Model Accuracy: {result['accuracy'] if result['accuracy'] is not None else 'N/A'}")
        st.subheader("LIME Explanation")
        lime_exp = result.get('lime_explanation')
        if isinstance(lime_exp, dict):
            st.write(lime_exp)
        else:
            st.write(lime_exp or "N/A")
        st.subheader("SHAP Explanation")
        shap_exp = result.get('shap_explanation')
        if isinstance(shap_exp, dict):
            st.write(shap_exp)
        else:
            st.write(shap_exp or "N/A")
        st.subheader("Risk Factors")
        if result.get('risk_factors'):
            for factor in result['risk_factors'][:5]:
                risk_type = "INCREASES" if factor['type'] == 'risk_increasing' else "DECREASES"
                st.write(f"{factor['feature']} {risk_type} risk (contribution: {factor['contribution']:.4f})")
        st.subheader("Recommendations")
        if result.get('recommendations'):
            for rec in result['recommendations']:
                st.write(f"- {rec}")
    else:
        st.error("Prediction failed or model not available for this disease.")

# --- AQI Prediction Section ---
st.header("AQI Prediction")
with st.form("aqi_form"):
    st.write("Enter pollution values to predict AQI:")
    aqi_features = ['PM2.5', 'PM10', 'NO2', 'SO2', 'CO', 'O3']
    aqi_input = []
    for feat in aqi_features:
        val = st.number_input(f"{feat} (μg/m³ or ppm)", min_value=0.0, max_value=1000.0, value=10.0, key=f"aqi_{feat}")
        aqi_input.append(val)
    aqi_submitted = st.form_submit_button("Predict AQI")

if aqi_submitted:
    with st.spinner("Predicting AQI and explaining..."):
        aqi_result = predict_aqi(aqi_input)
    if aqi_result is not None:
        aqi_value, lime_exp, shap_exp = aqi_result
        aqi_info = get_aqi_level_info(aqi_value)
        st.success(f"Predicted AQI: {aqi_value:.2f} ({aqi_info['emoji']} {aqi_info['level']})")
        st.subheader("LIME Explanation")
        st.write(lime_exp or "N/A")
        st.subheader("SHAP Explanation")
        if isinstance(shap_exp, dict):
            st.write(shap_exp)
        else:
            st.write(shap_exp or "N/A")
    else:
        st.error("AQI prediction failed or model not available.")

# After AQI prediction section, add the AQI levels table
st.markdown("### AQI Levels and Meanings")
aqi_levels = [
    {"range": "1–2", "emoji": "🟢", "desc": "Good", "meaning": "Air quality is clean and poses little or no risk."},
    {"range": "2–3", "emoji": "🟡", "desc": "Moderate", "meaning": "Acceptable air quality; some pollutants may affect a very small number of sensitive individuals."},
    {"range": "3–4", "emoji": "🟠", "desc": "Unhealthy for Sensitive Groups", "meaning": "Sensitive people (children, elderly, respiratory patients) may experience health effects."},
    {"range": "4–5", "emoji": "🔴", "desc": "Unhealthy", "meaning": "Everyone may begin to experience health effects; sensitive groups may have more serious effects."},
    {"range": "5+", "emoji": "🟣", "desc": "Very Unhealthy / Hazardous", "meaning": "Health alert: serious health effects for the entire population; avoid outdoor activities."},
]
st.markdown(
    "| Level | Air Quality | Meaning |\n"
    "|-------|-------------|---------|\n" +
    "\n".join(
        f"| {row['range']} | {row['emoji']} {row['desc']} | {row['meaning']} |"
        for row in aqi_levels
    )
)

st.markdown("---")
st.caption("Developed with ❤️ for Explainable AI in Air Quality and Health.") 