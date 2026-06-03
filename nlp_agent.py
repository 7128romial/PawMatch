import os
from openai import OpenAI
import json

# Expecting OPENAI_API_KEY to be set in environment
api_key = os.getenv("OPENAI_API_KEY")
if api_key and api_key != "your_api_key_here":
    client = OpenAI(api_key=api_key)
else:
    client = None

def analyze_user_input(user_text, current_params=None, active_param=None, lang='he'):
    if current_params is None:
        current_params = {}
        
    system_prompt_he = """
אתה עוזר וירטואלי של חברת PawMatch. המטרה היחידה שלך היא לאסוף פרטים מהמשתמש כדי להתאים לו את הכלב המושלם לאימוץ.

# חוקי ברזל (Guardrails):
1. אסור לך לענות על שאלות כלליות, אסור לך לתת ייעוץ רפואי או וטרינרי, ואסור לך להמציא מידע.
2. אם המשתמש שואל משהו שלא קשור לאימוץ כלבים, ענה בקצרה, החזר אותו בנימוס לנושא, וסווג את המצב כ-state_a.
3. אם המשתמש מביע מניע שאינו אחראי או אינו אתי לאימוץ (למשל אימוץ מתוך שעמום, רצון בצעצוע זמני), סווג את המצב כ-state_e.
4. שאל תמיד רק שאלה אחת בכל פעם ואל תציף את המשתמש בשאלות.

# שלבי הפעולה (Step-by-step Process):
אסוף את הפרטים הבאים בהדרגה מתוך הטקסט של המשתמש:
- סביבת מגורים (a1_adapts_well_to_apartment_living: דירה קטנה/בלי חצר=5, דירה בינונית/מרפסת=4, בית עם חצר=2, חצר גדולה=1)
- שעות לבד ביום (a4_tolerates_being_alone: יום שלם/מעל 8 שעות=5, חצי יום=3, מעט מאוד/עובד מהבית=1)
- ידידותיות לילדים (b2_incredibly_kid_friendly_dogs: ילדים קטנים/תינוקות=5, ילדים גדולים=4, רק מבוגרים/אין ילדים=1)
- רמת ניסיון (a2_good_for_novice_owners: כלב ראשון/אין ניסיון=5, בעל ניסיון/גידלתי בעבר=1)
- צרכי ספורט ופעילות (e3_exercise_needs: המון ספורט/רץ מרתון=5, מעט פעילות/בטטת כורסה=1)
- נטייה לנבוח (d5_tendency_to_bark_or_howl: רגיש לרעש/שלא ינבח=1, כלב שמירה=5)
- אלרגיות/נשירה (c1_amount_of_shedding: אלרגי לשיער/ללא נשירה=1, לא מפריע לי נשירה=5)
- ידידותיות לכלבים אחרים (b3_dog_friendly: יש לי עוד כלבים=5)

* שים לב: אם המשתמש שולל דברים (למשל "אין לי ילדים"), מפה את זה לערך המתאים (רק מבוגרים = 1). אם המשתמש עונה בחיוב או בשלילה קצרה ("כן", "לא", "אין לי") - התייחס לפרמטר שעליו הוא נשאל כרגע (Active Parameter).

# אופן הפלט (Output Format):
השתמש תמיד ב-Tool (הפונקציה) `extract_dog_preferences` שסופק לך כדי לשמור את הנתונים. 
אל תמציא ערכים - אם המשתמש לא סיפק נתון, השאר אותו ריק ואל תוסיף אותו לפלט.
אם חסרים עדיין פרטים קריטיים, סווג את המצב כ-state_b או state_c. אם כל הפרטים הקריטיים נאספו, סווג כ-state_d.
השתמש בשדה `next_question` בפונקציה כדי לשאול את השאלה הבאה מתוך רשימת הפרטים שטרם נאספו. נסח את השאלה באופן טבעי וקצר. אל תסיים את השיחה עד שכל שדות החובה מלאים.
"""

    system_prompt_en = """
You are a virtual assistant of PawMatch. Your sole goal is to collect details from the user to match them with the perfect dog for adoption.

# Guardrails:
1. You must not answer general questions, you must not give medical or veterinary advice, and you must not make up information.
2. If the user talks about topics unrelated to dog adoption, answer briefly, politely guide them back to the topic, and classify the state as state_a.
3. If the user expresses an unethical or irresponsible motive for adoption (e.g., temporary toy, boredom), classify the state as state_e.
4. Always ask only one question at a time and do not overwhelm the user with multiple questions.

# Step-by-step Process:
Gradually collect the following details from the user's text:
- Living environment (a1_adapts_well_to_apartment_living: small apt/no yard=5, medium apt/balcony=4, house with yard=2, big yard=1)
- Hours alone per day (a4_tolerates_being_alone: full day/8+ hours=5, half day=3, very few/work from home=1)
- Kid friendliness (b2_incredibly_kid_friendly_dogs: young kids/babies=5, older kids=4, adults only/no kids=1)
- Experience level (a2_good_for_novice_owners: first dog/no experience=5, experienced/raised before=1)
- Exercise needs (e3_exercise_needs: very active/runner=5, low activity/couch potato=1)
- Tendency to bark (d5_tendency_to_bark_or_howl: sensitive to noise/quiet dog=1, guard dog=5)
- Shedding/allergies (c1_amount_of_shedding: hypoallergenic/allergies=1, shedding doesn't matter=5)
- Friendly to other dogs (b3_dog_friendly: I have other dogs=5)

* Note: Pay attention to negations (e.g., "I don't have kids" -> adults only = 1). If the user replies with a short "yes", "no", or "none" - map it according to the currently active parameter they were asked about.

# Output Format:
Always use the provided `extract_dog_preferences` Tool/Function to save the data. 
Do not invent values - if the user didn't provide a data point, leave it out.
If critical details are still missing, classify as state_b or state_c. If all critical details are gathered, classify as state_d.
Use the `next_question` field in the function to naturally ask the next question about one of the missing details. Formulate the question in a natural, friendly tone. Do not end the conversation until all required fields are full.
"""

    system_prompt = system_prompt_he if lang == 'he' else system_prompt_en

    tools = [
        {
            "type": "function",
            "function": {
                "name": "extract_dog_preferences",
                "description": "Extracts dog preferences from user input, determines the conversation state, and asks the next question.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "state": {
                            "type": "string",
                            "enum": ["state_a", "state_b", "state_c", "state_d", "state_e"],
                            "description": "The conversation state. state_a=irrelevant, state_b=lacking essential info, state_c=partial info, state_d=full info, state_e=unethical motive."
                        },
                        "extracted_parameters": {
                            "type": "object",
                            "description": "The parameters extracted from the user's text.",
                            "properties": {
                                "a1_adapts_well_to_apartment_living": {"type": "integer"},
                                "a4_tolerates_being_alone": {"type": "integer"},
                                "b2_incredibly_kid_friendly_dogs": {"type": "integer"},
                                "a2_good_for_novice_owners": {"type": "integer"},
                                "sex": {"type": "string"},
                                "size": {"type": "string"},
                                "hair_length": {"type": "string"},
                                "color": {"type": "string"},
                                "breed_preference": {"type": "string"},
                                "e1_energy_level": {"type": "integer"},
                                "d1_easy_to_train": {"type": "integer"},
                                "b1_affectionate_with_family": {"type": "integer"},
                                "b3_dog_friendly": {"type": "integer"},
                                "c1_amount_of_shedding": {"type": "integer"},
                                "c2_drooling_potential": {"type": "integer"},
                                "d5_tendency_to_bark_or_howl": {"type": "integer"},
                                "e3_exercise_needs": {"type": "integer"}
                            }
                        },
                        "next_question": {
                            "type": "string",
                            "description": "The next question to ask the user to gather missing information. Formulate it naturally in the user's language."
                        }
                    },
                    "required": ["state", "extracted_parameters", "next_question"]
                }
            }
        }
    ]

    try:
        if client is None:
            raise Exception("OpenAI API key is missing or placeholder.")
            
        if lang == 'he':
            user_prompt = f"הנתונים שנאספו עד כה: {json.dumps(current_params)}\nהפרמטר שעליו המשתמש נשאל כרגע (Active Parameter): {active_param}\nקלט המשתמש הנוכחי: '{user_text}'"
        else:
            user_prompt = f"Data collected so far: {json.dumps(current_params)}\nCurrently asked parameter (Active Parameter): {active_param}\nCurrent user input: '{user_text}'"
            
        response = client.chat.completions.create(
            model="gpt-5.4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            tools=tools,
            tool_choice={"type": "function", "function": {"name": "extract_dog_preferences"}},
            temperature=0.0
        )
        
        tool_call = response.choices[0].message.tool_calls[0]
        arguments = tool_call.function.arguments
        result = json.loads(arguments)
        
        return result
    except Exception as e:
        print(f"OpenAI API Error: {e}")
        return {
            "state": "error",
            "extracted_parameters": {},
            "next_question": "אירעה שגיאה בחיבור, נסה שוב." if lang == 'he' else "An error occurred, please try again.",
            "error": str(e)
        }

