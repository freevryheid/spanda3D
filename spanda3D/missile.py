from panda3d.core import Vec3
from panda3d.core import VBase4
from panda3d.core import DirectionalLight
from panda3d.core import CollisionNode
from panda3d.core import CollisionSphere
from panda3d.physics import ActorNode
from panda3d.physics import ForceNode
from panda3d.physics import LinearVectorForce


class Missile:

    def __init__(self, base, name, speed, scale, color, mask, relA, xyz, relB, lookat, life):
        an = ActorNode()
        self.anp = base.render.attachNewNode(an)
        base.physicsMgr.attachPhysicalNode(an)
        self.anpo = an.getPhysicsObject()
        fn = ForceNode("force-missile")
        self.anp.attachNewNode(fn)
        bft = LinearVectorForce(Vec3(0, 1, 0)*speed)
        fn.addForce(bft)
        an.getPhysical(0).addLinearForce(bft)
        missile = base.loader.loadModel("./mdl/missile.egg")
        missile.setColor(color)
        missile.setScale(scale)
        missile.reparentTo(self.anp)
        missile.setTag(name, '1')
        missile_from_obj = missile.attachNewNode(CollisionNode(name))
        missile_from_obj.node().addSolid(CollisionSphere(0, 0, 0, 1))
        missile_from_obj.node().setFromCollideMask(mask)
        missile_from_obj.setCollideMask(mask)
        base.pusher.addCollider(missile_from_obj, self.anp)
        base.cTrav.addCollider(missile_from_obj, base.pusher)
        self.anp.setPos(relA, xyz)
        self.anp.lookAt(relB, lookat)
        # light the missile
        mlight = DirectionalLight('mlight')
        mlight.setColor(VBase4(1., 1., 1., 1))
        mlnp = base.render.attachNewNode(mlight)
        mlnp.setHpr(self.anp.getHpr())
        self.anp.setLightOff()
        self.anp.setLight(mlnp)
        # remove the missile
        base.taskMgr.doMethodLater(life, self.remove_missile, 'task-remove-missile', extraArgs=[self.anp], appendTask=True)

    def remove_missile(self, obj, task):
        obj.removeNode()
        return task.done

    # def __del__(self):
    #     print("del Missile")
