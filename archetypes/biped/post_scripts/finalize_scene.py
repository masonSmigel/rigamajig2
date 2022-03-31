import maya.cmds as cmds 
import maya.api.OpenMaya as om 

# camera 
if not om.MGlobal.mayaState(): 
	cmds.viewFit(all=True)