def generate_explanations(dogs, user_params, lang='he'):
    dogs_info = []
    for d in dogs:
        dogs_info.append({
            "name": d.get("name"),
            "breed": d.get("breed"),
            "match_score": d.get("match_score"),
            "sex": d.get("sex"),
            "size": d.get("size"),
            "color": d.get("color"),
            "hair_length": d.get("hair_length"),
            "a1_adapts_well_to_apartment_living": d.get("a1_adapts_well_to_apartment_living"),
            "a4_tolerates_being_alone": d.get("a4_tolerates_being_alone"),
            "b2_incredibly_kid_friendly_dogs": d.get("b2_incredibly_kid_friendly_dogs"),
            "a2_good_for_novice_owners": d.get("a2_good_for_novice_owners")
        })
        
    system_prompt = f"""
You are a warm, professional dog adoption coordinator for PawMatch.
Write personalized explanations and breed descriptions for 5 recommended dogs.
Generate your response in JSON format. The response language must be strictly: {"Hebrew (עברית)" if lang == 'he' else "English"}.

Output JSON structure:
{{
  "explanations": [
    {{
      "name": "Dog_Name",
      "match_reason": "A 1-2 sentence explanation of why this specific dog is a match for the user's parameters. Reference the user's environment/needs (e.g. apartment, hours alone, kids, etc.).",
      "breed_info": "A 1-2 sentence description of the breed's general temperament, origins, and key characteristics."
    }}
  ]
}}
"""

    user_prompt = f"""
User parameters: {json.dumps(user_params)}
Recommended dogs data: {json.dumps(dogs_info)}
"""

    try:
        if client is None:
            raise Exception("OpenAI API key is missing or placeholder.")
        response = client.chat.completions.create(
            model="gpt-5.4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={ "type": "json_object" },
            temperature=0.7
        )
        result = json.loads(response.choices[0].message.content)
        return result.get("explanations", [])
    except Exception as e:
        print(f"OpenAI API Error in generate_explanations: {e}")
        return []

