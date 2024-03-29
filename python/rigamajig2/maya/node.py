"""
Functions to quickly create utility nodes and setup their attribtues quickly
"""
import logging

import maya.cmds as cmds

import rigamajig2.maya.attr as attr
import rigamajig2.shared.common as common

logger = logging.getLogger(__name__)


def setConnection(plug, value):
    """
    Set a connection to a given value.

    Depending on the type of the value it will either connect the attribute or set the value

    :param plug: plug to be connected to
    :param value: value to set the plug to
    :return: None
    """
    if isinstance(value, (str, common.UNICODE)):
        try:
            cmds.connectAttr(value, plug)
        except:
            raise RuntimeError("The plug {} could not be set to {}".format(plug, value))
    else:
        cmds.setAttr(plug, value)


def setCompoundConnection(plug, value):
    """
    Set a compound connection to a given value.

    Depending on the type of the value it will either connect the attribute or set the value

    :param plug: plug to be connected to
    :param value: value to set the plug to
    :return: None
    """
    if isinstance(value, (str, common.UNICODE)):
        if attr.isCompound(value):
            cmds.connectAttr(value, plug)
        else:
            childAttrs = attr.getCompoundChildren(plug)
            setConnection(childAttrs[0], value)
    elif isinstance(value, (list, tuple)):
        childAttrs = attr.getCompoundChildren(plug)
        for value, childAttr in zip(value, childAttrs):
            setConnection(childAttr, value)
    elif isinstance(value, (float, int)):
        value = [value, 0, 0]
        cmds.setAttr(plug, *value)


def connectOutput(source, destination, f=True):
    """
    Connect a source plug to a destination plug.
    This function checks to ensure the attribute is connected to any compound children if they exist.

    :param source: source plug to connect
    :param destination: desitnation plug to be connectected to
    :param f: force the connection
    :return:
    """
    if not cmds.objExists(destination) and attr.isAttr(destination):
        logger.error(
            "Destination: {} does not exist or is not a valid attribute".format(
                destination
            )
        )
        return

    if attr.isCompound(destination):
        if attr.isCompound(source):
            cmds.connectAttr(source, destination, f=f)
        else:
            childAttrs = attr.getCompoundChildren(source)
            cmds.connectAttr(childAttrs[0], destination, f=f)
    else:
        if attr.isCompound(source):
            childAttrs = attr.getCompoundChildren(source)
            cmds.connectAttr(childAttrs[0], destination, f=f)
        else:
            cmds.connectAttr(source, destination, f=f)


def addDoubleLinear(input1=None, input2=None, output=None, name=None):
    """
    Create an addDoubleLinear node:

    :param str float input1: first input. Can be a value or a plug (as a string)
    :param str float input2: second input. Can be a value or a plug (as a string)
    :param str name: Optional - give the created node a name. (a suffix is added from the common module)
    :param str output: Node plug to connect the output of the node to.
    :return: name of the node created
    :rtype: str
    """
    if name:
        node = cmds.createNode(
            "addDoubleLinear", name=name + "_" + common.ADDDOUBLELINEAR
        )
    else:
        node = cmds.createNode("addDoubleLinear")

    if input1:
        setConnection(node + "." + "input1", input1)
    if input2:
        setConnection(node + "." + "input2", input2)
    if output:
        connectOutput(node + ".output", output)

    return node


def multDoubleLinear(input1=None, input2=None, output=None, name=None):
    """
    Create an MultDoubleLinear node:

    :param str float input1: first input. Can be a value or a plug (as a string)
    :param str float input2: second input. Can be a value or a plug (as a string)
    :param str name: Optional - give the created node a name. (a suffix is added from the common module)
    :param str output: Node plug to connect the output of the node to.
    :return: name of the node created
    :rtype: str
    """
    if name:
        node = cmds.createNode(
            "multDoubleLinear", name=name + "_" + common.MULTDOUBLELINEAR
        )
    else:
        node = cmds.createNode("multDoubleLinear")

    if input1:
        setConnection(node + "." + "input1", input1)
    if input2:
        setConnection(node + "." + "input2", input2)
    if output:
        connectOutput(node + ".output", output)

    return node


