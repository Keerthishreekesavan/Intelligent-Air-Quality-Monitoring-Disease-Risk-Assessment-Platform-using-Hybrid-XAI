import sys
print("Python executable:", sys.executable)
import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import train_test_split, GridSearchCV, cross_val_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.svm import SVC
from sklearn.naive_bayes import GaussianNB
from sklearn.utils.class_weight import compute_class_weight
from sklearn.metrics import accuracy_score, classification_report
import warnings
import os

# Try to import unified_model, handle if missing
try:
    from unified_model import UnifiedDiseaseModel
    UNIFIED_MODEL_AVAILABLE = True
except ImportError:
    UNIFIED_MODEL_AVAILABLE = False
    print("unified_model.py not found. Some features may be limited.")

# Add LIME and SHAP imports for explainable AI
try:
    import lime
    import lime.lime_tabular
    import shap
    EXPLAINABILITY_AVAILABLE = True
    print("LIME and SHAP libraries found - Explainable AI enabled!")
except ImportError:
    EXPLAINABILITY_AVAILABLE = False
    print("LIME or SHAP not found. Install with: pip install lime shap")
    print("Continuing without explainable AI features...")

warnings.filterwarnings("ignore")

# Load Dataset with better error handling
print("Loading Dataset...")
df = None
dataset_files = [
    'air_pollution_2024_2025(main).csv.csv',
    'air_pollution_2024_2025(main).csv',
    'air_pollution_data.csv',
    'data.csv'
]

for filename in dataset_files:
    try:
        if os.path.exists(filename):
            df = pd.read_csv(filename)
            print(f"Dataset loaded successfully from: {filename}")
            break
    except Exception as e:
        print(f"Failed to load {filename}: {e}")
        continue

if df is None:
    print("No dataset file found. Skipping dataset-dependent operations.")
    print("Available files in current directory:")
    try:
        files = [f for f in os.listdir('.') if f.endswith('.csv')]
        if files:
            print("CSV files found:", files)
        else:
            print("No CSV files found in current directory.")
    except Exception as e:
        print(f"Could not list directory contents: {e}")
    
    # Create a dummy dataset for demonstration
    print("\nCreating dummy dataset for demonstration purposes...")
    np.random.seed(42)
    n_samples = 1000
    
    dummy_data = {
        'PM2.5': np.random.normal(25, 10, n_samples),
        'PM10': np.random.normal(45, 15, n_samples),
        'NO2': np.random.normal(30, 8, n_samples),
        'SO2': np.random.normal(15, 5, n_samples),
        'CO': np.random.normal(1.2, 0.3, n_samples),
        'O3': np.random.normal(80, 20, n_samples)
    }
    
    # Add some disease labels based on pollution levels
    for key in dummy_data:
        dummy_data[key] = np.clip(dummy_data[key], 0, None)  # Ensure non-negative values
    
    df = pd.DataFrame(dummy_data)
    
    # Create binary disease labels based on pollution thresholds
    disease_thresholds = {
        'Asthma': lambda row: 1 if (row['PM2.5'] > 30 or row['PM10'] > 50 or row['NO2'] > 35) else 0,
        'COPD': lambda row: 1 if (row['PM2.5'] > 25 or row['PM10'] > 45 or row['SO2'] > 20) else 0,
        'Lung Cancer': lambda row: 1 if (row['PM2.5'] > 35 or row['PM10'] > 55 or row['NO2'] > 40 or row['O3'] > 100) else 0,
        'Heart Attacks': lambda row: 1 if (row['PM2.5'] > 30 or row['PM10'] > 50 or row['CO'] > 1.5) else 0,
        'Diabetes': lambda row: 1 if (row['PM2.5'] > 28 or row['NO2'] > 32 or row['SO2'] > 18) else 0
    }
    
    for disease, threshold_func in disease_thresholds.items():
        df[disease] = df.apply(threshold_func, axis=1)
    
    print("Dummy dataset created successfully!")

