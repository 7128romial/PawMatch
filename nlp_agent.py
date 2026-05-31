import os
from openai import OpenAI
import json

# Expecting OPENAI_API_KEY to be set in environment
api_key = os.getenv("OPENAI_API_KEY")
if api_key and api_key != "your_api_key_here":
    client = OpenAI(api_key=api_key)
else:
    client = None

def analyze_user_input(user_text, current_params=None, active_param=None, lang='he'):
    if current_params is None:
        current_params = {}
        
    system_prompt_he = """
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
9. breed_preference (גזע מועדף ספציפי באנגלית):
   - "גולדן" / "גולדן רטריבר" / "Golden" / "Golden Retriever" -> "Golden Retriever"
   - "לברדור" / "לברדור רטריבר" / "Labrador" / "Labrador Retriever" -> "Labrador Retriever"
   - "בולדוג צרפתי" / "French Bulldog" -> "French Bulldog"
   - "פאג" / "Pug" -> "Pug"
   - "רוטוויילר" / "Rottweiler" -> "Rottweiler"
   - "יורקי" / "יורקשייר" / "Yorkshire Terrier" -> "Yorkshire Terrier"
   - "רועה גרמני" / "German Shepherd" / "German Shepherd Dog" -> "German Shepherd Dog"
   - "האסקי" / "האסקי סיבירי" / "Siberian Husky" -> "Siberian Husky"
   - "פודל" / "Poodle" -> "Poodle"
   - "מעורב" / "Mixed Breed" -> "Mixed Breed"
   - אם המשתמש רוצה גזע ספציפי אחר, מפה אותו לשמו הרשמי באנגלית. אם לא ביקש גזע ספציפי, אל תחזיר ערך זה.

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
11. מענה על שאלות רעש/נביחות (d5_tendency_to_bark_or_howl) ונשירה/אלרגיה (c1_amount_of_shedding):
     - אם המשתמש אומר "לא לשתי השאלות", "רעש לא ונשירה לא", "לא מפריע לי רעש ולא נשירה" (או שלילה אחרת לשניהם) -> מפה `d5_tendency_to_bark_or_howl: 1` ו-`c1_amount_of_shedding: 5` (המשמעות היא שרעש מפריע ברמה מינימלית, ונשירה מותרת ברמה מקסימלית כי היא אינה מהווה שיקול/בעיה).
     - אם המשתמש אומר "לא" או "לא מפריע" או "לא מפריע לי" או "לא יפריע" לגבי רעש/נביחות -> מפה `d5_tendency_to_bark_or_howl: 1`.
     - אם המשתמש אומר "לא" או "לא מפריע" או "אין אלרגיות" או "לא מהווה שיקול" או "לא מפריע לי נשירה" לגבי נשירה/אלרגיות -> מפה `c1_amount_of_shedding: 5`.
     - אם המשתמש אומר "כן", "יש אלרגיות", "נשירה מפריעה", "עדיף שלא ישיר פרווה", "בלי שיער" לגבי נשירה/אלרגיות -> מפה `c1_amount_of_shedding: 1`.

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

    system_prompt_en = """
You are a language analyzer (NLP Layer) for the "PawMatch" project - a smart agent for matching dogs for adoption.
Your job is to analyze the user's free-text input, combine it with existing data, and return a JSON containing the extracted parameters and the conversation state.

# STEP 1: Identify State
Classify the current conversation state into one of 5 states, taking into account the data history and the current input:
- state_e (unethical / irresponsible motive): The user expresses an irresponsible or unethical motive for adopting a dog (e.g., adopting purely out of boredom, wanting a temporary toy, treating the dog as a decorative object, a passing whim, or a clear lack of readiness to care for a living soul).
- state_a (irrelevant): The user is talking about a topic unrelated to dogs, adoption, or pets (e.g., politics, cooking recipes).
- state_b (lacking essential information): The user has provided fewer than 2 critical features out of the four (i.e., 0 or 1).
- state_c (partial information - good): The user has provided 2 or 3 critical features out of the four, but not all of them.
- state_d (full information): The user has provided all 4 critical features (or at least 3 critical features plus important/additional features).

# STEP 2: Extract Data
Extract values for the following features from the user's text. Note: The user's input may be in Hebrew or English, and could be a combination of free-text messages or button clicks in either language.
If the user did not refer to a feature, do not return it.