def multiplyDivide(input1=None, input2=None, operation="mult", output=None, name=None):
    """
    Create a MultiplyDivide node. You can either pass a compound attribute,

    :param  list str float input1: first input. Can be a list of 3 values or a multi-plug (as a string)
    :param list str float input2: second input. Can be a list of 3 values or a multi-plug (as a string)
    :param str  operation: Set the operation to perform. Valid values are: 'mult', 'div' and 'pow'. Default: 'mult'
    :param str name: Optional - give the created node a name. (a suffix is added from the common module)
    :param str output:  Node plug to connect the output of the node to.
    :return: name of the node created
    :rtype: str
    """
    if name:
        node = cmds.createNode(
            "multiplyDivide", name=name + "_" + common.MULTIPLYDIVIDE
        )
    else:
        node = cmds.createNode("multiplyDivide")

    operationDict = {"mult": 1, "div": 2, "pow": 3}
    cmds.setAttr(node + ".operation", operationDict[operation])

    if input1:
        setCompoundConnection(node + "." + "input1", input1)
    if input2:
        setCompoundConnection(node + "." + "input2", input2)
    if output:
        connectOutput(node + ".output", output)

    return node


def unitConversion(input=None, output=None, conversionFactor=None, name=None):
    """
    Create a unit conversion node

    :param int float str input: input node
    :param int float str output: output node
    :param float conversionFactor: conversion factor
    :param str name: Optional - give the created node a name. (a suffix is added from the common module)
    :return: name of the node created
    """
    if name:
        node = cmds.createNode(
            "unitConversion", name=name + "_" + common.UNITCONVERSION
        )
    else:
        node = cmds.createNode("multiplyDivide")

    if input:
        setConnection(node + "." + "input", input)
    if conversionFactor:
        setConnection(node + "." + "conversionFactor", conversionFactor)
    if output:
        # use the regular old connect attribute for this since it can be super flexible and doesnt need checks
        cmds.connectAttr(node + ".output", output)

    return node


def plusMinusAverage1D(inputs, operation="sum", output=None, name=None):
    """
    Create a PlusMinusAverage node using the input 1D connections.

    :param list inputs: list of inputs to perform the opperation on
    :param str operation: Set the operation to perform. Valid values are: 'sum', 'sub' and 'ave'. Default: 'sum'
    :param str output:  Node plug to connect the output of the node to.
    :param str name: Optional - give the created node a name. (a suffix is added from the common module)
    :return: name of the node created. (use node.output1D)
    :rtype: str
    """
    if name:
        node = cmds.createNode(
            "plusMinusAverage", name=name + "_" + common.PLUSMINUSAVERAGE
        )
    else:
        node = cmds.createNode("plusMinusAverage")

    operationDict = {"sum": 1, "sub": 2, "ave": 3}
    cmds.setAttr(node + ".operation", operationDict[operation])

    for index, i in enumerate(inputs):
        setConnection(node + ".input1D[{}]".format(index), i)

    if output:
        connectOutput(node + ".output1D", output)

    return node


def plusMinusAverage3D(inputs, operation="sum", output=None, name=None):
    """
    Create a PlusMinusAverage node using the input 3D connections.

    :param list inputs: list of inputs to perform the opperation on. Can be a list of 3 values or a multi-plug (as a string)
    :param str operation: Set the operation to perform. Valid values are: 'sum', 'sub' and 'ave'. Default: 'sum'
    :param str output:  Node plug to connect the output of the node to.
    :param str name: Optional - give the created node a name. (a suffix is added from the common module)
    :return: name of the node created. (use node.output1D)
    :rtype: str
    """
    if name:
        node = cmds.createNode(
            "plusMinusAverage", name=name + "_" + common.PLUSMINUSAVERAGE
        )
    else:
        node = cmds.createNode("plusMinusAverage")

    operationDict = {"sum": 1, "sub": 2, "ave": 3}
    cmds.setAttr(node + ".operation", operationDict[operation])

    for index, i in enumerate(inputs):
        setCompoundConnection(node + ".input3D[{}]".format(index), i)

    if output:
        connectOutput(node + ".output3D", output)

    return node


def choice(selector=None, choices=None, output=None, name=None):
    """
    Create a choice node

    :param str float selector: selctor value. Can be a list of 3 values or a plug (as a string)
    :param list tuple choices: list of values to choose between
    :param str output: Node plug to connect the output of the node to.
    :param str name: Optional - give the created node a name. (a suffix is added from the common module)
    :return: name of the node created. (use node.output)
    :rtype: str
    """
    choices = choices or list()

    if name:
        node = cmds.createNode("choice", name=name + "_" + common.CHOICE)
    else:
        node = cmds.createNode("choice")

    if selector:
        setConnection(node + ".selector", selector)

    for i, choice in enumerate(choices):
        if isinstance(choice, str):
            cmds.connectAttr(choice, node + ".input[{}]".format(i))
        else:
            cmds.setAttr(node + ".input[{}]".format(i), choice)

    if output:
        connectOutput(node + ".output", output)

    return node


