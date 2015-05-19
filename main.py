from panda3d.core import loadPrcFile
from panda3d.core import ConfigVariableBool
from spanda3D.engine import Engine
from sky.cube import SkyCube
from spanda3D.light import Light
from spanda3D.joystick import XboxControllerHandler

if __name__ == "__main__":
    loadPrcFile("config.prc")
    mouse = ConfigVariableBool('keyboard_mouse')
    e = Engine(mouse.getValue())
    SkyCube(e)
    Light(e)
    if mouse:
        print("Using keyboard-mouse controller")
    else:
        print("Using X-Box controller")
        XboxControllerHandler(e)
    e.run()
