
function sendHeadValue(val) {
    const xhr = new XMLHttpRequest();
    xhr.open('POST', `headAngle/${JSON.stringify(val)}`)
    xhr.send()
}

function sendChangeColorRequest(newColor, cubeId) {
    fetch('/colorChange/', {
        method: 'POST',
        body: JSON.stringify({
            "cubeId": cubeId,
            "newColor": newColor
        }),
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(res => {
        res.text().then(imageName => {

            document.getElementById(imageName).setAttribute('src', "static/temp/" + imageName+".png");
        });
    });
}

function relaunchCozmoProgram() {
    const xhr = new XMLHttpRequest();

    xhr.open('POST', `reload`)
    xhr.send()
}

