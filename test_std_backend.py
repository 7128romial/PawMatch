import pytest
import pandas as pd
import ml_engine

# Ensure data is loaded before tests
ml_engine.load_data()

# TC_SERVER_01: Left join completeness
def test_tc_server_01_data_integrity():
    # Verify dataset has exactly 3000 rows
    assert ml_engine.df_final is not None, "Data should be loaded"
    assert len(ml_engine.df_final) == 3000, f"Expected 3000 rows, got {len(ml_engine.df_final)}"

# TC_SERVER_02: Neutral Fill for unanswered traits (no dynamic rescaling)
def test_tc_server_02_neutral_fill():
    # Send a user vector that omits Tier B traits (b2, b3, etc.).
    # The engine fills every missing trait with a neutral value of 3 and keeps
    # the full weight matrix (it does NOT drop/rescale the missing traits).
    text_params = {
        'a1_adapts_well_to_apartment_living': 5,
        'e3_exercise_needs': 3,
        'a4_tolerates_being_alone': 3,
        'd5_tendency_to_bark_or_howl': 3
    }
    df_one = ml_engine.df_final.iloc[[0]]  # single-row DataFrame
    scores = ml_engine.calculate_weighted_cosine_similarity(text_params, df_one)
    assert len(scores) == 1
    assert 0 <= scores[0] <= 100.0, "Score should be normalized between 0 and 100"

    # Explicitly confirm missing == neutral 3: a user who omits a trait must score
    # identically to a user who explicitly set that trait to 3.
    explicit = dict(text_params)
    for col in ml_engine.behavioral_cols:
        explicit.setdefault(col, 3)
    scores_explicit = ml_engine.calculate_weighted_cosine_similarity(explicit, df_one)
    assert abs(scores[0] - scores_explicit[0]) < 1e-6, "Missing traits must be treated as a neutral 3"

# TC_SERVER_03: Schema Mismatch
def test_tc_server_03_schema_mismatch():
    # Send string values for numeric parameters
    text_params = {
        'a1_adapts_well_to_apartment_living': "high", # Invalid string
        'e3_exercise_needs': 5
    }
    # It shouldn't crash; safe_int should catch the invalid string and fall back to the neutral default (3).
    df_one = ml_engine.df_final.iloc[[0]]
    scores = ml_engine.calculate_weighted_cosine_similarity(text_params, df_one)
    assert scores is not None and len(scores) == 1
    assert 0 <= scores[0] <= 100.0

# TC_SERVER_04: Filter Starvation
def test_tc_server_04_filter_starvation():
    # Impossible filters
    selects = {'size': 'Small'}
    text_params = {
        'size': 'Small',
        # Golden Retrievers are large, so requiring a Golden Retriever that is Small might be impossible 
        # or we can test an impossible color/size combo if we know it doesn't exist
        'color': 'Purple_Alien_Color' 
    }
    # Apply hard filters shouldn't crash
    filtered = ml_engine.apply_hard_filters(ml_engine.df_final, selects, text_params)
    
    # If filtered is empty, recommend_dogs should handle it gracefully
    result = ml_engine.recommend_dogs(selects, text_params, lang='he')
    assert "error" not in result or result["error"] != "Dataset not loaded."
    # The system should fallback to no direct match, or return something without crashing

# TC_EDGE_01: Breed Override
def test_tc_edge_01_breed_override():
    # User asks for Golden Retriever but has Small filter
    selects = {'size': 'Small'}
    text_params = {
        'breed_preference': 'Golden Retriever',
        'a1_adapts_well_to_apartment_living': 5
    }
    result = ml_engine.recommend_dogs(selects, text_params, lang='he')
    dogs = result.get("dogs", [])
    # Should return small dogs
    if dogs:
        assert str(dogs[0]["size"]).lower() == "small", "Fallback should respect the hard filter 'Small'"
        
# TC_EDGE_02: Basenji Outlier (Cluster 4)
def test_tc_edge_02_basenji_outlier():
    # Very specific behavior that fits Basenji (often independent, low bark)
    text_params = {
        'a1_adapts_well_to_apartment_living': 5,
        'a4_tolerates_being_alone': 5,
        'd5_tendency_to_bark_or_howl': 1,
        'e3_exercise_needs': 5
    }
    result = ml_engine.recommend_dogs({}, text_params, lang='he')
    dogs = result.get("dogs", [])
    # We don't guarantee Basenji is top 1, but we can verify it runs without error and returns matches
    assert len(dogs) > 0
    assert "cluster" in dogs[0]
