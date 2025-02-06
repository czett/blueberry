from flask import Flask, render_template, request, session
import ollama, json
from deep_translator import GoogleTranslator

with open("prompt_config.json", "r") as pc:
    prefixes = json.load(pc)
    prompt_prefix = prefixes["standard"]

app = Flask(__name__)
app.secret_key = "wefhwoeifhaoeiurhgqoeirgh"

def translate(text: str, flang: str, tlang: str) -> str:
    return GoogleTranslator(source=flang, target=tlang).translate(text)

@app.route('/')
def index():
    session["count"] = 0
    return render_template('index.html')

@app.route('/answer', methods=["POST", "GET"])
def answer():
    data = request.get_json()
    message = prompt_prefix + data['message']
    if session["count"] > 1:
        message = data['message']
    session["count"] += 1

    def generate():
        stream = ollama.chat(model="llama3.2:1b", messages=[{"role": "user", "content": message}], stream=True)
        
        for chunk in stream:
            if chunk["message"]["content"] is not None:
                yield chunk["message"]["content"]

    return generate(), {"Content-Type": "text/plain"}

if __name__ == '__main__':
    app.run(debug=True, port=5500, host='0.0.0.0')