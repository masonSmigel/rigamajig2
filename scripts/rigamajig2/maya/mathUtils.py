"""
Vector Functions
"""
import math
import maya.cmds as cmds
import maya.api.OpenMaya as om2


def isEqual(float0, float1, tol=0.0001):
    """
    Check if two values are close enough to be considered equal 
    :param float0: first float 
    :param float1: second float
    :param tol: tolerance to consider the same 
    :return: True if the values are equal. False if not
    :rtype: bool
    """
    return True if abs(float0 - float1) <= tol else False


def pointsEqual(point0, point1):
    """
    Check if two points are equal 
    :param point0: 
    :param point1: 
    :return: True if the values are equal. False if not
    :rtype: bool
    """
    if isEqual(point0[0], point1[0]) and isEqual(point0[1], point1[1]) and isEqual(point0[2], point1[2]):
        return True
    else:
        return False


def distance(point0=(0, 0, 0), point1=(0, 0, 0)):
    """
    Get the distance between two vectors
    :param point0: First point
    :param point1: Second point
    :return: distance length
    :rtype: float
    """
    vector0 = om2.MVector(point0[0], point0[1], point0[2])
    vector1 = om2.MVector(point1[0], point1[1], point1[2])
    v = vector0 - vector1

    return v.length()


def distanceNodes(transform0, transform1):
    """
    Get the distance between two transforms
    :param transform0: First transform
    :param transform1: Second Transform
    :return: distance length
    :rtype: float
    """
    point0 = cmds.xform(transform0, q=True, ws=True, t=True)
    point1 = cmds.xform(transform1, q=True, ws=True, t=True)
    return distance(point0, point1)


def dotProduct(vector0, vector1):
    """
    Returns the dot product (inner product) of 2 vectors
    :param vector0:
    :param vector1:
    :return:
    """
    vector0 = om2.MVector(vector0[0], vector0[1], vector0[2])
    vector1 = om2.MVector(vector1[0], vector1[1], vector1[2])

    return vector0 * vector1


def crossProduct(vector0, vector1):
    """
    Returns the dot product (inner product) of 2 vectors
    :param vector0: first vector
    :param vector1: second vector
    :return: cross product of two vectors
    """
    vector0 = om2.MVector(vector0[0], vector0[1], vector0[2])
    vector1 = om2.MVector(vector1[0], vector1[1], vector1[2])
    return vector0 ^ vector1


def mag(vector=(0, 0, 0)):
    """
    Return the magnitude of a vector
    :param vector: vector to get the length of
    :return: magnitude
    """
    return om2.MVector(vector[0], vector[1], vector[2]).length()


def addVector(vector0, vector1):
    """
    Returns the addition of two vectors
    :param vector0: first vector
    :param vector1: second vector
    :return: sum of two vectors
    """
    vector0 = om2.MVector(vector0[0], vector0[1], vector0[2])
    vector1 = om2.MVector(vector1[0], vector1[1], vector1[2])
    return vector0 + vector1


def subtractVector(vector0, vector1):
    """
   Returns the subtraction of two vectors
   :param vector0: minuhend vector
   :param vector1: subtrahend vector
   :return: difference of two vectors
   """
    vector0 = om2.MVector(vector0[0], vector0[1], vector0[2])
    vector1 = om2.MVector(vector1[0], vector1[1], vector1[2])
    return vector1 - vector0


def scalarMult(vector, scalar):
    """
    Multipy a vector by a scalar
    :param vector: vector to multipy
    :param scalar: scalar value to multiply each item of the vector by
    :return: vector
    """

    return [vector[0] * scalar, vector[1] * scalar, vector[2] * scalar]


def normalize(vector):
    """
    Normalize a vector
    :param vector: vector to normalize
    :return: normalized vector
    """
    v = om2.MVector(vector[0], vector[1], vector[2]).normalize()
    return [v[0], v[1], v[1]]


