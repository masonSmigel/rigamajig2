import rigamajig2.maya.container as continer 
import rigamajig2.maya.scriptNode as scriptNode
import maya.cmds as cmds 

# check if the riamajig scene config exists. If it doesnt create it 
if not cmds.objExists('rigamajig2_sceneConfig'):
    scriptNode.create('rigamajig2_sceneConfig', scriptType='Open/Close', beforeScript=continer.sainityCheck)