"""
This module contains path utilities
"""
import os


def cleanPath(path):
    """
    Cleanup a given path to work how it should.
    :param path: path to clean
    :returns: cleanup up path
    :rtype: str
    """
    rPath = path.replace('\\', '/')
    rPath = rPath.replace('//', '/')
    return rPath


def isFile(path):
    """Check if the path is a file"""
    root, ext = os.path.splitext(path)
    if ext:
        return True
    else:
        return False


def isDir(path):
    """Check if the path is a directory"""
    root, ext = os.path.splitext(path)
    if ext:
        return False
    else:
        return True


def getRelativePath(path, start):
    """
    :param path:
    :param start:
    :return:
    """
    return os.path.relpath(path, start)


def getAbsoultePath(rel, start):
    """
    :param rel: relative path
    :param start: path to start from
    :return: abs path
    """

    absoultePath = os.path.join(start, rel)
    normalizedPath = os.path.normpath(absoultePath)

    return normalizedPath


def mkdir(path):
    """
    :param path: path to create
    :type path: str

    :return: path. if creation failed return None
    :rtype: str
    """
    if isFile(path):
        path = os.path.dirname(path)

    if not os.path.isdir(path):
        os.makedirs(path)
    return path
