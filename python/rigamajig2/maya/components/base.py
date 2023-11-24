"""
base component
"""
import logging
import typing
from collections import OrderedDict

import maya.cmds as cmds
import maya.mel as mel

from rigamajig2.maya import attr
from rigamajig2.maya import color
from rigamajig2.maya import container
from rigamajig2.maya import meta
from rigamajig2.maya.rig.control import CONTROL_TAG

logger = logging.getLogger(__name__)

UNBUILT_STEP = 0
INITIALIZE_STEP = 1
GUIDE_STEP = 2
BUILD_STEP = 3
CONNECT_STEP = 4
FINALIZE_STEP = 5
OPTIMIZE_STEP = 6

METADATA_NODE_TYPE = "network"


# pylint:disable=too-many-public-methods
class BaseComponent(object):
    """
    Base component all components are subclassed from
    """

    VERSION_MAJOR = 1
    VERSION_MINOR = 0
    VERSION_PATCH = 0

    version_info = (VERSION_MAJOR, VERSION_MINOR, VERSION_PATCH)
    version = "%i.%i.%i" % version_info
    __version__ = version

    UI_COLOR = (200, 200, 200)

    def __init__(
        self, name, input, size=1, rigParent=None, componentTag=None, enabled=True
    ):
        """
        constructor of the base class.

        :param name: name of the components
        :type name: str
        :param input: list of input joints.
        :type input: list
        :param size: default size of the controls:
        :type size: float
        :param rigParent: node to parent to connect the component to in the hierarchy
        :type rigParent: str
        :param enabled: If set to false the component will not build
        """
        self._componentParameters = {}

        self.componentType = self.__module__.split("components.")[-1]
        self.name = name
        self.input = input
        self.enabled = enabled
        self.size = size
        self.rigParent = rigParent or str()
        self.componentTag = componentTag or str()

        # important global nodes
        self.container = self.name + "_container"

        # we will always need the container if it does not exist.
        if not cmds.objExists(self.container):
            self._createContainer()
            self._createMetaNode(metaNodeName=self.container + "_metadata")
            logger.debug(f"Component '{name}' container created.")

        self.metadataNode = self.getMetaDataNode()

        # define component parameters
        self.defineParameter(parameter="name", value=self.name, dataType="string")
        self.defineParameter(
            parameter="type", value=self.componentType, dataType="type"
        )
        self.defineParameter(parameter="input", value=self.input, dataType="list")
        self.defineParameter(parameter="enabled", value=self.enabled, dataType="bool")
        self.defineParameter(parameter="size", value=self.size, dataType="int")
        self.defineParameter(
            parameter="rigParent", value=self.rigParent, dataType="string"
        )
        self.defineParameter(
            parameter="componentTag", value=self.componentTag, dataType="string"
        )

    def help(self):
        """
        print useful component info to the script editor to help debugging.
        """
        returnString = "-" * 80
        returnString += f"\nRigamajig Component: <{self.__class__.__module__} object at {hex(id(self))}>\n"
        for key in self._componentParameters:
            tooltip = self._componentParameters[key].get("tooltip")
            tooltipString = f"\t({tooltip})" if tooltip else ""
            returnString += (
                f"\t{key} = {self._componentParameters[key]['value']} {tooltipString}\n"
            )

        returnString += "-" * 80
        print(returnString)

    @classmethod
    def fromContainer(cls, container):
        """Create a component instance from a container"""
        metaNode = meta.MetaNode(container)
        containerData = metaNode.getAllData()

        componentInstance = cls.fromData(containerData)

        return componentInstance

    @classmethod
    def fromData(cls, data):
        """
        Create a class instance from a dictionary of data
        :param data: data file containing all important dictionary keys
        :return: a new class instance
        """

        REQUIRED_PARAMETERS = ["name", "input", "rigParent"]
        try:
            name = data.get("name")
            input = data.get("input")
            rigParent = data.get("rigParent") or None
            size = data.get("size") or 1
            componentTag = data.get("componentTag") or None

        except KeyError as e:
            raise KeyError(f"failed to gather data from: {data}", e)

        componentInstance = cls(
            name=name,
            input=input,
            rigParent=rigParent,
            size=size,
            componentTag=componentTag,
        )

        # gather other data from the class
        for key in componentInstance._componentParameters:
            if key not in REQUIRED_PARAMETERS:
                if key not in data.keys():
                    logger.warning(
                        f"{componentInstance.name}: Failed to get value for: {key}. Skipping parameter"
                    )
                    continue
                value = data.get(key)
                componentInstance.setParameterValue(parameter=key, value=value)

        return componentInstance

    def initializeComponent(self):
        """
        setup all initialize functions for the component

        process order:
            self._createContainer
        """
        if self.getStep() < INITIALIZE_STEP and self.enabled:
            self._setInitialData()
            self.setStep(1)

        else:
            logger.debug("component {} already initialized.".format(self.name))

    def guideComponent(self):
        """
        setup the component guides
        process order:
            self.preScript
            self._createJoints
            self.createBuildGuides
        """
        self._updateClassParameters()

        if self.getStep() < GUIDE_STEP and self.enabled:
            # anything that manages or creates nodes should set the active container
            with container.ActiveContainer(self.container):
                self._createJoints()
                self._createBuildGuides()
            self.setStep(2)

        else:
            logger.debug("component {} already guided.".format(self.name))

    def buildComponent(self):
        """
        build the rig

        process order:
            self._initialHierarchy
            self._preRigSetup
            self._rigSetup
            self._postRigSetup
        """
        self._updateClassParameters()

        if self.getStep() < BUILD_STEP and self.enabled:
            # anything that manages or creates nodes should set the active container
            with container.ActiveContainer(self.container):
                self._autoOrientGuides()
                self._initialHierarchy()
                self._preRigSetup()
                self._rigSetup()
                self._postRigSetup()
                self._setupAnimAttrs()
            self.setStep(3)
        else:
            logger.debug("component {} already built.".format(self.name))

    def connectComponent(self):
        """connect components within the rig"""
        self._updateClassParameters()

        if self.getStep() < CONNECT_STEP and self.enabled:
            with container.ActiveContainer(self.container):
                self._preConnect()
                self._connect()
                self._postConnect()
            self.setStep(4)
        else:
            logger.debug("component {} already connected.".format(self.name))

    def finalizeComponent(self):
        """
        finalize component

         process order:
            self._publishNodes
            self._publishAttributes
            self.finalize
            self.postScripts
        """
        # self._updateClassParameters()

        if self.getStep() < FINALIZE_STEP and self.enabled:
            self._publishNodes()
            self._publishAttributes()
            with container.ActiveContainer(self.container):
                self._finalize()
                self._setControlAttributes()

            # if we added a component tag build that now!
            if self.componentTag:
                meta.tag(self.container, "component", self.componentTag)

            self.setStep(5)
        else:
            logger.debug("component {} already finalized.".format(self.name))

    def optimizeComponent(self):
        """
        Optimize the component
        :return:
        """
        # self._updateClassParameters()

        if self.getStep() != OPTIMIZE_STEP:
            self._optimize()
            self.setStep(6)
        else:
            logger.debug("component {} already optimized.".format(self.name))

    # --------------------------------------------------------------------------------
    # functions
    # --------------------------------------------------------------------------------
    def _createJoints(self):
        """build joints required for the component"""
        pass

    def _createBuildGuides(self):
        """Add additional guides"""
        pass

    def _setInitialData(self):
        """
        Set initial component data.
        This allows you to set component data within subclasses.
        """
        pass

    def _createContainer(self):
        """Create a Container for the component"""
        if not cmds.objExists(self.container):
            self.container = container.create(self.container)
            meta.tag(self.container, "component")

            # tag the container with the proper component version
            attr.createAttr(
                self.container,
                "__version__",
                "string",
                value=self.__version__,
                keyable=False,
                locked=True,
            )

    def _createMetaNode(self, metaNodeName):
        """Create the metadata node. This will store any data we need to transfer across steps"""
        if not cmds.objExists(metaNodeName):
            self.metadataNode = cmds.createNode(METADATA_NODE_TYPE, name=metaNodeName)
            meta.createMessageConnection(
                self.container, self.metadataNode, sourceAttr="metaDataNetworkNode"
            )

            container.addNodes(self.metadataNode, self.container, force=True)

    def _autoOrientGuides(self):
        """Automate positioning and orienting of the guides."""

    def _initialHierarchy(self):
        """Setup the initial Hierarchy. implement in subclass"""
        self.rootHierarchy = cmds.createNode("transform", name=self.name + "_cmpt")
        self.paramsHierarchy = cmds.createNode(
            "transform", name=self.name + "_params", parent=self.rootHierarchy
        )
        self.controlHierarchy = cmds.createNode(
            "transform", name=self.name + "_control", parent=self.rootHierarchy
        )
        self.spacesHierarchy = cmds.createNode(
            "transform", name=self.name + "_spaces", parent=self.rootHierarchy
        )

        color.setOutlinerColor(self.rootHierarchy, [255, 255, 153])

        # lock and hide the attributes
        for hierarchy in [
            self.paramsHierarchy,
            self.controlHierarchy,
            self.spacesHierarchy,
        ]:
            attr.lockAndHide(hierarchy, attr.TRANSFORMS + ["v"])

    def _preRigSetup(self):
        """Pre rig setup. implement in subclass"""
        pass

    def _rigSetup(self):
        """Add the rig setup. implement in subclass"""
        pass

    def _postRigSetup(self):
        """Add the post setup. implement in subclass"""
        pass

    def _setupAnimAttrs(self):
        """Setup animation attributes. implement in subclass"""
        pass

    def _preConnect(self):
        """initialize the connection. implement in subclass"""
        pass

    def _connect(self):
        """create the connection. implement in subclass"""
        pass

    def _postConnect(self):
        """any final cleanup after the connection. implement in subclass"""
        pass

    def _publishNodes(self):
        """Publish nodes. implement in subclass"""
        container.addParentAnchor(self.rootHierarchy, container=self.container)
        container.addChildAnchor(self.rootHierarchy, container=self.container)

        # for the containers we need to _publish all controls within a container.
        allNodes = container.getNodesInContainer(self.container, getSubContained=True)
        for currentNode in allNodes:
            if meta.hasTag(currentNode, CONTROL_TAG):
                container.addPublishNodes(currentNode)

    def _publishAttributes(self):
        """_publish attributes. implement in subclass"""
        pass

    def _finalize(self):
        """Finalize a component. implement in subclass"""
        pass

    def _setControlAttributes(self):
        """Set attributes. implement in subclass"""
        pass

    def _optimize(self):
        """Optimize a component. implement in subclass"""
        pass

    def deleteSetup(self):
        """delete the rig setup"""
        logger.info("deleting component {}".format(self.name))
        cmds.select(self.container, replace=True)
        mel.eval("doDelete;")

        for input in self.input:
            if cmds.objExists(input):
                attr.unlock(input, attr.TRANSFORMS + ["v"])

    def setStep(self, step=0):
        """
        set the pipeline step.

        step 0 - unbuilt
        step 1 - initialize component
        step 2 - guide component
        step 3 - build component
        step 4 - connect component
        step 5 - finalize component
        step 6 - optimize component

        :param step:
        :return:
        """
        if not cmds.objExists("{}.{}".format(self.container, "build_step")):
            attr.createEnum(
                self.container,
                "build_step",
                value=0,
                enum=[
                    "unbuilt",
                    "initialize",
                    "guide",
                    "build",
                    "connect",
                    "finalize",
                    "optimize",
                ],
                keyable=False,
                channelBox=False,
            )

        cmds.setAttr("{}.{}".format(self.container, "build_step"), step)

    def getStep(self):
        """
        get the pipeline step
        :return:
        """
        if self.container and cmds.objExists(
            "{}.{}".format(self.container, "build_step")
        ):
            return cmds.getAttr("{}.{}".format(self.container, "build_step"))
        return 0

    def defineParameter(
        self,
        parameter: str,
        value: typing.Any,
        dataType: str = None,
        hide: bool = True,
        lock: bool = False,
        tooltip: str = None,
    ):
        """
        Define a parameter component. This makes up the core data structure of a component.
        This defines parameters and behaviors and is used to build the rest of the functionality but should NOT define the structre.

        :param str parameter: name of the parameter, This will be accessible through self.parameter in the class
        :param any value: the value of the parameter
        :param dataType: the type of data stored in the value. Default is derived from the value.
        :param bool hide: hide the added parameter from the channel box
        :param bool lock: lock the added parameter
        :param bool tooltip: Define a tooltip for the parameter. Shows up in the UI.
        """

        if not dataType:
            dataType = meta.validateDataType(value)

        logger.debug(f"adding component parameter {parameter}, {value} ({dataType})")
        self._componentParameters[parameter] = {"value": value, "dataType": dataType}

        if tooltip:
            self._componentParameters[parameter].update({"tooltip": tooltip})

        self.setParameterValue(parameter=parameter, value=value, hide=hide, lock=lock)

    def setParameterValue(
        self, parameter: str, value: typing.Any, hide: bool = True, lock: bool = False
    ) -> None:
        """
        Set the parameter value. unlike define parameter this will attempt to set the parameter to the given data type
        :param parameter:
        :param value:
        :param bool hide: hide the added parameter from the channel box
        :param bool lock: lock the added parameter
        :return:
        """
        if parameter not in self._componentParameters.keys():
            logger.warning(
                f"Parameter {parameter} does not exist on {self.__class__.__name__}"
            )
            return

        self._componentParameters[parameter]["value"] = value
        dataType = self._componentParameters[parameter].get("dataType")
        if not dataType:
            raise TypeError(f"{parameter} data type cannot be None")

        metaData = meta.MetaNode(self.container)
        metaData.setData(
            attr=parameter, value=value, attrType=dataType, hide=hide, lock=lock
        )

        setattr(self.__class__, parameter, value)

    def _getLocalComponentVariables(self):
        """Get a list of class variables"""

        localComponentVariables = list()
        allClassVariables = self.__dict__.keys()

        for var in allClassVariables:
            # ensure the variable is valid.
            if var in self._componentParameters:
                continue
            if var.startswith("_"):
                continue
            if var in [
                "container",
                "metadataNode",
                "metaDataNetworkNode",
                "componentType",
            ]:
                continue

            localComponentVariables.append(var)

        return localComponentVariables

    def _stashLocalVariablesToMetadata(self):
        localComponentVariables = self._getLocalComponentVariables()

        localComponentDataDict = {}

        for localVariable in localComponentVariables:
            localComponentDataDict[localVariable] = self.__getattribute__(localVariable)

        metaNode = meta.MetaNode(self.metadataNode)
        metaNode.setDataDict(localComponentDataDict)

    def _retreiveLocalVariablesFromMetadata(self):
        """
        This function will rebuild the properties based on the data added to the metanode.
        :return:
        """
        metaNode = meta.MetaNode(self.metadataNode)
        dataDict = metaNode.getAllData()

        for key in dataDict.keys():
            if key in ["metaDataNetworkNode"]:
                continue
            attrPlug = f"{self.metadataNode}.{key}"

            # # TODO: come back to this
            setattr(self.__class__, key, dataDict[key])

    def _updateClassParameters(self):
        """
        loadSettings metadata from the settings node into a dictionary.
        Only updates the value of the component parameters
        """
        newComponentData = self._componentParameters.copy()
        for key in self._componentParameters.keys():
            metaNode = meta.MetaNode(self.container)
            data = metaNode.getAllData()

            if not data:
                data = self._componentParameters

            if key in data.keys():
                setattr(self, key, data[key])
                newComponentData[key]["value"] = data[key]

        self._componentParameters.update(newComponentData)

    # GET
    def getContainer(self):
        """
        get the component container
        """
        if cmds.objExists(self.container):
            return self.container
        return None

    def getName(self):
        """Get component name"""
        return self.name

    def getMetaDataNode(self):
        return meta.getMessageConnection(f"{self.container}.metaDataNetworkNode")

    def getComponentData(self):
        """Get all component Data"""
        # ensure we are saving the most up-to-date versions of our code
        self._updateClassParameters()

        # create an info dictionary with the important component settings.
        infoDict = OrderedDict()

        for key in self._componentParameters.keys():
            # Check if the value associated with the key is a dictionary
            if isinstance(self._componentParameters[key], dict):
                value = self._componentParameters[key].get("value")
                if value is not None:
                    infoDict[key] = value

        logger.debug(infoDict)
        return infoDict

    def getComponentType(self):
        """Get the component type"""
        return self.componentType

    # SET
    def setName(self, value):
        """Set the component name"""
        self.name = value

    def setContainer(self, value):
        """Set the component container"""
        self.container = value

    # @staticmethod
    # def __getPropertyValue(propertyPlug):
    #     """used to dynamically get the value of a property"""
    #     propertyHolderNode, propertyAttr = propertyPlug.split(".")
    #
    #     def getter(self):
    #         metaNode = meta.MetaNode(propertyHolderNode)
    #         return metaNode.getData(propertyAttr)
    #
    #     return getter
    #
    # @staticmethod
    # def __setPropertyValue(propertyPlug):
    #     """Used to dynamically set the value of a propery"""
    #     propertyHolderNode, propertyAttr = propertyPlug.split(".")
    #
    #     def setter(self, value):
    #         metaNode = meta.MetaNode(propertyHolderNode)
    #         return metaNode.setData(propertyAttr, value=value)
    #
    #     return setter
