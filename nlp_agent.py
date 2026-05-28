import os
from openai import OpenAI
import json

# Expecting OPENAI_API_KEY to be set in environment
client = OpenAI()

def analyze_user_input(user_text, current_params=None):
    if current_params is None:
        current_params = {}
        
    system_prompt = """
אתה מנתח שפה (NLP Layer) עבור פרויקט "PawMatch" - סוכן חכם להתאמת כלבים לאימוץ.
תפקידך לנתח את קלט הטקסט החופשי של המשתמש, לשלב אותו עם מידע קיים, ולהחזיר JSON עם הנתונים והמצב (State).

# שלב 1: זיהוי State
סווג את הטקסט לאחד מ-4 מצבים:
- state_a (לא רלוונטי): המשתמש מדבר על נושא שלא קשור לכלבים, אימוץ, או חיות מחמד (למשל פוליטיקה, מתכונים).
- state_b (חסר מידע מהותי): המשתמש מדבר על אימוץ אך סיפק מעט מאוד מידע קריטי (פחות מ-2 תכונות קריטיות).
- state_c (מידע חלקי-טוב): המשתמש סיפק לפחות 3 תכונות קריטיות ועוד קצת מידע, אבל לא הכל.
- state_d (מידע מלא): המשתמש סיפק כמעט את כל הפרטים הנדרשים להתאמה מדויקת.

# שלב 2: חילוץ נתונים
חלץ ערכים (1-5 או ערך מספרי לגיל/משקל) עבור התכונות הבאות מתוך הטקסט של המשתמש.
אם המשתמש לא התייחס לתכונה, אל תחזיר אותה.

תכונות קריטיות:
- a1_adapts_well_to_apartment_living (סביבת מגורים: 1=חצר גדולה, 5=דירה קטנה ללא חצר)
- a4_tolerates_being_alone (שעות לבד: 1=מעט מאוד לבד, 5=הרבה שעות לבד)
- b2_incredibly_kid_friendly_dogs (ילדים/חיות: 1=אין ילדים/מעדיף כלב יחיד, 5=יש ילדים קטנים/עוד חיות)
- a2_good_for_novice_owners (רמת ניסיון: 1=מנוסה מאוד, 5=חסר ניסיון לחלוטין)

תכונות חשובות:
- e1_energy_level (רמת אנרגיה רצויה)
- d1_easy_to_train (עד כמה קל לאילוף/מטרת הכלב)

תכונות נוספות:
- b1_affectionate_with_family
- b3_dog_friendly
- c1_amount_of_shedding (נשירה / אלרגיה. 1=לא נושר כלל/היפואלרגני, 5=נושר מאוד)
- c2_drooling_potential
- d5_tendency_to_bark_or_howl
- e3_exercise_needs

פורמט הפלט (JSON בלבד):
{
  "state": "state_b",
  "extracted_parameters": {
    "a1_adapts_well_to_apartment_living": 5
  }
}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"היסטוריית נתונים עד כה (JSON): {json.dumps(current_params)}\n\nקלט המשתמש הנוכחי: '{user_text}'"}
            ],
            response_format={ "type": "json_object" },
            temperature=0.0
        )
        
        result = json.loads(response.choices[0].message.content)
        return result
    except Exception as e:
        print(f"OpenAI API Error: {e}")
        return {
            "state": "error",
            "extracted_parameters": {},
            "error": str(e)
        }
