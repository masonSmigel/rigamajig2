"""
Controller functions
"""
import os
import maya.cmds as cmds
import rigamajig2.shared.common
import rigamajig2.shared.path
import rigamajig2.maya.naming
import rigamajig2.maya.hierarchy
import rigamajig2.maya.data.curve_data
import rigamajig2.maya.curve
import rigamajig2.maya.color
import rigamajig2.maya.transform
import rigamajig2.maya.meta
import rigamajig2.maya.shape
import rigamajig2.maya.attr
import rigamajig2.maya.utils

CONTROLSHAPES = rigamajig2.shared.path.clean_path(os.path.join(os.path.dirname(__file__), "controlShapes.data"))

CONTROLTAG = 'control'


def create(name, side=None, shape='circle', hierarchy=['trsBuffer'], parent=None, position=[0, 0, 0],
           rotation=[0, 0, 0], size=1, hideAttrs=['v'], color='blue', type=None, rotateOrder='xyz',
           trasformType='transform', shapeAim='y'):
    """
    Create a control. It will also create a hierarchy above the control based on the hierarchy list.

    :param name: Name of the control.
    :type name: str

    :param side: Optional name of the side
    :type side: str

    :param shape: Shape of the control.
    :type shape: str

    :param hierarchy: List of suffixes to add to the hierarchy to add above the control.
    :type hierarchy: list | tuple

    :param parent: Optional- Parent the control under this node in the hierarchy
    :type parent: str

    :param position: Optional- Point in world space to position the control.
    :type position: list | tuple

    :param rotation: Optional- Rotation in world space to rotate the control.
    :type rotation: list | tuple

    :param size: Optional- Size of the control
    :type size: int | float

    :param hideAttrs: Optional- list of attributes to lock and hide. Default is ['v']
    :type hideAttrs: list

    :param color: Optional- Color of the control
    :type color: str | int

    :param type: Optional- Specifiy a control type.
    :type type: str

    :param rotateOrder: Specify a rotation order. Default is 'xyz'
    :type rotateOrder: str

    :param trasformType: Type of transform to use as a control. "transform", "joint"

    :param shapeAim: Set the direction to aim the control

    :return: list of hierarchy created above the control plus the control:
    :rtype: list | tuple
    """
    if side:
        name = rigamajig2.maya.naming.getUniqueName("{}_{}".format(name, side))
    else:
        name = rigamajig2.maya.naming.getUniqueName(name)
    control = cmds.createNode(trasformType, name=name)
    topNode = control

    setControlShape(control, shape)

    hierarchyList = list()
    if hierarchy:
        for suffix in hierarchy:
            node = rigamajig2.maya.naming.getUniqueName(control + "_" + suffix)
            hierarchyList.append(node)
        rigamajig2.maya.hierarchy.create(control, hierarchy=hierarchyList)
        topNode = hierarchyList[0]

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
    elif shapeAim == 'z':
        rotateVector = (90, 0, 0)
    else:
        rotateVector = (0, 0, 0)
    rotateShapes(control, rotateVector)

    tagAsControl(control, type=type)

    return hierarchyList + [control]


