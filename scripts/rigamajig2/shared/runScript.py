"""
Tool to run python scripts on the disk
"""
import os
import fnmatch
import runpy
import logging
logger = logging.getLogger(__name__)


def run_script(file_path, initGlobals=None):
    """
    Execute code located at the file_path
    :param file_path: File Path
    :param initGlobals: Optional- dictionary with module globals
    :return:
    """
    if initGlobals is None:
        initGlobals = dict()
    file_path = os.path.realpath(file_path)
    logger.info("Running: {}".format(os.path.basename(file_path)))
    runpy.run_path(file_path, initGlobals, "__main__")


def find_scripts(path):
    """
    Look through a directory and return the full path of all scripts within it.
    :param path: Path to search for python files
    :return: list of python files found
    """
    for root, dirs, files in os.walk(path):
        for basename in files:
            if fnmatch.fnmatch(basename, "*.py"):
                filename = os.path.join(root, basename)
                yield filename
