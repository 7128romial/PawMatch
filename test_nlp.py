import json
from dotenv import load_dotenv
load_dotenv()

from nlp_agent import analyze_user_input

scenarios = [
    {
        "name": "Time alone - short answer",
        "user_text": "2 hours",
        "active_param": "a4_tolerates_being_alone",
        "current_params": {}
    },
    {
        "name": "Exercise - short answer",
        "user_text": "2 hours",
        "active_param": "e3_exercise_needs",
        "current_params": {"a4_tolerates_being_alone": 2}
    },
    {
        "name": "Barking - short answer",
        "user_text": "I really care about noise",
        "active_param": "d5_tendency_to_bark_or_howl",
        "current_params": {}
    },
    {
        "name": "Time alone - word answer",
        "user_text": "nine hours",
        "active_param": "a4_tolerates_being_alone",
        "current_params": {}
    }
]

for idx, s in enumerate(scenarios):
    print(f"--- Test {idx+1}: {s['name']} ---")
    print(f"Active Param: {s['active_param']}")
    print(f"User Input: '{s['user_text']}'")
    
    result = analyze_user_input(
        user_text=s['user_text'],
        current_params=s['current_params'],
        active_param=s['active_param'],
        lang='he'
    )
    
    print(f"Extracted Params: {result.get('extracted_parameters')}")
    print(f"Next Question: {result.get('next_question')}")
    print("\n")