def createAtObject(name, side=None, shape='circle', hierarchy=['trsBuffer'], parent=None, xformObj=None, size=1,
                   hideAttrs=['v'], color='blue', type=None, rotateOrder='xyz', trasformType='transform', shapeAim='y'):
    """
    Wrapper to create a control at the position of a node.
    :param name: Name of the control.
    :type name: str

    :param side: Optional name of the side
    :type side: str

    :param shape: Shape of the control.
    :type shape: str

    :param hierarchy: List of suffixes to add to the hierarchy to add above the control.
    :type hierarchy: list | tuple

    :param parent: Optional- Parent the control under this node in the hierarchy
    :type parent: str

    :param xformObj: object to snap the control to.
    :type xformObj: str | list

    :param size: Optional- Size of the control
    :type size: int | float

    :param hideAttrs: Optional- list of attributes to lock and hide. Default is ['v']
    :type hideAttrs: list

    :param color: Optional- Color of the control
    :type color: str | int

    :param type: Optional- Specifiy a control type.
    :type type: str

    :param rotateOrder: Specify a rotation order. Default is 'xyz'
    :type rotateOrder: str

    :param trasformType: Type of transform to use as a control. "transform", "joint"

    :param shapeAim: Set the direction to aim the control

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

    xformObj = rigamajig2.shared.common.getFirstIndex(xformObj)

    position = cmds.xform(xformObj, q=True, ws=True, translation=True)
    controlHierarchy = create(name=name, side=side, shape=shape, hierarchy=hierarchy, parent=parent, position=position,
                              size=size, rotation=[0, 0, 0], hideAttrs=hideAttrs, color=color, type=type,
                              rotateOrder=rotateOrder, trasformType=trasformType, shapeAim=shapeAim)
    rigamajig2.maya.transform.matchRotate(xformObj, controlHierarchy[0])
    return controlHierarchy


def getAvailableControlShapes():
    """
    Get a list of available control shapes
    """
    controlData = rigamajig2.maya.data.curve_data.CurveData()
    controlData.read(CONTROLSHAPES)
    control_data = controlData.getData()
    return control_data.keys()


def tagAsControl(control, type=None):
    """
    Tag the object as a control
    :param control:
    :param type: Add a special type
    :return:
    """
    rigamajig2.maya.meta.tag(control, CONTROLTAG, type=type)


def untagAsControl(control):
    """
    untag specified controls as a control
    :param control: control to remove tag from
    """
    rigamajig2.maya.meta.untag(control, CONTROLTAG)


def getControls(namespace=None):
    """
    Get a list of all the controls in a scene.
    :param namespace: Get controls found within a specific namespace
    :type namespace: str
    :return:
    """
    return rigamajig2.maya.meta.getTagged(CONTROLTAG, namespace=namespace)


def createDisplayLine(point1, point2, name=None, parent=None, displayType='ref'):
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
    controls = rigamajig2.shared.common.toList(controls)

    for control in controls:
        shapes = cmds.listRelatives(control, s=True) or []
        for shape in shapes:
            cmds.connectAttr("{}.{}".format(driverNode, driverAttr), "{}.{}".format(shape, 'v'))


@rigamajig2.maya.utils.oneUndo
def setControlShape(control, shape, clearExisting=True):
    """
    Set the control shape
    :param control: control to change the shape of
    :param shape: name of the shape to set
    :param clearExisting: clear any existing shapes
    """
    if clearExisting:
        rigamajig2.maya.curve.wipeCurveShape(control)

    controlData = rigamajig2.maya.data.curve_data.CurveData()
    controlData.read(CONTROLSHAPES)
    control_data = controlData.getData()
    if shape in control_data.keys():
        source = controlData.applyData(shape, create=True)[0]
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
    controls = rigamajig2.shared.common.toList(controls)
    for control in controls:
        shapes = cmds.listRelatives(control, s=True) or []
        for shape in shapes:
            cmds.setAttr("{}.{}".format(shape, "lineWidth"), lineWidth)


def createGuide(name, side=None, shape="loc", type=None, parent=None, position=[0, 0, 0], rotation=[0, 0, 0], size=1,
                hideAttrs=['sx', 'sy', 'sz', 'v'], color='turquoise'):
    """
    Create a guide controler
    :param name: Name of the guide
    :param side: Optional - name of the side
    :param type: control type to tag as.
    :param shape: shape of the guide
    :param parent: Optional - Parent the guide in the control hierarchy
    :param position: Optional - Point in world space to position the control
    :param rotation: Optional - Rotation in world space to rotate the control
    :param size: Optional - Size of the guide
    :param hideAttrs: Optional - list of attributes to lock and hide. Default is ['s', 'v']
    :param color: Optional - Color of the guide
    :return: Control created
    """
    name = rigamajig2.maya.naming.getUniqueName(name, side=side)
    guide = cmds.createNode('joint', name=name)

    # set the control shape
    if shape == "loc":
        loc = cmds.createNode('locator', p=guide, n="{}Shape".format(name))
        cmds.setAttr("{}.localScale".format(loc), size, size, size, type="double3")
    else:
        setControlShape(guide, shape)
        scaleShapes(guide, (size, size, size))

    cmds.setAttr("{}.drawStyle".format(guide), 2)
    hideAttrs.append('radius')

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

    rigamajig2.maya.meta.tag(guide, 'guide', type=type)

    return guide