# Continue with the rest of the processing if we have a dataset
if df is not None:
    # Fill missing values with more sophisticated approach
    df.fillna(df.median(numeric_only=True), inplace=True)
    df.columns = df.columns.str.strip()

    # Define diseases and features
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

    # Add effects and precautions for each disease
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

    # Check which features and diseases are available in the dataset
    available_features = [col for col in df.columns if col in ['PM2.5', 'PM10', 'NO2', 'SO2', 'CO', 'O3']]
    available_diseases = [disease for disease in disease_labels.keys() if disease in df.columns]
    print(f"Available features: {available_features}")
    print(f"Available diseases: {available_diseases}")
    if not available_diseases:
        print("No disease columns found in dataset. Available columns:", df.columns.tolist())

    # Encode disease labels for available diseases
    le_disease = LabelEncoder()
    for disease in available_diseases:
        try:
            df[disease] = le_disease.fit_transform(df[disease])
        except Exception as e:
            print(f"Error encoding {disease}: {e}")
            continue

    # Train models for each available disease
    trained_models = []
    for disease, features in disease_labels.items():
        if disease not in available_diseases:
            print(f"Skipping {disease} - not found in dataset")
            continue
        # Check if all required features are available
        missing_features = [f for f in features if f not in available_features]
        if missing_features:
            print(f"Skipping {disease} - missing features: {missing_features}")
            continue
        try:
            X, y = df[features], df[disease]
            # Check if we have enough samples and class diversity
            if len(X) < 10:
                print(f"Skipping {disease} - insufficient samples ({len(X)})")
                continue
            unique_classes = np.unique(y)
            if len(unique_classes) < 2:
                print(f"Skipping {disease} - insufficient class diversity")
                continue
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
            print(f"Training Hybrid SVM-Naive Bayes model for {disease}...")
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            nb_model = GaussianNB()
            nb_model.fit(X_train_scaled, y_train)
            X_train_hybrid = np.hstack((X_train_scaled, np.log(np.clip(nb_model.predict_proba(X_train_scaled), 1e-9, 1))))
            X_test_hybrid = np.hstack((X_test_scaled, np.log(np.clip(nb_model.predict_proba(X_test_scaled), 1e-9, 1))))
            class_weights = {i: weight for i, weight in zip(unique_classes, compute_class_weight(class_weight='balanced', classes=unique_classes, y=y_train))}
            svm = SVC(class_weight=class_weights, probability=True, random_state=42, kernel='rbf', C=100, gamma='auto')
            svm.fit(X_train_hybrid, y_train)
            # Calculate accuracy
            y_pred = svm.predict(X_test_hybrid)
            accuracy = accuracy_score(y_test, y_pred)
            print(f"Model accuracy for {disease}: {accuracy:.3f}")
            # Save model with error handling
            try:
                if UNIFIED_MODEL_AVAILABLE:
                    background_data = X_train_scaled[:100] if X_train_scaled.shape[0] > 100 else X_train_scaled
                    unified_model = UnifiedDiseaseModel(
                        svm=svm,
                        nb=nb_model,
                        scaler=scaler,
                        feature_names=features,
                        background_data=background_data,
                        class_names=['Low Risk', 'High Risk']
                    )
                    model_to_save = unified_model
                else:
                    # Create a simple model container if UnifiedDiseaseModel isn't available
                    model_to_save = {
                        'svm': svm,
                        'nb': nb_model,
                        'scaler': scaler,
                        'feature_names': features,
                        'accuracy': accuracy,
                        'class_names': ['Low Risk', 'High Risk']
                    }
                model_filename = f"{disease.lower().replace(' ', '_').replace('&', 'and').replace('(', '').replace(')', '')}_unified_model.pkl"
                joblib.dump(model_to_save, model_filename)
                print(f"Saved model for {disease} as {model_filename}")
                trained_models.append((disease, model_filename, accuracy))
            except Exception as e:
                print(f"Error saving model for {disease}: {e}")
                continue
        except Exception as e:
            print(f"Error training model for {disease}: {e}")
            continue
    print("\n=== Training Summary ===")
    if trained_models:
        print(f"Successfully trained {len(trained_models)} models:")
        for disease, filename, accuracy in trained_models:
            print(f"  {disease}: {filename} (accuracy: {accuracy:.3f})")
    else:
        print("No models were successfully trained.")

