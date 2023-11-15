import maya.cmds as cmds

import rigamajig2.maya.file

rigamajig2.maya.file.new(f=True)

# setup the camera
cmds.setAttr('perspShape.focalLength', 55)


