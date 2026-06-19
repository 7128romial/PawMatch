import pandas as pd
from ml_engine import calculate_weighted_cosine_similarity, apply_hard_filters, load_data

load_data()
from ml_engine import df_final

profiles = [
    {
        "name": "Apartment dweller, lazy, works 9 hours",
        "selects": {"size": "Small", "age_group": "Adult"},
        "text_params": {
            "a1_adapts_well_to_apartment_living": 5,
            "e3_exercise_needs": 1,
            "a4_tolerates_being_alone": 5,
            "d5_tendency_to_bark_or_howl": 1
        }
    },
    {
        "name": "Active runner, house with yard, home all day",
        "selects": {"size": "Large", "age_group": "Young"},
        "text_params": {
            "a1_adapts_well_to_apartment_living": 1,
            "e3_exercise_needs": 5,
            "a4_tolerates_being_alone": 1,
            "d5_tendency_to_bark_or_howl": 3
        }
    },
    {
        "name": "Family with 3 kids, wants medium friendly dog",
        "selects": {"size": "Medium", "age_group": "Adult"},
        "text_params": {
            "b2_incredibly_kid_friendly_dogs": 5,
            "e3_exercise_needs": 3,
            "d1_easy_to_train": 4,
            "b3_dog_friendly": 4
        }
    },
    {
        "name": "Novice owner, allergic, apartment",
        "selects": {"size": "Small", "age_group": "Adult"},
        "text_params": {
            "a2_good_for_novice_owners": 5,
            "c1_amount_of_shedding": 1,
            "a1_adapts_well_to_apartment_living": 5
        }
    },
    {
        "name": "Expert owner, wants guard dog, large yard",
        "selects": {"size": "Large", "age_group": "Adult"},
        "text_params": {
            "a2_good_for_novice_owners": 1,
            "e3_exercise_needs": 5,
            "d5_tendency_to_bark_or_howl": 5,
            "b2_incredibly_kid_friendly_dogs": 1
        }
    },
    {
        "name": "Quiet old lady, small apartment, no kids",
        "selects": {"size": "Small", "age_group": "Senior"},
        "text_params": {
            "e3_exercise_needs": 1,
            "a1_adapts_well_to_apartment_living": 5,
            "d5_tendency_to_bark_or_howl": 1,
            "a4_tolerates_being_alone": 5
        }
    },
    {
        "name": "Couples who hike on weekends, medium dog",
        "selects": {"size": "Medium", "age_group": "Adult"},
        "text_params": {
            "e3_exercise_needs": 4,
            "a1_adapts_well_to_apartment_living": 3,
            "a4_tolerates_being_alone": 3
        }
    },
    {
        "name": "Someone who wants a very affectionate velcro dog",
        "selects": {"size": "Small", "age_group": "Puppy"},
        "text_params": {
            "a4_tolerates_being_alone": 1,
            "b1_affectionate_with_family": 5,
            "d1_easy_to_train": 4
        }
    },
    {
        "name": "Works long hours, needs independent dog",
        "selects": {"size": "Medium", "age_group": "Adult"},
        "text_params": {
            "a4_tolerates_being_alone": 5,
            "e3_exercise_needs": 2,
            "d5_tendency_to_bark_or_howl": 2
        }
    },
    {
        "name": "Multi-dog household, wants friendly large dog",
        "selects": {"size": "Large", "age_group": "Adult"},
        "text_params": {
            "b3_dog_friendly": 5,
            "b2_incredibly_kid_friendly_dogs": 4,
            "e3_exercise_needs": 4
        }
    }
]

def run():
    print("Running Similarity Distribution Test...")
    print("==================================================")
    
    above_80 = 0
    between_50_80 = 0
    below_50 = 0
    
    for p in profiles:
        filtered_df = apply_hard_filters(df_final, p['selects'], p['text_params'])
        if len(filtered_df) == 0:
            print(f"Profile: {p['name']} -> NO DOGS MATCHED HARD FILTERS!")
            continue
            
        # Vectorized: score the whole filtered set at once (returns a numpy array of %).
        scores = calculate_weighted_cosine_similarity(p['text_params'], filtered_df)
        max_score = max(scores)
        
        print(f"Profile: {p['name']}")
        print(f"Highest Score in DB: {max_score:.2f}%")
        print("-" * 50)
        
        if max_score >= 80:
            above_80 += 1
        elif max_score >= 50:
            between_50_80 += 1
        else:
            below_50 += 1

    print("Distribution of Highest Scores Across 10 Profiles:")
    print(f"Above 80% (Great Match): {above_80}")
    print(f"Between 50% and 80% (Partial Match): {between_50_80}")
    print(f"Below 50% (Poor Match): {below_50}")

if __name__ == '__main__':
    run()
