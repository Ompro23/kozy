# Emotional Companion App

An AI-powered emotional companion application that provides responsive conversation and emotional support to users.

## Features

- Responsive conversational AI using HuggingFace's models
- Web interface for easy interaction
- Admin dashboard to monitor conversations
- REST API for integration with other applications
- No API keys required - uses open-source models

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/emotional-companion.git
   cd emotional-companion
   ```

2. Create a virtual environment and activate it:
   ```
   python -m venv venv
   
   # On Windows:
   venv\Scripts\activate
   
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Run the application:
   ```
   python app.py
   ```

5. Open a web browser and go to http://127.0.0.1:5000/ to start using the application.

## API Documentation

### Chat API

Endpoint: `/api/chat`  
Method: POST  
Parameters:
- `message` (string): The user's message
- `conversation_id` (string, optional): ID to continue an existing conversation

Response:
```json
{
    "response": "Bot's response message",
    "conversation_id": "unique_conversation_id"
}
```

Example:
```bash
curl -X POST http://127.0.0.1:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, how are you?", "conversation_id": "12345"}'
```

### Conversations API

Endpoint: `/api/conversations`  
Method: GET  
Parameters:
- `id` (string, optional): Specific conversation ID to retrieve

Response: JSON object containing conversation history

## Admin Dashboard

The admin dashboard allows you to:
- View all conversations
- See detailed message history
- Monitor system statistics

Access the admin dashboard at http://127.0.0.1:5000/admin

Default admin credentials:
- Username: admin
- Password: admin

## Android Integration

To integrate with an Android application, use the API endpoints to send and receive messages. Example code:

```java
StringRequest stringRequest = new StringRequest(Request.Method.POST,
    "http://your-server-address:5000/api/chat",
    new Response.Listener<String>() {
        @Override
        public void onResponse(String response) {
            // Process the response
            JSONObject jsonResponse = new JSONObject(response);
            String botMessage = jsonResponse.getString("response");
            String conversationId = jsonResponse.getString("conversation_id");
            
            // Update UI with the bot's response
        }
    },
    new Response.ErrorListener() {
        @Override
        public void onErrorResponse(VolleyError error) {
            // Handle error
        }
    }
) {
    @Override
    protected Map<String, String> getParams() {
        Map<String, String> params = new HashMap<>();
        params.put("message", userMessage);
        if (conversationId != null) {
            params.put("conversation_id", conversationId);
        }
        return params;
    }
    
    @Override
    public Map<String, String> getHeaders() {
        Map<String, String> headers = new HashMap<>();
        headers.put("Content-Type", "application/json");
        return headers;
    }
};

// Add request to queue
RequestQueue requestQueue = Volley.newRequestQueue(context);
requestQueue.add(stringRequest);
```

## Customization

### Changing the AI Model

You can change the AI model by modifying the `model_name` variable in `app.py`:

```python
# Change to any compatible HuggingFace model
model_name = "facebook/blenderbot-400M-distill"
```

### UI Customization

Modify the CSS files in the `static/css` directory and HTML templates in the `templates` directory to customize the look and feel of the application.

## License

This project is licensed under the MIT License - see the LICENSE file for details.# kozy