def condition(
    firstTerm=None,
    secondTerm=None,
    ifTrue=None,
    ifFalse=None,
    operation="==",
    output=None,
    name=None,
):
    """
    Create a condition Node.

    :param str float firstTerm: first term. Can be a list of 3 values or a multi-plug (as a string)
    :param str float secondTerm: first term. Can be a list of 3 values or a multi-plug (as a string)
    :param str float list ifTrue: result to return if statement is true. Can be a list of 3 values or a compound plug (as a string)
    :param str float list ifFalse:result to return if statement is False. Can be a list of 3 values or a compound plug (as a string)
    :param str  operation: operation to evaluate. valid values are: '==', '!=', '>', '>=', '<', '<='
    :param str output: Node plug to connect the output of the node to.
    :param str name: Optional - give the created node a name. (a suffix is added from the common module)
    :return: name of the node created. (use node.outColor)
    :rtype: str
    """
    if name:
        node = cmds.createNode("condition", name=name + "_" + common.CONDITION)
    else:
        node = cmds.createNode("condition")

    operationDict = {"==": 0, "!=": 1, ">": 2, ">=": 3, "<": 4, "<=": 5}
    cmds.setAttr(node + ".operation", operationDict[operation])

    if firstTerm:
        setConnection(
            node + ".firstTerm",
            firstTerm,
        )
    if secondTerm:
        setConnection(node + ".secondTerm", secondTerm)
    if ifTrue:
        setCompoundConnection(node + ".colorIfTrue", ifTrue)
    if ifFalse:
        setCompoundConnection(node + ".colorIfFalse", ifFalse)
    if output:
        connectOutput(node + ".outColor", output)

    return node


def reverse(input1=None, output=None, name=None):
    """
    Create a reverse node

    :param str float list input1: input. Can be a list of 3 values or a multi-plug (as a string)
    :param str output: Node plug to connect the output of the node to.
    :param str name: Optional - give the created node a name. (a suffix is added from the common module)
    :return: name of the node created.
    :rtype: str
    """
    if name:
        node = cmds.createNode("reverse", name=name + "_" + common.REVERSE)
    else:
        node = cmds.createNode("reverse")

    if input1:
        setCompoundConnection(node + ".input", input1)

    if output:
        connectOutput(node + ".output", output)

    return node


def pairBlend(
    input1=None,
    input2=None,
    weight=None,
    output=None,
    outputRot=True,
    outputPos=True,
    rotInterp="euler",
    name=None,
):
    """
    Create a pair blend node.

    :param str float list input1: input transform node.  (use a node name. not a plug)
    :param str float list input2: input transform node.  (use a node name. not a plug)
    :param float int str weight: weight of the blend. 1 = input2; 0 = input1.
    :param str output: node to connect output to. (use a node name. not a plug)
    :param bool outputRot: output the rotation to the output node
    :param bool outputPos: output the translation to the output node
    :param str rotInterp: Method of rotation interperlation. Valid values are: 'euler', 'quat'. Default 'euler'
    :param str name: Optional - give the created node a name. (a suffix is added from the common module)
    :return: name of the node created.
    :rtype: str
    """
    if name:
        node = cmds.createNode("pairBlend", name=name + "_" + common.PAIRBLEND)
    else:
        node = cmds.createNode("pairBlend")

    if weight:
        setConnection(node + ".weight", weight)
    if input1:
        setCompoundConnection(node + ".inTranslate1", input1 + ".t")
        setCompoundConnection(node + ".inRotate1", input1 + ".r")
    if input2:
        setCompoundConnection(node + ".inTranslate2", input2 + ".t")
        setCompoundConnection(node + ".inRotate2", input2 + ".r")
    if output:
        if outputPos:
            connectOutput(node + ".outTranslate", output + ".t")
        if outputRot:
            connectOutput(node + ".outRotate", output + ".r")

    rotInterpDict = {"euler": 0, "quat": 1}
    cmds.setAttr(node + ".rotInterpolation", rotInterpDict[rotInterp])

    return name


