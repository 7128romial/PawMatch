import os
from openai import OpenAI
import json

# Expecting OPENAI_API_KEY to be set in environment
api_key = os.getenv("OPENAI_API_KEY")
if api_key and api_key != "your_api_key_here":
    client = OpenAI(api_key=api_key)
else:
    client = None

def analyze_user_input(user_text, current_params=None, active_param=None):
    if current_params is None:
        current_params = {}
        
    system_prompt = """
אתה מנתח שפה (NLP Layer) עבור פרויקט "PawMatch" - סוכן חכם להתאמת כלבים לאימוץ.
תפקידך לנתח את קלט הטקסט החופשי של המשתמש, לשלב אותו עם מידע קיים, ולהחזיר JSON עם הנתונים והמצב (State).

# שלב 1: זיהוי State
סווג את מצב השיחה הנוכחי לאחד מ-5 מצבים, בהתחשב בהיסטוריית הנתונים ובקלט הנוכחי:
- state_e (מניע לא אתי / לא אחראי): המשתמש מביע מניע שאינו אחראי או אינו אתי לאימוץ כלב (למשל: אימוץ מתוך שעמום בלבד, רצון בצעצוע זמני, יחס לכלב כאל חפץ קישוטי בלבד, גחמה חולפת, או חוסר מוכנות מובהק לטיפול בנפש חיה).
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
   - "כלב ראשון" / "פעם ראשונה" / "First Time" / "first dog" / ללא ניסיון / "no experience" -> 5
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

# שלב 3: הנחיות קריטיות לשלילות והשלכות לוגיות (Negations and Implications)
אנא שים לב לביטויי שלילה ומשמעויות נגררות של דברי המשתמש:
1. ילדים וחיות מחמד (b2_incredibly_kid_friendly_dogs):
   - אם המשתמש מציין שאין ילדים או חיות מחמד בבית, או שאין לו ילדים (למשל: "אין ילדים", "אין לי ילדים", "בלי ילדים", "ללא ילדים", "אין חיות", "אין", "לא", "לא אין", "אין לי", "no kids", "no"): מפה ל-`b2_incredibly_kid_friendly_dogs: 1` (Adults Only).
   - אם המשתמש מציין שיש ילדים בבית (למשל: "יש ילדים", "יש לי ילדים", "כן", "יש", "יש לי", "kids"): מפה ל-`b2_incredibly_kid_friendly_dogs: 5`.
2. רמת ניסיון (a2_good_for_novice_owners):
   - אם המשתמש מציין שאין לו ניסיון, או שלא גידל כלב בעבר, או שזהו כלבו הראשון (למשל: "כלב ראשון", "פעם ראשונה", "אין לי ניסיון", "לא היו לי כלבים", "לא גידלתי כלב", "אין", "לא", "אין לי", "no experience", "first dog"): מפה ל-`a2_good_for_novice_owners: 5` (כלומר, מתאים לבעלים מתחילים).
   - אם המשתמש מציין שיש לו ניסיון או שגידל בעבר (למשל: "גידלתי בעבר", "היו לי כלבים", "בעל ניסיון", "יש ניסיון", "יש", "יש לי", "כן", "raised before", "have experience"): מפה ל-`a2_good_for_novice_owners: 1`.
3. שעות לבד בבית (a4_tolerates_being_alone):
   - אם המשתמש מציין שהכלב לא יישאר לבד בכלל או כמעט בכלל (למשל: "לא יישאר לבד", "אף פעם לא לבד", "עובד מהבית", "לא הרבה", "לא", "אף פעם", "always home"): מפה ל-`a4_tolerates_being_alone: 1`.
   - "לא ארבע שעות" / "לא הרבה שעות" -> מפה ל-`a4_tolerates_being_alone: 1`.
4. סביבת מגורים (a1_adapts_well_to_apartment_living):
   - "לא דירה" / "לא בית קטן" -> מפה ל-`a1_adapts_well_to_apartment_living: 1` (חצר גדולה).
5. אורך פרווה ונשירה (Implications):
    - "לא פרווה ארוכה" / "בלי פרווה ארוכה" / "no long hair" -> מפה אורך פרווה קצר `hair_length: "Short"`. בנוסף, השלם מכך שהמשתמש רוצה כלב שאינו משיר שיער, ולכן מפה גם רמת נשירה נמוכה `c1_amount_of_shedding: 1` או `2`.
    - "ללא נשירה" / "אלרגי לשיער" / "hypoallergenic" -> מפה רמת נשירה נמוכה `c1_amount_of_shedding: 1` וכן אורך פרווה קצר `hair_length: "Short"`.
6. רגישות לרעש ונביחות (d5_tendency_to_bark_or_howl):
   - "כלב שקט", "רגיש לרעש", "בלי נביחות", "לא רוצה שינבח", "שלא ינבח", "שקט", "quiet dog", "noise sensitive" -> מפה ל-`d5_tendency_to_bark_or_howl: 1`.
   - "כלב שמירה", "שינבח כשמישהו בא", "שמירה", "guard dog" -> מפה ל-`d5_tendency_to_bark_or_howl: 5`.
7. רמת אנרגיה וצרכי ספורט (e1_energy_level, e3_exercise_needs):
   - "אני רץ", "אוהב לרוץ", "פעיל מאוד", "ספורטיבי", "טיולים ארוכים בשטח", "active", "runner" -> מפה `e1_energy_level: 5` ו-`e3_exercise_needs: 5`.
   - "בטטת כורסה", "כלב עצלן", "טיולים קצרים", "lazy", "couch potato" -> מפה `e1_energy_level: 1` ו-`e3_exercise_needs: 1`.
8. חברות לכלבים אחרים בבית (b3_dog_friendly):
   - "יש לי כלב", "גר עם עוד כלבים", "חברותי לכלבים אחרים", "other dogs" -> מפה ל-`b3_dog_friendly: 5`.
9. רגישות לריור (c2_drooling_potential):
   - "שלא ירייר", "בלי ריר", "נקי", "no drool" -> מפה ל-`c2_drooling_potential: 1`.
10. רצון בכלב "דבק" ומפנק (b1_affectionate_with_family):
    - "כלב מחבק", "כלב דבק", "כלב מפנק", "להתכרבל", "cuddly dog" -> מפה ל-`b1_affectionate_with_family: 5`.

# שלב 4: התמודדות עם תשובות קצרות וחלקיות (כן/לא/יש/אין) על בסיס הפרמטר הפעיל
המשתמש נשאל כעת שאלה לגבי הפרמטר הפעיל הבא (active_param): {active_param}
אם קלט המשתמש הנוכחי הוא קצר או ישיר (למשל: "כן", "לא", "יש", "אין", "אין לי", "לא אין") והוא עונה על השאלה לגבי {active_param}, אנא השתמש בחוקי שלב 3 ובמשמעות של {active_param} כדי לקבוע את הערך הנכון.

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
        if client is None:
            raise Exception("OpenAI API key is missing or placeholder.")
        system_prompt_final = system_prompt.replace("{active_param}", str(active_param or "None"))
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt_final},
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

def generate_explanations(dogs, user_params, lang='he'):
    dogs_info = []
    for d in dogs:
        dogs_info.append({
            "name": d.get("name"),
            "breed": d.get("breed"),
            "match_score": d.get("match_score"),
            "sex": d.get("sex"),
            "size": d.get("size"),
            "color": d.get("color"),
            "hair_length": d.get("hair_length"),
            "a1_adapts_well_to_apartment_living": d.get("a1_adapts_well_to_apartment_living"),
            "a4_tolerates_being_alone": d.get("a4_tolerates_being_alone"),
            "b2_incredibly_kid_friendly_dogs": d.get("b2_incredibly_kid_friendly_dogs"),
            "a2_good_for_novice_owners": d.get("a2_good_for_novice_owners")
        })
        
    system_prompt = f"""
