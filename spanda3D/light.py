from panda3d.core import VBase4
from panda3d.core import AmbientLight
from panda3d.core import DirectionalLight


class Light:

    def __init__(self, base):
        self.base = base
        alight = AmbientLight("ambient-light")
        alight.setColor(VBase4(0.2, 0.2, 0.2, 1))
        alnp = base.render.attachNewNode(alight)
        base.render.setLight(alnp)
        dlight = DirectionalLight("direction-light")
        dlight.setColor(VBase4(0.8, 0.8, 0.5, 1))
        dlnp = base.render.attachNewNode(dlight)
        base.render.setLight(dlnp)
