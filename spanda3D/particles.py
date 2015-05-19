from direct.particles.Particles import Particles
from direct.particles.ParticleEffect import ParticleEffect
from panda3d.core import Vec4
from panda3d.physics import BaseParticleRenderer


class Explosion:

    def __init__(self, base):
        self.base = base
        self.p = Particles()
        self.p.setFactory("PointParticleFactory")
        self.p.setRenderer("LineParticleRenderer")
        self.p.setEmitter("SphereSurfaceEmitter")
        self.p.setPoolSize(256)
        self.p.setBirthRate(0.01)
        self.p.setLitterSize(256)
        self.p.setSystemLifespan(2)
        self.p.factory.setLifespanBase(5.0000)
        self.p.renderer.setTailColor(Vec4(1.0, 1.0, 0.0, 1.0))
        self.p.renderer.setHeadColor(Vec4(1.0, 0.0, 0.0, 1.0))
        self.p.renderer.setAlphaMode(BaseParticleRenderer.PRALPHAOUT)
        self.p.renderer.setUserAlpha(1.00)
        self.p.renderer.setLineScaleFactor(32.00)
        self.p.emitter.setRadius(2.0000)
        self.p.setRenderParent(base.render)
        self.p.enable()
        self.pn = base.render.attachNewNode("particleExpNode")
        # self.pn.setDepthWrite(False)
        # self.pn.setBin("fixed", 0)
        self.pe = ParticleEffect("exp-effect", self.p)
        self.pe.reparentTo(self.pn)
        self.pe.enable()


class Spacedust:

    def __init__(self, base):
        self.base = base
        self.p = Particles()
        self.p.setFactory("PointParticleFactory")
        self.p.setRenderer("LineParticleRenderer")
        self.p.setEmitter("SphereSurfaceEmitter")
        self.p.setPoolSize(1024)
        self.p.setBirthRate(0.05)
        self.p.setLitterSize(32)
        self.p.factory.setLifespanBase(1.0000)
        self.p.emitter.setRadius(5.0000)
        self.p.renderer.setTailColor(Vec4(1.0, 1.0, 1.0, 1.0))
        self.p.renderer.setHeadColor(Vec4(1.0, 1.0, 1.0, 1.0))
        # self.p.renderer.setAlphaMode(BaseParticleRenderer.PRALPHAOUT)
        # self.p.renderer.setUserAlpha(1.00)
        self.p.setRenderParent(base.render)
        self.p.enable()
        self.pn = base.render.attachNewNode("particleDustNode")
        # self.pn.setDepthWrite(False)
        # self.pn.setBin("fixed", 0)
        self.pe = ParticleEffect("dust-effect", self.p)
        self.pe.reparentTo(self.pn)
        self.pe.enable()
