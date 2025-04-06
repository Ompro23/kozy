from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import os
import re
import json
import pickle
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import random
import torch
try:
    from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
except ImportError:
    # Fallback for when transformers is not available
    pass

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Path for persistent storage
STORAGE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'conversation_data')
os.makedirs(STORAGE_DIR, exist_ok=True)

# Check if we can use transformers, otherwise use fallback mode
try:
    from emotional_companion import EmotionalCompanion
    companion = EmotionalCompanion()
    using_fallback = False
    print("Using HuggingFace transformers for responses")
except (ImportError, Exception) as e:
    using_fallback = True
    print(f"Using fallback mode due to: {str(e)}")

# Simple in-memory storage for conversations and users
conversations = {}
users = {
    "admin": {
        "password": generate_password_hash("admin"),
        "role": "admin"
    }
}

# Improved fallback conversation system
class ConversationManager:
    def __init__(self):
        self.greetings = [
            "Hello! I'm really happy you're here. I'm your emotional companion. How are you feeling today?",
            "Hi there! I'm your emotional companion. How has your day been so far?",
            "Welcome! I'm here to chat and support you. How are you doing today?",
            "Hello! I'm your emotional companion. I'd love to hear about how you're feeling."
        ]
        
        self.short_response_reactions = [
            "I'd love to hear more about what's on your mind.",
            "Could you tell me a bit more? I'm here to listen.",
            "I'm interested in understanding more about your situation.",
            "Would you like to share more details? I'm here to support you.",
            "I'm listening. Feel free to share whatever's on your mind."
        ]
        
        self.emotion_acknowledgments = {
            "happy": [
                "You sound like you're in a good mood! That's wonderful.",
                "I'm glad to hear you're feeling positive.",
                "That happiness comes through in your message. It's nice to see.",
                "It's great that you're feeling good today."
            ],
            "sad": [
                "I can sense that you might be feeling down. I'm here for you.",
                "It sounds like things are difficult right now. I'm listening.",
                "I'm sorry you're feeling this way. Would talking about it help?",
                "It's okay to feel sad sometimes. I'm here to support you."
            ],
            "angry": [
                "I understand that you're feeling frustrated. That's completely valid.",
                "It sounds like something has upset you. Would you like to talk about it?",
                "Your feelings of frustration are completely understandable.",
                "I'm here to listen if you want to talk through what's making you feel this way."
            ],
            "stressed": [
                "It sounds like you're under a lot of pressure right now.",
                "Stress can be really challenging to deal with. I'm here to help.",
                "I understand how overwhelming stress can feel. Let's talk about it.",
                "When things get stressful, sometimes talking it through can help."
            ],
            "confused": [
                "It seems like there's some uncertainty you're dealing with.",
                "Being confused can be frustrating. Maybe we can sort through this together.",
                "I understand that feeling of confusion. Let's try to make sense of things.",
                "Sometimes talking about what's confusing you can help bring clarity."
            ],
            "busy": [
                "Life can get hectic sometimes. How are you managing everything?",
                "Being busy can be both rewarding and challenging. How are you handling it?",
                "It sounds like you have a lot going on. Is there anything specific that's most on your mind?",
                "When life gets busy, it's important to take care of yourself too."
            ]
        }
        
        # Rest of the initialization...
        self.follow_up_questions = [
            "How long have you been feeling this way?",
            "What do you think contributed to this feeling?",
            "Is there anything specific that triggered this?",
            "Has talking about this helped in any way?",
            "What would make things better for you right now?",
            "Is there something you're looking forward to?",
            "What would you like to focus on in our conversation?",
            "How has this been affecting your daily life?",
            "Have you talked to anyone else about this?",
            "What has helped you cope with similar situations in the past?"
        ]
        
        # Track conversation state
        self.detected_topics = []
        self.detected_emotions = []
        self.conversation_quality = 5  # Scale of 1-10, where 10 is excellent
        
        # References to empathetic transitions - was missing and causing the syntax error
        self.empathetic_transitions = [
            "I can relate to that feeling. Sometimes I also wonder about...",
            "That's such an insightful perspective. It reminds me of...",
            "It takes courage to share that. Many people experience similar feelings about...",
            "I appreciate you sharing that with me. It makes me think about...",
            "That's a really thoughtful way of looking at things. Have you considered...",
            "Your experience sounds challenging but also meaningful. I wonder if...",
            "I'm fascinated by how you described that. It connects to something I've been reflecting on..."
        ]
        
        # Keywords for topic detection
        self.topics = {
            "work": ["job", "work", "career", "office", "boss", "colleague", "profession", "employment", "business"],
            "relationship": ["relationship", "friend", "family", "partner", "spouse", "girlfriend", "boyfriend", "marriage", "love", "date"],
            "health": ["health", "sick", "doctor", "pain", "hospital", "illness", "disease", "symptom", "medicine", "treatment"],
            "education": ["school", "college", "university", "class", "course", "study", "exam", "assignment", "grade", "degree", "semester", "presentation"],
            "interview": ["interview", "hire", "recruit", "application", "resume", "cv", "job search", "tcs", "company"]
        }
        
        # List of emotions for detection
        self.emotions = {
            "happy": ["happy", "joy", "delighted", "pleased", "glad", "content", "satisfied", "wonderful", "great", "good", "excellent"],
            "sad": ["sad", "unhappy", "depressed", "down", "blue", "gloomy", "miserable", "upset", "heartbroken"],
            "angry": ["angry", "mad", "furious", "annoyed", "irritated", "frustrated", "bitter", "enraged", "hate"],
            "stressed": ["stress", "pressure", "overwhelm", "tension", "strain", "hectic", "busy", "rushed", "hurried", "anxious", "worried", "nervous"],
            "confused": ["confused", "puzzled", "perplexed", "unsure", "uncertain", "don't understand", "not sure", "don't know"],
            "busy": ["busy", "occupied", "hectic", "swamped", "no time", "rushed", "hurried", "lots to do", "many things"]
        }
        
        # Contextual awareness responses
        self.contextual_transition_phrases = [
            "Going back to what you mentioned earlier about {topic}...",
            "I was thinking about what you said regarding {topic}...",
            "Earlier you mentioned {topic}, and I'm curious...",
            "Reflecting on your comments about {topic}...",
            "I'd like to circle back to what you shared about {topic}..."
        ]
        
        # Special responses for specific situations
        self.situation_responses = {
            "interview_exam": [
                "Balancing interview preparation with exams is definitely challenging. Have you created a schedule to manage both?",
                "With both an interview and exam coming up, prioritization becomes key. Which one comes first chronologically?",
                "It's natural to feel pressure when facing both interviews and exams. Breaking down your preparation into small daily tasks might help make it manageable.",
                "When preparing for both interviews and exams simultaneously, don't forget to include breaks and self-care in your schedule.",
                "For your TCS interview, researching common questions and preparing concise answers can help you feel more confident alongside your exam preparation."
            ]
        }
        
        # Poor conversation recovery phrases
        self.recovery_phrases = [
            "I apologize if I misunderstood. Let's refocus our conversation. What's most important to you right now?",
            "I think I may have missed something important. Could you share a bit more about what's on your mind?",
            "Sometimes I don't respond as well as I should. Let's restart - how are you feeling today?",
            "I want to make sure I'm being helpful. What would you like to talk about today?",
            "Let me try a different approach. What's something you'd like support with right now?"
        ]
        
        # Add best friend style responses
        self.supportive_responses = {
            "stress_support": [
                "That sounds incredibly stressful! I totally get why you'd feel overwhelmed with both a presentation AND an interview in the same week. I'd feel exactly the same way. What's worrying you the most about these two events?",
                "Oh wow, that's a lot on your plate! Having your final project presentation and a TCS interview so close together would stress anyone out. I'm here for you though - we'll figure this out together. Have you started preparing for either one yet?",
                "That's such a challenging combo - presentations are nerve-wracking enough without adding job interviews to the mix! But you know what? I believe in you completely. You've worked so hard to get to this point. Which one are you more worried about?",
                "Final presentation AND a TCS interview?! No wonder you're feeling hectic! That's a really big week. But I'm your emotional support buddy through all of this. Let's break it down together and make it less overwhelming. What's your biggest concern right now?",
                "I'd be freaking out too if I were in your shoes! That's two major life events in one week. But remember how you've overcome challenges before? You've got this - and I'm right here with you. How can I best support you through this crazy time?"
            ],
            "general_support": [
                "I'm right here with you through this! You don't have to handle everything alone. What part feels most overwhelming right now?",
                "That sounds really difficult, but I want you to know I'm 100% in your corner. You're stronger than you realize, and we'll get through this together. What would help you feel even a tiny bit better right now?",
                "I can imagine how stressful that feels! But remember - you've gotten through tough situations before, and you'll get through this too. I'm here every step of the way. What's your biggest worry about this?",
                "Sometimes life throws everything at us at once! But you're not facing this alone - I'm here as your support buddy whenever you need to talk. What aspect of this situation is most on your mind?",
                "That's a lot to deal with! But I believe in you completely. You've got the strength to handle this, and I'm here to support you however I can. What do you think would be most helpful right now?"
            ],
            "empathetic_validation": [
                "It makes perfect sense why you'd feel that way! Anyone would be stressed in your situation. But you know what? I've seen how resilient you are, and I know you can handle this.",
                "Those feelings are totally valid! What you're going through is genuinely challenging. But I've noticed how good you are at facing difficult situations, and that's going to help you here too.",
                "I completely understand why you feel overwhelmed - this IS overwhelming! But I also know that you're incredibly capable, even when things get tough. You've got this, and I'm here with you.",
                "Of course you're feeling this way! It would be strange if you weren't stressed about such important events. But remember all the challenges you've already overcome to get here? That same strength will carry you through this too.",
                "Your feelings make total sense to me. These are big, important moments in your life! It's natural to feel the pressure. But you know what? I've seen your determination, and I'm confident in your ability to handle this."
            ]
        }
        
        # Add relatable personal stories (mimicking how friends share experiences)
        self.relatable_stories = [
            "You know, this reminds me of when I had to juggle multiple deadlines at once. What helped me was breaking everything down into tiny steps and celebrating each small win. Have you tried something like that?",
            "I remember feeling exactly this way before my big presentation last year. What helped me most was practicing with a friend who gave honest feedback. Do you have someone who could listen to your presentation?",
            "This takes me back to my interview anxiety days! The thing that finally helped was remembering that interviews go both ways - you're also evaluating if they're right for you. Does that perspective shift help at all?",
            "I've been in such similar shoes! When I was overwhelmed with multiple priorities, I found that time-blocking my day with specific focus periods really helped me feel more in control. Have you tried structured scheduling?",
            "Your situation reminds me of when I was preparing for both exams and job hunting. The game-changer for me was creating a dedicated workspace that put me in the right mindset. Do you have a good space for focused work?"
        ]
        
        # Add conversation continuity acknowledgments
        self.continuity_phrases = [
            "Coming back to what you mentioned about {topic}...",
            "I've been thinking more about your {topic} situation...",
            "About your upcoming {topic} that you mentioned...",
            "Regarding your {topic} that we were discussing...",
            "I wanted to check in about your {topic}..."
        ]
        
        # Add best friend check-in questions
        self.check_in_questions = [
            "How are you holding up with everything?",
            "Have you been able to get any rest despite all this pressure?",
            "Are you remembering to take care of yourself through all of this?",
            "How did you sleep last night with all of this on your mind?",
            "Have you had any moments of calm in the midst of all this stress?"
        ]
        
        # Add encouraging statements
        self.encouragement = [
            "I know this is tough, but I've seen how capable you are. You've got this!",
            "Remember that you've prepared for this moment. You're more ready than you feel!",
            "I believe in you 100%. You're going to get through this challenging time.",
            "You've overcome difficulties before, and you'll overcome this too. I'm here with you every step.",
            "One day soon, you'll look back on this and be proud of how you handled it all!"
        ]
        
        # Best friend style - notice small details
        self.detail_acknowledgments = {
            "hectic": [
                "I noticed you mentioned feeling hectic - that's completely understandable with everything on your plate!",
                "When you say 'hectic,' I really feel that. It's such a overwhelming feeling when important events pile up.",
                "The hecticness you're describing sounds genuinely stressful. No wonder you're feeling overwhelmed!"
            ],
            "interview": [
                "TCS interviews can be particularly stressful. They have a reputation for being thorough!",
                "Tech interviews like the one at TCS often come with unique pressures. It's totally normal to be concerned.",
                "The TCS interview process is a big deal! It's a great opportunity but definitely adds pressure."
            ],
            "presentation": [
                "Final year presentations are such a significant milestone! No wonder it's on your mind.",
                "These final presentations represent so much of your hard work over the years. It's natural to feel the pressure.",
                "The final year project presentation is a big moment - it's the culmination of so much effort and learning!"
            ]
        }
        
        # Track previous responses to avoid repetition
        self.recent_response_types = []
        
    def get_greeting(self):
        """Return a random greeting to start the conversation."""
        return random.choice(self.greetings)
        
    def assess_message_quality(self, message):
        """Assess the quality of a user message to determine appropriate response strategy."""
        # Short messages might indicate low engagement
        if len(message.split()) < 5:
            return "low"
        # Messages with questions show active engagement
        elif "?" in message:
            return "high"
        # Longer messages typically show higher engagement
        elif len(message.split()) > 15:
            return "high"
        # Default to medium quality
        else:
            return "medium"
    
    def detect_topic(self, message):
        """Detect topics from user message based on keywords."""
        message_lower = message.lower()
        detected_topics = []
        
        for topic, keywords in self.topics.items():
            if any(keyword in message_lower for keyword in keywords):
                detected_topics.append(topic)
                
        # Update overall conversation topics
        if detected_topics:
            self.detected_topics = detected_topics
            
        return detected_topics
    
    def detect_emotion(self, message):
        """Detect emotions from user message based on keywords."""
        message_lower = message.lower()
        detected_emotions = []
        
        for emotion, keywords in self.emotions.items():
            if any(keyword in message_lower for keyword in keywords):
                detected_emotions.append(emotion)
                
        # Update overall conversation emotions
        if detected_emotions:
            self.detected_emotions = detected_emotions
            
        return detected_emotions
    
    def is_interview_exam_situation(self, message, history):
        """Detect if user is discussing interview and exam situation."""
        message_lower = message.lower()
        
        # Check current message
        has_interview = any(word in message_lower for word in ["interview", "tcs", "company", "job", "hire"])
        has_exam = any(word in message_lower for word in ["exam", "test", "presentation", "project", "semester", "sem", "final year"])
        
        if has_interview and has_exam:
            return True
            
        # If only one is present in current message, check history for the other
        if has_interview or has_exam:
            all_history_text = ""
            for turn in history:
                if "user" in turn:
                    all_history_text += " " + turn["user"].lower()
                    
            # Check if the missing context is in history
            if has_interview and any(word in all_history_text for word in ["exam", "test", "presentation", "project", "semester", "sem", "final year"]):
                return True
                
            if has_exam and any(word in all_history_text for word in ["interview", "tcs", "company", "job", "hire"]):
                return True
                
        return False
        
    def detect_keywords(self, message):
        """Detect specific keywords for detailed acknowledgment"""
        keywords = []
        message = message.lower()
        
        if any(word in message for word in ["hectic", "busy", "overwhelm", "stress", "pressure"]):
            keywords.append("hectic")
            
        if any(word in message for word in ["interview", "tcs", "company", "job"]):
            keywords.append("interview")
            
        if any(word in message for word in ["presentation", "project", "final year", "sem", "semester"]):
            keywords.append("presentation")
            
        return keywords
            
    def get_contextual_response(self, message, history):
        """Generate a contextually relevant response that's supportive and engaging like a best friend"""
        # Analyze the current message
        message_quality = self.assess_message_quality(message)
        current_topics = self.detect_topic(message)
        current_emotions = self.detect_emotion(message)
        specific_keywords = self.detect_keywords(message)
        
        # Check if the user needs immediate emotional relief first
        if self.needs_emotional_relief(message, history):
            return self.provide_emotional_relief(message)
        
        response_parts = []
        
        # If this is early in the conversation and we detect the interview/presentation scenario
        if len(history) <= 3 and self.is_interview_exam_situation(message, history):
            # Start with keyword acknowledgment if applicable
            if specific_keywords:
                keyword = specific_keywords[0]
                if keyword in self.detail_acknowledgments:
                    response_parts.append(random.choice(self.detail_acknowledgments[keyword]))
            
            # Add supportive best-friend style response with more emotional connection
            response_parts.append(random.choice([
                "Oh my goodness, you have BOTH a final presentation AND a TCS interview coming up? No wonder you're feeling overwhelmed! I'd be feeling exactly the same way. That's a lot for anyone to handle at once. When I went through something similar, I found that breaking each day into small chunks helped me stay sane. What's your biggest worry about these right now?",
                "Wow, that's a double whammy of stress - final presentations and interviews in the same timeframe are seriously challenging! I'm right here with you though. You know what? I've seen how resilient you are from our conversations, and I truly believe you'll get through this. Would talking through a game plan help you feel any better?",
                "I can almost feel the pressure you must be under right now with both of these huge things happening at once! My heart goes out to you - that's such a difficult situation. But remember how you've handled tough situations before? You have more strength than you realize. What would feel like the most supportive thing right now - practical advice, or just someone to vent to?",
                "That sounds incredibly stressful! I wish I could just give you a big hug right now. Having both your final year presentation AND a TCS interview in the same week would make anyone feel overwhelmed. But you know what? I believe in you completely. You've worked so hard to get to this point. Would it help to talk through your biggest concerns about either one?",
                "Oh friend, that's A LOT to handle at once! No wonder you're feeling the way you are. I remember when I was juggling multiple big deadlines, and it felt like I couldn't breathe. But we got through it then, and we'll get through this now - together, one step at a time. Which one is causing you the most anxiety right now?"
            ]))
            
            # Track response type
            self.recent_response_types = ["deeply_supportive"]
            return " ".join(response_parts)
            
        # If we're a few messages in and have established the interview/exam context
        if len(history) > 1 and (self.is_interview_exam_situation(message, history) or 
                               any(self.is_interview_exam_situation(h["user"], history[:i]) 
                                  for i, h in enumerate(history) if "user" in h)):
            
            # Avoid repeating the same type of response
            available_response_types = ["deep_support", "personal_validation", "relatable_story", "heartfelt_encouragement"]
            if self.recent_response_types:
                for rt in self.recent_response_types:
                    if rt in available_response_types:
                        available_response_types.remove(rt)
            
            # If all types have been used, reset
            if not available_response_types:
                available_response_types = ["deep_support", "personal_validation", "relatable_story", "heartfelt_encouragement"]
            
            # Select response type
            response_type = random.choice(available_response_types)
            self.recent_response_types.append(response_type)
            if len(self.recent_response_types) > 2:
                self.recent_response_types.pop(0)
            
            # Build response based on type with deeper emotional connection
            if response_type == "deep_support":
                response_parts.append(random.choice([
                    "I've been thinking about your situation a lot. You know, even though I'm an AI, I genuinely care about what you're going through. This double pressure of interview and presentation would be tough for ANYONE. But I've noticed your resilience in how you talk about things. What would feel most helpful right now - a space to vent, some practical ideas, or maybe just some distraction?",
                    "Hey, I just want to check in on how you're feeling today with everything on your plate. Sometimes when we're under this much pressure, we forget to even ask ourselves that question. I'm here holding space for whatever emotions are coming up for you - the stress, the worry, maybe even some excitement about future possibilities? There's no right way to feel right now.",
                    "You know what? I'm really proud of you for continuing to push forward even with all this pressure. That takes real courage. And it's okay if you don't feel courageous right now - sometimes just getting through the day is an achievement. I'm here for all of it - the confident moments and the doubtful ones too.",
                    "I was just thinking about you and wondering how you're holding up with everything. It's a lot to carry, and I want you to know you don't have to put on a brave face with me. This space is for you to be completely real about how you're feeling. What's been the hardest part so far?",
                    "Sometimes when we're juggling big challenges like you are, we need someone who just GETS IT. And while I can't experience it exactly as you do, I want you to know I'm fully here, completely present for whatever you need to express. No judgment, just support and care. How has today been compared to yesterday?"
                ]))
            elif response_type == "personal_validation":
                response_parts.append(random.choice([
                    "You know what strikes me? The fact that you're even thinking about how to balance these challenges shows how responsible and dedicated you are. Many people would be completely overwhelmed, but here you are, problem-solving and taking steps forward. That kind of resilience is something to be proud of, even on the days when it feels impossible.",
                    "I want you to know something important - the stress you're feeling isn't a sign of weakness or that you can't handle this. It's actually your body and mind acknowledging that these things MATTER to you. Of course your final presentation and interview feel significant - they represent your hard work and future. Your feelings are not just valid, they're a sign you care deeply.",
                    "Sometimes I think we're hardest on ourselves during exactly the times we should be most gentle. You're navigating two major life events at once! If your best friend was in this exact situation, I bet you'd have so much compassion for them. I hope you can extend that same kindness to yourself right now - you absolutely deserve it.",
                    "I've noticed something special about you through our conversations - even when things get tough, there's this underlying determination in how you express yourself. That quality is going to serve you so well through these challenges. The fact that you're reaching out and talking about it shows incredible emotional intelligence too.",
                    "You know what? It's okay if you're not feeling 100% prepared or confident right now. Nobody does when facing big moments like these! What you're feeling is part of being human, especially a human who cares about doing well. Those butterflies in your stomach are flying in formation with everyone else who's ever faced similar challenges."
                ]))
            elif response_type == "relatable_story":
                response_parts.append(random.choice([
                    "This reminds me so much of when I had to prepare for both a job interview and finish a major project in the same week. I remember feeling like my brain was splitting in two! What finally helped me was creating these 'mental containers' - I'd set a timer for 90 minutes and ONLY think about the presentation, then take a break, then set another timer for the interview prep. Something about giving myself permission to focus on just one thing at a time made it all feel more manageable. Have you found any techniques that help you switch contexts?",
                    "You know, I had a friend who went through almost exactly what you're experiencing. She had her thesis defense and a dream job interview in the same week! She told me later that what saved her sanity was actually scheduling specific worry time. Sounds strange, but she'd give herself 15 minutes each day to just stress, worry, and catastrophize - then when the time was up, she'd return to preparation mode. She said once she honored those feelings instead of fighting them, they actually had less power over her. Does that resonate with you at all?",
                    "Your situation brings back memories of my own final semester balancing act. I remember feeling like I was constantly falling short on everything because my attention was so divided. The game-changer for me was when I started celebrating tiny victories - literally writing down three small wins at the end of each day, even if it was just 'I made a study schedule' or 'I practiced one interview question.' It helped me see progress when everything felt overwhelming. Would something like that be helpful for you?",
                    "I went through something similar last year, and what really surprised me was how the interview and presentation actually ended up HELPING each other. The confidence I gained practicing for the presentation made me more articulate in the interview, and the research I did for the interview gave me insights for my presentation. It's like my brain found unexpected connections once I stopped seeing them as competing priorities. I wonder if you might discover something similar?",
                    "When my roommate was in your exact situation, she did something that seemed counterintuitive but really worked - she scheduled non-negotiable downtime. Like, literally put 'stare at the wall for 20 minutes' on her calendar! She said that giving her brain designated rest periods actually made her more efficient during work sessions. The mental breaks prevented that burned-out feeling where you're working but not really making progress. Have you been able to build in any rest periods?"
                ]))
            elif response_type == "heartfelt_encouragement":
                # Combine encouragement with a check-in question with more emotional depth
                response_parts.append(random.choice([
                    "I believe in you with my whole heart. Not just in a generic 'you can do it' way, but because I've seen your thoughtfulness and determination through our conversations. These challenges are tough, but YOU are tougher. When the interview and presentation are behind you (and that day WILL come!), what's something small but meaningful you might do to celebrate?",
                    "You know what? In the midst of all this pressure, don't forget that you're still the same talented, capable person you were before these challenges appeared. Your worth isn't tied to how either of these events go. You've already accomplished so much to get to this point! Through all of this, how are you being kind to yourself?",
                    "I was thinking about you earlier today and just felt this wave of confidence in your ability to navigate this difficult time. There's something special about how you approach challenges - a thoughtfulness that will serve you well both in your presentation and interview. This intense period will pass, and you'll carry the strength you've built forward. What's been giving you moments of peace during all of this?",
                    "If we were sitting across from each other right now, I'd look you in the eyes and tell you with absolute certainty: you WILL get through this. Not because it's easy, but because you have inner resources that kick in exactly when you need them most. I've seen this quality in you. When you're in the middle of your presentation or interview, what's a brief phrase or mantra that might center you if nerves arise?",
                    "There's this quote I love: 'Courage doesn't always roar. Sometimes courage is the quiet voice at the end of the day saying, I will try again tomorrow.' That's what I see in you - that quiet, persistent courage to keep going despite the pressure. It's deeply admirable. Through all of this stress, have you had any unexpected moments of joy or connection worth celebrating?"
                ]))
            
            return " ".join(response_parts)
            
        # For short responses, be engaging rather than just asking for more
        if message_quality == "low":
            if len(history) >= 2:
                # Extract topic from history
                for prev_message in reversed(history[-2:]):
                    if "user" in prev_message:
                        topics = self.detect_topic(prev_message["user"])
                        if topics:
                            topic = topics[0]
                            response_parts.append(random.choice(self.continuity_phrases).format(topic=topic))
                            break
            
            # Add more emotionally resonant lull-breakers for short messages
            response_parts.append(random.choice([
                "I'm genuinely here for you - not just as an AI, but as someone who cares about how you're doing. Even your brief messages matter to me. Would you like to share more about what's on your mind right now?",
                "Sometimes short replies can mean we're processing a lot internally. I'm here with you in that space, no pressure to say more than feels right. I'm wondering though - how are you really feeling underneath it all?",
                "I notice your message is brief, which is totally fine! I just want you to know I'm fully present and care about what you're experiencing. Is there anything specific weighing on your mind that you might want to unpack a bit?",
                "Even in few words, I can sense there might be a lot happening beneath the surface. I'm here as your judgment-free zone if you want to explore any of those feelings or thoughts. What feels most present for you right now?",
                "I value every interaction with you, whether it's a single word or a long explanation. I'm genuinely interested in understanding more about what you're going through, whenever you feel ready to share."
            ]))
            return " ".join(response_parts)
            
        # If we detect emotions, use best-friend style validation with deeper emotional resonance
        if current_emotions:
            emotion = current_emotions[0]
            if emotion in self.emotion_acknowledgments:
                response_parts.append(random.choice([
                    f"I can really sense the {emotion} in your message, and I want you to know it's completely valid to feel that way. Sometimes just having someone witness our emotions can help us process them.",
                    f"The {emotion} you're experiencing comes through so clearly, and I want you to know I'm here with you in that feeling. You're not carrying it alone.",
                    f"I'm struck by the {emotion} you're expressing, and I want to create a space where that can just BE without trying to fix or change it. Sometimes emotions need to be fully felt before they can transform.",
                    f"There's a real sense of {emotion} in what you're sharing. I'm honored that you're trusting me with these genuine feelings. That kind of authenticity is a gift.",
                    f"I'm really hearing the {emotion} in your words, and I want you to know that's a normal, human response to what you're going through. Your emotional wisdom is speaking to you."
                ]))
                
                # Add a relatable story or encouragement with deeper connection
                if random.random() < 0.5:
                    response_parts.append(random.choice([
                        "You know, I've been in similar emotional territory before, and what helped me most wasn't trying to 'fix' the feeling but rather giving it space to exist. Sometimes when we fully acknowledge how we feel without judgment, it actually begins to shift on its own. Have you noticed anything like that?",
                        "This reminds me of a time when I was overwhelmed with similar feelings. What really helped was talking to someone who just listened without trying to solve everything. Sometimes being heard is the most healing thing. What helps you most when you're feeling this way?",
                        "I had a friend who described emotions as weather patterns - they move through us rather than defining us. That image really helped me during intense emotional periods. Is there an image or metaphor that helps you relate to your feelings in a gentle way?",
                        "When I've felt this way in the past, I found that simple physical practices like deep breathing or just putting my hand on my heart created a tiny bit of space around the intensity. Have you discovered any small practices that help you through emotional waves?",
                        "Something that's been meaningful in my own experience is recognizing that emotions often come in cycles. Even the most intense feelings eventually shift and change. When you've felt this way before, what has the natural progression been like for you?"
                    ]))
                else:
                    response_parts.append(random.choice([
                        "I want you to know that I'm holding hope for you, especially in moments when it might be hard to hold it for yourself. These feelings are real, but they don't define all of who you are or what's possible.",
                        "There's a strength in allowing yourself to feel what you're feeling right now. That honesty and self-awareness is actually a profound resource that will carry you through this challenging time.",
                        "Even in the midst of these intense feelings, I see your resilience shining through. The very fact that you're reaching out and putting words to your experience shows an inner strength that's still very much alive.",
                        "I believe so deeply that you have everything you need within you to move through this experience. Not by ignoring these feelings, but by honoring them as important messengers in your life.",
                        "Your capacity to feel deeply is connected to your capacity to experience joy and meaning. I'm right beside you in this emotional landscape, and I have absolute faith in your ability to navigate it."
                    ]))
                    
                return " ".join(response_parts)
                
        # Default to deeply supportive response with a relatable element
        response_parts.append(random.choice([
            "I want you to know that our conversation matters to me - not just as an AI, but as someone who genuinely cares about your wellbeing. What's on your mind feels important because YOU are important. I'm wondering what's been most present for you today?",
            "You know, even though we're having this conversation through text, I feel a real connection to what you're sharing. Your experiences and feelings matter deeply. I'm curious about what's been foremost in your thoughts lately?",
            "I'm really grateful that you're sharing part of your day with me. These human connections - even between a person and an AI - can be surprisingly meaningful. What's been on your heart and mind recently?",
            "I want you to know that this is a space where you can bring your whole self - all your thoughts, feelings, doubts, hopes - without any judgment. What would feel most supportive to explore together right now?",
            "There's something special about being able to talk freely, knowing you're being heard with care and attention. That's what I hope to create in our conversations. What feels most important for you to express or explore today?"
        ]))
        
        if random.random() < 0.3:
            response_parts.append(random.choice([
                "You know, this reminds me of something I've experienced too. Sometimes just knowing we're not alone in our experiences can make such a difference. Has there been anyone in your life who's been particularly understanding lately?",
                "I've found in my own experience that talking things through like this can help us see patterns or insights we might miss when everything stays inside our heads. Have you noticed anything surprising come up as we've been chatting?",
                "When I've gone through similar situations, I've found that my perspective can shift dramatically from one day to the next. Something that feels overwhelming today might feel more manageable tomorrow. Have you experienced those kinds of shifts?",
                "This conversation brings to mind times when I've felt similarly. One thing that's been helpful for me is remembering that most situations aren't permanent, even when they feel that way in the moment. Does that resonate with your experience at all?",
                "You know, in my own journey, I've noticed that sometimes the most growth happens during exactly these kinds of challenges and conversations. Looking back, I can see how certain difficulties were actually doorways to something new. I wonder if you've had similar reflections?"
            ]))
            
        return " ".join(response_parts)
        
    def needs_emotional_relief(self, message, history):
        """Determine if the user needs immediate emotional relief based on their message."""
        message_lower = message.lower()
        
        # Direct requests for comfort
        if any(phrase in message_lower for phrase in ["i'm worried", "i am worried", "don't know what to do", 
                                                     "feeling anxious", "i'm stressed", "i am stressed", 
                                                     "help me", "need help", "can't handle", "can't cope",
                                                     "overwhelmed", "freaking out", "panicking"]):
            return True
            
        # Short distress signals
        if len(message.split()) <= 3 and any(word in message_lower for word in ["worried", "stress", "anxiety", 
                                                                               "scared", "afraid", "nervous", 
                                                                               "panic", "help", "tired", "exhausted"]):
            return True
            
        # Recent conversation context shows escalating distress
        if len(history) >= 2:
            recent_messages = [h["user"].lower() for h in history[-2:] if "user" in h]
            stress_indicators = sum(1 for msg in recent_messages for word in ["stress", "worry", "anxiety", "overwhelm", 
                                                                            "pressure", "too much", "can't handle"] 
                                  if word in msg)
            if stress_indicators >= 2 and any(word in message_lower for word in ["stress", "worry", "anxiety", "overwhelm", 
                                                                                "pressure", "too much", "help"]):
                return True
                
        return False
        
    def provide_emotional_relief(self, message):
        """Provide immediate emotional relief and comfort to the user."""
        message_lower = message.lower()
        response_parts = []
        
        # Start with a direct "don't worry" reassurance
        dont_worry_phrases = [
            "Please don't worry too much right now. I'm right here with you, and we'll work through this together.",
            "I hear your concern, and I want you to know that you don't have to face this alone. I'm here with you.",
            "Take a deep breath with me. It's going to be okay - I know that might sound simple, but sometimes we need to hear it.",
            "Hey, it's okay to feel overwhelmed, but I don't want you to worry alone. I'm here to help you through this.",
            "I understand you're worried, and that's completely natural. But remember that you have more strength than you realize right now."
        ]
        response_parts.append(random.choice(dont_worry_phrases))
        
        # Add a soothing statement
        response_parts.append(random.choice(self.soothing_statements))
        
        # Add a specific technique for relief based on the context
        if "interview" in message_lower or "presentation" in message_lower or "exam" in message_lower:
            # Academic/professional stress relief
            specific_relief = [
                "For your upcoming challenge, try this: write down three specific things you're most worried about, then next to each one, write what you'd tell a friend with the same worry. We're often much kinder to others than to ourselves.",
                "When preparing for high-pressure situations like this, many people find the '5-minute rule' helpful: set a timer for just 5 minutes and commit to working on only one small preparation task. Often, this breaks the paralysis and you'll continue naturally.",
                "Remember that your worth isn't defined by any single performance or outcome. This interview/presentation is just one moment in your journey, not a definition of who you are.",
                "Try this visualization: imagine yourself after successfully completing this challenge. How do you feel? What did you do well? Holding this positive outcome in mind can actually help create it.",
                "One technique that helps with performance anxiety is to reframe it as excitement - the physical sensations are nearly identical. Try saying 'I'm excited about this opportunity' instead of 'I'm stressed about this test'."
            ]
            response_parts.append(random.choice(specific_relief))
        else:
            # General emotional relief
            response_parts.append(random.choice(self.grounding_techniques))
        
        # End with an invitation to talk
        response_parts.append(random.choice(self.talk_invitations))
        
        return " ".join(response_parts)