def blendColors(input1=None, input2=None, weight=None, output=None, name=None):
    """
    Create a blend colors node.

    :param str float list input1: input. Can be a list of 3 values or a multi-plug (as a string)
    :param str float list input2: input. Can be a list of 3 values or a multi-plug (as a string)
    :param float int str weight: 1 = input2; 0 = input1.
    :param str output: Node plug to connect the output of the node to.
    :param str name: Optional - give the created node a name. (a suffix is added from the common module)
    :return: name of the node created.
    :rtype: str
    """
    if name:
        node = cmds.createNode("blendColors", name=name + "_" + common.BLENDCOLOR)
    else:
        node = cmds.createNode("blendColors")

    if weight:
        setConnection(node + ".blender", weight)
    if input1:
        setCompoundConnection(node + ".color2", input1)
    if input2:
        setCompoundConnection(node + ".color1", input2)
    if output:
        connectOutput(node + ".output", output)
    return node


def blendTwoAttrs(input1=None, input2=None, weight=None, output=None, name=None):
    """
    Create a blend two attrs node.

    :param str float list input1: input. Can be a list of 3 values or a multi-plug (as a string)
    :param str float list input2: input. Can be a list of 3 values or a multi-plug (as a string)
    :param float int str weight: 1 = input2; 0 = input1.
    :param str output: Node plug to connect the output of the node to.
    :param str name: Optional - give the created node a name. (a suffix is added from the common module)
    :return: name of the node created.
    :rtype: str
    """
    if name:
        node = cmds.createNode("blendTwoAttr", name=name + "_" + common.BLENDTWOATTR)
    else:
        node = cmds.createNode("blendTwoAttr")

    if weight:
        setConnection(node + ".attributesBlender", weight)

    if input1:
        setConnection(node + ".input[0]", input1)
    if input2:
        setConnection(node + ".input[1]", input2)
    if output:
        connectOutput(node + ".output", output)
    return node


def distance(input1, input2, output=None, name=None):
    """
    Create a distance between node.

    :param str list input1: input transform node.  (use a node name. not a plug)
    :param str list input2: input transform node.  (use a node name. not a plug)
    :param str output: Node plug to connect the output of the node to.
    :param st name: Optional - give the created node a name. (a suffix is added from the common module)
    :return: name of the node created.
    :rtype: str
    """
    if name:
        node = cmds.createNode(
            "distanceBetween", name=name + "_" + common.DISTANCEBETWEEN
        )
    else:
        node = cmds.createNode("distanceBetween")

    if "." not in input1:
        dcmp1 = cmds.createNode(
            "decomposeMatrix", n=input1 + "_dist_" + common.DECOMPOSEMATRIX
        )
        cmds.connectAttr(input1 + ".worldMatrix", dcmp1 + ".inputMatrix")
        cmds.connectAttr(dcmp1 + ".outputTranslate", node + ".point1")
    else:
        cmds.connectAttr(input1, node + ".point1")
    if "." not in input2:
        dcmp2 = cmds.createNode(
            "decomposeMatrix", n=input2 + "_dist_" + common.DECOMPOSEMATRIX
        )
        cmds.connectAttr(input2 + ".worldMatrix", dcmp2 + ".inputMatrix")
        cmds.connectAttr(dcmp2 + ".outputTranslate", node + ".point2")
    else:
        cmds.connectAttr(input2, node + ".point2")

    if output:
        connectOutput(node + ".distance", output)

    return node


def multMatrix(
    inputs=None, outputs=None, translate=False, rotate=False, scale=False, name=None
):
    """
    create a mult matrix node.

    :param list inputs: list of input matrix's
    :param str list outputs: list of nodes to connect the output of the multMatrix to.
    :param bool translate: Connect to the translation
    :param bool rotate: Connect to the rotation
    :param bool scale: Connect to the scale
    :param str name: Optional - give the created node a name. (a suffix is added from the common module)
    :return: name of the node created
    :rtype: str
    """
    if name:
        node = cmds.createNode("multMatrix", name=name + "_" + common.MULTMATRIX)
    else:
        node = cmds.createNode("multMatrix")

    if inputs:
        for i, input in enumerate(inputs):
            if isinstance(input, (list, tuple)):
                cmds.setAttr(node + ".matrixIn[{}]".format(i), input, type="matrix")
            else:
                cmds.connectAttr(input, node + ".matrixIn[{}]".format(i))

    if outputs:
        outputs = common.toList(outputs)
        if name:
            dcmp = cmds.createNode(
                "decomposeMatrix", n=name + "_mm_" + common.DECOMPOSEMATRIX
            )
        else:
            dcmp = cmds.createNode("decomposeMatrix")
        cmds.connectAttr(node + ".matrixSum", dcmp + ".inputMatrix")
        for output in outputs:
            if translate:
                cmds.connectAttr(
                    dcmp + ".outputTranslate", output + ".translate", f=True
                )
            if rotate:
                cmds.connectAttr(dcmp + ".outputRotate", output + ".rotate", f=True)
            if scale:
                cmds.connectAttr(dcmp + ".outputScale", output + ".scale", f=True)

        return node, dcmp
    return node


