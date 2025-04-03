# Kozy - AI Emotional Companion

An AI-powered emotional companion that uses Hugging Face's Llama model to provide emotionally intelligent responses.

## Features

- Emotion detection and appropriate responses
- Flask web interface for direct interaction
- API endpoints for integration with Flutter app
- Conversation history tracking
- Fallback to template-based responses if model loading fails

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Virtual environment (recommended)

### Installation

1. Clone the repository:
   ```
   git clone https://your-repository-url/Final-kozy.git
   cd Final-kozy
   ```

2. Create and activate a virtual environment (recommended):
   ```
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   ```

3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

### Running the Application

#### Run the main Flask application (with web UI):

```
python app.py
```

This will start the Flask server on http://localhost:5000

#### Run the standalone API server:

```
python api.py
```

This will start the API server on http://localhost:5001

## API Usage

### Endpoint: `/api/chat` (from app.py)

**Request:**
```
POST /api/chat
Content-Type: application/json

{
    "text": "Hello, how are you?"
}
```

**Response:**
```json
{
    "response": "I'm doing well, thank you for asking! How are you feeling today?"
}
```

### Endpoint: `/vfrd_api.php` (from api.py)

This is the endpoint designed to be compatible with the Flutter app.

**Request:**
```
POST /vfrd_api.php
Content-Type: application/x-www-form-urlencoded

text=Hello, how are you?
```

**Response:**
```
I'm doing well, thank you for asking! How are you feeling today?
```

## Integration with Flutter App

The API is designed to be compatible with the existing Flutter app's API calls. The Flutter app should send POST requests to `/vfrd_api.php` with the user's message in the 'text' parameter.

## Deployment

For production deployment, consider:

1. Using gunicorn as a WSGI server:
   ```
   gunicorn -w 4 app:app
   ```

2. Setting up Nginx as a reverse proxy
3. Deploying on a cloud platform (AWS, GCP, Azure, etc.)
4. Setting appropriate environment variables for security and configuration

## License

[Your License Information]

## Acknowledgements

- Hugging Face for the Llama model
- Flask for the web framework