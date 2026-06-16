import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import KMeans
from sklearn.ensemble import IsolationForest

def safe_int(val, default=None):
    if val is None:
        return default
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return default

numerical_cols = ['age_years', 'weight_kg', 'a1_adapts_well_to_apartment_living', 'a2_good_for_novice_owners', 
                  'a4_tolerates_being_alone', 'b1_affectionate_with_family', 'b2_incredibly_kid_friendly_dogs', 
                  'b3_dog_friendly', 'c1_amount_of_shedding', 'c2_drooling_potential', 'd1_easy_to_train', 
                  'd5_tendency_to_bark_or_howl', 'e1_energy_level', 'e3_exercise_needs', 'life_span_min', 'life_span_max']

# המשקלים הרשמיים מהדו"ח (סכומם שווה ל-1.0)
base_weights = {
    'a1_adapts_well_to_apartment_living': 0.18,
    'e3_exercise_needs': 0.16,
    'a4_tolerates_being_alone': 0.13,
    'd5_tendency_to_bark_or_howl': 0.11,
    'b3_dog_friendly': 0.09,
    'b2_incredibly_kid_friendly_dogs': 0.09,
    'd1_easy_to_train': 0.08,
    'c1_amount_of_shedding': 0.08,
    'a2_good_for_novice_owners': 0.05,
    'c2_drooling_potential': 0.03
}

behavioral_cols = list(base_weights.keys())

df_final = None
df_numerical_scaled = None
scaler = MinMaxScaler()
kmeans_model = KMeans(n_clusters=6, random_state=42)
# Anomaly detector (innovation layer 2): flags behaviorally unusual dogs (e.g. the outlier Basenji profile)
iso_forest = IsolationForest(n_estimators=100, contamination=0.05, random_state=42)

def load_data():
    global df_final, df_numerical_scaled, scaler, kmeans_model, iso_forest
    try:
        df_final = pd.read_csv("data/dogs_final.csv")
        df_numerical_scaled = pd.DataFrame(scaler.fit_transform(df_final[numerical_cols]), columns=numerical_cols, index=df_final.index)
        kmeans_model.fit(df_numerical_scaled)
        df_final['cluster'] = kmeans_model.labels_
        # Isolation Forest anomaly detection on the behavioral profile (-1 = outlier, 1 = normal)
        df_final['is_outlier'] = iso_forest.fit_predict(df_numerical_scaled[behavioral_cols])
    except FileNotFoundError:
        print("Error: data/dogs_final.csv not found.")
    except Exception as e:
        print(f"Error loading data: {e}")

