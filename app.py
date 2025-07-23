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
    session.clear()
    return render_template('index.html')

@app.route('/answer', methods=["POST"])
def answer():
    data = request.get_json()
    user_message = data['message']

    if "messages" not in session:
        session["messages"] = []

    session["messages"].append({"role": "user", "content": user_message})
    messages_copy = list(session["messages"])

    global assistant_response
    assistant_response = ""

    # stupid a$$ github copilot couldnt figure out how to do this (history and realtime)
    # turns out even I am smart enough to do ts
    # it even suggests these comments to mob itself wth

    def generate():
        global assistant_response
        for chunk in ollama.chat(model="qwen2.5:3b", messages=messages_copy, stream=True):
            if chunk["message"]["content"]:
                assistant_response += chunk["message"]["content"]
                yield chunk["message"]["content"]

    session["messages"].append({"role": "assistant", "content": assistant_response})
    session.modified = True

    # store messages locally, i can extend it to multiple chats later on then
    # with open("chat_sessions/session_1.json", "w") as f:
    #     data = {"messages": session["messages"]}
    #     json.dump(data, f)
    
    #print(assistant_response)
    return Response(generate(), content_type="text/plain")

if __name__ == '__main__':
    app.run(debug=True, port=5500, host='0.0.0.0')