def decomposeMatrix(
    matrix=None, outputs=None, translate=True, rotate=True, scale=False, name=None
):
    """
    Creates a decompose matrix node.

    :param str matrix: matrix attribute to decompose
    :param str list outputs: node to output decompose matrix to.
    :param bool translate: Connect to the translation
    :param bool rotate: Connect to the rotation
    :param bool scale: Connect to the scale
    :param str name: Optional - give the created node a name. (a suffix is added from the common module)
    :return: name of the node created
    :rtype: str
    """
    if name:
        node = cmds.createNode(
            "decomposeMatrix", name=name + "_" + common.DECOMPOSEMATRIX
        )
    else:
        node = cmds.createNode("decomposeMatrix")
    if matrix:
        cmds.connectAttr(matrix, node + ".inputMatrix")

    if outputs:
        outputs = common.toList(outputs)
        for output in outputs:
            if translate:
                cmds.connectAttr(
                    node + ".outputTranslate", output + ".translate", f=True
                )
            if rotate:
                cmds.connectAttr(node + ".outputRotate", output + ".rotate", f=True)
            if scale:
                cmds.connectAttr(node + ".outputScale", output + ".scale", f=True)

    return node


# pylint: disable = too-many-arguments
def composeMatrix(
    inputTranslate=None,
    inputRotate=None,
    inputScale=None,
    inputQuat=None,
    rotateOrder="xyz",
    eulerRotation=True,
    outputs=None,
    translate=False,
    rotate=False,
    scale=False,
    name=None,
):
    """
    Creates a composeMatrix Node

    :param list str inputTranslate: input translate values
    :param list str inputRotate: input rotate values
    :param list str inputScale: input scale calues
    :param list str inputQuat: input quat values
    :param str rotateOrder: Rotation order to set
    :param bool eulerRotation: use Euler rotation
    :param str outputs: Optional- connect the node to a given output
    :param bool translate: connect the output tranlation
    :param bool rotate: connect the output rotation
    :param bool scale: connect the output scale
    :param str name:  Optional - give the created node a name. (a suffix is added from the common module)
    :return: name of the node created
    """
    inputTranslate = inputTranslate or [0, 0, 0]
    inputRotate = inputRotate or [0, 0, 0]
    inputScale = inputScale or [1, 1, 1]
    inputQuat = inputQuat or [0, 0, 0, 0]

    if name:
        node = cmds.createNode("composeMatrix", name=name + "_" + common.COMPOSEMATRIX)
    else:
        node = cmds.createNode("composeMatrix")

    setCompoundConnection(node + ".inputTranslate", inputTranslate)
    setCompoundConnection(node + ".inputRotate", inputRotate)
    setCompoundConnection(node + ".inputScale", inputScale)
    # Set the quaternion values
    setConnection(node + ".inputQuatX", inputQuat[0])
    setConnection(node + ".inputQuatY", inputQuat[1])
    setConnection(node + ".inputQuatZ", inputQuat[2])
    setConnection(node + ".inputQuatW", inputQuat[3])

    import rigamajig2.maya.axis

    cmds.setAttr(
        node + ".inputRotateOrder", rigamajig2.maya.axis.getRotateOrder(rotateOrder)
    )
    cmds.setAttr(node + ".useEulerRotation", eulerRotation)

    if outputs:
        outputs = common.toList(outputs)
        for output in outputs:
            if translate:
                cmds.connectAttr(
                    node + ".outputTranslate", output + ".translate", f=True
                )
            if rotate:
                cmds.connectAttr(node + ".outputRotate", output + ".rotate", f=True)
            if scale:
                cmds.connectAttr(node + ".outputScale", output + ".scale", f=True)

    return node


