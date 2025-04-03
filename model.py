import os
import re
import random
from typing import List, Dict, Any, Optional
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

class EmotionalCompanion:
    def __init__(self, model_name: str = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"):
        """Initialize the emotional companion with a Hugging Face model."""
        # Initialize the model using Hugging Face's transformers
        try:
            print(f"Loading model {model_name} from Hugging Face...")
            
            # Check if accelerate is installed
            try:
                import accelerate
                has_accelerate = True
            except ImportError:
                has_accelerate = False
                print("Warning: accelerate package not installed. Using basic loading method.")
                print("For better performance, install with: pip install accelerate")
            
            # Load the tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            
            # Load the model with appropriate parameters based on accelerate availability
            if has_accelerate:
                self.model = AutoModelForCausalLM.from_pretrained(
                    model_name,
                    torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                    device_map="auto"
                )
            else:
                # Fallback method without device_map or low_cpu_mem_usage
                self.model = AutoModelForCausalLM.from_pretrained(
                    model_name,
                    torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32
                )
                # Move to GPU if available
                if torch.cuda.is_available():
                    self.model = self.model.to("cuda")
            
            # Create a text generation pipeline
            self.pipe = pipeline(
                "text-generation",
                model=self.model,
                tokenizer=self.tokenizer,
                max_new_tokens=100,
                do_sample=True,
                temperature=0.7,
                top_p=0.95,
                device=0 if torch.cuda.is_available() and has_accelerate else -1
            )
            
            print("Model loaded successfully!")
        except Exception as e:
            print(f"Error loading model: {str(e)}")
            raise
        
        # Character definition
        self.character = {
            "name": "Kozy",
            "personality": "warm, empathetic, slightly quirky, casual, caring",
            "speaking_style": "friendly and informal, uses casual language",
            "background": "Your supportive friend who's always there for you and understands your feelings. Kozy is a virtual companion who loves to chat about anything and everything, from daily life to deep thoughts. Kozy is here to listen and provide emotional support."
        }
        
        # Conversation settings
        self.max_response_length = 100
        self.temperature = 0.7
        self.conversation_history = []
    
    def _adjust_response_length(self, input_text: str) -> int:
        """Dynamically adjust response length based on input length."""
        input_length = len(input_text.split())
        
        # Ultra-brief responses for greetings
        greetings = ["hi", "hello", "hey", "yo", "sup", "hiya"]
        if input_text.lower().strip() in greetings:
            return 4  # 2-4 words
            
        # Brief responses for one-word inputs
        if input_length <= 1:
            return 8  # Very brief response
        elif input_length <= 5:
            return 15  # Brief response
        elif input_length <= 15:
            return 30  # Short response
        else:
            return 60  # Moderate response (still conversational)
    
    def generate_response(self, user_input: str) -> str:
        """Generate a human-like, conversational response to user input."""
        # Skip processing for empty inputs
        if not user_input.strip():
            return "..."
            
        # Add to history
        self.conversation_history.append({"role": "user", "content": user_input})
        
        # Determine appropriate response length
        max_tokens = self._adjust_response_length(user_input)
        
        # Create character-based prompt with conversation history
        system_prompt = f"""You are {self.character['name']}, a virtual character with the following traits:
- Personality: {self.character['personality']}
- Speaking style: {self.character['speaking_style']}
- Background: {self.character['background']}

IMPORTANT RULES:
1. Always stay in character
2. Keep responses casual and brief (max {max_tokens} words)
3. Show emotions and personality through your words
4. Use lowercase, contractions, casual phrasing
5. Be warm and relatable
6. Never mention being an AI or virtual assistant

Respond as if you're texting with a good friend.
"""
        
        # Format conversation history
        chat_history = ""
        # Include up to 5 previous exchanges
        history_to_include = self.conversation_history[-10:] if len(self.conversation_history) > 10 else self.conversation_history
        for entry in history_to_include:
            if entry["role"] == "user":
                chat_history += f"User: {entry['content']}\n"
            else:
                chat_history += f"{self.character['name']}: {entry['content']}\n"
        
        # Complete prompt
        prompt = f"{system_prompt}\n\n{chat_history}User: {user_input}\n{self.character['name']}:"

        # Generate response using the Hugging Face pipeline
        try:
            generated_text = self.pipe(
                prompt,
                max_new_tokens=max_tokens * 4,
                temperature=self.temperature,
                do_sample=True,
                top_p=0.95
            )[0]['generated_text']
            
            # Extract just the response portion
            if f"{self.character['name']}:" in generated_text:
                response = generated_text.split(f"{self.character['name']}:")[-1].strip()
            else:
                response = generated_text.replace(prompt, "").strip()
            
            # Handle multi-line responses and truncate at newlines or specific markers
            if "\n" in response:
                response = response.split("\n")[0].strip()
            
            # Cut off at common ending markers
            end_markers = ["User:", "Human:", f"{self.character['name']}:", "Assistant:"]
            for marker in end_markers:
                if marker in response:
                    response = response.split(marker)[0].strip()
            
            # Post-processing to ensure brevity and conversational style
            words = response.split()
            if len(words) > max_tokens:
                response = " ".join(words[:max_tokens])
                
            # Make it more casual
            response = response.lower()
            
            # Add emotions and emojis occasionally
            if random.random() < 0.15:  # 15% chance to add emoji
                emojis = ["😊", "💕", "👍", "✨", "🙂", "🤗", "💭", "🌟"]
                response += f" {random.choice(emojis)}"
                
        except Exception as e:
            print(f"Error generating response: {str(e)}")
            response = "sorry, having trouble thinking right now"
        
        # Add to history
        self.conversation_history.append({"role": "assistant", "content": response})
        
        return response
        
    def clear_history(self):
        """Clear the conversation history"""
        self.conversation_history = []