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


class RigamajigLoggerOptions:
    """
    A configuration class for rigamajig2 logger options.

    :param bool logToFile: Indicates whether to log messages to a file.
    :param str logFileName: The filename for the log file.
    """
    logToFile = False
    logFileName = None
    logRootName = None


class LowercaseFormatter(Formatter):
    """Custom Formatter that displays the level name in lowercase."""

    def format(self, record):
        """
        Format the log record.

        :param logging.LogRecord record: The log record to be formatted.

        :return: The formatted log message.
        :rtype: str
        """
        # Call the original formatter to get the message
        msg = super().format(record)
        # Convert the log level to lowercase
        level = record.levelname.lower()
        # Replace the original log level in the message
        msg = msg.replace(record.levelname, level)
        return msg


# to override the default logger we need to store
# the old get logger. keep a reference to this function
# in the variable getLogger_
getLogger_ = getLogger


def getLogger(name: str, level: int = None, propagate: bool = False) -> Logger:
    """
    Create a new logger configured for rigamajig2.

    Using get loggers will clear out all handlers.

    :param str name: Name of the logger.
    :param int level: Default logging level.
    :param bool propagate: Propagate logging messages to parent.

    :return: A newly created logger.
    :rtype: logging.Logger
    """
    logger = getLogger_(name)

    handler = maya.utils.MayaGuiLogHandler() if inMaya else StreamHandler()

    fmt = LowercaseFormatter(DCC_LOGGING_FORMATT)
    handler.setFormatter(fmt)
    logger.handlers = [handler]

    if RigamajigLoggerOptions.logToFile and name.startswith(RigamajigLoggerOptions.logRootName):
        __addFileHandler(logger=logger, filename=RigamajigLoggerOptions.logFileName)

    if level: logger.setLevel(level)
    logger.propagate = propagate

    return logger


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


def __addFileHandler(logger: Logger, filename: str):
    """
    Add a FileHandler to the logger.

    :param logging.Logger logger: Logger object.
    :param str filename: The name of the log file.
    """

    existingFileHandlers = [handler for handler in logger.handlers if isinstance(handler, FileHandler)]
    if existingFileHandlers:
        return

    fileHandler = FileHandler(filename)
    fileHandler.setLevel(INFO)

    # Set the formatter if provided
    fmt = Formatter(LOG_FILE_FORMATT)
    fileHandler.setFormatter(fmt)

    logger.addHandler(fileHandler)


def writeToFile(loggerName: str, filename: str):
    """
    Enable logging to a file for all loggers below the specified loggerName.

    This function sets the global flag `RigamajigLoggerOptions.logToFile` to True
    and updates the log file name using `RigamajigLoggerOptions.logFileName`.

    For each logger below the specified `loggerName`, it adds a `FileHandler` to
    write log messages to the provided file.

    :param str loggerName: The logger name.
    :param str filename: The name of the log file.
    """
    RigamajigLoggerOptions.logToFile = True
    RigamajigLoggerOptions.logFileName = filename
    RigamajigLoggerOptions.logRootName = loggerName

    # first set all current loggers to write to a file
    for logger in getChildLoggers(loggerName=loggerName):
        __addFileHandler(logger=logger, filename=filename)


def endWriteToFile(loggerName: str):
    """
    Remove all FileHandler loggers from a list of files.

    :param str loggerName: The logger name.
    """
    for logger in getChildLoggers(loggerName=loggerName):
        for handler in logger.handlers:
            if isinstance(handler, FileHandler):
                logger.removeHandler(handler)
                print(f"logger: {logger.name} end logging to file")

    # reset the logger options
    RigamajigLoggerOptions.logToFile = False
    RigamajigLoggerOptions.logFileName = None
    RigamajigLoggerOptions.logRootName = None


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

    testLogger.info("this is an info message")
    testLogger.warning("this is a warning ")
    testLogger.error("this is an error")
