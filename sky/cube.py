from pandac.PandaModules import TextureStage
from pandac.PandaModules import TexGenAttrib


class SkyCube:

    def __init__(self, base):
        tex = base.loader.loadCubeMap("./sky/sky_#.png")
        cube = base.loader.loadModel("./sky/icube.egg")
        cube.setTexGen(TextureStage.getDefault(), TexGenAttrib.MWorldPosition)
        cube.setTexProjector(TextureStage.getDefault(), base.render, cube)
        cube.setTexture(tex)
        cube.setBin("background", 1)
        cube.setLightOff()
        cube.setDepthWrite(False)
        cube.setScale(5, 5, 5)
        cube.reparentTo(base.camera)
        cube.setCompass()

    # def __del__(self):
    #     print("del Sky")
