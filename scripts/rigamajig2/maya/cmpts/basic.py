"""
basic component
"""
import maya.cmds as cmds
import rigamajig2.maya.cmpts.base
import rigamajig2.maya.rig.control as rig_control
import rigamajig2.maya.rig.spaces as spaces
import rigamajig2.maya.rig.ikfk as ikfk
import rigamajig2.maya.transform as rig_transform
import rigamajig2.shared.common as common
import rigamajig2.maya.meta as meta

import logging

logger = logging.getLogger(__name__)


class Basic(rigamajig2.maya.cmpts.base.Base):

    def __init__(self, name, input=[], size=1):
        super(Basic, self).__init__(name, input=input, size=size)
