"""
Regression for the screenshot bug: a combined "hours alone AND exercise" question
let "2 hours alone" leak into e3 (exercise), so the mandatory exercise question was
skipped. Now Tier A is asked one trait at a time and a time-alone answer must NOT
fill exercise.
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

# Active param is a4 (time alone). a1 already known; e3 and d5 still missing.
print("--- 'שעתיים לבד' while asking about time-alone: must NOT fill exercise ---")
res = analyze_user_input(
    user_text="הוא ישאר שעתיים לבד",
    current_params={"a1_adapts_well_to_apartment_living": 5},
    active_param="a4_tolerates_being_alone",
    lang='he',
    retry_count=0,
    chat_history=[{"role": "assistant",
                   "content": "כמה שעות בערך הכלב יישאר לבד בבית ביום ממוצע?"}],
)
params = res.get("extracted_parameters", {})
print(f"  Extracted: {params}")
check("a4 (time alone) extracted", "a4_tolerates_being_alone" in params)
check("e3 (exercise) NOT contaminated", "e3_exercise_needs" not in params,
      f"-> e3 wrongly set to {params.get('e3_exercise_needs')}")

# Control: when actually asked about exercise, a real exercise answer fills e3.
print("\n--- control: a real exercise answer fills e3 ---")
res2 = analyze_user_input(
    user_text="אני יכולה לטייל איתו שעה בבוקר ושעה בערב",
    current_params={"a1_adapts_well_to_apartment_living": 5, "a4_tolerates_being_alone": 1},
    active_param="e3_exercise_needs",
    lang='he',
    retry_count=0,
    chat_history=[{"role": "assistant",
                   "content": "כמה פעילות גופנית או טיולים תוכלי להעניק לכלב ביום?"}],
)
params2 = res2.get("extracted_parameters", {})
print(f"  Extracted: {params2}")
check("e3 extracted as high (4-5)", params2.get("e3_exercise_needs") in (4, 5),
      f"-> got {params2.get('e3_exercise_needs')}")

print(f"\n=== {passed} passed, {failed} failed ===")
