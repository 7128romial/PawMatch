# -*- coding: utf-8 -*-
"""
Headless regeneration of data/dogs_final.csv following the academic report's pipeline
(merge -> clean -> categories -> KMeans clustering on 53 breeds -> Isolation Forest).
No matplotlib / no demo code. Produces the report-correct columns.
"""
import sys
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.ensemble import IsolationForest

SRC_DOGS = "data/dogs_dataset 1.csv"
SRC_BREEDS = "data/breeds.csv"
OUT = "data/dogs_final.csv"

# ---- load ----
df_dogs = pd.read_csv(SRC_DOGS)
df_breeds = pd.read_csv(SRC_BREEDS)

# ---- standardize dog columns: 'Age (Years)' -> 'age_years', 'Weight (kg)' -> 'weight_kg', etc. ----
df_dogs.columns = (
    df_dogs.columns.str.lower()
    .str.replace(' ', '_')
    .str.replace('(', '', regex=False)
    .str.replace(')', '', regex=False)
)

# ---- normalize breed values and reconcile the two known mismatches ----
df_dogs['breed'] = df_dogs['breed'].str.strip().str.lower()
df_breeds['breed'] = df_breeds['breed'].str.strip().str.lower()
df_dogs['breed'] = df_dogs['breed'].replace({
    'german shepherd': 'german shepherd dog',
    'schnauzer': 'standard schnauzer',
})

# ---- merge (left join keeps all 3000 dogs) ----
df_merged = pd.merge(df_dogs, df_breeds, on='breed', how='left')
dropped = df_merged['a_adaptability'].isnull().sum()
df_merged = df_merged.dropna(subset=['a_adaptability']).reset_index(drop=True)
print(f"merged rows: {len(df_merged)} | dropped unmatched: {dropped}")

# ---- keep the report's 17 columns (5 physical + 12 behavioral) ----
columns_to_keep = [
    'breed', 'age_years', 'weight_kg', 'color', 'gender',
    'a1_adapts_well_to_apartment_living', 'a2_good_for_novice_owners', 'a4_tolerates_being_alone',
    'b1_affectionate_with_family', 'b2_incredibly_kid_friendly_dogs', 'b3_dog_friendly',
    'c1_amount_of_shedding', 'c2_drooling_potential',
    'd1_easy_to_train', 'd5_tendency_to_bark_or_howl',
    'e1_energy_level', 'e3_exercise_needs',
]
df_final = df_merged[columns_to_keep].copy()

# ---- categorical columns for filtering (report thresholds) ----
def categorize_size(w):
    return 'small' if w <= 15 else ('medium' if w <= 30 else 'large')

def categorize_age(a):
    return 'puppy' if a <= 3 else ('adult' if a <= 8 else 'senior')

color_mapping = {
    'Black': 'dark', 'Brown': 'dark', 'Black and Tan': 'dark',
    'White': 'light', 'Cream': 'light', 'Tan': 'light', 'Gray': 'light',
    'Bicolor': 'mixed', 'Black and White': 'mixed', 'Spotted': 'mixed', 'Brindle': 'mixed', 'Tricolor': 'mixed',
    'Red': 'unique', 'Blue': 'unique', 'Merle': 'unique', 'Sable': 'unique',
}
df_final['size'] = df_final['weight_kg'].apply(categorize_size)
df_final['age_category'] = df_final['age_years'].apply(categorize_age)
df_final['color_category'] = df_final['color'].map(color_mapping)
print("unmapped colors:", df_final[df_final['color_category'].isnull()]['color'].unique().tolist())

# ---- the 10 modelling features ----
FINAL_FEATURES = [
    'a1_adapts_well_to_apartment_living', 'a2_good_for_novice_owners', 'a4_tolerates_being_alone',
    'b2_incredibly_kid_friendly_dogs', 'b3_dog_friendly', 'c1_amount_of_shedding',
    'c2_drooling_potential', 'd1_easy_to_train', 'd5_tendency_to_bark_or_howl', 'e3_exercise_needs',
]

# ---- clustering on the 53 unique breeds (StandardScaler, K=6) ----
df_breeds_unique = df_final[['breed'] + FINAL_FEATURES].drop_duplicates(subset='breed').reset_index(drop=True)
X = StandardScaler().fit_transform(df_breeds_unique[FINAL_FEATURES].values)
kmeans = KMeans(n_clusters=6, random_state=42, n_init=10)
df_breeds_unique['cluster'] = kmeans.fit_predict(X)

CLUSTER_NAMES = {
    0: 'family_active', 1: 'independent_character', 2: 'small_companion',
    3: 'large_working', 4: 'outlier_unique', 5: 'smart_active',
}
df_breeds_unique['cluster_name'] = df_breeds_unique['cluster'].map(CLUSTER_NAMES)
print("cluster sizes:", df_breeds_unique['cluster'].value_counts().sort_index().to_dict())
print("basenji cluster:", df_breeds_unique[df_breeds_unique['breed'] == 'basenji']['cluster'].tolist())

df_final = df_final.merge(df_breeds_unique[['breed', 'cluster', 'cluster_name']], on='breed', how='left')

# ---- Isolation Forest anomaly detection over all 3000 dogs ----
iso = IsolationForest(contamination=0.05, random_state=42, n_estimators=100)
df_final['is_anomaly'] = iso.fit_predict(df_final[FINAL_FEATURES].values)
df_final['anomaly_score'] = iso.decision_function(df_final[FINAL_FEATURES].values)
print("anomalies:", int((df_final['is_anomaly'] == -1).sum()), "/", len(df_final))

df_final.to_csv(OUT, index=False)
print(f"WROTE {OUT} | rows={len(df_final)} cols={len(df_final.columns)}")
print("columns:", df_final.columns.tolist())
