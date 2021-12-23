import json
import sys
import time

import cozmo
import numpy as np
from PIL import ImageOps

import cubes as cb
import hand as hd
try:
    import requests
except ImportError:
    sys.exit("Cannot import from requests: Do `pip3 install --user requests` to install")

def hand_detection(robot: cozmo.robot.Robot):
    """
    This function will use the two above functions to count fingers on both hands with cozmo's camera.

    :param robot: An instance of cozmo Robot.
    :return: **finalTotal** - An int that represents the counted fingers.
    """

    try:
        hand = -1
        finalTotal = -2

        # Times of no hand detected
        nbNoHand = 0

        # To check twice the number of fingers
        while hand != finalTotal:

            # Get the image of cozmo's camera
            latest_image = robot.world.latest_image

            if latest_image:
                # Get the raw image
                im = latest_image.raw_image
                # Flip horizontally the image
                im = ImageOps.mirror(im)
                # Transform image in a numpy array
                im = np.array(im)

                # Hand landmarks process
                frame, results = hd.detectHandsLandmarks(im, hd.hands_videos, display=False)

                # Check if the hands landmarks in the frame are detected.
                if results.multi_hand_landmarks:
                    # Count the number of fingers up of each hand in the frame.
                    frame, fingers_statuses, count = hd.countFingers(frame, results, display=False)
                    totalFingers = sum(count.values())

                    # Check if detected number is the right number
                    if hand != totalFingers:
                        hand = totalFingers
                    else:
                        finalTotal = totalFingers
                        if finalTotal == 1 and (fingers_statuses.get("RIGHT_MIDDLE") is True or fingers_statuses.get(
                                "LEFT_MIDDLE") is True):
                            robot.say_text("Tu veux te battre LAAAAAAA", in_parallel=True).wait_for_completed()
                        robot.say_text(f'{totalFingers}', in_parallel=True).wait_for_completed()
                        currentHeadAngle = robot.head_angle
                        robot.play_anim_trigger(cozmo.anim.Triggers.CodeLabHappy,
                                                ignore_lift_track=True, ignore_body_track=True,
                                                in_parallel=True).wait_for_completed()
                        robot.set_head_angle(currentHeadAngle, in_parallel=True).wait_for_completed()
                        return finalTotal

                    time.sleep(2)

                else:
                    print("No hand detected")

                    # One more no hand detected
                    nbNoHand += 1
                    robot.play_anim(name="anim_mm_thinking", ignore_head_track=True,
                                    in_parallel=True).wait_for_completed()

                    # If hands are not detected for a long time
                    if nbNoHand == 100:
                        nbNoHand = 0
                        currentHeadAngle = robot.head_angle
                        robot.say_text("Je ne te vois pas", in_parallel=True).wait_for_completed()
                        robot.play_anim(name="anim_bored_01", ignore_body_track=True,
                                        in_parallel=True).wait_for_completed()
                        robot.set_head_angle(currentHeadAngle, in_parallel=True).wait_for_completed()

    # To detect Ctrl+C and shut down properly
    except KeyboardInterrupt:
        sys.exit()


def cozmo_program(robot: cozmo.robot.Robot, cubesArg):
    """
    This function will be executed by cozmo and handled all interactions between cozmo, cubes and the code.

    :param cubesArg:
    :param robot: An instance of cozmo Robot.
    """
    # Set cozmo's head angle
    robot.set_head_angle(cozmo.robot.MAX_HEAD_ANGLE / 2, in_parallel=True).wait_for_completed()

    handler = robot.add_event_handler(cozmo.objects.EvtObjectTapped,
                                      cb.Cubes.on_cube_tapped)

    cubes = cubesArg

    # The final result initialized
    finalResult = -1

    # Detect the first number
    firstNumber = hand_detection(robot)
    print(firstNumber)
    requests.post("http://127.0.0.1:5000/", data={'firstNumber': firstNumber})

    # Wait for any cubes tapped
    print('J\'' + 'attends que tu tapes')
    robot.say_text("Tape sur un cube").wait_for_completed()
    robot.world.wait_for(cozmo.objects.EvtObjectTapped)  # Timeout par defaut 30 secondes
    operation = cubes.cube_blinking(cubes.cube_tapped_id)

    # Detect the second number
    secondNumber = hand_detection(robot)
    requests.post("http://127.0.0.1:5000/", data={'secondNumber': secondNumber})

    if operation == '+':
        finalResult = firstNumber + secondNumber
    elif operation == '-':
        finalResult = firstNumber - secondNumber
        if finalResult < 0:
            finalResult = "moins" + str(-finalResult)
    elif operation == '*':
        finalResult = firstNumber * secondNumber

    # Cozmo say the result
    robot.say_text(f'{firstNumber}' + operation + f'{secondNumber}' + "=" + f'{finalResult}',
                   in_parallel=True).wait_for_completed()

    print(finalResult)