def pickMatrix(
    inputMatrix=None,
    outputs=None,
    translate=True,
    rotate=True,
    scale=True,
    shear=True,
    name=None,
):
    """
    Create a pick matrix node

    :param list str inputMatrix: input matrix to use
    :param str outputs:  Optional- connect the node to a given plug
    :param bool translate: use translate in the picked matrix
    :param bool rotate: use rotate in the picked matrix
    :param bool scale: use scale in the picked matrix
    :param bool shear: use shear in the picked matrix
    :param str name: Optional - give the created node a name. (a suffix is added from the common module)
    :return: name of the node created
    :rtype: str
    """

    if name:
        node = cmds.createNode("pickMatrix", name=name + "_" + common.PICKMATRIX)
    else:
        node = cmds.createNode("pickMatrix")

    if inputMatrix:
        cmds.connectAttr(inputMatrix, node + ".inputMatrix".format())

    cmds.setAttr(node + ".useTranslate", translate)
    cmds.setAttr(node + ".useRotate", rotate)
    cmds.setAttr(node + ".useScale", scale)
    cmds.setAttr(node + ".useShear", shear)

    if outputs:
        outputs = common.toList(outputs)
        for output in outputs:
            cmds.connectAttr(node + ".outputMatrix", output)

    return node


def clamp(input, inMin=None, inMax=None, output=None, name=None):
    """
    Creates a clamp node.

    :param str float list input:  Input. Can be a list of 3 values or a multi-plug (as a string)
    :param str float list inMin: Minimum value
    :param str float list inMax:  Maximum value
    :param str output: Node plug to connect the output of the node to.
    :param str name: Optional - give the created node a name. (a suffix is added from the common module)
    :return: name of the node created
    :rtype: str
    """
    if name:
        node = cmds.createNode("clamp", name=name + "_" + common.CLAMP)
    else:
        node = cmds.createNode("clamp")

    setCompoundConnection(node + ".input", input)

    if inMin:
        setCompoundConnection(node + ".min", inMin)
    if inMax:
        setCompoundConnection(node + ".max", inMax)

    if output:
        connectOutput(node + ".output", output)

    return node


def remapValue(
    input,
    inMin=None,
    inMax=None,
    outMin=None,
    outMax=None,
    interp="linear",
    output=None,
    name=None,
):
    """
    Creates a remap value node.

    :param str float list input:  Input. Can be a list of 3 values or a multi-plug (as a string)
    :param str float inMin: Minimum value
    :param str float inMax:  Maximum value
    :param str float outMin: Minimum value to output
    :param str float outMax: Maximum value to output
    :param str interp: Sets the interpolation. Valid values are: 'linear', 'slow', 'fast', 'smooth'. Default 'linear'
    :param str output: Node plug to connect the output of the node to.
    :param str name: Optional - give the created node a name. (a suffix is added from the common module)
    :return: name of the node created
    :rtype: str
    """
    if name:
        node = cmds.createNode("remapValue", name=name + "_" + common.REMAP)
    else:
        node = cmds.createNode("remapValue")

    setConnection(node + ".inputValue", input)

    # For all interperlation presets each list represents [position, value, interperlation]
    linearDict = {"0": [0.0, 0.0, 1], "1": [1.0, 1.0, 1]}
    fastDict = {
        "0": [0.0, 0.0, 3],
        "1": [0.5, 0.3, 3],
        "2": [0.95, 0.92, 3],
        "3": [1.0, 1.0, 3],
    }
    slowDict = {
        "0": [0.0, 0.0, 3],
        "1": [0.04, 0.05, 3],
        "2": [0.5, 0.7, 3],
        "3": [1.0, 1.0, 3],
    }
    smoothDict = {"0": [0.0, 0.0, 2], "1": [1.0, 1.0, 2]}

    interpDict = linearDict
    if interp == "fast":
        interpDict = fastDict
    if interp == "slow":
        interpDict = slowDict
    if interp == "smooth":
        interpDict = smoothDict

    for i in interpDict.keys():
        cmds.setAttr(node + ".value[{}].value_Position".format(i), interpDict[i][0])
        cmds.setAttr(node + ".value[{}].value_FloatValue".format(i), interpDict[i][1])
        cmds.setAttr(node + ".value[{}].value_Interp".format(i), interpDict[i][2])

    if inMin is not None:
        setConnection(node + ".inputMin", inMin)
    if inMax is not None:
        setConnection(node + ".inputMax", inMax)
    if outMin is not None:
        setConnection(node + ".outputMin", outMin)
    if outMax is not None:
        setConnection(node + ".outputMax", outMax)

    if output:
        connectOutput(node + ".outValue", output)

    return node


