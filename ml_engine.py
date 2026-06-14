import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import KMeans

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

behavioral_cols = [
    'a1_adapts_well_to_apartment_living',
    'e3_exercise_needs',
    'a4_tolerates_being_alone',
    'd5_tendency_to_bark_or_howl',
    'c1_amount_of_shedding',
    'b3_dog_friendly',
    'b2_incredibly_kid_friendly_dogs',
    'd1_easy_to_train',
    'a2_good_for_novice_owners',
    'c2_drooling_potential'
]

df_final = None
df_numerical_scaled = None
scaler = MinMaxScaler()
kmeans_model = KMeans(n_clusters=6, random_state=42)

def load_data():
    global df_final, df_numerical_scaled, scaler, kmeans_model
    try:
        df_final = pd.read_csv("data/dogs_final.csv")
        df_numerical_scaled = pd.DataFrame(scaler.fit_transform(df_final[numerical_cols]), columns=numerical_cols, index=df_final.index)
        kmeans_model.fit(df_numerical_scaled)
        df_final['cluster'] = kmeans_model.labels_
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
            
    if size and size != "No Preference":
        temp = filtered[filtered['size'] == size]
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

def calculate_weighted_score(row, text_params):
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
    
    level_a = {
        'a1_adapts_well_to_apartment_living',
        'e3_exercise_needs',
        'a4_tolerates_being_alone',
        'd5_tendency_to_bark_or_howl'
    }
    
    # Identify active parameters for renormalization:
    # Level A parameters are always active. Level B/C are active only if present in text_params.
    active_params = []
    for p in base_weights:
        if p in level_a or p in text_params:
            active_params.append(p)
            
    weight_sum = sum(base_weights[p] for p in active_params)
    if weight_sum == 0:
        weight_sum = 1.0
        
    score = 0.0
    for p in active_params:
        w_norm = base_weights[p] / weight_sum
        
        if p in text_params:
            user_val = text_params[p]
            # Convert to numeric if possible (e.g. float or string number)
            user_val_num = safe_int(user_val, None)
            if user_val_num is not None:
                dog_val = row[p]
                if pd.isna(dog_val):
                    pct_match = 0.80
                else:
                    diff = abs(user_val_num - dog_val)
                    pct_match = max(0, 1 - (diff / 4.0))
                score += w_norm * pct_match
            else:
                score += w_norm * 0.85
        else:
            # Unspecified Level A parameters get a default match of 80% to prevent score inflation
            score += w_norm * 0.80
            
    return score * 100

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
        
    # Check if a specific breed was requested but is not in our database
    breed_preference = text_params.get('breed_preference')
    breed_not_found = False
    if breed_preference:
        if len(df_final[df_final['breed'] == breed_preference]) == 0:
            breed_not_found = True
            
    filtered_df = apply_hard_filters(df_final, selects, text_params)
    
    # Calculate weighted scores
    scores = []
    for idx, row in filtered_df.iterrows():
        scores.append(calculate_weighted_score(row, text_params))
        
    filtered_df = filtered_df.copy()
    filtered_df['match_score'] = scores
    
    # Apply strict 75% threshold
    filtered_df = filtered_df[filtered_df['match_score'] >= 75]
    filtered_df = filtered_df.sort_values('match_score', ascending=False)
    
    if len(filtered_df) == 0:
        msg = ("אנחנו מצטערים, אבל כרגע אין לנו כלבים במאגר שפוגשים את הדרישות שלך בהתאמה מספקת (מעל 75%). "
               "נשמח לעזור אם משהו ישתנה בעתיד, תחזרו אלינו!") if lang == 'he' else \
              ("We are sorry, but currently we have no dogs in our database that meet your requirements with a high enough match (>75%). "
               "We'd be happy to help if anything changes in the future, please come back!")
        return {"type": "result", "dogs": [], "message": msg}

    # Take top 3
    top_3 = filtered_df.head(3)
    dogs_list = []
    for _, d in top_3.iterrows():
        d_dict = d.to_dict()
        d_dict['match_score'] = int(round(d['match_score']))
        dogs_list.append(clean_dict(d_dict))
        
    msg = None
    if breed_not_found:
        msg = f"לא מצאנו כלבי {breed_preference} כרגע במאגר לאימוץ, אך מצאנו את הכלבים הבאים שמתאימים לכם." if lang == 'he' else f"We couldn't find any {breed_preference} dogs available for adoption right now, but we found these great matches."
        
    return {"type": "result", "dogs": dogs_list, "message": msg}
