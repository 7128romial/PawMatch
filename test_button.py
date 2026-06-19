from app import app, chat
from flask import request

with app.test_request_context('/api/button_click', json={
    "selection": "הצג תוצאות עכשיו",
    "lang": "he",
    "session_data": {
        "text_params": {
            "size": "Medium",
            "a1_adapts_well_to_apartment_living": 4,
            "e3_exercise_needs": 3
        },
        "state": "step_5_soft",
        "no_preference_count": 0,
        "state_b_count": 0
    }
}):
    # Simulate button_click()
    data = request.json or {}
    selection = data.get('selection')
    data['message'] = selection
    # Run chat()
    response = chat()
    print("Status:", response.status_code)
    print("Data:", response.get_data(as_text=True))
