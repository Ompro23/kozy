import re
from transformers import pipeline
import random

# Try to load the emotion classifier model
try:
    emotion_classifier = pipeline("text-classification", model="j-hartmann/emotion-english-distilroberta-base")
    print("Emotion detection model loaded successfully")
except Exception as e:
    print(f"Error loading emotion detection model: {e}")
    emotion_classifier = None

# Emotion keywords dictionary
EMOTION_KEYWORDS = {
    "happy": ["happy", "joy", "delighted", "pleased", "glad", "thrilled", "excited", "wonderful", 
              "amazing", "good", "great", "lovely", "smile", "enjoy", "fun", "love", "laugh", "fantastic"],
    
    "sad": ["sad", "unhappy", "depressed", "miserable", "heartbroken", "down", "blue", "upset", 
            "disappointed", "regret", "lonely", "hurt", "sorrow", "grief", "crying", "tears"],
    
    "angry": ["angry", "mad", "furious", "outraged", "annoyed", "irritated", "frustrated", 
              "upset", "enraged", "hate", "dislike", "resentful", "fed up", "pissed"],
    
    "excited": ["excited", "eager", "enthusiastic", "looking forward", "can't wait", 
                "thrilled", "pumped", "energetic", "keen", "psyched", "hyped"],
    
    "fear": ["afraid", "scared", "frightened", "terrified", "anxious", "worried", "nervous", 
             "paranoid", "uneasy", "dread", "panic", "horror", "terror", "concern"],
    
    "bored": ["bored", "uninterested", "tired", "dull", "boring", "nothing to do", "monotonous", 
              "mundane", "tedious", "repetitive", "same old", "unexciting"]
}

# Contextual phrases that modify emotion interpretation
CONTEXTUAL_MODIFIERS = {
    "negation": ["not", "don't", "doesn't", "didn't", "isn't", "aren't", "wasn't", "weren't",
                 "no", "never", "none", "nobody", "nothing", "nowhere"],
    
    "intensifiers": ["very", "really", "extremely", "incredibly", "absolutely", "completely", 
                     "totally", "utterly", "so", "too", "quite", "particularly", "especially"],
    
    "diminishers": ["slightly", "somewhat", "a bit", "a little", "kind of", "sort of", 
                    "not very", "not too", "hardly", "barely", "scarcely", "only"]
}

def detect_emotion_keywords(text):
    """Detect emotions based on keyword matches"""
    text_lower = text.lower()
    
    # Count keyword matches for each emotion
    emotion_scores = {}
    for emotion, keywords in EMOTION_KEYWORDS.items():
        count = 0
        for keyword in keywords:
            # Check for exact word matches (with word boundaries)
            matches = re.findall(r'\b' + re.escape(keyword) + r'\b', text_lower)
            count += len(matches)
        
        # Only include emotions with matches
        if count > 0:
            emotion_scores[emotion] = count
    
    # Check for negations that might flip emotion detection
    for negation in CONTEXTUAL_MODIFIERS["negation"]:
        if re.search(r'\b' + re.escape(negation) + r'\b', text_lower):
            # If negation found near emotion words, adjust scoring
            for emotion in list(emotion_scores.keys()):
                for keyword in EMOTION_KEYWORDS[emotion]:
                    if re.search(r'\b' + re.escape(negation) + r'.*?\b' + re.escape(keyword) + r'\b', text_lower) or \
                       re.search(r'\b' + re.escape(keyword) + r'.*?\b' + re.escape(negation) + r'\b', text_lower):
                        # Reduce score for negated emotions
                        emotion_scores[emotion] = max(0, emotion_scores[emotion] - 1)
    
    # If no clear emotion found, return None
    if not emotion_scores:
        return None
        
    # Return the emotion with highest score
    return max(emotion_scores.items(), key=lambda x: x[1])[0]

def detect_emotion_model(text):
    """Detect emotion using pretrained model"""
    if not emotion_classifier:
        return None
        
    try:
        # The model returns a list of dict with label and score
        result = emotion_classifier(text)
        
        # Map model output to our emotion categories
        model_to_our_categories = {
            "joy": "happy",
            "sadness": "sad",
            "anger": "angry",
            "surprise": "excited",  # Approximation
            "fear": "fear",
            "disgust": "angry",     # Approximation
            "neutral": None         # No strong emotion detected
        }
        
        if result and len(result) > 0:
            predicted_label = result[0]['label']
            return model_to_our_categories.get(predicted_label, None)
            
    except Exception as e:
        print(f"Error in emotion model detection: {e}")
        
    return None

