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


# pylint:disable=too-many-public-methods
class Base(object):
    """
    Base component all components are subclassed from
    """
    VERSION_MAJOR = 1
    VERSION_MINOR = 0
    VERSION_PATCH = 0

    version_info = (VERSION_MAJOR, VERSION_MINOR, VERSION_PATCH)
    version = '%i.%i.%i' % version_info
    __version__ = version

    def __init__(self, name, input, size=1, rigParent=str()):
        """
        constructor of the base class.

        An important note about rigamajig is that it has several
        'magic variables' such as self.bindJoints, self.controlers, self.input.
        These should always be available within the classes and can be used within subclasses.

        Other varriables stored within the self.CmptSettings are published
        into the class as parameters so they can be acessed through
        self.myVariable within the the class.

        :param name: name of the components
        :type name: str
        :param input: list of input joints.
        :type input: list
        :param size: default size of the controls:
        :type size: float
        :param rigParent: node to parent to connect the component to in the heirarchy
        :type rigParent: str
        """
        self.name = name
        self.componentType = self.__module__.split('cmpts.')[-1]
        self.input = input
        self.rigParent = rigParent
        self.container = self.name + '_container'
        self.metaNode = None

        # element lists
        self.bindjoints = list()
        self.controlers = list()
        self.guidesHierarchy = None

        # node metaData
        self.cmptSettings = OrderedDict(
            name=name,
            type=self.componentType,
            input=self.input,
            size=size,
            rigParent=rigParent
            )

    def _initalizeComponent(self):
        """
        setup all intialize functions for the component

        process order:
            self.createContainer
            self.preScript
        """
        if self.getStep() < 1:
            # fullDict = dict(self.metaData, **self.cmptSettings)
            self.setInitalData()
            self.createContainer()

            # Store to component node
            self.metaNode = rigamajig2.maya.meta.MetaNode(self.container)
            # self.metaNode.setDataDict(data=self.cmptData, hide=True)
            self.metaNode.setDataDict(data=self.cmptSettings, hide=True)

            rigamajig2.maya.attr.lock(self.container, ["name", "type"])

            # anything that manages or creates nodes should set the active container
            with rigamajig2.maya.container.ActiveContainer(self.container):
                self.preScript()  # run any pre-build scripts
                self.createJoints()
                self.createBuildGuides()
            self.setStep(1)

            # load all parameters back to the class so theyre always there
            self._loadComponentParametersToClass()
        else:
            logger.debug('component {} already initalized.'.format(self.name))

    def _buildComponent(self):
        """
        build the rig

        process order:
            self.initalHierachy
            self.preRigSetup
            self.rigSetup
            self.postRigSetup
        """
        self._loadComponentParametersToClass()

        if self.getStep() < 2:

            # anything that manages or creates nodes should set the active container
            with rigamajig2.maya.container.ActiveContainer(self.container):
                self.initalHierachy()
                self.preRigSetup()
                self.rigSetup()
                self.postRigSetup()
                self.setupAnimAttrs()
            self.setStep(2)
        else:
            logger.debug('component {} already built.'.format(self.name))

    def _connectComponent(self):
        """ connect components within the rig"""
        self._loadComponentParametersToClass()

        if self.getStep() < 3:
            with rigamajig2.maya.container.ActiveContainer(self.container):
                self.initConnect()
                self.connect()
                self.postConnect()
            self.setStep(3)
        else:
            logger.debug('component {} already connected.'.format(self.name))

    def _finalizeComponent(self):
        """
        finalize component

         process order:
            self.publishNodes
            self.publishAttributes
            self.finalize
            self.postScripts
        """
        self._loadComponentParametersToClass()

        if self.getStep() < 4:
            self.publishNodes()
            self.publishAttributes()
            with rigamajig2.maya.container.ActiveContainer(self.container):
                self.finalize()
                self.setAttrs()
                self.postScript()
            self.setStep(4)
        else:
            logger.debug('component {} already finalized.'.format(self.name))

    def _optimizeComponent(self):
        """"""
        self._loadComponentParametersToClass()

        if self.getStep() != 5:
            self.optimize()
            self.setStep(5)
        else:
            logger.debug('component {} already optimized.'.format(self.name))

    # --------------------------------------------------------------------------------
    # functions
    # --------------------------------------------------------------------------------
    def createJoints(self):
        """build joints required for the component"""
        pass

    def createBuildGuides(self):
        """Add additional guides"""
        pass

    def setInitalData(self):
        """
        Set inital component data.
        This allows you to set component data within subclasses.
        """
        pass

    def createContainer(self):
        """Create a Container for the component"""
        if not cmds.objExists(self.container):
            self.container = rigamajig2.maya.container.create(self.container)
            rigamajig2.maya.meta.tag(self.container, 'component')

            # tag the container with the proper component version
            rigamajig2.maya.attr.createAttr(self.container, "__version__", "string",
                                            value=self.__version__,
                                            keyable=False,
                                            locked=True
                                            )

    def preScript(self):
        """run a prescript"""
        pass

    def setupAnimAttrs(self):
        """Setup animation attributes. implement in subclass"""
        pass

    def initalHierachy(self):
        """Setup the inital Hirarchy. implement in subclass"""
        self.rootHierarchy = cmds.createNode('transform', n=self.name + '_cmpt')
        self.paramsHierarchy = cmds.createNode('transform', n=self.name + '_params',
                                               parent=self.rootHierarchy)
        self.controlHierarchy = cmds.createNode('transform', n=self.name + '_control',
                                                parent=self.rootHierarchy)
        self.spacesHierarchy = cmds.createNode('transform', n=self.name + '_spaces',
                                               parent=self.rootHierarchy)

    def preRigSetup(self):
        """Pre rig setup. implement in subclass"""
        pass

    def rigSetup(self):
        """Add the rig setup. implement in subclass"""
        pass

    def postRigSetup(self):
        """Add the post setup. implement in subclass"""
        pass

    def initConnect(self):
        """initalize the connection. implement in subclass"""
        pass

    def connect(self):
        """create the connection. implement in subclass"""
        pass

    def postConnect(self):
        """any final cleanup after the connection. implement in subclass"""
        pass

    def publishNodes(self):
        """Publush nodes. implement in subclass"""
        rigamajig2.maya.container.addParentAnchor(self.rootHierarchy, container=self.container)
        rigamajig2.maya.container.addChildAnchor(self.rootHierarchy, container=self.container)
        rigamajig2.maya.container.addPublishNodes(self.controlers)

    def publishAttributes(self):
        """publish attributes. implement in subclass"""
        pass

    def finalize(self):
        """Finalize a component. implement in subclass"""
        pass

    def setAttrs(self):
        """Set attributes. implement in subclass"""
        pass

    def postScript(self):
        """run a post script"""
        pass

    def optimize(self):
        """Optimize a component. implement in subclass"""
        pass

    def deleteSetup(self):
        """ delete the rig setup"""
        logger.info("deleting component {}".format(self.name))
        cmds.select(self.container, r=True)
        mel.eval("doDelete;")

        for input in self.input:
            rigamajig2.maya.attr.unlock(input, rigamajig2.maya.attr.TRANSFORMS + ['v'])

    def setStep(self, step=0):
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
            rigamajig2.maya.attr.createEnum(self.container, 'build_step', value=0,
                                            enum=['unbuilt', 'initalize', 'build', 'connect', 'finalize', 'optimize'],
                                            keyable=False, channelBox=False)

        cmds.setAttr("{}.{}".format(self.container, 'build_step'), step)

    def getStep(self):
        """
        get the pipeline step
        :return:
        """
        if self.container and cmds.objExists("{}.{}".format(self.container, 'build_step')):
            return cmds.getAttr("{}.{}".format(self.container, 'build_step'))
        return 0

    def loadSettings(self, data):
        """
        Load setting data onto the self.metaNode
        :param data: data to store on the self.metaNode
        :return:
        """
        keysToRemove = ['name', 'type', 'input']
        newDict = {key: val for key, val in data.items() if key not in keysToRemove}
        if self.metaNode:
            self.metaNode.setDataDict(newDict)

    def _loadComponentParametersToClass(self):
        """
        loadSettings meta data from the settings node into a dictionary
        """
        newComponentData = OrderedDict()
        for key in self.cmptSettings.keys():
            if self.metaNode:
                data = self.metaNode.getAllData()
            else:
                data = self.cmptSettings

            if key in data.keys():
                setattr(self, key, data[key])
                newComponentData[key] = data[key]

        self.cmptSettings.update(newComponentData)

    @staticmethod
    def createInputJoints(name=None, side=None, numJoints=None):
        """static method to create input joints"""
        return list()

    # GET
    def getContainer(self):
        """
        get the component container
        """
        if cmds.objExists(self.container):
            return self.container
        return None

    def getInputs(self):
        """Get component inputs"""
        return self.input

    def getComponentData(self):
        """Get all component Data """
        # create an info dictionary with the important component settings.
        # This is used to save the component to a file
        infoDict = OrderedDict()
        data = self.cmptSettings

        for key in self.cmptSettings.keys() + ['name', 'type', 'input']:
            infoDict[key] = data[key]
        return infoDict

    def getComponenetType(self):
        """Get the component type"""
        return self.componentType

    # SET
    def setInputs(self, value):
        """Set the component input"""
        self.input = value

    def setName(self, value):
        """Set the component name"""
        self.name = value

    @classmethod
    def testBuild(cls, cmpt):
        """
        Static method to run the initialize, build, connect, finalize and optimize steps
        :param cmpt: component to test the build.
        :return:
        """
        cmpt._initalizeComponent()
        cmpt._buildComponent()
        cmpt._connectComponent()
        cmpt._finalizeComponent()
        cmpt._optimizeComponent()
