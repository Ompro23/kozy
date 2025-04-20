# KOZY - Smart Emotional Companion

KOZY is a Flask-based emotional companion chatbot that provides empathetic responses to users. The application integrates with Firebase for data storage and Hugging Face for AI-powered conversations.

## Features

- User authentication with Firebase UID
- Real-time chat interface
- AI-powered responses using Hugging Face models
- Persistent chat storage in Firebase Realtime Database
- Session-based conversations with fresh starts for each session

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- Firebase account with Realtime Database set up

### Installation

1. Clone the repository or download the source code

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. The Firebase configuration is already included in the app.py file. If you want to use your own Firebase project, replace the configuration in app.py.

4. Run the application:
   ```
   python app.py
   ```

5. Open your web browser and navigate to:
   ```
   http://127.0.0.1:5000/
   ```

### Usage

1. Enter your Firebase UID on the login page
2. Start chatting with KOZY
3. Your conversations will be stored in the Firebase Realtime Database under your UID

## Data Structure

The application stores chat data in Firebase with the following structure:

# kozy
