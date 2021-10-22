import sys
import time
import numpy as np
import hand_tracking_module as htm
import cubes as cb
import cozmo
from cozmo.objects import LightCube1Id, LightCube2Id, LightCube3Id


def hand_detection(robot: cozmo.robot.Robot):
    # On active le stream
    robot.camera.image_stream_enabled = True
    # On passe la caméra en couleur
    robot.camera.color_image_enabled = True
    # On règle l'angle de la tête de Cozmo
    robot.set_head_angle(cozmo.robot.MAX_HEAD_ANGLE/2).wait_for_completed()

    try:
        detector = htm.HandDetector(detectionCon=0.75)
        tipIds = [4, 8, 12, 16, 20]
        hand = -1
        finalTotal = -2
        nbNoHand = 0

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
                        robot.play_anim_trigger(cozmo.anim.Triggers.CodeLabHappy).wait_for_completed()
                        return finalTotal

                    robot.say_text(f'{totalFingers}').wait_for_completed()
                    time.sleep(2)

                else:
                    print("No hand detected")
                    nbNoHand += 1
                    robot.play_anim(name="anim_mm_thinking", ignore_head_track=True).wait_for_completed()
                    if nbNoHand == 20:
                        nbNoHand = 0
                        robot.say_text("Je ne te vois pas").wait_for_completed()
                        robot.play_anim(name="anim_bored_01", ignore_body_track=True).wait_for_completed()
                        robot.set_head_angle(cozmo.robot.MAX_HEAD_ANGLE/2).wait_for_completed()

            # refresh tous les 100 ms
            time.sleep(0.1)

    # pour capter le Ctrl+C et terminer proprement
    except KeyboardInterrupt:
        sys.exit()


def cozmo_program(robot: cozmo.robot.Robot):
    handler = robot.add_event_handler(cozmo.objects.EvtObjectTapped,
                                      cb.Cubes.on_cube_tapped)  # Essayer de le mettre autre part
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
    print(firstNumber)

    print('Jattend que tu tapes')
    robot.world.wait_for(cozmo.objects.EvtObjectTapped)
    if cb.Cubes.cube_tapped == cube1.__getattribute__('object_id'):
        print("Cube1 tapped")
        finalResult = firstNumber + hand_detection(robot)

    if cb.Cubes.cube_tapped == cube2.__getattribute__('object_id'):
        print("Cube2 tapped")
        finalResult = firstNumber - hand_detection(robot)

    if cb.Cubes.cube_tapped == cube3.__getattribute__('object_id'):
        print("Cube3 tapped")
        finalResult = firstNumber * hand_detection(robot)

    print(finalResult)
    robot.say_text(f'{finalResult}').wait_for_completed()


cozmo.robot.Robot.drive_off_charger_on_connect = False
cozmo.run_program(cozmo_program, use_viewer=True, force_viewer_on_top=True)
