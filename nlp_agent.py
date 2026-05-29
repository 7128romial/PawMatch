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
חלץ ערכים עבור התכונות הבאות מתוך הטקסט של המשתמש. שים לב: קלט המשתמש עשוי להיות בעברית או באנגלית, ויכול להיות מורכב משילוב של הודעות חופשיות או לחיצות על כפתורים בשתי השפות.
אם המשתמש לא התייחס לתכונה, אל תחזיר אותה.

תכונות קריטיות והנחיות מיפוי (בפרט עבור כפתורי בחירה מהירה בעברית או באנגלית):
1. a1_adapts_well_to_apartment_living (סביבת מגורים):
   - "דירה קטנה" / "Small Apartment" / דירה ללא חצר / "apartment" -> 5
   - "דירה בינונית" / "Medium Apartment" / דירה עם מרפסת -> 4
   - "בית עם חצר" / "House with Yard" / חצר קטנה / "house" -> 2
   - חצר גדולה / "big yard" -> 1
2. a4_tolerates_being_alone (שעות לבד ביום):
   - "יום שלם" / "Full Day" / הרבה שעות לבד / מעל 8 שעות -> 5
   - "חצי יום" / "Half Day" / 4-6 שעות -> 3
   - "מעט מאוד" / "Very Few" / עובד מהבית / לא לבד כמעט / "work from home" -> 1
3. b2_incredibly_kid_friendly_dogs (ידידותיות לילדים/חיות):
   - "כן, ילדים קטנים" / "Yes, Young Kids" / תינוקות / "kids" -> 5
   - "ילדים גדולים" / "Older Kids" / ילדים מעל גיל 6 -> 4
   - "רק מבוגרים" / "Adults Only" / ללא ילדים -> 1
4. a2_good_for_novice_owners (רמת ניסיון של הבעלים):
   - "פעם ראשונה" / "First Time" / ללא ניסיון / "no experience" -> 5
   - "גידלתי בעבר" / "Raised Before" / בעל ניסיון / "have experience" -> 1

מאפיינים פיזיים (קריטי להחזיר בדיוק את ערכי ה-string הבאים באנגלית):
5. sex (מין):
   - "זכר" / "Male" -> "Male"
   - "נקבה" / "Female" -> "Female"
6. size (גודל):
   - "קטן" / "Small" -> "Small"
   - "בינוני" / "Medium" -> "Medium"
   - "גדול" / "Large" -> "Large"
7. hair_length (אורך פרווה):
   - "קצרה" / "קצר" / "Short" -> "Short"
   - "ארוכה" / "ארוך" / "Long" -> "Long"
8. color (צבע פרווה):
   - "שחור" / "Black" -> "Black"
   - "לבן" / "White" -> "White"
   - "חום" / "Brown" / "Tan" -> "Tan"
   - "אפור" / "Gray" -> "Gray"
   - "מעורב" / "Mixed" / "Bicolor" -> "Bicolor"

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
    "a1_adapts_well_to_apartment_living": 5,
    "sex": "Male"
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
