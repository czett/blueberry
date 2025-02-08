from flask import Flask, render_template, request, session, Response
import ollama, json

with open("prompt_config.json", "r") as pc:
    prefixes = json.load(pc)
    prompt_prefix = prefixes["standard"]

app = Flask(__name__)
app.secret_key = "wefhwoeifhaoeiurhgqoeirgh"
app.config['SESSION_PERMANENT'] = False

@app.route('/')
def index():
    session.clear()  # Reset session completely
    return render_template('index.html')

@app.route('/answer', methods=["POST"])
def answer():
    data = request.get_json()
    user_message = data['message']

    # Ensure session["messages"] exists
    if "messages" not in session:
        session["messages"] = []

    # Add user message to conversation history
    session["messages"].append({"role": "user", "content": user_message})

    # Copy the conversation history for the model (Flask session is a dict-like object)
    messages_copy = list(session["messages"])

    # Now return the response as a generator
    def generate():
        assistant_response = ""
        for chunk in ollama.chat(model="qwen2.5:3b", messages=messages_copy, stream=True):
            if chunk["message"]["content"]:
                assistant_response += chunk["message"]["content"]
                yield chunk["message"]["content"]
        
        # Store assistant response in session after streaming
        session["messages"].append({"role": "assistant", "content": assistant_response})
        session.modified = True  # Ensure session updates persist

    return Response(generate(), content_type="text/plain")

if __name__ == '__main__':
    app.run(debug=True, port=5500, host='0.0.0.0')
