from flask import Flask, render_template, request
import ollama

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/answer', methods=["POST", "GET"])
def answer():
    data = request.get_json()
    message = data['message']

    def generate():
        stream = ollama.chat(model="llama3.2:1b", messages=[{"role": "user", "content": message}], stream=True)
        
        for chunk in stream:
            if chunk["message"]["content"] is not None:
                yield chunk["message"]["content"]

    return generate(), {"Content-Type": "text/plain"}

if __name__ == '__main__':
    app.run(debug=True, port=5500)