def apply_hard_filters(dogs_df, selects, text_params):
    filtered = dogs_df.copy()
    
    color = selects.get('color') or text_params.get('color')
    sex = selects.get('sex') or text_params.get('sex')
    size = selects.get('size') or text_params.get('size')
    age_group = selects.get('age_group') or text_params.get('age_group')
    
    # 1. Physical / Breed preferences filtering
    breed_preference = text_params.get('breed_preference')
    if breed_preference:
        temp = filtered[filtered['breed'] == breed_preference]
        if len(temp) > 0:
            filtered = temp

    if color and color != "No Preference":
        temp = filtered[filtered['color'] == color]
        if len(temp) > 0: filtered = temp
            
    if sex and sex != "No Preference":
        temp = filtered[filtered['sex'] == sex]
        if len(temp) > 0: filtered = temp
            
    if size and size != "No Preference" and 'weight_kg' in filtered.columns:
        # Derive size from the real weight (report thresholds), not the noisy 'size' column,
        # so each breed maps to a realistic size and the breed-alternative fallback can work.
        size_lower = str(size).lower()
        if size_lower == 'small':
            temp = filtered[filtered['weight_kg'] <= 15]
        elif size_lower == 'medium':
            temp = filtered[(filtered['weight_kg'] > 15) & (filtered['weight_kg'] <= 30)]
        elif size_lower == 'large':
            temp = filtered[filtered['weight_kg'] > 30]
        else:
            temp = filtered
        if len(temp) > 0: filtered = temp
            
    if age_group and age_group != "No Preference" and 'age_years' in filtered.columns:
        if isinstance(age_group, str):
            age_group_lower = age_group.lower()
            if age_group_lower == 'puppy':
                temp = filtered[filtered['age_years'] <= 1.5]
            elif age_group_lower == 'adult':
                temp = filtered[(filtered['age_years'] > 1.5) & (filtered['age_years'] < 8)]
            elif age_group_lower == 'senior':
                temp = filtered[filtered['age_years'] >= 8]
            else:
                temp = filtered
            if len(temp) > 0:
                filtered = temp

    # 2. Text Critical Filtering
    # If allergy mentioned (c1_amount_of_shedding <= 2 implies hypoallergenic needed)
    c1_val = safe_int(text_params.get('c1_amount_of_shedding'), 5)
    if c1_val <= 2:
        temp = filtered[filtered['c1_amount_of_shedding'] <= 2]
        if len(temp) > 0: filtered = temp
        
    # If small apartment (a1 >= 4)
    a1_val = safe_int(text_params.get('a1_adapts_well_to_apartment_living'), 0)
    if a1_val >= 4:
        temp = filtered[filtered['weight_kg'] <= 25] # Small/Medium
        if len(temp) > 0: filtered = temp
        
    # If kids (b2 >= 4)
    b2_val = safe_int(text_params.get('b2_incredibly_kid_friendly_dogs'), 0)
    if b2_val >= 4:
        temp = filtered[filtered['b2_incredibly_kid_friendly_dogs'] >= 4]
        if len(temp) > 0: filtered = temp

    return filtered

def calculate_weighted_cosine_similarity(user_params, df_target):
    """
    מנוע ה-ML החדש: מחשב דמיון קוסינוס משוקלל אמיתי ומטריציוני
    בין פרופיל המאמץ שחולץ לכל הכלבים שעברו את הסינון הראשוני.
    מחזיר מערך numpy של ציונים באחוזים (0-100), שורה לכל כלב ב-df_target.
    """
    # בניית וקטור המשתמש (ערך ברירת מחדל 3 לתכונות שלא עלו בשיחה)
    user_vector = np.array([float(safe_int(user_params.get(col), 3)) for col in behavioral_cols])

    # בניית מטריצת הכלבים מתוך המאגר המסונן
    dogs_matrix = df_target[behavioral_cols].fillna(3).values

    # וקטור המשקלים המנורמל
    weights = np.array([base_weights[col] for col in behavioral_cols])
    weights_normalized = weights / np.sum(weights)

    # הטמעת המשקלים בוקטורים (מכפילים בשורש המשקל לטובת דמיון קוסינוס משוקלל תקין)
    sqrt_weights = np.sqrt(weights_normalized)
    user_weighted = user_vector * sqrt_weights
    dogs_weighted = dogs_matrix * sqrt_weights

    # חישוב דמיון קוסינוס בריצה מטריציונית מהירה
    similarities = cosine_similarity([user_weighted], dogs_weighted)[0]

    # החזרת הציון באחוזים (0-100)
    return similarities * 100

def clean_dict(d):
    clean = {}
    for k, v in d.items():
        if isinstance(v, (np.integer, np.int64)):
            clean[k] = int(v)
        elif isinstance(v, (np.floating, np.float64)):
            clean[k] = float(v) if not np.isnan(v) else None
        elif isinstance(v, np.ndarray):
            clean[k] = v.tolist()
        elif isinstance(v, (list, dict)):
            clean[k] = v
        elif pd.isna(v):
            clean[k] = None
        else:
            clean[k] = v
    return clean

def get_fallback_similar(user_vector, target_df=None, k=5):
    if target_df is None:
        target_df = df_final
    # Scale behavior columns only for the selected sub-dataframe indices
    df_behavior = df_numerical_scaled.loc[target_df.index, behavioral_cols]
    similarities = cosine_similarity([user_vector], df_behavior.values)[0]
    top_indices = np.argsort(similarities)[::-1][:k]
    return target_df.iloc[top_indices]

