"""
Functions for working with matricies
"""
from maya.api import OpenMaya as om2
import math


def buildMatrix():
    """
    Build matrix
    :return:
    """
    pass


def matrixMult(matrix1, matrix2):
    """
    Multiply two matrices

    :param matrix1: first matrix to multiply
    :param matrix2: Second matrix to multiply
    :return: sum of the two multiplied matricies
    :rtype: tuple
    """

    matrix1 = om2.MMatrix(matrix1)
    matrix2 = om2.MMatrix(matrix2)
    resultMatrix = matrix1 * matrix2
    return tuple(resultMatrix)


def getTranslation(matrix):
    """
    Get the translation values of a matrix

    :param matrix: matrix to decompose
    :return: list of translate values
    :rtype: list
    """
    return decompMatrix(matrix)[0]


def getRotation(matrix, rotateOrder='xyz'):
    """
    Get the rotation of a matrix. Must provide a rotate order for accurate Euler values

    :param matrix: matrix to get the rotation of
    :param rotateOrder: rotate order of the matrix. Default is 'xyz'
    :return: list of angles
    :rtype: list
    """
    return decompMatrix(matrix, rotateOrder)[1]


def getScale(matrix):
    """
    Get the scale of a matrix

    :param matrix: matrix to get the scale of
    :return: list of scale values
    :rtype: list
    """
    return decompMatrix(matrix)[2]


def decompMatrix(matrix, rotateOrder='xyz'):
    """
    Decomposes a MMatrix. Returns an list of translation,rotation and scale in world space.

    :param matrix: input matrix
    :param rotateOrder: rotate order used to calculate Euler angles
    :return: list of [translate, rotate, scale] tuples
            ex: [(0, 0, 0), (0, 0, 0), (1, 1, 1)]
    :rtype: list
    """
    if not isinstance(matrix, om2.MMatrix):
        matrix = om2.MMatrix(matrix)
    rotOrderDict = {'xyz': 0, 'yzx': 1, 'zxy': 2, 'xzy': 3, 'yxz': 4, 'zyx': 5}
    # Puts matrix into transformation matrix
    mTransformMtx = om2.MTransformationMatrix(matrix)

    # Translate
    trans = mTransformMtx.translation(om2.MSpace.kWorld)

    # Rotate
    eulerRot = mTransformMtx.rotation()
    eulerRot.reorderIt(rotOrderDict[rotateOrder])
    angles = [math.degrees(angle) for angle in (eulerRot.x, eulerRot.y, eulerRot.z)]

    # Scale
    scale = mTransformMtx.scale(om2.MSpace.kWorld)

    # Return Values
    return [trans.x, trans.y, trans.z], angles, scale

