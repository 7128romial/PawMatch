from flask import Flask, request, jsonify, session, send_from_directory
from dotenv import load_dotenv
import os
import re
import json
import time

load_dotenv()

from nlp_agent import analyze_user_input, generate_explanations, answer_breed_question
from ml_engine import recommend_dogs

app = Flask(__name__)
# Use a stable secret key to keep session valid across restarts and gunicorn workers
app.secret_key = os.getenv("SECRET_KEY", "pawmatch_stable_secret_key_123")

def contains_sensitive_info(text):
    if not text:
        return False
    # Remove hyphens and spaces
    cleaned = re.sub(r'[\s\-]', '', str(text))
    # Search for exactly 9 or 10 consecutive digits
    match = re.search(r'(?<!\d)\d{9,10}(?!\d)', cleaned)
    return bool(match)

def is_primarily_english(text):
    if not text:
        return False
    letters = re.findall(r'[\u0590-\u05fe]|[a-zA-Z]', str(text))
    if not letters:
        return False
    eng_count = sum(1 for c in letters if re.match(r'[a-zA-Z]', c))
    heb_count = sum(1 for c in letters if re.match(r'[\u0590-\u05fe]', c))
    
    if eng_count > heb_count * 1.5:
        if len(text.strip().split()) <= 2 and eng_count < 15:
            return False
        return True
    return False

def is_abusive_intent(text):
    if not text:
        return False
    text_clean = text.strip().lower()
    patterns = [
        r'להרביץ',
        r'להכות',
        r'לבעוט',
        r'לפגוע בכלב',
        r'לפגוע לכלב',
        r'התעללות',
        r'להרוג',
        r'לרצוח',
        r'hit the dog',
        r'beat the dog',
        r'abuse',
        r'hurt the dog',
        r'kick the dog',
        r'kill the dog'
    ]
    for pattern in patterns:
        if re.search(pattern, text_clean):
            return True
    return False


def is_greeting_message(text):
    if not text:
        return False
    clean_msg = text.strip().lower()
    clean_msg_unpunct = re.sub(r'[^\w\s]', '', clean_msg).strip()
    greetings = ["היי", "שלום", "אהלן", "בוקר טוב", "צהריים טובים", "ערב טוב", "hi", "hello", "hey", "howdy"]
    words = clean_msg_unpunct.split()
    
    if clean_msg_unpunct in greetings:
        return True
    if len(words) <= 3 and any(w in greetings for w in words):
        return True
    
    # Check if the entire message is exactly one of the adoption intent phrases
    adoption_phrases = ["רוצה לאמץ", "מעוניין לאמץ", "מעוניינת לאמץ", "מחפש כלב", "מחפשת כלב", "רוצה כלב", "want to adopt", "adopt a dog", "looking for a dog"]
    if clean_msg_unpunct in adoption_phrases:
        return True
        
    return False



@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

button_mappings = {
    'sex': {
        'זכר': 'Male', 'Male': 'Male',
        'נקבה': 'Female', 'Female': 'Female',
        'אין לי העדפה': 'No Preference', 'No Preference': 'No Preference'
    },
    'size': {
        'קטן': 'Small', 'Small': 'Small',
        'בינוני': 'Medium', 'Medium': 'Medium',
        'גדול': 'Large', 'Large': 'Large',
        'אין לי העדפה': 'No Preference', 'No Preference': 'No Preference'
    },
    'age_group': {
        'גור': 'Puppy', 'Puppy': 'Puppy',
        'בוגר': 'Adult', 'Adult': 'Adult',
        'מבוגר': 'Senior', 'Senior': 'Senior',
        'אין לי העדפה': 'No Preference', 'No Preference': 'No Preference'
    },
    'color': {
        'שחור': 'Black', 'Black': 'Black',
        'לבן': 'White', 'White': 'White',
        'חום': 'Tan', 'Brown': 'Tan', 'Tan': 'Tan',
        'אפור': 'Gray', 'Gray': 'Gray',
        'מעורב': 'Bicolor', 'Mixed': 'Bicolor',
        'אין לי העדפה': 'No Preference', 'No Preference': 'No Preference'
    },
    'a1_adapts_well_to_apartment_living': {
        'דירה קטנה': 5, 'Small Apartment': 5,
        'דירה עם מרפסת': 4, 'Medium Apartment': 4,
        'בית עם חצר': 2, 'House with Yard': 2,
        'חצר גדולה': 1, 'Big Yard': 1,
        'אין לי העדפה': 3, 'No Preference': 3
    },
    'a4_tolerates_being_alone': {
        'מעט מאוד (עובד מהבית)': 1, 'Very Few (WFH)': 1,
        'חצי יום (4-6 שעות)': 3, 'Half Day (4-6 hours)': 3,
        'יום שלם (מעל 8 שעות)': 5, 'Full Day (8+ hours)': 5,
        'אין לי העדפה': 3, 'No Preference': 3
    },
    'b2_incredibly_kid_friendly_dogs': {
        'כן, ילדים קטנים': 5, 'Yes, Young Kids': 5,
        'ילדים גדולים': 4, 'Older Kids': 4,
        'רק מבוגרים': 1, 'Adults Only': 1,
        'אין לי העדפה': 3, 'No Preference': 3
    },
    'a2_good_for_novice_owners': {
        'כלב ראשון (אין ניסיון)': 5, 'First Dog (No experience)': 5,
        'גידלתי בעבר (יש ניסיון)': 1, 'Raised Before (Experienced)': 1,
        'אין לי העדפה': 3, 'No Preference': 3
    }
}

