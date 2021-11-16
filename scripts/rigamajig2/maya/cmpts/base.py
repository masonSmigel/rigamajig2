"""
base component
"""
import maya.cmds as cmds

import rigamajig2.maya.container
import rigamajig2.maya.attr as r_attr
import logging

logger = logging.getLogger(__name__)


class Base(object):

    def __init__(self, name, input=[], size=1):
        """
        :param name:
        :param input:
        :type input
        """
        self.name = name
        self.cmpt_type = self.__class__.__name__.lower()
        self.input = input
        self.size = size
        self.container = self.name + "_" + self.cmpt_type + '_container'

        # element lists
        self.joints = list()
        self.controlers = list()

        self.metaData = {'component_name': self.name,
                         'component_type': self.cmpt_type}

    def _intialize_cmpt(self):
        """
        setup all intialize functions for the component

        process order:
            self.createContainer
            self.preScript
            self.initHierachy
            self.addAnimParams
        """
        if not self.get_step() >= 1:
            self.createContainer(self.metaData)

            # anything that manages or creates nodes should set the active container
            with rigamajig2.maya.container.ActiveContainer(self.container):
                self.preScript()
                self.initalHierachy()
                self.addAnimParams()
            self.set_step(1)
        else:
            logger.warning('component {} already initalized.'.format(self.name))

    def _build_cmpt(self):
        """
        build the rig

        process order:
            self.preRigSetup
            self.rigSetup
            self.postRigSetup
        """
        if not self.get_step() >= 2:
            # anything that manages or creates nodes should set the active container
            with rigamajig2.maya.container.ActiveContainer(self.container):
                self.preRigSetup()
                self.rigSetup()
                self.postRigSetup()
            self.set_step(2)
        else:
            logger.warning('component {} already built.'.format(self.name))

    def _connect_cmpt(self):
        """ connect components within the rig"""
        if not self.get_step() >= 3:
            with rigamajig2.maya.container.ActiveContainer(self.container):
                pass
            self.set_step(3)
        else:
            logger.warning('component {} already connected.'.format(self.name))

    def _finalize_cmpt(self):
        """
        finalize component

         process order:
            self.publishNodes
            self.publishAttributes
            self.finalize
            self.postScripts
        """
        if not self.get_step() >= 4:
            self.publishNodes()
            self.publishAttributes()
            with rigamajig2.maya.container.ActiveContainer(self.container):
                self.finalize()
                self.setAttrs()
                self.postScript()
            self.set_step(4)
        else:
            logger.warning('component {} already finalized.'.format(self.name))

    def _optimize_cmpt(self):
        """"""
        if not self.get_step() >= 5:
            self.optimize()
            self.set_step(5)
        else:
            logger.warning('component {} already optimized.'.format(self.name))

    # functions
    def preScript(self):
        pass

    def createContainer(self, data={}):
        """Create a Container for the component"""
        if not cmds.objExists(self.container):
            self.container = rigamajig2.maya.container.create(self.container)

            for key in data.keys():
                r_attr.addAttr(self.container, key, attributeType='string', value=data[key])
                r_attr.lock(self.container, key)

    def initalHierachy(self):
        """Setup the inital Hirarchy"""
        pass

    def addAnimParams(self):
        """ Add all attributes needed"""
        pass

    def preRigSetup(self):
        """Pre rig setup"""
        pass

    def rigSetup(self):
        """Add the rig setup"""
        pass

    def postRigSetup(self):
        """Add the rig setup"""
        pass

    def addBindJoints(self):
        """Add bind joints to the rig"""
        pass

    def publishNodes(self):
        """Publush nodes"""
        rigamajig2.maya.container.addParentAnchor(self.root, container=self.container)
        rigamajig2.maya.container.addChildAnchor(self.root, container=self.container)
        rigamajig2.maya.container.addPublishNodes(self.controlers)

    def publishAttributes(self):
        """publish attributes"""
        pass

    def finalize(self):
        """Finalize a component"""
        pass

    def setAttrs(self):
        """Set attributes"""
        pass

    def postScript(self):
        pass

    def optimize(self):
        """Optimize a component"""
        pass

    def set_step(self, step=0):
        """
        set the pipeline step.

        step 0 - unbuilt
        step 1 - initalize component
        step 2 - build component
        step 3 - connect component
        step 4 - finalize component
        step 4 - optimize component

        :param step:
        :return:
        """
        if not cmds.objExists("{}.{}".format(self.container, 'build_step')):
            r_attr.addAttr(self.container, 'build_step', attributeType='long', value=0, minValue=0,
                           keyable=False, channelBox=False)
            r_attr.lock(self.container, 'build_step')

        r_attr.unlock(self.container, 'build_step')
        cmds.setAttr("{}.{}".format(self.container, 'build_step'), step)
        r_attr.lock(self.container, 'build_step')

    def get_step(self):
        """
        get the pipeline step
        :return:
        """
        if self.container and cmds.objExists("{}.{}".format(self.container, 'build_step')):
            return cmds.getAttr("{}.{}".format(self.container, 'build_step'))
        return 0

    def save(self):
        pass

    def load(self):
        pass
