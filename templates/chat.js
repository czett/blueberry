const submitBtn = document.querySelector('button');
const input = document.querySelector('input');

let msgCount = 0;

function intToString(num) {
    return num.toString();
}

submitBtn.addEventListener('click', async(e) => {
    e.preventDefault();

    let prompt = "p" + intToString(msgCount);
    let answer = "a" + intToString(msgCount);

    console.log(prompt);

    document.querySelector("." + prompt).innerHTML = input.value;

    const response = await fetch('/answer', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({message: input.value})
    });
    
    const reader = response.body.getReader();
    let output = "";

    while (true) {
        const { done, value } = await reader.read();

        if (done) {
            break;
        }

        output += new TextDecoder().decode(value);
        document.querySelector("." + answer).innerHTML = marked.parse(output);
    }

    // create next obj for prompt and answer
    const newPrompt = document.createElement('div');
    newPrompt.className = "prompt p" + intToString(msgCount + 1);
    document.querySelector('.chat').appendChild(newPrompt);

    const newAnswer = document.createElement('div');
    newAnswer.className = "answer a" + intToString(msgCount + 1);
    document.querySelector('.chat').appendChild(newAnswer);

    msgCount++;
});