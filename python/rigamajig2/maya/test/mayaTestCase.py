"""
This module contains functions and classes for smoother unittesting in maya

from: Chad Vernon
https://github.com/chadmv/cmt

"""

import logging
import os
import shutil
import tempfile
import unittest
import uuid

import maya.cmds as cmds

# Setup an environment variable to signify tests are run with TestResult class
RIGMAJIG_TEST_VAR = "RIGAMAJIG_UNITTEST"


# TODO: eventually this should be deprecated
class Settings(object):
    """Contains settings for running tests"""

    # temp path where files generate during tests go
    TempDirectory = os.path.join(tempfile.gettempdir(), "mayaPytest", str(uuid.uuid4()))

    # reduce the ammount of output messages durring testing.
    bufferOutput = True

    # delete temp files after unittest has run
    deleteFiles = True

    # create a new maya scene betweeen tests cases
    fileNew = True


def setTempDirectory(directory):
    """
    Set where files generated from tests should be stored.
    :param directory: A path path.
    """
    if os.path.exists(directory):
        Settings.TempDirectory = directory
    else:
        raise RuntimeError("{0} does not exist.".format(directory))


def setDeleteFiles(value):
    """
    Set whether temp files should be deleted after running all tests in a test case.
    :param value: True to delete files registered with a TestCase.
    """
    Settings.deleteFiles = value


def setBufferOutput(value):
    """
    Set whether the standard output and standard error streams are buffered during the test run.
    :param value: True or False
    """
    Settings.bufferOutput = value


def setFileNew(value):
    """
    Set whether a new file should be created after each test.
    :param value: True or False
    """
    Settings.fileNew = value


class TestCase(unittest.TestCase):
    """
    Base class for unit tests cases run in Maya.
    Tests do not have to inherit from this TestCase but this derived TestCase contains convenience
    functions to load/unload plug-ins and clean up temporary files.
    """

    # Keep track of all temporary files that were created so they can be cleaned up after all tests have been run
    filesCreated = []

    # Keep track of which plugins were loaded so we can unload them after all tests have been run
    pluginsLoaded = set()

    @classmethod
    def tearDownClass(cls):
        super(TestCase, cls).tearDownClass()
        cls.deleteTempFiles()
        cls.unloadPlugins()

    @classmethod
    def loadPlugins(cls, plugin):
        """Load the given plug-in and saves it to be unloaded when the TestCase is finished.
        @param plugin: Plug-in name
        """
        cmds.loadPlugin(plugin, quiet=True)
        cls.pluginsLoaded.add(plugin)

    @classmethod
    def unloadPlugins(cls):
        """Unload any plugins that this tests case loaded"""
        for plugin in cls.pluginsLoaded:
            cmds.unloadPlugin(plugin)
        cls.pluginsLoaded = []

    @classmethod
    def deleteTempFiles(cls):
        """Delete the temp files in the cache and clear the cache."""
        # If we don't want to keep temp files around for debugging purposes, delete them when
        # all tests in this TestCase have been run
        if Settings.deleteFiles:
            for f in cls.filesCreated:
                if os.path.exists(f):
                    os.remove(f)
            cls.files_create = []
            if os.path.exists(Settings.TempDirectory):
                shutil.rmtree(Settings.TempDirectory)

    @classmethod
    def getTempFilename(cls, fileName):
        """
        Get a unique filepath name in the testing path.
        The file will not be created, that is up to the caller.  This file will be deleted when
        the tests are finished.
        :param fileName: A partial path ex: 'path/somefile.txt'
        :return The full path to the temporary file.
        """
        tempDirectory = Settings.TempDirectory
        if not os.path.exists(tempDirectory):
            os.makedirs(tempDirectory)
        baseName, ext = os.path.splitext(fileName)
        path = "{0}/{1}{2}".format(tempDirectory, baseName, ext)
        count = 0
        while os.path.exists(path):
            # If the file already exists, add an incrememted number
            count += 1
            path = "{0}/{1}{2}{3}".format(tempDirectory, baseName, count, ext)
        cls.filesCreated.append(path)
        return path

    def assertListAlmostEqual(self, first, second, places=7, msg=None, delta=None):
        """
        Asserts that a list of floating point values is almost equal.
        unittest has assertAlmostEqual and assertListEqual but no assertListAlmostEqual.
        """
        self.assertEqual(len(first), len(second), msg)
        for a, b in zip(first, second):
            self.assertAlmostEqual(a, b, places, msg, delta)

    def assertFileExists(self, filePath):
        self.assertTrue(os.path.exists(filePath), f"The file '{filePath}' does not exist.")

    def tearDown(self):
        if Settings.fileNew and RIGMAJIG_TEST_VAR not in os.environ.keys():
            # If running tests without the custom runner, like with PyCharm, the file new of the TestResult class isn't
            # used so call file new here
            cmds.file(f=True, new=True)


