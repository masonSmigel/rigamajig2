"""
Axis utilities
"""
ROTATEORDER = ['xyz', 'yzx', 'zxy', 'xzy', 'yxz', 'zyx']


def getVectorFromAxis(axis):
    if axis.lower() == 'x':
        vector = [1, 0, 0]
    elif axis.lower() == 'y':
        vector = [0, 1, 0]
    elif axis.lower() == 'z':
        vector = [0, 0, 1]
    elif axis.lower() == '-x':
        vector = [-1, 0, 0]
    elif axis.lower() == '-y':
        vector = [0, -1, 0]
    elif axis.lower() == '-z':
        vector = [0, 0, -1]
    else:
        raise ValueError("Keyword Argument: 'axis' not of accepted value ('x', 'y', 'z', '-x', '-y', '-z').")
    return vector


def getRotateOrder(order):
    """
    Get the proper rotate order index
    :param order: rotate order
    :type order: str
    :return:
    """
    return ROTATEORDER.index(order)
