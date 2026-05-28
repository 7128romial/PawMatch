from flask import Flask, request, jsonify, session, send_from_directory
from dotenv import load_dotenv
import os
from nlp_agent import analyze_user_input
from ml_engine import recommend_dogs

load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message', '')
    selects = data.get('selects', {})
    skip_to_results = data.get('skip', False)
    
    # Initialize session state if not exists
    if 'text_params' not in session:
        session['text_params'] = {}
    if 'no_preference_count' not in session:
        session['no_preference_count'] = 0
        
    if skip_to_results or session['no_preference_count'] >= 2:
        return process_recommendation(selects, session['text_params'])
        
    if not user_message:
        return jsonify({"response": "אנא הכנס טקסט."})
        
    # Analyze input
    nlp_result = analyze_user_input(user_message, session['text_params'])
    
    if nlp_result.get("state") == "error":
        return jsonify({"response": "שגיאה בחיבור למודל. אנא בדוק מפתח API."})
        
    state = nlp_result.get('state')
    extracted = nlp_result.get('extracted_parameters', {})
    
    # Merge parameters
    for k, v in extracted.items():
        session['text_params'][k] = v
        
    # State Machine Logic
    if state == "state_a":
        return jsonify({"response": "אני יודע לעזור רק בהתאמת גזע כלב, ספרי לי על הסביבה שלך ועל מה את מחפשת."})
        
    elif state == "state_b":
        return jsonify({"response": "אשמח לשמוע עוד פרטים כלליים: איפה את גרה? כמה זמן את בבית? ואיזה אופי כלב מתאים לך?"})
        
    elif state == "state_c":
        # Missing some info, ask a specific question with buttons
        missing = get_missing_critical(session['text_params'])
        if missing:
            question, options = generate_question(missing[0])
            return jsonify({
                "response": question,
                "options": options
            })
        else:
            # Somehow it's C but we have criticals, treat as D
            return process_recommendation(selects, session['text_params'])
            
    elif state == "state_d":
        return process_recommendation(selects, session['text_params'])

    return jsonify({"response": "לא הצלחתי להבין, אפשר לנסח שוב?"})

def get_missing_critical(params):
    criticals = [
        'a1_adapts_well_to_apartment_living',
        'a4_tolerates_being_alone',
        'b2_incredibly_kid_friendly_dogs',
        'a2_good_for_novice_owners'
    ]
    return [c for c in criticals if c not in params]

def generate_question(param_key):
    questions = {
        'a1_adapts_well_to_apartment_living': ("איפה הכלב יגור?", ["דירה קטנה", "דירה בינונית", "בית עם חצר", "אין לי העדפה"]),
        'a4_tolerates_being_alone': ("כמה שעות הכלב יהיה לבד ביום?", ["מעט מאוד", "חצי יום", "יום שלם", "אין לי העדפה"]),
        'b2_incredibly_kid_friendly_dogs': ("האם יש ילדים או חיות בבית?", ["כן, ילדים קטנים", "ילדים גדולים", "רק מבוגרים", "אין לי העדפה"]),
        'a2_good_for_novice_owners': ("מה רמת הניסיון שלך עם כלבים?", ["גידלתי בעבר", "פעם ראשונה", "אין לי העדפה"])
    }
    return questions.get(param_key, ("חסר לי קצת מידע, להמשיך לתוצאות?", ["כן", "אין לי העדפה"]))

@app.route('/api/button_click', methods=['POST'])
def button_click():
    data = request.json
    selection = data.get('selection')
    
    if selection == "אין לי העדפה":
        session['no_preference_count'] = session.get('no_preference_count', 0) + 1
        
    # Treat as normal chat input to let NLP map the button text to param values
    return chat()

def process_recommendation(selects, text_params):
    rec = recommend_dogs(selects, text_params)
    session.clear() # Reset for next
    
    if "error" in rec:
        return jsonify({"response": rec["error"]})
        
    return jsonify({
        "type": "result",
        "match_type": rec["type"],
        "dogs": rec.get("dogs", []),
        "score": rec.get("score")
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)
