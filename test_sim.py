import os
from dotenv import load_dotenv
load_dotenv()
from nlp_agent import analyze_user_input

def run_test(scenario, text, f, current_params=None):
    if current_params is None: current_params = {}
    f.write(f"\n--- תרחיש: {scenario} ---\n")
    f.write(f"משתמש: {text}\n")
    res = analyze_user_input(text, current_params, lang='he')
    f.write(f"סטטוס שחזר: {res.get('state')}\n")
    f.write(f"פרמטרים שחולצו: {res.get('extracted_parameters')}\n")
    f.write(f"תגובת האג'נט: {res.get('next_question')}\n")

with open('sim_results.txt', 'w', encoding='utf-8') as f:
    run_test("סתירה (דירה קטנה וכלב ענק)", "אני גר בדירת סטודיו של 20 מטר, מחפש כלב ענק שצריך לרוץ המון אבל אין לי כוח לטייל איתו כמעט.", f)
    run_test("מחוץ לתחום (Out of Scope)", "תגיד, איזה סוג של אוכל לחתולים אתה ממליץ לקנות לדעתך?", f)
    run_test("זרימה תקינה ומידע חלקי", "אני גר בבית פרטי עם חצר, אני אוהב לרוץ בחוץ אז הכלב ירוץ איתי כל יום. אין ילדים.", f)
