from direct.showbase import Audio3DManager
from direct.showbase.ShowBase import ShowBase
from direct.filter.CommonFilters import CommonFilters
from direct.gui.OnscreenText import OnscreenText
from direct.gui.OnscreenImage import OnscreenImage
from panda3d.core import Vec3
from panda3d.core import Vec4
from panda3d.core import BitMask32
from panda3d.core import WindowProperties
from panda3d.core import CollisionTraverser
from panda3d.core import CollisionNode
from panda3d.core import CollisionSphere
from panda3d.core import TransparencyAttrib
from panda3d.core import TextNode
from panda3d.core import lookAt
from panda3d.core import Quat
from panda3d.physics import ActorNode
from panda3d.physics import ForceNode
from panda3d.physics import LinearVectorForce
from panda3d.physics import PhysicsCollisionHandler
from panda3d.ai import AIWorld
from missile import Missile
from enemy import Enemy
from copy import copy
from random import uniform
from random import randint
from particles import Spacedust


class Engine(ShowBase):

    def __init__(self, mouse):
        ShowBase.__init__(self)
        self.mouse = mouse
        self.joy_x = None
        self.joy_y = None
        props = WindowProperties()
        props.setMouseMode(WindowProperties.MRelative)  # keep mouse in screen
        self.disableMouse()
        self.win.requestProperties(props)
        self.setBackgroundColor(0, 0, 0)
        # Make missiles glow
        self.filters = CommonFilters(self.win, self.cam)
        self.filters.setBloom(blend=(0, 0, 0, 1), desat=-0.5, intensity=3.0, size="large")
        self.screen_width = self.win.getXSize()
        self.screen_height = self.win.getYSize()
        self.center_x = self.screen_width/2
        self.center_y = self.screen_height/2
        # self.win.movePointer(0, self.center_x, self.center_y)
        self.enableParticles()
        self.cTrav = CollisionTraverser()
        # self.cTrav.setRespectPrevTransform(True)
        self.pusher = PhysicsCollisionHandler()
        self.pusher.addInPattern('%fn-into-%in')
        self.target = None
        self.maxvel = 50
        self.roll_time = 0
        self.fuel = 1000
        self.ship()
        self.sounds()
        self.hud()
        self.part = Spacedust(self)
        self.events()
        self.camLens.setFov(70)
        self.camLens.setNear(1)
        self.camLens.setFar(500)
        self.get_key = {
            "ACCEL": False,
            "DECEL": False,
            "FORWARD_THRUST": False,
            "REVERSE_THRUST": False,
            "ROLL_LEFT": False,
            "ROLL_RIGHT": False,
            "ROLL_LEFT_BEG": False,
            "ROLL_RIGHT_BEG": False,
            "FIRE": False,
            "FIRING": False,
            "LOCK": False,
            "LOCKING": False,
        }
        self.AIworld = AIWorld(self.render)
        self.taskMgr.add(self.update, "task-update")
        self.taskMgr.doMethodLater(1, self.fuel_usage, "task-fuel-usage")
        self.taskMgr.add(self.AI_update, "AI-update")
        self.gen_enemy()

    def gen_enemy(self):
        x = randint(-1000, 1000)
        y = randint(-1000, 1000)
        z = randint(-1000, 1000)
        Enemy(self, 0, x, y, z)

    def AI_update(self, task):
        self.AIworld.update()
        return task.cont

    def hud(self):
        self.font = self.loader.loadFont("./fnt/subatomic.tsoonami.ttf")
        self.aim = OnscreenImage(image="./png/ring.png", pos=Vec3(0), scale=0.02)
        self.aim.setTransparency(TransparencyAttrib.MAlpha)
        self.locker = OnscreenImage(image="./png/ring.png", pos=Vec3(0), scale=0.12)
        self.locker.setTransparency(TransparencyAttrib.MAlpha)
        self.locker.hide()

        self.txtFuel = OnscreenText(parent=self.render2d, align=TextNode.ALeft, pos=(-0.95, 0.8), text='FUEL', fg=(1, 1, 1, 0.5), scale=0.05, font=self.font, mayChange=True)
        self.txtSpeed = OnscreenText(parent=self.render2d, align=TextNode.ALeft, pos=(-0.95, 0.7), text='SPEED', fg=(1, 1, 1, 0.5), scale=0.05, font=self.font, mayChange=True)
        self.txtDist = OnscreenText(parent=self.render2d, align=TextNode.ALeft, pos=(-0.95, 0.6), text='DIST', fg=(1, 1, 1, 0.5), scale=0.05, font=self.font, mayChange=True)
        self.txtCoord = OnscreenText(parent=self.render2d, align=TextNode.ALeft, pos=(-0.95, 0.5), text='COORD', fg=(1, 1, 1, 0.5), scale=0.05, font=self.font, mayChange=True)
        self.taskMgr.doMethodLater(1, self.instruments, "task-instruments")

    def instruments(self, task):
        self.txtSpeed.setText("SPEED: %s" % str(int(self.mvel)))
        self.txtFuel.setText("FUEL: %s" % str(self.fuel))
        if self.target is not None:
            self.txtDist.setText("DISTANCE: %s" % str(round(self.dist, 1)))
        else:
            self.txtDist.setText("DISTANCE: ---")
        self.txtCoord.setText("COORD: %s %s %s" % (str(round(self.fighter.getX(), 1)), str(round(self.fighter.getY(), 1)), str(round(self.fighter.getZ(), 1))))
        return task.again

    def set_key(self, key, value):
        self.get_key[key] = value

    def toggle_key(self, key):
        self.set_key(key, not self.get_key[key])

    def init_roll(self, a, task):
        if task.time <= 2:
            if self.roll_time <= task.time:
                self.roll_time = task.time
            else:
                self.roll_time += task.time
                if self.roll_time > 2:
                    self.roll_time = 2
            self.fighter.setR(self.fighter.getR() + a * self.roll_time)
        else:
            self.fighter.setR(self.fighter.getR() + a * 2)
        return task.cont

    def end_roll(self, a, b, task):
        if task.time < b:
            self.roll_time -= task.time
            if self.roll_time < 0:
                self.roll_time = 0
            self.fighter.setR(self.fighter.getR() + a * (b - task.time))
            return task.cont
        else:
            return task.done

    def roll(self, a):
        if a > 0:
            self.set_key("ROLL_RIGHT_BEG", True)
        else:
            self.set_key("ROLL_LEFT_BEG", True)
        self.taskMgr.add(self.init_roll, "task-init-roll", extraArgs=[a], appendTask=True)

    def unroll(self, a):
        if a > 0:
            self.set_key("ROLL_RIGHT_BEG", False)
        else:
            self.set_key("ROLL_LEFT_BEG", False)
        self.taskMgr.remove("task-init-roll")
        self.taskMgr.add(self.end_roll, "task-end-roll", extraArgs=[a, self.roll_time], appendTask=True)

    def to_roll(self):
        if self.get_key["ROLL_LEFT"]:
            if not self.get_key["ROLL_LEFT_BEG"]:
                if self.fuel > 5:
                    self.roll(-1)
                    self.snd_roller.play()
        else:
            if self.get_key["ROLL_LEFT_BEG"]:
                self.unroll(-1)
                self.snd_roller.stop()
        if self.get_key["ROLL_RIGHT"]:
            if not self.get_key["ROLL_RIGHT_BEG"]:
                if self.fuel > 5:
                    self.roll(+1)
                    self.snd_roller.play()
        else:
            if self.get_key["ROLL_RIGHT_BEG"]:
                self.unroll(+1)
                self.snd_roller.stop()

    def fuel_usage(self, task):
        if self.get_key["FORWARD_THRUST"] or self.get_key["REVERSE_THRUST"]:
            self.fuel -= 9
        if self.get_key["ROLL_LEFT_BEG"] or self.get_key["ROLL_RIGHT_BEG"]:
            self.fuel -= 4
        self.fuel -= 1
        if self.fuel < 0:
            self.fuel = 0
        return task.again

    def chk_speed(self, mvel):
        if mvel < 0.01:
            # stop fighter dead
            if self.prt.getActive():
                self.set_key("DECEL", False)
            mvel = 0
        if mvel > self.maxvel:
            # stop fighter accelerating
            if self.pft.getActive():
                self.set_key("ACCEL", False)
            mvel = self.maxvel
        self.part.p.renderer.setLineScaleFactor(mvel*2)
        self.part.pn.setPos(self.fighter, 0, 10, 0)
        return mvel

    def thrust_shake(self, task):
        x = uniform(-1000, 1000)
        y = uniform(-1000, 1000)
        self.repos(x, y, 0.001)
        return task.cont

    def thrust_end(self, task):
        if task.time < 5:
            f = (5. - task.time) / 5.
            s = 1000.*f
            x = uniform(-s, s)
            y = uniform(-s, s)
            self.repos(x, y, 0.001)
            self.snd_thrust.setVolume(f)
            return task.cont
        self.snd_thrust.stop()
        return task.done

    def thrust(self, a):
        if a > 0:
            self.set_key("FORWARD_THRUST", True)
        else:
            self.set_key("REVERSE_THRUST", True)
        self.taskMgr.remove("task-thrust-end")
        self.snd_thrust.setVolume(1)
        self.snd_thrust.play()
        self.taskMgr.add(self.thrust_shake, "task-thrust-shake")

    def unthrust(self, a):
        if a > 0:
            self.set_key("FORWARD_THRUST", False)
        else:
            self.set_key("REVERSE_THRUST", False)
        self.taskMgr.remove("task-thrust-shake")
        self.taskMgr.add(self.thrust_end, "task-thrust-end")

    def to_thrust(self):
        if self.get_key["ACCEL"]:
            if self.mvel < self.maxvel - 1:
                if not self.get_key["FORWARD_THRUST"]:
                    if self.fuel > 10:
                        self.pft.setActive(True)
                        self.thrust(+1)
        else:
            if self.get_key["FORWARD_THRUST"]:
                self.pft.setActive(False)
                self.unthrust(+1)
        if self.get_key["DECEL"]:
            if self.mvel > 0:
                if not self.get_key["REVERSE_THRUST"]:
                    if self.fuel > 10:
                        self.prt.setActive(True)
                        self.thrust(-1)
        else:
            if self.get_key["REVERSE_THRUST"]:
                self.prt.setActive(False)
                self.unthrust(-1)

    def events(self):
        self.accept("escape", self.quit)
        self.accept('mouse1', self.set_key, ["FIRE", True])
        self.accept('mouse1-up', self.set_key, ["FIRE", False])
        self.accept('mouse3', self.set_key, ["LOCK", True])
        self.accept('mouse3-up', self.set_key, ["LOCK", False])
        self.accept("w", self.set_key, ["ACCEL", True])
        self.accept("w-up", self.set_key, ["ACCEL", False])
        self.accept("s", self.set_key, ["DECEL", True])
        self.accept("s-up", self.set_key, ["DECEL", False])
        self.accept("a", self.set_key, ["ROLL_LEFT", True])
        self.accept("a-up", self.set_key, ["ROLL_LEFT", False])
        self.accept("d", self.set_key, ["ROLL_RIGHT", True])
        self.accept("d-up", self.set_key, ["ROLL_RIGHT", False])

    def update(self, task):
        self.pos()
        self.speed()
        if self.fuel > 0:
            self.to_roll()
            self.to_thrust()
            self.to_fire()
            self.to_lock()
        self.rehud()
        return task.cont

    def rehud(self):
        if self.target is not None:
            c = self.target.np.getPos(self.fighter)
            self.dist = c.length()
            c.normalize()
            self.d2 = c - Vec3(0, 1, 0)*c.dot(Vec3(0, 1, 0))
            self.target.radar.setPos(self.d2.getX(), 1, self.d2.getZ())

    def sounds(self):
        self.audio3d = Audio3DManager.Audio3DManager(self.sfxManagerList[0], self.camera)
        self.audio3d.setListenerVelocityAuto()
        self.snd_space = self.loader.loadSfx("./snd/space.flac")
        self.snd_space.setLoop(True)
        self.snd_thrust = self.loader.loadSfx("./snd/thrust.flac")
        self.snd_thrust.setLoop(True)
        self.snd_roller = self.loader.loadSfx("./snd/roller.flac")
        self.snd_roller.setLoop(True)
        self.snd_launch = self.loader.loadSfx("./snd/launch.flac")
        self.snd_lock = self.loader.loadSfx("./snd/lock.flac")
        self.snd_space.play()

    def quit(self):
        self.taskMgr.running = False

    def repos(self, x, y, d):
        player_q = self.fighter.getQuat()
        up = player_q.getUp()
        right = player_q.getRight()
        up.normalize()
        right.normalize()
        up_q = copy(player_q)
        right_q = copy(player_q)
        up_q.setFromAxisAngle(-(x * d), up)
        right_q.setFromAxisAngle(y * d, right)
        self.fighter.setQuat(player_q.multiply(up_q.multiply(right_q)))

    def move_end(self, x, y, task):
        if task.time <= 1:
            d = 0.002*(1 - task.time)
            self.repos(x, y, d)
            return task.cont
        return task.done

    def pos(self):
        if self.mouse:
            md = self.win.getPointer(0)
            x = md.getX()
            y = md.getY()
        else:
            x = self.joy_x
            y = self.joy_y
        if self.win.movePointer(0, self.center_x, self.center_y):
            x -= self.center_x
            y -= self.center_y
            if x != 0 or y != 0:
                self.taskMgr.add(self.move_end, 'task-move-end', extraArgs=[x, y], appendTask=True)

    def speed(self):
        fwd = self.fighter.getQuat().getForward()
        fwd.normalize()
        self.mvel = self.anpo.getVelocity().length()
        # speed control
        self.mvel = self.chk_speed(self.mvel)
        self.anpo.setVelocity(fwd * self.mvel)

    def ship(self):
        an = ActorNode()
        an.getPhysicsObject().setMass(100)
        self.fighter = self.render.attachNewNode(an)
        self.physicsMgr.attachPhysicalNode(an)
        self.anpo = an.getPhysicsObject()
        fn = ForceNode("force-node-fighter")
        self.fighter.attachNewNode(fn)
        self.pft = LinearVectorForce(Vec3(0, +1, 0) * 500)  # forward thrust
        self.prt = LinearVectorForce(Vec3(0, -1, 0) * 500)  # reverse thrust
        self.pft.setMassDependent(1)
        self.prt.setMassDependent(1)
        self.pft.setActive(False)
        self.prt.setActive(False)
        fn.addForce(self.pft)
        fn.addForce(self.prt)
        an.getPhysical(0).addLinearForce(self.pft)
        an.getPhysical(0).addLinearForce(self.prt)
        self.camera.reparentTo(self.fighter)
        from_obj = self.fighter.attachNewNode(CollisionNode('fighter'))
        from_obj.node().setFromCollideMask(BitMask32(0x1))
        from_obj.setCollideMask(BitMask32(0x1))
        from_obj.node().addSolid(CollisionSphere(0, 0, 0, 1))
        # from_obj.show()
        self.pusher.addCollider(from_obj, self.fighter)
        self.cTrav.addCollider(from_obj, self.pusher)

    def launch_bullet(self):
        speed = 500.
        scale = Vec3(0.05)
        color = Vec4(0, 1, 0, 1)
        mask = BitMask32(0x2)
        lookat = Vec3(0, 100, 0)
        Missile(self, "bullet", speed, scale, color, mask, self.fighter, Vec3(-0.5, 0, 0), self.fighter, lookat, 0.5)
        Missile(self, "bullet", speed, scale, color, mask, self.fighter, Vec3(+0.5, 0, 0), self.fighter, lookat, 0.5)
        self.snd_launch.play()

    def to_fire(self):
        if self.get_key["FIRE"]:
            if not self.get_key["FIRING"]:
                self.set_key("FIRING", True)
                self.taskMgr.doMethodLater(0.16, self.fire_bullet, "task-fire-bullet")
        else:
            if self.get_key["FIRING"]:
                self.set_key("FIRING", False)
                self.taskMgr.remove("task-fire-bullet")

    def fire_bullet(self, task):
        if self.fuel >= 5:
            self.fuel -= 5
            self.launch_bullet()
        return task.again

    def launch_missile(self):
        speed = 100
        scale = Vec3(0.2)
        color = Vec4(1, 0, 0, 1)
        mask = BitMask32(0x2)
        lookat = Vec3(0, 0, 0)
        self.missile = Missile(self, "missile", speed, scale, color, mask, self.fighter, Vec3(0, 0, -2), self.target.np, lookat, 3)
        self.snd_launch.play()
        self.taskMgr.add(self.guide_missile, "task-guide-missile")

    def guide_missile(self, task):
        try:
            quat = Quat()
            lookAt(quat, self.target.np.getPos() - self.missile.anp.getPos(), Vec3.up())
            self.missile.anp.setQuat(quat)
            fwd = quat.getForward()
            fwd.normalize()
            mvel = self.missile.anpo.getVelocity().length()
            self.missile.anpo.setVelocity(fwd*mvel)
        except:
            return task.done
        return task.cont

    def can_lock(self):
        if self.dist >= 30 and self.dist <= 300 and abs(self.d2.getX()) <= 0.1 and abs(self.d2.getZ()) <= 0.1:
            return True
        else:
            return False

    def remove_lock(self):
        if self.get_key["LOCKING"]:
            self.set_key("LOCKING", False)
            self.locker.hide()
            self.snd_lock.stop()
            self.taskMgr.remove("task-fire-missile")

    def to_lock(self):
        if self.get_key["LOCK"]:
            if self.can_lock():
                if self.fuel >= 100:
                    if not self.get_key["LOCKING"]:
                        self.set_key("LOCKING", True)
                        self.locker.setScale(0.12)
                        self.locker.setColor(1, 0, 0, 0.5)
                        self.locker.show()
                        self.snd_lock.play()
                        self.taskMgr.add(self.fire_missile, "task-fire-missile")
                else:
                    self.remove_lock()
            else:
                self.remove_lock()
        else:
            self.remove_lock()

    def fire_missile(self, task):
        if self.fuel >= 100:
            if task.time < 3.6:
                e = (3.6 - task.time)/3.6
                f = 0.02 + e*0.1
                self.locker.setScale(f)
                self.locker.setColor(e, 1-e, 0, 0.5)
                return task.cont
            else:
                self.fuel -= 100
                self.launch_missile()
                return task.done
