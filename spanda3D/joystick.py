import pygame
from panda3d.core import Vec2

A = 0
B = 1
X = 2
Y = 3
LB = 4
RB = 5
BACK = 6
START = 7
LS = 8
RS = 9


class XboxControllerState:

    def __init__(self, joy):
        self.joy = joy
        self.leftStick = Vec2()
        self.rightStick = Vec2()
        self.dpad = Vec2()
        self.triggers = 0.0
        self.buttons = [False] * self.joy.get_numbuttons()

    def update(self):
        self.leftStick.setX(self.joy.get_axis(0))
        self.leftStick.setY(self.joy.get_axis(1))
        self.rightStick.setX(self.joy.get_axis(4))
        self.rightStick.setY(self.joy.get_axis(3))
        self.triggers = self.joy.get_axis(2)
        for i in range(self.joy.get_numbuttons()):
            self.buttons[i] = self.joy.get_button(i)


class XboxControllerHandler:

    def __init__(self, base):
        self.base = base
        self.controller = None
        pygame.init()
        pygame.joystick.init()
        for i in range(pygame.joystick.get_count()):
            joy = pygame.joystick.Joystick(i)
            name = joy.get_name()
            if "Xbox" in name or "XBOX" in name or "X-Box" in name:
                joy.init()
                self.controller = joy
                self.state = XboxControllerState(joy)
                base.taskMgr.add(self.updateInput, "update input")

    def updateInput(self, task):
        pygame.event.pump()
        if self.controller:
            self.state.update()
            if self.state.buttons[Y]:
                self.base.set_key("ACCEL", True)
            else:
                self.base.set_key("ACCEL", False)
            if self.state.buttons[X]:
                self.base.set_key("DECEL", True)
            else:
                self.base.set_key("DECEL", False)
            if self.state.buttons[LB]:
                self.base.set_key("ROLL_LEFT", True)
            else:
                self.base.set_key("ROLL_LEFT", False)
            if self.state.buttons[RB]:
                self.base.set_key("ROLL_RIGHT", True)
            else:
                self.base.set_key("ROLL_RIGHT", False)
            if self.state.buttons[A]:
                self.base.set_key("FIRE", True)
            else:
                self.base.set_key("FIRE", False)
            if self.state.buttons[B]:
                self.base.set_key("LOCK", True)
            else:
                self.base.set_key("LOCK", False)
            x = self.state.leftStick.getX()
            y = self.state.leftStick.getY()
            self.base.joy_x = self.base.center_x+x*20
            self.base.joy_y = self.base.center_y-y*20
            return task.cont