# Load models and make predictions with explainability
def predict_disease_with_explanation(features, disease_name):
    """
    Make prediction with comprehensive explainability using LIME and SHAP
    """
    if disease_name not in disease_labels:
        print(f"Disease '{disease_name}' not found in disease_labels")
        return None
    model_filename = f"{disease_name.lower().replace(' ', '_').replace('&', 'and').replace('(', '').replace(')', '')}_unified_model.pkl"
    try:
        if not os.path.exists(model_filename):
            print(f"Model file {model_filename} not found. Available model files:")
            pkl_files = [f for f in os.listdir('.') if f.endswith('_unified_model.pkl')]
            if pkl_files:
                print(f"  {pkl_files}")
            else:
                print("  No model files found")
            return None
        model_data = joblib.load(model_filename)
        # Handle both UnifiedDiseaseModel and dictionary formats
        if hasattr(model_data, 'scaler'):
            # UnifiedDiseaseModel format
            scaler = model_data.scaler
            nb_model = model_data.nb
            svm_model = model_data.svm
            feature_names = model_data.feature_names
            accuracy = getattr(model_data, 'accuracy', None)
        else:
            # Dictionary format
            scaler = model_data['scaler']
            nb_model = model_data['nb']
            svm_model = model_data['svm']
            feature_names = model_data['feature_names']
            accuracy = model_data.get('accuracy', None)
        # Make prediction
        features_scaled = scaler.transform([features])
        nb_probs = nb_model.predict_proba(features_scaled)
        features_hybrid = np.hstack((features_scaled, np.log(np.clip(nb_probs, 1e-9, 1))))
        pred = svm_model.predict(features_hybrid)
        pred_proba = svm_model.predict_proba(features_hybrid)
        result = {
            'prediction': pred[0],
            'probability': pred_proba[0],
            'model_type': 'hybrid_svm_nb',
            'accuracy': accuracy,
            'feature_importance': None,
            'input_features': dict(zip(feature_names, features)),
            'lime_explanation': None,
            'shap_explanation': None,
            'risk_factors': [],
            'recommendations': []
        }
        # Add LIME explanation
        if EXPLAINABILITY_AVAILABLE:
            try:
                # Create LIME explainer
                def predict_fn(X):
                    """Prediction function for LIME"""
                    X_scaled = scaler.transform(X)
                    nb_probs_lime = nb_model.predict_proba(X_scaled)
                    X_hybrid = np.hstack((X_scaled, np.log(np.clip(nb_probs_lime, 1e-9, 1))))
                    return svm_model.predict_proba(X_hybrid)
                # Create training data for LIME explainer (use some dummy data if background not available)
                if hasattr(model_data, 'background_data'):
                    training_data = model_data.background_data
                else:
                    # Create dummy training data
                    training_data = np.random.normal(0, 1, (100, len(features)))
                explainer = lime.lime_tabular.LimeTabularExplainer(
                    training_data,
                    feature_names=feature_names,
                    class_names=['Low Risk', 'High Risk'],
                    mode='classification'
                )
                # Get LIME explanation
                exp = explainer.explain_instance(
                    np.array(features), 
                    predict_fn, 
                    num_features=len(features)
                )
                # Extract LIME results
                lime_list = exp.as_list()
                feature_weights = {}
                for feature_desc, weight in lime_list:
                    # Extract feature name from description
                    for fname in feature_names:
                        if fname in feature_desc:
                            feature_weights[fname] = weight
                            break
                result['lime_explanation'] = {
                    'prediction': exp.predict_proba[1],
                    'confidence': max(exp.predict_proba),
                    'feature_weights': feature_weights
                }
                # Create risk factors from LIME
                risk_factors = []
                for feature, weight in feature_weights.items():
                    risk_factors.append({
                        'feature': feature,
                        'contribution': abs(weight),
                        'type': 'risk_increasing' if weight > 0 else 'risk_decreasing'
                    })
                result['risk_factors'] = sorted(risk_factors, key=lambda x: x['contribution'], reverse=True)
            except Exception as e:
                print(f"LIME explanation failed for {disease_name}: {e}")
                result['lime_explanation'] = f"LIME failed: {str(e)}"
            # Add SHAP explanation
            try:
                # Create SHAP explainer
                def shap_predict_fn(X):
                    """Prediction function for SHAP"""
                    X_scaled = scaler.transform(X)
                    nb_probs_shap = nb_model.predict_proba(X_scaled)
                    X_hybrid = np.hstack((X_scaled, np.log(np.clip(nb_probs_shap, 1e-9, 1))))
                    return svm_model.predict_proba(X_hybrid)[:, 1]  # Return probability of positive class
                # Use kernel explainer for model-agnostic explanations
                if hasattr(model_data, 'background_data'):
                    background = model_data.background_data[:50]  # Use subset for speed
                else:
                    background = np.random.normal(0, 1, (50, len(features)))
                explainer = shap.KernelExplainer(shap_predict_fn, background)
                shap_values = explainer.shap_values(np.array([features]), nsamples=100)
                # Extract SHAP results
                feature_importance = {}
                for i, fname in enumerate(feature_names):
                    feature_importance[fname] = float(shap_values[0][i])
                result['shap_explanation'] = {
                    'base_value': float(explainer.expected_value),
                    'feature_importance': feature_importance,
                    'prediction_value': float(explainer.expected_value + np.sum(shap_values[0]))
                }
            except Exception as e:
                print(f"SHAP explanation failed for {disease_name}: {e}")
                result['shap_explanation'] = f"SHAP failed: {str(e)}"
        # Add recommendations based on risk factors
        if result['risk_factors']:
            recommendations = []
            high_risk_factors = [f for f in result['risk_factors'] if f['type'] == 'risk_increasing'][:3]
            for factor in high_risk_factors:
                feature = factor['feature']
                if 'PM' in feature:
                    recommendations.append(f"Reduce exposure to particulate matter - consider air purifiers and avoid outdoor activities during high pollution days")
                elif 'NO2' in feature:
                    recommendations.append(f"Limit exposure to traffic pollution - avoid busy roads and use alternative transport")
                elif 'SO2' in feature:
                    recommendations.append(f"Reduce exposure to sulfur dioxide - avoid industrial areas and use indoor air filtration")
                elif 'CO' in feature:
                    recommendations.append(f"Ensure proper ventilation and avoid enclosed spaces with combustion sources")
                elif 'O3' in feature:
                    recommendations.append(f"Limit outdoor activities during peak ozone hours (typically afternoon)")
            if not recommendations:
                recommendations.append("Maintain good general health practices and monitor air quality regularly")
            result['recommendations'] = recommendations
        # Effects
        effect = disease_effects.get(disease_name, "N/A")
        print(f"\nPossible Health Effects: {effect}")
        # Precautions
        precaution = disease_precautions.get(disease_name, "N/A")
        print(f"Precautions: {precaution}")
        return result
    except FileNotFoundError as e:
        print(f"Model file not found for {disease_name}: {model_filename}")
        print(f"FileNotFoundError: {e}")
        return None
    except Exception as e:
        print(f"Error making prediction for {disease_name}: {e}")
        import traceback
        traceback.print_exc()
        return None

