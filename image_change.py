from PIL import Image
import numpy as np
from flask import Flask, render_template, request


def hexa_color_converter(color_code):
    if color_code[0:2] == "0x" and len(color_code) == 8:
        return int(color_code[2:4], 16), int(color_code[4:6], 16), int(color_code[6:8], 16)
    return -1, -1, -1


def recolor_cube(image_path, color_code, save_image_name):
    r, g, b = hexa_color_converter(color_code)
    if r == -1:
        print("Bad color format")
        return
    green = (0, 255, 0, 255)
    image = Image.open(image_path)
    im = np.array(image)

    larg, long, coul = im.shape

    for i in range(2, 30):
        for j in range(44, 105):
            for k in range(coul - 1):
                if all(x == y for x, y in zip(im[i][j], green)):
                    im[i][j] = (r, g, b, 255)
                    im[148 - i][148 - j] = (r, g, b, 255)
                    im[j][i] = (r, g, b, 255)
                    im[148 - j][148 - i] = (r, g, b, 255)
            im[i][j][3] = 255

    imag = Image.fromarray(im)
    imag.save(save_image_name)


app = Flask(__name__)


@app.route('/')
def index():
    return render_template('Cozmo_page.html')


@app.route('/colorChange/', methods=['POST'])
def colorChange():
    arguments = request.get_json()

    newColor = arguments['newColor']
    cubeId = arguments['cubeId']


    recolor_cube("static/" + cubeId+".png", newColor, "static/temp/" + cubeId+".png")
    return cubeId


@app.after_request
def add_header(r):
    r.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    r.headers['Pragma'] = 'no-cache'
    return r


if __name__ == '__main__':
    app.run(debug=True)

# recolor_cube('autre.png', "0x00FF00", 'autre2.png')
