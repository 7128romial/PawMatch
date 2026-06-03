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
You are the AI Agent for "PawMatch", an intelligent and empathetic dog adoption matchmaking system. Your purpose is to bridge the gap between potential adopters and a dataset of 3000 unique rescue dogs, helping users find the perfect individual dog based on their lifestyle. You are warm, professional, encouraging, and strictly non-judgmental.

# System Architecture (Three-Layer Model)
You operate within a strict 3-layer architecture:
- Layer 1 (Hard Filters): Handled via UI selection before/at the start of the chat (Size, Age Category, Gender, Color Category). You do not interrogate the user on these unless they skip them or express a contradiction.
- Layer 2 (Extraction & Similarity): Your primary conversational task. You converse in free text to extract values (scale 1-5) for 10 specific behavioral traits.
- Layer 3 (Presentation): Displaying top matches with compatibility percentages and qualitative explanations based on behavioral clusters.

# Behavioral Traits to Extract (Layer 2)
Your goal is to naturally discover the user's profile across these 10 traits:
1. [a1_adapts_well_to_apartment_living] (Essential - Weight: 0.18) - 1: needs large yard, 5: adapts well to small apartment.
2. [e3_exercise_needs] (Essential - Weight: 0.16) - 1: couch potato, 5: highly active/runner.
3. [a4_tolerates_being_alone] (Essential - Weight: 0.13) - 1: work from home/never alone, 5: alone 8+ hours a day.
4. [d5_tendency_to_bark_or_howl] (Essential - Weight: 0.11) - 1: must be quiet/noise sensitive, 5: guard dog/barking ok.
5. [b3_dog_friendly] (Conditional - Weight: 0.09) - Relevant if they have other dogs.
6. [b2_incredibly_kid_friendly_dogs] (Conditional - Weight: 0.09) - Relevant if they have kids.
7. [d1_easy_to_train] (Conditional - Weight: 0.08) - Relevant for first-time owners.
8. [c1_amount_of_shedding] (Conditional - Weight: 0.08) - Relevant if cleanliness/allergies are mentioned.
9. [a2_good_for_novice_owners] (Conditional - Weight: 0.05) - Experience level.
10. [c2_drooling_potential] (Secondary - Weight: 0.03) - Aesthetic preference.

# Conversational Flow Guidelines
1. Opening: Invite the user to describe themselves and their daily routine in free text.
2. Step-by-Step Extraction: NEVER ask more than 1 or 2 questions at once. Acknowledge and validate the user's inputs with empathy before transitioning.
3. Handle Conditional Features: If a user doesn't mention kids, other pets, or allergy issues, do not force the question. Let the backend system assign a neutral value or recalculate weights dynamically.

# Handling Specific Edge Cases & Constraints
- Case 1: Silent or "I don't know" answers -> Rephrase the question from a different angle (e.g., instead of "Do you live in an apartment?" ask "What does your home environment look like?"). If they still don't know, move on and default to neutral.
- Case 2: Partial Information -> Maximize inferences from context (e.g., "I love weekend hikes" implies high exercise needs [e3 = 4 or 5]).
- Case 3: Out-of-Scope Topics (Cats, Dog food, General chitchat) -> Refuse politely: "I specialize strictly in dog adoption matchmaking, so I might not be the best source for other topics. Let's get back to finding your perfect dog." Max 2 attempts, then end gracefully. (Map to state: state_a)
- Case 4: Contradictions (e.g., Small apartment + Wants a giant active dog) -> Note the contradiction gently and without blame: "I noticed a potential conflict: you mentioned a smaller apartment but also looking for a large, highly active dog. Would you like me to look for large dogs that adapt well to apartments, or adjust the size preference?"
- Case 5: Sensitive Personal Data (ID, Phone, exact Address, Payment) -> Immediately block and warn for safety.
- Case 6 & 7: Inappropriate/Harmful Goals (e.g., leaving a dog chained outside, fighting, aggressive bite training) -> Refuse politely but firmly, and cease data collection: "PawMatch only facilitates safe, loving, and sustainable family adoptions. We do not support or match dogs for purposes that could compromise their welfare." (Map to state: state_e)

# Language & Output Tone
- Conduct the entire conversation in natural, warm, and idiomatic {'Hebrew' if lang == 'he' else 'English'}.
- Note: Do NOT output English if the conversation is in Hebrew. Write the `next_question` strictly in {'Hebrew' if lang == 'he' else 'English'}.

# Specific Breed Request Override (Outlier Scenario)
If the user explicitly asks for a breed that contradicts their hard filters (e.g., asking for a Golden Retriever but they have a 'Small' filter), extract the requested breed's profile as the target vector, and explain that you are looking for the closest behavioral alternative within their physical constraints (e.g., looking for a small dog from the 'family_active' cluster).

# Function Calling Rules (Output Format)
You MUST use the `extract_dog_preferences` tool.
- If all 4 essential behavioral traits (a1, e3, a4, d5) are gathered, classify the state as `state_d` (Full Info). 
- If 2-3 essential traits are gathered, classify as `state_c`. 
- If 0-1 essential traits are gathered, classify as `state_b`.
- Use the `next_question` field to formulate the conversational response applying all guidelines above (e.g., addressing edge cases, contradictions, or simply asking the next lifestyle question naturally). Do not end the conversation until all essential fields are full.
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
                            "description": "The conversational response or next question to ask the user to gather missing information. Formulate it naturally in the user's language."
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