def detect_emotion(text, chat_history=None):
    """Combined emotion detection using both keywords and model"""
    # Try the model-based detection first (more accurate)
    model_emotion = detect_emotion_model(text)
    
    # Fall back to keyword detection if model fails or returns None
    keyword_emotion = detect_emotion_keywords(text)
    
    # Combine results, prioritizing model detection
    detected_emotion = model_emotion if model_emotion else keyword_emotion
    
    # If still no clear emotion, check context from previous messages
    if not detected_emotion and chat_history:
        # Look for emotion patterns in the last few messages
        recent_emotions = []
        for entry in chat_history[-3:]:  # Check last 3 messages
            if 'user' in entry and entry['user']:
                msg_emotion = detect_emotion_keywords(entry['user'])
                if msg_emotion:
                    recent_emotions.append(msg_emotion)
        
        # If consistent emotion found in history, use it as a hint
        if recent_emotions and all(emotion == recent_emotions[0] for emotion in recent_emotions):
            detected_emotion = recent_emotions[0]
    
    # If still no emotion detected, default to neutral
    return detected_emotion or "neutral"

def get_emotion_response_style(emotion, intensity=None):
    """Return response style guidelines based on detected emotion"""
    
    # Define response styles for each emotion
    response_styles = {
        "happy": {
            "tone": "cheerful and positive",
            "validation": "share in their joy and enthusiasm",
            "approach": "be upbeat but authentic",
            "emotes": ["✨", "☆", "♪", "(>ᴗ<)"]
        },
        "sad": {
            "tone": "gentle and compassionate",
            "validation": "acknowledge their feelings without trying to immediately fix them",
            "approach": "offer understanding and emotional support",
            "emotes": ["♥", "(｡•́‿•̀｡)", "(´｡• ᵕ •｡`)"]
        },
        "angry": {
            "tone": "calm and measured",
            "validation": "recognize their frustration without escalating it",
            "approach": "acknowledge what upset them and provide constructive perspective",
            "emotes": ["•᎑•", "◡‿◡"]
        },
        "excited": {
            "tone": "enthusiastic and energetic",
            "validation": "mirror their excitement and encourage sharing more",
            "approach": "be responsive and show genuine interest in what excites them",
            "emotes": ["✨", "!!", "♪"]
        },
        "fear": {
            "tone": "reassuring and steady",
            "validation": "acknowledge their concerns as legitimate",
            "approach": "provide calming perspective without dismissing their worries",
            "emotes": ["♡", "(っ.❛ ᴗ ❛.)っ"]
        },
        "bored": {
            "tone": "engaging and interesting",
            "validation": "acknowledge their state without judgment",
            "approach": "introduce new topics or perspectives to spark interest",
            "emotes": ["✧", "~"]
        },
        "neutral": {
            "tone": "friendly and conversational",
            "validation": "focus on the content of their message",
            "approach": "be attentive and responsive to the topics they mention",
            "emotes": ["✨", "~", "☆", "♥"]
        }
    }
    
    return response_styles.get(emotion, response_styles["neutral"])

def get_relevant_resources(emotion, message_text):
    """Return relevant resources based on emotion and message content"""
    resources = {
        "sad": [
            {"title": "Coping with Sadness", "description": "Practical strategies for managing feelings of sadness", "link": "https://www.mind.org.uk/"},
            {"title": "Self-Care Activities", "description": "Simple self-care practices to help improve mood", "link": "https://www.healthline.com/health/self-care"}
        ],
        "fear": [
            {"title": "Managing Anxiety", "description": "Techniques to manage anxiety and worry", "link": "https://www.anxietycanada.com/"},
            {"title": "Grounding Exercises", "description": "Quick exercises to help with anxious feelings", "link": "https://www.healthline.com/health/grounding-techniques"}
        ],
        "angry": [
            {"title": "Anger Management Techniques", "description": "Healthy ways to express and manage anger", "link": "https://www.apa.org/topics/anger/control"},
            {"title": "Conflict Resolution Strategies", "description": "Effective approaches to resolving conflicts", "link": "https://www.helpguide.org/articles/relationships-communication/conflict-resolution-skills.htm"}
        ]
    }
    
    # Check if there's a crisis situation that needs specialized resources
    crisis_keywords = ["suicide", "kill myself", "end my life", "want to die", "hurt myself"]
    if any(keyword in message_text.lower() for keyword in crisis_keywords):
        return [
            {"title": "Crisis Support", "description": "24/7 support for those experiencing a mental health crisis", "link": "https://988lifeline.org/"},
            {"title": "Emergency Resources", "description": "If you're in immediate danger, please call 911 or your local emergency number", "link": None},
            {"title": "Crisis Text Line", "description": "Text HOME to 741741 to connect with a Crisis Counselor", "link": "https://www.crisistextline.org/"}
        ]
    
    # Return resources based on emotion if available
    return resources.get(emotion, []) if emotion in resources else []
