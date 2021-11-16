import sys
import logging

VERSION_MAJOR = 1
VERSION_MINOR = 0
VERSION_PATCH = 0

version_info = (VERSION_MAJOR, VERSION_MINOR, VERSION_PATCH)
version = '%i.%i.%i' % version_info
__version__ = version

__all__ = ['version', 'version_info', '__version__']

logger = logging.getLogger(__name__)


def reloadModule(name='rigamajig2', log=True):
    """
    Reload a module
    :param name: name of tha module to reload
    :param log: log the modules reloaded
    :return:
    """
    for mod in sys.modules.keys():
        if mod.startswith(name):
            if log:
                logger.info("Reloaded module: {}".format(mod))
            del sys.modules[mod]

#
# # Custom Logger class
# class Logger(object):
#     LOGGER_NAME = 'Rigamajig2'
#
#     LEVEL_DEFAULT = logging.DEBUG
#     PROPAGATE_DEFAULT = False
#
#     _logger_obj = None
#
#     @classmethod
#     def logger_obj(cls):
#         if not cls._logger_obj:
#             if cls.logger_exists():
#                 cls._logger_obj = logging.getLogger(cls.LOGGER_NAME)
#             else:
#                 cls._logger_obj = logging.getLogger(cls.LOGGER_NAME)
#                 cls._logger_obj.setLevel(cls.LEVEL_DEFAULT)
#                 cls._logger_obj.propagate = cls.PROPAGATE_DEFAULT
#
#                 fmt = logging.Formatter("[%(name)s][%(levelname)s][%(message)s]")
#
#                 stream_handler = logging.StreamHandler(sys.stdout)
#                 stream_handler.setFormatter(fmt)
#                 cls._logger_obj.addHandler(stream_handler)
#
#         return cls._logger_obj
#
#     @classmethod
#     def logger_exists(cls):
#         return cls.LOGGER_NAME in logging.Logger.manager.loggerDict.keys()
#
#     @classmethod
#     def set_level(cls, level):
#         lg = cls.logger_obj()
#         lg.setLevel(level)
#
#     @classmethod
#     def set_propagate(cls, propagate):
#         lg = cls.logger_obj()
#         lg.propagate = propagate
#
#     @classmethod
#     def debug(cls, msg, *args, **kwargs):
#         lg = cls.logger_obj()
#         lg.debug(msg, *args, **kwargs)
#
#     @classmethod
#     def info(cls, msg, *args, **kwargs):
#         lg = cls.logger_obj()
#         lg.info(msg, *args, **kwargs)
#
#     @classmethod
#     def warning(cls, msg, *args, **kwargs):
#         lg = cls.logger_obj()
#         lg.warning(msg, *args, **kwargs)
#
#     @classmethod
#     def error(cls, msg, *args, **kwargs):
#         lg = cls.logger_obj()
#         lg.error(msg, *args, **kwargs)
#
#     @classmethod
#     def critical(cls, msg, *args, **kwargs):
#         lg = cls.logger_obj()
#         lg.critical(msg, *args, **kwargs)
#
#     @classmethod
#     def log(cls, lvl, msg, *args, **kwargs):
#         lg = cls.logger_obj()
#         lg.log(lvl, msg, *args, **kwargs)
#
#     @classmethod
#     def exception(cls, msg, *args, **kwargs):
#         lg = cls.logger_obj()
#         lg.exception(msg, *args, **kwargs)
#
#     @classmethod
#     def write_to_file(cls, path, level=logging.WARNING):
#         file_handler = logging.FileHandler(path)
#         file_handler.setLevel(level)
#
#         fmt = logging.Formatter("[%(asctime)s][%(levelname)s][%(message)s]")
#         file_handler.setFormatter(fmt)
#         lg = cls.logger_obj()
#         lg.addHandler(file_handler)
