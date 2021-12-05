"""
This module contains our rig builder
"""
import os
import time

import maya.cmds as cmds
import rigamajig2.shared.common as common
import rigamajig2.shared.runScript as runScript
import rigamajig2.maya.data.abstract_data as abstract_data
import rigamajig2.maya.file as file
from rigamajig2.maya.cmpts import *

import logging

logger = logging.getLogger(__name__)

CMPT_PATH = os.path.abspath(os.path.join(__file__, '../../cmpts'))

_EXCLUDED_FOLDERS = []
_EXCLUDED_FILES = ['__init__.py', 'base.py']

# BUILD ENVIORNMENT GLOBLALS
PRE_SCRIPT_PATH = 'pre_script'
POST_SCRIPT_PATH = 'post_script'
PUB_SCRIPT_PATH = 'pub_script'

# RIG FILE KEYS
SKELETON_FILE = "skeleton_file"
SKELETON_POS = "skeleton_pos"
CONTROL_SHAPES = "control_shapes"


class Builder(object):
    def __init__(self, path=None):
        """
        Initalize the builder
        :param path: path to build enviornment
        """
        self.set_path(path)
        self.cmpts = list()

        self._cmpts_path_dict = dict()
        self._available_cmpts = list()
        self.getComponents()

        # varibles we need
        self.top_skeleton_nodes = list()

        logger.info('Initalize Rig Builder: {0}'.format(self.path))

    def getComponents(self):
        path = CMPT_PATH
        self.__lookForComponents(path)

    def __lookForComponents(self, path):
        res = os.listdir(path)
        toReturn = list()
        for r in res:
            if r not in _EXCLUDED_FOLDERS and os.path.isdir(path + '/' + r) == True:
                self.__lookForComponents()
            if r.find('.py') != -1 and r.find('.pyc') == -1 and r not in _EXCLUDED_FILES:
                if r.find('reload') == -1:
                    toReturn.append(r)
                    self._cmpts_path_dict[r] = path + r
        self._available_cmpts += toReturn

    def absPath(self, path):
        return os.path.join(self.path, path)

    # RIG BUILD STEPS
    def import_model(self, path=None):
        pass

    def import_skeleton(self):
        import rigamajig2.maya.data.node_data as node_data

        if os.path.exists(self.absPath(self.read_data(SKELETON_FILE))):
            nodes = file.import_(self.absPath(self.read_data(SKELETON_FILE)), ns=None)
            joint_data = node_data.NodeData()
            # joint_data.read(self.absPath(self.read_data(SKELETON_POS)))
            # joint_data.applyData()
        else:
            return

        # get top level nodes in the skeleton
        for node in cmds.ls(nodes, l=True, type='transform'):
            if not len(node.split('|')) > 2:
                self.top_skeleton_nodes.append(node)
        logger.info("skeleton imported")

    def initalize(self):
        """Initalize rig (this is where the user can make changes)"""
        for cmpt in self.cmpts:
            logger.info('Initalizing: {}'.format(cmpt.name))
            cmpt._intialize_cmpt()
        logger.info("initalize -- complete")

    def build(self):
        """build rig"""
        for cmpt in self.cmpts:
            logger.info('Building: {}'.format(cmpt.name))
            cmpt._build_cmpt()
            # if the component is not a main parent the cmpt.root to the rig
            if cmds.objExists('rig') and not isinstance(cmpt, main.Main):
                cmds.parent(cmpt.root, 'rig')

        # parent the bind joints to the bind group. if one exists
        if cmds.objExists('bind'):
            cmds.parent(self.top_skeleton_nodes, 'bind')

        logger.info("build -- complete")

    def connect(self):
        """connect rig"""
        for cmpt in self.cmpts:
            logger.info('Connecting: {}'.format(cmpt.name))
            cmpt._connect_cmpt()
        logger.info("connect -- complete")

    def finalize(self):
        """finalize rig"""
        for cmpt in self.cmpts:
            logger.info('Finalizing: {}'.format(cmpt.name))
            cmpt._finalize_cmpt()
        logger.info("finalize -- complete")

    def optimize(self):
        """optimize rig"""
        for cmpt in self.cmpts:
            logger.info('Optimizing {}'.format(cmpt.name))
            cmpt._optimize_cmpt()
        logger.info("optimize -- complete")

    def load_controlShapes(self, applyColor=True):
        """
        Load the control shapes
        :param applyColor: Apply the control colors.
        :return:
        """
        import rigamajig2.maya.data.curve_data as curve_data

        cd = curve_data.CurveData()
        if self.absPath(self.read_data(CONTROL_SHAPES)):
            cd.read(self.absPath(self.read_data(CONTROL_SHAPES)))

        controls = cd.getData().keys()
        logger.info("loading shapes for {} controls".format(len(controls)))
        cd.applyData(controls, applyColor=applyColor)
        logger.info("control shapes -- complete")

    def load_data(self):
        """
        Load other data, this is stuff like skinweights, blendshapes, clusters etc.
        :return:
        """
        logger.info("data loading -- complete")

    # RUN SCRIPTS
    def pre_script(self, scripts=[]):
        """
         Run pre scripts. You can add scripts by path, but the main use is through the PRE SCRIPT path
        :param scripts: path to scripts to run
        """
        if self.path:
            scripts_path = self.absPath(PRE_SCRIPT_PATH)
            for script in runScript.find_scripts(scripts_path):
                scripts.append(script)

        for script in scripts:
            runScript.run_script(script)
        logger.info("pre scripts -- complete")

    def post_script(self, scripts=[]):
        """
        Run post scripts. You can add scripts by path, but the main use is through the POST SCRIPT path
        :param scripts: path to scripts to run
        """
        if self.path:
            scripts_path = self.absPath(POST_SCRIPT_PATH)
            for script in runScript.find_scripts(scripts_path):
                scripts.append(script)

        for script in scripts:
            runScript.run_script(script)
        logger.info("post scripts -- complete")

    def pub_script(self, scripts=[]):
        """
        Run Post Scripts. You can add scripts by path, but the main use is through the POST SCRIPT path
        :param scripts:
        :return:
        """
        if self.path:
            scripts_path = self.absPath(PUB_SCRIPT_PATH)
            for script in runScript.find_scripts(scripts_path):
                scripts.append(script)

        for script in scripts:
            runScript.run_script(script)
        logger.info("publish scripts -- complete")

    # ULITITY FUNCTION TO BUILD THE ENTIRE RIG
    def run(self, optimize=True):
        if not self.path:
            logger.error('you must provide a build enviornment path. Use Bulder.set_path()')
            return

        start_time = time.time()
        print('\nBegin Rig Build\n{0}\nbuild env: {1}\n'.format('-' * 70, self.path))
        self.pre_script()
        self.import_model()
        self.import_skeleton()
        self.initalize()
        self.build()
        self.connect()
        self.finalize()
        self.load_controlShapes()
        if optimize: self.optimize()
        self.load_data()
        self.post_script()
        end_time = time.time()
        final_time = end_time - start_time

        print('\nCompleted Rig Build \t -- time elapsed: {0}\n{1}'.format(final_time, '-' * 70))

    # UTILITY FUNCTIONS
    def set_path(self, path):
        self.path = path
        self.rig_file = os.path.join(self.path, self.path.split(os.sep)[-1] + '.rig')

    def get_path(self):
        return self.path

    def set_cmpts(self, cmpts):
        """
        Set the self.cmpts
        :param cmpts: list of components to set
        """
        cmpts = common.toList(cmpts)
        self.cmpts = cmpts

    def append_cmpts(self, cmpts):
        """
        append a component
        :param cmpts: list of components to append
        :return:
        """
        cmpts = common.toList(cmpts)
        for cmpt in cmpts:
            self.cmpts.append(cmpt)

    def read_data(self, key):
        """
        read the data from the self.rig_file
        :param key:
        :return:
        """
        if not os.path.exists(self.path):
            raise RuntimeError('rig file at {} does not exist'.format(self.rig_file))

        data = abstract_data.AbstractData()
        data.read(self.rig_file)
        if data.getData().has_key(key):
            return data.getData()[key]


def build_directory():
    pass
