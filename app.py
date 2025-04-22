from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import pyrebase
import os
from datetime import datetime
import uuid
import json
import random  # Add the missing import for random
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
import torch
import re # Ensure re is imported at the top

# Import our new modules
from emotion_detector import detect_emotion, get_emotion_response_style, get_relevant_resources
from knowledge_base import KnowledgeBase

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Firebase Configuration
firebase_config = {
    "apiKey": "AIzaSyCQK9chjw2Ykyd8KfMaUOJb0P6sBiyLWF0",
    "authDomain": "bf-flutter-e3a99.firebaseapp.com",
    "databaseURL": "https://bf-flutter-e3a99-default-rtdb.firebaseio.com",
    "projectId": "bf-flutter-e3a99",
    "storageBucket": "bf-flutter-e3a99.firebasestorage.app",
    "messagingSenderId": "654994166203",
    "appId": "1:654994166203:web:50969dfcf6a30eaae9749e",
    "measurementId": "G-1KX6EJ33MN"
}

firebase = pyrebase.initialize_app(firebase_config)
db = firebase.database()

# Set up a simpler text generation pipeline instead of full model
try:
    from transformers import pipeline, set_seed
    set_seed(42)  # For consistency
    generator = pipeline('text-generation', model="gpt2")  # Using GPT-2 which is more reliable
    print("Text generation model loaded successfully")
except Exception as e:
    print(f"Error loading model: {e}")
    # Define a rule-based fallback if models fail
    generator = None
    print("Using rule-based fallback responses")

# Initialize knowledge base
knowledge_base = KnowledgeBase()

# Global counters for tracking conversation depth
def initialize_user_tracking():
    """Initialize or get the user tracking dictionary"""
    if 'user_tracking' not in session:
        session['user_tracking'] = {
            'message_count': 0,
            'detected_emotions': [],
            'topics_discussed': [],
            'unanswered_questions': 0,
            'max_depth_topic': None
        }
    return session['user_tracking']

