import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import KMeans

numerical_cols = ['age_years', 'weight_kg', 'a1_adapts_well_to_apartment_living', 'a2_good_for_novice_owners', 
                  'a4_tolerates_being_alone', 'b1_affectionate_with_family', 'b2_incredibly_kid_friendly_dogs', 
                  'b3_dog_friendly', 'c1_amount_of_shedding', 'c2_drooling_potential', 'd1_easy_to_train', 
                  'd5_tendency_to_bark_or_howl', 'e1_energy_level', 'e3_exercise_needs', 'life_span_min', 'life_span_max']

df_final = None
df_numerical_scaled = None
scaler = MinMaxScaler()
kmeans_model = KMeans(n_clusters=4, random_state=42)

def load_data():
    global df_final, df_numerical_scaled, scaler, kmeans_model
    try:
        df_final = pd.read_csv("data/dogs_final.csv")
        df_numerical_scaled = pd.DataFrame(scaler.fit_transform(df_final[numerical_cols]), columns=numerical_cols, index=df_final.index)
        kmeans_model.fit(df_numerical_scaled)
    except FileNotFoundError:
        print("Error: data/dogs_final.csv not found.")
    except Exception as e:
        print(f"Error loading data: {e}")

def apply_hard_filters(dogs_df, selects, text_params):
    filtered = dogs_df.copy()
    
    color = selects.get('color') or text_params.get('color')
    sex = selects.get('sex') or text_params.get('sex')
    size = selects.get('size') or text_params.get('size')
    hair_length = selects.get('hair_length') or text_params.get('hair_length')
    
    # 1. Physical preferences filtering
    if color:
        temp = filtered[filtered['color'] == color]
        if len(temp) > 0: filtered = temp
            
    if sex:
        temp = filtered[filtered['sex'] == sex]
        if len(temp) > 0: filtered = temp
            
    if size:
        temp = filtered[filtered['size'] == size]
        if len(temp) > 0: filtered = temp
            
    if hair_length and 'hair_length' in filtered.columns:
        temp = filtered[filtered['hair_length'] == hair_length]
        if len(temp) > 0: filtered = temp

    # 2. Text Critical Filtering
    # If allergy mentioned (c1_amount_of_shedding <= 2 implies hypoallergenic needed)
    if text_params.get('c1_amount_of_shedding', 5) <= 2:
        temp = filtered[filtered['c1_amount_of_shedding'] <= 2]
        if len(temp) > 0: filtered = temp
        
    # If small apartment (a1 >= 4)
    if text_params.get('a1_adapts_well_to_apartment_living', 0) >= 4:
        temp = filtered[filtered['weight_kg'] <= 25] # Small/Medium
        if len(temp) > 0: filtered = temp
        
    # If kids (b2 >= 4)
    if text_params.get('b2_incredibly_kid_friendly_dogs', 0) >= 4:
        temp = filtered[filtered['b2_incredibly_kid_friendly_dogs'] >= 4]
        if len(temp) > 0: filtered = temp

    return filtered

def calculate_weighted_score(row, text_params):
    score = 0
    max_score = 0
    
    weights = {
        'a1_adapts_well_to_apartment_living': 30,
        'a4_tolerates_being_alone': 30,
        'b2_incredibly_kid_friendly_dogs': 30,
        'a2_good_for_novice_owners': 30,
        'e1_energy_level': 15,
        'd1_easy_to_train': 15,
        'c1_amount_of_shedding': 15,
        'b1_affectionate_with_family': 5,
        'b3_dog_friendly': 5
    }
    
    for param, user_val in text_params.items():
        if param in weights and param in row:
            w = weights[param]
            max_score += w
            
            # Simple distance normalized to 0-1 (since scale is 1-5)
            # max distance is 4. So diff/4 is percentage wrong.
            dog_val = row[param]
            diff = abs(user_val - dog_val)
            pct_match = max(0, 1 - (diff / 4.0))
            score += w * pct_match
            
    if max_score == 0:
        return 0
    return (score / max_score) * 100

def get_fallback_similar(user_vector, k=3):
    # Cluster pivot and cosine similarity
    similarities = cosine_similarity([user_vector], df_numerical_scaled.values)[0]
    top_indices = np.argsort(similarities)[::-1][:k]
    return df_final.iloc[top_indices]

def recommend_dogs(selects, text_params):
    if df_final is None:
        load_data()
        
    if df_final is None or len(df_final) == 0:
        return {"error": "Dataset not loaded."}
        
    filtered_df = apply_hard_filters(df_final, selects, text_params)
    
    # Calculate weighted scores
    scores = []
    for idx, row in filtered_df.iterrows():
        scores.append(calculate_weighted_score(row, text_params))
        
    filtered_df['match_score'] = scores
    filtered_df = filtered_df.sort_values('match_score', ascending=False)
    
    if len(filtered_df) == 0:
        # Extreme edge case, return similarity
        user_vector = np.full(len(numerical_cols), 0.5) # Default
        for p, v in text_params.items():
            if p in numerical_cols:
                idx = numerical_cols.index(p)
                min_v, max_v = scaler.data_min_[idx], scaler.data_max_[idx]
                user_vector[idx] = (v - min_v) / (max_v - min_v) if max_v > min_v else 0.5
        top_dogs = get_fallback_similar(user_vector, 3)
        return {"type": "partial", "dogs": top_dogs.to_dict(orient="records"), "message": "לא נמצאה התאמה ישירה. הנה הכלבים הדומים ביותר לפרופיל."}

    top_dog = filtered_df.iloc[0]
    
    if top_dog['match_score'] >= 90:
        return {
            "type": "perfect",
            "score": round(top_dog['match_score']),
            "dogs": [top_dog.to_dict()]
        }
    else:
        # Partial match - take top 3
        top_3 = filtered_df.head(3)
        dogs_list = []
        for _, d in top_3.iterrows():
            d_dict = d.to_dict()
            d_dict['match_score'] = round(d['match_score'])
            dogs_list.append(d_dict)
            
        return {
            "type": "partial",
            "dogs": dogs_list
        }
