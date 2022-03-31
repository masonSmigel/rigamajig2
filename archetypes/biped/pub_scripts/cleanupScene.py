import rigamajig2.maya.container as continer 
import rigamajig2.maya.scriptNode as scriptNode

scriptNode.create('rigamajig2_sceneConfig', scriptType='Open/Close', beforeScript =continer.sainityCheck)