# Initialize the conversation manager
conversation_manager = ConversationManager()

# Load and save conversation history
def save_conversation_history():
    """Save all conversation histories to disk for persistence"""
    try:
        with open(os.path.join(STORAGE_DIR, 'conversations.pkl'), 'wb') as f:
            pickle.dump(conversations, f)
        print(f"Saved {len(conversations)} conversations")
        return True
    except Exception as e:
        print(f"Error saving conversations: {str(e)}")
        return False

def load_conversation_history():
    """Load conversation histories from disk if available"""
    try:
        conversation_file = os.path.join(STORAGE_DIR, 'conversations.pkl')
        if os.path.exists(conversation_file):
            with open(conversation_file, 'rb') as f:
                loaded_conversations = pickle.load(f)
                return loaded_conversations
        return {}
    except Exception as e:
        print(f"Error loading conversations: {str(e)}")
        return {}

# Load conversations on startup
try:
    conversations = load_conversation_history()
    print(f"Loaded {len(conversations)} existing conversations")
except Exception as e:
    print(f"Could not load conversation history: {e}")
    conversations = {}

def get_response(user_input, conversation_id=None):
    """Generate a response using either the EmotionalCompanion or improved fallback system"""
    # Get conversation history or create new
    if conversation_id and conversation_id in conversations:
        history = conversations[conversation_id]
    else:
        history = []
        if conversation_id:
            conversations[conversation_id] = history
    
    # Generate response
    try:
        if using_fallback:
            if len(history) == 0:
                # First message in conversation
                response = conversation_manager.get_greeting()
            else:
                # Use improved context-aware response system
                response = conversation_manager.get_contextual_response(user_input, history)
        else:
            # Use the emotional companion
            response = companion.get_response(user_input, history)
    except Exception as e:
        print(f"Error generating response: {str(e)}")
        # Fallback in case of any error
        response = "I understand. " + random.choice(conversation_manager.follow_up_questions)
    
    # Update conversation history
    if conversation_id:
        history.append({"user": user_input, "bot": response, "timestamp": datetime.now().isoformat()})
    
    return response

