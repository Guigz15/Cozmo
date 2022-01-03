const gUserAgent = window.navigator.userAgent;

const gIsMicrosoftBrowser = gUserAgent.indexOf('MSIE ') > 0 || gUserAgent.indexOf('Trident/') > 0 || gUserAgent.indexOf('Edge/') > 0;

if (gIsMicrosoftBrowser) {
    document.getElementById("cozmoImageMicrosoftWarning").style.display = "block";
}

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

}