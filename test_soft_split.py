"""
Verifies the optional Tier B ("soft") question is split across two messages
instead of dumping all 5 topics at once. Pure-function test, no API calls.
"""
from app import get_next_question_and_options

passed = failed = 0
def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1; print(f"  [PASS] {name}")
    else:
        failed += 1; print(f"  [FAIL] {name} {detail}")

# Base profile: all physical filters + Tier A done, nothing in Tier B yet.
base = {
    "size": "Medium", "age_group": "Adult", "sex": "Male", "color": "Mixed",
    "welcome_done": True,
    "a1_adapts_well_to_apartment_living": 4,
    "e3_exercise_needs": 3,
    "a4_tolerates_being_alone": 4,
    "d5_tendency_to_bark_or_howl": 2,
}

print("--- Round 1 (soft_round=0): should ask only the first half ---")
p = dict(base)  # soft_round absent -> treated as 0
q, opts, state = get_next_question_and_options(p, 'he')
print(f"  Q: {q}")
check("state is step_5_soft", state == 'step_5_soft', f"-> {state}")
check("asks about shedding/allergies", "נשירת פרווה" in q)
check("asks about other dogs", "כלבים נוספים" in q)
check("asks about kids", "ילדים קטנים" in q)
check("does NOT ask about training yet", "קל לאילוף" not in q)
check("does NOT ask about experience yet", "ניסיון קודם" not in q)

print("\n--- Round 2 (soft_round=1): asks ONLY the second half, never re-asks round 1 ---")
# Reproduces the screenshot: in round 1 the user answered ONLY the allergy (c1),
# leaving b3 (other dogs) and b2 (kids) unanswered. Round 2 must NOT re-ask those.
p2 = dict(base)
p2.update({"c1_amount_of_shedding": 1})  # only the allergy was answered
p2["soft_round"] = 1
q2, opts2, state2 = get_next_question_and_options(p2, 'he')
print(f"  Q: {q2}")
check("state is step_5_soft", state2 == 'step_5_soft', f"-> {state2}")
check("asks about training", "קל לאילוף" in q2)
check("asks about experience", "ניסיון קודם" in q2)
check("does NOT re-ask about other dogs", "כלבים נוספים" not in q2)
check("does NOT re-ask about kids", "ילדים קטנים" not in q2)
check("uses the 'final question' intro", "ולסיום" in q2, f"-> {q2[:30]}")

print("\n--- After round 2 (soft_round=2): no more soft, go to results ---")
p3 = dict(base)
p3["soft_round"] = 2
q3, opts3, state3 = get_next_question_and_options(p3, 'he')
check("no soft question, state is state_q", state3 == 'state_q', f"-> {state3}")

print("\n--- Edge: all Tier B answered after round 1 -> straight to results ---")
p4 = dict(base)
p4.update({"c1_amount_of_shedding": 2, "b3_dog_friendly": 5, "b2_incredibly_kid_friendly_dogs": 1,
           "d1_easy_to_train": 4, "a2_good_for_novice_owners": 5, "soft_round": 1})
q4, opts4, state4 = get_next_question_and_options(p4, 'he')
check("no needless second soft, state is state_q", state4 == 'state_q', f"-> {state4}")

print(f"\n=== {passed} passed, {failed} failed ===")