def print_comprehensive_explanation(result, disease_name):
    """
    Print comprehensive explanation including LIME and SHAP results
    Args:
        result: Prediction result dictionary
        disease_name: Name of the disease
    """
    if result is None:
        print(f"No prediction available for {disease_name}")
        return
    print(f"\n{'='*60}")
    print(f"COMPREHENSIVE ANALYSIS: {disease_name}")
    print(f"{'='*60}")
    # Basic prediction info
    print(f"Prediction: {'HIGH RISK' if result['prediction'] == 1 else 'LOW RISK'}")
    print(f"Confidence: {max(result['probability']):.3f}")
    if result.get('accuracy') is not None:
        print(f"Model Accuracy: {result['accuracy']:.3f}")
    else:
        print("Model Accuracy: N/A")
    # Input features
    print(f"\nInput Features:")
    for feature, value in result['input_features'].items():
        print(f"  {feature}: {value:.2f}")
    # LIME explanation
    lime_exp = result.get('lime_explanation')
    if isinstance(lime_exp, dict):
        print(f"\nLIME Explanation:")
        print(f"  Predicted Class: {lime_exp['prediction']}")
        print(f"  Confidence: {lime_exp['confidence']:.3f}")
        print(f"  Feature Contributions:")
        for feature, weight in lime_exp['feature_weights'].items():
            direction = "UP" if weight > 0 else "DOWN"
            print(f"    {feature}: {weight:.4f} {direction}")
    elif lime_exp:
        print(f"\nLIME Explanation: {lime_exp}")
    # SHAP explanation
    shap_exp = result.get('shap_explanation')
    if isinstance(shap_exp, dict):
        print(f"\nSHAP Explanation:")
        print(f"  Base Value: {shap_exp['base_value']:.4f}")
        print(f"  Feature Importance:")
        for feature, importance in shap_exp['feature_importance'].items():
            print(f"    {feature}: {importance:.4f}")
    elif shap_exp:
        print(f"\nSHAP Explanation: {shap_exp if shap_exp is not None else 'N/A'}")
    # Risk factors
    if result.get('risk_factors'):
        print(f"\nRisk Factor Analysis:")
        for factor in result['risk_factors'][:5]:  # Top 5 factors
            risk_type = "INCREASES" if factor['type'] == 'risk_increasing' else "DECREASES"
            print(f"  {factor['feature']} {risk_type} risk (contribution: {factor['contribution']:.4f})")
    # Recommendations
    if result.get('recommendations'):
        print(f"\nRecommendations:")
        for i, rec in enumerate(result['recommendations'], 1):
            print(f"  {i}. {rec}")
    # Effects
    effect = disease_effects.get(disease_name, "N/A")
    print(f"\nPossible Health Effects: {effect}")
    # Precautions
    precaution = disease_precautions.get(disease_name, "N/A")
    print(f"Precautions: {precaution}")
    # Traditional feature importance
    if result.get('feature_importance'):
        if result['feature_importance'] is not None:
            print(f"\nTraditional Feature Importance:")
            for feature, importance in sorted(result['feature_importance'].items(), key=lambda x: x[1], reverse=True):
                print(f"  {feature}: {importance:.4f}")
        else:
            print("\nTraditional Feature Importance: N/A")
    print(f"\n{'='*60}")

