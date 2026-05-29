from flask import Flask, request, jsonify, session, send_from_directory
from dotenv import load_dotenv
import os
from nlp_agent import analyze_user_input, generate_explanations
from ml_engine import recommend_dogs

load_dotenv()

app = Flask(__name__)
# Use a stable secret key to keep session valid across restarts and gunicorn workers
app.secret_key = os.getenv("SECRET_KEY", "pawmatch_secure_production_key_2026")

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
        "state_b_count": session.get('state_b_count', 0)
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
        nlp_result = analyze_user_input(user_message, session['text_params'])
    
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
            question, options = generate_question(missing[0], lang)
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

def generate_question(param_key, lang='he'):
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
    
    questions_en = {
        'a1_adapts_well_to_apartment_living': ("Tell me about your living environment (small apartment, large house, do you have a yard)?", None),
        'a4_tolerates_being_alone': ("Approximately how many hours is the dog expected to be left alone at home during the day?", None),
        'b2_incredibly_kid_friendly_dogs': ("Are there children or other pets in the house? Tell me a bit about your family.", None),
        'a2_good_for_novice_owners': ("What is your experience level with dogs (is it your first dog or have you raised dogs before)?", None),
        'sex': ("Which gender do you prefer?", ["Male", "Female", "No Preference"]),
        'size': ("Which size fits you best?", ["Small", "Medium", "Large", "No Preference"]),
        'hair_length': ("Which coat length do you prefer?", ["Short", "Long", "No Preference"]),
        'color': ("Do you have any coat color preference?", ["Black", "White", "Brown", "Gray", "Mixed", "No Preference"])
    }
    
    if lang == 'en':
        return questions_en.get(param_key, ("I need a bit more info, proceed to results?", ["Yes", "No Preference"]))
    return questions_he.get(param_key, ("חסר לי קצת מידע, להמשיך לתוצאות?", ["כן", "אין לי העדפה"]))

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
    rec = recommend_dogs(selects, text_params)
    lang = session.get('lang', 'he')
    
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
        explanations = generate_explanations(dogs, text_params, lang)
        
    # Merge explanations back into the dog records
    explanation_map = {e.get("name"): e for e in explanations if isinstance(e, dict)}
    for dog in dogs:
        exp = explanation_map.get(dog.get("name"), {})
        dog["match_reason"] = exp.get("match_reason", "")
        dog["breed_info"] = exp.get("breed_info", "")
        
    is_full_match = len(get_missing_critical(text_params)) == 0
    top_score = dogs[0].get("match_score") if dogs else 0
    score_val = top_score if (is_full_match and top_score >= 90) else None

    session.clear() # Reset for next
    
    response_payload = {
        "type": "result",
        "match_type": rec["type"],
        "dogs": dogs,
        "score": score_val,
        "session_data": {}
    }
    
    if "message" in rec:
        msg = rec["message"]
        if lang == 'en' and msg == "לא נמצאה התאמה ישירה. הנה הכלבים הדומים ביותר לפרופיל.":
            msg = "No direct match found. Here are the dogs most similar to your profile."
        response_payload["message"] = msg
        
    return jsonify(response_payload)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
