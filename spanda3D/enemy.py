from direct.gui.OnscreenImage import OnscreenImage
from panda3d.core import Vec3
from panda3d.core import BitMask32
from panda3d.core import TransparencyAttrib
from panda3d.core import CollisionNode
from panda3d.core import CollisionBox
from panda3d.ai import AICharacter
from math import exp
from random import uniform
from particles import Explosion


class Enemy:

    def __init__(self, base, n, x, y, z):
        self.base = base
        self.n = n
        self.health = 4
        self.np = base.loader.loadModel("./mdl/enemy.egg")
        self.np.setColor(1, 1, 0, 1)
        self.np.reparentTo(base.render)
        self.np.setPos(x, y, z)
        self.np.setAlphaScale(0.)
        base.target = self
        self.radar = OnscreenImage(image="./png/radar.png", pos=Vec3(0), scale=0.01)
        self.radar.setTransparency(TransparencyAttrib.MAlpha)

        # collisions
        cn = CollisionNode("enemy"+str(n))
        cn.addSolid(CollisionBox(0, 2.5, 2, 0.5))
        cn.setCollideMask(BitMask32(0x1) | BitMask32(0x2))
        # cc = self.np.attachNewNode(cn)
        self.np.attachNewNode(cn)
        base.accept("fighter-into-enemy"+str(n), self.ship_collision)
        base.accept("bullet-into-enemy"+str(n), self.bullet_collision)
        base.accept("missile-into-enemy"+str(n), self.missile_collision)

        # sound
        self.snd_crash = base.loader.loadSfx("./snd/crash.flac")
        self.snd_blip = base.audio3d.loadSfx("./snd/blip.flac")
        self.snd_hit = base.loader.loadSfx("./snd/hit.flac")
        self.snd_explode = base.loader.loadSfx("./snd/explosion.flac")
        base.audio3d.attachSoundToObject(self.snd_blip, self.np)
        base.audio3d.setSoundVelocityAuto(self.snd_blip)
        base.audio3d.attachSoundToObject(self.snd_crash, self.np)
        base.audio3d.setSoundVelocityAuto(self.snd_crash)
        base.audio3d.attachSoundToObject(self.snd_hit, self.np)
        base.audio3d.setSoundVelocityAuto(self.snd_hit)
        base.audio3d.attachSoundToObject(self.snd_explode, self.np)
        base.audio3d.setSoundVelocityAuto(self.snd_explode)
        self.snd_blip.setLoop(True)
        self.snd_blip.play()

        self.setAI()

    def setAI(self):
        self.AIchar = AICharacter("enemy", self.np, 100, 10., 50)
        self.base.AIworld.addAiChar(self.AIchar)
        self.AIbehaviors = self.AIchar.getAiBehaviors()
        self.AIbehaviors.wander(50, 0, 1000, 1.0)

    def explode(self):
        self.snd_blip.stop()
        self.base.audio3d.detachSound(self.snd_blip)
        self.base.audio3d.detachSound(self.snd_crash)
        self.base.audio3d.detachSound(self.snd_hit)
        self.radar.hide()
        self.np.hide()
        self.base.taskMgr.remove("fighter-into-enemy"+str(self.n))
        self.base.taskMgr.remove("bullet-into-enemy"+str(self.n))
        self.base.taskMgr.remove("missile-into-enemy"+str(self.n))
        self.base.taskMgr.remove("enemy-hit-task")
        self.base.taskMgr.remove("enemy-crash-task")
        self.snd_explode.play()
        self.part = Explosion(self.base)
        self.part.pn.setPos(self.np.getPos())
        self.base.taskMgr.doMethodLater(5, self.remove_part, "task-remove-part")

    def cleanup(self):
        self.base.audio3d.detachSound(self.snd_explode)
        self.base.AIworld.removeAiChar("enemy")
        self.base.target = None
        self.radar.destroy()
        self.np.removeNode()
        self.base.fuel += 500
        self.base.gen_enemy()

    def ship_collision(self, entry):
        # degree of shaking depends on my speed/velocity (mvel)
        self.health -= 1
        self.base.fuel -= 500
        d = exp(0.047 * self.base.mvel - 7.)
        self.snd_crash.play()
        self.base.taskMgr.add(self.enemy_crash, "enemy-crash-task", extraArgs=[d], appendTask=True)

    def enemy_crash(self, d, task):
        if task.time < 5:
            f = (5. - task.time) / 5.
            s = 3000.*f
            x = uniform(-s, s)
            y = uniform(-s, s)
            self.base.repos(x, y, d)
            return task.cont
        return task.done

    def bullet_collision(self, entry):
        self.snd_hit.play()
        objNP = entry.getFromNodePath().findNetTag("bullet")
        objNP.removeNode()
        self.health -= 1
        if self.health == 0:
            self.explode()
        else:
            self.base.taskMgr.add(self.enemy_hit, "enemy-hit-task")

    def missile_collision(self, entry):
        self.snd_hit.play()
        objNP = entry.getFromNodePath().findNetTag("missile")
        objNP.removeNode()
        self.explode()

    def enemy_hit(self, task):
        if task.time < 3:
            f = (3. - task.time) / 3.
            self.np.setColor(1, 1-f, 0, 1)
            self.np.setAlphaScale(f)
            return task.cont
        return task.done

    def remove_part(self, task):
        self.part.pe.cleanup()
        self.cleanup()
        return task.done

    # def __del__(self):
    #     print("del Fighter")
