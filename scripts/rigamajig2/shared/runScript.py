"""
Tool to run python scripts on the disk
"""
import os
import fnmatch
import runpy
import logging
logger = logging.getLogger(__name__)


def runScript(filePath, initGlobals=None):
    """
    Execute code located at the file_path
    :param filePath: File Path
    :param initGlobals: Optional- dictionary with module globals
    :return:
    """
    if initGlobals is None:
        initGlobals = dict()
    filePath = os.path.realpath(filePath)
    logger.info("Running: {}".format(os.path.basename(filePath)))
    runpy.run_path(filePath, initGlobals, "__main__")


def findScripts(path):
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