def get_kozy_response(message, chat_history):
    """Generate better empathetic responses without prompt leakage"""
    
    # Update tracking metrics to improve context
    tracking = initialize_user_tracking()
    tracking['message_count'] += 1
    
    # Detect emotion in the current message
    detected_emotion = detect_emotion(message, chat_history)
    if detected_emotion and detected_emotion != "neutral":
        tracking['detected_emotions'].append(detected_emotion)
        # Keep only the last 5 emotions
        if len(tracking['detected_emotions']) > 5:
            tracking['detected_emotions'] = tracking['detected_emotions'][-5:]
    
    # If we couldn't load the model, use rule-based responses
    if generator is None:
        return get_rule_based_response(message, chat_history, detected_emotion)
    
    try:
        # Get emotion response style to guide the model
        emotion_style = get_emotion_response_style(detected_emotion)
        
        # Much simpler prompt strategy to avoid instruction leakage
        recent_exchanges = min(6, len(chat_history)) # Slightly more context
        recent_history = chat_history[-recent_exchanges:] if recent_exchanges > 0 else []
        
        # IMPROVED PROMPT: Create a more directive prompt with emotion awareness
        prompt_header = f"""You are Kozy, a deeply empathetic and insightful AI companion that excels at supportive conversation.

IMPORTANT INSTRUCTIONS:
1. ALWAYS acknowledge and address the specific topics the user mentions (like work issues, boss problems, conflicts with peers, etc.)
2. Focus on the user's current message while maintaining context from the conversation
3. Respond with genuine warmth and validation that matches the user's situation
4. Avoid generic responses that could apply to any situation
5. When the user mentions a new topic, make sure to address it directly
6. If the user mentions a problem with their boss, workplace, peers, or conflicts, focus your response on that specific issue
7. End with an open-ended question related to what they've just shared

USER'S CURRENT EMOTION: {detected_emotion}
RESPONSE STYLE: Use a {emotion_style['tone']} tone. {emotion_style['validation']}. {emotion_style['approach']}.

CONVERSATION STYLE:
- Be warm, thoughtful and genuine
- Show you're carefully listening to their concerns
- Validate their feelings appropriately
- Respond to the specific situation they describe
- Keep your responses conversational and natural

"""
        conversation = prompt_header
        
        # Add context about previous messages to help model understand the conversation flow
        for entry in recent_history:
            if entry.get('user') and entry.get('user').strip():
                conversation += f"Friend: {entry['user']}\nKozy: {entry['kozy']}\n"
            # Include Kozy's previous multi-part messages correctly if stored that way
            elif entry.get('kozy') and isinstance(entry['kozy'], list):
                 conversation += f"Kozy: {' '.join(entry['kozy'])}\n"
            elif entry.get('kozy'):
                 conversation += f"Kozy: {entry['kozy']}\n"

        # Add explicit contextual hints for important topics
        message_lower = message.lower()
        if any(term in message_lower for term in ["boss", "manager", "supervisor"]):
            conversation += "Note: The user is mentioning issues with their boss or manager. Make sure to address this specific workplace concern.\n"
        if any(term in message_lower for term in ["work", "job", "task", "assignment"]) and any(term in message_lower for term in ["too much", "so much", "overload", "stress"]):
            conversation += "Note: The user is mentioning workload stress or overwhelming job responsibilities. Focus on this workplace concern.\n"
        if any(term in message_lower for term in ["peer", "colleague", "coworker"]) and any(term in message_lower for term in ["fight", "conflict", "argument"]):
            conversation += "Note: The user is mentioning interpersonal conflict at work. Address this relationship concern specifically.\n"

        # Add the current message with simple formatting
        prompt_input = f"Friend: {message}\nKozy:"
        conversation += prompt_input
        
        # Add structured reasoning step for complex situations with advice component
        reasoning_prompt = f"""
Before responding as Kozy, analyze the situation first:
1. IDENTIFY the key issues or emotions in the user's message
2. RECALL any relevant context from the conversation history
3. CONSIDER the appropriate emotional response and specific topics to address
4. PLAN a helpful, supportive response that:
   a) Validates their feelings
   b) Offers 1-2 gentle, practical suggestions or perspectives that might help
   c) Ends with an open-ended question to encourage deeper reflection

IMPORTANT: Balance empathy with practical support. When the user shares a challenge or difficult situation, 
always include a brief supportive suggestion or gentle advice along with your question.

Now, formulate your response as Kozy:
"""
        conversation += reasoning_prompt
        
        # Generate response with parameters optimized for emotional support and better reasoning
        result = generator(
            conversation,
            max_length=len(conversation.split()) + 180,  # Further increased max_length for advice + reasoning
            num_return_sequences=1,
            temperature=0.8,  # Slightly increased for more adaptability to new situations
            top_k=50,
            top_p=0.94,  # Increased slightly for more creative responses
            do_sample=True,
            repetition_penalty=1.2,  # Add repetition penalty to avoid circular reasoning
            pad_token_id=50256
        )
        
        generated_text = result[0]['generated_text']
        
        # Enhanced extraction logic to handle reasoning structure
        try:
            # First see if we can find the final response after reasoning
            kozy_marker = "Now, formulate your response as Kozy:"
            if kozy_marker in generated_text:
                response_start_index = generated_text.find(kozy_marker) + len(kozy_marker)
                kozy_response = generated_text[response_start_index:].strip()
            else:
                # Fall back to original extraction method
                response_start_index = generated_text.find(prompt_input) + len(prompt_input)
                kozy_response = generated_text[response_start_index:].strip()

            # Clean up any trailing text or repeated prompts
            cutoff_markers = ["Friend:", "\n\n", "\nFriend", "You are Kozy", "respond with empathy", "Listen carefully", "1. IDENTIFY", "2. RECALL", "3. CONSIDER", "4. PLAN", "Before responding"]
            for marker in cutoff_markers:
                if marker in kozy_response:
                    kozy_response = kozy_response.split(marker)[0].strip()

            # Further check for prompt leakage or very short/empty responses
            prompt_keywords = ["empathy", "companion", "Kozy", "respond", "deeply", "caring", "authentic", "validate", "acknowledge"] # Expanded keywords
            contains_prompt_leak = any(keyword in kozy_response.lower()[:70] for keyword in prompt_keywords)

            # Add check for nonsensical or unsafe content
            unsafe_keywords = ["fight back", "hit them", "attack", "kill", "hurt them"]
            contains_unsafe_content = any(keyword in kozy_response.lower() for keyword in unsafe_keywords)
            # Basic check for nonsensical phrases (can be expanded)
            contains_nonsense = "feathers are feathers" in kozy_response.lower()

            # Check for proper session context awareness and message appropriateness
            current_session_references = False
            inappropriate_response = False
            
            # Detect if this is a simple greeting or short message that doesn't warrant emotional validation
            message_lower = message.lower().strip()
            simple_greetings = ["hi", "hey", "hello", "yo", "sup", "hiya", "good morning", "good afternoon", "good evening"]
            is_simple_greeting = message_lower in simple_greetings or message_lower.startswith(tuple(simple_greetings))
            
            # Check if response has inappropriate validation for simple messages
            inappropriate_validations = [
                "it makes complete sense that you'd feel that way",
                "that sounds really difficult",
                "i understand your feelings",
                "your feelings are valid",
                "that's a lot to handle",
                "it sounds like you're carrying"
            ]
            
            # Flag inappropriate validations for simple greetings
            if is_simple_greeting and any(validation in kozy_response.lower() for validation in inappropriate_validations):
                inappropriate_response = True
                print(f"Inappropriate validation detected for greeting: '{kozy_response}'")
                
            # Check for irrelevant or generic responses to specific topics
            important_topics = {
                "boss": ["boss", "manager", "supervisor"],
                "work": ["work", "job", "workload", "tasks", "assignment"],
                "peers": ["peer", "peers", "colleague", "coworker", "coworkers"],
                "conflict": ["fight", "conflict", "argument", "disagreement", "angry"]
            }
            
            # Detect if message contains important topics
            detected_topics = []
            for topic, keywords in important_topics.items():
                if any(keyword in message_lower for keyword in keywords):
                    detected_topics.append(topic)
            
            # Evaluate if the response acknowledges the topics appropriately
            missing_topic_acknowledgment = False
            if detected_topics:
                # Check if any important topics are acknowledged in the response
                topic_acknowledged = False
                for topic in detected_topics:
                    topic_keywords = important_topics.get(topic, [])
                    if any(keyword in kozy_response.lower() for keyword in topic_keywords):
                        topic_acknowledged = True
                        break
                
                # Also check for related terms that would indicate topic acknowledgment
                if topic_acknowledged == False:
                    if "boss" in detected_topics and any(term in kozy_response.lower() for term in ["manager", "supervisor", "workplace", "management", "superior"]):
                        topic_acknowledged = True
                    elif "work" in detected_topics and any(term in kozy_response.lower() for term in ["workload", "job", "task", "professional", "career", "workplace"]):
                        topic_acknowledged = True
                    elif "peers" in detected_topics and any(term in kozy_response.lower() for term in ["coworker", "colleague", "relationship", "team", "professional relationship"]):
                        topic_acknowledged = True
                    elif "conflict" in detected_topics and any(term in kozy_response.lower() for term in ["tension", "disagreement", "argument", "situation", "difficult interaction", "confrontation"]):
                        topic_acknowledged = True
                
                # If no acknowledgment of important topics, mark response as potentially irrelevant
                if not topic_acknowledged:
                    print(f"Response doesn't acknowledge important topics {detected_topics}: '{kozy_response}'")
                    missing_topic_acknowledgment = True
            
            if not kozy_response or len(kozy_response) < 15 or contains_prompt_leak or contains_unsafe_content or contains_nonsense or inappropriate_response or missing_topic_acknowledgment:
                print(f"LLM response rejected: '{kozy_response}'. Reason: short/leak/unsafe/nonsense/inappropriate/missing topic. Falling back to rule-based.")
                
                # Handle simple greetings appropriately
                if is_simple_greeting:
                    greeting_responses = [
                        f"Hi there! It's nice to hear from you. How are you feeling today? ✨",
                        f"Hello! I'm here and ready to chat. What's on your mind today?",
                        f"Hey! Thanks for reaching out. How are you doing right now? I'm here to listen.",
                        f"Hi! I'm glad you're here. How has your day been so far?"
                    ]
                    return [random.choice(greeting_responses)]
                
                # Enhanced topic detection with typo tolerance (new function)
                def fuzzy_match(text, keywords):
                    """Detect keywords even with typos"""
                    # Convert text to lowercase for comparison
                    text_lower = text.lower()
                    
                    # Check for exact matches first
                    for keyword in keywords:
                        if keyword in text_lower:
                            return True
                    
                    # Check for close matches (handle common typos)
                    typo_mapping = {
                        'wokr': 'work', 'wrk': 'work', 'wark': 'work',
                        'bos': 'boss', 'boss': 'boss', 'manage': 'manager',
                        'stres': 'stress', 'stresed': 'stressed', 'stressd': 'stressed',
                        'hecti': 'hectic', 'hactice': 'hectic', 'hetic': 'hectic',
                        'overwelm': 'overwhelm', 'overwhelmd': 'overwhelmed',
                        'colleg': 'colleague', 'cowork': 'coworker', 'peer': 'peer',
                        'figt': 'fight', 'fite': 'fight', 'argu': 'argument'
                    }
                    
                    # Extract words from text
                    words = text_lower.split()
                    
                    # Check each word for potential typos
                    for word in words:
                        if word in typo_mapping and typo_mapping[word] in keywords:
                            return True
                        # Check for partial matches (if word is at least 4 chars)
                        if len(word) >= 4:
                            for keyword in keywords:
                                # If 70% of the characters match, consider it a match
                                if len(keyword) >= 4 and (word in keyword or keyword in word):
                                    return True
                    
                    return False
                
                # Check for hectic/busy day mentions using fuzzy matching
                if fuzzy_match(message_lower, ["hectic", "busy", "crazy day", "wild day", "rough day", "tough day"]):
                    hectic_responses = [
                        ["Oh wow, sounds like your day has been really hectic! Those kinds of days can be so draining.",
                         "When everything feels chaotic, it's like you can barely catch your breath between one thing and the next.",
                         "What's been the most challenging part of your day so far? Sometimes just talking about it helps a bit."],
                        ["Hectic days are so exhausting! I completely get that overwhelmed feeling when everything's happening at once.",
                         "It's like you're being pulled in ten different directions and can't fully focus on any one thing properly.",
                         "Have you had any chance to take even a tiny breather today? Sometimes even 5 minutes can help reset a bit."],
                        ["Those super busy days can really take it out of you! I'm sorry you're dealing with that chaos.",
                         "It's tough when you don't even have space to process one thing before the next thing demands your attention.",
                         "What typically helps you decompress after days like this? I'm here to listen if you just need to vent about it all."]
                    ]
                    return random.choice(hectic_responses)
                
                # Enhanced boss topic detection with better typo handling
                if fuzzy_match(message_lower, ["boss", "manager", "supervisor", "superior", "management"]):
                    boss_responses = [
                        ["Oh no, boss troubles? That can be so frustrating! I've heard from so many people who struggle with their managers.",
                         "Sometimes it feels like they just don't understand what we're dealing with day-to-day, right?",
                         "Tell me more about what's happening with your boss - I really want to understand what you're going through."],
                        ["Boss issues can be so draining! I totally get why that would be on your mind.",
                         "The dynamics with managers can really affect our whole mood and even how we feel about ourselves sometimes.",
                         "What's been happening lately with your boss? I'm all ears and no judgment here."],
                        ["Ugh, dealing with difficult bosses is seriously one of the hardest parts of work life! I'm sorry you're facing that.",
                         "It's like they have so much power over our daily experience and when it's not good, it's REALLY not good.",
                         "Want to vent about what's going on? Sometimes just getting it all out can help a little."]
                    ]
                    return random.choice(boss_responses)
                
                # Enhanced workload detection with typo tolerance
                if (fuzzy_match(message_lower, ["work", "job", "task", "project", "deadline", "workload"]) and 
                    (fuzzy_match(message_lower, ["too much", "so much", "lots", "overload", "overwhelm", "pile", "stress"]) or 
                    fuzzy_match(message_lower, ["little time", "not enough time", "deadline", "behind", "catching up"]))):
                    workload_responses = [
                        ["Wow, sounds like you're completely swamped with work! That overwhelming feeling is the worst.",
                         "It's like being stuck in quicksand sometimes - the harder you try to catch up, the more exhausted you feel.",
                         "How long have things been this intense? Have you had any chance to take a breather lately?"],
                        ["Being overloaded at work is so stressful! I hate that feeling of never being able to catch up.",
                         "It's not just the work itself that's hard - it's that constant pressure in the back of your mind, even when you're supposed to be relaxing.",
                         "What's contributing most to the workload right now? Is it a particular project or just everything piling up at once?"],
                        ["Oh gosh, too much work is seriously the worst! Makes it hard to even think straight sometimes.",
                         "I find it so frustrating when there's just not enough hours in the day to get everything done properly.",
                         "Have you been able to talk to anyone at work about redistributing some of the load? Or is that not really an option?"]
                    ]
                    return random.choice(workload_responses)
                
                # Combined stress and not feeling well detection (improved for broader matching)
                if fuzzy_match(message_lower, ["stress", "anxious", "worried", "overwhelm", "pressure", "tension"]) or (
                   fuzzy_match(message_lower, ["not feeling", "feel bad", "feeling bad", "not well", "terrible", "awful"])):
                    stress_responses = [
                        ["I can hear that you're feeling really stressed right now. That's such a tough emotional state to be in.",
                         "Stress has this way of making everything feel heavier and more difficult than it normally would.",
                         "What do you think is contributing the most to your stress right now? Sometimes identifying the biggest factor can help a little."],
                        ["Being stressed and not feeling well is such a difficult combination to deal with. I'm sorry you're experiencing that.",
                         "Our bodies and minds are so connected - when one is struggling, the other usually feels it too.",
                         "Have you been able to do anything small for yourself today that might bring even a moment of relief?"],
                        ["Stress can be so physically and emotionally draining! It sounds like you're really going through it right now.",
                         "Sometimes when we're stressed, everything feels like it's piling on all at once and won't let up.",
                         "What's one small thing that typically helps you feel even slightly better when you're stressed like this?"]
                    ]
                    return random.choice(stress_responses)
                
                # Better peer conflict detection with contextual awareness
                if (fuzzy_match(message_lower, ["peer", "colleague", "coworker", "workmate", "teammate"]) and 
                    fuzzy_match(message_lower, ["fight", "argument", "conflict", "disagreement", "issue", "problem", "tension"])):
                    conflict_responses = [
                        ["Oof, colleague drama is so stressful! Especially since you can't just avoid seeing them like you could with other people.",
                         "Those workplace relationships get complicated fast when there's tension - it affects everything!",
                         "Do you want to tell me what happened? Sometimes talking it through with someone outside the situation helps sort things out."],
                        ["Workplace conflicts are so awkward and draining! I'm sorry you're dealing with that right now.",
                         "It's like you're stuck in this weird space where you have to keep being professional while also having all these feelings.",
                         "What led to the conflict? I'm curious to hear your perspective on how things unfolded."],
                        ["Oh no, trouble with colleagues? That can make even walking into work feel like a huge challenge.",
                         "Those relationship dynamics at work can really mess with your peace of mind - it's hard to just leave it at the office sometimes.",
                         "Want to talk about what happened between you two? No judgment here, just a friendly ear."]
                    ]
                    return random.choice(conflict_responses)
                
                # Add general response for when someone is sharing something negative but topic isn't clear
                if fuzzy_match(message_lower, ["bad", "awful", "terrible", "worst", "horrible", "not good", "difficult", "rough"]):
                    general_negative_responses = [
                        ["I'm sorry to hear you're having a rough time. That really sucks, and I appreciate you sharing that with me.",
                         "Sometimes life throws a lot at us all at once, and it can feel overwhelming to deal with.",
                         "Would you like to tell me more about what's going on? I'm here to listen without judgment."],
                        ["It sounds like things have been pretty difficult for you lately. That's really hard to deal with.",
                         "When life gets tough, even small things can start to feel like big challenges.",
                         "What's been the hardest part to handle recently? Sometimes talking through it can help, even just a little."],
                        ["I'm sorry you're going through this tough time. It takes courage to acknowledge when things aren't going well.",
                         "Everyone struggles sometimes, and it's completely okay to not be okay.",
                         "Is there anything specific that's been weighing on you the most? I'm here to listen if you want to talk about it."]
                    ]
                    return random.choice(general_negative_responses)
                
                # For specific emotional or physical distress triggers, use specialized responses
                message_lower = message.lower()
                
                # Special handling for physical pain mentions with more personal tone
                if any(word in message_lower for word in ["pain", "paining", "hurt", "ache", "body", "physical"]):
                    pain_responses = [
                        ["I'm so sorry you're in pain right now - that's really tough to deal with on top of everything else.",
                         "Physical discomfort has this way of taking over your whole experience. It's hard to focus on anything else, isn't it?",
                         "Is there anything that's been helping with the pain, even a little bit? I really wish I could do more than just listen."],
                        ["Oh no, physical pain is so draining! I really feel for you - it's exhausting to deal with that.",
                         "Our bodies and minds are so connected - physical pain can really wear down our emotional reserves too.",
                         "How long have you been feeling this way? I'm here to listen if you want to talk more about what you're experiencing."],
                        ["Being in pain is such a lonely experience sometimes - I'm really glad you told me about it.",
                         "It's so hard when your body isn't feeling right. It affects literally everything else in life.",
                         "What does your pain feel like today? Sometimes putting it into words can help, even just a little."]
                    ]
                    return random.choice(pain_responses)
                
                # Enhanced handling for mental health crisis with more empathy and urgency
                if any(phrase in message_lower for phrase in ["want to die", "kill myself", "end it all", "suicide", "not worth living"]):
                    crisis_responses = [
                        ["I'm really concerned about what you just shared, and I'm glad you felt you could tell me.",
                         "Those feelings are incredibly difficult to bear alone, and it takes courage to speak about them.",
                         "Would it be okay if we talked about some resources that might help? There are people trained specifically to help with these intense feelings.",
                         "The National Suicide Prevention Lifeline is available 24/7 at 988 or 1-800-273-8255, and they really do care."],
                        ["I'm giving you my full attention right now because what you're sharing matters deeply.",
                         "Those dark thoughts can feel overwhelming, but please know you don't have to face them by yourself.",
                         "Sometimes talking to a crisis counselor who's specially trained can make a real difference - would you consider reaching out to one?",
                         "You can text HOME to 741741 to reach the Crisis Text Line anytime - they're really good at helping in moments like this."],
                        ["Thank you for trusting me with something so personal and difficult. That shows real strength.",
                         "These feelings are incredibly painful, but they don't define you or your future. Things really can get better with support.",
                         "Would you be willing to talk to a professional who can help navigate these feelings? You deserve that kind of specialized support.",
                         "The 988 Suicide & Crisis Lifeline has helped many people through moments just like this - they're just a call or text away."]
                    ]
                    return random.choice(crisis_responses)
                
                # New: Handling for "not feeling well" with more personality
                if any(phrase in message_lower for phrase in ["not feeling well", "feel sick", "feeling bad", "not good", "terrible", "awful"]):
                    unwell_responses = [
                        ["I'm sorry you're not feeling well today. That's really tough, especially when you have other things you want or need to do.",
                         "Sometimes just having someone acknowledge that you're struggling can help a tiny bit. So consider me officially in your corner!",
                         "What do you think might help you feel even a little better right now? Even small comforts can make a difference."],
                        ["Oh no, feeling unwell is the worst! I hate those days when you just can't seem to get comfortable or feel right.",
                         "Being sick or off-balance affects everything - your mood, your energy, your whole outlook on life!",
                         "Have you been able to give yourself any little breaks or comforts today? Sometimes that's the best we can do when we're not feeling great."],
                        ["Not feeling well? That's really rough - I'm sorry you're going through that right now.",
                         "It's frustrating when our bodies or minds aren't cooperating with what we want to do or how we want to feel.",
                         "What specifically doesn't feel good? Sometimes talking about it can help make it feel a little less overwhelming."]
                    ]
                    return random.choice(unwell_responses)
                
                # Fall back to rule-based for other cases
                return get_rule_based_response(message, chat_history)
                
            # Enhanced conversion to multi-part messages for more natural flow
            sentence_parts = []
            sentences = re.split(r'(?<=[.?!])\s+', kozy_response)
            current_part = ""
            
            # Combine sentences more thoughtfully, aiming for 1-2 sentences per part
            part_sentence_count = 0
            for sentence in sentences:
                if sentence:
                    current_part += sentence + " "
                    part_sentence_count += 1
                    # Create a new part after 1-2 sentences or if length exceeds limit
                    if part_sentence_count >= random.randint(1, 2) or len(current_part) > 130:
                         sentence_parts.append(current_part.strip())
                         current_part = ""
                         part_sentence_count = 0

            # Add the final part if not empty
            if current_part.strip():
                sentence_parts.append(current_part.strip())

            # Ensure at least one part exists
            if not sentence_parts:
                 sentence_parts.append(kozy_response)

            # Add appropriate emotes based on emotional content - MORE SUBTLE
            if sentence_parts:
                emotion = 'caring'
                message_lower = message.lower()
                last_part = sentence_parts[-1]

                if any(word in message_lower for word in ["sad", "hurt", "pain", "upset", "not feeling", "bad", "fight", "conflict", "stress"]):
                    emotion = 'concerned'
                    emotes = ["(｡•́‿•̀｡)", "(´｡• ᵕ •｡`)", "♥"]
                elif any(word in message_lower for word in ["happy", "good", "great", "wonderful", "excited", "amazing", "joy"]):
                    emotion = 'happy'
                    emotes = ["✨", "☆", "(>ᴗ<)", "♪"]
                else: # Default to caring/neutral emotes
                    emotes = ["✨", "☆", "♥", "( ´･ᴗ･` )", "~"]
                
                # Add emote to last part with lower chance (e.g., 40%) and ensure it fits naturally
                if random.random() < 0.4 and last_part and last_part[-1].isalnum():
                     sentence_parts[-1] += f" {random.choice(emotes)}"
                elif random.random() < 0.2 and last_part: # Even lower chance if ending with punctuation
                     sentence_parts[-1] += f" {random.choice(emotes)}"


            # Final safety check
            if sentence_parts and any(keyword in sentence_parts[0].lower() for keyword in unsafe_keywords):
                 print(f"LLM response part rejected post-split (unsafe): '{sentence_parts[0]}'. Falling back to rule-based.")
                 return get_rule_based_response(message, chat_history)

            return sentence_parts
                
        except Exception as e:
            print(f"Error processing LLM response: {e}")
            return get_rule_based_response(message, chat_history)
            
    except Exception as e:
        print(f"Error generating response: {e}")
        return get_rule_based_response(message, chat_history)

