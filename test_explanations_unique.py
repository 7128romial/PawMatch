"""
Regression: two dogs of the SAME breed used to collapse to one shared explanation
(the explanation_map was keyed by breed). Now each dog must get its own distinct
match_reason, mapped by a unique id.
"""
from dotenv import load_dotenv
load_dotenv()
from nlp_agent import generate_explanations

passed = failed = 0
def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1; print(f"  [PASS] {name}")
    else:
        failed += 1; print(f"  [FAIL] {name} {detail}")

# Two whippets, same breed/traits but distinct individuals.
dogs = [
    {"name": "ברק", "breed": "whippet", "age_years": 7, "weight_kg": 7, "color": "מנומר",
     "match_score": 98, "cluster": 1,
     "a1_adapts_well_to_apartment_living": 5, "a4_tolerates_being_alone": 3,
     "d1_easy_to_train": 4, "e3_exercise_needs": 5},
    {"name": "לונה", "breed": "whippet", "age_years": 4, "weight_kg": 13, "color": "Blue",
     "match_score": 98, "cluster": 1,
     "a1_adapts_well_to_apartment_living": 5, "a4_tolerates_being_alone": 3,
     "d1_easy_to_train": 4, "e3_exercise_needs": 5},
]
user_params = {"a1_adapts_well_to_apartment_living": 5, "c1_amount_of_shedding": 1}
user_text = "אני גרה בדירה, אלרגית לשיער, יש לי ילדים קטנים"

exps = generate_explanations(dogs, user_params, user_original_text=user_text, lang='he')
print(f"  Got {len(exps)} explanations")
for e in exps:
    print(f"   - id={e.get('id')} name={e.get('name')}: {e.get('match_reason')}")

check("one explanation per dog", len(exps) == 2, f"-> got {len(exps)}")
ids = [e.get("id") for e in exps if isinstance(e, dict)]
check("ids are unique and present", sorted(ids) == [0, 1], f"-> ids={ids}")
reasons = [e.get("match_reason", "") for e in exps]
check("match_reason texts are DISTINCT", len(set(reasons)) == len(reasons), f"-> {reasons}")

print(f"\n=== {passed} passed, {failed} failed ===")
