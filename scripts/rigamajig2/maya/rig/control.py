"""
Controller functions
"""
import os
import maya.cmds as cmds

import rigamajig2.maya.decorators
import rigamajig2.shared.common as common
import rigamajig2.shared.path
import rigamajig2.maya.naming
import rigamajig2.maya.hierarchy
import rigamajig2.maya.data.curve_data
import rigamajig2.maya.curve
import rigamajig2.maya.color
import rigamajig2.maya.transform
import rigamajig2.maya.meta as meta
import rigamajig2.maya.shape
import rigamajig2.maya.attr
import rigamajig2.maya.joint

CONTROLSHAPES = os.path.join(os.path.dirname(__file__), "controlShapes.data").replace("\\", "/")

CONTROLTAG = 'control'


class Control(object):
    """Utility class for working with rig controlers"""

    def __init__(self, control):
        """
        this is the constructor for the Control class.
        The control class manages transforms for a control such as the offset, trs and sdk groups.


        transforms should go in the following order:
        | orig
          |- spaces
            |- trs
              |- sdk
                |- control


        :param control:
        """
        self.control = control

    def addOrig(self):
        """
        Add a transform orig group.
        It will be placed at the top of the controler node heirarchy
        :return: name of the orig node if one was created
        """
        if cmds.objExists("{}.__{}__".format(self.control, common.ORIG)):
            return None

        orig = rigamajig2.maya.hierarchy.create(self.control, [self.control + "_" + common.ORIG], above=True)
        meta.createMessageConnection(sourceNode=self.control, destNode=orig[0], sourceAttr="__{}__".format(common.ORIG))

    def addSpaces(self):
        """
        Add a transform spaces group.
        It will be placed under the orig group
        :return: name of the spaces node if one was created
        """
        if cmds.objExists("{}.__{}__".format(self.control, common.SPACES)):
            return None

        sdkNode = self.getNode(common.SDK)
        trsNode = self.getNode(common.SDK)
        if trsNode:
            child = trsNode
        elif sdkNode:
            child = sdkNode
        else:
            child = self.control

        spaces = rigamajig2.maya.hierarchy.create(child, [self.control + "_" + common.SPACES], above=True)
        meta.createMessageConnection(sourceNode=self.control, destNode=spaces[0],
                                     sourceAttr="__{}__".format(common.SPACES))

    def addSdk(self):
        """
        Add a transform sdk group.
        It will be placed between the trs and control nodes
        :return: name of the sdk node if one was created
        """
        if cmds.objExists("{}.__{}__".format(self.control, common.SDK)):
            return None

        sdk = rigamajig2.maya.hierarchy.create(self.control, [self.control + "_" + common.SDK], above=True)
        meta.createMessageConnection(sourceNode=self.control, destNode=sdk[0], sourceAttr="__{}__".format(common.SDK))
        return sdk[0]

    def addTrs(self, name=None):
        """
        Add a transform offset group.
        It will be placed between the spaces and sdk nodes
        :param name: optional name to add. It will be added as "{}Trs"
        :return: name of the trs node if one was created
        """
        if cmds.objExists("{}.__{}__".format(self.control, common.TRS)):
            return None

        sdkNode = self.getNode(common.SDK)
        if sdkNode:
            trsChild = sdkNode
        else:
            trsChild = self.control

        trsSuffix = "_{}Trs".format(name) if name else "_trs"
        trs = rigamajig2.maya.hierarchy.create(trsChild, [self.control + trsSuffix], above=True)
        meta.createMessageConnection(sourceNode=self.control, destNode=trs[0], sourceAttr="__{}__".format(common.TRS))

    def getNode(self, node):
        """
        Get the name of a node associated with the controller.
        This is used for other subclasses to get shapes in a more UX freindly way.
        :param str node: type of controller node to return.
        """

        if cmds.objExists("{}.__{}__".format(self.control, node)):
            return meta.getMessageConnection("{}.__{}__".format(self.control, node))

    @property
    def name(self):
        """
        :return: orign node
        :rtype: str
        """
        return self.control

    @property
    def orig(self):
        """
        :return: orign node
        :rtype: str
        """
        return self.getNode(common.ORIG)

    @property
    def spaces(self):
        """
        :return: spaces node
        :rtype: str
        """
        return self.getNode(common.SPACES)

    @property
    def trs(self):
        """
        :return: trs node
        :rtype: str
        """
        return self.getNode(common.TRS)

    @property
    def sdk(self):
        """
        :return: sdk node
        :rtype: str
        """
        return self.getNode(common.SDK)