def get_rule_based_response(message, chat_history=None, user_emotion=None):
    """Provide engaging, supportive responses with a mature, empathetic vibe"""
    # We don't need to re-import random here since we now have it globally
    
    # Convert message to lowercase for easier matching
    message_lower = message.lower().strip()
    
    # Handle greetings and short messages first
    simple_greetings = ["hi", "hey", "hello", "yo", "sup", "hiya", "good morning", "good afternoon", "good evening"]
    if message_lower in simple_greetings or message_lower.startswith(tuple(simple_greetings)):
        greeting_responses = [
            f"Hi there! It's nice to hear from you. How are you feeling today? ✨",
            f"Hello! I'm here and ready to chat. What's on your mind today?",
            f"Hey! Thanks for reaching out. How are you doing right now? I'm here to listen.",
            f"Hi! I'm glad you're here. How has your day been so far? I'm here to listen."
        ]
        return [random.choice(greeting_responses)]
    
    # Improved topic detection for more specific responses
    topic_matches = {
        "boss": ["boss", "supervisor", "manager"],
        "workload": ["too much work", "so much work", "overloaded", "workload", "too many tasks", "deadlines", "overwhelmed at work"],
        "peer_conflict": ["fight with peer", "argument with colleague", "conflict with coworker", "disagreement with team", "colleague issue"],
        "not_feeling_well": ["not feeling well", "feel sick", "not good", "feeling bad", "unwell", "ill"],
        "stress": ["stressed", "stress", "anxiety", "anxious", "worried", "overwhelmed", "pressure"]
    }
    
    # Detect primary topic
    detected_topics = []
    for topic, keywords in topic_matches.items():
        if any(keyword in message_lower for keyword in keywords):
            detected_topics.append(topic)
    
    # Enhanced topic-specific responses
    if "boss" in detected_topics:
        return [
            "I understand you're dealing with difficulties related to your boss. That can definitely be stressful.",
            "Manager relationships can significantly impact our work experience and wellbeing. Your frustration sounds valid.",
            "Would you like to tell me more about the specific challenges you're facing with your boss? I'm here to listen and support you."
        ]
    
    if "workload" in detected_topics:
        return [
            "It sounds like you're dealing with an overwhelming amount of work right now. That must be really draining.",
            "Having too many tasks and responsibilities can leave us feeling constantly behind and stressed.",
            "How has this heavy workload been affecting you? I'm here to listen if you'd like to talk more about it."
        ]
    
    if "peer_conflict" in detected_topics:
        return [
            "I'm sorry to hear about the conflict with your peers. Workplace relationships can be quite challenging.",
            "Arguments with colleagues are particularly difficult since you still need to work together afterward.",
            "Would you like to share what happened? Sometimes talking through these situations can help process the emotions involved."
        ]
    
    # For specific emotional or physical distress triggers, use specialized responses
    # ...existing code...

