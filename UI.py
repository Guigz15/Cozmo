import asyncio
import io
import json
import sys
import flask_helpers
import cozmo
import cubes as cb
import numpy as np
from threading import Thread
import two_hands

try:
    from flask import Flask, render_template, request
except ImportError:
    sys.exit("Cannot import from flask: Do `pip3 install --user flask` to install")

try:
    from PIL import Image, ImageDraw, ImageOps
except ImportError:
    sys.exit("Cannot import from PIL: Do `pip3 install --user Pillow` to install")

try:
    import requests
except ImportError:
    sys.exit("Cannot import from requests: Do `pip3 install --user requests` to install")


def create_default_image(image_width, image_height, do_gradient=False):
    '''Create a place-holder PIL image to use until we have a live feed from Cozmo'''
    image_bytes = bytearray([0x70, 0x70, 0x70]) * image_width * image_height

    if do_gradient:
        i = 0
        for y in range(image_height):
            for x in range(image_width):
                image_bytes[i] = int(255.0 * (x / image_width))  # R
                image_bytes[i + 1] = int(255.0 * (y / image_height))  # G
                image_bytes[i + 2] = 0  # B
                i += 3

    image = Image.frombytes('RGB', (image_width, image_height), bytes(image_bytes))
    return image


flask_app = Flask(__name__)
remote_control_cozmo = None
_default_camera_image = create_default_image(320, 240)


class RemoteControlCozmo:
    cube1 = None
    cube2 = None
    cube3 = None
    cubes = None

    def __init__(self, coz, cubes):
        self.cozmo = coz
        self.cubes = cubes
        self.cube1 = self.cubes.cube1
        self.cube2 = self.cubes.cube2
        self.cube3 = self.cubes.cube3

    def update_head_angle(self, angleValue):
        angle = cozmo.util.degrees(float(angleValue))
        self.cozmo.set_head_angle(angle, in_parallel=True)

    def update_cube_color(self, cubeId, newColor):
        r, g, b = hexa_color_converter(newColor)
        color = cozmo.lights.Light(cozmo.lights.Color(rgb=(r, g, b)))

        if cubeId == "Cozmo_cube_add":
            self.cube1.set_lights(color)
            self.cubes.cube1_color = color

        if cubeId == "Cozmo_cube_substract":
            self.cube2.set_lights(color)
            self.cubes.cube2 = color

        if cubeId == "Cozmo_cube_multiply":
            self.cube3.set_lights(color)
            self.cubes.cube3 = color


@flask_app.route("/")
def handle_index_page():
    return render_template('Cozmo_page.html')


def streaming_video(url_root):
    '''Video streaming generator function'''
    try:
        while True:
            if remote_control_cozmo:
                image = remote_control_cozmo.cozmo.world.latest_image
                image = image.raw_image
                image = ImageOps.mirror(image)

                img_io = io.BytesIO()
                image.save(img_io, 'PNG')
                img_io.seek(0)
                yield (b'--frame\r\n'
                       b'Content-Type: image/png\r\n\r\n' + img_io.getvalue() + b'\r\n')
            else:
                asyncio.sleep(.1)
    except cozmo.exceptions.SDKShutdown:
        # Tell the main flask thread to shutdown
        requests.post(url_root + 'shutdown')


def serve_single_image():
    if remote_control_cozmo:
        try:
            image = remote_control_cozmo.cozmo.world.latest_image
            image = image.raw_image

            if image:
                return flask_helpers.serve_pil_image(image)
        except cozmo.exceptions.SDKShutdown:
            requests.post('shutdown')
    return flask_helpers.serve_pil_image(_default_camera_image)


def is_microsoft_browser(request):
    agent = request.user_agent.string
    return 'Edge/' in agent or 'MSIE ' in agent or 'Trident/' in agent


@flask_app.route("/cozmoImage")
def handle_cozmoImage():
    if is_microsoft_browser(request):
        return serve_single_image()
    return flask_helpers.stream_video(streaming_video, request.url_root)


@flask_app.route('/shutdown', methods=['POST'])
def shutdown():
    flask_helpers.shutdown_flask(request)
    return ""


@flask_app.route('/headAngle/<string:angleValue>', methods=['POST'])
def headAngle(angleValue):
    angleValue = json.loads(angleValue)
    remote_control_cozmo.update_head_angle(angleValue)
    return ""


def hexa_color_converter(color_code):
    if color_code[0:2] == "0x" and len(color_code) == 8:
        return int(color_code[2:4], 16), int(color_code[4:6], 16), int(color_code[6:8], 16)
    return -1, -1, -1


def recolor_cube(image_path, color_code, save_image_name):
    r, g, b = hexa_color_converter(color_code)
    if r == -1:
        print("Bad color format")
        return
    red = (255, 0, 0, 255)
    green = (0, 255, 0, 255)
    blue = (0, 0, 255, 255)
    image = Image.open(image_path)
    im = np.array(image)

    larg, long, coul = im.shape

    '''TODO: Improved this coloring algorithm'''
    for i in range(0, 30):
        for j in range(30, 110):
            for k in range(coul - 1):
                if all(x == y for x, y in zip(im[i][j], green)) or all(x == y for x, y in zip(im[i][j], red)) or all(x == y for x, y in zip(im[i][j], blue)):
                    im[i][j] = (r, g, b, 255)
                    im[149 - i][149 - j] = (r, g, b, 255)
                    im[j][i] = (r, g, b, 255)
                    im[149 - j][149 - i] = (r, g, b, 255)
            im[i][j][3] = 255

    imag = Image.fromarray(im)
    imag.save(save_image_name)


@flask_app.route('/colorChange/', methods=['POST'])
def colorChange():
    arguments = request.get_json()

    newColor = arguments['newColor']
    cubeId = arguments['cubeId']
    recolor_cube("static/images/" + cubeId + ".png", newColor, "static/temp/" + cubeId + ".png")
    remote_control_cozmo.update_cube_color(cubeId, newColor)
    return cubeId


@flask_app.after_request
def add_header(r):
    r.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    r.headers['Pragma'] = 'no-cache'
    return r


def run(sdk_conn):
    robot = sdk_conn.wait_for_robot()
    robot.enable_device_imu(True, True, True)

    # Turn on image receiving by the camera
    robot.camera.image_stream_enabled = True
    # Enable color image
    robot.camera.color_image_enabled = True

    global remote_control_cozmo
    remote_control_cozmo = RemoteControlCozmo(robot, cb.Cubes(robot))
    cozmoThread = Thread(target=two_hands.cozmo_program, args=(robot, remote_control_cozmo.cubes))
    cozmoThread.start()

    flask_helpers.run_flask(flask_app)


if __name__ == '__main__':
    cozmo.setup_basic_logging()
    cozmo.robot.Robot.drive_off_charger_on_connect = False  # RC can drive off charger if required
    try:
        cozmo.connect(run)
    except KeyboardInterrupt as e:
        pass
    except cozmo.ConnectionError as e:
        sys.exit("A connection error occurred: %s" % e)
