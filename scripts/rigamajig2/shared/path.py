"""
This module contains path utilities
"""
import os


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