def remapValue(value, nMin, nMax, oMin=0, oMax=1):
    """
    remap a value
    :param value:
    :param nMin:
    :param nMax:
    :param oMin:
    :param oMax:
    :return:
    """
    # range check
    if oMin == oMax:
        raise ValueError("Warning: Zero output range")

    if nMin == nMax:
        raise ValueError("Warning: Zero output range")

    # check reversed input range
    reverseInput = False
    oldMin = min(oMin, oMax)
    oldMax = max(oMin, oMax)
    if not oldMin == oMin:
        reverseInput = True

    # check reversed output range
    reverseOutput = False
    newMin = min(nMin, nMax)
    newMax = max(nMin, nMax)
    if not newMin == nMin:
        reverseOutput = True

    portion = (value - oldMin) * (newMax - newMin) / (oldMax - oldMin)
    if reverseInput:
        portion = (oldMax - x) * (newMax - newMin) / (oldMax - oldMin)

    result = portion + newMin
    if reverseOutput:
        result = newMax - portion

    return result


def lerp(min, max, percent):
    """
    returns linear interpolation between floats min and max at float percent
    :param min: minimum value
    :param max: maximim value
    :param percent: percent of interperlation
    """
    return ((max - min) * percent) + min


def vectorLerp(min, max, percent):
    """
    returns linear interpolation between vectors min and max at float percent
    :param min: minimum vector
    :param max: maximim vector
    :param percent: percent of interperlation
    """
    x = lerp(min[0], max[0], percent)
    y = lerp(min[1], max[1], percent)
    z = lerp(min[2], max[2], percent)
    return [x, y, z]


def nodePosLerp(minNode, maxNode, percent):
    """
    returns linear interpolation between positions of a min and max node at float percent
    :param minNode: minimum vector
    :param maxNode: maximim vector
    :param percent: percent of interperlation
    """
    min = cmds.xform(minNode, q=True, ws=True, t=True)
    max = cmds.xform(maxNode, q=True, ws=True, t=True)
    return vectorLerp(min, max, percent)


def offsetVector(point0, point1):
    """
    returns the offset vector between two points
    :param point0: start point of the offset vector
    :param point1: end point of the offset vector
    :return: offset vector
    """
    pnt0 = om2.MPoint(point0[0], point0[1], point0[2], 1.0)
    pnt1 = om2.MPoint(point1[0], point1[1], point1[2], 1.0)
    vec = pnt1 - pnt0
    return vec


def closestPointOnLine(point, lineA, lineB, clamp=False):
    """
    Find the closest point along a given line
    :param point: find the point on the line closest to this
    :param lineA: Start point of the line
    :param lineB: End point of the line
    :param clamp: clamp the result to the line segment
    :return: point on the line closest to the given point
    """
    line_vec = subtractVector(lineA, lineB)
    pnt_vec = subtractVector(lineA, point)

    # scale both vectors to the length of the line.
    line_len = mag(line_vec)
    line_norm_vec = normalize(line_vec)
    pnt_vec_scaled = scalarMult(pnt_vec, (1.0 / line_len))

    # get the dot product.
    dot = dotProduct(line_norm_vec, pnt_vec_scaled)

    # clamp the return to the line segment. if not false the result vector can be any point on the line.
    if clamp:
        if dot < 0.0: dot = 0.0
        if dot > 1.0: dot = 1.0

    # get the closest distance from the point to the line (offset from line to point at closest distance)
    offset_vec = scalarMult(line_vec, dot)
    # add the offset to the first point of the line to get the vector in proper 3D space
    nearest = addVector(offset_vec, lineA)
    return nearest


def slerp(min, max, percent, smooth=1.0):
    """
    Smoothly interperlate between a mix and max value using hermite interperlation
    :param min: minimum value of interperlation range
    :param max: maximum value of interperlation range
    :param percent: percent of interperlation
    :param smooth: strength of smooth applied
    :return:
    """
    range_val = max - min
    smooth_value = pow(percent, 2) * (3 - percent * 2)
    smooth_value = percent + ((smooth_value - percent) * smooth)
    value = min + range_val * smooth_value
    return value


def parabolainterp(min, max, percent):
    """
    Interpolate values between a min and max value with a parabola interpolation.


    |
    |                     .
    |                 .		  .
    |
    |              .		      .
    |
    |            .				    .
    _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

    :param min: minimum value
    :param max: maximim value
    :param percent: percent of interperlation
    :return:
    """
    # get the percent on the of the value
    parabola = -pow(2 * percent - 1, 2) + 1

    # remap the 0 to 1 value of the parabola between the min and max ranges
    value = remapValue(parabola, nMin=min, nMax=max, oMin=0, oMax=1)
    return value