def recommend_dogs(selects, text_params, lang='he'):
    if df_final is None:
        load_data()
        
    if df_final is None or len(df_final) == 0:
        return {"error": "Dataset not loaded."}
        
    breed_preference = text_params.get('breed_preference')

    # Standard hard filtering (includes the breed filter when a breed was requested)
    filtered_df = apply_hard_filters(df_final, selects, text_params).copy()

    # --- Section #12: smart breed-alternative fallback ---
    # If a specific breed was requested but none of that breed survived the hard
    # filters, search by the requested breed's behavioral profile instead of the
    # user's, to surface dogs that BEHAVE like the breed the user hoped for.
    fallback_to_breed_vector = False
    if breed_preference:
        has_requested_breed = len(filtered_df[filtered_df['breed'].str.lower() == str(breed_preference).lower()]) > 0
        if not has_requested_breed:
            fallback_to_breed_vector = True
            # Re-run the physical filters WITHOUT the breed filter so similar breeds can surface
            tp_no_breed = {k: v for k, v in text_params.items() if k != 'breed_preference'}
            filtered_df = apply_hard_filters(df_final, selects, tp_no_breed).copy()

    if len(filtered_df) == 0:
        msg = ("אנחנו מצטערים, אבל לא נמצאו כלבים שתואמים את הסינון הבסיסי שבחרת. "
               "נסו לשנות את ההעדפות הפיזיות (גודל / גיל / צבע) ונשמח לעזור!") if lang == 'he' else \
              ("We're sorry, but no dogs matched your basic filters. "
               "Try adjusting the physical preferences (size / age / color) and we'll be happy to help!")
        return {"type": "result", "dogs": [], "message": msg}

    # Choose the search vector: the requested breed's behavioral profile, or the user's.
    if fallback_to_breed_vector:
        breed_row = df_final[df_final['breed'].str.lower() == str(breed_preference).lower()]
        if len(breed_row) > 0:
            # Use the requested breed's behavioral values as the query profile
            search_params = {col: breed_row.iloc[0][col] for col in behavioral_cols}
        else:
            # Breed not present in the dataset at all -> fall back to the user's own profile
            search_params = text_params
            fallback_to_breed_vector = False

    else:
        search_params = text_params

    filtered_df['match_score'] = calculate_weighted_cosine_similarity(search_params, filtered_df)

    # Apply the strict 75% match threshold, then sort.
    filtered_df = filtered_df[filtered_df['match_score'] >= 75]
    filtered_df = filtered_df.sort_values('match_score', ascending=False)

    if len(filtered_df) == 0:
        msg = ("אנחנו מצטערים, אבל כרגע אין לנו כלבים במאגר שפוגשים את הדרישות שלך בהתאמה מספקת (מעל 75%). "
               "נשמח לעזור אם משהו ישתנה בעתיד, תחזרו אלינו!") if lang == 'he' else \
              ("We are sorry, but currently we have no dogs in our database that meet your requirements with a high enough match (>75%). "
               "We'd be happy to help if anything changes in the future, please come back!")
        return {"type": "result", "dogs": [], "message": msg}

    # Take top 3 (is_outlier from the Isolation Forest is preserved on each row - Section #11)
    top_3 = filtered_df.head(3)
    dogs_list = []
    for _, d in top_3.iterrows():
        d_dict = d.to_dict()
        d_dict['match_score'] = int(round(d['match_score']))
        dogs_list.append(clean_dict(d_dict))

    msg = None
    if fallback_to_breed_vector:
        msg = (f"לא מצאנו כלבי {breed_preference} שמתאימים לסינון שלך כרגע, אבל מצאנו כלבים עם אופי התנהגותי דומה מאוד לגזע הזה."
               if lang == 'he' else
               f"We couldn't find any {breed_preference} matching your filters right now, but we found dogs with a very similar behavioral profile.")

    return {"type": "result", "dogs": dogs_list, "message": msg,
            "fallback_to_breed_vector": fallback_to_breed_vector,
            "breed_requested": breed_preference if fallback_to_breed_vector else None}
