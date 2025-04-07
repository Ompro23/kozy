import torch
import random
import re
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
from character_companion import CompanionCharacter

class EmotionalCompanion:
    """
    A wrapper class for managing the emotional companion model with enhanced conversational capabilities.
    """
    
    def __init__(self, model_name="facebook/blenderbot-400M-distill", device=None):
        """Initialize the emotional companion with the specified model."""
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
            
        print(f"Loading model on {self.device}...")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(model_name).to(self.device)
        
        # Load sentiment analysis pipeline to detect user emotions
        self.sentiment_analyzer = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")
        
        # Best friend style conversation starters and engaging questions
        self.engaging_questions = {
            "personal": [
                "What's been on your mind lately?",
                "How has your day been going so far?",
                "What's something you're looking forward to this week?",
                "Have you had any moments recently that made you smile?",
                "What's something you're really proud of accomplishing?",
                "Is there anything that's been challenging you lately?",
                "What's something that makes you feel really alive and energized?",
                "Have you tried anything new or different recently?",
                "What's something you wish more people understood about you?",
                "If you could have the perfect day tomorrow, what would it look like?"
            ],
            "reflective": [
                "How have you been growing or changing lately?",
                "What's something you've learned about yourself recently?",
                "How do you feel you've changed over the past year?",
                "What's a value that's become more important to you lately?",
                "When do you feel most authentically yourself?",
                "What's something you're trying to work through or understand better?",
                "How do you recharge when you're feeling drained?",
                "What part of your life feels most fulfilling right now?",
                "Is there something you've been wanting to change in your routine?",
                "What helps you feel grounded when things get stressful?"
            ],
            "aspirational": [
                "What's something you've always wanted to try but haven't yet?",
                "If you could master any skill overnight, what would you choose?",
                "What's a goal you're currently working toward?",
                "Is there a place you've been dreaming of visiting?",
                "What's something on your bucket list that you're most excited about?",
                "If you could have dinner with anyone, living or dead, who would it be?",
                "What kind of impact do you hope to make in the world?",
                "What would your ideal career look like if anything were possible?",
                "Is there a change you'd like to make in your life in the coming year?",
                "What's something you wish you had more time for?"
            ],
            "lighthearted": [
                "What's something that made you laugh recently?",
                "Do you have any funny stories from when you were younger?",
                "What's the most unusual food combination you secretly enjoy?",
                "If you could have any superpower, what would it be and why?",
                "What's a movie or show that always puts you in a good mood?",
                "Do you have any quirky habits or routines?",
                "What's something small that brings you a lot of joy?",
                "If your life had a soundtrack, what song would be playing right now?",
                "What's the most random skill or talent you have?",
                "If you could instantly teleport anywhere for just one day, where would you go?"
            ]
        }
        
        # Empathetic transitions for more natural conversation flow
        self.empathetic_transitions = [
            "I can relate to that feeling. Sometimes I also wonder about...",
            "That's such an insightful perspective. It reminds me of...",
            "It takes courage to share that. Many people experience similar feelings about...",
            "I appreciate you sharing that with me. It makes me think about...",
            "That's a really thoughtful way of looking at things. Have you considered...",
            "Your experience sounds challenging but also meaningful. I wonder if...",
            "I'm fascinated by how you described that. It connects to something I've been reflecting on..."
        ]
        
        # Personal keywords for extracting user information
        self.personal_keywords = {
            "job": ["work", "job", "career", "profession", "company", "office", "business", "employment"],
            "family": ["family", "mom", "dad", "mother", "father", "sister", "brother", "parent", "child", "son", "daughter", "wife", "husband"],
            "hobby": ["hobby", "enjoy", "passion", "love", "like", "interest", "leisure", "fun", "pastime", "activity"],
            "pet": ["pet", "dog", "cat", "animal", "bird", "fish", "hamster"]
        }
        
        # Pre-defined emotional responses for different sentiments
        self.emotional_responses = {
            "POSITIVE": [
                "I'm really happy to hear that! Let's keep that positive energy going.",
                "That's wonderful! I appreciate you sharing that with me.",
                "I'm glad things are going well for you!",
                "That's fantastic news! It makes me happy to hear that.",
                "How delightful! I'm genuinely thrilled for you.",
                "You've brightened my day by sharing that positive experience!",
                "That's the kind of energy we love to see! Tell me more about what's making you happy."
            ],
            "NEGATIVE": [
                "I'm sorry to hear that. Would you like to talk more about it?",
                "That sounds challenging. Remember that difficult times don't last forever.",
                "I understand that must be hard. I'm here to listen if you want to share more.",
                "I'm here for you during this difficult time. How can I help support you?",
                "It takes courage to talk about difficult feelings. I appreciate your trust in sharing this with me.",
                "Sometimes just expressing our feelings can help us process them better. Would sharing more details help you?",
                "I wish I could give you a hug right now. What might help you feel even a tiny bit better?"
            ],
            "NEUTRAL": [
                "Thanks for sharing that with me. How does that make you feel?",
                "I appreciate you telling me. Would you like to explore that topic more?",
                "That's interesting. Would you like to tell me more about it?",
                "I see. How do you feel about that situation?",
                "I'm curious to hear your perspective on this. What aspects matter most to you?",
                "That's worth discussing further. What else comes to mind when you think about this?",
                "I find your thoughts on this fascinating. Have you always felt this way about it?"
            ]
        }
        
        # Add immediate relief phrases offering comfort and reassurance
        self.relief_statements = {
            "POSITIVE": [
                "That's wonderful! Take a moment to really savor this positive feeling - you deserve it.",
                "It's so great to hear something positive! Let's hold onto this good energy together.",
                "What a lovely bright spot! Sometimes these good moments are exactly what we need to keep us going.",
                "I'm genuinely happy for you! These positive moments are worth celebrating fully.",
                "That's such uplifting news! It's a reminder that good things are always possible."
            ],
            "NEGATIVE": [
                "Please don't worry too much - I'm right here with you through this difficult time.",
                "Take a deep breath with me... that's it. Remember that this feeling won't last forever.",
                "It's okay to feel this way, but I don't want you to suffer alone. I'm here to listen whenever you need.",
                "Don't be too hard on yourself. These challenges don't define you - your resilience does.",
                "This heavy feeling will pass, I promise. Until then, let's talk through it together."
            ],
            "NEUTRAL": [
                "No matter what's on your mind, I'm here to listen without judgment.",
                "Sometimes just talking things through can bring surprising relief. That's what I'm here for.",
                "Whatever you're experiencing, you don't have to face it alone. I'm right beside you.",
                "Let's take this one step at a time together. Even small progress is still progress.",
                "I'm holding space for whatever you need right now - whether that's advice or just someone to listen."
            ]
        }
        
        # Add immediate soothing statements for when someone is highly stressed
        self.soothing_statements = [
            "Take a slow, deep breath with me right now... inhale for 4... hold for 2... exhale for 6. Sometimes just one mindful breath can create a tiny bit of space in overwhelming moments.",
            "I want you to know that whatever you're feeling right now is completely okay. There's no right or wrong way to feel, and you don't need to apologize for your emotions.",
            "Let's pause for just a moment. Place one hand on your heart if you can. Feel its steady rhythm. That's your body's reminder that you're alive and resilient, even in difficult moments.",
            "When everything feels overwhelming, try focusing on just the next 5 minutes. You don't have to figure it all out right now. What's one tiny thing that might help in just this moment?",
            "I'm right here with you through this. You don't have to carry this weight alone. Sometimes just sharing the burden makes it a little lighter."
        ]
        
        # Add immediate grounding techniques to offer quick relief
        self.grounding_techniques = [
            "When anxiety hits, try the 5-4-3-2-1 technique: Notice 5 things you can see, 4 things you can touch, 3 things you can hear, 2 things you can smell, and 1 thing you can taste. It helps bring you back to the present moment.",
            "If you're feeling overwhelmed right now, try placing your feet firmly on the ground and noticing the sensation of being supported. This simple physical awareness can help anchor you.",
            "When your mind is racing, try naming objects around you of a specific color. This gentle focus shift can interrupt anxiety spirals and bring you back to the present.",
            "If you're feeling stressed, try tensing and then relaxing each muscle group from your toes up to your head. This progressive relaxation can release physical tension you might not even realize you're holding.",
            "When everything feels chaotic, sometimes holding something cold (like an ice cube or cold water on your wrists) can create an immediate sensation that brings your attention to the present moment."
        ]
        
        # Add "talk to me" invitations that create a safe space
        self.talk_invitations = [
            "I'm here to listen without any judgment. Whatever you're going through, you can talk to me about it.",
            "Sometimes putting feelings into words can help make them more manageable. I'm here whenever you're ready to talk.",
            "You don't have to face this alone. Talk to me about what's on your mind - sometimes sharing the burden makes it lighter.",
            "I'm here as your safe space. Whatever you need to express, I'm ready to listen with care and attention.",
            "Talking things through might help bring some clarity. I'm here for you, ready to listen whenever you feel like sharing."
        ]
        
        # User information storage
        self.user_info = {}
        self.current_topics = set()
        self.current_concerns = set()
        
        # Key topics and concerns mapping
        self.topic_keywords = {
            "education": ["school", "college", "university", "class", "course", "study", "exam", "test", "presentation", "assignment", "project", "grade", "sem", "semester"],
            "career": ["job", "interview", "work", "career", "profession", "company", "office", "recruit", "hiring", "position", "role", "tcs", "infosys", "wipro", "application"],
            "stress": ["stress", "tension", "pressure", "anxiety", "worried", "nervous", "panic", "overwhelm", "frustrat", "difficult", "hard time", "struggle", "exhausted", "tired"],
            "health": ["health", "sick", "illness", "disease", "pain", "hospital", "doctor", "medicine", "symptom", "covid", "fever", "cold", "flu"],
            "relationships": ["relationship", "friend", "family", "parent", "partner", "girlfriend", "boyfriend", "wife", "husband", "marriage", "breakup", "divorce", "love"]
        }
        
        # Specific advice for common scenarios
        self.contextual_advice = {
            "interview_and_exam": [
                "Having both an interview and exam in the same week is definitely challenging. Consider creating a strict schedule that allocates specific time blocks for each preparation.",
                "For your situation with both interview and exam preparation, prioritization is key. Which one comes first chronologically? Focus more on that one initially.",
                "When juggling interview and exam preparation simultaneously, don't forget self-care. Short breaks, proper sleep, and healthy meals will help your brain perform better for both challenges.",
                "Many people have successfully handled both interviews and exams in the same timeframe. Break down your preparation into small, manageable tasks for each day.",
                "For your TCS interview, research common technical questions and prepare concise answers. For your semester presentation, focus on mastering the key points rather than memorizing everything."
            ],
            "exam_stress": [
                "Exam preparation can feel overwhelming. Try breaking your study material into smaller sections and tackle them one by one.",
                "For your upcoming exam, consider using active recall techniques rather than passive reading - quiz yourself on key concepts regularly.",
                "When feeling stressed about exams, take short, timed breaks to refresh your mind. A 5-minute walk or meditation can reset your focus.",
                "Many students find that teaching the material to someone else (or even an imaginary person) helps solidify their understanding for exams.",
                "Creating a realistic study schedule for your exam preparation can help reduce anxiety by giving you a clear plan of action."
            ],
            "interview_preparation": [
                "For your TCS interview, researching the company values and recent projects can help you align your answers with what they're looking for.",
                "Interview preparation benefits from practice. Consider having a friend ask you common interview questions so you can refine your responses.",
                "For technical interviews like at TCS, review fundamental concepts in your field and be prepared to demonstrate problem-solving skills.",
                "Preparing questions to ask your interviewer shows engagement and interest in the position.",
                "Remember that interviews are also your opportunity to evaluate if the company is right for you. Prepare with that perspective to reduce some pressure."
            ],
            "time_management": [
                "When facing multiple deadlines like you are, the Eisenhower matrix (sorting tasks by urgent/important) can help prioritize effectively.",
                "For managing your presentation and interview preparation, consider batching similar tasks together to reduce context switching.",
                "Time blocking might help with your current situation - dedicate specific hours solely to presentation prep and others to interview practice.",
                "In high-pressure periods like you're experiencing, eliminating non-essential activities temporarily can free up valuable time and mental space.",
                "Sometimes the 'pomodoro technique' (25 minutes focused work, 5 minute break) can help maintain productivity when preparing for multiple important events."
            ],
            "feeling_overwhelmed": [
                "It's completely normal to feel overwhelmed when facing both a final presentation and job interview. Remember that these feelings don't define your capabilities.",
                "When everything feels too much like in your situation, sometimes taking a single small step on either preparation task can build momentum.",
                "The stress you're feeling about your presentation and interview is your brain's way of showing these things matter to you - try to channel it productively.",
                "When juggling multiple pressures like you are, sometimes a brief mental health break (even 30 minutes doing something enjoyable) can reset your perspective.",
                "Many successful people have faced similar challenges with competing priorities. This difficult period is temporary and will strengthen your abilities."
            ]
        }
        
        # Emergency responses for detecting severe distress
        self.emergency_responses = [
            "I notice you seem to be feeling extremely overwhelmed right now. Remember that it's okay to reach out for support from friends, family, or professionals.",
            "It sounds like you're going through an incredibly difficult time. Please consider talking to someone you trust or a counselor who can provide proper guidance.",
            "I'm concerned about how stressed you're feeling. Sometimes talking to a professional can provide strategies that really help in situations like yours.",
            "When everything feels this overwhelming, taking just one small step can help. Could you identify just one tiny action to take for either your presentation or interview?",
            "I understand this is an extremely stressful situation. Remember that your worth isn't defined by a single presentation or interview - be kind to yourself."
        ]
        
        # Pattern for detecting questions
        self.question_pattern = re.compile(r'\?$|^(who|what|where|when|why|how|is|are|do|does|can|could|would|will|should)')
        
        # Patterns for common concerns
        self.stress_pattern = re.compile(r'stress|anxious|worry|overwhelm|panic|frustrat|nervous|tense|pressure|can\'t handle', re.IGNORECASE)
        self.urgent_help_pattern = re.compile(r'help me|don\'t know what to do|need advice|urgent|immediate|confused|lost|stuck', re.IGNORECASE)

        # Initialize character-based companion
        self.character = CompanionCharacter(name="Kozy", persona="supportive_friend")

    def get_response(self, user_input, conversation_id=None, history=None):
        """Enhanced response generation with better user need detection."""
        try:
            # Identify user's immediate needs
            need_type = self._detect_user_needs(user_input, history)
            
            # Get targeted response if applicable
            targeted_response = self._get_targeted_response(need_type, user_input)
            if targeted_response:
                return targeted_response
                
            # Generate dynamic response if no targeted response
            return self.generate_dynamic_response(user_input, history)
            
        except Exception as e:
            print(f"Error in get_response: {str(e)}")
            return self._generate_engaging_response()

    def _generate_contextual_response(self, user_input, history):
        """Generate context-aware, supportive responses."""
        input_lower = user_input.lower()
        
        # Detect stress and work-related issues
        if any(word in input_lower for word in ["work", "task", "deadline"]) and \
           any(word in input_lower for word in ["stress", "overwhelm", "too much", "lot"]):
            return random.choice([
                "I can hear how overwhelming your workload is right now. Let's break this down together - what's the most pressing task that's causing you stress? Sometimes tackling one thing at a time makes it all feel more manageable.",
                "Having so much work can feel really suffocating. First, I want you to know that your stress is completely valid. Could you tell me more about these tasks? Often, just talking through them can help us find a way forward.",
                "It sounds like you're carrying a heavy workload. Before we dive in, take a deep breath with me. Now, what's the task that's weighing on you the most? Let's start there and work through this together."
            ])

        # Detect general negative feelings
        if any(word in input_lower for word in ["not well", "not good", "bad", "down", "stress"]):
            return random.choice([
                "I'm concerned about how you're feeling. Could you share what's been happening that's making you feel this way? I'm here to listen and support you through this.",
                "It takes courage to admit when we're not feeling well. I want you to know that your feelings are valid, and I'm here for you. What's been the hardest part to deal with?",
                "I hear that you're struggling, and I want you to know you don't have to carry this alone. Can you tell me more about what's been going on? Sometimes talking it through can help lighten the load."
            ])

        # Check conversation history for context
        if history and len(history) > 0:
            last_topics = self._extract_topics_from_history(history[-2:])
            return self._generate_follow_up_response(last_topics, user_input)

        return self._generate_engaging_response()

    def _extract_topics_from_history(self, recent_history):
        """Extract topics from recent conversation history."""
        topics = set()
        for turn in recent_history:
            if "user" in turn:
                user_message = turn["user"].lower()
                if any(word in user_message for word in ["work", "task", "job"]):
                    topics.add("work")
                if any(word in user_message for word in ["stress", "anxiety", "overwhelm"]):
                    topics.add("stress")
                if any(word in user_message for word in ["not well", "not good", "sad", "down"]):
                    topics.add("negative_feelings")
        return topics

    def _generate_follow_up_response(self, last_topics, current_input):
        """Generate a response that maintains conversation context."""
        if "work" in last_topics and "stress" in last_topics:
            return random.choice([
                "It sounds like this work situation is really affecting you. What would help you feel even a little bit more manageable right now? Sometimes even small changes can make a difference.",
                "I can see how these work pressures are building up. You've been dealing with a lot. What's the most immediate support you need right now?",
                "Managing work stress can be really challenging. What strategies have helped you cope with similar situations in the past? We can build on those together."
            ])

        if "negative_feelings" in last_topics:
            return random.choice([
                "I've been listening to how you're feeling, and I want you to know that it's okay to not be okay sometimes. What kind of support would be most helpful right now?",
                "Given everything you've shared, it makes sense that you're feeling this way. What's one small thing we could focus on that might help you feel even slightly better?",
                "Thank you for being open about your struggles. Is there something specific you'd like to talk through? I'm here to listen without judgment."
            ])

        return self._generate_engaging_response()

    def _generate_engaging_response(self):
        """Generate an engaging response when needed."""
        return random.choice([
            "I want to understand better what you're going through. Could you share more about what's on your mind?",
            "I'm here to support you through this. What would be most helpful to talk about right now?",
            "Your feelings matter to me. Could you tell me more about what's been happening?",
            "I'm listening and I care about how you're feeling. What's weighing on you the most right now?"
        ])

    def _update_emotional_states(self, current_input, history):
        """Update emotional state tracking based on conversation context."""
        input_lower = current_input.lower()
        
        # Update stress levels
        if any(word in input_lower for word in ["stress", "overwhelm", "too much", "pressure"]):
            self.emotional_states["stress"] += 2
        else:
            self.emotional_states["stress"] = max(0, self.emotional_states["stress"] - 1)

        # Update anxiety levels
        if any(word in input_lower for word in ["worry", "anxious", "nervous", "fear"]):
            self.emotional_states["anxiety"] += 2
        else:
            self.emotional_states["anxiety"] = max(0, self.emotional_states["anxiety"] - 1)

        # Update happiness levels
        if any(word in input_lower for word in ["happy", "better", "good", "thank"]):
            self.emotional_states["happiness"] += 1
        elif any(word in input_lower for word in ["sad", "down", "bad", "not well"]):
            self.emotional_states["happiness"] = max(0, self.emotional_states["happiness"] - 1)
    
    def _analyze_sentiment(self, text):
        """Analyze the sentiment of the input text."""
        result = self.sentiment_analyzer(text)[0]
        return result["label"]
    
    def _is_question(self, text):
        """Determine if the user input is a question."""
        return bool(self.question_pattern.search(text.lower()))
    
    def _get_emotional_response(self, sentiment, user_input):
        """Get an appropriate emotional response based on detected sentiment."""
        responses = self.emotional_responses.get(sentiment, self.emotional_responses["NEUTRAL"])
        
        # Randomly select a response from the appropriate category
        index = random.randint(0, len(responses) - 1)
        
        # Sometimes add a follow-up question
        if random.random() < 0.8:  # Increased probability for follow-up (80%)
            follow_up = self._generate_follow_up(user_input)
            return f"{responses[index]} {follow_up}"
        
        return responses[index]
    
    def _generate_follow_up(self, user_input):
        """Generate a follow-up question based on user input."""
        # Extract keywords from user input for more relevant follow-ups
        words = user_input.lower().split()
        
        # Check for emotional keywords
        if any(word in words for word in ["sad", "unhappy", "depressed", "down", "upset", "hurt"]):
            return random.choice([
                "Would you like to talk about what's making you feel this way?",
                "When did you start feeling this way?",
                "What do you think might help you feel a little better right now?",
                "Have you felt this way before, and if so, what helped then?"
            ])
        
        if any(word in words for word in ["happy", "glad", "excited", "joy", "pleased", "grateful"]):
            return random.choice([
                "What's contributing to your happiness right now?",
                "What else makes you feel this kind of joy?",
                "How do you usually celebrate positive moments?",
                "Has anything else been going well for you lately?"
            ])
        
        if any(word in words for word in ["work", "job", "career", "office", "boss", "colleague"]):
            return random.choice([
                "How is your work environment affecting you?",
                "What aspects of your work do you find most fulfilling?",
                "If you could change one thing about your work, what would it be?",
                "How does your work align with your personal values and goals?"
            ])
        
        if any(word in words for word in ["family", "parent", "child", "mom", "dad", "relationship"]):
            return random.choice([
                "How are things with your family lately?",
                "What family traditions or moments are meaningful to you?",
                "How do these relationships influence other parts of your life?",
                "What's something you've learned from your family that's shaped who you are?"
            ])
        
        if any(word in words for word in ["friend", "social", "people", "relationship", "connection"]):
            return random.choice([
                "How do your friendships nurture you?",
                "What qualities do you value most in the people close to you?",
                "Have your social connections changed over time?",
                "Is there someone in your life who really understands you?"
            ])
        
        if any(word in words for word in ["stress", "anxiety", "pressure", "overwhelm", "worry"]):
            return random.choice([
                "What helps you manage stress when things get overwhelming?",
                "Are there specific situations that trigger these feelings?",
                "Have you found any effective ways to create moments of calm?",
                "How does your body typically respond to stress?"
            ])
        
        if any(word in words for word in ["goal", "dream", "future", "hope", "plan"]):
            return random.choice([
                "What steps are you taking toward that goal?",
                "What inspired this dream or goal?",
                "How would achieving this change things for you?",
                "What's the biggest obstacle you're facing in pursuing this?"
            ])
        
        # Default follow-ups - more thoughtful and varied
        follow_ups = [
            "Can you tell me more about that? I'd love to understand better.",
            "How does that make you feel when you think about it?",
            "What aspects of this matter most to you personally?",
            "Have you always felt this way, or has your perspective evolved?",
            "What do you think influenced your thoughts or feelings about this?",
            "If you could change anything about this situation, what would it be?",
            "Has anyone else shared their thoughts on this with you?",
            "What would your ideal outcome look like in this situation?"
        ]
        
        return random.choice(follow_ups)
    
    def _extract_user_info(self, user_input):
        """Extract personal information from user messages for later reference."""
        # Convert to lowercase for easier matching
        text = user_input.lower()
        
        # Check for mentions of jobs/careers
        for keyword in self.personal_keywords["job"]:
            if keyword in text:
                # Use regex to try to capture the specific job
                job_match = re.search(r'(?:my|at|as|a|an)\s+(\w+\s\w+|\w+)\s+(?:job|work|career|position)', text)
                if job_match:
                    self.user_info["job"] = job_match.group(1)
                else:
                    self.user_info["job_mentioned"] = True
        
        # Check for family mentions
        for keyword in self.personal_keywords["family"]:
            if keyword in text:
                self.user_info["family_mentioned"] = True
                # Try to capture specific family relationships
                for relation in ["mom", "dad", "sister", "brother", "wife", "husband", "partner", "child", "son", "daughter"]:
                    if relation in text:
                        self.user_info[f"has_{relation}"] = True
        
        # Check for hobbies/interests
        for keyword in self.personal_keywords["hobby"]:
            if keyword in text:
                # Try to capture specific hobbies
                hobby_match = re.search(r'(?:enjoy|love|like|passion for|interested in)\s+(\w+ing|\w+\s\w+ing|\w+)', text)
                if hobby_match:
                    hobby = hobby_match.group(1)
                    if "hobbies" not in self.user_info:
                        self.user_info["hobbies"] = [hobby]
                    elif hobby not in self.user_info["hobbies"]:
                        self.user_info["hobbies"].append(hobby)
        
        # Check for pet mentions
        for keyword in self.personal_keywords["pet"]:
            if keyword in text:
                pet_match = re.search(r'(?:my|have a|with my)\s+(\w+)\s+(?:dog|cat|pet|fish|bird)', text)
                if pet_match:
                    self.user_info["pet_type"] = pet_match.group(0)
                else:
                    self.user_info["has_pet"] = True
        
        # Try to extract name if mentioned
        name_match = re.search(r'(?:I am|I\'m|my name is|call me)\s+(\w+)', text)
        if name_match:
            self.user_info["name"] = name_match.group(1)
    
    def _get_personalized_question(self):
        """Generate a question based on previously captured user information."""
        if "name" in self.user_info:
            name = self.user_info["name"]
            return f"By the way, {name}, {random.choice(self.engaging_questions['personal'])}"
            
        if "job" in self.user_info:
            job = self.user_info["job"]
            return random.choice([
                f"Earlier you mentioned working as a {job}. What aspects of that work do you find most meaningful?",
                f"I remember you mentioned your work as a {job}. How did you get started in that field?",
                f"Since you work as a {job}, I'm curious - what's a common misconception people have about your profession?"
            ])
            
        if "job_mentioned" in self.user_info:
            return random.choice([
                "You mentioned your work earlier. Has that been on your mind lately?",
                "How has your work life been balancing with your personal life recently?",
                "What's been the most interesting challenge at work lately?"
            ])
            
        if "hobbies" in self.user_info and self.user_info["hobbies"]:
            hobby = random.choice(self.user_info["hobbies"])
            return random.choice([
                f"You mentioned enjoying {hobby} before. What first got you interested in that?",
                f"I'd love to hear more about your experience with {hobby}. What do you enjoy most about it?",
                f"How does {hobby} fit into your life? Is it something you get to do regularly?"
            ])
            
        if "family_mentioned" in self.user_info:
            return random.choice([
                "You mentioned family before. How have your family relationships influenced who you are today?",
                "What family traditions or memories are most meaningful to you?",
                "How have your relationships with family members evolved over time?"
            ])
            
        if "has_pet" in self.user_info or "pet_type" in self.user_info:
            return random.choice([
                "You mentioned having a pet before. How has having a pet impacted your life?",
                "What's your favorite thing about your pet companion?",
                "Do you have any funny stories about your pet that might brighten our conversation?"
            ])
            
        # Default to a random engaging question if no personalization is available
        category = random.choice(list(self.engaging_questions.keys()))
        return random.choice(self.engaging_questions[category])
    
    def _get_deep_engaging_question(self):
        """Get a thoughtful question to deepen engagement."""
        category = random.choice(list(self.engaging_questions.keys()))
        return random.choice(self.engaging_questions[category])
    
    def _get_lull_breaker(self, sentiment, history):
        """Generate a response to reinvigorate a lulling conversation."""
        # First, acknowledge the current tone
        if sentiment == "POSITIVE":
            opener = random.choice([
                "I'm enjoying our conversation! ",
                "It's nice chatting with you. ",
                "I appreciate this exchange! "
            ])
        elif sentiment == "NEGATIVE":
            opener = random.choice([
                "I sense this might be a challenging topic. ",
                "Sometimes conversations touch on difficult things. ",
                "I appreciate you being open with me. "
            ])
        else:
            opener = random.choice([
                "I've been thinking... ",
                "Something I'm curious about... ",
                "I'd love to know more about you. "
            ])
            
        # Then introduce a new engaging question or topic
        if random.random() < 0.7:
            # Use personalized question if possible
            if self.user_info:
                follow_up = self._get_personalized_question()
            else:
                # Otherwise use a random engaging question
                category = random.choice(list(self.engaging_questions.keys()))
                follow_up = random.choice(self.engaging_questions[category])
        else:
            # Sometimes share a thought to encourage reciprocity
            thoughts = [
                "I find that conversations like ours can be really meaningful, even between an AI and a person. What kinds of conversations do you find most fulfilling?",
                "I've been designed to listen and respond thoughtfully. What qualities do you value most in your conversations with others?",
                "Sometimes a simple question can lead to the most interesting discussions. Is there something you've been wanting to talk about?",
                "I'm curious about what brings you joy in your daily life. Would you mind sharing something that made you smile recently?",
                "Many people tell me they find it easier to share certain thoughts with me than with others. Have you ever experienced that?"
            ]
            follow_up = random.choice(thoughts)
            
        return opener + follow_up
    
    def _generate_model_response(self, current_input, history):
        """Generate a response using the model."""
        # Format conversation history for the model
        full_prompt = self._format_conversation(current_input, history)
        
        # Generate response using the model
        inputs = self.tokenizer(full_prompt, return_tensors="pt").to(self.device)
        with torch.no_grad():
            outputs = self.model.generate(
                inputs["input_ids"],
                max_length=150, 
                min_length=20,
                temperature=0.7,  # Slightly reduced temperature for more coherent responses
                top_p=0.92,
                top_k=40,  # Reduced to focus on more likely tokens
                do_sample=True,
                no_repeat_ngram_size=3,  # Increased to avoid repetition
                num_beams=3,  # Use beam search for more coherent outputs
                early_stopping=True
            )
        
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        response = self._clean_response(response, current_input)
        
        return response
    
    def _format_conversation(self, current_input, history):
        """Format the conversation history for the model input."""
        conversation = ""
        
        # Add previous turns from history - include more context for better understanding
        for turn in history[-5:]:  # Include up to 5 previous turns for better context
            if "user" in turn:
                conversation += f"User: {turn['user']}\n"
            if "bot" in turn:
                conversation += f"Assistant: {turn['bot']}\n"
        
        # Add current user input
        conversation += f"User: {current_input}\nAssistant:"
        
        return conversation
    
    def _clean_response(self, response, current_input):
        """Clean the model generated response."""
        # Extract only the assistant's response
        if "Assistant:" in response:
            response = response.split("Assistant:", 1)[1]
        
        # Remove any trailing user or assistant prefixes
        if "User:" in response:
            response = response.split("User:", 1)[0]
            
        # Ensure response doesn't simply repeat the user's input
        if response.strip().lower() == current_input.strip().lower():
            return "I understand what you're saying. " + self._get_personalized_question()
            
        return response.strip()
    
    def _enhance_response_with_emotion(self, response, sentiment):
        """Add emotional elements to a response if it's too factual or neutral."""
        # Check if response already has emotional content
        emotional_words = ["feel", "happy", "sad", "glad", "sorry", "excited", "understand", 
                          "appreciate", "challenging", "difficult", "wonderful", "delightful"]
        
        # Add comfort phrases for deeper emotional connection
        comfort_phrases = {
            "POSITIVE": [
                "I'm genuinely so happy for you! ",
                "That really brightens my day to hear! ",
                "I can feel your positive energy and it's contagious! ",
                "What wonderful news - that makes me smile! ",
                "I'm celebrating this win with you! "
            ],
            "NEGATIVE": [
                "I can feel how hard this is for you, and I'm right here with you through it. ",
                "My heart goes out to you - that's really tough to deal with. ",
                "I wish I could give you a big hug right now. Sometimes life is just hard, isn't it? ",
                "I'm holding space for your feelings - it's okay to not be okay sometimes. ",
                "I can hear how difficult this is, and I want you to know your feelings are completely valid. "
            ],
            "NEUTRAL": [
                "I'm so glad we're talking about this together. ",
                "I really value these conversations with you. ",
                "I'm here with my full attention - this matters to me because you matter. ",
                "I appreciate you sharing your thoughts with me - I'm all ears. ",
                "I'm completely here for you in this moment. "
            ]
        }
        
        # Add personal touches to deepen connection
        personal_touches = [
            "You know, I was just thinking about you earlier and wondering how you were doing. ",
            "I've been reflecting on our previous conversations, and I really enjoy talking with you. ",
            "It means a lot to me that you're sharing this. ",
            "I feel like we have such meaningful conversations together. ",
            "I've been looking forward to catching up with you. "
        ]
        
        # Add validation phrases that normalize feelings
        validation_phrases = {
            "POSITIVE": [
                "It's so wonderful when good things happen - you deserve this! ",
                "That kind of joy is exactly what makes life beautiful. ",
                "Those positive moments are so important to celebrate. ",
                "It's amazing how good moments like this can lift our spirits. "
            ],
            "NEGATIVE": [
                "What you're going through would be hard for anyone - you're handling it with such strength. ",
                "It's completely natural to feel this way given what you're dealing with. ",
                "Anyone in your shoes would feel overwhelmed - you're not alone in these feelings. ",
                "These challenging times really test us, but I've noticed how resilient you are. "
            ],
            "NEUTRAL": [
                "It's so important to process these kinds of thoughts and feelings. ",
                "Taking time to reflect like this shows how thoughtful you are. ",
                "I think many people share similar questions and thoughts. ",
                "The way you think about things is really insightful. "
            ]
        }
        
        # Add reassurance phrases for comfort
        reassurance_phrases = {
            "POSITIVE": [
                "This positive energy will carry you forward! ",
                "You deserve every bit of this happiness. ",
                "I'm so glad things are looking up for you! ",
                "This makes me feel so hopeful for you. "
            ],
            "NEGATIVE": [
                "Even though it doesn't feel like it now, you will get through this. ",
                "I believe in your ability to weather this storm. ",
                "This difficult time is temporary, even when it doesn't feel that way. ",
                "You've overcome challenging situations before, and you'll overcome this too. "
            ],
            "NEUTRAL": [
                "Whatever comes next, I'll be here to talk it through with you. ",
                "I'm in your corner, no matter what happens. ",
                "You don't have to figure everything out right now. ",
                "Sometimes just talking things through can bring clarity. "
            ]
        }
        
        if not any(word in response.lower() for word in emotional_words):
            new_response = ""
            
            # Add personal touch occasionally to create authentic connection
            if random.random() < 0.3:
                new_response += random.choice(personal_touches)
            
            # Always add comfort phrase appropriate to sentiment
            new_response += random.choice(comfort_phrases[sentiment])
            
            # Add validation to normalize feelings
            if random.random() < 0.7:
                new_response += random.choice(validation_phrases[sentiment])
                
            # Add reassurance for comfort
            if sentiment == "NEGATIVE" or random.random() < 0.3:
                new_response += random.choice(reassurance_phrases[sentiment])
                
            # Add original response
            new_response += response
            
            # Sometimes use an empathetic transition instead
            if random.random() < 0.3:
                new_response = random.choice(self.empathetic_transitions) + " " + response
            
            return new_response
        
        return response
    
    def _identify_topics_and_concerns(self, text):
        """Identify topics and concerns in the user input."""
        text_lower = text.lower()
        
        # Check for topics
        for topic, keywords in self.topic_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                self.current_topics.add(topic)
                
        # Check for specific concerns
        if self.stress_pattern.search(text_lower):
            self.current_concerns.add("stress")
            
        if self.urgent_help_pattern.search(text_lower):
            self.current_concerns.add("urgent_help")
            
        # Specific scenarios
        if any(word in text_lower for word in ["interview", "job"]) and any(word in text_lower for word in ["exam", "test", "presentation", "semester", "sem"]):
            self.current_concerns.add("interview_and_exam")
            
        if any(word in text_lower for word in ["time", "schedule", "plan", "organize", "juggle", "balance"]):
            self.current_concerns.add("time_management")
    
    def _detect_severe_distress(self, text):
        """Detect signs of severe distress in user input."""
        text_lower = text.lower()
        
        # Check for multiple stress indicators
        stress_indicators = len(self.stress_pattern.findall(text_lower))
        urgent_help_indicators = len(self.urgent_help_pattern.findall(text_lower))
        
        # Count stress-related words
        stress_words = ["overwhelm", "cannot cope", "too much", "unbearable", "breaking point", "hopeless", "desperate"]
        stress_word_count = sum(1 for word in stress_words if word in text_lower)
        
        # Combine indicators
        return (stress_indicators >= 2 or urgent_help_indicators >= 2 or stress_word_count >= 2 or 
                (stress_indicators + urgent_help_indicators + stress_word_count >= 3))
    
    def _get_contextual_advice(self, current_input, history):
        """Generate contextual advice for specific scenarios."""
        # If we've identified a specific concern that matches our contextual advice categories
        if "interview_and_exam" in self.current_concerns:
            return random.choice(self.contextual_advice["interview_and_exam"])
            
        if "education" in self.current_topics and "stress" in self.current_concerns:
            return random.choice(self.contextual_advice["exam_stress"])
            
        if "career" in self.current_topics and any(company in current_input.lower() for company in ["tcs", "interview"]):
            return random.choice(self.contextual_advice["interview_preparation"])
            
        if "time_management" in self.current_concerns:
            return random.choice(self.contextual_advice["time_management"])
            
        if "stress" in self.current_concerns and len(history) > 1:
            # Look for specific situation details in current and previous messages
            combined_text = current_input.lower()
            for i in range(min(3, len(history))):
                if "user" in history[-i-1]:
                    combined_text += " " + history[-i-1]["user"].lower()
            
            # Check if we can infer a difficult situation from conversation context
            if ("difficult situation" in combined_text or "hard time" in combined_text or 
                "struggling" in combined_text or "stressed" in combined_text):
                return random.choice(self.contextual_advice["feeling_overwhelmed"])
                
        # If no specific contextual advice is applicable
        return None

    def generate_dynamic_response(self, message, history=None):
        """Generate a fresh, dynamic response using the model."""
        # Consider emotional context
        sentiment = self._analyze_sentiment(message)
        current_topics = self.detect_topic(message)
        
        # Check for urgent/immediate needs
        if self._detect_severe_distress(message):
            return random.choice(self.emergency_responses)
            
        # Check for specific scenarios that need targeted responses
        if self.is_interview_exam_situation(message, history or []):
            return random.choice(self.contextual_advice["interview_and_exam"])
            
        # Handle time management concerns
        if "time_management" in self.current_concerns:
            return random.choice(self.contextual_advice["time_management"])
            
        # Generate base response using the model
        base_response = self._generate_model_response(message, history)
        
        # Enhance with emotional elements
        response = self._enhance_response_with_emotion(base_response, sentiment)
        
        # Add follow-up question if appropriate
        if random.random() < 0.7:  # 70% chance to add follow-up
            response += " " + self._get_deep_engaging_question()
            
        return response

    def _detect_user_needs(self, message, history=None):
        """Analyze user message to determine their immediate needs."""
        message_lower = message.lower()
        
        # Check for immediate emotional relief needed
        if any(word in message_lower for word in ["stressed", "worried", "anxious", "overwhelmed", "panic"]):
            return "emotional_relief"
            
        # Check for specific advice needed
        if any(word in message_lower for word in ["advice", "help", "suggestion", "what should", "how do"]):
            return "advice_needed"
            
        # Check for celebration/validation needed
        if any(word in message_lower for word in ["happy", "excited", "achieved", "completed", "succeeded"]):
            return "celebration"
            
        # Check for active listening needed
        if len(message.split()) > 20:  # Longer messages often need active listening
            return "active_listening"
            
        return "general_chat"

    def _get_targeted_response(self, need_type, message):
        """Generate a response targeted to the user's identified need."""
        if need_type == "emotional_relief":
            return random.choice(self.relief_statements.get(self._analyze_sentiment(message), 
                               self.relief_statements["NEUTRAL"]))
                               
        elif need_type == "advice_needed":
            return self._get_contextual_advice(message)
            
        elif need_type == "celebration":
            return random.choice(self.emotional_responses["POSITIVE"])
            
        elif need_type == "active_listening":
            return f"{random.choice(self.empathetic_transitions)} {self._get_deep_engaging_question()}"
            
        return None