def preprocess_user_message(message):
    """Check message for patterns that need special responses"""
    message_lower = message.lower().strip()
    
    # Detect greetings and common conversation starters
    simple_greetings = ["hi", "hey", "hello", "yo", "sup", "hiya", "good morning", "good afternoon", "good evening"]
    
    # For very short messages, determine the appropriate response type
    if len(message.split()) <= 2:
        # Handle common greetings naturally
        if message_lower in simple_greetings or message_lower.startswith(tuple(simple_greetings)):
            greeting_responses = [
                f"Hi there! It's nice to hear from you. How are you feeling today? ✨",
                f"Hello! I'm here and ready to chat. What's on your mind today?",
                f"Hey! Thanks for reaching out. How are you doing right now?",
                f"Hi! I'm glad you're here. How has your day been so far? I'm here to listen."
            ]
            return True, random.choice(greeting_responses)
            
        # Handle common expressions separately
        if message_lower in ["what", "huh", "why", "how", "ok", "okay"]:
            return True, "I'm here to chat and support you! Could you share a bit more about what's on your mind? The more you share, the better I can understand how you're feeling ✨"
    
    # Not a special case
    return False, None

def get_session_history():
    """Get chat history from the current session"""
    if 'chat_history' not in session:
        session['chat_history'] = []
    
    # Reset the chat history if coming from a new Firebase session
    if 'firebase_session_key' in session and 'last_firebase_session' in session:
        if session['firebase_session_key'] != session['last_firebase_session']:
            session['chat_history'] = []
            session['last_firebase_session'] = session['firebase_session_key']
    
    return session['chat_history']

