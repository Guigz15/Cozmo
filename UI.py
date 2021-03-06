import asyncio
import io
import json
import sys
import threading
import signal
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
    """
    Create a place-holder PIL image to use until we have a live feed from Cozmo

    :param image_width: Image's width.
    :param image_height: Image's height.
    :param do_gradient: To perform a gradient.
    :return: **image** - Cozmo's image.
    """

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
robot = None
_default_camera_image = create_default_image(320, 240)


class RemoteControlCozmo:
    """
    This class allow to control cozmo and its cubes with web page.
    """

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
        """
        Allow updating head angle.

        :param angleValue: New head angle value.
        """

        angle = cozmo.util.degrees(float(angleValue))
        self.cozmo.set_head_angle(angle, in_parallel=True)

    def update_cube_color(self, cubeId, newColor):
        """
        Allow updating cube's color.

        :param cubeId: The cube updated.
        :param newColor: New color of the cube linked to cubeID.
        """
        r, g, b = hexa_color_converter(newColor)
        color = cozmo.lights.Light(cozmo.lights.Color(rgb=(r, g, b)))

        if cubeId == "Cozmo_cube_add":
            self.cube1.set_lights(color)
            self.cubes.cube1_color = color

        if cubeId == "Cozmo_cube_substract":
            self.cube2.set_lights(color)
            self.cubes.cube2_color = color

        if cubeId == "Cozmo_cube_multiply":
            self.cube3.set_lights(color)
            self.cubes.cube3_color = color


@flask_app.route("/")
def handle_index_page():
    """
    Display html page.

    :return: Source code of our html page.
    """

    return render_template('Cozmo_page.html')


def streaming_video(url_root):
    """
    Video streaming generator function.

    :param url_root: Html page's URL.
    """

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
    """
    To get cozmo's image.

    :return: Cozmo's image.
    """

    if remote_control_cozmo:
        try:
            image = remote_control_cozmo.cozmo.world.latest_image
            image = image.raw_image

            if image:
                return flask_helpers.serve_pil_image(image)
        except cozmo.exceptions.SDKShutdown:
            requests.post('shutdown')
    return flask_helpers.serve_pil_image(_default_camera_image)


@flask_app.route("/cozmoImage")
def handle_cozmoImage():
    return flask_helpers.stream_video(streaming_video, request.url_root)


@flask_app.route('/shutdown', methods=['POST'])
def shutdown():
    """
    Shutdown flask server.
    """

    flask_helpers.shutdown_flask(request)
    return ""


@flask_app.route('/reload', methods=['POST'])
def reload():
    cozmoThread = Thread(target=two_hands.cozmo_program, args=(robot, remote_control_cozmo.cubes), daemon=True)
    cozmoThread.start()
    return ""


@flask_app.route('/headAngle/<string:angleValue>', methods=['POST'])
def headAngle(angleValue):
    """
    Get angle value from the slider in html page and update cozmo's head angle.

    :param angleValue: Angle value from slider.
    """

    angleValue = json.loads(angleValue)
    remote_control_cozmo.update_head_angle(angleValue)
    return ""


def hexa_color_converter(color_code):
    """
    Convert hex code to rgb values.

    :param color_code: Hex code color.
    :return: An absurd value to detect error.
    """
    if color_code[0] == "#" and len(color_code) == 7:
        return int(color_code[1:3], 16), int(color_code[3:5], 16), int(color_code[5:7], 16)
    return -1, -1, -1


def recolor_cube(image_path, color_code, save_image_name):
    """
    Color cube image with new color.

    :param image_path: Original image to color.
    :param color_code: Hex code color.
    :param save_image_name: Name of modified image.
    """

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

    for i in range(0, 30):
        for j in range(30, 110):
            for k in range(coul - 1):
                if all(x == y for x, y in zip(im[i][j], green)) or all(x == y for x, y in zip(im[i][j], red)) or all(
                        x == y for x, y in zip(im[i][j], blue)):
                    im[i][j] = (r, g, b, 255)
                    im[149 - i][149 - j] = (r, g, b, 255)
                    im[j][i] = (r, g, b, 255)
                    im[149 - j][149 - i] = (r, g, b, 255)
            im[i][j][3] = 255

    imag = Image.fromarray(im)
    imag.save(save_image_name)


@flask_app.route('/colorChange/', methods=['POST'])
def colorChange():
    """
    Color real cozmo's cube.

    :return: ID of modified color.
    """

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
    global robot
    robot = sdk_conn.wait_for_robot()
    robot.enable_device_imu(True, True, True)

    # Turn on image receiving by the camera
    robot.camera.image_stream_enabled = True
    # Enable color image
    robot.camera.color_image_enabled = True

    global remote_control_cozmo
    remote_control_cozmo = RemoteControlCozmo(robot, cb.Cubes(robot))

    cozmoThread = Thread(target=two_hands.cozmo_program, args=(robot, remote_control_cozmo.cubes), daemon=True)
    cozmoThread.start()

    flask_helpers.run_flask(flask_app)


if __name__ == '__main__':
    cozmo.setup_basic_logging()
    cozmo.robot.Robot.drive_off_charger_on_connect = False  # RC can drive off charger if required
    try:
        cozmo.connect(run)
    except KeyboardInterrupt as e:
        sys.exit()
    except cozmo.ConnectionError as e:
        sys.exit("A connection error occurred: %s" % e)
