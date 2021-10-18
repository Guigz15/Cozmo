import sys
import time
import numpy as np
from cozmo import *

import hand_tracking_module as htm
import cozmo
from cozmo.objects import LightCube1Id, LightCube2Id, LightCube3Id


async def on_cube_tapped(event, *, obj, tap_count, tap_duration, **kw):
    cube_tapped = obj.__getattribute__('object_id')
    print(cube_tapped)
    return cube_tapped
    # handler = robot.Robot.add_event_handler(cozmo.objects.EvtObjectTapped, on_cube_tapped)


def hand_detection(robot: cozmo.robot.Robot):
    # On active le stream
    robot.camera.image_stream_enabled = True
    # On passe la caméra en couleur
    robot.camera.color_image_enabled = True

    try:
        detector = htm.handDetector(detectionCon=0.75)
        tipIds = [4, 8, 12, 16, 20]
        hand = -1
        finalTotal = -2

        while hand != finalTotal:

            latest_image = robot.world.latest_image
            if latest_image:
                # récupération du raw
                im = latest_image.raw_image
                im = np.array(im)

                img = detector.findHands(im)
                lmList = detector.findPosition(img, draw=False)

                if len(lmList) != 0:
                    fingers = []
                    # print(lmList[tipIds[0]][1])

                    # Hand face up
                    if lmList[0][2] > lmList[tipIds[2]][2]:
                        facing = 1
                        # print('Hand face up')
                    else:
                        facing = 0
                        # print('Hand face down')

                    # Left thumb
                    if lmList[tipIds[0]][1] < lmList[tipIds[0] - 1][1] and lmList[tipIds[0]][1] < lmList[tipIds[4]][1]:
                        fingers.append(1)
                        # print('thumb open')
                    # Right thumb
                    elif lmList[tipIds[0]][1] > lmList[tipIds[0] - 1][1] and lmList[tipIds[0]][1] > lmList[tipIds[4]][
                        1]:
                        fingers.append(1)
                        # print('thumb open')
                    else:
                        fingers.append(0)
                        # print('thumb close')

                    for id in range(1, 5):  # y axis
                        if lmList[tipIds[id]][2] < lmList[tipIds[id] - 2][2] and facing == 1:
                            fingers.append(1)
                        elif lmList[tipIds[id]][2] > lmList[tipIds[id] - 2][2] and facing == 0:
                            fingers.append(1)
                        else:
                            fingers.append(0)

                    totalFingers = fingers.count(1)
                    # print(totalFingers)

                    # Permet de vérifier que la valeur vue par le robot est bien celle souhaitée par l'utilisateur
                    if hand != totalFingers:
                        hand = totalFingers
                    else:
                        finalTotal = totalFingers
                        return finalTotal

                    robot.say_text(f'{totalFingers}').wait_for_completed()
                    time.sleep(2)

                else:
                    print("No hand detected")

            # refresh tous les 100 ms
            time.sleep(0.1)

    # pour capter le Ctrl+C et terminer proprement
    except KeyboardInterrupt:
        sys.exit()


def cozmo_program(robot: cozmo.robot.Robot):
    handler = robot.add_event_handler(cozmo.objects.EvtObjectTapped, on_cube_tapped)  # Essayer de le mettre autre part
    cube1 = robot.world.get_light_cube(LightCube1Id)
    cube2 = robot.world.get_light_cube(LightCube2Id)
    cube3 = robot.world.get_light_cube(LightCube3Id)

    if cube1 is not None:
        cube1.set_lights(cozmo.lights.red_light)

    if cube2 is not None:
        cube2.set_lights(cozmo.lights.blue_light)

    if cube3 is not None:
        cube3.set_lights(cozmo.lights.green_light)

    finalResult = -1

    firstNumber = hand_detection(robot)
    robot.say_text(f'{finalResult}').wait_for_completed()


'''
    if cube_tapped == cube1.__getattribute__('object_id'):
        print("Cube1 tapped")
        finalResult = firstNumber + hand_detection(robot)

    if handler.__getattribute__('object_id') == 2:
        print("Cube2 tapped")
        finalResult = firstNumber - hand_detection(robot)

    if handler.__getattribute__('object_id') == 3:
        print("Cube3 tapped")
        finalResult = firstNumber * hand_detection(robot)
'''

cozmo.robot.Robot.drive_off_charger_on_connect = False
cozmo.run_program(cozmo_program, use_viewer=True, force_viewer_on_top=True)