def create_chat_session(uid):
    """Create a new chat session in Firebase"""
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        timestamp = str(datetime.now().timestamp()).replace(".", "_")
        
        # Create a session key for the current chat session
        session_key = timestamp
        session['firebase_session_key'] = session_key
        session['last_firebase_session'] = session_key  # Track for history management
        session['session_start_time'] = datetime.now().strftime("%H:%M:%S")
        
        # Initialize the chat session in Firebase
        db.child("kozy").child(uid).child(today).child(session_key).set({"created_at": datetime.now().strftime("%H:%M:%S")})
        
        # Clear session history when creating a new session
        session['chat_history'] = []
        
        return session_key
    except Exception as e:
        print(f"Error creating chat session: {e}")
        return None

def save_chat_to_firebase(uid, user_message, kozy_response):
    """Save chat messages to the current session in Firebase with emotion data"""
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Get the current session key or create a new one
        session_key = session.get('firebase_session_key')
        if not session_key:
            session_key = create_chat_session(uid)
        
        # Generate a unique message ID based on timestamp
        message_id = str(datetime.now().timestamp()).replace(".", "_")
        
        # Get emotion if available
        user_emotion = None
        if 'user_tracking' in session and 'detected_emotions' in session['user_tracking'] and session['user_tracking']['detected_emotions']:
            user_emotion = session['user_tracking']['detected_emotions'][-1]
        
        # Create chat message data with emotion
        chat_data = {
            "user": user_message,
            "kozy": kozy_response,
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "emotion": user_emotion
        }
        
        # Save to the current session
        db.child("kozy").child(uid).child(today).child(session_key).child("messages").child(message_id).set(chat_data)
        
        return True
    except Exception as e:
        print(f"Error saving to Firebase: {e}")
        return False