def isControl(control):
    """
    Check if the controller is controller
    :param control: name of the controller to check
    :return: True if Valid. False is invalid.
    """
    return meta.hasTag(control, 'control')


# pylint:disable=too-many-arguments
def create(name, side=None, shape='circle', orig=True, spaces=False, trs=False, sdk=False, parent=None,
           position=None, rotation=None, size=1, hideAttrs=None, color='blue', type=None, rotateOrder='xyz',
           trasformType='transform', shapeAim='y'):
    """
    Create a control. It will also create a hierarchy above the control based on the hierarchy list.

    :param str name: Name of the control.
    :param str side: Optional name of the side
    :param str shape: Shape of the control.
    :param bool orig: add an orig node
    :param bool spaces: add spaces node
    :param bool trs: add a trs node
    :param bool sdk: add an sdk node
    :param str parent: Optional- Parent the control under this node in the hierarchy
    :param list tuple position: Optional- Point in world space to position the control.
    :param list tuple rotation: Optional- Rotation in world space to rotate the control.
    :param int float size: Optional- Size of the control
    :param list hideAttrs: Optional- list of attributes to lock and hide. Default is ['v']
    :param str int color: Optional- Color of the control
    :param str type: Optional- Specifiy a control type.
    :param str rotateOrder: Specify a rotation order. Default is 'xyz'
    :param str trasformType: Type of transform to use as a control. "transform", "joint"
    :param str shapeAim: Set the direction to aim the control

    :return: list of hierarchy created above the control plus the control:
    :rtype: list | tuple
    """

    if position is None:
        position = [0, 0, 0]

    if rotation is None:
        rotation = [0, 0, 0]
    if hideAttrs is None:
        hideAttrs = ['v']

    if side:
        name = rigamajig2.maya.naming.getUniqueName("{}_{}".format(name, side))
    else:
        name = rigamajig2.maya.naming.getUniqueName(name)
    control = cmds.createNode(trasformType, name=name)
    tagAsControl(control, type=type)
    topNode = control

    setControlShape(control, shape)

    controlObj = Control(control)
    if orig:
        controlObj.addOrig()
        topNode = controlObj.getNode(common.ORIG)
    if spaces:
        controlObj.addSpaces()
    if trs:
        controlObj.addTrs()
    if sdk:
        controlObj.addSdk()

    # hierarchyList = list()
    # if hierarchy:
    #     for suffix in hierarchy:
    #         node = rigamajig2.maya.naming.getUniqueName(control + "_" + suffix)
    #         hierarchyList.append(node)
    #     rigamajig2.maya.hierarchy.create(control, hierarchy=hierarchyList)
    #     topNode = hierarchyList[0]

    if trasformType == 'joint':
        cmds.setAttr("{}.drawStyle".format(control), 2)
        hideAttrs.append('radius')

    for attr in hideAttrs:
        if cmds.objExists("{}.{}".format(control, attr)):
            rigamajig2.maya.attr.lockAndHide(control, attr)
            # cmds.setAttr("{}.{}".format(control, attr), channelBox=False, keyable=False, lock=True)

    if parent:
        cmds.parent(topNode, parent)
    if position:
        cmds.xform(topNode, ws=True, translation=position)
    if rotation:
        cmds.xform(topNode, ws=True, rotation=rotation)
    if color:
        rigamajig2.maya.color.setOverrideColor(control, color)

    if rotateOrder in rigamajig2.maya.transform.ROTATEORDER:
        cmds.setAttr("{}.rotateOrder".format(control), rigamajig2.maya.transform.ROTATEORDER.index(rotateOrder))

    # scale the control shape
    if size > 0:
        scaleShapes(control, [size, size, size])

    # aim the control shape
    if shapeAim == 'x':
        rotateVector = (0, 0, 90)
    if shapeAim == '-x':
        rotateVector = (0, 0, -90)
    elif shapeAim == 'z':
        rotateVector = (90, 0, 0)
    elif shapeAim == '-z':
        rotateVector = (-90, 0, 0)
    else:
        rotateVector = (0, 0, 0)
    rotateShapes(control, rotateVector)

    tagAsControl(control, type=type)

    return controlObj


