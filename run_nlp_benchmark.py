import json
import os
from dotenv import load_dotenv

# Load environment variables FIRST
load_dotenv()

from nlp_agent import analyze_user_input

test_cases = [
    {
        "text": "אני עובדת מהבית 9 שעות ביום",
        "active_param": "a4_tolerates_being_alone",
        "expected_range": [1, 2] # Doesn't need to tolerate being alone
    },
    {
        "text": "אני יוצא לרוץ שעתיים כל ערב ומחפש שותף לריצה",
        "active_param": "e3_exercise_needs",
        "expected_range": [4, 5]
    },
    {
        "text": "הדירה שלי ממש קטנה בלי חצר",
        "active_param": "a1_adapts_well_to_apartment_living",
        "expected_range": [4, 5] # Needs to adapt well
    },
    {
        "text": "אין לי שום ניסיון עם כלבים, זו פעם ראשונה שאני מאמץ",
        "active_param": "a2_good_for_novice_owners",
        "expected_range": [4, 5] # Needs to be good for beginners
    },
    {
        "text": "יש לי 3 ילדים קטנים שרצים בבית ועושים רעש",
        "active_param": "b2_incredibly_kid_friendly_dogs",
        "expected_range": [4, 5]
    },
    {
        "text": "אין לי כוח לשערות על הספה, אני קצת חולה ניקיון",
        "active_param": "c1_amount_of_shedding",
        "expected_range": [1, 2] # 1: hypoallergenic/no shedding
    },
    {
        "text": "השכנים שלי ממש רגישים לרעש, אז שיהיה כלב שקט",
        "active_param": "d5_tendency_to_bark_or_howl",
        "expected_range": [1, 2] # 1: low barking
    },
    {
        "text": "יש לי כבר שני כלבים בבית שרוצים חבר",
        "active_param": "b3_dog_friendly",
        "expected_range": [4, 5]
    },
    {
        "text": "אין לי סבלנות לאלף, אני רוצה כלב שמקשיב מהר",
        "active_param": "d1_easy_to_train",
        "expected_range": [4, 5] # 5: eager to please
    },
    {
        "text": "אני עובד 10 שעות במשרד ולא חוזר הביתה באמצע",
        "active_param": "a4_tolerates_being_alone",
        "expected_range": [4, 5] # 5: fine being left alone
    }
]

def run_benchmark():
    correct = 0
    total = len(test_cases)
    print("Starting NLP Extraction Benchmark...")
    print("-" * 40)
    
    for i, tc in enumerate(test_cases):
        print(f"Test {i+1}: {tc['text']}")
        try:
            result = analyze_user_input(
                user_text=tc['text'],
                current_params={},
                active_param=tc['active_param'],
                lang='he'
            )
            extracted = result.get('extracted_parameters', {})
            val = extracted.get(tc['active_param'])
            
            if val is not None and int(val) in tc['expected_range']:
                print(f"[PASS] Extracted: {val} (Expected: {tc['expected_range']})\n")
                correct += 1
            else:
                print(f"[FAIL] Extracted: {val} (Expected: {tc['expected_range']})\n")
        except Exception as e:
            print(f"[ERROR] running test: {e}\n")

    accuracy = (correct / total) * 100
    print("-" * 40)
    print(f"Total Accuracy: {accuracy}% ({correct}/{total})")

if __name__ == "__main__":
    run_benchmark()
