"""
This module contains path utilities
"""
import os

VERSION_DELIMINATOR = '_v'


def clean_path(path):
    """
    Cleanup a given path to work how it should.
    :param path: path to clean
    :returns: cleanup up path
    :rtype: str
    """
    r_path = path.replace('\\', '/')
    r_path = r_path.replace('//', '/')
    return r_path


def is_file(path):
    """Check if the path is a file"""
    root, ext = os.path.splitext(path)
    if ext:
        return True
    else:
        return False


def is_dir(path):
    """Check if the path is a directory"""
    root, ext = os.path.splitext(path)
    if ext:
        return False
    else:
        return True


def get_rel_path(path, start):
    """
    :param path:
    :param start:
    :return:
    """
    return os.path.relpath(path, start)


def get_abs_from_rel(rel, start):
    """
    :param rel: relative path
    :param start: path to start from
    :return: abs path
    """

    abs_path = os.path.join(start, rel)
    norm_path = os.path.normpath(abs_path)

    return norm_path


def make_dir(path):
    """
    :param path: path to create
    :type path: str

    :return: path. if creation failed return None
    :rtype: str
    """
    if is_file(path):
        path = os.path.dirname(path)

    if not os.path.isdir(path):
        os.makedirs(path)
    return path


# file re-naming and versioning
def isUniqueFile(path):
    """
    Check if file is unique
    :param path: file to test
    :type path: str
    :return: if the name is unique
    :rtype: bool
    """

    return False if os.path.exists(path) else True


def getUniqueFile(file, directory, indexPosition=-1):
    """
    Add an index to the given name. The last interger found in the string will be used as the index.
    :param file: filename to check 
    :param directory: directory of file to check 
    :param indexPosition: where to add the index if one is not found. default is -2 (after the suffix)
    :return: returns a new unique name
    """
    # name is already unique
    path = os.path.join(directory, file)
    if isUniqueFile(path):
        return path

    filebase = ".".join(file.split('.')[:-1])
    fileext = file.split('.')[-1]

    fileSplit = filebase.split(VERSION_DELIMINATOR)
    indexStr = [int(s) for s in fileSplit if s.isdigit()]

    if indexStr:
        # Get the location in the name the index appears.
        # Then incriment the index and replace the original in the fileSplit
        oldIndex = (int(indexStr[-1]) if indexStr else -1)
        newIndex = oldIndex + 1
    else:
        # if the index is '-1' add the new index to the end of the string instead of inserting it.
        newIndex = 1
        if indexPosition == -1:
            fileSplit.append(str(newIndex).zfill(3))
        # if the fileSplit is greater than the index, add the index to the end instead of inserting it.
        elif len(fileSplit) >= abs(indexPosition):
            fileSplit.insert(indexPosition + 1, str(newIndex).zfill(3))
        else:
            fileSplit.append(str(newIndex).zfill(3))
            indexPosition = -1

    # check if an object exists with the name until we find a unique name.
    for i in range(2000):
        fileSplit[indexPosition] = str(newIndex)
        newName = VERSION_DELIMINATOR.join(fileSplit)
        path = os.path.join(directory, "{}.{}".format(newName, fileext))
        if not isUniqueFile(path):
            newIndex += 1
        else:
            return path