# pylint:disable=too-many-arguments
def createAtObject(name, side=None, shape='circle', orig=True, spaces=False, trs=False, sdk=False, parent=None,
                   xformObj=None, size=1, hideAttrs=None, color='blue', type=None, rotateOrder='xyz',
                   trasformType='transform', shapeAim='y'):
    """
    Wrapper to create a control at the position of a node.

    :param str name: Name of the control.
    :param str side: Optional name of the side
    :param str shape: Shape of the control.
    :param bool orig: add an orig node
    :param bool spaces: add spaces node
    :param bool trs: add a trs node
    :param bool sdk: add an sdk node
    :param str parent: Optional- Parent the control under this node in the hierarchy
    :param str list  xformObj: object to snap the control to.
    :param int float size: Optional- Size of the control
    :param list hideAttrs: Optional- list of attributes to lock and hide. Default is ['v']
    :param str int color: Optional- Color of the control
    :param str type: Optional- Specifiy a control type.
    :param str rotateOrder: Specify a rotation order. Default is 'xyz'
    :param str trasformType: Type of transform to use as a control. "transform", "joint"
    :param str shapeAim: Set the direction to aim the control

    :return: list of hierarchy created above the control plus the control:
    :rtype: list | tuple
    """
    if not xformObj:
        cmds.error("You must pass an xform object to create a control at. Otherwise use control.create")
        return

    if not cmds.objExists(xformObj):
        cmds.error(
            "Object {} does not exist. cannot create a control at a transform that doesnt exist".format(xformObj))
        return

    xformObj = common.getFirstIndex(xformObj)

    position = cmds.xform(xformObj, q=True, ws=True, translation=True)
    controlObj = create(name=name, side=side, shape=shape, orig=orig, spaces=spaces, trs=trs, sdk=sdk,
                        parent=parent, position=position, size=size, rotation=[0, 0, 0],
                        hideAttrs=hideAttrs, color=color, type=type, rotateOrder=rotateOrder,
                        trasformType=trasformType, shapeAim=shapeAim)
    orig = controlObj.getNode(common.ORIG)
    rigamajig2.maya.transform.matchRotate(xformObj, orig)
    return controlObj


def getAvailableControlShapes():
    """
    Get a list of available control shapes
    """
    controlData = rigamajig2.maya.data.curve_data.CurveData()
    controlData.read(CONTROLSHAPES)
    controlData = controlData.getData()
    return controlData.keys()


def tagAsControl(control, type=None):
    """
    Tag the object as a control
    :param control:
    :param type: Add a special type
    :return:
    """
    meta.tag(control, CONTROLTAG, type=type)


def untagAsControl(control):
    """
    untag specified controls as a control
    :param control: control to remove tag from
    """
    meta.untag(control, CONTROLTAG)


def getControls(namespace=None):
    """
    Get a list of all the controls in a scene.
    :param namespace: Get controls found within a specific namespace
    :type namespace: str
    :return:
    """
    return meta.getTagged(CONTROLTAG, namespace=namespace)


