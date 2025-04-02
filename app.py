from flask import Flask, request, Response
from flask_cors import CORS
from g4f.client import Client
from g4f.Provider import Blackbox

# Initialize the Flask application
app = Flask(__name__)

# Enable CORS for all routes under /api/*, allowing requests from any origin
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Initialize the g4f client
client = Client()

# Define the route to handle POST requests compatible with OpenAI-like format
@app.route('/v1/chat/completions', methods=['POST'])
def chat_completions():
    # Extract data from the JSON request body (OpenAI-like format)
    data = request.json
    messages = data.get('messages')
    stream = data.get('stream', False)

    # Validate messages
    if not messages or not isinstance(messages, list) or not messages[0].get('content'):
        return Response("Missing or invalid 'messages' parameter", status=400, mimetype='text/plain')

    # Generator function to stream the response
    def generate_response():
        try:
            chat_completion = client.chat.completions.create(
                provider=Blackbox,
                model='claude-3.7-sonnet',
                messages=messages,
                stream=True
            )
            for completion in chat_completion:
                content = completion.choices[0].delta.content or ""
                # Format as OpenAI-like streaming response
                yield f"data: {{ \"choices\": [{{ \"delta\": {{ \"content\": \"{content}\" }} }} ] }}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: {{ \"error\": \"{str(e)}\" }}\n\n"

    # Non-streaming response
    def get_full_response():
        try:
            chat_completion = client.chat.completions.create(
                provider=Blackbox,
                model='claude-3.7-sonnet',
                messages=messages,
                stream=False
            )
            content = chat_completion.choices[0].message.content
            return Response(
                f'{{"choices": [{{"message": {{"content": "{content}"}}}}]}}',
                mimetype='application/json'
            )
        except Exception as e:
            return Response(f'{{"error": "{str(e)}"}}', status=500, mimetype='application/json')

    if stream:
        return Response(generate_response(), mimetype='text/event-stream')
    else:
        return get_full_response()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
