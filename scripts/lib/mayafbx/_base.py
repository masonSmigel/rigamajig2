from __future__ import division, absolute_import, print_function
import logging
import re

from maya import mel

from ._enums import (
    QuaternionInterpolation,
    ConvertUnit,
    UpAxis,
    ForcedFileAxis,
    AxisConversionMethod,
    NurbsSurfaceAs,
    FileFormat,
    MergeMode,
    SamplingRate,
    SkeletonDefinition)

LOG = logging.getLogger('mayafbx')

_ENUM_COMMANDS_VALUES_MAP = {
    "FBXProperty Export|IncludeGrp|Animation|ExtraGrp"
    "|Quaternion": tuple(QuaternionInterpolation),

    "FBXProperty Export|AdvOptGrp|UnitsGrp|UnitsSelector": tuple(ConvertUnit),
    "FBXProperty Export|AdvOptGrp|AxisConvGrp|UpAxis": tuple(UpAxis),
    "FBXImportForcedFileAxis": tuple(ForcedFileAxis),
    "FBXExportAxisConversionMethod": tuple(AxisConversionMethod),

    "FBXProperty Export|IncludeGrp|Geometry"
    "|GeometryNurbsSurfaceAs": tuple(NurbsSurfaceAs),

    # "FBXExportFileVersion": tuple(FileVersion),  # No check for file version.
    "FBXProperty Export|AdvOptGrp|Fbx|AsciiFbx": tuple(FileFormat),

    "FBXProperty Import|IncludeGrp|Animation|SamplingPanel"
    "|SamplingRateSelector": tuple(SamplingRate),

    "FBXProperty Import|IncludeGrp|Animation|ConstraintsGrp"
    "|CharacterType": tuple(SkeletonDefinition),
    "FBXImportMode": tuple(MergeMode),
}


RE_PROPERTIES = re.compile(
    r"# PATH: (?P<path>.*?)"                            # Property path
    r"\s*\( TYPE: (?P<type>.*?) \)"                     # Value type
    r"\s*\( VALUE: (?P<value>.*?) \)"                   # Current value
    r"\s*(?:\(POSSIBLE VALUES: (?P<values>.*?) \))? #"  # Possible enum values
)  #: Unused regex, useful to cleanup info from the "FBXProperties" mel command.


def run_mel_command(command):
    try:
        value = mel.eval(command)
    except RuntimeError as error:
        LOG.error("Failed to run: %s", command)
        raise error
    else:
        LOG.debug("Runned: %s", command)
        return value


class FbxPropertyOption(object):

    @property
    def default(self):
        return self._default() if callable(self._default) else self._default

    def __init__(self, command, default, type):
        self.command = command
        self._default = default
        self.type = type
        self.allowed_values = _ENUM_COMMANDS_VALUES_MAP.get(self.command, None)

    def __get__(self, instance, owner):
        return instance._options.get(self.command, self.default)

    def __set__(self, instance, value):
        if self.allowed_values and value not in self.allowed_values:
            raise ValueError('Invalid value: {}'.format(value))
        instance._options[self.command] = self.type(value)

    def apply(self, instance):
        """Set value in `instance` to scene."""
        formatter = {
            bool: lambda v: str(v).lower(),
            str: lambda v: '"{}"'.format(v)
        }.get(self.type, lambda v: str(v))
        value = formatter(instance._options.get(self.command, self.default))

        args = [self.command]
        if self.command not in ('FBXExportUpAxis',
                                'FBXExportAxisConversionMethod',):
            args += ['-v']
        args += [value]

        command = ' '.join(args)
        try:
            run_mel_command(command)
        except RuntimeError:
            raise ValueError("Bad value for command: {}".format(command))

    def query(self, instance):
        """Query value from scene and set it to `instance`."""
        command = ' '.join([self.command, '-q'])
        try:
            value = run_mel_command(command)
        except RuntimeError:
            raise RuntimeError("Property not found: {}".format(command))
        value = {'true': True, 'false': False}.get(value, self.type(value))
        instance._options[self.command] = value


class FbxOptions(object):

    # TODO __contain__ for non-default options ?
    # TODO list modified options

    _NON_DESCRIPTOR_ATTRIBUTES = tuple()

    @classmethod
    def _properties(cls):
        # TODO move as a static dict in metaclass ?
        return {
            key: value
            for key, value in cls.__dict__.items()
            if isinstance(value, FbxPropertyOption)}

    @classmethod
    def from_scene(cls):
        """Return a new instance initialized from scene options."""
        instance = cls()
        for _, option in cls._properties().items():
            option.query(instance)
        return instance

    def __init__(self, **kwargs):
        self._options = {}
        #: Mapping {command: value}, managed by the FbxPropertyOption attributes.

        self._backup_options = None
        #: Back scene options during context. Set in __enter__ and __exit__.

        for key, value in kwargs.items():
            setattr(self, key, value)

    def __setitem__(self, key, value):
        if key not in self._NON_DESCRIPTOR_ATTRIBUTES:
            prop = self.__class__.__dict__.get(key)
            if not isinstance(prop, FbxPropertyOption):
                raise KeyError(
                    "{} has no attribute '{}'"
                    .format(self.__class__.__name__, key))
        return setattr(self, key, value)

    def __getitem__(self, key):
        if key not in self._NON_DESCRIPTOR_ATTRIBUTES:
            prop = self.__class__.__dict__.get(key)
            if not isinstance(prop, FbxPropertyOption):
                raise KeyError(
                    "{} has no attribute '{}'"
                    .format(self.__class__.__name__, key))
        return getattr(self, key)

    def __enter__(self):
        self._backup_options = self.__class__.from_scene()
        self.apply()
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self._backup_options.apply()
        self._backup_options = None

    def apply(self):
        """Apply options in this instance to the scene."""
        for _, option in self._properties().items():
            option.apply(self)
