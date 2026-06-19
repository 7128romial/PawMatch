"""
Flow-level regression for the screenshot bug: after the welcome answer the agent
jumped straight to an optional Tier B question (kids / other pets), skipping the
mandatory Tier A questions. While any Tier A trait is missing, the question shown
must be the backend's focused Tier A question, never the LLM's jump-ahead.
"""
from dotenv import load_dotenv
load_dotenv()
from app import app

passed = failed = 0
def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1; print(f"  [PASS] {name}")
    else:
        failed += 1; print(f"  [FAIL] {name} {detail}")

app.config['TESTING'] = True
client = app.test_client()

# Post-welcome state: physical filters done, a1 (apartment) known, Tier A e3/a4/d5 missing.
with client.session_transaction() as sess:
    sess['text_params'] = {
        'size': 'Medium', 'age_group': 'Adult', 'sex': 'Male', 'color': 'Mixed',
        'welcome_done': True,
        'a1_adapts_well_to_apartment_living': 5,
    }
    sess['state'] = 'step_4_essential'
    sess['lang'] = 'he'
    sess['chat_history'] = []

resp = client.post('/api/chat', json={'message': 'אני גרה בדירה', 'lang': 'he'})
data = resp.get_json()
q = data.get('response', '')
state = data.get('session_data', {}).get('state')
print(f"  Next state: {state}")
print(f"  Q: {q}")

tier_a_topics = ['פעילות', 'טיול', 'לבד', 'נביח', 'רעש']  # exercise / alone / barking
tier_b_topics = ['ילדים', 'חיות מחמד', 'אלרגי', 'אילוף', 'ניסיון']

check("stays in mandatory Tier A state", state == 'step_4_essential', f"-> {state}")
check("asks a mandatory Tier A topic", any(t in q for t in tier_a_topics), f"-> {q}")
check("does NOT jump to an optional Tier B topic", not any(t in q for t in tier_b_topics), f"-> {q}")

print(f"\n=== {passed} passed, {failed} failed ===")
