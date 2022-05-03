import rigamajig2.maya.container as continer 
import rigamajig2.maya.scriptNode as scriptNode
import maya.cmds as cmds 


cmds.setAttr("bind.v", 0)

scriptNode.create('rigamajig2_sceneConfig', scriptType='Open/Close', beforeScript =continer.sainityCheck)