from flask import Flask, request, jsonify, session, send_from_directory
from dotenv import load_dotenv
import os
import re

load_dotenv()

from nlp_agent import analyze_user_input, generate_explanations, answer_breed_question
from ml_engine import recommend_dogs

app = Flask(__name__)
# Use a stable secret key to keep session valid across restarts and gunicorn workers
app.secret_key = os.getenv("SECRET_KEY", "pawmatch_secure_production_key_2026")

def contains_sensitive_info(text):
    if not text:
        return False
    # Remove hyphens and spaces
    cleaned = re.sub(r'[\s\-]', '', str(text))
    # Search for exactly 9 or 10 consecutive digits
    match = re.search(r'(?<!\d)\d{9,10}(?!\d)', cleaned)
    return bool(match)


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
    'hair_length': {
        'קצרה': 'Short', 'Short': 'Short',
        'ארוכה': 'Long', 'Long': 'Long',
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
    session.clear()
    return jsonify({"status": "success"})

def build_session_data():
    return {
        "text_params": session.get('text_params', {}),
        "state": session.get('state', 'state_b'),
        "no_preference_count": session.get('no_preference_count', 0),
        "state_b_count": session.get('state_b_count', 0),
        "last_asked_param": session.get('last_asked_param', None),
        "param_retry_count": session.get('param_retry_count', 0)
    }

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json or {}
    user_message = data.get('message', data.get('selection', ''))
    selects = data.get('selects', {})
    skip_to_results = data.get('skip', False)
    lang = data.get('lang', 'he')
    
    # Store active language in session
    session['lang'] = lang
    
    # Load session data from request payload or fallback to Flask session
    client_session = data.get('session_data') or {}
    
    text_params = client_session.get('text_params')
    if text_params is None:
        if 'text_params' not in session:
            session['text_params'] = {}
        text_params = session['text_params']
    else:
        session['text_params'] = text_params
        
    no_preference_count = client_session.get('no_preference_count')
    if no_preference_count is None:
        no_preference_count = session.get('no_preference_count', 0)
    session['no_preference_count'] = no_preference_count
    
    state_b_count = client_session.get('state_b_count')
    if state_b_count is None:
        state_b_count = session.get('state_b_count', 0)
    session['state_b_count'] = state_b_count
    
    current_session_state = client_session.get('state')
    if current_session_state is None:
        current_session_state = session.get('state', 'state_b')
    session['state'] = current_session_state
    
    last_asked_param = client_session.get('last_asked_param')
    if last_asked_param is None:
        last_asked_param = session.get('last_asked_param', None)
    session['last_asked_param'] = last_asked_param
    
    param_retry_count = client_session.get('param_retry_count')
    if param_retry_count is None:
        param_retry_count = session.get('param_retry_count', 0)
    session['param_retry_count'] = param_retry_count
    
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

    
    if current_session_state == "state_q":
        recommended_breeds = client_session.get('recommended_dogs', session.get('recommended_dogs', []))
        session['recommended_dogs'] = recommended_breeds
        if not user_message:
            err_msg = "Please enter text." if lang == 'en' else "אנא הכנס טקסט."
            return jsonify({
                "response": err_msg,
                "session_data": {
                    "text_params": text_params,
                    "state": "state_q",
                    "no_preference_count": no_preference_count,
                    "state_b_count": state_b_count,
                    "recommended_dogs": recommended_breeds
                }
            })
        answer = answer_breed_question(user_message, recommended_breeds, lang)
        return jsonify({
            "response": answer,
            "session_data": {
                "text_params": text_params,
                "state": "state_q",
                "no_preference_count": no_preference_count,
                "state_b_count": state_b_count,
                "recommended_dogs": recommended_breeds
            }
        })
        
    if skip_to_results or session['no_preference_count'] >= 2:
        return process_recommendation(selects, session['text_params'])
        
    if not user_message:
        err_msg = "Please enter text." if lang == 'en' else "אנא הכנס טקסט."
        return jsonify({
            "response": err_msg,
            "session_data": build_session_data()
        })
        
    # Get missing parameters before processing
    missing_before = get_missing_critical(session['text_params'])
    
    # Intercept button selections / "No Preference" in the backend
    is_button_option = False
    extracted_val = None
    if missing_before:
        current_param = missing_before[0]
        if current_param in button_mappings:
            msg_key = user_message.strip()
            if msg_key in button_mappings[current_param]:
                extracted_val = button_mappings[current_param][msg_key]
                is_button_option = True
            elif msg_key.lower() in {k.lower(): v for k, v in button_mappings[current_param].items()}:
                extracted_val = {k.lower(): v for k, v in button_mappings[current_param].items()}[msg_key.lower()]
                is_button_option = True

    if is_button_option:
        session['text_params'][current_param] = extracted_val
        # Bypass the LLM API call, preserve the session state
        nlp_result = {"state": session.get('state', "state_c"), "extracted_parameters": {}}
    elif user_message in ["אין לי העדפה", "No Preference"] and missing_before:
        current_param = missing_before[0]
        if current_param in ['sex', 'size', 'hair_length', 'color']:
            session['text_params'][current_param] = "No Preference"
        else:
            session['text_params'][current_param] = 3
        # Bypass the LLM API call
        nlp_result = {"state": session.get('state', "state_c"), "extracted_parameters": {}}
    else:
        # Analyze input normally via LLM
        active_param = missing_before[0] if missing_before else None
        nlp_result = analyze_user_input(user_message, session['text_params'], active_param=active_param, lang=lang)
    
    if nlp_result.get("state") == "error":
        err_msg = "Error connecting to model. Please check API key." if lang == 'en' else "שגיאה בחיבור למודל. אנא בדוק מפתח API."
        return jsonify({
            "response": err_msg,
            "session_data": build_session_data()
        })
        
    state = nlp_result.get('state')
    extracted = nlp_result.get('extracted_parameters', {})
    
    # Merge parameters
    for k, v in extracted.items():
        session['text_params'][k] = v
        
    # Prevent regression: if current session state is state_c or state_d, do not regress to state_a or state_b
    current_session_state = session.get('state', 'state_b')
    if current_session_state in ["state_c", "state_d"] and state in ["state_a", "state_b"]:
        state = current_session_state
        
    # Force state to state_c if there are still missing critical parameters
    missing_criticals = get_missing_critical(session['text_params'])
    if missing_criticals and state == "state_d":
        state = "state_c"
        
    # State Machine Logic
    if state == "state_e":
        msg = ("Adopting a dog is a significant and long-term responsibility (10-15 years) and is not recommended solely out of boredom or as a temporary solution. "
               "A dog is a living soul that needs care, time, and lots of love. If you are ready for this commitment, tell me about your lifestyle and we can begin the match.") if lang == 'en' else \
              ("אימוץ כלב הוא צעד משמעותי ואחראי לטווח ארוך (10-15 שנים) ולא מומלץ לעשות זאת רק מתוך שעמום או כפתרון זמני. "
               "כלב הוא נפש חיה שזקוקה לטיפול, זמן והמון אהבה. אם אתם מוכנים להתחייבות הזו, ספרו לי על אורח החיים שלכם ונתחיל בהתאמה.")
        return jsonify({
            "response": msg,
            "session_data": build_session_data()
        })

    if state == "state_a":
        session['state'] = "state_a"
        msg = "I can only help with matching dog breeds. Tell me about your environment and what you are looking for." if lang == 'en' else "אני יודע לעזור רק בהתאמת גזע כלב, ספרי לי על הסביבה שלך ועל מה את מחפשת."
        return jsonify({
            "response": msg,
            "session_data": build_session_data()
        })
        
    if state == "state_b":
        session['state_b_count'] = session.get('state_b_count', 0) + 1
        # If user is stuck in state_b for consecutive requests, upgrade to state_c to guide them
        if session['state_b_count'] >= 2:
            state = "state_c"
        else:
            session['state'] = "state_b"
            msg = "I'd love to hear more general details: Where do you live? How much time are you home? And what kind of dog personality matches you?" if lang == 'en' else "אשמח לשמוע עוד פרטים כלליים: איפה את גרה? כמה זמן את בבית? ואיזה אופי כלב מתאים לך?"
            return jsonify({
                "response": msg,
                "session_data": build_session_data()
            })
            
    if state == "state_c":
        session['state_b_count'] = 0
        session['state'] = "state_c"
        # Missing some info, ask a specific question with buttons
        missing = get_missing_critical(session['text_params'])
        if missing:
            current_param = missing[0]
            last_asked = session.get('last_asked_param')
            retry_count = session.get('param_retry_count', 0)
            
            if last_asked == current_param:
                retry_count += 1
            else:
                last_asked = current_param
                retry_count = 0
                
            session['last_asked_param'] = last_asked
            session['param_retry_count'] = retry_count
            
            question, options = generate_question(current_param, lang, retry_count)
            return jsonify({
                "response": question,
                "options": options,
                "session_data": build_session_data()
            })
        else:
            # If we somehow have all critical parameters, treat as state_d
            state = "state_d"
            
    if state == "state_d":
        session['state_b_count'] = 0
        session['state'] = "state_d"
        return process_recommendation(selects, session['text_params'])

    session['state'] = state
    msg = "I couldn't understand, could you rephrase?" if lang == 'en' else "לא הצלחתי להבין, אפשר לנסח שוב?"
    return jsonify({
        "response": msg,
        "session_data": build_session_data()
    })

def get_missing_critical(params):
    criticals = [
        'a1_adapts_well_to_apartment_living',
        'a4_tolerates_being_alone',
        'b2_incredibly_kid_friendly_dogs',
        'a2_good_for_novice_owners',
        'sex',
        'size',
        'hair_length',
        'color'
    ]
    return [c for c in criticals if c not in params]

def generate_question(param_key, lang='he', retry_count=0):
    if lang == 'he':
        questions_he = {
            'a1_adapts_well_to_apartment_living': ("ספרו לי על סביבת המגורים שלכם (דירה קטנה, בית גדול, האם יש חצר)?", None),
            'a4_tolerates_being_alone': ("כמה שעות בערך הכלב צפוי להישאר לבד בבית במהלך היום?", None),
            'b2_incredibly_kid_friendly_dogs': ("האם יש ילדים או חיות מחמד אחרות בבית? ספרו לי קצת על המשפחה שלכם.", None),
            'a2_good_for_novice_owners': ("מהי רמת הניסיון שלכם בגידול כלבים (האם זהו כלב ראשון או שגידלתם בעבר)?", None),
            'sex': ("איזה מין כלב אתם מעדיפים?", ["זכר", "נקבה", "אין לי העדפה"]),
            'size': ("איזה גודל כלב מתאים לכם יותר?", ["קטן", "בינוני", "גדול", "אין לי העדפה"]),
            'hair_length': ("איזה אורך פרווה אתם מעדיפים?", ["קצרה", "ארוכה", "אין לי העדפה"]),
            'color': ("איזה צבע פרווה אתם מעדיפים?", ["שחור", "לבן", "חום", "אפור", "מעורב", "אין לי העדפה"])
        }
        
        retry_questions_he = {
            'a1_adapts_well_to_apartment_living': ("האם אתם גרים בדירה (קטנה או גדולה) או בבית פרטי? ספרו לי כדי שנתאים את רמת הפעילות של הכלב למגורים שלכם.", None),
            'a4_tolerates_being_alone': ("כדי שאדייק בהתאמה, תוכלי להעריך פחות או יותר כמה שעות הכלב יהיה לבד ביום רגיל?", None),
            'b2_incredibly_kid_friendly_dogs': ("חשוב לי לדעת אם הכלב יפגוש ילדים קטנים ביומיום או שיש חיות מחמד נוספות בבית, כדי לסנן כלבים מתאימים.", None),
            'a2_good_for_novice_owners': ("האם כבר גידלתם בעבר כלב משלכם, או שזהו הכלב הראשון שאתם מאמצים וזקוקים לגזע קל במיוחד לאילוף?", None),
            'sex': ("כדי להתקדם, תוכלי לסמן אם יש העדפה למין הכלב?", ["זכר", "נקבה", "אין לי העדפה"]),
            'size': ("איזה טווח גודל של כלב אתם מחפשים? (בחרו מהאפשרויות הבאות כדי לסנן)", ["קטן", "בינוני", "גדול", "אין לי העדפה"]),
            'hair_length': ("בנוגע לפרווה, האם יש לכם העדפה לאורך הפרווה של הכלב?", ["קצרה", "ארוכה", "אין לי העדפה"]),
            'color': ("בנוגע לצבע הפרווה, האם יש צבע ספציפי שתרצו?", ["שחור", "לבן", "חום", "אפור", "מעורב", "אין לי העדפה"])
        }
        
        if retry_count > 0:
            return retry_questions_he.get(param_key, questions_he[param_key])
        return questions_he[param_key]
        
    else:
        questions_en = {
            'a1_adapts_well_to_apartment_living': ("Tell me about your living environment:", None),
            'a4_tolerates_being_alone': ("Approximately how many hours is the dog expected to be left alone at home during the day?", None),
            'b2_incredibly_kid_friendly_dogs': ("Are there children or other pets in the house?", None),
            'a2_good_for_novice_owners': ("What is your experience level with dogs?", None),
            'sex': ("Which gender do you prefer?", ["Male", "Female", "No Preference"]),
            'size': ("Which size fits you best?", ["Small", "Medium", "Large", "No Preference"]),
            'hair_length': ("Which coat length do you prefer?", ["Short", "Long", "No Preference"]),
            'color': ("Do you have any coat color preference?", ["Black", "White", "Brown", "Gray", "Mixed", "No Preference"])
        }
        
        retry_questions_en = {
            'a1_adapts_well_to_apartment_living': ("Do you live in an apartment or a house? Please let know so I can match the activity level:", None),
            'a4_tolerates_being_alone': ("To make a better match, how many hours is the dog expected to be alone on a typical day?", None),
            'b2_incredibly_kid_friendly_dogs': ("Could you tell me if there are children or other pets in the house so I can screen kid-friendly dogs?", None),
            'a2_good_for_novice_owners': ("Have you owned a dog before, or is this your first time adopting?", None),
            'sex': ("Do you have a preference for the dog's gender?", ["Male", "Female", "No Preference"]),
            'size': ("What size range are you looking for?", ["Small", "Medium", "Large", "No Preference"]),
            'hair_length': ("Do you have a preference for short or long coat?", ["Short", "Long", "No Preference"]),
            'color': ("Is there any specific coat color you prefer?", ["Black", "White", "Brown", "Gray", "Mixed", "No Preference"])
        }
        
        if retry_count > 0:
            return retry_questions_en.get(param_key, questions_en[param_key])
        return questions_en[param_key]


@app.route('/api/button_click', methods=['POST'])
def button_click():
    data = request.json or {}
    selection = data.get('selection')
    
    client_session = data.get('session_data') or {}
    session['text_params'] = client_session.get('text_params', session.get('text_params', {}))
    session['no_preference_count'] = client_session.get('no_preference_count', session.get('no_preference_count', 0))
    session['state_b_count'] = client_session.get('state_b_count', session.get('state_b_count', 0))
    session['state'] = client_session.get('state', session.get('state', 'state_b'))
    
    if selection in ["אין לי העדפה", "No Preference"]:
        session['no_preference_count'] = session.get('no_preference_count', 0) + 1
        
    # Inject selection as message so chat() can process it
    data['message'] = selection
    return chat()

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
        
        # Generate warm personalized explanations and breed details using GPT-3.5
        explanations = []
        if dogs:
            try:
                explanations = generate_explanations(dogs, text_params, lang)
            except Exception as ex_err:
                print(f"Error generating explanations: {ex_err}")
                explanations = []
            if not isinstance(explanations, list):
                explanations = []
            
        # Merge explanations back into the dog records
        explanation_map = {e.get("name"): e for e in explanations if isinstance(e, dict)}
        for dog in dogs:
            exp = explanation_map.get(dog.get("name"), {})
            dog["match_reason"] = exp.get("match_reason", "")
            dog["breed_info"] = exp.get("breed_info", "")
            
        is_full_match = len(get_missing_critical(text_params)) == 0
        top_score = dogs[0].get("match_score") if dogs else 0
        score_val = top_score if (is_full_match and top_score >= 90) else None

        # Do not clear session entirely, transition to state_q so user can ask questions about the breeds
        session['state'] = "state_q"
        session['recommended_dogs'] = [d.get("breed") for d in dogs]
        
        session['last_asked_param'] = None
        session['param_retry_count'] = 0
        
        response_payload = {
            "type": "result",
            "match_type": rec["type"],
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
        
        if "message" in rec:
            msg = rec["message"]
            if lang == 'en' and msg == "לא נמצאה התאמה ישירה. הנה הכלבים הדומים ביותר לפרופיל.":
                msg = "No direct match found. Here are the dogs most similar to your profile."
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
                "state": "state_c",
                "no_preference_count": 0,
                "state_b_count": 0
            }
        })

if __name__ == '__main__':
    app.run(debug=True, port=5000)
