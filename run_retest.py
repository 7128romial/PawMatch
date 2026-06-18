# -*- coding: utf-8 -*-
"""End-to-end re-test harness for PawMatch.
Drives the real /api/chat & /api/button_click routes via Flask's test_client
(real OpenAI calls) and checks the two recently-fixed behaviors:
  1. The chat does NOT re-ask a Tier B trait the user already volunteered.
  2. The Isolation Forest anomaly warning is injected into match_reason.
Run:  python run_retest.py
"""
import sys
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
from app import app
import ml_engine as m

client = app.test_client()
ANOMALY = "פרופיל התנהגותי ייחודי"


def post(path, payload):
    return client.post(path, json=payload).get_json()


def show(tag, data):
    print(f"\n[{tag}]")
    resp = (data.get("response") or "").strip()
    if resp:
        print("  BOT:", resp[:400])
    if data.get("options"):
        print("  options:", data["options"])
    if "dogs" in data:
        print(f"  >>> {len(data['dogs'])} DOGS RETURNED:")
        for d in data["dogs"]:
            print(f"     - {d.get('breed')} | score {d.get('match_score')} | "
                  f"cluster {d.get('cluster')} | is_anomaly {d.get('is_anomaly')}")
            mr = (d.get("match_reason") or "").replace("\n", " ")
            print(f"       match_reason: {mr[:280]}")
    return data


def buttons(selections):
    d = None
    for s in selections:
        d = post("/api/button_click", {"selection": s, "lang": "he"})
    return d


def scenario_1():
    print("=" * 72)
    print("SCENARIO 1 — full path; must NOT re-ask experience, must reach results")
    print("=" * 72)
    client.post("/api/reset")
    d = buttons(["בינוני", "בוגר", "אין לי העדפה", "אין לי העדפה"])
    show("after physical filters (welcome)", d)

    questions = []
    d = post("/api/chat", {"message": "אני גרה בדירה קטנה בלי חצר, עובדת מהבית רוב הזמן, "
                                      "אוהבת טיולים קצרים ורגועים, ואין לי ניסיון קודם עם כלבים.",
                           "lang": "he"})
    show("after rich free-text", d)
    if "dogs" not in d:
        questions.append(d.get("response", ""))

    if "dogs" not in d:
        d = post("/api/chat", {"message": "שיהיה שקט", "lang": "he"})
        show("after 'שיהיה שקט' (bark answer)", d)
        if "dogs" not in d:
            questions.append(d.get("response", ""))

    # force results if it is still asking soft questions
    if "dogs" not in d:
        d = post("/api/chat", {"message": "", "skip": True, "lang": "he"})
        show("after skip -> results", d)

    reasked = any(("ראשון" in q) or ("ניסיון" in q) for q in questions)
    reached = bool(d and "dogs" in d and len(d["dogs"]) > 0)
    print("\n  CHECK no re-ask of first-dog/experience:",
          "FAIL (re-asked!)" if reasked else "PASS")
    print("  CHECK reached results (>=1 dog):", "PASS" if reached else "FAIL")
    return (not reasked) and reached


def scenario_3():
    print("\n" + "=" * 72)
    print("SCENARIO 3 — user says 'I already have a dog'; must NOT ask 'first dog?'")
    print("=" * 72)
    client.post("/api/reset")
    buttons(["אין לי העדפה", "אין לי העדפה", "אין לי העדפה", "אין לי העדפה"])
    questions = []
    d = post("/api/chat", {"message": "חשוב לי שיהיה שקט כי אני אלרגית, ויש לי כבר כלב אחד בבית",
                           "lang": "he"})
    show("after 'allergic + already have a dog'", d)
    if "dogs" not in d:
        questions.append(d.get("response", ""))
    # one more natural turn then force results
    if "dogs" not in d:
        d = post("/api/chat", {"message": "כן הוא יכול להיות לבד כמה שעות", "lang": "he"})
        show("after alone answer", d)
        if "dogs" not in d:
            questions.append(d.get("response", ""))
    if "dogs" not in d:
        d = post("/api/chat", {"message": "", "skip": True, "lang": "he"})
        show("after skip -> results", d)
    reasked_first = any("ראשון" in q for q in questions)
    print("\n  questions asked:", [q[:120] for q in questions])
    print("  CHECK did NOT ask 'first dog' after user said they own a dog:",
          "FAIL (asked!)" if reasked_first else "PASS")
    return not reasked_first


def scenario_2_direct():
    print("\n" + "=" * 72)
    print("SCENARIO 2a — anomaly flag flows through ml_engine (deterministic)")
    print("=" * 72)
    rec = m.recommend_dogs(selects={}, text_params={"breed_preference": "Basenji"}, lang="he")
    dogs = rec.get("dogs", [])
    print(f"  {len(dogs)} dogs for breed_preference=Basenji")
    flagged = [d for d in dogs if d.get("is_anomaly") == -1 or d.get("cluster") == 4]
    for d in dogs:
        print(f"     - {d.get('breed')} | cluster {d.get('cluster')} | is_anomaly {d.get('is_anomaly')}")
    ok = len(dogs) > 0 and len(flagged) > 0
    print("  CHECK at least one returned dog is flagged anomalous:", "PASS" if ok else "FAIL")
    return ok


def scenario_2_e2e():
    print("\n" + "=" * 72)
    print("SCENARIO 2b — anomaly WARNING injected into match_reason (end-to-end)")
    print("=" * 72)
    client.post("/api/reset")
    buttons(["אין לי העדפה", "אין לי העדפה", "אין לי העדפה", "אין לי העדפה"])
    post("/api/chat", {"message": "אני רוצה כלב מגזע Basenji", "lang": "he"})
    d = post("/api/chat", {"message": "", "skip": True, "lang": "he"})
    show("Basenji results", d)
    has_warn = bool(d and "dogs" in d and any(ANOMALY in (dog.get("match_reason") or "") for dog in d["dogs"]))
    print("\n  CHECK anomaly warning text present in a match_reason:",
          "PASS" if has_warn else "FAIL (no warning — maybe Basenji not in results)")
    return has_warn


if __name__ == "__main__":
    results = {
        "1 - no re-ask + results": scenario_1(),
        "3 - owns a dog -> no 'first dog?'": scenario_3(),
        "2a - anomaly flag (ml)": scenario_2_direct(),
        "2b - anomaly warning (e2e)": scenario_2_e2e(),
    }
    print("\n" + "=" * 72)
    print("SUMMARY")
    print("=" * 72)
    for name, ok in results.items():
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
    sys.exit(0 if all(results.values()) else 1)
