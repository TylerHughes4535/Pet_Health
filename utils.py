import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def plot_anomalies(df, column='body_temp'):
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    plt.figure(figsize=(12, 6))
    sns.lineplot(x='timestamp', y=column, data=df, label=column)
    sns.scatterplot(
        x='timestamp',
        y=column,
        data=df[df['is_anomaly'] == -1],
        color='red',
        label='Anomaly',
        marker='X',
        s=100
    )
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.title(f"{column} with Anomalies")
    plt.show()