def createDisplayLine(point1, point2, name=None, parent=None, displayType='temp'):
    """
    Create a display line between two points
    :param point1: First node to connect the line to.
    :param point2: Second node to connect the line to.
    :param name: Name of the display line
    :param parent: node to parent the display line to
    :param displayType: Set the display type. Valid values are: 'norm', 'temp', 'ref'
    :return: name of the curve created.
    """
    if displayType not in ['norm', 'temp', 'ref']:
        cmds.error("{} is not a valid display type. Valid values are: ['norm', 'temp', 'ref']".format(displayType))
        return
    if not name:
        name = rigamajig2.maya.naming.getUniqueName("displayLine")

    displayLine = rigamajig2.maya.curve.createCurveFromTransform([point1, point2], name=name, degree=1)

    displayTypeDict = {'norm': 0, 'temp': 1, 'ref': 2}

    cmds.setAttr(displayLine + '.overrideEnabled', 1)
    cmds.setAttr(displayLine + '.overrideDisplayType', displayTypeDict[displayType])
    if parent:
        cmds.parent(displayLine, parent)

    # create some decompose matrix nodes
    mm1 = cmds.createNode('multMatrix', n=displayLine + "_1_mm")
    mm2 = cmds.createNode('multMatrix', n=displayLine + "_2_mm")
    dcmp1 = cmds.createNode('decomposeMatrix', n=displayLine + "_1_dcmp")
    dcmp2 = cmds.createNode('decomposeMatrix', n=displayLine + "_2_dcmp")

    # connect the attributes
    cmds.connectAttr(point1 + '.worldMatrix', mm1 + ".matrixIn[0]", f=True)
    cmds.connectAttr(displayLine + '.worldInverseMatrix', mm1 + ".matrixIn[1]", f=True)
    cmds.connectAttr(point2 + '.worldMatrix', mm2 + ".matrixIn[0]", f=True)
    cmds.connectAttr(displayLine + '.worldInverseMatrix', mm2 + ".matrixIn[1]", f=True)
    cmds.connectAttr(mm1 + '.matrixSum', dcmp1 + '.inputMatrix')
    cmds.connectAttr(mm2 + '.matrixSum', dcmp2 + '.inputMatrix')

    displayLineShape = cmds.listRelatives(displayLine, s=True) or []
    cmds.connectAttr(dcmp1 + '.outputTranslate', displayLineShape[0] + '.controlPoints[0]', f=True)
    cmds.connectAttr(dcmp2 + '.outputTranslate', displayLineShape[0] + '.controlPoints[1]', f=True)


def connectControlVisiblity(driverNode, driverAttr, controls):
    """
    connect to the control visiblity
    :param driverNode: name of the node to drive the control visibility
    :param driverAttr: name of the attribute on the node to drive the control visibility
    :param controls: list of the controls to drive their visibility of
    """
    controls = common.toList(controls)

    for control in controls:
        shapes = cmds.listRelatives(control, s=True) or []
        for shape in shapes:
            cmds.connectAttr("{}.{}".format(driverNode, driverAttr), "{}.{}".format(shape, 'v'))


@rigamajig2.maya.decorators.oneUndo
def setControlShape(control, shape, clearExisting=True):
    """
    Set the control shape
    :param control: control to change the shape of
    :param shape: name of the shape to set
    :param clearExisting: clear any existing shapes
    """
    if clearExisting:
        rigamajig2.maya.curve.wipeCurveShape(control)

    controlDataObj = rigamajig2.maya.data.curve_data.CurveData()
    controlDataObj.read(CONTROLSHAPES)
    if shape in controlDataObj.getData().keys():
        source = controlDataObj.applyData(shape, create=True)[0]
        rigamajig2.maya.curve.copyShape(source, control)
        cmds.delete(source)
    else:
        cmds.setAttr("{}.displayHandle".format(control), 1)


