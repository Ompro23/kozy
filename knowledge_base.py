import json
import os
import re
import random

class KnowledgeBase:
    def __init__(self):
        self.faqs = {
            "mental health": [
                {"q": "How can I manage stress?", 
                 "a": "Managing stress can involve several strategies like deep breathing, regular exercise, adequate sleep, setting boundaries, and practicing mindfulness. Would you like more specific techniques for your situation?"},
                {"q": "What are signs of anxiety?", 
                 "a": "Common signs of anxiety include excessive worry, restlessness, feeling on edge, fatigue, difficulty concentrating, irritability, muscle tension, and sleep problems. Are you noticing any of these symptoms?"},
                {"q": "How to improve mood?", 
                 "a": "Improving your mood can involve physical activity, spending time in nature, connecting with loved ones, practicing gratitude, and doing activities you enjoy. What kinds of activities typically help lift your spirits?"}
            ],
            "relationships": [
                {"q": "How to handle conflict?", 
                 "a": "Handling conflict effectively involves active listening, using 'I' statements, staying calm, focusing on the problem rather than the person, and looking for compromise. Is there a specific conflict you're dealing with?"},
                {"q": "Signs of a healthy relationship?", 
                 "a": "Healthy relationships typically involve mutual respect, trust, honesty, good communication, support for each other's independence, and the ability to resolve conflicts constructively. How would you describe your relationship?"},
                {"q": "How to set boundaries?", 
                 "a": "Setting boundaries involves identifying your limits, communicating them clearly and directly, being consistent, preparing for pushback, and practicing self-care. Would you like help setting a specific boundary?"}
            ],
            "work": [
                {"q": "How to handle work stress?", 
                 "a": "Managing work stress can involve prioritizing tasks, taking breaks, setting realistic expectations, communicating with your manager, and maintaining work-life balance. Which area do you struggle with most?"},
                {"q": "Dealing with difficult colleagues?", 
                 "a": "When dealing with difficult colleagues, try to understand their perspective, focus on the issue not the person, communicate assertively, set boundaries, and seek mediation if needed. What specific challenges are you having?"},
                {"q": "Managing workload?", 
                 "a": "To manage workload effectively, try prioritizing tasks, breaking projects into smaller steps, learning to delegate, setting realistic deadlines, and communicating with your manager about capacity. Would you like more specific advice?"}
            ],
            "boredom": [
                {"q": "Activities for boredom?",
                 "a": "When feeling bored, try engaging your mind with reading, learning something new, creative activities like drawing or writing, or physical exercise. Which of these sounds most appealing to you?"},
                {"q": "Productive ways to use free time?",
                 "a": "Free time can be used to develop a new skill, work on a personal project, reach out to friends, or practice self-care. Is there something you've been wanting to try?"}
            ],
            "success": [
                {"q": "How to celebrate achievements?",
                 "a": "Celebrating achievements helps reinforce positive behavior. Consider treating yourself to something special, sharing your success with others, or simply taking time to acknowledge your hard work. How do you usually celebrate your wins?"},
                {"q": "Handling impostor syndrome?",
                 "a": "Many people feel like impostors even when successful. Remember your accomplishments, accept praise, talk about your feelings, and focus on the value you provide. Do you sometimes feel you don't deserve your success?"}
            ]
        }
        
        # Replace external resources with BeFriends app features
        self.app_features = {
            "self_reflection": [
                {"name": "Mood Diary", "feature": "diary", "description": "Write in your diary and get a sentiment analysis score to track your emotional patterns"},
                {"name": "Color Analysis", "feature": "color_analysis", "description": "Take our color test to receive a detailed personality report that may provide new insights"}
            ],
            "connection": [
                {"name": "Listeners Chat", "feature": "listeners", "description": "Connect with our trained listeners who can provide additional emotional support"},
                {"name": "Community Reels", "feature": "reels", "description": "Watch short, uplifting videos from our community that might boost your mood"}
            ],
            "relaxation": [
                {"name": "Candle Store", "feature": "candle_store", "description": "Browse our selection of aromatherapy candles designed to create a calming environment"},
                {"name": "Guided Meditation", "feature": "meditation", "description": "Try a quick guided meditation to help center yourself"}
            ],
            "emergency": [
                {"name": "Crisis Support", "feature": "crisis_support", "description": "Connect immediately with specialized support resources"},
                {"name": "Wellness Check", "feature": "wellness_check", "description": "Take a quick wellness assessment to receive personalized coping strategies"}
            ]
        }
        
        # Emotion-specific response templates for more personalized interactions
        self.emotion_responses = {
            "happy": [
                "That's fantastic news! I'm so happy for you! 🎉 {follow_up_question}",
                "Wow, that's something to celebrate! I'm genuinely thrilled to hear this! ✨ {follow_up_question}",
                "That's wonderful! It's great to see good things happening for you! 🌟 {follow_up_question}",
                "I'm so glad to hear that! You deserve this moment of joy! ☺️ {follow_up_question}",
                "That's really something to be proud of! Congratulations! 🎊 {follow_up_question}"
            ],
            "sad": [
                "I'm sorry you're feeling this way. It sounds really difficult right now. {follow_up_question}",
                "That's tough to deal with. I'm here to listen if you want to talk more about what's got you feeling down. {follow_up_question}",
                "I can hear that you're going through a hard time. Sometimes just expressing these feelings can help a little. {follow_up_question}",
                "It's okay to feel sad sometimes. Would sharing more about what's happening help you process it? {follow_up_question}",
                "I'm here with you during this difficult time. Your feelings are valid and important. {follow_up_question}"
            ],
            "angry": [
                "I understand why you'd feel frustrated about that. It sounds genuinely aggravating. {follow_up_question}",
                "That would annoy me too! It's completely valid to feel upset about this situation. {follow_up_question}",
                "I can see why that would make you angry. Sometimes acknowledging these feelings is the first step. {follow_up_question}",
                "That sounds really frustrating to deal with. I'm here to listen as you work through these feelings. {follow_up_question}",
                "It makes sense that you're feeling upset about this. Would talking more about it help? {follow_up_question}"
            ],
            "excited": [
                "That sounds amazing! I'm excited for you too! 🎉 {follow_up_question}",
                "How wonderful! Your enthusiasm is contagious! ✨ {follow_up_question}",
                "That's fantastic news! I'd love to hear more about what you're looking forward to! {follow_up_question}",
                "I can feel your excitement! This sounds like such a great opportunity! 🌟 {follow_up_question}",
                "Wow! That's definitely something to be excited about! Tell me more! {follow_up_question}"
            ],
            "fear": [
                "It's completely natural to feel anxious about this. Many people feel the same way in similar situations. {follow_up_question}",
                "I understand why you're worried. Uncertainty can be really challenging to deal with. {follow_up_question}",
                "Those concerns make perfect sense. Let's talk through what's making you anxious. {follow_up_question}",
                "It's okay to feel nervous about this. Would it help to talk about specific aspects that worry you most? {follow_up_question}",
                "I hear your concern. Sometimes naming our fears can make them feel a bit more manageable. {follow_up_question}"
            ],
            "bored": [
                "Feeling a bit unstimulated? Sometimes that's actually an opportunity for something new! {follow_up_question}",
                "Having nothing to do can actually be a great moment to try something different. {follow_up_question}",
                "Those moments when we feel bored can sometimes lead to unexpected creativity. {follow_up_question}",
                "I get that feeling! Sometimes our minds just need a new challenge or experience. {follow_up_question}",
                "Boredom can be surprisingly uncomfortable, but it can also be a doorway to discovering new interests. {follow_up_question}"
            ],
            "neutral": [
                "I'd love to hear more about what's on your mind today. {follow_up_question}",
                "Thanks for sharing that with me. {follow_up_question}",
                "I appreciate you telling me about this. {follow_up_question}",
                "That's interesting to hear. {follow_up_question}",
                "I'm glad you're sharing this with me. {follow_up_question}"
            ]
        }
        
        # Follow-up questions based on emotion
        self.follow_up_questions = {
            "happy": [
                "What are you most excited about with this news?",
                "How are you planning to celebrate?",
                "Has this been something you've been working toward for a while?",
                "Who was the first person you shared this news with?",
                "What does this mean for you moving forward?"
            ],
            "sad": [
                "Would you like to talk more about what's making you feel this way?",
                "What's been the hardest part to deal with?",
                "Is there anything specific that might help you feel a little better right now?",
                "Have you been feeling this way for a while, or is it more recent?",
                "Would it help to talk about some small steps that might make things easier?"
            ],
            "angry": [
                "What exactly happened that frustrated you the most?",
                "Have you had a chance to process these feelings yet?",
                "What would a good resolution look like for you?",
                "Is there a particular part of the situation that feels most unfair?",
                "Is there something I can do to help you with this situation?"
            ],
            "excited": [
                "Tell me more about what you're looking forward to!",
                "How long have you been anticipating this?",
                "What aspect are you most excited about?",
                "How are you preparing for this?",
                "What are you most looking forward to about this?"
            ],
            "fear": [
                "What specifically feels most worrying to you?",
                "What has helped you manage similar feelings in the past?",
                "Is there a particular outcome you're concerned about?",
                "Would it help to talk about some strategies for handling this?",
                "On a scale of 1-10, how anxious are you feeling about this right now?"
            ],
            "bored": [
                "What kinds of activities usually capture your interest?",
                "Is there something new you've been wanting to try?",
                "Would you prefer something active or something more relaxing right now?",
                "Have you considered trying one of our mindfulness activities?",
                "What's something you enjoy that you haven't done in a while?"
            ],
            "neutral": [
                "How has your day been going so far?",
                "Is there anything specific on your mind today?",
                "What would be most helpful for us to talk about?",
                "How are you feeling right now?",
                "What brought you to our conversation today?"
            ]
        }
        
        # Track suggested resources and FAQs to avoid repetition
        self.suggested_features = set()
        self.suggested_faqs = set()
        self.conversation_context = {
            "last_emotion": None,
            "emotion_history": [],
            "topic_history": [],
            "feature_suggestion_count": 0
        }
    
    def find_relevant_faq(self, message, emotion=None, chat_history=None):
        """Find FAQs relevant to the user's message and emotional state, avoiding repetition"""
        message = message.lower()
        relevant_faqs = []
        
        # Track this emotion
        self.conversation_context["last_emotion"] = emotion
        self.conversation_context["emotion_history"].append(emotion)
        if len(self.conversation_context["emotion_history"]) > 5:
            self.conversation_context["emotion_history"] = self.conversation_context["emotion_history"][-5:]
        
        # Expanded keywords for better topic detection
        category_keywords = {
            "mental health": ["anxiety", "stress", "depression", "mental health", "therapy", "mood", "emotion", 
                            "feeling", "sad", "worried", "overwhelm", "anxious", "nervous", "tense", "pressure", 
                            "burned out", "exhausted", "drained", "down", "upset"],
            "relationships": ["relationship", "partner", "friend", "family", "boyfriend", "girlfriend", "husband", 
                            "wife", "marriage", "date", "conflict", "team", "colleague", "coworker", "fight", 
                            "argue", "misunderstand", "communicate", "trust"],
            "work": ["work", "job", "boss", "colleague", "career", "workplace", "workload", "task", "project", 
                    "manager", "coworker", "promotion", "deadline", "meeting", "presentation", "client", 
                    "responsibility", "performance", "stress"],
            "boredom": ["bored", "boring", "nothing to do", "idle", "unoccupied", "free time", "unstimulated", 
                        "dull", "monotonous", "uninteresting"],
            "success": ["success", "achievement", "accomplish", "promotion", "celebrate", "proud", "recognition", 
                        "reward", "win", "achieve", "goal", "milestone", "proud"]
        }
        
        # Extract keywords from message for topic tracking
        message_words = set(re.findall(r'\b\w+\b', message))
        detected_topics = set()
        
        # Detect categories and track topics
        relevant_categories = []
        for category, keywords in category_keywords.items():
            if any(keyword in message for keyword in keywords):
                relevant_categories.append(category)
                detected_topics.add(category)
        
        # Update topic history
        for topic in detected_topics:
            if topic not in self.conversation_context["topic_history"]:
                self.conversation_context["topic_history"].append(topic)
        
        # If no direct category matches, use emotion as a guide
        if not relevant_categories and emotion:
            if emotion in ["sad", "fear"]:
                relevant_categories.append("mental health")
            elif emotion == "angry" and any(word in message for word in ["person", "people", "friend", "they", "team"]):
                relevant_categories.append("relationships")
            elif emotion == "happy" or emotion == "excited":
                relevant_categories.append("success")
            elif emotion == "bored":
                relevant_categories.append("boredom")
        
        # Special case: don't suggest FAQs for certain patterns
        if len(message_words) <= 3 or message.endswith('?'):
            return []
            
        # Skip FAQ suggestions for happy/excited emotions unless explicitly asking for information
        if (emotion in ["happy", "excited"]) and not any(x in message for x in ["how to", "how do", "advice", "help", "suggestion"]):
            return []
            
        # Get FAQs from relevant categories
        candidate_faqs = []
        for category in relevant_categories:
            for faq in self.faqs.get(category, []):
                # Skip already suggested FAQs
                faq_key = faq["q"][:30]  
                if faq_key not in self.suggested_faqs:
                    candidate_faqs.append(faq)
        
        # If no unseen FAQs, reset tracking to avoid getting stuck
        if not candidate_faqs and len(self.suggested_faqs) > 0:
            if len(relevant_categories) > 0:
                self.suggested_faqs.clear()
                # Try again with cleared history
                for category in relevant_categories:
                    candidate_faqs.extend(self.faqs.get(category, []))
        
        # Score FAQs by relevance
        if candidate_faqs:
            scored_faqs = []
            for faq in candidate_faqs:
                score = 0
                # Match specific words
                for word in re.findall(r'\b\w+\b', faq["q"].lower()):
                    if word in message and len(word) > 3:  # Only count meaningful words
                        score += 2
                    # Emotion-relevant boosting
                    if emotion == "sad" and word in ["improve", "help", "feel", "better"]:
                        score += 1
                    elif emotion == "angry" and word in ["handle", "manage", "difficult", "conflict"]:
                        score += 1
                    elif emotion == "fear" and word in ["anxiety", "worry", "stress", "manage"]:
                        score += 1
                scored_faqs.append((faq, score))
            
            # Sort by relevance score and take top
            scored_faqs.sort(key=lambda x: x[1], reverse=True)
            
            # Take top FAQ if relevance is high enough
            if scored_faqs and scored_faqs[0][1] >= 2:
                top_faq = scored_faqs[0][0]
                self.suggested_faqs.add(top_faq["q"][:30])
                relevant_faqs = [top_faq]
        
        return relevant_faqs
    
    def get_app_feature(self, emotion, message, chat_history=None):
        """Get appropriate app feature suggestion based on emotion, message, and conversation context"""
        previously_suggested = self.suggested_features
        
        # Track suggestions to avoid repetition
        self.conversation_context["feature_suggestion_count"] += 1
        
        # Check chat history for recently mentioned topics to personalize feature recommendations
        recent_topics = set()
        recurring_topics = set()
        
        if chat_history and len(chat_history) > 0:
            # Analyze recent messages for topic frequency
            last_messages = chat_history[-5:] if len(chat_history) >= 5 else chat_history
            topic_counts = {}
            
            for entry in last_messages:
                if 'user' in entry and entry['user']:
                    user_msg = entry['user'].lower()
                    
                    # Extract topics from user messages
                    if "lonely" in user_msg or "alone" in user_msg or "talk" in user_msg:
                        recent_topics.add("connection")
                        topic_counts["connection"] = topic_counts.get("connection", 0) + 1
                        
                    if "stress" in user_msg or "relax" in user_msg or "calm" in user_msg:
                        recent_topics.add("relaxation")
                        topic_counts["relaxation"] = topic_counts.get("relaxation", 0) + 1
                        
                    if "feel" in user_msg or "emotion" in user_msg or "understand" in user_msg:
                        recent_topics.add("self_reflection")
                        topic_counts["self_reflection"] = topic_counts.get("self_reflection", 0) + 1
            
            # Identify recurring topics (mentioned 2+ times)
            for topic, count in topic_counts.items():
                if count >= 2:
                    recurring_topics.add(topic)
        
        # Don't suggest features too often - adjusted to be less frequent (20% of messages)
        if self.conversation_context["feature_suggestion_count"] % 5 != 0:
            return None
        
        # Crisis keywords trigger emergency features regardless of frequency rules
        crisis_keywords = ["suicide", "kill myself", "end my life", "want to die", "hurt myself", "harming", "end it all"]
        if any(keyword in message.lower() for keyword in crisis_keywords):
            feature_category = "emergency"
            feature_options = self.app_features.get(feature_category, [])
            # Critical safety features should always be shown regardless of repetition
            return feature_options[0] if feature_options else None
        
        # Map emotions to feature categories with BeFriends-specific mappings
        emotion_to_feature = {
            "sad": ["connection", "relaxation", "self_reflection"],
            "fear": ["relaxation", "connection", "self_reflection"],
            "angry": ["relaxation", "self_reflection", "connection"],
            "happy": ["connection", "self_reflection"],  # Happy users might enjoy Reels or Diary
            "excited": ["connection", "self_reflection"],  # Excited users might enjoy sharing via Reels
            "bored": ["connection", "relaxation", "self_reflection"],  # Bored users could enjoy any feature
            "neutral": ["self_reflection", "connection", "relaxation"]
        }
        
        # Get relevant feature categories for this emotion
        relevant_categories = emotion_to_feature.get(emotion, ["self_reflection", "connection"])
        
        # Prioritize recurring topics from conversation history
        if recurring_topics:
            for topic in recurring_topics:
                if topic in self.app_features:
                    relevant_categories.insert(0, topic)
        
        # Specific keywords in current message might override emotion-based suggestions
        message_lower = message.lower()
        if "understand" in message_lower or "feeling" in message_lower or "emotions" in message_lower:
            relevant_categories.insert(0, "self_reflection")
        if "alone" in message_lower or "talk" in message_lower or "lonely" in message_lower:
            relevant_categories.insert(0, "connection")
        if "stress" in message_lower or "relax" in message_lower or "calm" in message_lower:
            relevant_categories.insert(0, "relaxation")
            
        # Try to find a feature from relevant categories that hasn't been suggested yet
        for category in relevant_categories:
            feature_options = self.app_features.get(category, [])
            for feature in feature_options:
                feature_key = f"{category}_{feature['name']}"
                if feature_key not in previously_suggested:
                    self.suggested_features.add(feature_key)
                    return feature
        
        # If all relevant features have been suggested, pick a random one
        # But first check if we've suggested too many already
        if len(previously_suggested) >= 8:
            # Reset tracking if we've suggested many features
            self.suggested_features.clear()
            # And skip this time to avoid being too pushy
            return None
            
        # Try a random feature from the first relevant category
        if relevant_categories and self.app_features.get(relevant_categories[0]):
            random_feature = random.choice(self.app_features[relevant_categories[0]])
            return random_feature
            
        return None
    
    def get_personality_response(self, message, emotion, features=None, chat_history=None):
        """Generate a personality-driven response based on emotion and conversation context"""
        if not emotion or emotion not in self.emotion_responses:
            emotion = "neutral"
        
        # Analyze conversation context for more personalization
        conversation_depth = 0
        recurring_topics = []
        user_name = None
        
        if chat_history:
            # Calculate conversation depth
            conversation_depth = len(chat_history)
            
            # Extract user name if they've shared it
            for entry in chat_history:
                if entry.get('user'):
                    user_msg = entry['user'].lower()
                    name_matches = re.findall(r"(my name is|i am|i'm|call me) (\w+)", user_msg)
                    if name_matches:
                        potential_name = name_matches[0][1].capitalize()
                        if len(potential_name) > 2:  # Avoid short words that aren't names
                            user_name = potential_name
                            break
            
            # Find recurring topics
            topic_mentions = {}
            for entry in chat_history:
                if entry.get('user'):
                    user_msg = entry['user'].lower()
                    
                    # Check for topic keywords
                    for topic, keywords in {
                        "work": ["work", "job", "boss", "career", "colleague"],
                        "relationships": ["friend", "partner", "family", "relationship"],
                        "self-care": ["self", "care", "health", "wellness"],
                        "emotions": ["feel", "emotion", "mood", "happy", "sad", "angry"]
                    }.items():
                        if any(keyword in user_msg for keyword in keywords):
                            topic_mentions[topic] = topic_mentions.get(topic, 0) + 1
            
            # Topics mentioned more than once are recurring
            recurring_topics = [topic for topic, count in topic_mentions.items() if count > 1]
        
        # Select a response template for this emotion
        template = random.choice(self.emotion_responses[emotion])
        
        # Select an appropriate follow-up question based on conversation context
        follow_up_questions = self.follow_up_questions[emotion]
        
        # For deeper conversations, use more personalized follow-ups
        if conversation_depth > 5 and recurring_topics:
            # Craft a more specific follow-up based on recurring topics
            if "work" in recurring_topics:
                follow_up = "Has anything changed at work since we last talked about it?"
            elif "relationships" in recurring_topics:
                follow_up = "How have things been developing with that relationship situation you mentioned?"
            elif "self-care" in recurring_topics:
                follow_up = "Have you been able to take some time for yourself lately?"
            else:
                follow_up = random.choice(follow_up_questions)
        else:
            follow_up = random.choice(follow_up_questions)
        
        # Add name personalization if we know their name
        if user_name and random.random() < 0.3:  # Use name occasionally, not every time
            response = template.format(follow_up_question=follow_up)
            if "?" in response and not response.startswith(user_name):
                name_parts = response.split('?', 1)
                if len(name_parts) > 1:
                    response = f"{name_parts[0]}, {user_name}?{name_parts[1]}"
            elif random.random() < 0.5:  # Sometimes add name at beginning
                response = f"{user_name}, {response[0].lower()}{response[1:]}"
        else:
            response = template.format(follow_up_question=follow_up)
        
        # If we have app features to suggest, create a second message about them
        feature_message = None
        if features:
            feature_message = f"You might want to try our {features['name']} feature - {features['description']}."
        
        # Return the response and optional feature message
        if feature_message:
            return [response, feature_message]
        else:
            return [response]