@app.route('/api/reset', methods=['POST'])
def reset():
    # Explicitly drop the previous user's accumulated free-text profile, then wipe the session.
    session.pop('user_raw_text', None)
    session.clear()
    return jsonify({"status": "success"})

def build_session_data():
    return {
        "text_params": session.get('text_params', {}),
        "state": session.get('state', 'step_1_size'),
        "no_preference_count": session.get('no_preference_count', 0),
        "state_b_count": session.get('state_b_count', 0),
        "last_asked_param": session.get('last_asked_param', None),
        "param_retry_count": session.get('param_retry_count', 0),
        "chat_history": session.get('chat_history', [])
    }

def build_combined_level_a_question(missing_keys, lang='he'):
    if lang == 'he':
        phrases = {
            'a1_adapts_well_to_apartment_living': "סביבת המגורים שלכם (דירה, בית עם חצר)",
            'e3_exercise_needs': "רמת הפעילות הפיזית או הטיולים שתוכלו להעניק לכלב",
            'a4_tolerates_being_alone': "כמה שעות בערך הכלב יישאר לבד ביום",
            'd5_tendency_to_bark_or_howl': "האם רעש או נביחות יפריעו לכם",
            'c1_amount_of_shedding': "האם נשירת פרווה/אלרגיות מהוות שיקול עבורכם"
        }
        parts = [phrases[k] for k in missing_keys if k in phrases]
        if parts:
            return f"כדי לדייק בהתאמה, ספרו לי קצת על {parts[0]}."
        return "כדי לדייק בהתאמה, ספרו לי קצת על אורח החיים שלכם."
    else:
        phrases = {
            'a1_adapts_well_to_apartment_living': "your living environment (apartment, house with yard)",
            'e3_exercise_needs': "the exercise level or walks you can provide for the dog",
            'a4_tolerates_being_alone': "how many hours the dog will be left alone daily",
            'd5_tendency_to_bark_or_howl': "whether barking or noise will be an issue for you",
            'c1_amount_of_shedding': "whether shedding or allergies are a concern for you"
        }
        parts = [phrases[k] for k in missing_keys if k in phrases]
        if parts:
            return f"To make the best match, tell me a bit about {parts[0]}."
        return "To make the best match, tell me a bit about your lifestyle."

def build_combined_level_b_question(missing_keys, lang='he'):
    if lang == 'he':
        phrases = {
            'c1_amount_of_shedding': "האם נשירת פרווה/אלרגיות מהוות שיקול עבורכם",
            'b3_dog_friendly': "האם יש לכם כלבים נוספים בבית",
            'b2_incredibly_kid_friendly_dogs': "האם הכלב יפגוש ילדים קטנים ביומיום",
            'd1_easy_to_train': "האם חשוב לכם שהכלב יהיה קל לאילוף",
            'a2_good_for_novice_owners': "האם יש לכם ניסיון קודם בגידול כלב"
        }
        parts = [phrases[k] for k in missing_keys if k in phrases]
        if parts:
            joined = " או ".join([", ".join(parts[:-1]), parts[-1]]) if len(parts) > 1 else parts[0]
            return f"שאלה נוספת (אופציונלית) – ספרו לי: האם רלוונטי לכם משהו מבין אלה? {joined}."
        return "יש עוד פרטים שתרצו לשתף?"
    else:
        phrases = {
            'c1_amount_of_shedding': "whether shedding or allergies are a concern for you",
            'b3_dog_friendly': "whether you have other dogs at home",
            'b2_incredibly_kid_friendly_dogs': "if you have young kids at home",
            'd1_easy_to_train': "whether ease of training is important to you",
            'a2_good_for_novice_owners': "your experience level with dogs (is this your first dog)"
        }
        parts = [phrases[k] for k in missing_keys if k in phrases]
        if parts:
            joined = " or ".join([", ".join(parts[:-1]), parts[-1]]) if len(parts) > 1 else parts[0]
            return f"One additional optional question – tell me if any of these are relevant: {joined}."
        return "Anything else you'd like to share?"

