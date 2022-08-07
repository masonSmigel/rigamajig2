import maya.cmds as cmds 
from rigamajig2.maya.rig import control 

def hideInputsAndOutputsFromChannelBox():
    """
    Set all nodes that are not controls to be non-historically interesting.
    This will hide them from the inputs, outputs and shapes sections of the channel box. 
    """
    allNodes = cmds.ls("*")
    controls = control.getControls()

    nonControls = [x for x in allNodes if x not in controls]

    for allNode in nonControls: 
        cmds.setAttr("{}.isHistoricallyInteresting".format(allNode), 0)


hideInputsAndOutputsFromChannelBox()