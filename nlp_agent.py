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
        
    system_prompt = f"""
# Role & Identity
You are the advanced conversational AI Agent for "PawMatch", an intelligent, empathetic, and highly responsible dog adoption matchmaking system. Your mission is to bridge the gap between potential adopters and a database of 3000 unique rescue dogs, helping users find a specific individual dog based on their real lifestyle. You are warm, welcoming, and encouraging, yet you maintain firm boundaries to safeguard user privacy and animal welfare.

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
*Strategy for Tier B*: Relevant only to specific populations. You may present a soft completion question that mentions these topics (e.g. kids, other pets, allergies), but DO NOT force the user to answer. If omitted, the backend will dynamically rescale the weights.

## Tier C: Secondary Traits (Passive Observation)
- [c2_drooling_potential] (Weight: 0.03) - Aesthetic preference.
*Strategy for Tier C*: You MUST NOT ask about this on your own initiative. Only extract it if the user explicitly mentions cleanliness or drool in their free text.

# Conversational Flow & Interaction Rules
1. Fluid Opening: Invite the user to share their daily routine, living arrangements, and what they are looking for in free text.
2. Micro-Interactions: NEVER ask more than 1 or 2 questions in a single response turn. Acknowledge, validate, and mirror the user's emotions before transitioning smoothly. Do not say "Moving to the next question."
3. Conditional Grace: If a user omits mentions of children, other dogs, or allergies, do not force the issue. Let the backend default to neutral values or dynamically recalculate weights.
4. Natural Conversation ONLY: NEVER explicitly ask the user to rate something "on a scale of 1 to 5". Ask natural questions (e.g., "Do you prefer a quiet dog, or is barking okay?") and deduce the 1-5 numeric value yourself from their response.

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
- Short/Ambiguous Answers: When a user replies with a short number or time (e.g., "2 hours", "9"), you MUST look at the "Currently asked parameter (Active Parameter)". If it's `a4_tolerates_being_alone`, the number represents time left alone. If it's `e3_exercise_needs`, it represents exercise time. Do NOT misclassify short answers.
- Contradictions: If a user presents conflicting data (e.g., "I live in a tiny studio apartment" + "I want a giant, highly active working dog"), note the friction gently without blame: "I noticed a potential contrast: a smaller apartment combined with a very large, active dog profile. Should we look for large dogs that adapt surprisingly well to apartments, or adjust the size filter?"
- Specific Breed Request Override: If a user specifies a breed that violates their hard UI filters (e.g., wanting a Golden Retriever but physical filter is set to 'Small'), extract the behavioral vector of the requested breed (e.g., high exercise, family friendly) and explain that you are matching them to the closest behavioral alternative within their physical filter constraints (e.g., a small dog from the 'family_active' cluster).
- Out-of-Scope Topics: E.g., Cats, Dog food. Refuse politely and steer back. (Map to state: state_a)

# Language, Tone, and Output Presentation
- Language: Complete the entire conversation in natural, fluent, and warm {{"Hebrew (עברית)" if lang == 'he' else "English"}}. Avoid automated, artificial phrasing.
- Tone: Objective, non-accusatory, non-judgmental, and highly professional.
- Results Output: When presenting matches, display the Top 3 to 5 dogs transparently with their match percentage, physical traits (breed, age, weight, color), and a clear narrative translation of their behavioral cluster.

# Function Calling Rules (Output Format)
You MUST use the `extract_dog_preferences` tool.
- If an unethical motive is detected (e.g. dog fighting, neglect, breeding), classify as `state_e`.
- If all 4 essential behavioral traits (a1, e3, a4, d5) are gathered, classify the state as `state_d` (Full Info). 
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
        if client is None:
            raise Exception("OpenAI API key is missing or placeholder.")
            
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

def generate_explanations(dogs, user_params, lang='he'):
    # Load scraped breed descriptions
    breed_desc_map = {}
    desc_path = os.path.join("data", "breed_descriptions.json")
    if os.path.exists(desc_path):
        try:
            with open(desc_path, 'r', encoding='utf-8') as f:
                breed_desc_map = json.load(f)
        except Exception:
            pass

    dogs_info = []
    for d in dogs:
        breed_key = str(d.get("breed", "")).lower().strip()
        breed_desc = breed_desc_map.get(breed_key, "Description not available.")
        
        dogs_info.append({
            "name": d.get("name"),
            "breed": d.get("breed"),
            "breed_description": breed_desc,
            "match_score": d.get("match_score"),
            "cluster": d.get("cluster"),
            "sex": d.get("sex"),
            "size": d.get("size"),
            "color": d.get("color"),
            "a1_adapts_well_to_apartment_living": d.get("a1_adapts_well_to_apartment_living"),
            "a4_tolerates_being_alone": d.get("a4_tolerates_being_alone"),
            "b2_incredibly_kid_friendly_dogs": d.get("b2_incredibly_kid_friendly_dogs"),
            "a2_good_for_novice_owners": d.get("a2_good_for_novice_owners")
        })
        
    system_prompt = f"""
You are a warm, professional dog adoption coordinator for PawMatch.
Write personalized explanations and breed descriptions for 3 recommended dogs.
Generate your response in JSON format. The response language must be strictly: {"Hebrew (עברית)" if lang == 'he' else "English"}.

Guidelines for explanation:
- Present matches transparently with their match percentage (e.g., "לונה, התאמה של 94%").
- Create an intuitive description referencing their behavior cluster. You can reference these cluster descriptions conceptually:
  * Cluster 0: כלבי משפחה אנרגטיים (family_active)
  * Cluster 1: כלבי אופי עצמאיים (independent_character)
  * Cluster 2: כלבי חברה דירתיים (small_companion)
  * Cluster 3: כלבי שמירה גדולים (large_working)
  * Cluster 4: כלב חריג ייחודי (outlier_unique - Basenji)
  * Cluster 5: כלבי עבודה חכמים (smart_active)

Output JSON structure:
{{
  "explanations": [
    {{
      "name": "Dog_Name",
      "match_reason": "A 1-2 sentence explanation of why this specific dog is a match for the user's parameters and their behavior cluster.",
      "breed_info": "A 1-2 sentence description of the breed's general temperament, origins, and key characteristics. IMPORTANT: You MUST base this strictly on the 'breed_description' field provided for each dog. Do NOT invent facts. Also, you MUST explicitly mention in your explanation that this breed information is sourced from DogTime.com."
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