def get_next_question_and_options(text_params, lang='he'):
    # Step 1: Sequential physical filters
    if 'size' not in text_params:
        question = "איזה גודל כלב מתאים לכם יותר?" if lang == 'he' else "Which size fits you best?"
        options = ["קטן", "בינוני", "גדול", "אין לי העדפה"] if lang == 'he' else ["Small", "Medium", "Large", "No Preference"]
        return question, options, 'step_1_size'
        
    if 'age_group' not in text_params:
        question = "איזה גיל כלב אתם מעדיפים?" if lang == 'he' else "Which age group do you prefer?"
        options = ["גור", "בוגר", "מבוגר", "אין לי העדפה"] if lang == 'he' else ["Puppy", "Adult", "Senior", "No Preference"]
        return question, options, 'step_1_age'
        
    if 'sex' not in text_params:
        question = "איזה מין כלב אתם מעדיפים?" if lang == 'he' else "Which gender do you prefer?"
        options = ["זכר", "נקבה", "אין לי העדפה"] if lang == 'he' else ["Male", "Female", "No Preference"]
        return question, options, 'step_1_sex'
        
    if 'color' not in text_params:
        question = "איזה צבע פרווה אתם מעדיפים?" if lang == 'he' else "Do you have any coat color preference?"
        options = ["שחור", "לבן", "חום", "אפור", "מעורב", "אין לי העדפה"] if lang == 'he' else ["Black", "White", "Brown", "Gray", "Mixed", "No Preference"]
        return question, options, 'step_1_color'

    # All physical filters answered.
    # Level A parameters
    level_a = [
        'a1_adapts_well_to_apartment_living',
        'e3_exercise_needs',
        'a4_tolerates_being_alone',
        'd5_tendency_to_bark_or_howl'
    ]
    missing_level_a = [p for p in level_a if p not in text_params]
    
    if not text_params.get('welcome_done'):
        question = ("ספר/י לי קצת על עצמך ועל אורח החיים שלך, ככל שתפרט/י יותר, ההתאמה תהיה מדויקת יותר. למשל, ספרו לי איפה אתם גרים (דירה/בית עם חצר)?" 
                    if lang == 'he' else 
                    "Tell me a bit about yourself and your lifestyle. The more details you provide, the more accurate the match will be. For example, where do you live (apartment/house)?")
        return question, None, 'step_2_welcome'

    # Step 4: Combined Level A question
    if missing_level_a:
        question = build_combined_level_a_question(missing_level_a, lang)
        return question, None, 'step_4_essential'

    # Step 5: Combined Level B question
    level_b = [
        'c1_amount_of_shedding',
        'b3_dog_friendly',
        'b2_incredibly_kid_friendly_dogs',
        'd1_easy_to_train',
        'a2_good_for_novice_owners'
    ]
    missing_level_b = [p for p in level_b if p not in text_params]
    if missing_level_b and not text_params.get('soft_done'):
        question = build_combined_level_b_question(missing_level_b, lang)
        options = ["הצג תוצאות עכשיו"] if lang == 'he' else ["Show Results Now"]
        return question, options, 'step_5_soft'

    # Everything is complete!
    return None, None, 'state_q'

def parse_filter_value(param, text):
    if not text:
        return None
    text_clean = text.strip().lower()
    
    if text_clean in ["no preference", "אין העדפה", "אין לי העדפה", "כלשהו", "any", "בלי העדפה", "לא משנה", "הכל הולך", "הכל"]:
        return "No Preference"
        
    if param == 'size':
        if text_clean in ['קטן', 'small', 's', 'small size', 'קטנה']:
            return 'Small'
        if text_clean in ['בינוני', 'medium', 'm', 'medium size', 'בינונית']:
            return 'Medium'
        if text_clean in ['גדול', 'large', 'l', 'large size', 'גדולה', 'ענק']:
            return 'Large'
            
    elif param == 'age_group':
        if text_clean in ['גור', 'puppy', 'puppies', 'גורים', 'צעיר', 'גורה']:
            return 'Puppy'
        if text_clean in ['בוגר', 'adult', 'בוגרים', 'בוגרת']:
            return 'Adult'
        if text_clean in ['מבוגר', 'senior', 'מבוגרים', 'מבוגרת', 'זקן', 'קשיש']:
            return 'Senior'
            
    elif param == 'sex':
        if text_clean in ['זכר', 'male', 'בן', 'זכרים']:
            return 'Male'
        if text_clean in ['נקבה', 'female', 'בת', 'נקבות']:
            return 'Female'
            
    elif param == 'color':
        if text_clean in ['שחור', 'black', 'dark', 'שחורה']:
            return 'Black'
        if text_clean in ['לבן', 'white', 'light', 'לבנה']:
            return 'White'
        if text_clean in ['חום', 'brown', 'tan', 'חום בהיר', 'ג\'ינג\'י', 'חומה']:
            return 'Tan'
        if text_clean in ['אפור', 'gray', 'grey', 'אפורה']:
            return 'Gray'
        if text_clean in ['מעורב', 'mixed', 'bicolor', 'דו-צבעי', 'דו צבעי', 'צבעוני']:
            return 'Bicolor'
            
    return None

