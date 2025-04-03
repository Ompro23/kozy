import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from model import EmotionalCompanion

app = Flask(__name__)
CORS(app)  # Enable CORS to allow requests from any origin

# Initialize the emotional companion model
companion = EmotionalCompanion()

@app.route('/vfrd_api.php', methods=['POST'])
def api_endpoint():
    """Main API endpoint that can be called from external applications like Flutter"""
    try:
        # Handle form data from Flutter or other apps
        text = request.form.get('text')
        
        # Also support JSON data for more flexibility
        if not text and request.is_json:
            data = request.get_json()
            text = data.get('text')
            
        if not text:
            return "Please provide a 'text' parameter", 400
            
        # Process special first message
        if text == "__first":
            response = "Hello! I'm Kozy, your emotional companion. How are you feeling today?"
        else:
            # Generate response from the model
            response = companion.generate_response(text)
            
        # Return just the response text for compatibility with the Flutter app
        return response
    
    except Exception as e:
        print(f"API Error: {str(e)}")
        return f"Sorry, I encountered an error: {str(e)}", 500

if __name__ == '__main__':
    # Default port is 5001 to avoid conflict with main app
    port = int(os.environ.get('API_PORT', 5001))
    app.run(host='0.0.0.0', port=port)