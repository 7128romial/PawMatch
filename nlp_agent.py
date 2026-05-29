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
סווג את מצב השיחה הנוכחי לאחד מ-4 מצבים, בהתחשב בהיסטוריית הנתונים ובקלט הנוכחי:
- state_a (לא רלוונטי): המשתמש מדבר על נושא שלא קשור לכלבים, אימוץ, או חיות מחמד (למשל פוליטיקה, מתכונים).
- state_b (חסר מידע מהותי): המשתמש סיפק פחות מ-2 תכונות קריטיות מתוך הארבע (כלומר 0 או 1).
- state_c (מידע חלקי-טוב): המשתמש סיפק 2 או 3 תכונות קריטיות מתוך הארבע, אך לא את כולן.
- state_d (מידע מלא): המשתמש סיפק את כל 4 התכונות הקריטיות (או לפחות 3 תכונות קריטיות בתוספת תכונות חשובות/נוספות).

# שלב 2: חילוץ נתונים
חלץ ערכים (1-5 או ערך מספרי לגיל/משקל) עבור התכונות הבאות מתוך הטקסט של המשתמש.
אם המשתמש לא התייחס לתכונה, אל תחזיר אותה.

תכונות קריטיות והנחיות מיפוי (בפרט עבור כפתורי בחירה מהירה):
1. a1_adapts_well_to_apartment_living (סביבת מגורים):
   - "דירה קטנה" / דירה ללא חצר -> 5
   - "דירה בינונית" / דירה עם מרפסת -> 4
   - "בית עם חצר" / חצר קטנה -> 2
   - חצר גדולה -> 1
2. a4_tolerates_being_alone (שעות לבד ביום):
   - "יום שלם" / הרבה שעות לבד / מעל 8 שעות -> 5
   - "חצי יום" / 4-6 שעות -> 3
   - "מעט מאוד" / עובד מהבית / לא לבד כמעט -> 1
3. b2_incredibly_kid_friendly_dogs (ידידותיות לילדים/חיות):
   - "כן, ילדים קטנים" / תינוקות -> 5
   - "ילדים גדולים" / ילדים מעל גיל 6 -> 4
   - "רק מבוגרים" / ללא ילדים -> 1
4. a2_good_for_novice_owners (רמת ניסיון של הבעלים):
   - "פעם ראשונה" / ללא ניסיון -> 5
   - "גידלתי בעבר" / בעל ניסיון -> 1

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
