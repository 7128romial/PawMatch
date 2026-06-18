import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity


def safe_int(val, default=None):
    if val is None:
        return default
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return default


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

# Maps the raw color values (and the front-end color buttons) to the 4 color categories
# that the data pipeline produced in the color_category column.
COLOR_TO_CATEGORY = {
    'Black': 'dark', 'Brown': 'dark', 'Black and Tan': 'dark',
    'White': 'light', 'Cream': 'light', 'Tan': 'light', 'Gray': 'light',
    'Bicolor': 'mixed', 'Black and White': 'mixed', 'Spotted': 'mixed', 'Brindle': 'mixed', 'Tricolor': 'mixed',
    'Red': 'unique', 'Blue': 'unique', 'Merle': 'unique', 'Sable': 'unique',
}

df_final = None


def load_data():
    # The dataset is fully prepared offline by regenerate_dataset.py (merge, categories,
    # KMeans clustering -> cluster/cluster_name, Isolation Forest -> is_anomaly). Here we
    # only load it; no clustering/anomaly is recomputed at runtime.
    global df_final
    try:
        df_final = pd.read_csv("data/dogs_final.csv")
    except FileNotFoundError:
        print("Error: data/dogs_final.csv not found.")
    except Exception as e:
        print(f"Error loading data: {e}")


def apply_hard_filters(dogs_df, selects, text_params):
    """Hard (binary) physical filters on the precomputed categorical columns:
    size, age_category, gender, color_category. A True hard filter — it can return 0 rows
    (matching the report; the 'too specific -> no result' case comes from here)."""
    filtered = dogs_df.copy()

    color = selects.get('color') or text_params.get('color')
    sex = selects.get('sex') or text_params.get('sex')
    size = selects.get('size') or text_params.get('size')
    age_group = selects.get('age_group') or text_params.get('age_group')

    if size and size != "No Preference" and 'size' in filtered.columns:
        filtered = filtered[filtered['size'] == str(size).lower()]

    if age_group and age_group != "No Preference" and 'age_category' in filtered.columns:
        filtered = filtered[filtered['age_category'] == str(age_group).lower()]

    if sex and sex != "No Preference" and 'gender' in filtered.columns:
        filtered = filtered[filtered['gender'] == sex]

    if color and color != "No Preference" and 'color_category' in filtered.columns:
        # Accept either a category directly (dark/light/mixed/unique) or a raw color to map.
        category = COLOR_TO_CATEGORY.get(color, str(color).lower())
        filtered = filtered[filtered['color_category'] == category]

    return filtered


def calculate_weighted_cosine_similarity(user_params, df_target):
    """
    מנוע ה-ML: מחשב דמיון קוסינוס משוקלל אמיתי ומטריציוני בין פרופיל המאמץ
    לכל הכלבים שעברו את הסינון. מחזיר מערך numpy של ציונים באחוזים (0-100).
    """
    # בניית וקטור המשתמש (ערך ברירת מחדל 3 לתכונות שלא עלו בשיחה)
    user_vector = np.array([float(safe_int(user_params.get(col), 3)) for col in behavioral_cols])

    # בניית מטריצת הכלבים מתוך המאגר המסונן
    dogs_matrix = df_target[behavioral_cols].fillna(3).values

    # וקטור המשקלים המנורמל
    weights = np.array([base_weights[col] for col in behavioral_cols])
    weights_normalized = weights / np.sum(weights)

    # הטמעת המשקלים בוקטורים (מכפילים בשורש המשקל לדמיון קוסינוס משוקלל תקין)
    sqrt_weights = np.sqrt(weights_normalized)
    user_weighted = user_vector * sqrt_weights
    dogs_weighted = dogs_matrix * sqrt_weights

    similarities = cosine_similarity([user_weighted], dogs_weighted)[0]
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


def recommend_dogs(selects, text_params, lang='he'):
    if df_final is None:
        load_data()

    if df_final is None or len(df_final) == 0:
        return {"error": "Dataset not loaded."}

    breed_preference = text_params.get('breed_preference')

    # Physical hard filters only (size/age/gender/color). Breed is handled separately below.
    filtered_df = apply_hard_filters(df_final, selects, text_params).copy()

    # --- Section #12: smart breed-alternative fallback ---
    # If a specific breed was requested but none of it survived the physical filters,
    # search by the requested breed's behavioral profile to surface dogs that BEHAVE
    # like the breed the user hoped for.
    fallback_to_breed_vector = False
    if breed_preference:
        breed_mask = filtered_df['breed'].str.lower() == str(breed_preference).lower()
        if breed_mask.any():
            filtered_df = filtered_df[breed_mask].copy()
        else:
            fallback_to_breed_vector = True  # requested breed not available within the filters

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
            search_params = {col: breed_row.iloc[0][col] for col in behavioral_cols}
        else:
            search_params = text_params
            fallback_to_breed_vector = False
    else:
        search_params = text_params

    filtered_df['match_score'] = calculate_weighted_cosine_similarity(search_params, filtered_df)

    # Strict 75% match threshold, then sort.
    filtered_df = filtered_df[filtered_df['match_score'] >= 75]
    filtered_df = filtered_df.sort_values('match_score', ascending=False)

    if len(filtered_df) == 0:
        msg = ("אנחנו מצטערים, אבל כרגע אין לנו כלבים במאגר שפוגשים את הדרישות שלך בהתאמה מספקת (מעל 75%). "
               "נשמח לעזור אם משהו ישתנה בעתיד, תחזרו אלינו!") if lang == 'he' else \
              ("We are sorry, but currently we have no dogs in our database that meet your requirements with a high enough match (>75%). "
               "We'd be happy to help if anything changes in the future, please come back!")
        return {"type": "result", "dogs": [], "message": msg}

    # Take top 5 (is_anomaly from the Isolation Forest is preserved on each row - Section #11)
    top_5 = filtered_df.head(5)
    dogs_list = []
    for _, d in top_5.iterrows():
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
