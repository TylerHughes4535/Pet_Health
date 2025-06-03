import pandas as pd
import joblib
import sys
import os

def load_model(path="models/anomaly_model.pkl"):
    return joblib.load(path)

def run_inference(df, model):
    features = ['body_temp', 'ambient_temp', 'humidity']
    df['anomaly_score'] = model.decision_function(df[features])
    df['is_anomaly'] = model.predict(df[features])
    return df

if __name__ == "__main__":
    # Allow filename override
    input_file = sys.argv[1] if len(sys.argv) > 1 else "data/cat_sensor_log.csv"
    df = pd.read_csv(input_file)
    model = load_model()
    df = run_inference(df, model)

    # Create labeled filename
    base, ext = os.path.splitext(input_file)
    labeled_file = f"{base}_labeled{ext}"
    df.to_csv(labeled_file, index=False)

    print(f"Labeled data saved to {labeled_file}")
    
    

    
