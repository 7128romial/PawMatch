"""
Regression for the out-of-scope guardrail (see screenshot): the user asked about
the weather / a pasta recipe / how to treat a cat, and the bot silently ignored it
and just asked the next trait question. Off-topic messages must map to state_a (the
backend then politely declines and steers back), even when they are very short
("מה השעה?"). A genuine lifestyle description must NOT be treated as out of scope.
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

HIST = [{"role": "assistant", "content": "ספר/י לי על אורח החיים שלך. איפה אתם גרים?"}]
def state_of(text):
    return analyze_user_input(
        user_text=text, current_params={},
        active_param="a1_adapts_well_to_apartment_living",
        lang='he', retry_count=0, chat_history=HIST)

print("--- off-topic messages must be state_a (decline + steer back) ---")
OFF = [
    "מה השעה?",
    "מה המזג אוויר בלונדון?",
    "תכתוב לי קוד בפייתון",
    "איך מטפלים בחתול סיאמי?",
    "תגיד, מה המזג אוויר עכשיו בלונדון? ואתה יכול לכתוב לי מתכון לפסטה שמנת פטריות או לספר איך מטפלים בחתול סיאמי",
]
for t in OFF:
    r = state_of(t)
    check(f"state_a for {t[:30]!r}", r.get("state") == "state_a",
          f"-> got {r.get('state')}")

print("\n--- genuine lifestyle must NOT be out of scope, and still extracts ---")
r1 = state_of("אני גר בדירה")
check("apartment description is not state_a", r1.get("state") != "state_a", f"-> {r1.get('state')}")
check("a1 extracted from apartment description",
      r1.get("extracted_parameters", {}).get("a1_adapts_well_to_apartment_living") == 5)

print(f"\n=== {passed} passed, {failed} failed ===")
