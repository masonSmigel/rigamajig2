"""
base component
"""
import maya.cmds as cmds
import maya.mel as mel
from collections import OrderedDict

import rigamajig2.maya.container
import rigamajig2.maya.attr
import rigamajig2.maya.meta
import rigamajig2.maya.data.joint_data as joint_data
import rigamajig2.maya.transform as transform


import logging

logger = logging.getLogger(__name__)


class Base(object):

    def __init__(self, name, rigParent=str()):
        self.name = name
        self.container = self.name + '_container'
        self.metaNode = None

        self.cmptSettings = OrderedDict(name=name, type=self.cmpt_type, input=self.input, size=size,
                                        rigParent=rigParent)

    def createContainer(self):
        """Create a Container for the component"""
        if not cmds.objExists(self.container):
            self.container = rigamajig2.maya.container.create(self.container)
            rigamajig2.maya.meta.tag(self.container, 'component')

    def initalHierachy(self):
        """Setup the inital Hirarchy. implement in subclass"""
        self.root_hrc = cmds.createNode('transform', n=self.name + '_cmpt')
        self.params_hrc = cmds.createNode('transform', n=self.name + '_params', parent=self.root_hrc)
        self.control_hrc = cmds.createNode('transform', n=self.name + '_control', parent=self.root_hrc)

    def createGuides(self):
        """Create component guides"""

    def run(self):
        """Run the entire build"""

        # GET

    def getContainer(self):
        """
        get the component container
        :return:
        """
        if cmds.objExists(self.container):
            return self.container
        return None