def get_missing_critical(params):
    v3_criticals = [
        'size',
        'age_group',
        'sex',
        'color',
        'a1_adapts_well_to_apartment_living',
        'e3_exercise_needs',
        'a4_tolerates_being_alone'
    ]
    return [c for c in v3_criticals if c not in params]

@app.route('/api/chat', methods=['POST'])
def chat(parsed_data=None):
    data = parsed_data if parsed_data is not None else (request.json or {})
    user_message = data.get('message', data.get('selection', ''))
    if user_message and len(user_message) > 500:
        err_msg = "ההודעה ארוכה מדי. אנא קצר/י ל-500 תווים." if request.json.get('lang', 'he') == 'he' else "Message is too long. Please shorten to 500 characters."
        return jsonify({
            "response": err_msg,
            "session_data": {
                "text_params": session.get('text_params', {}),
                "state": session.get('state', 'step_1_size'),
                "no_preference_count": session.get('no_preference_count', 0),
                "state_b_count": session.get('state_b_count', 0)
            }
        })
        
    selects = data.get('selects', {})
    skip_to_results = data.get('skip', False)
    lang = data.get('lang', 'he')
    
    session['lang'] = lang
    
    # Ensure session variables exist
    if 'text_params' not in session:
        session['text_params'] = {}
    text_params = session['text_params']
        
    no_preference_count = session.get('no_preference_count', 0)
    session['no_preference_count'] = no_preference_count
    
    state_b_count = session.get('state_b_count', 0)
    session['state_b_count'] = state_b_count
    
    current_session_state = session.get('state', 'step_1_size')
    session['state'] = current_session_state
    
    # Check for sensitive personal information (privacy guardrail)
    if contains_sensitive_info(user_message):
        warning_msg = (
            "⚠️ Attention: Your message seems to contain a phone number or ID number. "
            "To protect your privacy, please do not share sensitive personal information here. "
            "Please rewrite your request without it."
        ) if lang == 'en' else (
            "⚠️ שים לב: ההודעה שלך נראית כמי שמכילה מספר טלפון או מספר תעודת זהות. "
            "למען שמירה על פרטיותך וביטחונך, אנא אל תשתף מידע אישי רגיש בצ'אט. "
            "אנא נסח שוב את פנייתך ללא פרטים אלו."
        )
        return jsonify({
            "response": warning_msg,
            "session_data": build_session_data()
        })

    # Check for abusive intent or violence towards animals
    if is_abusive_intent(user_message):
        abuse_warning = (
            "🚨 Warning: PawMatch strongly opposes any form of violence or animal abuse. "
            "Your request has been blocked. A dog is a living soul deserving of respectful treatment, loving care, and complete protection."
        ) if lang == 'en' else (
            "🚨 אזהרה: PawMatch מתנגדת בתוקף לכל גילוי של אלימות או התעללות בבעלי חיים. "
            "פנייתך נחסמה. כלב הוא נפש חיה הזכאית ליחס מכבד, טיפול אוהב והגנה מלאה."
        )
        return jsonify({
            "response": abuse_warning,
            "session_data": build_session_data()
        })

    # Check if the user is typing English in Hebrew mode
    if lang == 'he' and is_primarily_english(user_message):
        is_button = False
        current_param = None
        if 'size' not in session['text_params']:
            current_param = 'size'
        elif 'age_group' not in session['text_params']:
            current_param = 'age_group'
        elif 'sex' not in session['text_params']:
            current_param = 'sex'
        elif 'color' not in session['text_params']:
            current_param = 'color'
            
        if current_param is not None:
            if parse_filter_value(current_param, user_message) is not None:
                is_button = True
                
        clean_msg = user_message.strip().lower()
        if clean_msg in ["no preference", "show results now", "other"]:
            is_button = True
            
        if not is_button:
            lang_warning = (
                "⚠️ שמנו לב שהקלדת באנגלית. כדי לקבל את החוויה הטובה ביותר ולסייע לנו להתאים לך במדויק, "
                "אנא לחצו על כפתור 🌐 **English** בראש המסך כדי להעביר את ממשק השיחה לאנגלית."
            )
            return jsonify({
                "response": lang_warning,
                "session_data": build_session_data()
            })

    is_skip_text = user_message in ["הצג תוצאות עכשיו", "Show Results Now", "הציגי לי תוצאות חלקיות עכשיו", "Show me partial results now"]
    if skip_to_results or is_skip_text:
        session['text_params']['soft_done'] = True
        session['state'] = 'state_q'
        return process_recommendation(selects, session['text_params'])
        
    if current_session_state == "state_q":
        recommended_breeds = session.get('recommended_dogs', [])
        session['recommended_dogs'] = recommended_breeds
        if not user_message:
            err_msg = "Please enter text." if lang == 'en' else "אנא הכנס טקסט."
            return jsonify({
                "response": err_msg,
                "session_data": {
                    "text_params": text_params,
                    "state": "state_q",
                    "recommended_dogs": recommended_breeds
                }
            })
        answer = answer_breed_question(user_message, recommended_breeds, lang)
        return jsonify({
            "response": answer,
            "session_data": {
                "text_params": text_params,
                "state": "state_q",
                "recommended_dogs": recommended_breeds
            }
        })
        
    if not user_message:
        err_msg = "Please enter text." if lang == 'en' else "אנא הכנס טקסט."
        return jsonify({
            "response": err_msg,
            "session_data": build_session_data()
        })
        
    # Check if we are in Step 1 (Physical filters)
    current_param = None
    if 'size' not in session['text_params']:
        current_param = 'size'
    elif 'age_group' not in session['text_params']:
        current_param = 'age_group'
    elif 'sex' not in session['text_params']:
        current_param = 'sex'
    elif 'color' not in session['text_params']:
        current_param = 'color'
        
    if current_param is not None:
        val = parse_filter_value(current_param, user_message)
        if val is not None:
            session['text_params'][current_param] = val
            next_q, next_opts, next_state = get_next_question_and_options(session['text_params'], lang)
            session['state'] = next_state
            return jsonify({
                "response": next_q,
                "options": next_opts,
                "session_data": build_session_data()
            })
        else:
            is_greeting = is_greeting_message(user_message)
            is_off_topic = False
            nlp_result = {}
            if not is_greeting:
                nlp_result = analyze_user_input(user_message, session['text_params'], active_param=None, lang=lang)
                if nlp_result.get("state") == "state_a":
                    # Fallback check
                    clean_msg = user_message.strip().lower()
                    clean_msg_unpunct = re.sub(r'[^\w\s]', '', clean_msg).strip()
                    greetings = ["היי", "שלום", "אהלן", "בוקר טוב", "צהריים טובים", "ערב טוב", "hi", "hello", "hey", "howdy"]
                    if clean_msg_unpunct in greetings or any(g in clean_msg_unpunct for g in greetings):
                        is_greeting = True
                    else:
                        is_off_topic = True
            
            if not is_off_topic and not is_greeting and nlp_result.get("state") != "error" and nlp_result.get("extracted_parameters"):
                for k, v in nlp_result["extracted_parameters"].items():
                    if v is not None and v != "":
                        session['text_params'][k] = v
            
            next_q, next_opts, next_state = get_next_question_and_options(session['text_params'], lang)
            session['state'] = next_state
            
            friendly_names = {
                'he': { 'size': 'גודל', 'age_group': 'גיל', 'sex': 'מין', 'color': 'צבע' },
                'en': { 'size': 'size', 'age_group': 'age group', 'sex': 'gender', 'color': 'color' }
            }
            param_name = friendly_names[lang].get(current_param, current_param)
            
            if is_off_topic:
                msg = (
                    f"I can only help with matching dogs for adoption. Let's focus on selecting the dog's {param_name}:\n\n{next_q}"
                    if lang == 'en' else
                    f"אני יודע לעזור רק בהתאמת כלבים לאימוץ. בואו נתמקד בבחירת {param_name} הכלב:\n\n{next_q}"
                )
            elif is_greeting:
                msg = (
                    f"Great! Let's start the matching process:\n\n{next_q}"
                    if lang == 'en' else
                    f"בשמחה! בואו נתחיל בתהליך ההתאמה:\n\n{next_q}"
                )
            else:
                msg = (
                    f"Got it. Let's focus on selecting the dog's {param_name} to proceed:\n\n{next_q}"
                    if lang == 'en' else
                    f"הבנתי. בואו נתמקד בבחירת {param_name} הכלב כדי שנוכל להתקדם:\n\n{next_q}"
                )
            
            return jsonify({
                "response": msg,
                "options": next_opts,
                "session_data": build_session_data()
            })
        
    # Free-text processing (Steps 2, 4, 5)
    level_a = [
        'a1_adapts_well_to_apartment_living',
        'e3_exercise_needs',
        'a4_tolerates_being_alone',
        'd5_tendency_to_bark_or_howl'
    ]
    missing_level_a = [p for p in level_a if p not in session['text_params']]
    
    level_b = [
        'b3_dog_friendly',
        'b2_incredibly_kid_friendly_dogs',
        'd1_easy_to_train',
        'c1_amount_of_shedding',
        'a2_good_for_novice_owners'
    ]
    missing_level_b = [p for p in level_b if p not in session['text_params']]
    
    active_params_str = ", ".join(missing_level_a) if missing_level_a else None
    
    is_greeting = is_greeting_message(user_message)
    if is_greeting:
        next_q, next_opts, next_state = get_next_question_and_options(session['text_params'], lang)
        session['state'] = next_state
        msg = (
            f"Great! Let's continue the matching process:\n\n{next_q}"
            if lang == 'en' else
            f"בשמחה! בואו נמשיך בתהליך ההתאמה:\n\n{next_q}"
        )
        return jsonify({
            "response": msg,
            "options": next_opts,
            "session_data": build_session_data()
        })

    # צבירת הטקסט החופשי הגולמי של המשתמש לאורך כל השיחה (לא מוגבל כמו chat_history),
    # כדי שמנוע הנימוקים יוכל להצליב מול אורח החיים המקורי שתואר.
    if user_message:
        existing_raw = session.get('user_raw_text', '')
        session['user_raw_text'] = (existing_raw + " " + user_message).strip() if existing_raw else user_message.strip()

    retry_count = session.get('param_retry_count', 0)
    chat_history = session.get('chat_history', [])
    nlp_result = analyze_user_input(user_message, session['text_params'], active_param=active_params_str, lang=lang, retry_count=retry_count, chat_history=chat_history)
    
    if nlp_result.get("state") == "error":
        err_msg = "Error connecting to model. Please check API key." if lang == 'en' else "שגיאה בחיבור למודל. אנא בדוק מפתח API."
        return jsonify({
            "response": err_msg,
            "session_data": build_session_data()
        })
        
    state = nlp_result.get('state')
    extracted = nlp_result.get('extracted_parameters', {})
    next_question_from_llm = nlp_result.get('next_question', '')
    
    if state == "state_e":
        fallback_msg = ("Adopting a dog is a significant and long-term responsibility (10-15 years) and is not recommended solely out of boredom or as a temporary solution. "
               "A dog is a living soul that needs care, time, and lots of love. If you are ready for this commitment, tell me about your lifestyle and we can begin the match.") if lang == 'en' else \
              ("אימוץ כלב הוא צעד משמעותי ואחראי לטווח ארוך (10-15 שנים) ולא מומלץ לעשות זאת רק מתוך שעמום או כפתרון זמני. "
               "כלב הוא נפש חיה שזקוקה לטיפול, זמן והמון אהבה. אם אתם מוכנים להתחייבות הזו, ספרו לי על אורח החיים שלכם ונתחיל בהתאמה.")
        msg = next_question_from_llm if next_question_from_llm else fallback_msg
        
        if user_message and msg:
            ch = session.get('chat_history', [])
            ch.append({"role": "user", "content": user_message})
            ch.append({"role": "assistant", "content": msg})
            session['chat_history'] = ch[-6:]
            
        return jsonify({
            "response": msg,
            "session_data": build_session_data()
        })

    if state == "state_a":
        # Fallback check
        clean_msg = user_message.strip().lower()
        clean_msg_unpunct = re.sub(r'[^\w\s]', '', clean_msg).strip()
        greetings = ["היי", "שלום", "אהלן", "בוקר טוב", "צהריים טובים", "ערב טוב", "hi", "hello", "hey", "howdy"]
        if clean_msg_unpunct in greetings or any(g in clean_msg_unpunct for g in greetings):
            next_q, next_opts, next_state = get_next_question_and_options(session['text_params'], lang)
            session['state'] = next_state
            msg = (
                f"Great! Let's continue the matching process:\n\n{next_q}"
                if lang == 'en' else
                f"בשמחה! בואו נמשיך בתהליך ההתאמה:\n\n{next_q}"
            )
            return jsonify({
                "response": msg,
                "options": next_opts,
                "session_data": build_session_data()
            })

        next_q, next_opts, next_state = get_next_question_and_options(session['text_params'], lang)
        msg = next_question_from_llm if next_question_from_llm else (
            f"I can only help with matching dogs for adoption. Let's get back to our matching:\n\n{next_q}"
            if lang == 'en' else
            f"אני יודע לעזור רק בהתאמת כלבים לאימוץ. בואו נחזור להתאמה שלנו:\n\n{next_q}"
        )
        if user_message and msg:
            ch = session.get('chat_history', [])
            ch.append({"role": "user", "content": user_message})
            ch.append({"role": "assistant", "content": msg})
            session['chat_history'] = ch[-6:]
            
        return jsonify({
            "response": msg,
            "options": next_opts,
            "session_data": build_session_data()
        })
        
    # Merge extracted parameters
    if extracted:
        for k, v in extracted.items():
            if v is not None and v != "":
                session['text_params'][k] = v
            
    # Retry tracking for the active parameters
    if active_params_str:
        # Check which of the previously missing parameters were just extracted
        newly_extracted = [p for p in missing_level_a if p in session['text_params']]
        
        if len(newly_extracted) == len(missing_level_a):
            # All asked parameters were extracted
            session['param_retry_count'] = 0
            session['confidence_penalty'] = session.get('confidence_penalty', False) or any(session['text_params'][p] == 3 for p in missing_level_a) and retry_count >= 1
        elif len(newly_extracted) > 0:
            # User answered AT LEAST ONE of the asked parameters. 
            # Reset retry count so the bot can ask about the remaining ones without skipping.
            session['param_retry_count'] = 0
        else:
            # User answered NONE of the asked parameters.
            new_retry = retry_count + 1
            session['param_retry_count'] = new_retry
            if new_retry >= 2:
                # Force fill all missing Tier A to prevent infinite loop
                for p in missing_level_a:
                    if p not in session['text_params']:
                        session['text_params'][p] = 3
                session['confidence_penalty'] = True
                session['param_retry_count'] = 0

    if current_session_state == 'step_2_welcome':
        session['text_params']['welcome_done'] = True
    elif current_session_state == 'step_5_soft':
        session['text_params']['soft_done'] = True
        
    next_q, next_opts, next_state = get_next_question_and_options(session['text_params'], lang)
    session['state'] = next_state

    # Reconcile a model/backend disagreement: the model declared it has all the
    # essential info (state_d) and tends to reply "results coming soon", but the
    # backend is still missing a Tier A trait it never managed to extract (e.g. the
    # user never discussed barking). Without this we'd show that message and dead-end
    # with no question and no results. Default the missing essentials and proceed.
    if state == 'state_d' and next_state == 'step_4_essential':
        # LLM hallucinated state_d early. Demote state and force backend question.
        state = 'state_c'
        response_text = next_q
    elif next_state == 'step_5_soft':
        response_text = next_q
    else:
        response_text = next_question_from_llm if next_question_from_llm else next_q
        
    if next_state == 'state_q':
        return process_recommendation(selects, session['text_params'])
    
    if user_message and response_text:
        ch = session.get('chat_history', [])
        ch.append({"role": "user", "content": user_message})
        ch.append({"role": "assistant", "content": response_text})
        session['chat_history'] = ch[-6:]
        
    return jsonify({
        "response": response_text,
        "options": next_opts,
            "session_data": build_session_data()
        })