@app.route('/')
def index():
    """Landing page - asks for Firebase UID"""
    if 'uid' in session:
        return redirect(url_for('chat'))
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    """Handle login form submission"""
    uid = request.form.get('uid')
    if uid:
        session['uid'] = uid
        session['chat_history'] = []
        
        # Create a new session in Firebase for this user
        create_chat_session(uid)
        
        return redirect(url_for('chat'))
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    """Clear session and redirect to login"""
    session.clear()
    return redirect(url_for('index'))

@app.route('/chat')
def chat():
    """Main chat interface"""
    if 'uid' not in session:
        return redirect(url_for('index'))
    
    # Always create a new session when loading the chat page
    create_chat_session(session['uid'])
    
    # Start fresh with a greeting
    chat_history = get_session_history()
    if not chat_history:
        kozy_greeting = "Hi there! I'm Kozy, your emotional companion. How are you feeling today? I'm here to listen and chat with you! ✨"
        chat_history.append({"user": "", "kozy": kozy_greeting, "timestamp": datetime.now().strftime("%H:%M:%S")})
        session['chat_history'] = chat_history
        save_chat_to_firebase(session['uid'], "", kozy_greeting)
    
    return render_template('chat.html', chat_history=chat_history)

@app.route('/send_message', methods=['POST'])
def send_message():
    """Handle sending a new message with improved response selection and safety checks"""
    if 'uid' not in session:
        return jsonify({"error": "Not logged in"}), 401
    
    data = request.get_json()
    user_message = data.get('message', '').strip()
    
    if not user_message:
        return jsonify({"error": "Empty message"}), 400
    
    # Get current chat history and tracking info
    chat_history = get_session_history()
    tracking = initialize_user_tracking()
    
    try:
        # Detect emotion in the user's message
        user_emotion = detect_emotion(user_message, chat_history)
        
        # Update tracking data with new emotion
        if user_emotion != "neutral":
            tracking['detected_emotions'].append(user_emotion)
            if len(tracking['detected_emotions']) > 5:
                tracking['detected_emotions'] = tracking['detected_emotions'][-5:]
        
        # Check for special cases that need direct handling
        is_special, special_response = preprocess_user_message(user_message)
        if is_special:
            kozy_response = [special_response]  # Wrap in list for consistency
        else:
            # Try personality-driven response first with enhanced context awareness
            try:
                # Get app feature recommendation if appropriate, passing chat history for context
                suggested_feature = knowledge_base.get_app_feature(
                    user_emotion, 
                    user_message,
                    chat_history  # Pass chat history for context-aware suggestions
                )
                
                # Get emotion-appropriate personality response with chat history context
                personality_response = knowledge_base.get_personality_response(
                    user_message, 
                    user_emotion, 
                    suggested_feature,
                    chat_history  # Pass chat history for personalized responses
                )
                
                # If we have a good personality response, use it
                if personality_response and len(personality_response) > 0:
                    kozy_response = personality_response
                else:
                    # Fall back to LLM or rule-based
                    kozy_response = get_kozy_response(user_message, chat_history)
                
                # Debug: Print out the response type and content
                print(f"Response type: {type(kozy_response)}")
                print(f"Response content: {kozy_response}")
                
                # Check for message repetition pattern and avoid it
                if chat_history and len(chat_history) >= 4:
                    recent_kozy_msgs = []
                    for entry in chat_history[-4:]:
                        if isinstance(entry.get('kozy'), list) and len(entry['kozy']) > 0:
                            recent_kozy_msgs.append(entry['kozy'][0])
                        elif isinstance(entry.get('kozy'), str):
                            recent_kozy_msgs.append(entry['kozy'])
                    
                    # Check if we're repeating the same message pattern
                    if len(recent_kozy_msgs) > 3 and recent_kozy_msgs[0] == recent_kozy_msgs[2] and recent_kozy_msgs[1] == recent_kozy_msgs[3]:
                        # We're in a repetition loop, force a different response
                        print("Detected response repetition pattern, generating alternative response")
                        
                        # Use different emotion template to break pattern
                        alternate_emotions = [e for e in ["happy", "sad", "neutral", "excited", "bored"] if e != user_emotion]
                        alt_emotion = random.choice(alternate_emotions)
                        kozy_response = knowledge_base.get_personality_response(
                            user_message, 
                            alt_emotion, 
                            None,  # No feature suggestion in this case
                            chat_history
                        )
                        
                        # If still seems repetitive, use a completely different approach
                        if isinstance(kozy_response, list) and len(kozy_response) > 0:
                            if any(msg == kozy_response[0] for msg in recent_kozy_msgs):
                                kozy_response = [
                                    "I notice we might be going in circles a bit. Let's try a different approach.",
                                    "What's one thing you'd like to talk about that we haven't discussed yet? I'm here to listen to anything that's on your mind."
                                ]
                
                # Check for relevant FAQs that match the topic, append if appropriate
                # But only do this occasionally to avoid being repetitive
                if random.random() < 0.25:  # 25% chance to add FAQ
                    relevant_faqs = knowledge_base.find_relevant_faq(
                        user_message, 
                        user_emotion, 
                        chat_history
                    )
                    
                    if relevant_faqs:
                        faq = relevant_faqs[0]
                        faq_msg = f"By the way, {faq['q']} {faq['a']}"
                        
                        if isinstance(kozy_response, list):
                            # Insert the FAQ as the last message
                            kozy_response.append(faq_msg)
                        else:
                            kozy_response = [kozy_response, faq_msg]
                
            except Exception as personality_error:
                print(f"Personality response failed: {str(personality_error)}")
                # Fall back to LLM response
                kozy_response = get_kozy_response(user_message, chat_history)
            
            # Ensure we have a list response
            if not isinstance(kozy_response, list):
                kozy_response = [str(kozy_response)]
        
        # --- Final Safety Check ---
        unsafe_keywords = ["fight back", "hit them", "attack", "kill", "hurt them"] 
        contains_unsafe_content = False
        if kozy_response and isinstance(kozy_response, list):
             # Check only the first message part for immediate safety issues
             if any(keyword in str(kozy_response[0]).lower() for keyword in unsafe_keywords):
                 contains_unsafe_content = True
        
        if contains_unsafe_content:
            print(f"Final response rejected (unsafe): '{kozy_response[0]}'. Substituting safe response.")
            # Substitute with a safe, concerned response
            kozy_response = [
                "I sense a lot of strong emotions right now, and I want to make sure we talk safely.",
                "Violence isn't the answer. Can we talk more about what led to this feeling? I'm here to support you. ♥"
                ]

        # Add timestamp to each message for better tracking
        current_time = datetime.now().strftime("%H:%M:%S")
        
        # Save to session and Firebase
        if kozy_response:
            first_message = kozy_response[0]
            remaining_messages = kozy_response[1:] if len(kozy_response) > 1 else []
            
            # Store the remaining messages in the session for retrieval
            session['pending_messages'] = remaining_messages
            
            # Store the full list for better context
            full_kozy_response_for_history = kozy_response
            chat_history.append({"user": user_message, "kozy": full_kozy_response_for_history, "timestamp": current_time, "emotion": user_emotion})
            save_chat_to_firebase(session['uid'], user_message, first_message)  # Save first message to Firebase

            session['chat_history'] = chat_history # Update session history

            return jsonify({
                "response": first_message,
                "has_more": len(remaining_messages) > 0,
                "emotion": user_emotion
            })
        else:
            # Fallback response
            fallback = "I'm processing that. Tell me more about how you feel~"
            chat_history.append({"user": user_message, "kozy": fallback, "emotion": user_emotion})
            session['chat_history'] = chat_history
            save_chat_to_firebase(session['uid'], user_message, fallback)
            return jsonify({"response": fallback, "has_more": False, "emotion": user_emotion})
            
    except Exception as e:
        # Log the error and return a friendly message
        print(f"Error generating response: {str(e)}")
        error_response = "I'm having a moment processing that! But I'm still here for you. Could you share more about how you're feeling? ✨"
        chat_history.append({"user": user_message, "kozy": error_response})
        session['chat_history'] = chat_history
        save_chat_to_firebase(session['uid'], user_message, error_response)
        return jsonify({"response": error_response, "has_more": False})