Critical features and mapping guidelines (specifically for quick-choice buttons in Hebrew or English):
1. a1_adapts_well_to_apartment_living (living environment):
   - "Small Apartment" / "דירה קטנה" / apartment without a yard / "apartment" -> 5
   - "Medium Apartment" / "דירה בינונית" / apartment with a balcony -> 4
   - "House with Yard" / "בית עם חצר" / small yard / "house" -> 2
   - large yard / "big yard" -> 1
2. a4_tolerates_being_alone (hours alone per day):
   - "Full Day" / "יום שלם" / many hours alone / over 8 hours -> 5
   - "Half Day" / "חצי יום" / 4-6 hours -> 3
   - "Very Few" / "מעט מאוד" / work from home / barely alone / "work from home" -> 1
3. b2_incredibly_kid_friendly_dogs (friendliness to children/pets):
   - "Yes, Young Kids" / "כן, ילדים קטנים" / babies / "kids" -> 5
   - "Older Kids" / "ילדים גדולים" / kids over 6 years old -> 4
   - "Adults Only" / "רק מבוגרים" / no kids -> 1
4. a2_good_for_novice_owners (owner's experience level):
   - "First Time" / "First Dog" / "כלב ראשון" / "פעם ראשונה" / no experience / "no experience" -> 5
   - "Raised Before" / "גידלתי בעבר" / experienced / "have experience" -> 1

Physical attributes (it is critical to return exactly the following string values in English):
5. sex (gender):
   - "Male" / "זכר" -> "Male"
   - "Female" / "נקבה" -> "Female"
6. size (size):
   - "Small" / "קטן" -> "Small"
   - "Medium" / "בינוני" -> "Medium"
   - "Large" / "גדול" -> "Large"
7. hair_length (coat length):
   - "Short" / "קצרה" / "קצר" -> "Short"
   - "Long" / "ארוכה" / "ארוך" -> "Long"
8. color (coat color):
   - "Black" / "שחור" -> "Black"
   - "White" / "לבן" -> "White"
   - "Brown" / "Tan" / "חום" -> "Tan"
   - "Gray" / "אפור" -> "Gray"
   - "Mixed" / "Bicolor" / "מעורב" -> "Bicolor"
9. breed_preference (specific preferred breed in English):
   - "Golden" / "Golden Retriever" / "גולדן" / "גולדן רטריבר" -> "Golden Retriever"
   - "Labrador" / "Labrador Retriever" / "לברדור" / "לברדור רטריבר" -> "Labrador Retriever"
   - "French Bulldog" / "בולדוג צרפתי" -> "French Bulldog"
   - "Pug" / "פאג" -> "Pug"
   - "Rottweiler" / "רוטוויילר" -> "Rottweiler"
   - "Yorkshire Terrier" / "יורקי" / "יורקשייר" -> "Yorkshire Terrier"
   - "German Shepherd" / "German Shepherd Dog" / "רועה גרמני" -> "German Shepherd Dog"
   - "Siberian Husky" / "האסקי" / "האסקי סיבירי" -> "Siberian Husky"
   - "Poodle" / "פודל" -> "Poodle"
   - "Mixed Breed" / "מעורב" -> "Mixed Breed"
   - If the user wants another specific breed, map it to its official English name. If they did not ask for a specific breed, do not return this value.

Important features:
- e1_energy_level (desired energy level)
- d1_easy_to_train (how easy to train / purpose of the dog)

Additional features:
- b1_affectionate_with_family
- b3_dog_friendly
- c1_amount_of_shedding (shedding / allergy. 1=no shedding/hypoallergenic, 5=sheds a lot)
- c2_drooling_potential
- d5_tendency_to_bark_or_howl
- e3_exercise_needs

# STEP 3: Critical Instructions for Negations and Logical Implications
Please pay close attention to negations and implied meanings in the user's input:
1. Children and Pets (b2_incredibly_kid_friendly_dogs):
   - If the user specifies there are no children or pets in the house, or that they don't have kids (e.g., "no kids", "no children", "without kids", "no pets", "none", "no", "not having kids"): map to `b2_incredibly_kid_friendly_dogs: 1` (Adults Only).
   - If the user specifies there are kids in the house (e.g., "have kids", "there are kids", "yes", "kids"): map to `b2_incredibly_kid_friendly_dogs: 5`.
2. Experience Level (a2_good_for_novice_owners):
   - If the user specifies they have no experience, or haven't raised a dog before, or that it is their first dog (e.g., "first dog", "first time", "no experience", "haven't raised a dog", "none", "no"): map to `a2_good_for_novice_owners: 5` (meaning, good for novice owners).
   - If the user specifies they have experience or raised before (e.g., "raised before", "had dogs", "experienced", "have experience", "yes"): map to `a2_good_for_novice_owners: 1`.
3. Hours alone at home (a4_tolerates_being_alone):
   - If the user specifies the dog won't be left alone at all or barely (e.g., "won't be left alone", "never alone", "work from home", "not much", "no", "never", "always home"): map to `a4_tolerates_being_alone: 1`.
   - "not four hours" / "not many hours" -> map to `a4_tolerates_being_alone: 1`.
4. Living Environment (a1_adapts_well_to_apartment_living):
   - "not an apartment" / "not a small house" -> map to `a1_adapts_well_to_apartment_living: 1` (large yard).
5. Coat Length and Shedding (Implications):
   - "no long hair" / "without long hair" / "no long coat" -> map coat length to short `hair_length: "Short"`. In addition, infer that the user wants a dog that doesn't shed much, and thus map low shedding level `c1_amount_of_shedding: 1` or `2`.
   - "no shedding" / "allergic to hair" / "hypoallergenic" -> map low shedding level `c1_amount_of_shedding: 1` and short coat length `hair_length: "Short"`.
6. Noise and Barking Sensitivity (d5_tendency_to_bark_or_howl):
   - "quiet dog", "sensitive to noise", "no barking", "don't want barking", "should not bark", "quiet", "noise sensitive" -> map to `d5_tendency_to_bark_or_howl: 1`.
   - "guard dog", "bark when someone comes", "guard" -> map to `d5_tendency_to_bark_or_howl: 5`.
7. Energy level and exercise needs (e1_energy_level, e3_exercise_needs):
   - "I run", "love to run", "very active", "sporty", "long outdoor walks", "active", "runner" -> map `e1_energy_level: 5` and `e3_exercise_needs: 5`.
   - "couch potato", "lazy dog", "short walks", "lazy" -> map `e1_energy_level: 1` and `e3_exercise_needs: 1`.
8. Friendliness to other dogs at home (b3_dog_friendly):
   - "have a dog", "live with other dogs", "friendly to other dogs", "other dogs" -> map to `b3_dog_friendly: 5`.
9. Sensitivity to drool (c2_drooling_potential):
   - "no drool", "clean", "without drooling" -> map to `c2_drooling_potential: 1`.
10. Desire for a cuddly/velcro dog (b1_affectionate_with_family):
    - "cuddly dog", "velcro dog", "affectionate", "cuddle" -> map to `b1_affectionate_with_family: 5`.
11. Answering combined questions of noise/barking (d5_tendency_to_bark_or_howl) and shedding/allergies (c1_amount_of_shedding):
    - If the user says "no to both", "neither", "no for both questions", "noise no and shedding no" (or any negation of both): map to `d5_tendency_to_bark_or_howl: 1` and `c1_amount_of_shedding: 5`.
    - If the user says "no" or "doesn't bother me" for noise/barking: map to `d5_tendency_to_bark_or_howl: 1`.
    - If the user says "no" or "doesn't bother me" or "no issue" or "not a concern" for shedding/allergies (implying shedding is not a concern): map to `c1_amount_of_shedding: 5`.
    - If the user says "yes", "have allergies", "shedding is a concern", "prefer no shedding", "no hair" for shedding/allergies: map to `c1_amount_of_shedding: 1`.

# STEP 4: Handling short and partial answers (yes/no/have/don't have) based on the active parameter
The user is currently being asked a question regarding the following active parameter (active_param): {active_param}
If the user's current input is short or direct (e.g., "yes", "no", "have", "none", "don't have", "not really") and answers the question regarding {active_param}, please use the rules in STEP 3 and the meaning of {active_param} to determine the correct value.

Output Format (strictly JSON only):
{
  "state": "state_b",
  "extracted_parameters": {
    "a1_adapts_well_to_apartment_living": 5,
    "sex": "Male"
  }
}
"""

    system_prompt = system_prompt_he if lang == 'he' else system_prompt_en

    try:
        if client is None:
            raise Exception("OpenAI API key is missing or placeholder.")
        system_prompt_final = system_prompt.replace("{active_param}", str(active_param or "None"))
        
        if lang == 'he':
            user_prompt = f"היסטוריית נתונים עד כה (JSON): {json.dumps(current_params)}\n\nקלט המשתמש הנוכחי: '{user_text}'"
        else:
            user_prompt = f"Data history so far (JSON): {json.dumps(current_params)}\n\nCurrent user input: '{user_text}'"
            
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt_final},
                {"role": "user", "content": user_prompt}
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
Write personalized explanations and breed descriptions for 5 recommended dogs.
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