def answer_breed_question(user_question, recommended_breeds=None, lang='he'):
    if recommended_breeds is None:
        recommended_breeds = []
        
    breeds_str = ", ".join(recommended_breeds) if recommended_breeds else "none currently recommended"
    
    system_prompt = f"""
    You are a friendly, professional canine breed and care expert for PawMatch.
    Your goal is to answer user questions about dog breeds, behavior, care, training, or suitability.
    The user was recently recommended the following breeds: {breeds_str}.
    
    Guidelines:
    1. Answer the question in a warm, helpful, and expert tone.
    2. Keep your response relatively concise (2-4 sentences).
    3. If the question is completely unrelated to dogs, breeds, or pets, politely guide the user back to dog-related questions, or tell them they can click "Start Over" to begin a new match search.
    4. You must respond strictly in: {"Hebrew (עברית)" if lang == 'he' else "English"}.
    """
    
    try:
        if client is None:
            raise Exception("OpenAI API key is missing or placeholder.")
        response = client.chat.completions.create(
            model="gpt-5.4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_question}
            ],
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"OpenAI API Error in answer_breed_question: {e}")
        return "I'm sorry, I encountered an error while answering your question." if lang == 'en' else "מצטער, נתקלתי בשגיאה בעת מענה על השאלה שלך."
