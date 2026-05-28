import pandas as pd
import numpy as np
import re
import os

def parse_life_span(span_str):
    if pd.isna(span_str):
        return 10.0, 13.0
    span_str = str(span_str).lower()
    # Find all numbers
    numbers = [float(x) for x in re.findall(r'\d+', span_str)]
    if len(numbers) >= 2:
        return numbers[0], numbers[1]
    elif len(numbers) == 1:
        return numbers[0], numbers[0]
    return 10.0, 13.0 # Fallback default

def preprocess():
    print("Starting preprocessing of real datasets...")
    
    # Load raw datasets
    breeds_path = "data/breeds 1.csv"
    dogs_path = "data/dogs_dataset 1.csv"
    
    if not os.path.exists(breeds_path) or not os.path.exists(dogs_path):
        print("Error: Make sure 'breeds 1.csv' and 'dogs_dataset 1.csv' are in the 'data' directory.")
        return
        
    breeds_df = pd.read_csv(breeds_path)
    dogs_df = pd.read_csv(dogs_path)
    
    # Standardize breed names for joining
    dogs_df['join_breed'] = dogs_df['Breed'].str.lower().str.strip()
    breeds_df['join_breed'] = breeds_df['breed'].str.lower().str.strip()
    
    # Align common mismatching names
    mismatches = {
        "german shepherd": "german shepherd dog",
        "shetland sheepdog": "shetland sheepdog",
        "miniature schnauzer": "miniature schnauzer"
    }
    dogs_df['join_breed'] = dogs_df['join_breed'].replace(mismatches)
    
    # Drop the redundant 'breed' column from breeds_df to prevent duplicate column labels
    breeds_df_for_join = breeds_df.drop(columns=['breed'])
    # Left join to preserve all dogs from the original dataset
    merged_df = pd.merge(dogs_df, breeds_df_for_join, on='join_breed', how='left')
    
    print(f"Total rows after merge: {len(merged_df)}")
    
    # Remove dogs lacking core behavioral data
    # We will check if 'a1_adapts_well_to_apartment_living' is missing
    merged_df = merged_df.dropna(subset=['a1_adapts_well_to_apartment_living'])
    print(f"Total rows after dropping missing behavioral traits: {len(merged_df)}")
    
    # Drop duplicates
    merged_df = merged_df.drop_duplicates()
    merged_df = merged_df.reset_index(drop=True)
    print(f"Total rows after dropping duplicates: {len(merged_df)}")
    
    # Parse life span min/max
    lifespans = merged_df['life_span'].apply(parse_life_span)
    merged_df['life_span_min'] = [x[0] for x in lifespans]
    merged_df['life_span_max'] = [x[1] for x in lifespans]
    
    # Size mapping based on Weight (kg)
    # Small (<=15 kg), Medium (15-30 kg), Large (>30 kg)
    def get_size(weight):
        if weight <= 15:
            return 'Small'
        elif weight <= 30:
            return 'Medium'
        return 'Large'
        
    merged_df['size'] = merged_df['Weight (kg)'].apply(get_size)
    
    # Standardize column names to match system expectations
    rename_cols = {
        'Breed': 'breed',
        'Age (Years)': 'age_years',
        'Weight (kg)': 'weight_kg',
        'Gender': 'sex',
        'Color': 'color'
    }
    merged_df = merged_df.rename(columns=rename_cols)
    
    # Map hair_length based on standard breeds
    long_haired_breeds = [
        'golden retriever', 'german shepherd dog', 'siberian husky', 'poodle', 
        'yorkshire terrier', 'shetland sheepdog', 'havanese', 'maltese', 
        'shih tzu', 'lhasa apso', 'cavalier king charles spaniel', 'alaskan malamute', 
        'bernese mountain dog', 'samoyed', 'border collie', 'pomeranian', 
        'papillon', 'pekingese', 'cocker spaniel', 'irish setter'
    ]
    
    def get_hair_length(breed_name):
        b = str(breed_name).lower().strip()
        for l_breed in long_haired_breeds:
            if l_breed in b:
                return 'Long'
        return 'Short'
        
    merged_df['hair_length'] = merged_df['breed'].apply(get_hair_length)
    
    # Generate unique sequential dog names
    merged_df['name'] = [f"Dog_{i}" for i in range(len(merged_df))]
    
    # Fill remaining NaNs for numerical fields with median/mode to keep model safe
    fill_cols = [
        'a1_adapts_well_to_apartment_living', 'a2_good_for_novice_owners', 
        'a4_tolerates_being_alone', 'b1_affectionate_with_family', 
        'b2_incredibly_kid_friendly_dogs', 'b3_dog_friendly', 
        'c1_amount_of_shedding', 'c2_drooling_potential', 
        'd1_easy_to_train', 'd5_tendency_to_bark_or_howl', 
        'e1_energy_level', 'e3_exercise_needs'
    ]
    for col in fill_cols:
        merged_df[col] = pd.to_numeric(merged_df[col], errors='coerce')
        merged_df[col] = merged_df[col].fillna(merged_df[col].median() if not merged_df[col].isna().all() else 3.0).astype(int)
        
    # Save the processed datasets
    output_dogs_path = "data/dogs_final.csv"
    output_breeds_path = "data/breeds.csv"
    
    merged_df.to_csv(output_dogs_path, index=False)
    
    # Also clean and save breeds.csv
    breeds_df['life_span_parsed'] = breeds_df['life_span'].apply(parse_life_span)
    breeds_df['life_span_min'] = [x[0] for x in breeds_df['life_span_parsed']]
    breeds_df['life_span_max'] = [x[1] for x in breeds_df['life_span_parsed']]
    breeds_df.drop(columns=['life_span_parsed']).to_csv(output_breeds_path, index=False)
    
    print(f"Successfully created clean production files:")
    print(f" -> {output_dogs_path} ({len(merged_df)} rows)")
    print(f" -> {output_breeds_path} ({len(breeds_df)} rows)")

if __name__ == "__main__":
    preprocess()
