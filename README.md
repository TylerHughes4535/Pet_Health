# collect_ble_data.py

**Purpose:**  
Connect to the NanoSense BLE device, read temperature/humidity/IMU once per second, and write raw sensor readings into a CSV in `data/` for a fixed duration.

**Usage:**  
```bash
python collect_ble_data.py <output_filename.csv> <duration_seconds>

# train_model.py

**Purpose:**  
Load the “healthy” baseline CSV (`data/baseline.csv`), engineer features, scale them, train a multivariate `IsolationForest` on baseline data, pick a threshold from baseline anomaly scores, and save all artifacts.

**Usage:**  
```bash
python train_model.py

# streaming_detect.py

**Purpose:**  
Perform live anomaly detection: wait for user to press ENTER, then continuously read BLE data, scale and score each reading against the saved model, print anomalies in real time, and log all readings (with anomaly flags) to `data/live_data.csv` until stopped.

**Usage:**  
```bash
python streaming_detect.py

# run_pipeline.py

**Purpose:**  
Automate the entire workflow in one command: collect a baseline CSV, train the model, wait a bit, then start live anomaly detection. No filenames need to be typed—only durations are provided.

**Usage:**  
```bash
python run_pipeline.py <baseline_seconds> <wait_seconds>

# detect_anomalies.py

**Purpose:**  
Batch‐label a saved CSV under `data/` (e.g. `live_data.csv`) using the trained artifacts. For each row, it computes multivariate anomaly labels, per-feature z-scores vs. baseline, and a `contributing_features` column that lists which feature(s) (or “multivariate”) caused the anomaly.

**Usage:**  
```bash
python detect_anomalies.py


## Model Artifacts (`.pkl`)

After you run `train_model.py`, three key files appear:

1. **`model/scaler.pkl`**  
   - **What it is:** A serialized `sklearn.preprocessing.StandardScaler` object.  
   - **Why it’s important:**  
     - During training, we compute the mean (µ) and standard deviation (σ) of each feature (temperature, humidity, accel_x, accel_y, accel_z, and accel_mag) over the baseline data.  
     - `StandardScaler` stores those µ and σ values.  
     - When new data arrives (live or batch), we apply the exact same normalization:  
       \[
         X_{\text{scaled}} = \frac{X - \mu}{\sigma}.
       \]
     - This ensures the anomaly detector sees data on the same scale as it was trained on, preventing one feature (e.g. accel_x ~ ±1 g) from dominating another (temp_C ~ 20–25 °C).

2. **`model/iso_multivar.pkl`**  
   - **What it is:** A serialized `sklearn.ensemble.IsolationForest` model trained on scaled baseline features.  
   - **Why it’s important:**  
     - We trained a single multivariate IsolationForest on the 6‐D space:  
       ```
       [temp_C, humidity_%, accel_x, accel_y, accel_z, accel_mag]
       ```  
     - IsolationForest constructs “random partition trees” that isolate outliers faster than inliers.  
     - After training, calling `.decision_function(X_scaled)` on a new point returns a continuous “anomaly score” (higher means more normal).  
     - Lower scores indicate that the point lies in a region of feature space rarely seen in the baseline, so it’s flagged as an anomaly.

3. **`data/threshold.pkl`**  
   - **What it is:** A single floating‐point number representing the 5th‐percentile of baseline anomaly scores (i.e., the cutoff below which we consider an anomaly).  
   - **Why it’s important:**  
     - During training, we compute:  
       ```python
       scores_baseline = iso.decision_function(X_baseline_scaled)
       threshold = np.percentile(scores_baseline, 5)
       ```  
     - That “5th percentile” means we allow 5 % of baseline data to lie below this cutoff (a small tolerance for natural noise).  
     - For any new sample, if `anomaly_score < threshold`, we classify it as `"anomaly"`. Otherwise, it’s `"normal"`.  
     - Storing `threshold.pkl` lets both `streaming_detect.py` and `detect_anomalies.py` apply the **same** decision boundary that was chosen during training.

---

## How the Model Works

1. **Feature Engineering:**  
   - Baseline data is read from `data/baseline.csv`.  
   - We compute a derived feature:  
     ```
     accel_mag = sqrt(accel_x^2 + accel_y^2 + accel_z^2).
     ```  
   - The full feature vector per row becomes 6‐dimensional.

2. **Scaling (Standardization):**  
   - We fit `StandardScaler` on the 6‐dimensional baseline matrix.  
   - Each feature is transformed to have zero mean and unit variance.

3. **IsolationForest Training:**  
   - We train one `IsolationForest` instance on the scaled baseline matrix. This forest learns the “shape” of normal data in 6‐D.  
   - The `contamination=0.05` parameter tells it that ~5 % of baseline points may be borderline. After training, we still compute anomaly scores on all baseline points to pick an exact threshold.

4. **Threshold Selection:**  
   - We gather all anomaly scores (`iso.decision_function`) on the baseline set.  
   - We set `threshold = 5th percentile` of those scores. This means we accept up to 5 % of baseline scores as “allowed noise,” and anything below that in future is considered a true anomaly.

5. **Detection (Live or Batch):**  
   - **Live (`streaming_detect.py`)**: For each new reading, compute `accel_mag`, scale with `scaler.pkl`, get `anomaly_score = iso_multivar.decision_function(...)`, and compare to `threshold.pkl`. If below threshold, print “ANOMALY DETECTED.” Log all readings to `data/live_data.csv`.  
   - **Batch (`detect_anomalies.py`)**: Load any saved CSV (e.g. `live_data.csv`), recompute `accel_mag`, scale via `scaler.pkl`, compute anomaly scores, label “normal”/“anomaly,” then compute per-feature z-scores vs. baseline and fill `contributing_features` (including “multivariate” fallback). Write results to `data/results/new_data_labeled.csv`.

By storing both the **scaler** and the **IsolationForest** (plus the **threshold**), we guarantee that all future data—whether streaming or saved—gets judged on the exact same scale and decision boundary that the model was trained on.


