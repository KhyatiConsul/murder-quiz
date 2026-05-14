import matplotlib
matplotlib.use("Agg")

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings("ignore")

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

def savefig(name):
    plt.savefig(name, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved: {name}")

#load and prep

df = pd.read_csv(csv_path)
df["age"] = 2026 - df["birthyear"]
bins = [0, 9, 17, 27, 39, 49, 60]
age_order = ["Kid", "Teenager", "Young Adult", "Adult", "Middle-Aged", "Senior"]
df["age_group"] = pd.cut(df["age"], bins= bins, labels=age_order).astype(str)

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

# Train models

def train_model(X, y, label):
    rf = RandomForestClassifier(n_estimators = n_estimators,
                                random_state = random_state, n_jobs=-1)
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=random_state)
    cv_scores = cross_val_score(rf, X, y, cv=cv, scoring="accuracy")
    X_tr, X_te, y_tr, y_te = train_test_split(
        X,y, test_size=test_size, random_state=random_state, stratify=y)
    rf.fit(X_tr, y_tr)
    y_pred = rf.predict(X_te)
    print(f"{label.upper()}")
    print(f"5-Fold CV Accuracy: {cv_scores.mean():.3f} +- {cv_scores.std():.3f}\n")
    print(f"Test Accuracy: {accuracy_score(y_te, y_pred):.3f}\n")
    print(classification_report(y_te, y_pred))
    return rf, y_te, y_pred

rf_age, y_te_age, y_pred_age = train_model(x_full, df["age_group"], "Age Group")
rf_city, y_te_city, y_pred_city = train_model(x_full, df["city"], "City")

# Age Group Visulaization

age_means = df.groupby("age_group")[features].mean().loc[age_order]

# 1. Heatmap
fig, ax = plt.subplots(figsize=(13,5))
data_norm = (age_means-age_means.min())/(age_means.max()-age_means.min())
im = ax.imshow(data_norm.values, cmap="RdYlGn", aspect="auto", vmin=0, vmax=1)
ax.set_xticks(range(len(features)))
ax.set_xticklabels(features, rotation=35, ha="right", fontsize=11)
ax.set_yticks(range(len(age_order)))
ax.set_yticklabels(age_order, fontsize=11)
for i in range(len(age_order)):
    for j in range(len(features)):
        v = age_means.values[i, j]
        ax.text(j, i, f"{v:.1f}", ha="center", va="center", fontsize=9, color="black", fontweight="bold")
plt.colorbar(im, ax=ax, label="Normalised Intensity")
ax.set_title("Trait Dominance by Age Group", fontsize=14, fontweight="bold", pad=12)
plt.tight_layout()
savefig("age_trait_heatmap.png")

#2. Radar charts
n = len(features)
angles = np.linspace(0, 2*np.pi, n, endpoint=False).tolist()
angles += angles[:1]

fig, axes = plt.subplots(2,3, figsize=(14,9), subplot_kw=dict(polar=True))
fig.suptitle("Emotional Trait Profiles- Age Groups", fontsize=15, fontweight="bold")
axes= axes.flatten()

for idx, grp in enumerate(age_order):
    ax = axes[idx]
    vals = age_means.loc[grp].values.tolist() + [age_means.loc[grp].values[0]]
    color = palette_age[grp]
    ax.plot(angles, vals, color=color, linewidth=2)
    ax.fill(angles, vals, color=color, alpha=0.25)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(features, size=8)
    ax.set_ylim(0,4)
    ax.set_yticks([1,2,3,4])
    ax.set_yticklabels(["1", "2", "3", "4"], size=7, color="grey")
    ax.set_title(grp, size=12, fontweight="bold", color=color, pad=12)
    top_trait = age_means.loc[grp].idxmax()
    ax.annotate(f"{top_trait}", xy=(0.5,-0.12), xycoords="axes fraction",
                ha="center", fontsize=9, color=color, fontstyle="italic")
    
plt.tight_layout()
savefig("age_radar_profiles.png")

# 3. Dominant & weakest trait per age group
fig, ax = plt.subplots(figsize=(10,5))
x = np.arange(len(age_order))
top_vals = age_means.max(axis=1).values
bot_vals = age_means.min(axis=1).values
top_traits = age_means.idxmax(axis=1).values
bot_traits = age_means.idxmin(axis=1).values
colors = [palette_age[g] for g in age_order]

ax.bar(x, top_vals, color=colors, alpha=0.85, edgecolor="white",
       linewidth=1.2, label="Dominant Trait")
ax.bar(x, bot_vals, color=colors, alpha=0.3, edgecolor="white",
       linewidth=1.2, label="Weakest Trait")

for i in range(len(age_order)):
    ax.text(x[i], top_vals[i] + 0.05, f"{top_traits[i]}\n({top_vals[i]:.2f})",
            ha="center", va="bottom", fontsize=9, fontweight="bold", color=colors[i])
    ax.text(x[i], bot_vals[i] - 0.05, f"{bot_traits[i]}\n({bot_vals[i]:.2f})",
            ha="center", va="top", fontsize=9, color="grey")
    
ax.set_xticks(x)
ax.set_xticklabels(age_order, fontsize=11)
ax.set_ylim(0,5)
ax.set_ylabel("Mean score (0-4)", fontsize=11)
ax.set_title("Strongest & Weakest Trait per Age Group", fontsize=13, fontweight="bold")
ax.legend(fontsize=9)
ax.grid(axis="y", alpha=0.3)
savefig("age_dominant_traits.png")

# 4. Confusion Matrix
def plot_confusion_matrix(y_true, y_pred, labels, title, cmap, filename):
    cm = confusion_matrix(y_true, y_pred, labels=labels)
    fig, ax = plt.subplots(figsize=(8, 6))
    im = ax.imshow(cm, cmap=cmap, aspect="auto")
    plt.colorbar(im, ax=ax)
    ax.set_xticks(range(len(labels)))
    ax.set_yticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=35, ha="right", fontsize=10)
    ax.set_yticklabels(labels, fontsize=10)
    ax.set_xlabel("Predicted", fontsize=11)
    ax.set_ylabel("Actual", fontsize=11)
    ax.set_title(title, fontsize=13, fontweight="bold")
    thresh = cm.max() / 2
    for i in range(len(labels)):
        for j in range(len(labels)):
            ax.text(j, i, str(cm[i, j]), ha="center", va="center",
                    fontsize=12, fontweight="bold",
                    color="white" if cm[i, j] > thresh else "black")
    plt.tight_layout()
    savefig(filename)
 
plot_confusion_matrix(y_te_age, y_pred_age, age_order, "Confusion Matrix — Age Group", 
                      "Greens", "age_confusion_matrix.png")