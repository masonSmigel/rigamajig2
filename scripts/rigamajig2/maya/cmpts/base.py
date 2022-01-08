"""
base component
"""
import maya.cmds as cmds
from collections import OrderedDict

import rigamajig2.maya.container
import rigamajig2.maya.attr as r_attr
import logging
import rigamajig2.maya.meta

logger = logging.getLogger(__name__)


class Base(object):

    def __init__(self, name, input=[], size=1, rigParent=str()):
        """
        :param name: name of the components
        :type name: str
        :param input: list of input joints. This must be a length of 4
        :type input: list
        :param size: default size of the controls:
        :param rigParent: node to parent to connect the component to in the heirarchy
        :type size: float
        """
        self.name = name
        self.cmpt_type = ".".join([self.__module__.split('cmpts.')[-1],  self.__class__.__name__])
        self.input = input
        self.container = self.name + '_container'

        # element lists
        self.joints = list()
        self.controlers = list()

        # node metaData
        self.metaData = {'component_name': self.name,
                         'component_type': self.cmpt_type}
        # node cmpt settings
        self.cmptSettings = OrderedDict(size=size, rigParent=rigParent)

        self.proxySetupGrp = self.name + "_proxy"

    def _intialize_cmpt(self):
        """
        setup all intialize functions for the component

        process order:
            self.createContainer
            self.preScript
        """
        if not self.get_step() >= 1:
            # fullDict = dict(self.metaData, **self.cmptSettings)
            self.setInitalData()
            self.createContainer()
            # Store
            self.metaNode = rigamajig2.maya.meta.MetaNode(self.container)
            self.metaNode.setDataDict(data=self.metaData, hide=True, lock=True)
            self.metaNode.setDataDict(data=self.cmptSettings, hide=True)

            # anything that manages or creates nodes should set the active container
            with rigamajig2.maya.container.ActiveContainer(self.container):
                self.preScript()  # run any pre-build scripts
                self.createBuildGuides()
            self.set_step(1)
        else:
            logger.warning('component {} already initalized.'.format(self.name))

    def _show_advanced_proxy(self):
        """
        Show our advanced proxy setup
        """
        with rigamajig2.maya.container.ActiveContainer(self.container):
            self.showAdvancedProxy()

    def _build_cmpt(self):
        """
        build the rig

        process order:
            self.initalHierachy
            self.preRigSetup
            self.rigSetup
            self.postRigSetup
        """
        self._load_meta_to_component()

        if not self.get_step() >= 2:
            # if a proxy setup exists delete it.
            if self.proxy_setup_exists():
                self._delete_advanced_proxy()

            # anything that manages or creates nodes should set the active container
            with rigamajig2.maya.container.ActiveContainer(self.container):
                self.initalHierachy()
                self.preRigSetup()
                self.rigSetup()
                self.postRigSetup()
                self.setupAnimAttrs()
            self.set_step(2)
        else:
            logger.warning('component {} already built.'.format(self.name))

    def _connect_cmpt(self):
        """ connect components within the rig"""
        self._load_meta_to_component()

        if not self.get_step() >= 3:
            with rigamajig2.maya.container.ActiveContainer(self.container):
                self.initConnect()
                self.connect()
                self.postConnect()
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
        self._load_meta_to_component()

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
        self._load_meta_to_component()

        if not self.get_step() == 5:
            self.optimize()
            self.set_step(5)
        else:
            logger.warning('component {} already optimized.'.format(self.name))

    def _delete_advanced_proxy(self):
        """ Delete the advanced proxy """
        cmds.delete(self.proxySetupGrp)

    # --------------------------------------------------------------------------------
    # functions
    # --------------------------------------------------------------------------------
    def preScript(self):
        pass

    def createBuildGuides(self):
        """Add additional guides"""
        pass

    def setInitalData(self):
        """Set inital component data. This needs to be done in a compont so we control attrribute settings in subclasses."""
        pass

    def createContainer(self, data={}):
        """Create a Container for the component"""
        if not cmds.objExists(self.container):
            self.container = rigamajig2.maya.container.create(self.container)
            rigamajig2.maya.meta.tag(self.container, 'component')

    def initalHierachy(self):
        """Setup the inital Hirarchy"""
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

    def setupAnimAttrs(self):
        """Setup animation attributes"""
        pass

    def initConnect(self):
        """initalize the connection"""
        pass

    def connect(self):
        """create the connection"""
        pass

    def postConnect(self):
        """any final cleanup after the connection"""
        pass

    def publishNodes(self):
        """Publush nodes"""
        rigamajig2.maya.container.addParentAnchor(self.root_hrc, container=self.container)
        rigamajig2.maya.container.addChildAnchor(self.root_hrc, container=self.container)
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

    def showAdvancedProxy(self):
        """ Show advanved proxy attributes """
        pass

    def set_step(self, step=0):
        """
        set the pipeline step.

        step 0 - unbuilt
        step 1 - initalize component
        step 2 - build component
        step 3 - connect component
        step 4 - finalize component
        step 5 - optimize component

        :param step:
        :return:
        """
        if not cmds.objExists("{}.{}".format(self.container, 'build_step')):
            r_attr.addEnum(self.container, 'build_step', value=0,
                           enum=['unbuilt', 'initalize', 'build', 'connect', 'finalize', 'optimize'],
                           keyable=False, channelBox=False)

        cmds.setAttr("{}.{}".format(self.container, 'build_step'), step)

    def get_step(self):
        """
        get the pipeline step
        :return:
        """
        if self.container and cmds.objExists("{}.{}".format(self.container, 'build_step')):
            return cmds.getAttr("{}.{}".format(self.container, 'build_step'))
        return 0

    def proxy_setup_exists(self):
        return True if self.proxySetupGrp and cmds.objExists(self.proxySetupGrp) else False

    def save(self):
        """Return the settings of component name"""
        self._load_meta_to_component()
        return self._userSettings

    def load(self, meta):
        self.metaNode.setDataDict(meta)

    def _load_meta_to_component(self):
        """
        load meta data from the settings node into a dictionary
        """
        for key in self.cmptSettings.keys():
            setattr(self, key, self.metaNode.getData(key))
