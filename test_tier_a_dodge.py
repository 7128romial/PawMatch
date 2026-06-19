"""
Regression for the homeless-user bug: when a user cannot answer a mandatory Tier A
question (e.g. "I don't have an apartment" twice), the anti-loop must neutralize ONLY
that one trait and move on to the NEXT mandatory question — not force-fill all of
Tier A and skip straight to the optional Tier B questions.
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

# Post-welcome, a1 still missing, and the user has ALREADY dodged the living question
# once (param_retry_count=1). This message is the SECOND dodge.
with client.session_transaction() as sess:
    sess['text_params'] = {'size': 'Medium', 'age_group': 'Adult', 'sex': 'Male', 'color': 'Black',
                           'welcome_done': True}
    sess['state'] = 'step_4_essential'
    sess['lang'] = 'he'
    sess['param_retry_count'] = 1
    sess['chat_history'] = []

resp = client.post('/api/chat', json={'message': 'אין לי', 'lang': 'he'})
data = resp.get_json()
q = data.get('response', '')
sd = data.get('session_data', {})
state = sd.get('state')
params = sd.get('text_params', {})
print(f"  state: {state}")
print(f"  a1={params.get('a1_adapts_well_to_apartment_living')} e3={params.get('e3_exercise_needs')} "
      f"a4={params.get('a4_tolerates_being_alone')} d5={params.get('d5_tendency_to_bark_or_howl')}")
print(f"  Q: {q}")

tier_a_topics = ['פעילות', 'טיול', 'לבד', 'נביח', 'שקט']
tier_b_topics = ['נשירת', 'אלרגי', 'כלבים נוספים', 'ילדים', 'אילוף', 'ניסיון']

check("only a1 was neutralized to 3", params.get('a1_adapts_well_to_apartment_living') == 3,
      f"-> a1={params.get('a1_adapts_well_to_apartment_living')}")
check("other Tier A traits NOT force-filled",
      not all(params.get(p) is not None for p in
              ['e3_exercise_needs', 'a4_tolerates_being_alone', 'd5_tendency_to_bark_or_howl']),
      f"-> e3={params.get('e3_exercise_needs')} a4={params.get('a4_tolerates_being_alone')} d5={params.get('d5_tendency_to_bark_or_howl')}")
check("still collecting mandatory Tier A", state == 'step_4_essential', f"-> {state}")
check("asks the NEXT mandatory question, not Tier B",
      any(t in q for t in tier_a_topics) and not any(t in q for t in tier_b_topics), f"-> {q}")

print(f"\n=== {passed} passed, {failed} failed ===")
