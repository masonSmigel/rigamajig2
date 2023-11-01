"""
Constraint functions
"""
import maya.api.OpenMaya as om2
from maya import cmds as cmds

import rigamajig2.maya.mesh as mesh
import rigamajig2.maya.meta as meta
import rigamajig2.maya.naming as naming
import rigamajig2.maya.node as node
import rigamajig2.maya.transform as transform
import rigamajig2.shared.common as common
from rigamajig2.maya import deformer, uv, attr


def parentConstraint(driver, driven):
    """
    Create a matrix based 'parent constraint'

    :param str driver: node to drive the parent constraint
    :param str driven: node driven by the parent constraint
    :return: mult matrix and decompose matrix used in the constraint
    """
    multMatrix, decompMatrix = _createSimpleMatrixConstraintNetwork(driver=driver, driven=driven)

    # connect the translate and rotate
    cmds.connectAttr("{}.{}".format(decompMatrix, 'outputTranslate'), "{}.{}".format(driven, 'translate'), f=True)
    cmds.connectAttr("{}.{}".format(decompMatrix, 'outputRotate'), "{}.{}".format(driven, 'rotate'), f=True)

    return multMatrix, decompMatrix


def pointConstraint(driver, driven):
    """
    Create a matrix based 'point constraint'

    :param str driver: node to drive the point constraint
    :param str driven: node driven by the point constraint
    :return: mult matrix and decompose matrix used in the constraint
    """
    multMatrix, decompMatrix = _createSimpleMatrixConstraintNetwork(driver=driver, driven=driven)

    # connect the translate and rotate
    cmds.connectAttr("{}.{}".format(decompMatrix, 'outputTranslate'), "{}.{}".format(driven, 'translate'), f=True)

    return multMatrix, decompMatrix


def orientConstraint(driver, driven):
    """
    Create a matrix based 'orient constraint'

    :param str driver: node to drive the orient constraint
    :param str driven: node driven by the orient constraint
    :return: mult matrix and decompose matrix used in the constraint
    """
    multMatrix, decompMatrix = _createSimpleMatrixConstraintNetwork(driver=driver, driven=driven)

    # connect the translate and rotate
    cmds.connectAttr("{}.{}".format(decompMatrix, 'outputRotate'), "{}.{}".format(driven, 'rotate'), f=True)

    return multMatrix, decompMatrix


def scaleConstraint(driver, driven):
    """
    Create a matrix based 'scale constraint'

    :param str driver: node to drive the scale constraint
    :param str driven: node driven by the scale constraint
    :return: mult matrix and decompose matrix used in the constraint
    """
    multMatrix, decompMatrix = _createSimpleMatrixConstraintNetwork(driver=driver, driven=driven)
    # connect the translate and rotate
    cmds.connectAttr("{}.{}".format(decompMatrix, 'outputScale'), "{}.{}".format(driven, 'scale'), f=True)

    return multMatrix, decompMatrix


def _createSimpleMatrixConstraintNetwork(driver, driven):
    """
    This private function is used to check if a matrix constraint network exists and if not create it

    :param str driver: driver node
    :param str driven: driven node
    :return: mult matrix, decompose matrix
    """
    driven = common.getFirstIndex(driven)
    if cmds.objExists("{}.{}".format(driven, '{}_constraintMm'.format(driver))):
        multMatrix = meta.getMessageConnection('{}.{}'.format(driven, '{}_constraintMm'.format(driver)))
        decomposeMatrix = meta.getMessageConnection('{}.{}'.format(driven, '{}_constraintDcmp'.format(driver)))
    else:
        multMatrix = cmds.createNode('multMatrix', name=driven + '_mm')
        decomposeMatrix = cmds.createNode('decomposeMatrix', name=driven + '_dcmp')

        # convert the driver's world matrix into the parent space of the driven
        cmds.connectAttr("{}.{}".format(driver, 'worldMatrix'), "{}.{}".format(multMatrix, 'matrixIn[0]'))
        cmds.connectAttr("{}.{}".format(driven, 'parentInverseMatrix'), "{}.{}".format(multMatrix, 'matrixIn[1]'))

        # connect the new matrix to the decompose matrix
        cmds.connectAttr("{}.{}".format(multMatrix, 'matrixSum'), "{}.{}".format(decomposeMatrix, 'inputMatrix'))

        # create message connections to the mult matrix and decompose matrix.
        # this is used if we ever create another constraint to re-use the old nodes
        meta.createMessageConnection(driven, multMatrix, '{}_constraintMm'.format(driver))
        meta.createMessageConnection(driven, decomposeMatrix, '{}_constraintDcmp'.format(driver))

    return multMatrix, decomposeMatrix


def negate(driver, driven, t=False, r=False, s=False):
    """
    Negating a transform will add the inverse of any values to the driver to each of its driven objects.

    This becomes useful for things like facial rivet controls where the movement should be handled in a blendshape not
    the translation of the contorl

    :param str driver: transform to drive the negation. This will have its transfrom values inverted
    :param str list driven: transforms to have their transfroms negated.
        Its transforms will be populated with the inverse of the driver.
    :param bool t: negate the translation
    :param bool r: negate the rotation
    :param bool s: negate the scale
    """
    driver = common.getFirstIndex(driver)
    drivens = common.toList(driven)

    for driven in drivens:
        if t:
            node.unitConversion('{}.{}'.format(driver, 't'), '{}.{}'.format(driven, 't'), -1, name=driven + '_t_neg')

        if r:
            node.unitConversion('{}.{}'.format(driver, 'r'), '{}.{}'.format(driven, 'r'), -1, name=driven + '_r_neg')
            # get the opposite rotate order. this is hard coded.
            ro = [5, 3, 4, 1, 2, 0][cmds.getAttr('%s.rotateOrder' % driver)]
            cmds.setAttr("{}.{}".format(driven, 'rotateOrder'), ro)

        if s:
            node.multiplyDivide([1, 1, 1], '{}.{}'.format(driver, 's'), operation='div',
                                output='{}.{}'.format(driven, 's'), name=driven + '_s_neg')