@app.route('/get_next_message', methods=['GET'])
def get_next_message():
    """Return the next message in the queue with a simulated typing delay"""
    if 'uid' not in session:
        return jsonify({"error": "Not logged in"}), 401
    
    # Get pending messages
    pending_messages = session.get('pending_messages', [])
    
    if not pending_messages:
        return jsonify({"done": True})
    
    try:
        # Pop the next message
        next_message = pending_messages.pop(0)
        session['pending_messages'] = pending_messages
        
        # Calculate a realistic typing delay based on message length
        char_count = len(str(next_message))
        typing_delay = min(max(800, char_count * random.randint(20, 40)), 3000)  # Between 0.8-3 seconds
        
        # Save this message to chat history and Firebase
        chat_history = get_session_history()
        
        # Get user's current emotion if available
        user_emotion = None
        if 'user_tracking' in session and 'detected_emotions' in session['user_tracking'] and session['user_tracking']['detected_emotions']:
            user_emotion = session['user_tracking']['detected_emotions'][-1]
        
        chat_history.append({"user": "", "kozy": next_message, "emotion": user_emotion})
        session['chat_history'] = chat_history
        save_chat_to_firebase(session['uid'], "", next_message)
        
        return jsonify({
            "response": next_message,
            "typing_delay": typing_delay,
            "has_more": len(pending_messages) > 0,
            "emotion": user_emotion
        })
    except Exception as e:
        print(f"Error in get_next_message: {str(e)}")
        return jsonify({"error": "Error processing message", "done": True})

if __name__ == '__main__':
    app.run(debug=True,host="0.0.0.0", port=7000)
