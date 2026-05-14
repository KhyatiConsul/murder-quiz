import matplotlib
matplotlib.use("Agg")

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import warnings
import datetime
warnings.filterwarnings("ignore")

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, ConfusionMatrixDisplay
from itertools import combinations

csv_path = "quiz_responses.csv"
test_size = 0.2
random_state = 42
n_estimators = 300
current_year = datetime.date.today().year

features = [
    "grief", "rage", "control", "numb", "secrecy", "obsession", "compassion", "trauma", "envy", "chaos", "revenge"
]
age_order = ["Kid", "Teenager", "Young Adult", "Adult", "Middle-Aged", "Senior"]
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

n_traits = len(features)
angles = np.linspace(0, 2 * np.pi, n_traits, endpoint=False).tolist() + [0]
angle_deg = np.degrees(angles[:-1])

def savefig(name):
    plt.savefig(name, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved: {name}")

def age_to_group(age):
    if   age <= 9:  return "Kid"
    elif age <= 17: return "Teenager"
    elif age <= 27: return "Young Adult"
    elif age <= 39: return "Adult"
    elif age <= 49: return "Middle-Aged"
    elif age <= 60: return "Senior"
    return None

def plot_radar(ax, means_row, color, title, top_trait):
    vals = means_row.values.tolist() + [means_row.values[0]]
    ax.plot(angles, vals, color=color, linewidth=2)
    ax.fill(angles, vals, color=color, alpha=0.25)
    ax.set_thetagrids(angle_deg, labels=features, fontsize=8)
    ax.set_ylim(0, 4)
    ax.set_yticks([1, 2, 3, 4])
    ax.set_yticklabels(["1", "2", "3", "4"], size=7, color="grey")
    ax.set_title(title, size=12, fontweight="bold", color=color, pad=12)
    ax.annotate(f"↑ {top_trait}", xy=(0.5, -0.12), xycoords="axes fraction",
                ha="center", fontsize=9, color=color, fontstyle="italic")
 
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
    fig.tight_layout()
    savefig(filename)

#load and prep

df = pd.read_csv(csv_path)
df["age"] = current_year - df["birthyear"]
df["age_group"] = df["age"].apply(age_to_group)
df = df.dropna(subset=["age_group"])

print(f"Loaded {len(df)} rows")
print("Age groups:", df["age_group"].value_counts().to_dict())
print("Cities:", df["city"].value_counts().to_dict())

#trait-comparison

def build_trait_features(data):
    feat_df = data[features].copy()
    for a,b in combinations (features, 2):
        feat_df[f"{a}_vs_{b}"] = data[a].values - data[b].values
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

for i, grp in enumerate(age_order):
    for j, trait in enumerate(features):
        ax.text(j, i, f"{age_means.loc[grp, trait]:.1f}",
                ha="center", va="center", fontsize=9, color="black", fontweight="bold")
plt.colorbar(im, ax=ax, label="Normalised Intensity")
ax.set_title("Trait Dominance by Age Group", fontsize=14, fontweight="bold", pad=12)
plt.tight_layout()
savefig("age_trait_heatmap.png")

#2. Radar charts
fig, axes = plt.subplots(2,3, figsize=(14,9), subplot_kw=dict(polar=True))
fig.suptitle("Emotional Trait Profiles- Age Groups", fontsize=15, fontweight="bold")

for ax, grp in zip(axes.flatten(), age_order):
    plot_radar(ax, age_means.loc[grp], palette_age[grp], grp, age_means.loc[grp].idxmax())
    
fig.tight_layout()
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
fig.tight_layout()
savefig("age_dominant_traits.png")

# 4. Confusion Matrix
plot_confusion_matrix(y_te_age, y_pred_age, age_order,
                      "Confusion Matrix- Age Group", "Greens", "age_confusion_matrix.png")

# City Classification Visualisations

city_order = sorted(df["city"].unique().tolist())
city_means = df.groupby("city")[features].mean().loc[city_order]
n_cities = len(city_order)

# 1. Heatmap
fig, ax = plt.subplots(figsize=(13,7))
data_norm_c=(city_means-city_means.min())/(city_means.max()-city_means.min())
im2= ax.imshow(data_norm_c.values, cmap="Blues", aspect="auto", vmin=0, vmax=1)
ax.set_xticks(range(len(features)))
ax.set_xticklabels(features, rotation=35, ha="right", fontsize=11)
ax.set_yticks(range(n_cities))
ax.set_yticklabels(city_order, fontsize=11)

for i, city in enumerate(city_order):
    for j, trait in enumerate(features):
        ax.text(j, i, f"{city_means.loc[city, trait]:.1f}",
                ha="center", va="center", fontsize=9, color="black", fontweight="bold")
plt.colorbar(im2, ax=ax, label="Normalised Intensity")
ax.set_title("Trait Dominance by City", fontsize=14, fontweight="bold", pad=12)
fig.tight_layout()
savefig("city_trait_heatmap.png")

# 2. Top3 Traits per city (dot chart)
trait_idx = {t:i for i,t in enumerate(features)}
fig, ax = plt.subplots(figsize=(12, 7))
for ci, city in enumerate(city_order):
    for rank, (trait, val) in enumerate(
            city_means.loc[city].sort_values(ascending=False).head(3).items()):
        size  = [220, 140, 80][rank]
        alpha = [1.0, 0.70, 0.50][rank]
        ax.scatter(trait_idx[trait], ci, s=size,
                   color=palette_city.get(city, "#888"), alpha=alpha, zorder=3)
        ax.text(trait_idx[trait], ci + 0.32,
                f"{val:.1f}", ha="center", fontsize=7.5, color="#333")
    
ax.set_xticks(range(len(features)))
ax.set_xticklabels(features, fontsize=11, rotation=25, ha="right")
ax.set_yticks(range(n_cities))
ax.set_yticklabels(city_order, fontsize=11)
ax.set_xlim(-0.6, len(features) - 0.4)
ax.set_ylim(-0.8, n_cities - 0.3)
ax.grid(alpha=0.2)
ax.set_title("Top-3 Dominant Traits per City  (size = rank, label = mean score)",
             fontsize=13, fontweight="bold")
fig.tight_layout()
savefig("city_top_traits_dot.png")

# 3. City Radar
n_cols = 6
n_rows = (n_cities + n_cols - 1) // n_cols
fig, axes = plt.subplots(n_rows, n_cols, figsize=(22, 8), subplot_kw=dict(polar=True))
fig.suptitle("Emotional Trait Profiles — Cities", fontsize=15, fontweight="bold")
axes_flat = axes.flatten()
 
for idx, city in enumerate(city_order):
    plot_radar(axes_flat[idx], city_means.loc[city],
               palette_city.get(city, "#888"), city,
               city_means.loc[city].idxmax())
 
for idx in range(n_cities, len(axes_flat)):
    axes_flat[idx].set_visible(False)

plt.tight_layout()
savefig("city_radar_profiles.png")

# Confusion Matrix for City
plot_confusion_matrix(y_te_city, y_pred_city, city_order,
                      "Confusion Matrix — City", "Blues",
                      "city_confusion_matrix.png")

# Age vs City

def rolled_importance(rf):
    fi = pd.Series(rf.feature_importances_, index=x_full.columns)
    trait_scores = {t: 0.0 for t in features}
    for fname, imp in fi.items():
        tokens = fname.replace("_vs_", "|").split("|")
        for t in features:
            if t in tokens:
                trait_scores[t] += imp
    total = sum(trait_scores.values())
    return {k: v / total for k, v in trait_scores.items()}
 
fi_age  = rolled_importance(rf_age)
fi_city = rolled_importance(rf_city)
fi_df = pd.DataFrame({"Age Group": fi_age, "City": fi_city}).sort_values("Age Group")
 
traits  = fi_df.index.tolist()
n       = len(traits)
x       = np.arange(n)
fig, ax = plt.subplots(figsize=(10, 6))
 
bars1 = ax.barh(x - 0.2, fi_df["Age Group"].values, height=0.36,
                label="Age Group", color="#1D9E75", alpha=0.88)
bars2 = ax.barh(x + 0.2, fi_df["City"].values,      height=0.36,
                label="City",      color="#378ADD", alpha=0.88)
 
for bar in bars1:
    w = bar.get_width()
    ax.text(w + 0.002, bar.get_y() + bar.get_height() / 2,
            f"{w:.3f}", va="center", ha="left", fontsize=8, color="#1D9E75")
for bar in bars2:
    w = bar.get_width()
    ax.text(w + 0.002, bar.get_y() + bar.get_height() / 2,
            f"{w:.3f}", va="center", ha="left", fontsize=8, color="#378ADD")
 
ax.set_yticks(x)
ax.set_yticklabels(traits, fontsize=11)
ax.set_ylim(-0.6, n - 0.4)
ax.set_xlim(0, fi_df.values.max() * 1.35)
ax.set_xlabel("Relative trait importance", fontsize=11)
ax.set_title("Which Traits Matter Most — Age Group vs City",
             fontsize=13, fontweight="bold")
ax.legend(fontsize=10)
ax.grid(axis="x", alpha=0.3)
plt.tight_layout()
savefig("feature_importance_comparison.png")