class TestResult(unittest.TextTestResult):
    """
    Customize the tests result so we can do things like do a file new between each tests and suppress script
    editor output.
    """

    def __init__(self, stream, descriptions, verbosity):
        super(TestResult, self).__init__(stream, descriptions, verbosity)
        self.successes = []

    def startTestRun(self):
        """Called before any tests are run."""
        super(TestResult, self).startTestRun()
        # Create an environment variable that specifies tests are being run through the custom runner.
        os.environ[RIGMAJIG_TEST_VAR] = "1"

        ScriptEditorState.supressOutput()
        if Settings.bufferOutput:
            # Disable any logging while running tests. By disabling critical, we are disabling logging
            # at all levels below critical as well
            logging.disable(logging.DEBUG)

    def stopTestRun(self):
        """Called after all tests are run."""
        if Settings.bufferOutput:
            # Restore logging state
            logging.disable(logging.NOTSET)
        ScriptEditorState.restoreOutput()
        if Settings.deleteFiles and os.path.exists(Settings.TempDirectory):
            shutil.rmtree(Settings.TempDirectory)

        del os.environ[RIGMAJIG_TEST_VAR]

        super(TestResult, self).stopTestRun()

    def stopTest(self, test):
        """
        Called after an individual tests is run.
        :param test: TestCase that just ran.
        """
        super(TestResult, self).stopTest(test)
        if Settings.fileNew:
            cmds.file(f=True, new=True)

    def addSuccess(self, test):
        """
        Override the base addSuccess method so we can store a list of the successful tests.
        :param test: TestCase that successfully ran.
        """
        super(TestResult, self).addSuccess(test)
        self.successes.append(test)


class ScriptEditorState(object):
    """Provides methods to suppress and restore script editor output."""

    # Used to restore logging states in the script editor
    supressResults = None
    suppressErrors = None
    suppressWarnings = None
    suppressInfo = None

    @classmethod
    def supressOutput(cls):
        """Hides all script editor output."""
        if Settings.bufferOutput:
            cls.supressResults = cmds.scriptEditorInfo(q=True, suppressResults=True)
            cls.suppressErrors = cmds.scriptEditorInfo(q=True, suppressErrors=True)
            cls.suppressWarnings = cmds.scriptEditorInfo(q=True, suppressWarnings=True)
            cls.suppressInfo = cmds.scriptEditorInfo(q=True, suppressInfo=True)
            cmds.scriptEditorInfo(
                e=True,
                suppressResults=True,
                suppressInfo=True,
                suppressWarnings=True,
                suppressErrors=True,
            )

    @classmethod
    def restoreOutput(cls):
        """Restores the script editor output settings to their original values."""
        if None not in {
            cls.supressResults,
            cls.suppressErrors,
            cls.suppressWarnings,
            cls.suppressInfo,
        }:
            cmds.scriptEditorInfo(
                e=True,
                suppressResults=cls.supressResults,
                suppressInfo=cls.suppressInfo,
                suppressWarnings=cls.suppressWarnings,
                suppressErrors=cls.suppressErrors,
            )


if __name__ == "__main__":
    runTestsFromCommandLine()