You are a warm, professional dog adoption coordinator for PawMatch.
Write personalized explanations and breed descriptions for 3 recommended dogs.
Generate your response in JSON format. The response language must be strictly: {"Hebrew (עברית)" if lang == 'he' else "English"}.

Output JSON structure:
{{
  "explanations": [
    {{
      "name": "Dog_Name",
      "match_reason": "A 1-2 sentence explanation of why this specific dog is a match for the user's parameters. Reference the user's environment/needs (e.g. apartment, hours alone, kids, etc.).",
      "breed_info": "A 1-2 sentence description of the breed's general temperament, origins, and key characteristics."
    }}
  ]
}}
"""

    user_prompt = f"""
User parameters: {json.dumps(user_params)}
Recommended dogs data: {json.dumps(dogs_info)}
"""

    try:
        if client is None:
            raise Exception("OpenAI API key is missing or placeholder.")
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={ "type": "json_object" },
            temperature=0.7
        )
        result = json.loads(response.choices[0].message.content)
        return result.get("explanations", [])
    except Exception as e:
        print(f"OpenAI API Error in generate_explanations: {e}")
        return []

def answer_breed_question(user_question, recommended_breeds=None, lang='he'):
    if recommended_breeds is None:
        recommended_breeds = []
        
    breeds_str = ", ".join(recommended_breeds) if recommended_breeds else "none currently recommended"
    
    system_prompt = f"""
    You are a friendly, professional canine breed and care expert for PawMatch.
    Your goal is to answer user questions about dog breeds, behavior, care, training, or suitability.
    The user was recently recommended the following breeds: {breeds_str}.
    
    Guidelines:
    1. Answer the question in a warm, helpful, and expert tone.
    2. Keep your response relatively concise (2-4 sentences).
    3. If the question is completely unrelated to dogs, breeds, or pets, politely guide the user back to dog-related questions, or tell them they can click "Start Over" to begin a new match search.
    4. You must respond strictly in: {"Hebrew (עברית)" if lang == 'he' else "English"}.
    """
    
    try:
        if client is None:
            raise Exception("OpenAI API key is missing or placeholder.")
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_question}
            ],
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"OpenAI API Error in answer_breed_question: {e}")
        return "I'm sorry, I encountered an error while answering your question." if lang == 'en' else "מצטער, נתקלתי בשגיאה בעת מענה על השאלה שלך."
