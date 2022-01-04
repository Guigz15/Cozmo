import asyncio
import io
import json
import math
import sys
import flask_helpers
import cozmo
from threading import Thread
import two_hands

try:
    from flask import Flask, request
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

    def __init__(self, coz):
        self.cozmo = coz

    def update_head_angle(self, angleValue):
        angle = cozmo.util.degrees(float(angleValue))
        self.cozmo.set_head_angle(angle, in_parallel=True)


@flask_app.route("/")
def handle_index_page():
    return '''
    <html>
        <head>
            <title>User Interface for Cozmo</title>
        </head>
        <style>
            input[type="range"] {
                -webkit-appearance: slider-vertical;
            }
            
            input[type="range"]::-webkit-slider-runnable-track {
                height: 100%;
                width: 22px;
                border-radius: 10px;
                background-color: #eee;
                border: 2px solid #ccc;
            }
        </style>
        <body>
            <h1>Finger counter and operation with Cozmo</h1>
            <table>
                <tr>
                    <td valign = top>
                        <img src="cozmoImage" id="cozmoImageId" width=640 height=480>
                        <div id="DebugInfoId"></div>
                    </td>
                    <td width=30></td>
                    <td valign=top>
                        <h3>Cozmo's head angle</h3>
                        <br>
                        <input type="range" id="myRange" value="9.75" min="-25" max="44.5" step="0.1" onchange="sendHeadValue(this.value);" 
                            oninput="sendHeadValue(this.value)">
                    </td>
                </tr>
            </table>

            <script type="text/javascript">
                var gUserAgent = window.navigator.userAgent;
                var gIsMicrosoftBrowser = gUserAgent.indexOf('MSIE ') > 0 || gUserAgent.indexOf('Trident/') > 0 || gUserAgent.indexOf('Edge/') > 0;

                if (gIsMicrosoftBrowser) {
                    document.getElementById("cozmoImageMicrosoftWarning").style.display = "block";
                }
           
                function sendHeadValue(val) {
                    var xhr = new XMLHttpRequest();
                    xhr.open('POST', `headAngle/${JSON.stringify(val)}`)
                    xhr.send()
                }
            </script>
        </body>
    </html>
    '''


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


def run(sdk_conn):
    robot = sdk_conn.wait_for_robot()
    robot.enable_device_imu(True, True, True)

    # Turn on image receiving by the camera
    robot.camera.image_stream_enabled = True
    # Enable color image
    robot.camera.color_image_enabled = True

    global remote_control_cozmo
    remote_control_cozmo = RemoteControlCozmo(robot)
    cozmoThread = Thread(target=two_hands.cozmo_program, args=(robot,))
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
