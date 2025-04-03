from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os
import argparse
from model import EmotionalCompanion

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Run the Kozy emotional companion')
    parser.add_argument('--model', type=str, default="TinyLlama/TinyLlama-1.1B-Chat-v1.0", 
                        help='HuggingFace model to use (default: TinyLlama/TinyLlama-1.1B-Chat-v1.0)')
    args = parser.parse_args()
    
    # Initialize the emotional companion with the specified model
    print(f"Initializing Kozy with model: {args.model}")
    companion = EmotionalCompanion(model_name=args.model)
    
    print("\n🌟 Welcome to Kozy - Your Emotional Companion 🌟")
    print("Type 'exit', 'quit', or 'bye' to end the conversation.")
    print("Type 'clear' to clear the conversation history.")
    
    # Main conversation loop
    while True:
        user_input = input("\nYou: ").strip()
        
        # Check for exit commands
        if user_input.lower() in ['exit', 'quit', 'bye']:
            print("\nKozy: take care! talk to you later.")
            break
            
        # Check for clear command
        if user_input.lower() == 'clear':
            companion.clear_history()
            print("\nConversation history cleared.")
            continue
        
        # Generate and display response
        response = companion.generate_response(user_input)
        print(f"\nKozy: {response}")

if __name__ == "__main__":
    main()