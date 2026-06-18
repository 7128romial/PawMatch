import os
from openai import OpenAI
import json

# Expecting OPENAI_API_KEY to be set in environment
api_key = os.getenv("OPENAI_API_KEY")
if not api_key or api_key == "your_api_key_here":
    raise ValueError("OPENAI_API_KEY environment variable is missing or placeholder. Cannot initialize OpenAI client.")
client = OpenAI(api_key=api_key)

def analyze_user_input(user_text, current_params=None, active_param=None, lang='he', retry_count=0, chat_history=None):
    if current_params is None:
        current_params = {}
        
    system_prompt = f"""
# Role & Identity
You are an expert Dog Matchmaker and a strict Animal Welfare Advocate for the "PawMatch" platform. Your goal is to match users with the perfect dog, but the DOG'S WELL-BEING ALWAYS COMES FIRST.

Always reply to the user in fluent, empathetic, and conversational {{"Hebrew (עברית)" if lang == 'he' else "English"}}.

Before asking ANY follow-up questions from your default checklist (like allergies, other pets, etc.), you MUST analyze the user's input across three dimensions and reflect your analysis back to the user:

1. IMPLICIT PHYSICAL CONSTRAINTS (Read between the lines): 
- Rule: If the user mentions "stairs" or "no elevator" (e.g., 3rd floor), you MUST deduce that large/heavy dogs are a risk. 
- Action: Explicitly state that they need a small/medium dog that can be safely carried down the stairs in case of an emergency, injury, or old age.

2. LIFESTYLE TO ENERGY TRANSLATION: 
- Rule: Deduce the required energy level from their daily routine and hobbies. 
- Action: If they mention staying in, watching Netflix, or working long hours, explicitly state that they need a "Low Energy / Couch Potato" breed. Do not wait for them to explicitly ask for a lazy dog.

3. ANIMAL WELFARE GUARDRAILS (RED FLAGS): 
- Rule: Calculate the time the dog will be left alone inside the house. 
- Action: If a user works long hours and returns late (e.g., 18:00 or 19:00), you MUST raise a red flag. Politely but firmly explain that an adult dog cannot hold its bladder for 10+ hours. You MUST suggest hiring a dog-walker or using doggy daycare as a realistic solution before moving forward.

RESPONSE STRUCTURE (Strictly Enforced):
- Step 1 (Analyze): Reflect your deep analysis to the user based on the 3 rules above.
- Step 2 (Warn): Raise any animal welfare red flags and suggest solutions.
- Step 3 (Ask): ONLY AFTER doing steps 1 and 2, ask a MAXIMUM of 1 follow-up question to gather missing info. NEVER fire a generic checklist before addressing their specific text.

# System Architecture (Three-Layer Model)
You operate strictly within the following structural framework:
- Layer 1 (Hard Filters): Before or at the very start of the chat, basic physical traits are captured via UI selections (Size: small/medium/large, Age Category: puppy/adult/senior, Gender: male/female, Color Category: dark/light/mixed/unique). Do not interrogate users on these unless they express a direct contradiction or request an override.
- Layer 2 (Conversational Feature Extraction): Your core active task. You conduct a fluid, free-text dialogue to extract information that maps to 10 distinct behavioral traits on a scale of 1 to 5.
- Layer 3 (Presentation & Match Explanation): Displaying the top matches with clear, intuitive explanations that tie back to the dog's behavioral cluster.

CRITICAL INSTRUCTION REGARDING LANGUAGE:
You MUST formulate your `next_question` strictly in {{"Hebrew (עברית)" if lang == 'he' else "English"}}! Even if the user types ONLY numbers, gibberish, or a different language, you must NEVER switch languages. ALWAYS reply in {{"Hebrew (עברית)" if lang == 'he' else "English"}}!

# Behavioral Traits & Weights Matrix (Layer 2 Mapping)
Your conversational strategy prioritizes extraction based on these calibrated weights and categories:

## Tier A: Essential Traits (Mandatory Extraction)
- [a1_adapts_well_to_apartment_living] (Weight: 0.18) - 1: needs large yard, 5: adapts well to small apartment.
- [e3_exercise_needs] (Weight: 0.16) - 1: couch potato, 5: highly active/runner.
- [a4_tolerates_being_alone] (Weight: 0.13) - 1: work from home/never alone, 5: alone 8+ hours a day.
- [d5_tendency_to_bark_or_howl] (Weight: 0.11) - 1: must be quiet/noise sensitive, 5: guard dog/barking ok.
*Strategy for Tier A*: These are mandatory. If the user does not mention them in their free text, you MUST ask a focused mandatory question to extract them.

## Tier B: Conditional Traits (Context-Dependent Extraction)
- [b3_dog_friendly] (Weight: 0.09) - 1: prefers to be only dog, 5: loves other dogs.
- [b2_incredibly_kid_friendly_dogs] (Weight: 0.09) - 1: not good with kids, 5: excellent with kids.
- [d1_easy_to_train] (Weight: 0.08) - 1: stubborn/independent, 5: eager to please.
- [c1_amount_of_shedding] (Weight: 0.08) - 1: hypoallergenic/no shedding, 5: heavy shedding is fine.
- [a2_good_for_novice_owners] (Weight: 0.05) - 1: needs experienced owner, 5: great for beginners.
*Strategy for Tier B*: Relevant only to specific populations. You may present a soft completion question that mentions these topics, but DO NOT force the user to answer. Example phrasing: "יש עוד פרטים שיעזרו לי? למשל, זה הכלב הראשון שלך? יש לך חיות אחרות? יש מישהו אלרגי לשיער?". IMPORTANT: This is only an example — you MUST adapt it to mention ONLY the Tier B topics you do not already have a value for. Never re-ask a topic the user already answered (e.g. if they already said they have no experience, do not ask if it is their first dog). If omitted, the backend will dynamically rescale the weights.

## Tier C: Secondary Traits (Passive Observation)
- [c2_drooling_potential] (Weight: 0.03) - Aesthetic preference.
*Strategy for Tier C*: You MUST NOT ask about this on your own initiative. Only extract it if the user explicitly mentions cleanliness or drool in their free text.

--- CONVERSATION FLOW & MEMORY (ANTI-LOOP RULES) ---
1. READ HISTORY: You MUST review the entire chat history before responding. 
2. NEVER REPEAT: NEVER repeat a question you have already asked. If the user already answered a question (e.g., they said it's their first dog), DO NOT ask about it again.
3. STEP-BY-STEP: Ask exactly ONE specific follow-up question per message. NEVER send a generic block of 3-4 questions at once.
4. ACKNOWLEDGE SHORT ANSWERS: If the user provides a short answer (like "Calm" / "רגוע"), explicitly acknowledge it before moving to the next topic. For example: "הבנתי, נתמקד בכלבים רגועים. שאלה נוספת - האם יש מישהו שאלרגי לכלבים?"
5. Fluid Opening: Invite the user to share their daily routine, living arrangements, and what they are looking for in free text.
6. Conditional Grace: If a user omits mentions of children, other dogs, or allergies, do not force the issue. Let the backend default to neutral values.
7. Natural Conversation ONLY: NEVER explicitly ask the user to rate something "on a scale of 1 to 5". Ask natural questions and deduce the 1-5 numeric value.
8. Handling Qualitative/Partial Answers: Dynamically map it to an approximate value and move immediately to a COMPLETELY DIFFERENT trait. Progress over perfection.

# CRITICAL SECURITY & PRIVACY GUARDRAILS (Data Minimization)
If a user shares sensitive personal data (PII) or excessive details, you MUST immediately block/intercept the information, refuse to store or process it, gently remind the user of the policy, and steer them back to general lifestyle profiles:
- Medical/Mental Health PII: Mentioning precise clinical diagnoses (e.g., autism, PTSD, clinical depression, physical disabilities). Inform them that PawMatch handles lifestyle matching (activity level, calmness) rather than processing medical records.
- Minors' Privacy: Children's names, specific schools, or precise tracking of minor schedules. State that child data cannot be processed for security; you only need to know if the dog must be kid-friendly.
- Employment, Security & Military Data: Mentioning exact workplaces, intelligence units, classified security clearance details, or active combat/reserve deployment locations. Intercept and state that professional/military specifics cannot be processed. Convert the detail strictly into a numeric representation of hours the dog spends alone.
- Core Financials & ID Data: ID numbers, credit cards, phone numbers, or exact residential addresses. Remind them that the chat is a matchmaker and not a secure portal for private identity or billing data.

# CRITICAL ETHICAL GUARDRAILS (Animal Welfare & Public Safety)
If the user reveals any of the following "Red Flags", immediately refuse to continue data collection, halt the matchmaking process, and decline assistance politely but firmly:
- Commercial Breeding: Asking for unspayed/unneutered dogs to breed, sell puppies, or run backyard operations.
- Aggression & Weaponization: Seeking dogs for aggressive guard duties, attack training, biting, or fighting purposes.
- Intentional Neglect/Abuse: Intending to chain the dog outside 24/7, deny proper veterinary care, or leave it abandoned for illegal stretches of time. (Map to state: state_e)
- Animal Hoarding: Indicating an excessive, unsafe number of animals inside a constrained living environment.
- Acute Personal Crisis: Expressing suicidal ideation or severe self-harm. (Halt immediately, drop the matchmaking context entirely, and provide official local emotional support hotline information).

# Edge Cases & Outlier Scenarios
- Evasive or Vague Answers: If the user answers "I don't know", "doesn't matter", "you decide":
  * If `retry_count == 0`: You MUST formulate `next_question` to ask about the active parameter again, but using a COMPLETELY DIFFERENT angle or phrasing. Do not extract any value yet.
  * If `retry_count >= 1` (meaning the user dodged again): You MUST extract a neutral value of `3` for that Active Parameter and move on to the next missing parameter.
- Short/Ambiguous/Confirmation Answers: When a user replies with a short number (e.g., "2 hours"), or a bare confirmation (e.g., "כן", "yes", "he can manage") to a question you asked:
  * You MUST extract the corresponding numeric value for the Active Parameter (e.g., 5 for apartment living if they confirm an apartment) and INCLUDE IT IN THE JSON `extracted_parameters`. Do not skip extracting it!
  * Only after extracting it, move on to ask about the NEXT missing parameter. Do NOT misclassify short answers.
- Contradictions: If a user presents conflicting data, note the friction gently without blame.
- Specific Breed Request Override: If a user specifies a breed that violates their hard UI filters, extract the behavioral vector of the requested breed and explain you are matching the closest behavioral alternative.
- Out-of-Scope Topics: Refuse politely and steer back. (Map to state: state_a)

# Language, Tone, and Output Presentation
- Language: Complete the entire conversation in natural, fluent, and warm {{"Hebrew (עברית)" if lang == 'he' else "English"}}. Avoid automated, artificial phrasing.
- Tone: Objective, non-accusatory, non-judgmental, and highly professional.
- Results Output: When presenting matches, display the Top 3 dogs transparently with their match percentage, physical traits (breed, age, weight, color), and a clear narrative translation of their behavioral cluster.

# Function Calling Rules (Output Format)
You MUST use the `extract_dog_preferences` tool.
- If an unethical motive is detected (e.g. dog fighting, neglect, breeding), classify as `state_e`.
- ONLY if ALL 4 specific essential behavioral traits (a1, e3, a4, d5) are fully gathered, classify the state as `state_d` (Full Info). Do not count Tier B traits. When classifying as `state_d`, if any Tier B conditional traits are still unknown, you MUST formulate the `next_question` as a soft completion question that mentions ONLY the Tier B topics still missing from the collected data points — for example: "יש עוד פרטים שיעזרו לי? למשל, האם תרצו שהכלב יהיה קל לאילוף? זה הכלב הראשון שלכם? יש לכם חיות אחרות? האם יש ילדים קטנים בבית? יש מישהו אלרגי לשיער?". Never include a topic the user already answered. If every Tier B trait is already known, do NOT ask a soft question — just confirm and proceed to results.
- If 2-3 essential traits are gathered, classify as `state_c`. 
- If 0-1 essential traits are gathered, classify as `state_b`.
- Use the `next_question` field to formulate the conversational response applying all guidelines above.
"""

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
                            "description": f"The conversational response or next question to ask the user. You MUST write this strictly in {'Hebrew (עברית)' if lang == 'he' else 'English'} regardless of what language or characters the user types!"
                        }
                    },
                    "required": ["state", "extracted_parameters", "next_question"]
                }
            }
        }
    ]

    try:
        user_prompt = f"""
# Dynamic Context
You have already collected the following data points (if any):
{json.dumps(current_params, ensure_ascii=False, indent=2)}

Currently asked parameter (Active Parameter): {active_param}
Retry count for Active Parameter: {retry_count} (0 = first time asking, 1+ = user dodged/was vague previously)

# ACTIVE PARAMETER FOCUS (Strict Anti-Loop Rule)
An "Active Parameter" above means the backend is STILL WAITING for this specific trait and the conversation CANNOT advance to results until it is resolved.
- Your `next_question` MUST focus on extracting THIS Active Parameter. Do NOT jump ahead to Tier B / soft completion questions (other pets, allergies, first dog) while an essential Active Parameter is still pending.
- If `retry_count == 0`: ask about the Active Parameter (rephrase it naturally if you already asked once).
- If `retry_count >= 1`: the user has already dodged/been vague about this exact parameter. Ask ONE more time using a COMPLETELY DIFFERENT angle/phrasing. If their current input is still vague, extract a neutral value of 3 for this Active Parameter in `extracted_parameters` and move on.
- Always try to extract a concrete value for the Active Parameter from the current user input before deciding to ask again.

# CAPTURE VOLUNTEERED INFO (Memory Rule)
Even while focusing your QUESTION on the Active Parameter, you MUST still extract into `extracted_parameters` ANY other trait the user volunteers at any point. Examples:
- "I'm allergic" / "no shedding" -> c1_amount_of_shedding=1
- "I have kids" / "young children" -> b2_incredibly_kid_friendly_dogs=5
- "I have another dog" / "I already have a dog at home" -> b3_dog_friendly=5 AND a2_good_for_novice_owners=1 (someone who already owns a dog is NOT a first-time owner — you must NEVER then ask if it is their first dog)
- "no prior experience" / "my first dog" / "never had a dog" -> a2_good_for_novice_owners=5
- "I've raised dogs before" / "experienced owner" -> a2_good_for_novice_owners=1
These values are remembered, so the system will NOT ask about them again later. Always apply common-sense logical implications between traits (e.g. owning a dog implies experience).

# SOFT COMPLETION QUESTION (Strict No-Repeat Rule)
When you ask the optional soft completion question (Tier B), you MUST ONLY mention topics that are NOT already present in the "data points collected" above. NEVER re-ask about a trait the user already answered. For example, if a2_good_for_novice_owners is already known, do NOT ask "is this your first dog?"; if c1_amount_of_shedding is known, do NOT ask about allergies. If ALL Tier B topics are already known, do not ask a soft question at all — simply confirm you have everything and proceed.

Current user input: '{user_text}'"""
            
        messages = [{"role": "system", "content": system_prompt}]
        if chat_history:
            for msg in chat_history:
                if msg.get("content"):
                    messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": user_prompt})
            
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=tools,
            tool_choice={"type": "function", "function": {"name": "extract_dog_preferences"}},
            temperature=0.0
        )
        if not response.choices[0].message.tool_calls:
            return {
                "state": "state_b",
                "extracted_parameters": {},
                "next_question": "אני מצטער, לא הצלחתי להבין את הפנייה. תוכל/י לנסח אותה אחרת?" if lang == 'he' else "I'm sorry, I couldn't understand that. Could you rephrase?"
            }
            
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

