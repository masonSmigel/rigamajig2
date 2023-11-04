"""
hand component
"""
import maya.cmds as cmds

import rigamajig2.maya.attr as rig_attr
import rigamajig2.maya.components.base
import rigamajig2.maya.components.chain.chain
import rigamajig2.maya.components.hand.gestureUtils as gestureUtils
import rigamajig2.maya.meta as meta
import rigamajig2.maya.rig.control as rig_control
import rigamajig2.maya.rig.spaces as spaces
import rigamajig2.maya.transform as rig_transform
import rigamajig2.shared.common as common

FINGER_NAMES = ["thumb", "index", "middle", "ring", "pinky"]


class Hand(rigamajig2.maya.components.base.Base):
    """
    Hand component.
    The Hand is a system of chain components based on the input of each start finger joint.
    The component also adds a pose control.
    """

    VERSION_MAJOR = 1
    VERSION_MINOR = 1
    VERSION_PATCH = 1

    version_info = (VERSION_MAJOR, VERSION_MINOR, VERSION_PATCH)
    version = "%i.%i.%i" % version_info
    __version__ = version

    UI_COLOR = (0, 107, 185)

    def __init__(self, name, input, size=1, rigParent=str(), componentTag=None):
        """
        :param name: name of the components
        :type name: str
        :param input: list of base joints for each finger. Add the joints in from thumb to pinky
        :type input: list
        :param size: default size of the controls:
        :param useScale: enable the animator to scale the controls
        :type useScale: bool
        :param addFKSpace: add an FK space switch:
        :type addFKSpace: bool
        :param bool useSubMeta: use th subMeta controls between the meta and the first finger joint
        :param bool useFirstAsThumb: use the first input as a thumb. (it has special rules)
        """
        super(Hand, self).__init__(name, input=input, size=size, rigParent=rigParent, componentTag=componentTag)
        self.side = common.getSide(self.name)

        self.useScale = False
        self.addFKSpace = False
        self.useSubMeta = True
        self.useFirstAsThumb = True

        self.defineParameter(parameter="useScale", value=self.useScale, dataType="bool")
        self.defineParameter(parameter="addFKSpace", value=self.addFKSpace, dataType="bool")
        self.defineParameter(parameter="useSubMeta", value=self.useSubMeta, dataType="bool")
        self.defineParameter(parameter="useFirstAsThumb", value=self.useFirstAsThumb, dataType="bool")

        # initialize some other variables we need
        self.fingerComponentList = list()

    def _createBuildGuides(self):
        """Show Advanced Proxy"""
        self.guidesHierarchy = cmds.createNode("transform", name="{}_guide".format(self.name))

        self.thumbCupGuide = rig_control.createGuide("{}_thumbCup".format(self.name), parent=self.guidesHierarchy)
        rig_transform.matchTranslate(self.input[0], self.thumbCupGuide)

        if self.side == "r":
            cmds.xform(self.thumbCupGuide, worldSpace=True, rotation=(180, 0, 0))

    def _initialHierarchy(self):
        """Build the initial hierarchy"""
        super(Hand, self)._initialHierarchy()

        # create the hand gesture controller
        pos = rig_transform.getAveragePoint(self.input[1:])
        self.wrist = rig_control.create(
            "{}_poses".format(self.name),
            shape="square",
            position=pos,
            parent=self.controlHierarchy,
            hideAttrs=["t", "r", "s", "v"],
        )

        # disable auto-container placement
        cmds.container(self.container, edit=True, current=False)

        # initialize new components
        self.fingerComponentList = list()
        inputBaseNames = [x.split("_")[0] for x in self.input]
        for i in range(len(self.input)):
            allDescendants = cmds.listRelatives(self.input[i], allDescendents=True)
            allDescendants.reverse()
            endJoint = cmds.ls(allDescendants, type="joint")[-1]

            # initialize a finger component
            fingerName = inputBaseNames[i] + "_" + self.side if self.side else inputBaseNames[i]
            fingerComponent = rigamajig2.maya.components.chain.chain.Chain(
                fingerName, input=[self.input[i], endJoint], rigParent=self.wrist.name
            )
            fingerComponent.defineParameter("useScale", self.useScale)
            fingerComponent.defineParameter("addSdk", True)
            fingerComponent.defineParameter("addFKSpace", self.addFKSpace)

            fingerComponent.initializeComponent()
            cmds.container(self.container, edit=True, force=True, addNode=fingerComponent.getContainer())
            meta.tag(fingerComponent.getContainer(), "subComponent")
            self.fingerComponentList.append(fingerComponent)

    def _rigSetup(self):
        self.cupControls = list()
        for i, fingerComponent in enumerate(self.fingerComponentList):
            fingerComponent.buildComponent()
            cmds.parent(fingerComponent.controlHierarchy, self.controlHierarchy)
            cmds.parent(fingerComponent.spacesHierarchy, self.spacesHierarchy)

            # setup the cup controls
            if i == 0 and self.useFirstAsThumb:
                cupControl = rig_control.createAtObject(
                    fingerComponent.name + "Cup",
                    shape="cube",
                    orig=True,
                    trs=True,
                    parent=self.wrist.name,
                    xformObj=self.thumbCupGuide,
                )
                baseOffset = rig_control.Control(fingerComponent.controlsList[0]).orig
                cmds.parent(baseOffset, cupControl.name)

                self.cupControls.append(cupControl)

            elif i == 1 or i == 0:
                cupControl = rig_control.createAtObject(
                    fingerComponent.name + "Cup",
                    shape="cube",
                    orig=True,
                    trs=True,
                    parent=self.wrist.name,
                    xformObj=self.input[i + 1],
                )
                baseOffset = rig_control.Control(fingerComponent.controlsList[0]).orig

                if i == 1:
                    cmds.parent(baseOffset, self.cupControls[0].orig, cupControl.name)
                else:
                    cmds.parent(baseOffset, cupControl.name)
                self.cupControls.append(cupControl)

            elif i == 2:
                baseOffset = rig_control.Control(fingerComponent.controlsList[0]).orig
                cmds.parent(baseOffset, self.wrist.name)

            elif i > 2:
                parent = self.wrist.name if i < 4 else self.cupControls[-1].name

                cupControl = rig_control.createAtObject(
                    fingerComponent.name + "Cup",
                    shape="cube",
                    orig=True,
                    trs=True,
                    parent=parent,
                    xformObj=self.input[i - 1],
                )
                baseOffset = rig_control.Control(fingerComponent.controlsList[0]).orig
                cmds.parent(baseOffset, cupControl.name)

                self.cupControls.append(cupControl)

            # delete the root hrc from the finger component and re-assign the hand to be the component root
            cmds.delete(fingerComponent.rootHierarchy)
            cmds.delete(fingerComponent.controlHierarchy)
            fingerComponent.rootHierarchy = self.rootHierarchy

        self.setupSdk()

    def setupSdk(self):
        """setup the sdks in the rig"""
        metaControlsNum = 2 if self.useSubMeta else 1
        metasList = [x.controlsList[0] for x in self.fingerComponentList]
        metaSecondList = [x.controlsList[1] for x in self.fingerComponentList]
        fingerBaseList = [x.controlsList[metaControlsNum] for x in self.fingerComponentList]

        # setup the spreads
        rig_attr.addSeparator(self.wrist.name, "spread")
        gestureUtils.setupSpreadSdk(metasList[1:], self.wrist.name, "fingerSpread", multiplier=0.1)
        gestureUtils.setupSpreadSdk(metaSecondList[1:], self.wrist.name, "fingerSpread", multiplier=0.05)
        gestureUtils.setupSpreadSdk(fingerBaseList[1:], self.wrist.name, "fingerSpread", multiplier=0.85)

        gestureUtils.setupSpreadSdk(metasList[1:], self.wrist.name, "metaSpread", multiplier=0.7)
        gestureUtils.setupSpreadSdk(metaSecondList[1:], self.wrist.name, "metaSpread", multiplier=0.3)

        gestureUtils.setupSpreadSdk(metaSecondList[1:], self.wrist.name, "palmSpread", multiplier=1)

        rig_attr.addSeparator(self.wrist.name, "curl")
        fingerNameList = common.fillList(FINGER_NAMES, "finger", len(self.fingerComponentList))
        for finger, fingerComponent in zip(fingerNameList, self.fingerComponentList):
            gestureUtils.setupCurlSdk(
                fingerComponent.controlsList, self.wrist.name, "{}Curl".format(finger), metaControls=metaControlsNum
            )

        rig_attr.addSeparator(self.wrist.name, "splay")
        gestureUtils.setupFanSdk(metasList[1:], self.wrist.name, "MetaSplay", multiplier=1)
        gestureUtils.setupFanSdk(fingerBaseList[1:], self.wrist.name, "FingerSplay", multiplier=1)

        rig_attr.addSeparator(self.wrist.name, "relax")

        # Setup the finger relax we should slowly decrease the influence from the pinky to the index.
        # the lenFingers variable is used to create a multiplier to stabilize the rotation when there are
        # more or less than 4 fingers.
        offset = 0.25
        for i, fingerComponent in enumerate(self.fingerComponentList[1:]):
            value = offset * (i + 1)
            gestureUtils.setupCurlSdk(
                fingerComponent.controlsList, self.wrist.name, "relax", multiplier=value, metaControls=metaControlsNum
            )

        # setup the cupping control
        rig_attr.addSeparator(self.wrist.name, "cup")
        for i in range(len(self.cupControls)):
            fingerName = self.cupControls[i].trs.split("_")[0]
            if i < 2:
                gestureUtils.setupSimple(self.cupControls[i].trs, self.wrist.name, fingerName + "Cup", multplier=1)
            else:
                gestureUtils.setupSimple(self.cupControls[i].trs, self.wrist.name, fingerName + "Cup", multplier=-1)

    def _setupAnimAttrs(self):
        """setup animation attributes"""

        rigamajig2.maya.attr.addSeparator(self.wrist.name, "visibility")
        # add an attribute to hide the finger controls
        rigamajig2.maya.attr.createAttr(self.wrist.name, "cupPivots", "bool", value=0, keyable=False, channelBox=True)
        cupControls = [x.name for x in self.cupControls]
        rig_control.connectControlVisiblity(self.wrist.name, "cupPivots", cupControls)

        rigamajig2.maya.attr.createAttr(self.wrist.name, "fingers", "bool", value=1, keyable=False, channelBox=True)
        fingerControls = [x.controlsList for x in self.fingerComponentList]
        rig_control.connectControlVisiblity(self.wrist.name, "fingers", fingerControls)

    def _connect(self):
        if cmds.objExists(self.rigParent):
            rig_transform.connectOffsetParentMatrix(self.rigParent, self.wrist.orig, mo=True)

        if self.addFKSpace:
            self.wrist.addSdk()
            spaces.create(self.wrist.spaces, self.wrist.name, parent=self.spacesHierarchy)

            # if the main control exists connect the world space
            if cmds.objExists("trs_motion"):
                spaces.addSpace(self.wrist.spaces, ["trs_motion"], nameList=["world"], constraintType="orient")

    def _finalize(self):
        # navigate around container parenting since we have already parented the containers to the hand container
        for fingerComponent in self.fingerComponentList:
            fingerComponent._finalize()

    def _optimize(self):
        """Optimize the component"""
        for fingerComponent in self.fingerComponentList:
            fingerComponent.optimizeComponent()

    def __deleteSetup(self):
        """Delete the rig setup"""
        for fingerComponent in self.fingerComponentList:
            fingerComponent.__deleteSetup()
        super(Hand, self).__deleteSetup()
