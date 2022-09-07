"""
hand component
"""
import maya.cmds as cmds
import rigamajig2.maya.cmpts.base
import rigamajig2.maya.cmpts.chain.chain
import rigamajig2.maya.rig.control as rig_control
import rigamajig2.maya.rig.spaces as spaces
import rigamajig2.maya.rig.ikfk as ikfk
import rigamajig2.maya.transform as rig_transform
import rigamajig2.maya.attr as rig_attr
import rigamajig2.shared.common as common
import rigamajig2.maya.meta as meta
import rigamajig2.maya.container as container
import rigamajig2.maya.sdk as sdk
import rigamajig2.maya.hierarchy as hierarchy

import rigamajig2.maya.cmpts.hand.gestureUtils as gestureUtils

import logging

logger = logging.getLogger(__name__)

FINGER_NAMES = ['thumb', 'index', 'middle', 'ring', 'pinky']


class Hand(rigamajig2.maya.cmpts.base.Base):
    """
    Hand component.
    The Hand is a system of chain components based on the input of each start finger joint.
    The component also adds a pose control.
    """
    VERSION_MAJOR = 1
    VERSION_MINOR = 0
    VERSION_PATCH = 1

    version_info = (VERSION_MAJOR, VERSION_MINOR, VERSION_PATCH)
    version = '%i.%i.%i' % version_info
    __version__ = version

    def __init__(self, name, input, size=1, rigParent=str(),
                 useProxyAttrs=True, useScale=False, addFKSpace=False, useSubMeta=True, useFirstAsThumb=True):
        """
        :param name: name of the components
        :type name: str
        :param input: list of base joints for each finger. Add the joints in from thumb to pinky
        :type input: list
        :param size: default size of the controls:
        :param useProxyAttrs: use proxy attributes instead of an ikfk control
        :type useProxyAttrs: bool
        :param useScale: enable the animator to scale the controls
        :type useScale: bool
        :param addFKSpace: add an FK space switch:
        :type addFKSpace: bool
        :param bool useSubMeta: use th subMeta controls between the meta and the first finger joint
        :param bool useFirstAsThumb: use the first input as a thumb. (it has special rules)
        """
        super(Hand, self).__init__(name, input=input, size=size, rigParent=rigParent)
        self.side = common.getSide(self.name)

        self.cmptSettings['useProxyAttrs'] = useProxyAttrs
        self.cmptSettings['useScale'] = useScale
        self.cmptSettings['addFKSpace'] = addFKSpace
        self.cmptSettings['useSubMeta'] = useSubMeta
        self.cmptSettings['useFirstAsThumb'] = useFirstAsThumb

        # initalize some other variables we need
        self.fingerComponentList = list()

    def createBuildGuides(self):
        """Show Advanced Proxy"""
        self.guidesHierarchy = cmds.createNode("transform", name='{}_guide'.format(self.name))

        self.thumbCupGuide = rig_control.createGuide("{}_thumbCup".format(self.name), parent=self.guidesHierarchy)
        rig_transform.matchTranslate(self.input[0], self.thumbCupGuide)

        if self.side == 'r':
            cmds.xform(self.thumbCupGuide, ws=True, ro=(180, 0, 0))

    def initalHierachy(self):
        """Build the initial hirarchy"""
        super(Hand, self).initalHierachy()

        # create the hand gesture controller
        pos = rig_transform.getAveragePoint(self.input[1:])
        self.wrist = rig_control.create("{}_poses".format(self.name),
                                        shape='square',
                                        position=pos,
                                        parent=self.controlHierarchy,
                                        hideAttrs=['t', 'r', 's', 'v'])

        # disable auto-container placement
        cmds.container(self.container, e=True, c=False)

        # intialize new compoents
        self.fingerComponentList = list()
        inputBaseNames = [x.split("_")[0] for x in self.input]
        for i in range(len(self.input)):
            endJoint = cmds.ls(reversed(cmds.listRelatives(self.input[i], ad=True)), type='joint')[-1]

            # initalize a finger component
            fingerName = inputBaseNames[i] + '_' + self.side if self.side else inputBaseNames[i]
            fingerComponent = rigamajig2.maya.cmpts.chain.chain.Chain(
                fingerName,
                input=[self.input[i], endJoint],
                useScale=self.useScale,
                addSdk=True,
                addFKSpace=self.addFKSpace,
                rigParent=self.wrist.name
                )

            fingerComponent._initalizeComponent()
            cmds.container(self.container, e=True, f=True, addNode=fingerComponent.getContainer())
            meta.tag(fingerComponent.getContainer(), 'subComponent')
            self.fingerComponentList.append(fingerComponent)

    def rigSetup(self):
        self.cupControls = list()
        for i, cmpt in enumerate(self.fingerComponentList):
            cmpt._buildComponent()
            cmds.parent(cmpt.controlHierarchy, self.controlHierarchy)
            cmds.parent(cmpt.spacesHierarchy, self.spacesHierarchy)

            # setup the cup controls
            if i == 0 and self.useFirstAsThumb:

                cupControl = rig_control.createAtObject(cmpt.name + "Cup", shape='cube', orig=True, trs=True,
                                                        parent=self.wrist.name, xformObj=self.thumbCupGuide)
                baseOffset = rig_control.Control(cmpt.controlers[0]).orig
                cmds.parent(baseOffset, cupControl.name)

                self.cupControls.append(cupControl)

            elif i == 1 or not self.useFirstAsThumb:

                cupControl = rig_control.createAtObject(cmpt.name + "Cup", shape='cube', orig=True, trs=True,
                                                        parent=self.wrist.name, xformObj=self.input[i + 1])
                baseOffset = rig_control.Control(cmpt.controlers[0]).orig

                if i == 1:
                    cmds.parent(baseOffset, self.cupControls[0].orig, cupControl.name)
                else:
                    cmds.parent(baseOffset, cupControl.name)
                self.cupControls.append(cupControl)

            elif i == 2:
                baseOffset = rig_control.Control(cmpt.controlers[0]).orig
                cmds.parent(baseOffset, self.wrist.name)

            elif i > 2:
                parent = self.wrist.name if i < 4 else self.cupControls[-1].name

                cupControl = rig_control.createAtObject(cmpt.name + "Cup", shape='cube', orig=True, trs=True,
                                                        parent=parent, xformObj=self.input[i - 1])
                baseOffset = rig_control.Control(cmpt.controlers[0]).orig
                cmds.parent(baseOffset, cupControl.name)

                self.cupControls.append(cupControl)

            # delete the root hrc from the finger component and re-assign the hand to be the componet root
            cmds.delete(cmpt.rootHierarchy)
            cmds.delete(cmpt.controlHierarchy)
            cmpt.rootHierarchy = self.rootHierarchy

        self.setupSdk()

    def setupSdk(self):
        """setup the sdks in the rig """
        metaControlsNum = 2 if self.useSubMeta else 1
        metasList = [x.controlers[0] for x in self.fingerComponentList]
        metaSecondList = [x.controlers[1] for x in self.fingerComponentList]
        fingerBaseList = [x.controlers[metaControlsNum] for x in self.fingerComponentList]

        # setup the spreads
        rig_attr.addSeparator(self.wrist.name, 'spread')
        gestureUtils.setupSpreadSdk(metasList[1:], self.wrist.name, "fingerSpread", multiplier=0.1)
        gestureUtils.setupSpreadSdk(metaSecondList[1:], self.wrist.name, "fingerSpread", multiplier=0.05)
        gestureUtils.setupSpreadSdk(fingerBaseList[1:], self.wrist.name, "fingerSpread", multiplier=0.85)

        gestureUtils.setupSpreadSdk(metasList[1:], self.wrist.name, "metaSpread", multiplier=0.7)
        gestureUtils.setupSpreadSdk(metaSecondList[1:], self.wrist.name, "metaSpread", multiplier=0.3)

        gestureUtils.setupSpreadSdk(metaSecondList[1:], self.wrist.name, "palmSpread", multiplier=1)

        rig_attr.addSeparator(self.wrist.name, 'curl')
        fingerNameList = common.fillList(FINGER_NAMES, 'finger', len(self.fingerComponentList))
        for finger, cmpt in zip(fingerNameList, self.fingerComponentList):
            gestureUtils.setupCurlSdk(cmpt.controlers, self.wrist.name, "{}Curl".format(finger),
                                      metaControls=metaControlsNum)

        rig_attr.addSeparator(self.wrist.name, 'splay')
        gestureUtils.setupFanSdk(metasList[1:], self.wrist.name, "MetaSplay", multiplier=1)
        gestureUtils.setupFanSdk(fingerBaseList[1:], self.wrist.name, "FingerSplay", multiplier=1)

        rig_attr.addSeparator(self.wrist.name, 'relax')

        # Setup the finger relax we should slowly decrease the influence from the pinky to the index.
        # the lenFingers varrible is used to create a multiplier to stablize the rotation when there are
        # more or less then 4 fingers.
        offset = 0.25
        for i, cmpt in enumerate(self.fingerComponentList[1:]):
            value = offset * (i + 1)
            gestureUtils.setupCurlSdk(cmpt.controlers, self.wrist.name, "relax", multiplier=value,
                                      metaControls=metaControlsNum)

        # setup the cupping control
        rig_attr.addSeparator(self.wrist.name, 'cup')
        for i in range(len(self.cupControls)):
            fingerName = self.cupControls[i].trs.split("_")[0]
            if i < 2:
                gestureUtils.setupSimple(self.cupControls[i].trs, self.wrist.name, fingerName + 'Cup', multplier=1)
            else:
                gestureUtils.setupSimple(self.cupControls[i].trs, self.wrist.name, fingerName + 'Cup', multplier=-1)

    def connect(self):
        if cmds.objExists(self.rigParent):
            rig_transform.connectOffsetParentMatrix(self.rigParent, self.wrist.orig, mo=True)

        if self.addFKSpace:
            self.wrist.addSdk()
            spaces.create(self.wrist.spaces, self.wrist.name, parent=self.spacesHierarchy)

            # if the main control exists connect the world space
            if cmds.objExists('trs_motion'):
                spaces.addSpace(self.wrist.spaces, ['trs_motion'], nameList=['world'], constraintType='orient')

    def finalize(self):
        # navigate around container parenting since we have already parented the containers to the hand container
        for cmpt in self.fingerComponentList:
            cmpt.finalize()
            cmpt.setAttrs()
            cmpt.postScript()

    def optimize(self):
        """Optimize the component"""
        for cmpt in self.fingerComponentList:
            cmpt._optimizeComponent()

    def deleteSetup(self):
        """Delete the rig setup"""
        for cmpt in self.fingerComponentList:
            cmpt.deleteSetup()
        super(Hand, self).deleteSetup()

    @staticmethod
    def createInputJoints(name=None, side=None, numJoints=None):
        """static method to create input joints"""
        import rigamajig2.maya.naming as naming
        import rigamajig2.maya.joint as joint
        guidePostions = {
            "thumb": (1, 0, 6),
            "index": (2, 0, 2),
            "middle": (2, 0, 0),
            "ring": (2, 0, -2),
            "pinky": (2, 0, -4),
            }
        joints = list()

        for i, finger in enumerate(['thumb', 'index', 'middle', 'ring', 'pinky']):
            parent = None
            jointNum = 6
            if finger == 'thumb':
                jointNum = 5

            for j in range(jointNum):

                name = naming.getUniqueName(finger + "_0", side=side)
                jnt = cmds.createNode("joint", name=name)
                if parent:
                    cmds.parent(jnt, parent)

                if j < 1:
                    position = guidePostions[finger]
                    joints.append(jnt)
                    rootJnt = jnt
                elif j == 2:
                    position = (6, 0, 0)
                    if finger == 'thumb':
                        position = (4, 0, 0)
                elif j == 3:
                    position = (3, 0, 0)
                else:
                    position = (2, 0, 0)

                # apply the postion.
                if side == 'r':
                    position = (position[0] * -1, position[1], position[2])
                cmds.xform(jnt, os=True, t=position)

                parent = jnt

            if side == 'r':
                cmds.setAttr("{}.jox".format(rootJnt), 180)

        return joints
