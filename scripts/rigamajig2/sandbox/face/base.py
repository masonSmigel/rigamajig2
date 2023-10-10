"""
base component
"""
from collections import OrderedDict

import maya.cmds as cmds

import rigamajig2.maya.attr
import rigamajig2.maya.container
import rigamajig2.maya.meta


class Base(object):
    """
    Base class which all components are subclassed from
    """

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
        self.rootHeirarchy = cmds.createNode('transform', n=self.name + '_cmpt')
        self.paramsHierarchy = cmds.createNode('transform', n=self.name + '_params', parent=self.rootHeirarchy)
        self.controlHierarchy = cmds.createNode('transform', n=self.name + '_control', parent=self.rootHeirarchy)

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
