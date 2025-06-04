First, ensure you have Python 3.8+ and install dependencies with `pip install pandas scikit-learn bleak pytz`. 
Under `PET_HEALTH/`, create three folders: `data/`, `model/`, and `scripts/`. 

In `scripts/`, include `collect_ble_data.py` (which writes whatever filename you pass into `data/`), and `train_model.py` (which reads `data/baseline.csv`, converts timestamps to US/Eastern, trains one IsolationForest for each feature [`temp_C`, `humidity_%`, `accel_x`, `accel_y`, `accel_z`], and pickles those five models into `model/anomaly_models.pkl`). 

To start, run `cd PET_HEALTH/scripts` and execute `python collect_ble_data.py baseline.csv`, letting it collect 10–20 minutes of your pet at rest; this creates `PET_HEALTH/data/baseline.csv`. 
When you’re done, stop the script (Ctrl+C) and run `python train_model.py`, which overwrites or creates `PET_HEALTH/model/anomaly_models.pkl`.

Next, to flag anomalies in new readings, use the same BLE‐collection script but name the output `new_data.csv`:

After you stop collecting, run `python detect_anomalies.py` (also in `scripts/`), which loads `model/anomaly_models.pkl` and `data/new_data.csv`, runs each feature through its IsolationForest, and writes out `PET_HEALTH/data/results/new_data_labeled.csv` with raw (±1) and “normal”/“anomaly” labels for each feature, plus a comma‐separated `anomaly_features` column.

 Optionally, open `notebooks/Analytics.ipynb` and point it at `../data/results/new_data_labeled.csv` to generate summary tables, correlation matrices, and time‐series plots.```