def translateShapes(shape, translation=(0, 0, 0), world=False):
    """
    Translate the shape
    :param shape: shape shape to transform
    :param translation: translate vector
    :param world: apply translation in worldspace.
    """
    shapes = cmds.listRelatives(shape, s=True) or []

    for shape in shapes:
        if world:
            cmds.move(translation[0], translation[1], translation[2],
                      rigamajig2.maya.curve.getCvs(shape),
                      relative=True, worldSpace=True)
        else:
            cmds.move(translation[0], translation[1], translation[2],
                      rigamajig2.maya.curve.getCvs(shape),
                      relative=True, objectSpace=True)


def rotateShapes(shape, rotation=(0, 0, 0)):
    """
    Rotate the shape
    :param shape: shape shape to transform
    :param rotation: rotate vector
    """
    shapes = cmds.listRelatives(shape, s=True) or []

    for shape in shapes:
        cmds.rotate(rotation[0], rotation[1], rotation[2],
                    rigamajig2.maya.curve.getCvs(shape),
                    relative=True, objectSpace=True)


def scaleShapes(shape, scale=(1, 1, 1)):
    """
    Scale the shape
    :param shape: shape shape to transform
    :param scale: scale vector
    """
    shapes = cmds.listRelatives(shape, s=True) or []

    for shape in shapes:
        cmds.scale(scale[0], scale[1], scale[2],
                   rigamajig2.maya.curve.getCvs(shape),
                   relative=True, objectSpace=True)


def setLineWidth(controls, lineWidth=1):
    """
    set the control line width
    :param controls: controls to set the line width of
    :param lineWidth: line weight to set on the controls
    :return:
    """
    controls = common.toList(controls)
    for control in controls:
        shapes = cmds.listRelatives(control, s=True) or []
        for shape in shapes:
            cmds.setAttr("{}.{}".format(shape, "lineWidth"), lineWidth)


# pylint:disable=too-many-arguments
def createGuide(name, side=None, shape="loc", type=None, parent=None, joint=False,
                position=None, rotation=None, size=1,
                hideAttrs=None, color='turquoise'):
    """
    Create a guide controler
    :param name: Name of the guide
    :param side: Optional - name of the side
    :param type: control type to tag as.
    :param shape: shape of the guide
    :param parent: Optional - Parent the guide in the control hierarchy
    :param bool joint: choose to show or hide the joint
    :param position: Optional - Point in world space to position the control
    :param rotation: Optional - Rotation in world space to rotate the control
    :param size: Optional - Size of the guide
    :param hideAttrs: Optional - list of attributes to lock and hide. Default is ['s', 'v']
    :param color: Optional - Color of the guide
    :return: Control created
    """
    if hideAttrs is None:
        hideAttrs = list()

    if position is None:
        position = [0, 0, 0]
    if rotation is None:
        rotation = [0, 0, 0]
    if hideAttrs is None:
        hideAttrs = ['sx', 'sy', 'sz', 'v']

    name = rigamajig2.maya.naming.getUniqueName(name, side=side)
    guide = cmds.createNode('joint', name=name + "_guide")

    # set the control shape
    if shape == "loc":
        loc = cmds.createNode('locator', p=guide, n="{}Shape".format(name))
        cmds.setAttr("{}.localScale".format(loc), size, size, size, type="double3")
    elif shape != "joint":
        setControlShape(guide, shape)
        scaleShapes(guide, (size, size, size))

    if not joint:
        cmds.setAttr("{}.drawStyle".format(guide), 2)
        hideAttrs.append('radius')
    else:
        rigamajig2.maya.joint.addJointOrientToChannelBox(guide)

    for attr in hideAttrs:
        if cmds.objExists("{}.{}".format(guide, attr)):
            rigamajig2.maya.attr.lockAndHide(guide, attr)

    if parent:
        cmds.parent(guide, parent)
    if position:
        cmds.xform(guide, ws=True, translation=position)
    if rotation:
        cmds.xform(guide, ws=True, rotation=rotation)
    if color:
        rigamajig2.maya.color.setOverrideColor(guide, color)

    meta.tag(guide, 'guide', type=type)

    return guide
