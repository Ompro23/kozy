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

## Making API Requests

Here are examples of how to send requests to the API using different methods:

### cURL

```bash
# Start a new conversation
curl -X POST http://127.0.0.1:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, how are you?"}'

# Continue an existing conversation
curl -X POST http://127.0.0.1:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "I am feeling stressed today", "conversation_id": "1"}'

# Retrieve conversation history
curl -X GET http://127.0.0.1:5000/api/conversations?id=1
```

### Python with Requests

```python
import requests
import json

# Base URL of the API
base_url = "http://127.0.0.1:5000"

# Start a new conversation
def start_conversation(message):
    url = f"{base_url}/api/chat"
    payload = {"message": message}
    headers = {"Content-Type": "application/json"}
    
    response = requests.post(url, data=json.dumps(payload), headers=headers)
    return response.json()

# Continue an existing conversation
def continue_conversation(message, conversation_id):
    url = f"{base_url}/api/chat"
    payload = {"message": message, "conversation_id": conversation_id}
    headers = {"Content-Type": "application/json"}
    
    response = requests.post(url, data=json.dumps(payload), headers=headers)
    return response.json()

# Retrieve conversation history
def get_conversation(conversation_id):
    url = f"{base_url}/api/conversations?id={conversation_id}"
    response = requests.get(url)
    return response.json()

# Example usage
result = start_conversation("Hello, how are you?")
print(f"Bot says: {result['response']}")
print(f"Conversation ID: {result['conversation_id']}")

# Continue the conversation
result = continue_conversation("I'm feeling stressed", result['conversation_id'])
print(f"Bot says: {result['response']}")
```

### JavaScript/jQuery

```javascript
// Start a new conversation
function startConversation(message) {
    $.ajax({
        url: 'http://127.0.0.1:5000/api/chat',
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({
            message: message
        }),
        success: function(data) {
            console.log('Bot response:', data.response);
            console.log('Conversation ID:', data.conversation_id);
            
            // Store the conversation ID for later use
            localStorage.setItem('conversationId', data.conversation_id);
        },
        error: function(error) {
            console.error('Error:', error);
        }
    });
}

// Continue an existing conversation
function continueConversation(message) {
    const conversationId = localStorage.getItem('conversationId');
    
    $.ajax({
        url: 'http://127.0.0.1:5000/api/chat',
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({
            message: message,
            conversation_id: conversationId
        }),
        success: function(data) {
            console.log('Bot response:', data.response);
        },
        error: function(error) {
            console.error('Error:', error);
        }
    });
}

// Fetch conversation history
function getConversationHistory() {
    const conversationId = localStorage.getItem('conversationId');
    
    $.ajax({
        url: `http://127.0.0.1:5000/api/conversations?id=${conversationId}`,
        type: 'GET',
        success: function(data) {
            console.log('Conversation history:', data);
        },
        error: function(error) {
            console.error('Error:', error);
        }
    });
}
```

### JavaScript Fetch API

```javascript
// Start a new conversation
async function startConversation(message) {
    try {
        const response = await fetch('http://127.0.0.1:5000/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: message
            })
        });
        
        const data = await response.json();
        console.log('Bot response:', data.response);
        console.log('Conversation ID:', data.conversation_id);
        
        // Store conversation ID
        return data.conversation_id;
    } catch (error) {
        console.error('Error:', error);
    }
}

// Continue an existing conversation
async function continueConversation(message, conversationId) {
    try {
        const response = await fetch('http://127.0.0.1:5000/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: message,
                conversation_id: conversationId
            })
        });
        
        const data = await response.json();
        console.log('Bot response:', data.response);
        return data;
    } catch (error) {
        console.error('Error:', error);
    }
}
```

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
// Using Volley library
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

### Using OkHttp in Android

```java
// Using OkHttp library
private void sendChatRequest(String message, String conversationId) {
    OkHttpClient client = new OkHttpClient();
    
    // Create JSON object for request body
    JSONObject jsonBody = new JSONObject();
    try {
        jsonBody.put("message", message);
        if (conversationId != null) {
            jsonBody.put("conversation_id", conversationId);
        }
    } catch (JSONException e) {
        e.printStackTrace();
    }
    
    // Create request
    RequestBody body = RequestBody.create(
        MediaType.parse("application/json"), jsonBody.toString());
    
    Request request = new Request.Builder()
        .url("http://your-server-address:5000/api/chat")
        .post(body)
        .build();
    
    // Execute request asynchronously
    client.newCall(request).enqueue(new Callback() {
        @Override
        public void onFailure(Call call, IOException e) {
            // Handle failure
            e.printStackTrace();
        }
        
        @Override
        public void onResponse(Call call, Response response) throws IOException {
            if (response.isSuccessful()) {
                String responseData = response.body().string();
                try {
                    JSONObject jsonResponse = new JSONObject(responseData);
                    final String botMessage = jsonResponse.getString("response");
                    final String responseConversationId = jsonResponse.getString("conversation_id");
                    
                    // Update UI on main thread
                    runOnUiThread(new Runnable() {
                        @Override
                        public void run() {
                            // Update UI with bot response
                            // Save conversation ID for future requests
                        }
                    });
                } catch (JSONException e) {
                    e.printStackTrace();
                }
            }
        }
    });
}
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

This project is licensed under the MIT License - see the LICENSE file for details.