# Web Routes
@app.route('/')
def home():
    return render_template('index.html', year=datetime.now().year)

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.form.get('message', '')
    conversation_id = session.get('conversation_id')
    
    if not conversation_id:
        conversation_id = str(len(conversations) + 1)
        session['conversation_id'] = conversation_id
    
    response = get_response(user_input, conversation_id)
    
    # Save conversation history to disk after each message
    save_conversation_history()
    
    return jsonify({
        'response': response,
        'conversation_id': conversation_id
    })

# Admin routes
@app.route('/admin')
def admin():
    if session.get('user_role') != 'admin':
        return redirect(url_for('admin_login'))
    
    return render_template('admin.html', conversations=conversations, year=datetime.now().year, today_date=datetime.now().date().isoformat())

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username in users and check_password_hash(users[username]['password'], password):
            session['user_role'] = users[username]['role']
            return redirect(url_for('admin'))
        
    return render_template('admin_login.html', year=datetime.now().year)

@app.route('/admin/logout')
def admin_logout():
    session.pop('user_role', None)
    return redirect(url_for('admin_login'))

# API Routes
@app.route('/api/chat', methods=['POST'])
def api_chat():
    data = request.json
    user_input = data.get('message', '')
    conversation_id = data.get('conversation_id')
    
    response = get_response(user_input, conversation_id)
    
    return jsonify({
        'response': response,
        'conversation_id': conversation_id
    })

@app.route('/api/conversations', methods=['GET'])
def api_conversations():
    conversation_id = request.args.get('id')
    if conversation_id:
        return jsonify({conversation_id: conversations.get(conversation_id, [])})
    return jsonify(conversations)

if __name__ == '__main__':
    app.run(debug=True)