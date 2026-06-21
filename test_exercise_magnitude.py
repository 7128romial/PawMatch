"""
Regression for the "repeated question" bug (see screenshot): a clear magnitude
answer to the exercise question ("כל היום") was NOT extracted into e3, so the
backend kept re-asking the identical e3 question. Worse, "כל היום" was sometimes
misread as a wish for a calm/relaxed dog.

After the fix, magnitude/duration answers to the exercise question map to e3:
  - "all day" / "a lot" -> HIGH (4-5), never a low/relaxed value
  - "a little" -> LOW (2-3)
and e3 is ALWAYS extracted so the conversation advances instead of looping.
"""
from dotenv import load_dotenv
load_dotenv()
from nlp_agent import analyze_user_input

passed = failed = 0
def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1; print(f"  [PASS] {name}")
    else:
        failed += 1; print(f"  [FAIL] {name} {detail}")

E3_Q = "כמה זמן ביום בא לכם להקדיש לטיולים ולשחרור אנרגיה עם הכלב?"

def ask(text):
    return analyze_user_input(
        user_text=text,
        current_params={"a1_adapts_well_to_apartment_living": 5},
        active_param="e3_exercise_needs",
        lang='he',
        retry_count=0,
        chat_history=[{"role": "assistant", "content": E3_Q}],
    ).get("extracted_parameters", {})

# --- The exact screenshot answer: "כל היום" ---
print("--- 'כל היום' to the exercise question ---")
p = ask("כל היום")
print(f"  Extracted: {p}")
val = p.get("e3_exercise_needs")
check("e3 IS extracted (no re-ask loop)", val is not None, "-> e3 omitted, backend would repeat the question")
check("e3 is HIGH (4-5), not misread as 'relaxed'", val in (4, 5), f"-> got {val}")

# --- 'a little' must map LOW ---
print("\n--- 'מעט' to the exercise question ---")
p2 = ask("מעט")
print(f"  Extracted: {p2}")
val2 = p2.get("e3_exercise_needs")
check("e3 IS extracted", val2 is not None)
check("e3 is LOW (2-3)", val2 in (2, 3), f"-> got {val2}")

print(f"\n=== {passed} passed, {failed} failed ===")