def vectorProduct(
    input1=None, input2=None, output=None, operation="dot", normalize=False, name=None
):
    """
    Create a vector product node

    :param str float list input1: input. Can be a list of 3 values or a multi-plug (as a string)
    :param str float list input2: input. Can be a list of 3 values or a multi-plug (as a string)
    :param str operation: Set the opperation to perform. Valid Values are: 'dot' , 'cross', 'none'. Default = 'dot'
    :param bool normalize: normalize the output
    :param str output: Node plug to connect the output of the node to.
    :param str name: Optional - give the created node a name. (a suffix is added from the common module)
    :return: name of the node created.
    :rtype: str
    """
    if name:
        node = cmds.createNode("vectorProduct", name=name + "_" + common.VECTORPRODUCT)
    else:
        node = cmds.createNode("vectorProduct")

    if input1:
        setCompoundConnection(node + ".input1", input1)
    if input2:
        setCompoundConnection(node + ".input2", input2)

    operationDict = {"none": 0, "dot": 1, "cross": 2}
    cmds.setAttr(node + ".operation", operationDict[operation])

    if normalize:
        cmds.setAttr(node + ".normalizeOutput", 1)
    if output:
        connectOutput(node + ".output", output)

    return node


def sin(input, output=None, name=None):
    """
    Create a simple DG graph for sine fuctions.

    :param str float input: input connection or value
    :param str output: Node plug to connect the output of the node to.
    :param str name: name of the nodes created
    :return: attribute with the output of the sin operation
    """
    if name:
        mdl = cmds.createNode(
            "multDoubleLinear", name=name + "_sin_" + common.MULTDOUBLELINEAR
        )
        quat = cmds.createNode("eulerToQuat", name=name + "_sin_" + common.EULERTOQUAT)
    else:
        mdl = cmds.createNode("multDoubleLinear")
        quat = cmds.createNode("eulerToQuat")

    setConnection(mdl + ".input1", 2 * 57.2958)  # convert to degrees
    setConnection(mdl + ".input2", input)
    cmds.connectAttr(mdl + ".output", quat + ".inputRotateX")

    if output:
        connectOutput(quat + ".outputQuatX", output)

    return quat + ".outputQuatX"


def cos(input, output=None, name=None):
    """
    Create a simple DG graph for cos fuctions.

    :param input: input connection or value
    :param output: Node plug to connect the output of the node to.
    :param name: name of the nodes created
    :return: attribute with the output of the sin operation
    :rtype: str
    """
    if name:
        mdl = cmds.createNode(
            "multDoubleLinear", name=name + "_cos_" + common.MULTDOUBLELINEAR
        )
        quat = cmds.createNode("eulerToQuat", name=name + "_cos_" + common.EULERTOQUAT)
    else:
        mdl = cmds.createNode("multDoubleLinear")
        quat = cmds.createNode("eulerToQuat")

    setConnection(mdl + ".input1", 2 * 57.2958)  # convert to degrees
    setConnection(mdl + ".input2", input)
    cmds.connectAttr(mdl + ".output", quat + ".inputRotateX")

    if output:
        connectOutput(quat + ".outputQuatW", output)

    return quat + ".outputQuatW"


def tan(input, output=None, name=None):
    """
    Create a simple DG graph for tan fuctions.

    :param str float input: input connection or value
    :param str output: Node plug to connect the output of the node to.
    :param str name: name of the nodes created
    :return: attribute with the output of the sin operation
    :rtype: str
    """
    halfPi = 3.14159265359 * 0.5
    if name:
        adl = addDoubleLinear(input, halfPi * -1, name=name + "_tan")
        opp = sin(input, name=name + "_opp_tan")
        adj = sin(str(adl + ".output"), name=name + "_adj_tan")
        div = multiplyDivide(str(opp), str(adj), operation="div", name=name + "opp_adj")

    else:
        adl = addDoubleLinear(input, halfPi * -1)
        opp = sin(input)
        adj = sin(str(adl + ".output"))
        div = multiplyDivide(str(opp), str(adj), operation="div")

    if output:
        cmds.connectAttr(div + ".outputX", output)
    return div + ".outputX"
