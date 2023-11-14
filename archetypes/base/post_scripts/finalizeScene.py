import maya.api.OpenMaya as om
import maya.cmds as cmds

# camera 
if not om.MGlobal.mayaState(): 
	cmds.viewFit(all=True)