# Example usage with explainability
if 'trained_models' in globals() and trained_models:
    example_features = [12.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0]  # Replace with actual values
    print("\n=== Example Predictions with Explainability ===")
    # Only try predictions for diseases that were successfully trained
    trained_disease_names = [disease for disease, _, _ in trained_models]
    for disease in trained_disease_names:
        try:
            model_filename = f"{disease.lower().replace(' ', '_').replace('&', 'and').replace('(', '').replace(')', '')}_unified_model.pkl"
            if not os.path.exists(model_filename):
                print(f"Skipping {disease}: model file not found.")
                continue
            print(f"\nProcessing {disease}...")
            required_features = len(disease_labels[disease])
            if required_features <= len(example_features):
                result = predict_disease_with_explanation(
                    example_features[:required_features], 
                    disease
                )
                if result:
                    print_comprehensive_explanation(result, disease)
                else:
                    print(f"Could not generate prediction for {disease}")
            else:
                print(f"Not enough example features for {disease} (needs {required_features}, have {len(example_features)})")
        except Exception as e:
            print(f"Error processing {disease}: {e}")
            continue
else:
    print("\nNo trained models available for predictions.")
    print("This might be because:")
    print("1. No dataset was found")
    print("2. Dataset lacks required disease columns")
    print("3. Insufficient data for training")
    print("4. All training attempts failed")

print("\nScript execution completed!")

# === AQI Prediction Pipeline ===
def train_aqi_model():
    print("\n=== Training AQI Model (tamilnadu_air_pollution_2020_2024.csv) ===")
    aqi_file = 'tamilnadu_air_pollution_2020_2024.csv'
    if not os.path.exists(aqi_file):
        print(f"AQI data file '{aqi_file}' not found. Skipping AQI model training.")
        return
    aqi_df = pd.read_csv(aqi_file)
    # Map possible column names to expected names
    column_map = {
        'pm2_5': 'PM2.5',
        'pm10': 'PM10',
        'no2': 'NO2',
        'so2': 'SO2',
        'co': 'CO',
        'o3': 'O3',
        'AQI': 'AQI',
        'Air Quality Index': 'AQI',
        'no': 'NO',  # not used
        'nh3': 'NH3', # not used
        'timestamp': 'timestamp' # not used
    }
    # Rename columns if needed
    aqi_df = aqi_df.rename(columns={k: v for k, v in column_map.items() if k in aqi_df.columns})
    aqi_features = ['PM2.5', 'PM10', 'NO2', 'SO2', 'CO', 'O3']
    aqi_target = 'AQI'
    if not all(f in aqi_df.columns for f in aqi_features + [aqi_target]):
        print(f"AQI data missing required columns after renaming. Found columns: {aqi_df.columns.tolist()}")
        return
    X = aqi_df[aqi_features]
    y = aqi_df[aqi_target]
    # Ensure y is a Series, not a DataFrame
    if isinstance(y, pd.DataFrame):
        y = y.iloc[:, 0]
    # Ensure y is numeric; if not, map categories to AQI values
    if not np.issubdtype(y.dtype, np.number):
        # Try to convert to numeric, if fails, map categories
        try:
            y = pd.to_numeric(y)
        except Exception:
            # Map common AQI categories to numeric values (India AQI standard)
            aqi_category_map = {
                'Good': 50,
                'Satisfactory': 100,
                'Moderate': 200,
                'Poor': 300,
                'Very Poor': 400,
                'Severe': 500
            }
            if set(y.unique()).issubset(set(aqi_category_map.keys())):
                print("Warning: AQI target is categorical. Mapping categories to numeric AQI values for regression.")
                y = y.map(aqi_category_map)
            else:
                print(f"AQI target column contains unknown categories: {set(y.unique())}. Skipping AQI model training.")
                return
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    from sklearn.ensemble import RandomForestRegressor
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train_scaled, y_train)
    joblib.dump({'model': model, 'scaler': scaler, 'features': aqi_features, 'X_train': X_train_scaled}, 'aqi_model.pkl')
    print("AQI model trained and saved as aqi_model.pkl")
    # Evaluate
    y_pred = model.predict(X_test_scaled)
    from sklearn.metrics import mean_squared_error, r2_score
    print(f"AQI Test RMSE: {mean_squared_error(y_test, y_pred) ** 0.5:.2f}")
    print(f"AQI Test R2: {r2_score(y_test, y_pred):.3f}")

