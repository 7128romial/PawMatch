"""
Regression test for the "כן to a disjunctive question" bug (see screenshot).
The agent used to ask "X או Y?" then fail to map a bare "כן" to a single value.
After the fix:
  - A bare "כן" to a disjunctive question must NOT extract a value, and the
    next_question must be a single-direction (non "או") corrective question.
  - A concrete number answer must still extract a value (control case).
"""
import json
from dotenv import load_dotenv
load_dotenv()

from nlp_agent import analyze_user_input

passed = 0
failed = 0

def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  [PASS] {name}")
    else:
        failed += 1
        print(f"  [FAIL] {name} {detail}")


# --- Test 1: bare "כן" to a disjunctive question (the screenshot bug) ---
print("--- Test 1: 'כן' to a disjunctive (X או Y) question ---")
chat_history = [
    {"role": "assistant", "content": "האם יש לך אפשרות להעסיק מישהו שיוציא את הכלב לטיולים במהלך היום, או שאתה מתכנן להיות בבית רוב הזמן?"},
]
res = analyze_user_input(
    user_text="כן",
    current_params={"a1_adapts_well_to_apartment_living": 5},
    active_param="a4_tolerates_being_alone",
    lang='he',
    retry_count=0,
    chat_history=chat_history,
)
params = res.get("extracted_parameters", {})
nq = res.get("next_question", "")
print(f"  Extracted: {params}")
print(f"  Next Q:    {nq}")
check("a4 NOT extracted from ambiguous 'כן'", "a4_tolerates_being_alone" not in params,
      f"-> got {params.get('a4_tolerates_being_alone')}")
check("corrective question is single-direction (no 'או')", " או " not in f" {nq} ",
      f"-> question still disjunctive")


# --- Test 2 (control): concrete number must still extract ---
print("\n--- Test 2 (control): concrete number answer extracts ---")
res2 = analyze_user_input(
    user_text="בערך 9 שעות",
    current_params={"a1_adapts_well_to_apartment_living": 5},
    active_param="a4_tolerates_being_alone",
    lang='he',
    retry_count=0,
    chat_history=[{"role": "assistant", "content": "כמה שעות בערך הכלב יישאר לבד בבית ביום ממוצע?"}],
)
params2 = res2.get("extracted_parameters", {})
print(f"  Extracted: {params2}")
print(f"  Next Q:    {res2.get('next_question')}")
val = params2.get("a4_tolerates_being_alone")
check("a4 extracted as high (4-5) for 9 hours alone", val in (4, 5), f"-> got {val}")


print(f"\n=== {passed} passed, {failed} failed ===")
