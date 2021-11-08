import cozmo


class Cubes:
    cube_tapped_id = 0
    robot = cozmo.robot.Robot

    def __init__(self, cube_id, robot):
        self.cube_tapped_id = cube_id
        self.robot = robot

    async def on_cube_tapped(self, **kw):
        Cubes.cube_tapped_id = self.__getattribute__('obj').__getattribute__('object_id')