@app.route('/api/button_click', methods=['POST'])
def button_click():
    data = dict(request.json or {})
    selection = data.get('selection')
    
    # Secure session initialization (ignore client_session)
    if 'text_params' not in session:
        session['text_params'] = {}
    session['no_preference_count'] = session.get('no_preference_count', 0)
    session['state_b_count'] = session.get('state_b_count', 0)
    session['state'] = session.get('state', 'step_1_size')
    
    if selection in ["אין לי העדפה", "No Preference"]:
        session['no_preference_count'] = session.get('no_preference_count', 0) + 1
        
    data['message'] = selection
    return chat(parsed_data=data)

def process_recommendation(selects, text_params):
    try:
        lang = session.get('lang', 'he')
        rec = recommend_dogs(selects, text_params, lang=lang)
        
        if "error" in rec:
            err_msg = rec["error"]
            if lang == 'en' and err_msg == "Dataset not loaded.":
                err_msg = "Dataset not loaded."
            session.clear()
            return jsonify({
                "response": err_msg,
                "session_data": {}
            })
            
        dogs = rec.get("dogs", [])

        # הטקסט החופשי הגולמי שנצבר ב-session לאורך השיחה (השלם, לא מוגבל ל-6 הודעות)
        user_original_text = session.get('user_raw_text', '')
        # נפילה אחורה: אם לא נצבר טקסט (למשל הגעה לתוצאות דרך כפתורים בלבד), נשחזר מהיסטוריית השיחה
        if not user_original_text:
            chat_history = session.get('chat_history', [])
            user_original_text = " ".join(
                msg.get("content", "")
                for msg in chat_history
                if msg.get("role") == "user" and msg.get("content")
            ).strip()

        # Section #12: if the breed-alternative fallback was used, tell the explanation
        # layer which breed the user originally wanted so it can frame the alternatives.
        breed_requested = rec.get("breed_requested") if rec.get("fallback_to_breed_vector") else None

        explanations = []
        if dogs:
            try:
                explanations = generate_explanations(
                    dogs=dogs,
                    user_params=text_params,
                    user_original_text=user_original_text,
                    breed_requested=breed_requested,
                    lang=lang
                )
            except Exception as ex_err:
                print(f"Error generating explanations: {ex_err}")
                explanations = []
            if not isinstance(explanations, list):
                explanations = []
            
        explanation_map = {e.get("breed", e.get("name")): e for e in explanations if isinstance(e, dict)}
        for dog in dogs:
            exp = explanation_map.get(dog.get("breed", dog.get("name")), {})
            dog["match_reason"] = exp.get("match_reason", "")
            dog["breed_info"] = exp.get("breed_info", "")

            # Innovation layer 2: surface the Isolation Forest anomaly flag to the user.
            # is_anomaly == -1 is the data-driven flag precomputed in dogs_final.csv.
            # cluster 4 (outlier_unique / Basenji) is also treated as anomalous.
            is_anomaly = dog.get("is_anomaly") == -1 or dog.get("cluster") == 4
            if is_anomaly:
                anomaly_warning = (
                    "\n\n⚠️ שימו לב: כלב זה בעל פרופיל התנהגותי ייחודי ולא שגרתי, מומלץ להתייעץ עם צוות המקלט."
                    if lang == 'he' else
                    "\n\n⚠️ Note: This dog has a highly unique behavioral profile, shelter consultation recommended."
                )
                dog["match_reason"] = (dog["match_reason"] or "") + anomaly_warning

        is_full_match = len(get_missing_critical(text_params)) == 0
        top_score = dogs[0].get("match_score") if dogs else 0
        score_val = top_score if (is_full_match and top_score >= 90) else None

        session['state'] = "state_q"
        session['recommended_dogs'] = [d.get("breed") for d in dogs]
        
        session['last_asked_param'] = None
        session['param_retry_count'] = 0
        
        confidence_level = "Medium" if session.get('confidence_penalty') else "High"
        
        response_payload = {
            "type": "result",
            "match_type": rec["type"],
            "confidence_level": confidence_level,
            "dogs": dogs,
            "score": score_val,
            "session_data": {
                "text_params": text_params,
                "state": "state_q",
                "no_preference_count": 0,
                "state_b_count": 0,
                "last_asked_param": None,
                "param_retry_count": 0,
                "recommended_dogs": session['recommended_dogs']
            }
        }
        
        msg = rec.get("message", "")
        if lang == 'en' and msg == "לא נמצאה התאמה ישירה. הנה הכלבים הדומים ביותר לפרופיל.":
            msg = "No direct match found. Here are the dogs most similar to your profile."
            
        if confidence_level == "Medium":
            warning_text = "הערה: חלק מהנתונים חסרים, לכן ההמלצה היא ברמת ביטחון בינונית." if lang == 'he' else "Note: Some data is missing, so this recommendation is at Medium Confidence."
            msg = f"{msg}\n\n{warning_text}" if msg else warning_text
            
        if msg:
            response_payload["message"] = msg
            
        return jsonify(response_payload)
    except Exception as e:
        import traceback
        traceback.print_exc()
        lang = session.get('lang', 'he')
        err_msg = "Internal server error occurred while processing recommendations." if lang == 'en' else "שגיאת שרת פנימית בעת עיבוד ההמלצות."
        return jsonify({
            "response": err_msg,
            "session_data": {
                "text_params": text_params,
                "state": "step_1_size",
                "no_preference_count": 0,
                "state_b_count": 0
            }
        })

if __name__ == '__main__':
    # Render מגדיר את הפורט דרך משתנה סביבה. אם הוא לא קיים, נשתמש ב-5000 לוקאלית.
    port = int(os.environ.get("PORT", 5000))
    # ב-Production (Render) אנחנו מכבים את ה-debug ומאפשרים גישה מכל הכתובות (0.0.0.0)
    app.run(host='0.0.0.0', port=port, debug=False)
