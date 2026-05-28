import pandas as pd
import numpy as np
import random
import os

# Define breeds and their base traits
breeds_data = {
    'breed': ['Golden Retriever', 'Labrador Retriever', 'French Bulldog', 'Pug', 'Rottweiler', 
              'Yorkshire Terrier', 'German Shepherd Dog', 'Siberian Husky', 'Poodle', 'Mixed Breed'],
    'a1_adapts_well_to_apartment_living': [3, 2, 5, 5, 2, 5, 2, 1, 4, 3],
    'a2_good_for_novice_owners': [5, 5, 4, 4, 2, 3, 2, 1, 4, 4],
    'a4_tolerates_being_alone': [2, 2, 2, 1, 4, 2, 3, 2, 2, 3],
    'b1_affectionate_with_family': [5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
    'b2_incredibly_kid_friendly_dogs': [5, 5, 4, 4, 3, 2, 4, 4, 4, 4],
    'b3_dog_friendly': [5, 5, 4, 3, 3, 3, 3, 5, 4, 4],
    'c1_amount_of_shedding': [4, 4, 3, 4, 3, 1, 5, 5, 1, 3],
    'c2_drooling_potential': [3, 3, 3, 2, 4, 1, 2, 1, 1, 2],
    'd1_easy_to_train': [5, 5, 3, 2, 4, 3, 5, 2, 5, 4],
    'd5_tendency_to_bark_or_howl': [3, 3, 2, 3, 4, 4, 4, 5, 4, 3],
    'e1_energy_level': [4, 5, 2, 2, 4, 4, 5, 5, 4, 3],
    'e3_exercise_needs': [4, 5, 2, 2, 4, 3, 5, 5, 4, 3],
    'life_span_min': [10, 10, 10, 13, 9, 11, 7, 12, 10, 10],
    'life_span_max': [12, 12, 12, 15, 10, 15, 10, 14, 18, 15],
    'hair_length': ['Long', 'Short', 'Short', 'Short', 'Short', 'Long', 'Long', 'Long', 'Long', 'Short']
}

breeds_df = pd.DataFrame(breeds_data)

# Generate 300 mock dogs
num_dogs = 300
np.random.seed(42)

# Pick random breeds, except Labrador which we will intentionally set to 0 stock for testing
available_breeds = [b for b in breeds_data['breed'] if b != 'Labrador Retriever']

dogs = []
for i in range(num_dogs):
    breed = random.choice(available_breeds)
    breed_idx = breeds_df[breeds_df['breed'] == breed].index[0]
    
    # Base weight by breed approximate
    if breed in ['Golden Retriever', 'German Shepherd Dog', 'Rottweiler']:
        weight = np.random.normal(30, 5)
    elif breed in ['Siberian Husky', 'Mixed Breed']:
        weight = np.random.normal(22, 4)
    elif breed in ['French Bulldog', 'Pug', 'Poodle']:
        weight = np.random.normal(10, 2)
    else: # Yorkie
        weight = np.random.normal(3, 1)
        
    weight = max(2.0, weight) # prevent negative weight
    
    if weight <= 15:
        size = 'Small'
    elif weight <= 30:
        size = 'Medium'
    else:
        size = 'Large'
        
    age = max(1.0, np.random.normal(5, 3))
    
    dog = {
        'name': f'Dog_{i}',
        'breed': breed,
        'age_years': round(age, 1),
        'weight_kg': round(weight, 1),
        'size': size,
        'color': random.choice(['Black', 'White', 'Brown', 'Mixed', 'Golden']),
        'sex': random.choice(['Male', 'Female']),
        'hair_length': breeds_df.iloc[breed_idx]['hair_length']
    }
    
    # Add traits with some small random variance around breed mean
    for col in breeds_df.columns:
        if col not in ['breed', 'hair_length']:
            val = breeds_df.iloc[breed_idx][col]
            if 'life_span' not in col:
                val = max(1, min(5, val + np.random.randint(-1, 2)))
            dog[col] = val
        
    dogs.append(dog)

dogs_df = pd.DataFrame(dogs)

# Save to CSV
os.makedirs('data', exist_ok=True)
dogs_df.to_csv('data/dogs_final.csv', index=False)
breeds_df.to_csv('data/breeds.csv', index=False)

print("Mock data generated successfully in data/ directory!")
