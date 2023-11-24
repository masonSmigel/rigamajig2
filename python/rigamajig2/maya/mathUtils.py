"""
Vector Functions
"""
import math

import maya.api.OpenMaya as om2
import maya.cmds as cmds

# close enough approximation (we keep around 8 decimals in maya)
PI = 3.14159265359


def isEqual(float0, float1, tol=0.0001):
    """
    Check if two values are close enough to be considered equal

    :param float float0: first float
    :param float float1: second float
    :param float tol: tolerance to consider the same
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
    if (
        isEqual(point0[0], point1[0])
        and isEqual(point0[1], point1[1])
        and isEqual(point0[2], point1[2])
    ):
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
    vector = vector0 - vector1

    return vector.length()


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

    :param vector0: first vector
    :param vector1: second vector
    :return: the dot product of two vectors
    :rtype: tuple list
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
    :rtype: tuple list
    """
    vector0 = om2.MVector(vector0[0], vector0[1], vector0[2])
    vector1 = om2.MVector(vector1[0], vector1[1], vector1[2])
    return vector0 ^ vector1


def mag(vector=(0, 0, 0)):
    """
    Return the magnitude of a vector

    :param vector: vector to get the length of
    :return: magnitude
    :rtype: float
    """
    return om2.MVector(vector[0], vector[1], vector[2]).length()


def addVector(vector0, vector1):
    """
    Returns the addition of two vectors

    :param vector0: first vector
    :param vector1: second vector
    :return: sum of two vectors
    :rtype: tuple list
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
    :rtype: tuple list:
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
    :rtype: tuple list
    """

    return [vector[0] * scalar, vector[1] * scalar, vector[2] * scalar]


def normalize(vector):
    """
    Normalize a vector

    :param vector: vector to normalize
    :return: normalized vector
    :rtype: tuple list
    """
    vector = om2.MVector(vector[0], vector[1], vector[2]).normalize()
    return [vector[0], vector[1], vector[1]]


def remapValue(value, nMin, nMax, oMin=0, oMax=1):
    """
    remap a value

    :param value: value to remap
    :param nMin: input minimum to remap from
    :param nMax: input maximum to remap from
    :param oMin: output minimum to remap to
    :param oMax: output maximum to remap to
    :return: a new remaped value
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
        portion = (oldMax - value) * (newMax - newMin) / (oldMax - oldMin)

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
    :return: value interpolated between a min and max
    """
    return ((max - min) * percent) + min


def vectorLerp(min, max, percent):
    """
    returns linear interpolation between vectors min and max at float percent

    :param min: minimum vector
    :param max: maximim vector
    :param percent: percent of interperlation
    :return: Vector interpolated between a min and max
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
    :return: postion interpolated between a min and max positions
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
    lineVector = subtractVector(lineA, lineB)
    pointVector = subtractVector(lineA, point)

    # scale both vectors to the length of the line.
    lineLength = mag(lineVector)
    lineNormalizedVector = normalize(lineVector)
    pointVectorScaled = scalarMult(pointVector, (1.0 / lineLength))

    # get the dot product.
    dot = dotProduct(lineNormalizedVector, pointVectorScaled)

    # clamp the return to the line segment. if not false the result vector can be any point on the line.
    if clamp:
        if dot < 0.0:
            dot = 0.0
        if dot > 1.0:
            dot = 1.0

    # get the closest distance from the point to the line (offset from line to point at closest distance)
    offsetVector = scalarMult(lineVector, dot)
    # add the offset to the first point of the line to get the vector in proper 3D space
    nearest = addVector(offsetVector, lineA)
    return nearest


def slerp(min, max, percent, smooth=1.0):
    """
    Smoothly interperlate between a mix and max value using hermite interperlation

    :param min: minimum value of interperlation range
    :param max: maximum value of interperlation range
    :param percent: percent of interperlation
    :param smooth: strength of smooth applied
    :return: smoothly interpolated value
    """
    rangeValue = max - min
    smoothValue = pow(percent, 2) * (3 - percent * 2)
    smoothValue = percent + ((smoothValue - percent) * smooth)
    value = min + rangeValue * smoothValue
    return value


def parabolainterp(min, max, percent):
    """
    Interpolate values between a min and max value with a parabola interpolation.


    |
    |                     .
    |                 .        .
    |
    |              .              .
    |
    |            .                  .
    _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

    :param min: minimum value
    :param max: maximim value
    :param percent: percent of interperlation
    :return: parabola interpelated value
    """
    # get the percent on the of the value
    parabola = -pow(2 * percent - 1, 2) + 1

    # remap the 0 to 1 value of the parabola between the min and max ranges
    value = remapValue(parabola, nMin=min, nMax=max, oMin=0, oMax=1)
    return value


def closestValue(inputList, value):
    """
    Get the closest value in a list to a value

    :param list inputList: list of values to get the closest value from
    :param value: value to sample against to find the closest
    :return: closest value
    :rtype: float int
    """
    inputList.sort()
    difference = lambda input_list: abs(input_list - value)
    res = min(inputList, key=difference)

    return res


def radToDegree(angle):
    """
    Convert an angle from radians to degrees

    :param angle: angle in radians
    :return: angle in degrees
    """
    return [rad * 180 / math.pi for rad in angle]


def degreeToRad(angle):
    """
    Convert an angle from degrees to radians

    :param angle: angle in degrees
    :return: angle in radians
    """
    return [degree * (PI / 180) for degree in angle]


def quaternionToEuler(x, y, z, w, asDegrees=True):
    """
    Convert a quaternion into an angle

    Cool note: The body of this function was written with chatGPT!!!

    :param x: X component of a quaternion
    :param y: Y component of a quaternion
    :param z: Z component of a quaternion
    :param w: W component of a quaternion
    :param asDegrees: Return the output as degrees. otherwise it will be in radians
    :return: euler angle
    """

    # Calculate the Euler angles
    roll = math.atan2(2 * (w * x + y * z), 1 - 2 * (x**2 + y**2))
    pitch = math.asin(2 * (w * y - z * x))
    yaw = math.atan2(2 * (w * z + x * y), 1 - 2 * (y**2 + z**2))

    # Return the Euler angles
    if asDegrees:
        return radToDegree([roll, pitch, yaw])
    return [roll, pitch, yaw]
