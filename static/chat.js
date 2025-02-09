const submitBtn = document.querySelector('button');
const input = document.querySelector('input');

// console.log("chat.js loaded");

let msgCount = 0;

function intToString(num) {
    return num.toString();
}

submitBtn.addEventListener('click', async(e) => {
    e.preventDefault();
    input.disabled = true;
    
    let prompt = "p" + intToString(msgCount);
    let answer = "a" + intToString(msgCount);

    // create next obj for prompt and answer
    const newPrompt = document.createElement('div');
    newPrompt.className = "prompt";
    const newPromptContent = document.createElement('div');
    newPromptContent.className = "p" + intToString(msgCount);
    newPrompt.appendChild(newPromptContent);
    document.querySelector('.chat').appendChild(newPrompt);

    const newAnswer = document.createElement('div');
    newAnswer.className = "answer";
    const newAnswerContent = document.createElement('div');
    newAnswerContent.className = "a" + intToString(msgCount);
    newAnswer.appendChild(newAnswerContent);
    document.querySelector('.chat').appendChild(newAnswer);

    document.querySelector("." + prompt).innerHTML = input.value;
    const inp_prompt = input.value;
    input.value = "";
    
    const response = await fetch('/answer', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({message: inp_prompt})
    });

    const reader = response.body.getReader();
    let output = "";
    
    while (true) {
        const { done, value } = await reader.read();
        
        if (done) {
            break;
        }
        
        output += new TextDecoder().decode(value);
        document.querySelector("." + answer).innerHTML = "<p>" + marked.parse(output) + "</p>";
        document.querySelector('.chat').scrollTop = document.querySelector('.chat').scrollHeight;
    }
    
    input.disabled = false;
    input.focus();
    msgCount++;
});