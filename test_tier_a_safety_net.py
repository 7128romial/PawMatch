"""
Deterministic safety net for the mandatory Tier A traits (app._deterministic_tier_a).

The LLM occasionally fails to extract a clear answer (e.g. "כל היום" repeated across
two turns confuses it via the chat history), which made the backend re-ask the IDENTICAL
question. This net maps a recognizable answer to a 1/5 value for the ACTIVE trait so the
conversation always advances. It runs without any API call, so this test is fast and
non-flaky — it is the reliable backstop behind the probabilistic LLM extraction.
"""
from app import _deterministic_tier_a as f

passed = failed = 0
def check(param, text, expected):
    global passed, failed
    got = f(param, text)
    if got == expected:
        passed += 1; print(f"  [PASS] {param.split('_')[0]:3} {text!r} -> {got}")
    else:
        failed += 1; print(f"  [FAIL] {param.split('_')[0]:3} {text!r} -> {got} (want {expected})")

A1, E3, A4, D5 = ('a1_adapts_well_to_apartment_living', 'e3_exercise_needs',
                  'a4_tolerates_being_alone', 'd5_tendency_to_bark_or_howl')

print("--- the screenshot bug: 'כל היום' maps per-trait, never loops ---")
check(E3, "כל היום", 5)   # plenty of time for walks
check(A4, "כל היום", 5)   # alone all day

print("\n--- negation beats substring (longest-match wins) ---")
check(A4, "לא בבית", 5)   # owner away  -> high, must NOT be dragged low by 'בבית'
check(A4, "אני בבית", 1)  # owner home  -> low
check(A1, "אין לי חצר", 5)  # no yard   -> apartment-suited, not dragged low by 'חצר'

print("\n--- schedule / magnitude / no-time answers ---")
check(A4, "אני בעבודה", 5)
check(A4, "עובד מהבית", 1)
check(E3, "אין לי זמן", 1)
check(E3, "המון", 5)
check(A1, "דירה", 5)
check(A1, "וילה", 1)
check(D5, "צריך שקט", 1)
check(D5, "לא אכפת לי", 5)

print("\n--- genuine evasions stay unmapped (None) so retry/neutralize handles them ---")
check(A4, "לא יודע", None)
check(E3, "תלוי", None)
check(D5, "לא משנה", None)
check(E3, "", None)

print(f"\n=== {passed} passed, {failed} failed ===")
