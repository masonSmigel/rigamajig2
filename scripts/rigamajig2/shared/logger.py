#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: logger.py
    author: masonsmigel
    date: 06/2022

"""
import logging
import sys


class DisableLogger():
    """ Context manager to disable all logger messages from any logger."""

    def __enter__(self):
        logging.disable(logging.CRITICAL)

    def __exit__(self, exitType, exitValue, traceback):
        logging.disable(logging.NOTSET)


LOGGER_CODE = 'rigamajig2'

DCC_LOGGING_FORMATT = f"{LOGGER_CODE}.%(name)s - %(levelname)s:  %(message)s"
LOG_FILE_FORMATT = f"%(asctime)s: {LOGGER_CODE}.%(name)s - %(levelname):  %(message)s"


# Custom Logger class
class Logger(object):
    """
    custom rigamajig logger class
    """
    LOGGER_NAME = 'core'

    LEVEL_DEFAULT = logging.DEBUG
    PROPAGATE_DEFAULT = False

    _loggerObj = None

    @classmethod
    def loggerObj(cls):
        """
        constructor for the logger.

        if a logger exists return the logger,
        if not create one then return it.
        """
        if not cls._loggerObj:
            if cls.loggerExists():
                cls._loggerObj = logging.getLogger(cls.LOGGER_NAME)
            else:
                cls._loggerObj = logging.getLogger(cls.LOGGER_NAME)
                cls._loggerObj.setLevel(cls.LEVEL_DEFAULT)
                cls._loggerObj.propagate = cls.PROPAGATE_DEFAULT

                # "%(name)s %(levelname)s [%(module)s: %(lineno)d] %(message)s"
                fmt = logging.Formatter(DCC_LOGGING_FORMATT)

                streamHandler = logging.StreamHandler(sys.stderr)
                streamHandler.setFormatter(fmt)
                cls._loggerObj.addHandler(streamHandler)

        return cls._loggerObj

    @classmethod
    def loggerExists(cls):
        """check if the logger exists"""
        return cls.LOGGER_NAME in logging.Logger.manager.loggerDict.keys()

    @classmethod
    def setLevel(cls, level):
        """set the logging level"""
        logger = cls.loggerObj()
        logger.setLevel(level)

    @classmethod
    def setPropagate(cls, propagate):
        """set the propagate"""
        logger = cls.loggerObj()
        logger.propagate = propagate

    @classmethod
    def debug(cls, msg, *args, **kwargs):
        """create an debug statement"""
        logger = cls.loggerObj()
        logger.debug(msg, *args, **kwargs)

    @classmethod
    def info(cls, msg, *args, **kwargs):
        """create an info statement"""
        logger = cls.loggerObj()
        logger.info(msg, *args, **kwargs)

    @classmethod
    def warning(cls, msg, *args, **kwargs):
        """create an warning statement"""
        logger = cls.loggerObj()
        logger.warning(msg, *args, **kwargs)

    @classmethod
    def error(cls, msg, *args, **kwargs):
        """create an error statement"""
        logger = cls.loggerObj()
        logger.error(msg, *args, **kwargs)

    @classmethod
    def critical(cls, msg, *args, **kwargs):
        """create an critical statement"""
        logger = cls.loggerObj()
        logger.critical(msg, *args, **kwargs)

    @classmethod
    def log(cls, lvl, msg, *args, **kwargs):
        """create an log statement"""
        logger = cls.loggerObj()
        logger.log(lvl, msg, *args, **kwargs)

    @classmethod
    def exception(cls, msg, *args, **kwargs):
        """create an execption statement"""
        logger = cls.loggerObj()
        logger.exception(msg, *args, **kwargs)

    @classmethod
    def writeToFile(cls, path, level=logging.INFO):
        """write the log to a file"""
        fileHandler = logging.FileHandler(path)
        fileHandler.setLevel(level)

        fmt = logging.Formatter(LOG_FILE_FORMATT)
        fileHandler.setFormatter(fmt)
        logger = cls.loggerObj()
        logger.addHandler(fileHandler)

    @classmethod
    def endWriteToFile(cls):
        """ Remove all stream handlers that are logging to a file"""
        logger = cls.loggerObj()
        for hander in logger.handlers:
            if isinstance(hander, logging.FileHandler):
                logger.removeHandler(hander)


if __name__ == '__main__':
    Logger.setLevel(0)
    Logger.info("test")