train_aqi_model()

def predict_aqi(features):
    """
    Predict AQI given pollution features. features: [PM2.5, PM10, NO2, SO2, CO, O3]
    Returns prediction, LIME explanation, SHAP explanation
    """
    if not os.path.exists('aqi_model.pkl'):
        print("aqi_model.pkl not found. Please train the AQI model first or check your data file.")
        return None, None, None
    model_data = joblib.load('aqi_model.pkl')
    scaler = model_data['scaler']
    model = model_data['model']
    X_train = model_data['X_train']
    feature_names = model_data['features']
    X_scaled = scaler.transform([features])
    aqi_pred = model.predict(X_scaled)[0]
    lime_exp = None
    shap_exp = None
    # LIME explainability
    if EXPLAINABILITY_AVAILABLE:
        try:
            import lime.lime_tabular
            lime_explainer = lime.lime_tabular.LimeTabularExplainer(
                training_data=X_train,
                feature_names=feature_names,
                mode='regression'
            )
            lime_exp_obj = lime_explainer.explain_instance(
                np.array(features),
                model.predict,
                num_features=len(features)
            )
            lime_exp = dict(lime_exp_obj.as_list())
        except Exception as e:
            lime_exp = f"LIME failed: {e}"
        # SHAP explainability
        try:
            import shap
            shap_explainer = shap.KernelExplainer(model.predict, X_train[:50])
            shap_values = shap_explainer.shap_values(np.array([features]), nsamples=100)
            shap_exp = dict(zip(feature_names, shap_values[0]))
        except Exception as e:
            shap_exp = f"SHAP failed: {e}"
    return aqi_pred, lime_exp, shap_exp

# Example AQI prediction
print("\n=== Example AQI Prediction with Explainability ===")
example_aqi_features = [30, 50, 25, 10, 1.2, 60]  # [PM2.5, PM10, NO2, SO2, CO, O3]
aqi_result = predict_aqi(example_aqi_features)
if aqi_result is not None:
    aqi_value, lime_exp, shap_exp = aqi_result
    print(f"Predicted AQI: {aqi_value:.2f}")
    print(f"LIME Explanation: {lime_exp}")
    if isinstance(shap_exp, dict):
        print("SHAP Explanation:")
        for feature, value in shap_exp.items():
            print(f"  {feature}: {value:.4f}")
    else:
        print(f"SHAP Explanation: {shap_exp if shap_exp is not None else 'N/A'}")
else:
    print("AQI prediction skipped due to missing model or data.")

def get_aqi_level_info(aqi_index):
    """
    Map AQI index to emoji, level description, and meaning.
    Args:
        aqi_index (float or int): AQI index (normalized, e.g., 1-6 or 1-5+)
    Returns:
        dict: {'emoji': ..., 'level': ..., 'description': ...}
    """
    if aqi_index < 2:
        return {
            'emoji': '🟢',
            'level': 'Good',
            'description': 'Air quality is clean and poses little or no risk.'
        }
    elif aqi_index < 3:
        return {
            'emoji': '🟡',
            'level': 'Moderate',
            'description': 'Acceptable air quality; some pollutants may affect a very small number of sensitive individuals.'
        }
    elif aqi_index < 4:
        return {
            'emoji': '🟠',
            'level': 'Unhealthy for Sensitive Groups',
            'description': 'Sensitive people (children, elderly, respiratory patients) may experience health effects.'
        }
    elif aqi_index < 5:
        return {
            'emoji': '🔴',
            'level': 'Unhealthy',
            'description': 'Everyone may begin to experience health effects; sensitive groups may have more serious effects.'
        }
    else:
        return {
            'emoji': '🟣',
            'level': 'Very Unhealthy / Hazardous',
            'description': 'Health alert: serious health effects for the entire population; avoid outdoor activities.'
        }