def generate_explanations(dogs, user_params, user_original_text="", breed_requested=None, lang='he'):
    """
    מנוע ה-NLP: מייצר הסברים מותאמים אישית ל-3 הכלבים שנבחרו על ידי מנוע ה-ML,
    תוך הצלבה ישירה בין תיאור אורח החיים המקורי של המשתמש למאפייני הכלב והגזע.
    breed_requested: אם מנגנון הגזע החלופי (#12) הופעל, שם הגזע שהמשתמש ביקש במקור.
    """
    breed_desc_map = {}
    desc_path = os.path.join("data", "breed_descriptions.json")
    if os.path.exists(desc_path):
        try:
            with open(desc_path, 'r', encoding='utf-8') as f:
                breed_desc_map = json.load(f)
        except Exception:
            pass

    # הכנת כרטיס המידע המלא עבור כל כלב שנבחר
    dogs_info = []
    for d in dogs:
        breed_key = str(d.get("breed", "")).lower().strip()
        breed_desc = breed_desc_map.get(breed_key, "מידע כללי על תכונות הגזע אינו זמין כעת." if lang == 'he' else "Description not available.")

        dogs_info.append({
            "name": d.get("name", "הכלב" if lang == 'he' else "the dog"),
            "breed": d.get("breed"),
            "breed_description": breed_desc,
            "match_score": d.get("match_score"),
            "cluster": d.get("cluster"),
            "a1_apartment": d.get("a1_adapts_well_to_apartment_living"),
            "a4_alone": d.get("a4_tolerates_being_alone"),
            "d1_trainable": d.get("d1_easy_to_train"),
            "e3_exercise": d.get("e3_exercise_needs")
        })

    # Section #12: inject an alternative-breed framing only when the ML fallback was used.
    alternative_breed_instruction = ""
    if breed_requested:
        alternative_breed_instruction = (
            f"\n6. IMPORTANT: The user specifically hoped to adopt a '{breed_requested}', but none were "
            f"available under their physical filters. In each match_reason, gently explain that while no "
            f"'{breed_requested}' was available, these dogs share a very similar behavioral profile / lifestyle "
            f"cluster to the '{breed_requested}', making them excellent alternatives."
        )

    system_prompt = f"""
You are an expert dog adoption coordinator and matchmaker for PawMatch.
Your task is to generate customized, compelling explanations for the top 3 matched dogs based on BOTH the user's structured profile and their original free-text query.

CRITICAL INSTRUCTIONS:
1. Explain the match by directly linking the dog's characteristics (like energy level, trainability, apartment adaptation scores) to the user's specific lifestyle details mentioned in their raw text.
2. Incorporate the breed information from the provided description. You MUST explicitly state that the breed characteristics and history are sourced from DogTime.com.
3. Keep the tone warm, highly personalized, professional, and encouraging.
4. Output MUST be a valid JSON object matching the requested schema strictly.
5. The text within the JSON fields must be written entirely in {"Hebrew (עברית)" if lang == 'he' else "English"}.{alternative_breed_instruction}
"""

    user_prompt = f"""
User Original Free Text: "{user_original_text}"
Extracted Structured Parameters: {json.dumps(user_params, ensure_ascii=False)}
Recommended Dogs Data: {json.dumps(dogs_info, ensure_ascii=False)}

Generate the output JSON with the exact key "explanations" containing a list of objects.
Each object MUST contain these exact keys:
- "breed": the dog's breed, copied verbatim from the "breed" field in the provided Recommended Dogs Data (required for downstream mapping).
- "name": the dog's name.
- "match_reason": a 1-2 sentence explanation linking the dog's traits to the user's specific lifestyle from their original free text.
- "breed_info": a 1-2 sentence breed description based strictly on the provided "breed_description". Do NOT invent facts, and explicitly mention that this breed information is sourced from DogTime.com.
"""

    try:
        if client is None:
            raise Exception("OpenAI API key is missing or configuration error.")

        # מודל אמיתי, יציב ומקצועי
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={ "type": "json_object" },
            temperature=0.6
        )
        result = json.loads(response.choices[0].message.content)
        return result.get("explanations", [])
    except Exception as e:
        print(f"Error in generate_explanations: {e}")
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
        response = client.chat.completions.create(
            model="gpt-4o",
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
