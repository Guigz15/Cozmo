import time

import cozmo
from cozmo.objects import LightCube1Id, LightCube2Id, LightCube3Id


class Cubes:
    """
    This class represents the Cozmo's cubes and perform on tapped detection or blinking.
    """
    cube_tapped_id = 0
    robot = cozmo.robot.Robot
    cube1 = None
    cube2 = None
    cube3 = None
    cube1_color = None
    cube2_color = None
    cube3_color = None

    def __init__(self, robot):

        self.robot = robot
        self.cube1 = robot.world.get_light_cube(LightCube1Id)
        self.cube2 = robot.world.get_light_cube(LightCube2Id)
        self.cube3 = robot.world.get_light_cube(LightCube3Id)

        # Initialize cube one's color (red)
        if self.cube1 is not None:
            self.cube1_color = cozmo.lights.red_light
            self.cube1.set_lights(self.cube1_color)

        # Initialize cube two's color (blue)
        if self.cube2 is not None:
            self.cube2_color = cozmo.lights.blue_light
            self.cube2.set_lights(self.cube2_color)

        # Initialize cube three's color (green)
        if self.cube3 is not None:
            self.cube3_color = cozmo.lights.green_light
            self.cube3.set_lights(self.cube3_color)

    async def on_cube_tapped(self, **kw):
        """
        The function allows to get the cube object that is tapped.
        """
        Cubes.cube_tapped_id = self.__getattribute__('obj').__getattribute__('object_id')

    def cube_blinking(self, id_cube_tapped):
        """
        This function performs cube blinking.

        :param id_cube_tapped: The id of the cube tapped.
        :return: A string that represents operators linked to the cube tapped.
        """
        if id_cube_tapped == self.cube1.__getattribute__('object_id'):
            self.robot.say_text("plus", in_parallel=True).wait_for_completed()

            # blinking of tapped cube 1
            for i in range(4):
                self.cube1.set_light_corners(self.cube1_color, cozmo.lights.off_light,
                                             self.cube1_color, cozmo.lights.off_light)
                time.sleep(0.3)
                self.cube1.set_light_corners(cozmo.lights.off_light, self.cube1_color,
                                             cozmo.lights.off_light, self.cube1_color)
                time.sleep(0.3)
            self.cube1.set_lights(self.cube1_color)
            return "+"

        # If cube 2 is tapped, it will make a difference
        if id_cube_tapped == self.cube2.__getattribute__('object_id'):
            self.robot.say_text("moins", in_parallel=True).wait_for_completed()

            # blinking of tapped cube 2
            for i in range(4):
                self.cube2.set_light_corners(cozmo.lights.blue_light, cozmo.lights.off_light,
                                             cozmo.lights.blue_light, cozmo.lights.off_light)
                time.sleep(0.3)
                self.cube2.set_light_corners(cozmo.lights.off_light, cozmo.lights.blue_light,
                                             cozmo.lights.off_light, cozmo.lights.blue_light)
                time.sleep(0.3)
            self.cube2.set_lights(cozmo.lights.blue_light)
            return "-"

        if id_cube_tapped == self.cube3.__getattribute__('object_id'):
            self.robot.say_text("fois", in_parallel=True).wait_for_completed()

            # blinking of tapped cube 3
            for i in range(4):
                self.cube3.set_light_corners(cozmo.lights.green_light, cozmo.lights.off_light,
                                             cozmo.lights.green_light, cozmo.lights.off_light)
                time.sleep(0.3)
                self.cube3.set_light_corners(cozmo.lights.off_light, cozmo.lights.green_light,
                                             cozmo.lights.off_light, cozmo.lights.green_light)
                time.sleep(0.3)
            self.cube3.set_lights(cozmo.lights.green_light)
            return "*"
