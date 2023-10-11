#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: logging.py
    author: masonsmigel
    date: 06/2022

    we will use this logging module as
    the base logging module for rigamajig.

"""

import typing
# import all globals and locals from logging
from logging import *

# Try to load the maya utils module.
# If it can be imported assume the script is accessed from within maya.
try:
    import maya.utils

    inMaya = True
except:
    inMaya = False

DCC_LOGGING_FORMATT = f"%(name)s: %(message)s"
LOG_FILE_FORMATT = f"%(asctime)s : %(name)-32s : %(levelname)-8s : %(message)s"


class RigamajigLogger(Logger):
    def __init__(self, name, level=None, propagate=False):
        super().__init__(name)

        if not self.hasHandlers():
            handler = maya.utils.MayaGuiLogHandler() if inMaya else StreamHandler()
            fmt = Formatter(DCC_LOGGING_FORMATT)
            handler.setFormatter(fmt)
            self.addHandler(handler)

            if level:
                self.setLevel(level)
            self.propagate = propagate


# Override the default getLogger with RigamajigLogger
setLoggerClass(RigamajigLogger)


def getChildLoggers(loggerName: str = "rigamajig2") -> typing.List[Logger]:
    """
    Return a list of all rigamajig loggers.

    :param str loggerName: Get a list of loggers that start with the given string.

    :return: A list of loggers.
    :rtype: list[logging.Logger]
    """
    loggers = [getLogger(name) for name in Logger.manager.loggerDict]

    returnList = set()
    for logger in loggers:
        if logger.name.startswith(loggerName):
            returnList.add(logger)

    return list(returnList)


def _addFileHandler(logger: Logger, filename: str):
    """
    Add a FileHandler to the logger.

    :param logging.Logger logger: Logger object.
    :param str filename: The name of the log file.
    """
    fileHandler = FileHandler(filename)
    fileHandler.setLevel(INFO)

    # Set the formatter if provided
    fmt = Formatter(LOG_FILE_FORMATT)
    fileHandler.setFormatter(fmt)

    logger.addHandler(fileHandler)
    print(f"begin logging {logger.name} to {filename}")


def writeToFile(loggers: typing.List[Logger], filename: str):
    """
    Enable logging to a file for all loggers below the specified loggerName.

    This function sets the global flag `RigamajigLoggerOptions.logToFile` to True
    and updates the log file name using `RigamajigLoggerOptions.logFileName`.

    For each logger below the specified `loggerName`, it adds a `FileHandler` to
    write log messages to the provided file.

    :param loggers: list of loggers
    :param str filename: The name of the log file.
    """

    # first set all current loggers to write to a file
    for logger in loggers:

        # if there is already a stream handler for this specific file skip adding the handler.
        for handler in logger.handlers:
            if isinstance(handler, FileHandler):
                if filename and handler.baseFilename == filename:
                    return
        # otherwise add the logger.
        _addFileHandler(logger=logger, filename=filename)


def endWriteToFile(loggers: str, filename: str = None):
    """
    Remove all FileHandler loggers from a list of files.

    :param str loggers: The logger name.
    :param str filename: The name of the log file to remove (optional).
    """
    for logger in loggers:

        handlersToRemove = []
        for handler in logger.handlers:
            if isinstance(handler, FileHandler):
                if getattr(handler, "baseFilename", None) == filename:
                    # If a specific filename is provided, remove only handlers with that filename
                    handlersToRemove.append(handler)
                elif not filename:
                    # If no specific filename is provided, remove all FileHandlers
                    handlersToRemove.append(handler)

            for handler in handlersToRemove:
                logger.removeHandler(handler)
                print(f"logger: {logger.name} end logging to file: {handler.baseFilename}")


def setLoggingLevel(loggers: typing.List[Logger], level: int):
    """
    Set the logging level of all rigamajig loggers
    :return:
    """

    for logger in loggers:
        logger.setLevel(level=level)
        logger.info(f"Logging Level Changed to: {level}")


if __name__ == '__main__':
    testLogger = getLogger("test")
    writeToFile("test", "/Users/masonsmigel/Desktop/example.log")
    testLogger.info("this is an info message")
    testLogger.warning("this is a warning ")
    testLogger.error("this is an error")
