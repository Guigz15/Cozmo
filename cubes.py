import cozmo


class Cubes:
    cube_tapped = 0
    robot = cozmo.robot.Robot

    def __init__(self, cube, robot):
        self.cube_tapped = cube
        self.robot = robot

    async def on_cube_tapped(self, **kw):
        Cubes.cube_tapped = self.__getattribute__('obj').__getattribute__('object_id')
        # print(event.__getattribute__('obj').__getattribute__('object_id'))