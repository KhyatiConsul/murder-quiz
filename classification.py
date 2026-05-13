import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, ConfusionMatrixDisplay
from itertools import combinations

csv_path = "quiz_responses.csv"
test_size = 0.2
random_state = 42
n_estimators = 300

features = [
    "grief", "rage", "control", "numb", "secrecy", "obsession", "compassion", "trauma", "envy", "chaos", "revenge"
]
palette_age = {
    "Kid": "#F4A261", 
    "Teenager": "#E63946",
    "Young Adult": "#457B9D",
    "Adult": "#2A9D8F",
    "Middle-Aged":"#6A4C93",
    "Senior": "#8D99AE"
}
palette_city = {
    "Mumbai":    "#E63946", "Delhi":     "#457B9D",
    "Bangalore": "#2A9D8F", "Chennai":   "#F4A261",
    "Kolkata":   "#6A4C93", "Hyderabad": "#A8DADC",
    "Jaipur":    "#E9C46A", "Gurugram":  "#264653",
    "Ahmedabad": "#F77F00", "Pune":      "#4CC9F0",
    "Noida":     "#8D99AE",
}

#load and prep

df = pd.read_csv(csv_path)
df["age"] = 2026 - df["birthyear"]
bins = [0, 9, 17, 27, 39, 49, 60]
labels = ["Kid", "Teenager", "Young Adult", "Adult", "Middle-Aged", "Senior"]
df["age_group"] = pd.cut(df["age"], bins= bins, labels=labels).astype(str)

print(f"Loaded {len(df)} rows")
print("Age groups:", df["age_group"].value_counts().to_dict())
print("Cities:", df["city"].value_counts().to_dict())

#trait-comparison

def build_trait_features(data):
    feat_df = data[features].copy()
    for a,b in combinations (features, 2):
        feat_df[f"{a}_vs_{b}"] = data[a] - data[b]
    return feat_df
x_full = build_trait_features(df)
print(f"Total features (raw + parirwise diffs): {x_full.shape[1]}\n")

