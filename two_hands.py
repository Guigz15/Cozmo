import sys
import cozmo

import UI
import hand as hd
import time
import numpy as np
import cubes as cb
from PIL import ImageOps


def hand_detection(robot: cozmo.robot.Robot):
    """
    This function will use the two above functions to count fingers on both hands with cozmo's camera.

    :param robot: An instance of cozmo Robot.
    :return: **finalTotal** - An int that represents the counted fingers.
    """

    # Enable camera streaming
    robot.camera.image_stream_enabled = True
    # Enable color image
    robot.camera.color_image_enabled = True
    # Set cozmo's head angle
    robot.set_head_angle(cozmo.robot.MAX_HEAD_ANGLE / 2).wait_for_completed()

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
                        robot.say_text(f'{totalFingers}').wait_for_completed()
                        robot.play_anim_trigger(cozmo.anim.Triggers.CodeLabHappy,
                                                ignore_lift_track=True, ignore_body_track=True).wait_for_completed()
                        return finalTotal

                    time.sleep(2)

                else:
                    print("No hand detected")

                    # One more no hand detected
                    nbNoHand += 1
                    robot.play_anim(name="anim_mm_thinking", ignore_head_track=True).wait_for_completed()

                    # If hands are not detected for a long time
                    if nbNoHand == 100:
                        nbNoHand = 0
                        robot.say_text("Je ne te vois pas").wait_for_completed()
                        robot.play_anim(name="anim_bored_01", ignore_body_track=True).wait_for_completed()
                        robot.set_head_angle(cozmo.robot.MAX_HEAD_ANGLE / 2).wait_for_completed()

    # To detect Ctrl+C and shut down properly
    except KeyboardInterrupt:
        sys.exit()


def cozmo_program(robot: cozmo.robot.Robot):
    """
    This function will be executed by cozmo and handled all interactions between cozmo, cubes and the code.

    :param robot: An instance of cozmo Robot.
    """
    handler = robot.add_event_handler(cozmo.objects.EvtObjectTapped,
                                      cb.Cubes.on_cube_tapped)  # Essayer de le mettre autre part

    cubes = cb.Cubes(robot)

    # The final result initialized
    finalResult = -1

    # Detect the first number
    firstNumber = hand_detection(robot)
    print(firstNumber)

    # Wait for any cubes tapped
    print('J\'' + 'attends que tu tapes')
    robot.world.wait_for(cozmo.objects.EvtObjectTapped)

    operation = cubes.cube_blinking(cubes.cube_tapped_id)

    # Detect the second number
    secondNumber = hand_detection(robot)

    if operation == '+':
        finalResult = firstNumber + secondNumber
    elif operation == '-':
        finalResult = firstNumber - secondNumber
        if finalResult < 0:
            finalResult = "moins" + str(-finalResult)
    elif operation == '*':
        finalResult = firstNumber * secondNumber

    # Cozmo say the result
    robot.say_text(f'{firstNumber}' + operation + f'{secondNumber}' + "=" + f'{finalResult}').wait_for_completed()

    print(finalResult)


# To prevent Cozmo to drive off the charger when SDK mode enabled
cozmo.robot.Robot.drive_off_charger_on_connect = False
# To run the program on Cozmo
cozmo.run_program(cozmo_program, use_viewer=True)