def uvPin(meshVertex):
    """
    Create a mesh Rivet from the current vertex. This command uses the UvPin node.

    :param str meshVertex: vertex to create the rivet on ("model.vtx[0]")
    :return: the out matrix plug for the current vertex.
    """
    if not cmds.objExists(meshVertex):
        raise Exception("the vertex {} does not exist".format(meshVertex))

    if ".vtx[" not in meshVertex:
        raise Exception("{} is not a vertex.".format(meshVertex))

    meshName = meshVertex.split(".")[0]

    # get the orig shape node or create one if it doesnt exist
    origShape = cmds.deformableShape(meshName, og=True)[0]
    if not origShape:
        origShape = cmds.deformableShape(meshName, createOriginalGeometry=True)[0]
    origShape = origShape.split(".")[0]

    # get the deformable shape.
    deformShape = deformer.getDeformShape(meshName)

    # check if the deform shape is connected to a UV Pin node
    uvPinNode = None
    connections = cmds.listConnections("{}.worldMesh".format(deformShape), d=True, s=False, p=False) or []
    for node in connections:
        if cmds.nodeType(node) == 'uvPin':
            uvPinNode = node

    # if we dont have one then we can create one
    if not uvPinNode:
        name = naming.getUniqueName("{}_uvPin".format(meshName))
        uvPinNode = cmds.createNode("uvPin", name=name)
        cmds.connectAttr("{}.worldMesh[0]".format(deformShape), "{}.deformedGeometry".format(uvPinNode), f=True)
        cmds.connectAttr("{}.outMesh".format(origShape), "{}.originalGeometry".format(uvPinNode), f=True)

    # now we can finally add in the coordinates for the selected vertex.
    vertexId = meshVertex.split(".")[-1].split("[")[-1].split("]")[0]
    uvCoords = uv.getUvCoordsFromVertex(meshName, vertexId)

    # get the next available index on the coordinate plug
    nextIndex = attr.getNextAvailableElement("{}.coordinate".format(uvPinNode))

    # set the coortinate attributes
    cmds.setAttr("{}.coordinateU".format(nextIndex), uvCoords[0])
    cmds.setAttr("{}.coordinateV".format(nextIndex), uvCoords[1])

    # determine the plug to return. This should be the number of elements -1 (since its a 0 based list)
    plug = attr._getPlug("{}.coordinate".format(uvPinNode))
    index = plug.evaluateNumElements() - 1

    return "{}.outputMatrix[{}]".format(uvPinNode, index)


def uvPinConstraint(target, meshName, mo=False):
    """
    Create a uv pin constraint between the target and the mesh

    :param target: transform to constrain
    :param meshName: mesh to constrain the target to.
    """
    if not cmds.objExists(meshName):
        raise Exception("the mesh {} does not exist".format(meshName))

    # get the orig shape node or create one if it doesnt exist
    origShape = cmds.deformableShape(meshName, og=True)[0]
    if not origShape:
        origShape = cmds.deformableShape(meshName, createOriginalGeometry=True)[0]
    origShape = origShape.split(".")[0]

    # get the deformable shape.
    deformShape = deformer.getDeformShape(meshName)

    # check if the deform shape is connected to a UV Pin node
    uvPinNode = None
    connections = cmds.listConnections("{}.worldMesh".format(deformShape), d=True, s=False, p=False) or []
    for node in connections:
        if cmds.nodeType(node) == 'uvPin':
            uvPinNode = node

        # if we dont have one then we can create one
    if not uvPinNode:
        name = naming.getUniqueName("{}_uvPin".format(meshName))
        uvPinNode = cmds.createNode("uvPin", name=name)
        cmds.connectAttr("{}.worldMesh[0]".format(deformShape), "{}.deformedGeometry".format(uvPinNode), f=True)
        cmds.connectAttr("{}.outMesh".format(origShape), "{}.originalGeometry".format(uvPinNode), f=True)

    # now lets connect the coorindates to the uv pin. We can use pen maya to get the closest uv coords
    point = om2.MPoint(cmds.xform(target, q=True, t=True, ws=True))

    mfnMesh = mesh.getMeshFn(meshName)
    closestPoint, closestVertex = mfnMesh.getClosestPoint(point, space=om2.MSpace.kWorld)
    uvCoords = mfnMesh.getUVAtPoint(closestPoint, space=om2.MSpace.kWorld)

    # get the next available index on the coordinate plug
    nextIndex = attr.getNextAvailableElement("{}.coordinate".format(uvPinNode))

    # set the coortinate attributes
    cmds.setAttr("{}.coordinateU".format(nextIndex), uvCoords[0])
    cmds.setAttr("{}.coordinateV".format(nextIndex), uvCoords[1])

    # connect the uv pin to the target
    # determine the plug to return. This should be the number of elements -1 (since its a 0 based list)
    plug = attr._getPlug("{}.coordinate".format(uvPinNode))
    index = plug.evaluateNumElements() - 1
    outputPlug = "{}.outputMatrix[{}]".format(uvPinNode, index)

    transform.connectOffsetParentMatrix(outputPlug, driven=target, mo=mo, s=False, sh=False)

    # return the uv pin node and the output plug
    return uvPinNode, outputPlug
