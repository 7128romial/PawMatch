"""
Deterministic gibberish guard (app.looks_like_gibberish).

The user typed keyboard mash ("עדגגעשגכעגכעגשכע") and the bot silently advanced to
the next question instead of saying it didn't understand. The backend now detects
clearly unintelligible input (symbol-only, or a long low-variety single token) and
asks the user to rephrase. This runs without any API call, so it is fast and reliable.
The guard must be conservative: it must NEVER fire on a real short answer.
"""
from app import looks_like_gibberish as g

passed = failed = 0
def check(text, expected):
    global passed, failed
    got = g(text)
    if got == expected:
        passed += 1; print(f"  [PASS] {text!r} -> {got}")
    else:
        failed += 1; print(f"  [FAIL] {text!r} -> {got} (want {expected})")

print("--- gibberish / unintelligible: must be True ---")
for t in ["עדגגעשגכעגכעגשכע", "asdkjhaskjdh", "כגכגכגכג", "שדגשדגשדג",
          "...", "???", "!!!", "חחחחחחחח", "aaaaaaaa"]:
    check(t, True)

print("\n--- real input: must be False (no false positives) ---")
for t in ["דירה", "בית", "בית עם חצר", "אני גר בדירה", "כל היום", "8", "שלום",
          "apartment", "I live in an apartment", "אוניברסיטה", "אינטרנט",
          "קטן", "אין לי העדפה", "הצג תוצאות עכשיו", "לא יודע", "שעתיים", ""]:
    check(t, False)

print(f"\n=== {passed} passed, {failed} failed ===")
