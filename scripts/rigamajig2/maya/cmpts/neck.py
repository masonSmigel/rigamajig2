"""
neck component
"""
import maya.cmds as cmds
import rigamajig2.maya.cmpts.base
import rigamajig2.maya.rig.control as rig_control
import rigamajig2.maya.rig.spaces as spaces
import rigamajig2.maya.rig.spline as spline
import rigamajig2.maya.transform as rig_transform
import rigamajig2.maya.mathUtils as mathUtils
import rigamajig2.maya.constrain as constrain
import rigamajig2.maya.node as node
import rigamajig2.shared.common as common
import rigamajig2.maya.hierarchy as hierarchy
import rigamajig2.maya.attr as rig_attr
import rigamajig2.maya.meta as meta


class Neck(rigamajig2.maya.cmpts.base.Base):
    def __init__(self, name, input=[], size=1, rigParent=str()):
        super(Neck, self).__init__(name, input=input, size=size, rigParent=rigParent)

    def initalHierachy(self):
        self.root_hrc = cmds.createNode('transform', n=self.name + '_cmpt')